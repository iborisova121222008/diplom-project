import joblib
import pandas as pd
import pytest

from app.artifacts import (
    ArtifactReader,
    ArtifactValidationError,
    CANONICAL_ARTIFACTS
)
from app.config import ARTIFACT_ROOT


def test_artifact_reader_rejects_noncanonical_paths():
    reader = ArtifactReader(ARTIFACT_ROOT)

    with pytest.raises(ValueError, match="allowlist"):
        reader.path("results/lasso_custom_rf_first_run/fold_results.csv")

    with pytest.raises(ValueError, match="allowlist"):
        reader.path("../outside.joblib")


def test_missing_required_artifact_has_clear_error(tmp_path):
    reader = ArtifactReader(tmp_path)

    with pytest.raises(FileNotFoundError, match="missing"):
        reader.path("data/GSE25055_pre_lasso.joblib")


def test_required_csv_columns_are_validated(tmp_path):
    target = tmp_path / "results" / "lasso_balanced_rf"
    target.mkdir(parents=True)
    (target / "fold_results.csv").write_text(
        "fold,model\n1,Custom Random Forest\n",
        encoding="utf-8"
    )
    reader = ArtifactReader(tmp_path)

    with pytest.raises(ArtifactValidationError, match="missing columns"):
        reader.read_csv("results/lasso_balanced_rf/fold_results.csv")


def test_required_joblib_keys_are_validated(tmp_path):
    target = tmp_path / "data"
    target.mkdir()
    joblib.dump({}, target / "GSE25055_pre_lasso.joblib")
    reader = ArtifactReader(tmp_path)

    with pytest.raises(ArtifactValidationError, match="missing keys"):
        reader.load_joblib("data/GSE25055_pre_lasso.joblib")


def test_historical_experiments_are_not_canonical_sources():
    assert not any(
        "lasso_custom_rf_first_run" in path
        or "lasso_custom_rf_fold1" in path
        or "library_rf" in path
        for path in CANONICAL_ARTIFACTS
    )


def test_final_thresholds_match_authoritative_artifacts():
    reader = ArtifactReader(ARTIFACT_ROOT)
    package = reader.final_package
    external = pd.read_csv(
        ARTIFACT_ROOT
        / "results/final_external_validation_gse25065/external_metrics.csv"
    )
    thresholds = dict(zip(external["model"], external["threshold"]))

    assert thresholds["Custom Random Forest"] == package["custom_threshold"]
    assert thresholds["Sklearn Random Forest"] == package["sklearn_threshold"]
