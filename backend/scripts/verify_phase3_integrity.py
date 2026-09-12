"""Read-only Phase 3 scientific invariants and canonical artifact hashes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from sqlalchemy import text

from app.database import engine


PROJECT_DIR = Path(__file__).resolve().parents[2]
EXPECTED_HASHES = {
    "results/final_model_gse25055/final_model_package.joblib": "EF135BC5A7EF1E660AEF1F10B672FCF3ACA07AFAD10BABC9721F533F4C2257F5",
    "results/final_model_gse25055/final_selected_probes.csv": "79623C6B0181563747F16686086D2CCCA82CC7564476CC73BE05002C1181079F",
    "results/final_external_validation_gse25065/external_metrics.csv": "EA35AAEE8889A04FA27414B95C69C2ED1EA62B69EFE2CA609AA84C2DB63AD79A",
    "results/final_external_validation_gse25065/external_predictions.csv": "7F217CB18C07A14787C882698A2A4A1B422003A68148CCB4204E90F177EBCC6D",
    "results/model_comparison.csv": "C2550BF42F2C27C96E47480590A30A1CE18601F11897188E4850A170F43BF041",
    "results/lasso_selected_probes_by_fold.csv": "6A1E90221535D9DD8F18CB2D021ECC73AF746F812109BB10769494A7295922D7",
    "results/lasso_feature_stability.xlsx": "31813465408C317EFB9C86F222990A377E171D6275E58444E65478D9F86233EC",
    "results/lasso_balanced_rf/model_comparison.csv": "3EADF50BE42EF7A168FB4A37675FE8315A79B9A15BCEB145683281646A538180",
}
EXPECTED_PROBES = [
    "200011_s_at", "204012_s_at", "204568_at", "204775_at", "204825_at",
    "205347_s_at", "206373_at", "208854_s_at", "209644_x_at", "210084_x_at",
    "212330_at", "214431_at", "214746_s_at", "217744_s_at", "219051_x_at",
]
EXPECTED_EXTERNAL = {
    "custom_random_forest": {"threshold": 0.21, "roc_auc": 0.6946428571428571, "pr_auc": 0.4019152600471182, "matrix": [96, 44, 18, 24]},
    "sklearn_random_forest": {"threshold": 0.35, "roc_auc": 0.7112244897959183, "pr_auc": 0.4068663350953674, "matrix": [97, 43, 16, 26]},
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest().upper()


def verify() -> dict:
    hashes = {relative: digest(PROJECT_DIR / relative) for relative in EXPECTED_HASHES}
    if hashes != EXPECTED_HASHES:
        raise RuntimeError("Canonical artifact hash mismatch")
    with engine.connect() as connection:
        counts = dict(connection.execute(text(
            "SELECT 'prediction_records', count(*) FROM prediction_records "
            "UNION ALL SELECT 'fold_feature_similarity', count(*) FROM fold_feature_similarity "
            "UNION ALL SELECT 'selected_features', count(*) FROM selected_features"
        )).all())
        if counts != {"prediction_records": 1588, "fold_feature_similarity": 45, "selected_features": 5626}:
            raise RuntimeError(f"Database count mismatch: {counts}")
        probes = list(connection.execute(text(
            "SELECT sf.probe_id FROM selected_features sf JOIN experiments e ON e.id=sf.experiment_id "
            "WHERE e.slug='final-model-gse25055' ORDER BY sf.id"
        )).scalars())
        if probes != EXPECTED_PROBES:
            raise RuntimeError("Ordered final probe mismatch")
        rows = connection.execute(text(
            "SELECT m.model_key, m.configuration, m.overall_metrics, m.confusion_matrix "
            "FROM model_runs m JOIN experiments e ON e.id=m.experiment_id "
            "WHERE e.slug='locked-external-validation-gse25065'"
        )).all()
        for model_key, configuration, metrics, matrix in rows:
            expected = EXPECTED_EXTERNAL[model_key]
            actual_matrix = [matrix[key] for key in ("true_negative", "false_positive", "false_negative", "true_positive")]
            if configuration["classification_threshold"] != expected["threshold"] or metrics["roc_auc"] != expected["roc_auc"] or metrics["pr_auc"] != expected["pr_auc"] or actual_matrix != expected["matrix"]:
                raise RuntimeError(f"External contract mismatch for {model_key}")
    return {"status": "verified", "counts": counts, "ordered_probes": probes, "artifact_hashes": hashes}


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
