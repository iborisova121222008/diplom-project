import numpy as np
import pandas as pd
from sqlalchemy import func, select

from app.config import ARTIFACT_ROOT
from app.database import SessionLocal
from app.models import (
    Dataset,
    Experiment,
    FoldFeatureSimilarity,
    FoldMetric,
    ModelRun,
    PredictionRecord,
)
from app.seed import import_canonical_artifacts


def database_counts(session):
    return {
        "datasets": session.scalar(select(func.count(Dataset.id))),
        "experiments": session.scalar(select(func.count(Experiment.id))),
        "models": session.scalar(select(func.count(ModelRun.id))),
        "folds": session.scalar(select(func.count(FoldMetric.id))),
        "predictions": session.scalar(select(func.count(PredictionRecord.id))),
        "similarities": session.scalar(
            select(func.count(FoldFeatureSimilarity.id))
        ),
    }


def test_importer_is_idempotent():
    with SessionLocal.begin() as session:
        before = database_counts(session)
        import_canonical_artifacts(session)
        after = database_counts(session)

    assert before == after
    assert after == {
        "datasets": 2,
        "experiments": 5,
        "models": 8,
        "folds": 40,
        "predictions": 1588,
        "similarities": 45,
    }


def test_direct_and_derived_summary_sources_are_stored():
    with SessionLocal() as session:
        runs = {
            run.model_key: run
            for run in session.scalars(
                select(ModelRun)
                .join(Experiment)
                .where(Experiment.evaluation_stage == "cross_validation")
            )
        }

    assert runs["l2_logistic"].cv_summary_source_type == "direct"
    assert (
        runs["custom_random_forest"].cv_summary_source_type
        == "derived_during_import"
    )


def test_rf_summary_uses_sample_standard_deviation():
    source = pd.read_csv(
        ARTIFACT_ROOT / "results/lasso_balanced_rf/fold_results.csv"
    )
    source = source[source["model"] == "Custom Random Forest"]

    with SessionLocal() as session:
        run = session.scalar(
            select(ModelRun).where(
                ModelRun.model_key == "custom_random_forest",
                ModelRun.cv_summary_source_type == "derived_during_import"
            )
        )

    assert np.isclose(
        run.cv_summary["roc_auc"]["mean"], source["roc_auc"].mean()
    )
    assert np.isclose(
        run.cv_summary["roc_auc"]["std"], source["roc_auc"].std(ddof=1)
    )


def test_rf_confusion_uses_only_stored_oof_labels():
    source = pd.read_csv(
        ARTIFACT_ROOT / "results/lasso_balanced_rf/oof_predictions.csv"
    )
    actual = source["actual_class"]
    predicted = source["custom_prediction"]
    expected = {
        "true_negative": int(((actual == 0) & (predicted == 0)).sum()),
        "false_positive": int(((actual == 0) & (predicted == 1)).sum()),
        "false_negative": int(((actual == 1) & (predicted == 0)).sum()),
        "true_positive": int(((actual == 1) & (predicted == 1)).sum())
    }

    with SessionLocal() as session:
        run = session.scalar(
            select(ModelRun).where(
                ModelRun.model_key == "custom_random_forest",
                ModelRun.confusion_source_type == "derived_during_import"
            )
        )

    assert run.confusion_matrix == expected
    assert run.confusion_source_path.endswith("oof_predictions.csv")
