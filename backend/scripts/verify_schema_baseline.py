from sqlalchemy import inspect, select

from app.database import engine


EXPECTED_COLUMNS = {
    "datasets": {
        "id", "accession", "role", "included_patient_count",
        "original_patient_count", "excluded_patient_count", "feature_count",
        "label_mapping", "class_distribution", "source_path", "provenance",
        "methodology"
    },
    "experiments": {
        "id", "slug", "name", "dataset_id", "evaluation_stage",
        "result_scope", "locked", "source_path", "created_at"
    },
    "model_runs": {
        "id", "experiment_id", "model_key", "display_name", "model_family",
        "configuration", "configuration_source_path",
        "configuration_source_fields", "cv_summary",
        "cv_summary_source_type", "cv_summary_source_path",
        "cv_summary_source_fields", "cv_summary_derivation",
        "overall_metrics", "overall_source_path", "overall_source_fields",
        "confusion_matrix", "confusion_source_type", "confusion_source_path",
        "confusion_source_fields", "confusion_derivation"
    },
    "fold_metrics": {
        "id", "model_run_id", "fold", "training_patient_count",
        "validation_patient_count", "selected_probe_count",
        "selected_parameters", "metrics", "source_path", "source_fields"
    },
    "probe_annotations": {
        "probe_id", "gene_symbol", "gene_name", "entrez_id",
        "number_of_genes", "mapping_status", "source_path", "source_fields"
    },
    "selected_features": {
        "id", "experiment_id", "selection_context", "fold", "probe_id",
        "coefficient", "selected_folds", "selection_frequency",
        "coefficient_direction", "source_path", "source_fields"
    },
}
EXPECTED_COUNTS = {
    "datasets": 2,
    "experiments": 5,
    "model_runs": 8,
    "fold_metrics": 40,
    "probe_annotations": 22283,
    "selected_features": 5626,
}


if __name__ == "__main__":
    inspector = inspect(engine)
    available = set(inspector.get_table_names())
    missing = set(EXPECTED_COLUMNS) - available

    if missing:
        raise SystemExit(f"Baseline verification failed; missing tables: {missing}")

    for table, expected in EXPECTED_COLUMNS.items():
        actual = {column["name"] for column in inspector.get_columns(table)}

        if not expected.issubset(actual):
            raise SystemExit(
                f"Baseline verification failed for {table}; "
                f"missing columns: {expected - actual}"
            )

    with engine.connect() as connection:
        transaction = connection.begin()
        connection.exec_driver_sql("SET TRANSACTION READ ONLY")

        for table, expected in EXPECTED_COUNTS.items():
            actual = connection.exec_driver_sql(
                f'SELECT count(*) FROM "{table}"'
            ).scalar_one()

            if actual != expected:
                raise SystemExit(
                    f"Baseline verification failed for {table}: "
                    f"expected {expected}, found {actual}."
                )

        transaction.rollback()

    print("Verified existing six-table PostgreSQL baseline.")
