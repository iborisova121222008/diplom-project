"""Generate deterministic, read-only sklearn tree previews from the locked package.

This script never fits a model or writes scientific results. It derives display
assets and structural metadata from the fixed final-model artifact only.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from sklearn.tree import plot_tree  # noqa: E402


PROJECT_DIR = Path(__file__).resolve().parents[2]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
PACKAGE_PATH = PROJECT_DIR / "results/final_model_gse25055/final_model_package.joblib"
PROBE_PATH = PROJECT_DIR / "results/final_model_gse25055/final_selected_probes.csv"
OUTPUT_DIR = PROJECT_DIR / "backend/generated/tree_previews"
EXPECTED_PROBE_COUNT = 15
EXPECTED_TREE_COUNT = 30
GENERATED_DEPTH = 3


def package_identity(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def tree_feature_usage(estimator, selected_probes: list[str]):
    tree = estimator.tree_
    depths = {0: 0}
    stack = [0]
    by_probe: dict[str, list[int]] = defaultdict(list)
    while stack:
        node = stack.pop()
        feature_index = int(tree.feature[node])
        if feature_index >= 0:
            if feature_index >= len(selected_probes):
                raise ValueError(f"Tree feature index {feature_index} exceeds ordered probes")
            by_probe[selected_probes[feature_index]].append(depths[node])
            for child in (int(tree.children_left[node]), int(tree.children_right[node])):
                if child >= 0:
                    depths[child] = depths[node] + 1
                    stack.append(child)
    return [
        {
            "probe_id": probe,
            "split_count": len(values),
            "minimum_split_depth": min(values),
            "mean_split_depth": sum(values) / len(values),
        }
        for probe, values in by_probe.items()
    ]


def generate() -> dict:
    package = joblib.load(PACKAGE_PATH)
    selected_probes = list(package["selected_probes"])
    csv_probes = [
        line.split(",", 1)[0].strip()
        for line in PROBE_PATH.read_text(encoding="utf-8").splitlines()[1:]
        if line.strip()
    ]
    if len(selected_probes) != EXPECTED_PROBE_COUNT or selected_probes != csv_probes:
        raise ValueError("Locked package and ordered final-probe file do not match")

    forest = package["sklearn_random_forest"]
    if len(forest.estimators_) != EXPECTED_TREE_COUNT or forest.n_features_in_ != EXPECTED_PROBE_COUNT:
        raise ValueError("Locked sklearn forest does not match the verified 30×15 contract")
    custom_forest = package["custom_random_forest"]
    if len(custom_forest) != EXPECTED_TREE_COUNT or not all(
        hasattr(root, "feature_index") for root in custom_forest
    ):
        raise ValueError("Locked custom forest does not contain 30 traversable TreeNode roots")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    matplotlib.rcParams["svg.hashsalt"] = "diplom-project-locked-forest"
    tree_records = []
    aggregate = Counter()
    aggregate_depths: dict[str, list[float]] = defaultdict(list)

    for index, estimator in enumerate(forest.estimators_, start=1):
        usage = tree_feature_usage(estimator, selected_probes)
        for item in usage:
            aggregate[item["probe_id"]] += item["split_count"]
            aggregate_depths[item["probe_id"]].extend(
                [item["mean_split_depth"]] * item["split_count"]
            )

        figure, axis = plt.subplots(figsize=(18, 8), facecolor="white")
        plot_tree(
            estimator,
            feature_names=selected_probes,
            class_names=["RD", "pCR"],
            max_depth=GENERATED_DEPTH,
            filled=True,
            rounded=False,
            proportion=True,
            impurity=True,
            ax=axis,
            fontsize=7,
        )
        axis.set_title(f"Sklearn Random Forest · дърво {index} · съкратено до depth {GENERATED_DEPTH}")
        figure.tight_layout()
        filename = f"tree-{index:02d}.svg"
        figure.savefig(
            OUTPUT_DIR / filename,
            format="svg",
            metadata={"Date": package.get("created_at_utc", "locked-model-package")},
        )
        plt.close(figure)
        tree_records.append({
            "tree_index": index,
            "full_depth": int(estimator.tree_.max_depth),
            "node_count": int(estimator.tree_.node_count),
            "generated_depth": GENERATED_DEPTH,
            "used_probes": [item["probe_id"] for item in usage],
            "feature_usage": usage,
            "asset": filename,
        })

    feature_usage = []
    for probe in selected_probes:
        tree_items = [item for item in tree_records if probe in item["used_probes"]]
        depths = aggregate_depths[probe]
        feature_usage.append({
            "probe_id": probe,
            "trees_using": len(tree_items),
            "split_count": aggregate[probe],
            "minimum_split_depth": min(
                item["minimum_split_depth"]
                for tree in tree_items
                for item in tree["feature_usage"]
                if item["probe_id"] == probe
            ) if tree_items else None,
            "mean_split_depth": sum(depths) / len(depths) if depths else None,
            "tree_indices": [item["tree_index"] for item in tree_items],
        })

    manifest = {
        "derivation": "Read-only structure extraction from the locked fitted sklearn forest; no fit or prediction replacement.",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_package": "results/final_model_gse25055/final_model_package.joblib",
        "model_package_identity": package_identity(PACKAGE_PATH),
        "model_created_at_utc": package.get("created_at_utc"),
        "tree_count": EXPECTED_TREE_COUNT,
        "custom_tree_count": len(custom_forest),
        "selected_probes": selected_probes,
        "generated_depth": GENERATED_DEPTH,
        "trees": tree_records,
        "feature_usage": feature_usage,
    }
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    created = generate()
    print(
        f"Generated {created['tree_count']} locked sklearn tree previews "
        f"for {len(created['selected_probes'])} ordered probes."
    )
