from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.artifacts import ArtifactReader
from app.config import ARTIFACT_ROOT
from app.models import (
    Dataset,
    Experiment,
    FoldFeatureSimilarity,
    FoldMetric,
    ModelRun,
    PredictionRecord,
    ProbeAnnotation,
    SelectedFeature
)


CANONICAL_EXPERIMENT_SLUGS = [
    "l2-logistic-nested-cv",
    "lasso-logistic-nested-cv",
    "balanced-rf-nested-cv",
    "final-model-gse25055",
    "locked-external-validation-gse25065"
]


def parse_datetime(value):
    if not value:
        return None

    return datetime.fromisoformat(value)


def _upsert_annotations(session, annotations):
    values = list(annotations)
    dialect = session.get_bind().dialect.name

    if dialect == "postgresql":
        statement = postgresql_insert(ProbeAnnotation)
    elif dialect == "sqlite":
        statement = sqlite_insert(ProbeAnnotation)
    else:
        raise RuntimeError(
            f"Unsupported importer database dialect: {dialect}"
        )

    update_fields = {
        field: getattr(statement.excluded, field)
        for field in [
            "gene_symbol",
            "gene_name",
            "entrez_id",
            "number_of_genes",
            "mapping_status",
            "source_path",
            "source_fields"
        ]
    }

    for start in range(0, len(values), 1000):
        batch = values[start:start + 1000]
        session.execute(
            statement.values(batch).on_conflict_do_update(
                index_elements=[ProbeAnnotation.probe_id],
                set_=update_fields
            )
        )


def _remove_owned_experiments(session):
    experiment_ids = list(session.scalars(
        select(Experiment.id).where(
            Experiment.slug.in_(CANONICAL_EXPERIMENT_SLUGS)
        )
    ))

    if not experiment_ids:
        return

    model_run_ids = list(session.scalars(
        select(ModelRun.id).where(
            ModelRun.experiment_id.in_(experiment_ids)
        )
    ))

    session.execute(
        delete(SelectedFeature).where(
            SelectedFeature.experiment_id.in_(experiment_ids)
        )
    )

    if model_run_ids:
        session.execute(
            delete(PredictionRecord).where(
                PredictionRecord.model_run_id.in_(model_run_ids)
            )
        )
        session.execute(
            delete(FoldMetric).where(
                FoldMetric.model_run_id.in_(model_run_ids)
            )
        )
        session.execute(
            delete(ModelRun).where(
                ModelRun.id.in_(model_run_ids)
            )
        )

    session.execute(
        delete(FoldFeatureSimilarity).where(
            FoldFeatureSimilarity.experiment_id.in_(experiment_ids)
        )
    )

    session.execute(
        delete(Experiment).where(Experiment.id.in_(experiment_ids))
    )


def _upsert_datasets(session, records):
    datasets = {}

    for record in records:
        dataset = session.scalar(
            select(Dataset).where(
                Dataset.accession == record["accession"]
            )
        )

        if dataset is None:
            dataset = Dataset(accession=record["accession"])
            session.add(dataset)

        for field, value in record.items():
            setattr(dataset, field, value)

        session.flush()
        datasets[dataset.accession] = dataset

    return datasets


def import_canonical_artifacts(session: Session, artifact_root=None):
    """Validate and replace only importer-owned canonical experiment rows."""

    reader = ArtifactReader(
        ARTIFACT_ROOT if artifact_root is None else artifact_root
    )

    # Materialize and validate every source before changing database rows.
    reader.validate()
    dataset_records = reader.datasets()
    annotations = list(reader.annotations())
    selected_features = list(reader.selected_features())
    cv_sources = reader.cv_sources()
    prepared_cv = []

    for source in cv_sources:
        folds = reader.fold_results(source)
        summary = reader.cv_summary(source)
        overall = reader.overall_result(source)
        confusion = reader.cv_confusion(source, overall)
        prepared_cv.append(
            (source, folds, summary, overall, confusion)
        )

    final_configurations = reader.final_configurations()
    final_validation = reader.final_validation()
    prediction_records = reader.prediction_records()
    similarities = reader.fold_feature_similarities()
    evaluated_at = parse_datetime(
        reader.external_bundle["evaluated_at_utc"]
    )

    _remove_owned_experiments(session)
    datasets = _upsert_datasets(session, dataset_records)
    _upsert_annotations(session, annotations)

    experiment_specs = [
        {
            "slug": "l2-logistic-nested-cv",
            "name": "L2 Logistic Regression nested cross-validation",
            "dataset_id": datasets["GSE25055"].id,
            "evaluation_stage": "cross_validation",
            "result_scope": "per_fold_and_overall_oof",
            "locked": False,
            "source_path": "results/l2_logistic_cv_fold_metrics.csv"
        },
        {
            "slug": "lasso-logistic-nested-cv",
            "name": "LASSO Logistic Regression nested cross-validation",
            "dataset_id": datasets["GSE25055"].id,
            "evaluation_stage": "cross_validation",
            "result_scope": "per_fold_and_overall_oof",
            "locked": False,
            "source_path": "results/lasso_cv_fold_metrics.csv"
        },
        {
            "slug": "balanced-rf-nested-cv",
            "name": "Balanced paired Random Forest nested cross-validation",
            "dataset_id": datasets["GSE25055"].id,
            "evaluation_stage": "cross_validation",
            "result_scope": "per_fold_and_overall_oof",
            "locked": False,
            "source_path":
                "results/lasso_balanced_rf/experiment_results.joblib"
        },
        {
            "slug": "final-model-gse25055",
            "name": "Final models trained on complete GSE25055",
            "dataset_id": datasets["GSE25055"].id,
            "evaluation_stage": "final_training",
            "result_scope": "locked_configuration",
            "locked": True,
            "source_path":
                "results/final_model_gse25055/final_model_package.joblib"
        },
        {
            "slug": "locked-external-validation-gse25065",
            "name": "One-time locked external validation on GSE25065",
            "dataset_id": datasets["GSE25065"].id,
            "evaluation_stage": "external_validation",
            "result_scope": "locked_external_metrics",
            "locked": True,
            "source_path":
                "results/final_external_validation_gse25065/"
                "external_metrics.csv",
            "created_at": evaluated_at
        }
    ]
    experiments = {}

    for specification in experiment_specs:
        experiment = Experiment(**specification)
        session.add(experiment)
        session.flush()
        experiments[experiment.slug] = experiment

    model_runs = {}

    for source, folds, summary, overall, confusion in prepared_cv:
        run = ModelRun(
            experiment_id=experiments[source["experiment_slug"]].id,
            model_key=source["model_key"],
            display_name=source["display_name"],
            model_family=source["model_family"],
            configuration=source["configuration"],
            configuration_source_path=source["configuration_source"],
            configuration_source_fields={
                key: key for key in source["configuration"]
            },
            cv_summary=summary["values"],
            cv_summary_source_type=summary["source_type"],
            cv_summary_source_path=summary["source_path"],
            cv_summary_source_fields=summary["source_fields"],
            cv_summary_derivation=summary["derivation"],
            overall_metrics=overall["metrics"],
            overall_source_path=overall["source_path"],
            overall_source_fields=overall["source_fields"],
            confusion_matrix=confusion["values"],
            confusion_source_type=confusion["source_type"],
            confusion_source_path=confusion["source_path"],
            confusion_source_fields=confusion["source_fields"],
            confusion_derivation=confusion["derivation"]
        )
        session.add(run)
        session.flush()
        model_runs[(source["experiment_slug"], source["model_key"])] = run

        for fold in folds:
            session.add(FoldMetric(
                model_run_id=run.id,
                **fold
            ))

    final_experiment = experiments["final-model-gse25055"]

    for model_key, item in final_configurations.items():
        display_name = (
            "Custom Random Forest"
            if model_key == "custom_random_forest"
            else "Sklearn Random Forest"
        )
        run = ModelRun(
            experiment_id=final_experiment.id,
            model_key=model_key,
            display_name=display_name,
            model_family=display_name,
            configuration=item["configuration"],
            configuration_source_path=item["source_path"],
            configuration_source_fields=item["source_fields"],
            cv_summary={},
            cv_summary_source_fields={},
            overall_metrics={},
            overall_source_fields={},
            confusion_source_fields={}
        )
        session.add(run)
        session.flush()
        model_runs[("final-model-gse25055", model_key)] = run

    external_experiment = experiments[
        "locked-external-validation-gse25065"
    ]

    for item in final_validation:
        final_configuration = final_configurations[item["model_key"]]
        external_configuration = dict(final_configuration["configuration"])
        external_configuration["classification_threshold"] = item["threshold"]
        external_source_fields = dict(final_configuration["source_fields"])
        external_source_fields["classification_threshold"] = {
            "path": item["source_path"],
            "field": "threshold"
        }
        run = ModelRun(
            experiment_id=external_experiment.id,
            model_key=item["model_key"],
            display_name=item["display_name"],
            model_family=item["display_name"],
            configuration=external_configuration,
            configuration_source_path=final_configuration["source_path"],
            configuration_source_fields=external_source_fields,
            cv_summary={},
            cv_summary_source_fields={},
            overall_metrics=item["metrics"],
            overall_source_path=item["source_path"],
            overall_source_fields=item["source_fields"],
            confusion_matrix=item["confusion_matrix"],
            confusion_source_type="direct",
            confusion_source_path=item["source_path"],
            confusion_source_fields=item["source_fields"][
                "confusion_matrix"
            ]
        )
        session.add(run)
        session.flush()
        model_runs[("locked-external-validation-gse25065", item["model_key"])] = run

    for item in selected_features:
        experiment_slug = item.pop("experiment_slug")
        session.add(SelectedFeature(
            experiment_id=experiments[experiment_slug].id,
            **item
        ))

    for item in prediction_records:
        experiment_slug = item.pop("experiment_slug")
        model_key = item.pop("model_key")
        session.add(PredictionRecord(
            model_run_id=model_runs[(experiment_slug, model_key)].id,
            **item
        ))

    for item in similarities:
        experiment_slug = item.pop("experiment_slug")
        session.add(FoldFeatureSimilarity(
            experiment_id=experiments[experiment_slug].id,
            **item
        ))

    session.flush()

    return {
        "datasets": len(dataset_records),
        "experiments": len(experiments),
        "cv_model_runs": len(prepared_cv),
        "selected_features": len(selected_features),
        "annotations": len(annotations),
        "final_validation_models": len(final_validation),
        "prediction_records": len(prediction_records),
        "fold_feature_similarity": len(similarities)
    }


def backfill_phase2_records(session: Session, artifact_root=None):
    """Add the approved Phase 2 records without replacing existing rows."""

    reader = ArtifactReader(
        ARTIFACT_ROOT if artifact_root is None else artifact_root
    )
    reader.validate()
    predictions = reader.prediction_records()
    similarities = reader.fold_feature_similarities()
    selected_features = list(reader.selected_features())

    datasets = {
        item.accession: item
        for item in session.scalars(select(Dataset)).all()
    }
    experiments = {
        item.slug: item
        for item in session.scalars(select(Experiment)).all()
    }
    runs = {
        (run.experiment.slug, run.model_key): run
        for run in session.scalars(select(ModelRun)).all()
    }

    missing_experiments = set(CANONICAL_EXPERIMENT_SLUGS) - set(experiments)

    if "GSE25065" not in datasets or missing_experiments:
        raise RuntimeError(
            "The verified six-table baseline is incomplete; run the canonical "
            "import before the additive Phase 2 backfill."
        )

    datasets["GSE25065"].compatibility_metadata = (
        reader.external_compatibility_metadata()
    )
    datasets["GSE25055"].methodology = reader.datasets()[0]["methodology"]
    selected_lookup = {
        (
            item["experiment_slug"], item["selection_context"],
            item["fold"], item["probe_id"]
        ): item
        for item in selected_features
    }

    for feature in session.scalars(select(SelectedFeature)).all():
        lookup_key = (
            feature.experiment.slug,
            feature.selection_context,
            feature.fold,
            feature.probe_id,
        )
        expected_feature = selected_lookup.get(lookup_key)
        feature.mean_coefficient = (
            expected_feature["mean_coefficient"] if expected_feature else None
        )
        if expected_feature and expected_feature["coefficient_direction"]:
            feature.coefficient_direction = expected_feature[
                "coefficient_direction"
            ]
    dialect = session.get_bind().dialect.name
    prediction_values = []

    for item in predictions:
        record = dict(item)
        experiment_slug = record.pop("experiment_slug")
        model_key = record.pop("model_key")
        run = runs.get((experiment_slug, model_key))

        if run is None:
            raise RuntimeError(
                f"Missing model run {experiment_slug}/{model_key}."
            )

        prediction_values.append({"model_run_id": run.id, **record})

    similarity_values = []

    for item in similarities:
        record = dict(item)
        experiment_slug = record.pop("experiment_slug")
        similarity_values.append({
            "experiment_id": experiments[experiment_slug].id,
            **record
        })

    if dialect == "postgresql":
        prediction_insert = postgresql_insert(PredictionRecord)
        similarity_insert = postgresql_insert(FoldFeatureSimilarity)
    elif dialect == "sqlite":
        prediction_insert = sqlite_insert(PredictionRecord)
        similarity_insert = sqlite_insert(FoldFeatureSimilarity)
    else:
        raise RuntimeError(f"Unsupported importer database dialect: {dialect}")

    for start in range(0, len(prediction_values), 500):
        batch = prediction_values[start:start + 500]
        statement = prediction_insert.values(batch)
        session.execute(statement.on_conflict_do_update(
            index_elements=[
                PredictionRecord.model_run_id,
                PredictionRecord.patient_id
            ],
            set_={
                field: getattr(statement.excluded, field)
                for field in [
                    "actual_class", "predicted_class", "probability",
                    "validation_fold", "source_path", "source_fields"
                ]
            }
        ))

    statement = similarity_insert.values(similarity_values)
    session.execute(statement.on_conflict_do_update(
        index_elements=[
            FoldFeatureSimilarity.experiment_id,
            FoldFeatureSimilarity.fold_a,
            FoldFeatureSimilarity.fold_b
        ],
        set_={
            field: getattr(statement.excluded, field)
            for field in [
                "shared_probes", "union_probes", "jaccard_similarity",
                "source_path", "source_fields"
            ]
        }
    ))
    session.flush()

    return {
        "prediction_records": len(prediction_values),
        "fold_feature_similarity": len(similarity_values),
        "datasets_with_compatibility_metadata": 1,
        "selected_features_with_mean_coefficients": sum(
            item["mean_coefficient"] is not None
            for item in selected_lookup.values()
        ),
    }


# Backwards-compatible name for the initial prototype script.
seed_database = import_canonical_artifacts
