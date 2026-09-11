from functools import cached_property
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd

from app.methodology import METHODOLOGY_STEPS


METRIC_FIELDS = {
    "roc_auc": "roc_auc",
    "average_precision": "pr_auc",
    "pr_auc": "pr_auc",
    "accuracy": "accuracy",
    "balanced_accuracy": "balanced_accuracy",
    "f1": "f1",
    "precision": "precision",
    "sensitivity": "sensitivity",
    "specificity": "specificity",
    "ROC-AUC": "roc_auc",
    "PR-AUC": "pr_auc",
    "Accuracy": "accuracy",
    "Balanced accuracy": "balanced_accuracy",
    "F1": "f1",
    "Precision": "precision",
    "Sensitivity": "sensitivity",
    "Specificity": "specificity"
}

CANONICAL_ARTIFACTS = {
    "data/GSE25055_pre_lasso.joblib",
    "data/GSE25065_pre_lasso.joblib",
    "results/GSE25055_outer_fold_assignments.csv",
    "results/l2_logistic_cv_fold_metrics.csv",
    "results/l2_logistic_cv_summary.csv",
    "results/l2_logistic_oof_metrics.csv",
    "results/l2_logistic_out_of_fold_predictions.csv",
    "results/lasso_cv_fold_metrics.csv",
    "results/lasso_cv_summary.csv",
    "results/lasso_feature_stability.csv",
    "results/lasso_feature_stability.xlsx",
    "results/lasso_jaccard_stability.csv",
    "results/lasso_out_of_fold_predictions.csv",
    "results/lasso_selected_probes_by_fold.csv",
    "results/lasso_72_stable_features.xlsx",
    "results/model_comparison.csv",
    "results/lasso_balanced_rf/experiment_results.joblib",
    "results/lasso_balanced_rf/fold_results.csv",
    "results/lasso_balanced_rf/model_comparison.csv",
    "results/lasso_balanced_rf/oof_predictions.csv",
    "results/lasso_balanced_rf/selected_probes_by_fold.csv",
    "results/final_model_gse25055/final_model_package.joblib",
    "results/final_model_gse25055/final_selected_probes.csv",
    "results/final_external_validation_gse25065/external_metrics.csv",
    "results/final_external_validation_gse25065/external_predictions.csv",
    "results/final_external_validation_gse25065/external_validation_results.joblib"
}

REQUIRED_COLUMNS = {
    "results/GSE25055_outer_fold_assignments.csv": {
        "Patient", "validation_fold"
    },
    "results/l2_logistic_cv_fold_metrics.csv": {
        "fold", "training_patients", "validation_patients", "best_C",
        "best_class_weight", "roc_auc", "average_precision", "accuracy",
        "balanced_accuracy", "f1", "precision", "sensitivity", "specificity"
    },
    "results/l2_logistic_cv_summary.csv": {
        "Mean", "Standard deviation"
    },
    "results/l2_logistic_oof_metrics.csv": {"Metric", "Value"},
    "results/l2_logistic_out_of_fold_predictions.csv": {
        "Patient", "Actual_Response", "Predicted_Response", "pCR_Probability"
    },
    "results/lasso_cv_fold_metrics.csv": {
        "fold", "training_patients", "validation_patients", "best_C",
        "best_class_weight", "selected_probes", "roc_auc",
        "average_precision", "accuracy", "balanced_accuracy", "f1",
        "precision", "sensitivity", "specificity"
    },
    "results/lasso_cv_summary.csv": {"Mean", "Standard deviation"},
    "results/lasso_feature_stability.csv": {
        "PROBEID", "selected_folds", "mean_coefficient",
        "mean_absolute_coefficient", "selection_frequency", "SYMBOL",
        "GENENAME", "ENTREZID", "NUMBER_OF_GENES", "MAPPING_STATUS",
        "MODEL_DIRECTION"
    },
    "results/lasso_jaccard_stability.csv": {
        "fold_a", "fold_b", "shared_probes", "union_probes",
        "jaccard_similarity"
    },
    "results/lasso_out_of_fold_predictions.csv": {
        "Patient", "Actual_Response", "Predicted_Response", "pCR_Probability"
    },
    "results/lasso_selected_probes_by_fold.csv": {
        "fold", "PROBEID", "coefficient"
    },
    "results/model_comparison.csv": {
        "Model", "ROC-AUC", "PR-AUC", "Accuracy", "Balanced accuracy",
        "F1", "Precision", "Sensitivity", "Specificity", "True negatives",
        "False positives", "False negatives", "True positives"
    },
    "results/lasso_balanced_rf/fold_results.csv": {
        "fold", "model", "selected_probes", "rf_time_seconds", "roc_auc",
        "average_precision", "accuracy", "balanced_accuracy", "f1",
        "precision", "sensitivity", "specificity"
    },
    "results/lasso_balanced_rf/model_comparison.csv": {
        "model", "roc_auc", "average_precision", "accuracy",
        "balanced_accuracy", "f1", "precision", "sensitivity", "specificity"
    },
    "results/lasso_balanced_rf/oof_predictions.csv": {
        "patient", "actual_class", "custom_prediction",
        "custom_probability", "sklearn_prediction", "sklearn_probability"
    },
    "results/lasso_balanced_rf/selected_probes_by_fold.csv": {
        "fold", "probe_id"
    },
    "results/final_model_gse25055/final_selected_probes.csv": {
        "probe_id", "lasso_coefficient"
    },
    "results/final_external_validation_gse25065/external_metrics.csv": {
        "model", "threshold", "roc_auc", "pr_auc", "accuracy",
        "balanced_accuracy", "f1", "precision", "sensitivity",
        "specificity", "tn", "fp", "fn", "tp"
    },
    "results/final_external_validation_gse25065/external_predictions.csv": {
        "patient", "actual_class", "custom_probability",
        "custom_prediction", "sklearn_probability", "sklearn_prediction"
    }
}

REQUIRED_XLSX_COLUMNS = {
    "results/lasso_feature_stability.xlsx": {
        "PROBEID", "selected_folds", "mean_coefficient",
        "mean_absolute_coefficient", "selection_frequency", "SYMBOL",
        "GENENAME", "ENTREZID", "NUMBER_OF_GENES", "MAPPING_STATUS"
    },
    "results/lasso_72_stable_features.xlsx": {
        "PROBEID", "SYMBOL", "GENENAME", "selected_folds",
        "selection_frequency", "mean_coefficient",
        "mean_absolute_coefficient", "MODEL_DIRECTION", "MAPPING_STATUS"
    }
}

REQUIRED_JOBLIB_KEYS = {
    "data/GSE25055_pre_lasso.joblib": {
        "dataset_id", "label_mapping", "number_of_original_patients",
        "number_of_modeling_patients", "X", "y", "gene_annotation"
    },
    "data/GSE25065_pre_lasso.joblib": {
        "dataset_id", "role", "label_mapping", "number_of_original_patients",
        "number_of_validation_patients", "number_of_excluded_patients",
        "X", "y", "gene_annotation"
    },
    "results/lasso_balanced_rf/experiment_results.joblib": {
        "experiment_name", "dataset", "random_state", "outer_folds",
        "inner_folds", "lasso_parameter_grid", "number_of_trees",
        "max_depth", "min_samples_split", "classification_threshold",
        "class_weight", "fold_results", "comparison_table",
        "oof_predictions", "selected_probes_by_fold", "outer_splits"
    },
    "results/final_model_gse25055/final_model_package.joblib": {
        "training_dataset", "external_dataset", "label_mapping",
        "training_samples", "original_feature_count", "lasso_best_C",
        "selected_probes", "selected_probe_count", "custom_threshold",
        "sklearn_threshold", "custom_rf_config", "sklearn_rf_config"
    },
    "results/final_external_validation_gse25065/"
    "external_validation_results.joblib": {
        "evaluated_at_utc", "training_dataset", "external_dataset",
        "model_package_path", "selected_probes", "metrics", "predictions"
    }
}

EXPECTED_DATASETS = {
    "GSE25055": {
        "original": 310, "included": 306, "excluded": 4,
        "features": 22283, "class_distribution": {"0": 249, "1": 57}
    },
    "GSE25065": {
        "original": 198, "included": 182, "excluded": 16,
        "features": 22283, "class_distribution": {"0": 140, "1": 42}
    }
}

EXPECTED_FINAL = {
    "lasso_best_C": 0.03,
    "selected_probe_count": 15,
    "custom_threshold": 0.21,
    "sklearn_threshold": 0.35
}


class ArtifactValidationError(RuntimeError):
    pass


def clean_value(value):
    if isinstance(value, np.generic):
        return value.item()

    if isinstance(value, float) and np.isnan(value):
        return None

    return value


def metric_values(record):
    values = {}
    fields = {}

    for source_field, api_field in METRIC_FIELDS.items():
        if source_field in record:
            values[api_field] = clean_value(record[source_field])
            fields[api_field] = source_field

    return values, fields


class ArtifactReader:
    """Read the fixed, trusted canonical artifact set only."""

    def __init__(self, root: Path):
        self.root = root.resolve()

    def path(self, relative_path):
        if relative_path not in CANONICAL_ARTIFACTS:
            raise ValueError(
                f"Artifact is not in the canonical allowlist: {relative_path}"
            )

        path = (self.root / relative_path).resolve()

        if path != self.root and self.root not in path.parents:
            raise ValueError("Artifact path must stay inside the project.")

        if not path.is_file():
            raise FileNotFoundError(
                f"Required canonical artifact is missing: {relative_path}"
            )

        return path

    def read_csv(self, relative_path):
        frame = pd.read_csv(self.path(relative_path))
        required = REQUIRED_COLUMNS.get(relative_path, set())
        missing = sorted(required - set(frame.columns))

        if missing:
            raise ArtifactValidationError(
                f"{relative_path} is missing columns: {', '.join(missing)}"
            )

        return frame

    def load_joblib(self, relative_path):
        project_path = str(self.root)
        sys.dont_write_bytecode = True

        if project_path not in sys.path:
            sys.path.insert(0, project_path)

        value = joblib.load(self.path(relative_path))
        required = REQUIRED_JOBLIB_KEYS.get(relative_path, set())

        if not isinstance(value, dict):
            raise ArtifactValidationError(
                f"{relative_path} must contain a dictionary."
            )

        missing = sorted(required - set(value))

        if missing:
            raise ArtifactValidationError(
                f"{relative_path} is missing keys: {', '.join(missing)}"
            )

        return value

    def read_xlsx(self, relative_path):
        frame = pd.read_excel(self.path(relative_path))
        required = REQUIRED_XLSX_COLUMNS.get(relative_path, set())
        missing = sorted(required - set(frame.columns))

        if missing:
            raise ArtifactValidationError(
                f"{relative_path} is missing columns: {', '.join(missing)}"
            )

        return frame

    @cached_property
    def training_checkpoint(self):
        return self.load_joblib("data/GSE25055_pre_lasso.joblib")

    @cached_property
    def external_checkpoint(self):
        return self.load_joblib("data/GSE25065_pre_lasso.joblib")

    @cached_property
    def balanced_experiment(self):
        return self.load_joblib(
            "results/lasso_balanced_rf/experiment_results.joblib"
        )

    @cached_property
    def final_package(self):
        return self.load_joblib(
            "results/final_model_gse25055/final_model_package.joblib"
        )

    @cached_property
    def external_bundle(self):
        return self.load_joblib(
            "results/final_external_validation_gse25065/"
            "external_validation_results.joblib"
        )

    def validate(self):
        for relative_path in sorted(CANONICAL_ARTIFACTS):
            self.path(relative_path)

        for relative_path in REQUIRED_COLUMNS:
            self.read_csv(relative_path)

        for relative_path in REQUIRED_XLSX_COLUMNS:
            self.read_xlsx(relative_path)

        for relative_path in REQUIRED_JOBLIB_KEYS:
            self.load_joblib(relative_path)

        self._validate_datasets()
        self._validate_folds_and_patients()
        self._validate_selected_features()
        self._validate_final_results()
        self._validate_phase2_records()

    def _validate_datasets(self):
        for checkpoint, expected in [
            (self.training_checkpoint, EXPECTED_DATASETS["GSE25055"]),
            (self.external_checkpoint, EXPECTED_DATASETS["GSE25065"])
        ]:
            x = checkpoint["X"]
            y = checkpoint["y"]
            accession = checkpoint["dataset_id"]
            included = len(x)
            excluded = checkpoint["number_of_original_patients"] - included
            distribution = {
                str(key): int(value)
                for key, value in y.value_counts().sort_index().items()
            }
            actual = {
                "original": int(checkpoint["number_of_original_patients"]),
                "included": included,
                "excluded": excluded,
                "features": int(x.shape[1]),
                "class_distribution": distribution
            }

            if actual != expected:
                raise ArtifactValidationError(
                    f"{accession} checkpoint conflicts with expected "
                    f"consistency values: {actual}"
                )

            if int(checkpoint[
                "number_of_modeling_patients"
                if accession == "GSE25055"
                else "number_of_validation_patients"
            ]) != included:
                raise ArtifactValidationError(
                    f"{accession} stored included count conflicts with X."
                )

            if (
                "number_of_excluded_patients" in checkpoint
                and int(checkpoint["number_of_excluded_patients"]) != excluded
            ):
                raise ArtifactValidationError(
                    f"{accession} stored excluded count conflicts with X."
                )

            if not x.index.equals(y.index):
                raise ArtifactValidationError(
                    f"{accession} X and y indices are not aligned."
                )

        if not self.training_checkpoint["X"].columns.equals(
            self.external_checkpoint["X"].columns
        ):
            raise ArtifactValidationError(
                "Training and external probe order does not match."
            )

    def _validate_folds_and_patients(self):
        expected_patients = set(
            self.training_checkpoint["y"].index.astype(str)
        )
        fold_files = [
            "results/l2_logistic_cv_fold_metrics.csv",
            "results/lasso_cv_fold_metrics.csv",
            "results/lasso_balanced_rf/fold_results.csv"
        ]

        for relative_path in fold_files:
            frame = self.read_csv(relative_path)

            if sorted(frame["fold"].unique().tolist()) != list(range(1, 11)):
                raise ArtifactValidationError(
                    f"{relative_path} does not contain folds 1 through 10."
                )

            unique_fields = ["fold", "model"] if "model" in frame else ["fold"]

            if frame.duplicated(unique_fields).any():
                raise ArtifactValidationError(
                    f"{relative_path} contains duplicate fold rows."
                )

        prediction_specs = [
            (
                "results/l2_logistic_out_of_fold_predictions.csv",
                "Patient", "Actual_Response"
            ),
            (
                "results/lasso_out_of_fold_predictions.csv",
                "Patient", "Actual_Response"
            ),
            (
                "results/lasso_balanced_rf/oof_predictions.csv",
                "patient", "actual_class"
            )
        ]
        expected_labels = pd.Series(
            self.training_checkpoint["y"].to_numpy(),
            index=self.training_checkpoint["y"].index.astype(str)
        ).sort_index()

        for relative_path, patient_field, actual_field in prediction_specs:
            frame = self.read_csv(relative_path)
            patients = frame[patient_field].astype(str)

            if not patients.is_unique or set(patients) != expected_patients:
                raise ArtifactValidationError(
                    f"{relative_path} does not contain each training patient "
                    "exactly once."
                )

            labels = pd.Series(
                frame[actual_field].to_numpy(),
                index=patients
            ).sort_index()

            if not labels.equals(expected_labels):
                raise ArtifactValidationError(
                    f"{relative_path} actual labels conflict with GSE25055."
                )

        assignments = self.read_csv(
            "results/GSE25055_outer_fold_assignments.csv"
        )

        if (
            not assignments["Patient"].is_unique
            or set(assignments["Patient"].astype(str)) != expected_patients
            or sorted(assignments["validation_fold"].unique().tolist())
            != list(range(1, 11))
        ):
            raise ArtifactValidationError(
                "The shared outer-fold assignment artifact is inconsistent."
            )

        mapped_folds = pd.Series(
            index=self.training_checkpoint["y"].index,
            dtype="int64"
        )

        for fold, (_, validation_indices) in enumerate(
            self.balanced_experiment["outer_splits"], start=1
        ):
            mapped_folds.iloc[validation_indices] = fold

        stored_folds = (
            assignments.set_index("Patient")["validation_fold"]
            .reindex(mapped_folds.index)
        )

        if not np.array_equal(
            mapped_folds.to_numpy(dtype=int),
            stored_folds.to_numpy(dtype=int)
        ):
            raise ArtifactValidationError(
                "Balanced RF outer splits conflict with shared assignments."
            )

    def _validate_selected_features(self):
        root = self.read_csv("results/lasso_selected_probes_by_fold.csv")
        root_folds = self.read_csv("results/lasso_cv_fold_metrics.csv")
        root_counts = root.groupby("fold").size()
        stored_counts = root_folds.set_index("fold")["selected_probes"]

        if not root_counts.equals(stored_counts.astype(int)):
            raise ArtifactValidationError(
                "Root LASSO selected-probe counts conflict with fold metrics."
            )

        stability = self.read_csv(
            "results/lasso_feature_stability.csv"
        ).set_index("PROBEID")
        selection_counts = root.groupby("PROBEID")["fold"].nunique()

        if set(stability.index) != set(selection_counts.index):
            raise ArtifactValidationError(
                "Root LASSO stability probe set conflicts with fold selections."
            )

        if not np.array_equal(
            stability.loc[selection_counts.index, "selected_folds"].astype(int),
            selection_counts.astype(int)
        ):
            raise ArtifactValidationError(
                "Stored selected-fold counts conflict with fold selections."
            )

        if not np.allclose(
            stability.loc[selection_counts.index, "selection_frequency"],
            selection_counts / 10
        ):
            raise ArtifactValidationError(
                "Stored selection frequencies conflict with fold selections."
            )

        balanced = self.read_csv(
            "results/lasso_balanced_rf/selected_probes_by_fold.csv"
        )
        balanced_folds = self.read_csv(
            "results/lasso_balanced_rf/fold_results.csv"
        )
        balanced_counts = balanced.groupby("fold").size()
        model_counts = balanced_folds.groupby("fold")["selected_probes"]

        if not (
            (model_counts.nunique() == 1).all()
            and balanced_counts.equals(model_counts.first().astype(int))
        ):
            raise ArtifactValidationError(
                "Balanced RF selected-probe counts conflict with fold rows."
            )

    def _validate_final_results(self):
        package = self.final_package

        for field, expected in EXPECTED_FINAL.items():
            if clean_value(package[field]) != expected:
                raise ArtifactValidationError(
                    f"Final package field {field} conflicts with the "
                    f"expected locked value {expected}."
                )

        selected = self.read_csv(
            "results/final_model_gse25055/final_selected_probes.csv"
        )

        if list(selected["probe_id"]) != list(package["selected_probes"]):
            raise ArtifactValidationError(
                "Final selected-probe CSV order conflicts with the package."
            )

        if len(package["selected_probes"]) != package["selected_probe_count"]:
            raise ArtifactValidationError(
                "Final selected-probe count conflicts with the package list."
            )

        external = self.read_csv(
            "results/final_external_validation_gse25065/external_metrics.csv"
        )
        thresholds = dict(zip(external["model"], external["threshold"]))
        expected_thresholds = {
            "Custom Random Forest": package["custom_threshold"],
            "Sklearn Random Forest": package["sklearn_threshold"]
        }

        if thresholds != expected_thresholds:
            raise ArtifactValidationError(
                "External thresholds conflict with the final model package."
            )

        bundle = self.external_bundle

        if list(bundle["selected_probes"]) != list(package["selected_probes"]):
            raise ArtifactValidationError(
                "External bundle probe order conflicts with the final package."
            )

        if (
            bundle["training_dataset"] != package["training_dataset"]
            or bundle["external_dataset"] != package["external_dataset"]
        ):
            raise ArtifactValidationError(
                "External bundle dataset lineage conflicts with the package."
            )

    def _validate_phase2_records(self):
        external = self.read_csv(
            "results/final_external_validation_gse25065/"
            "external_predictions.csv"
        )
        expected_labels = pd.Series(
            self.external_checkpoint["y"].to_numpy(),
            index=self.external_checkpoint["y"].index.astype(str)
        ).sort_index()
        patients = external["patient"].astype(str)
        actual = pd.Series(
            external["actual_class"].to_numpy(),
            index=patients
        ).sort_index()

        if not patients.is_unique or not actual.equals(expected_labels):
            raise ArtifactValidationError(
                "External predictions do not contain each GSE25065 patient "
                "and label exactly once."
            )

        bundle_predictions = self.external_bundle["predictions"]

        if list(bundle_predictions.columns) != list(external.columns):
            raise ArtifactValidationError(
                "External CSV and Joblib prediction columns differ."
            )

        for column in external.columns:
            left = external[column]
            right = bundle_predictions[column]

            if pd.api.types.is_numeric_dtype(left):
                matches = np.allclose(left, right, atol=1e-12, rtol=0)
            else:
                matches = left.astype(str).equals(right.astype(str))

            if not matches:
                raise ArtifactValidationError(
                    f"External CSV and Joblib differ in {column}."
                )

        selections = self.read_csv(
            "results/lasso_selected_probes_by_fold.csv"
        )
        fold_sets = {
            int(fold): set(group["PROBEID"])
            for fold, group in selections.groupby("fold")
        }
        similarities = self.read_csv(
            "results/lasso_jaccard_stability.csv"
        )

        if len(similarities) != 45:
            raise ArtifactValidationError(
                "Expected 45 pairwise LASSO fold similarities."
            )

        for row in similarities.to_dict(orient="records"):
            left = fold_sets[int(row["fold_a"])]
            right = fold_sets[int(row["fold_b"])]
            shared = len(left & right)
            union = len(left | right)

            if (
                int(row["shared_probes"]) != shared
                or int(row["union_probes"]) != union
                or not np.isclose(
                    row["jaccard_similarity"], shared / union,
                    atol=1e-12, rtol=0
                )
            ):
                raise ArtifactValidationError(
                    "Stored Jaccard records conflict with fold selections."
                )

    def datasets(self):
        records = []

        for checkpoint, role, patient_key, excluded_key, source_path in [
            (
                self.training_checkpoint,
                "training_and_cross_validation",
                "number_of_modeling_patients",
                None,
                "data/GSE25055_pre_lasso.joblib"
            ),
            (
                self.external_checkpoint,
                self.external_checkpoint["role"],
                "number_of_validation_patients",
                "number_of_excluded_patients",
                "data/GSE25065_pre_lasso.joblib"
            )
        ]:
            x = checkpoint["X"]
            y = checkpoint["y"]
            included = len(x)
            original = int(checkpoint["number_of_original_patients"])
            excluded = (
                int(checkpoint[excluded_key])
                if excluded_key else original - included
            )
            distribution = {
                str(key): int(value)
                for key, value in y.value_counts().sort_index().items()
            }
            records.append({
                "accession": checkpoint["dataset_id"],
                "role": role,
                "included_patient_count": included,
                "original_patient_count": original,
                "excluded_patient_count": excluded,
                "feature_count": int(x.shape[1]),
                "label_mapping": checkpoint["label_mapping"],
                "class_distribution": distribution,
                "source_path": source_path,
                "methodology": METHODOLOGY_STEPS if role ==
                    "training_and_cross_validation" else [],
                "compatibility_metadata": (
                    self.external_compatibility_metadata()
                    if checkpoint["dataset_id"] == "GSE25065" else {}
                ),
                "provenance": {
                    "accession": "dataset_id",
                    "role": "role" if "role" in checkpoint else
                            "canonical lineage classification",
                    "included_patient_count": f"len(X), checked against {patient_key}",
                    "original_patient_count": "number_of_original_patients",
                    "excluded_patient_count": (
                        excluded_key
                        if excluded_key else
                        "number_of_original_patients - len(X)"
                    ),
                    "feature_count": "X.shape[1]",
                    "label_mapping": "label_mapping",
                    "class_distribution": "y.value_counts()",
                    "methodology": "traceable producing notebook sources"
                }
            })

        return records

    def annotations(self):
        source_path = "data/GSE25055_pre_lasso.joblib"
        annotation = self.training_checkpoint["gene_annotation"]

        for row in annotation.to_dict(orient="records"):
            mapping_status = clean_value(row.get("MAPPING_STATUS"))
            symbol = clean_value(row.get("SYMBOL"))
            number_of_genes = clean_value(row.get("NUMBER_OF_GENES"))

            if mapping_status is None:
                if symbol is None:
                    mapping_status = "No gene symbol"
                elif number_of_genes == 1:
                    mapping_status = "Unique"
                elif number_of_genes is not None and number_of_genes > 1:
                    mapping_status = "Multiple genes"
                else:
                    mapping_status = "Not available"

            yield {
                "probe_id": str(row["PROBEID"]),
                "gene_symbol": symbol,
                "gene_name": clean_value(row.get("GENENAME")),
                "entrez_id": (
                    None if clean_value(row.get("ENTREZID")) is None
                    else str(clean_value(row.get("ENTREZID")))
                ),
                "number_of_genes": (
                    None if number_of_genes is None else int(number_of_genes)
                ),
                "mapping_status": mapping_status,
                "source_path": source_path,
                "source_fields": {
                    "probe_id": "gene_annotation.PROBEID",
                    "gene_symbol": "gene_annotation.SYMBOL",
                    "gene_name": "gene_annotation.GENENAME",
                    "entrez_id": "gene_annotation.ENTREZID",
                    "number_of_genes": "gene_annotation.NUMBER_OF_GENES",
                    "mapping_status": "gene_annotation.MAPPING_STATUS"
                }
            }

    def selected_features(self):
        root_path = "results/lasso_selected_probes_by_fold.csv"
        stability_path = "results/lasso_feature_stability.csv"
        root = self.read_csv(root_path)
        stability = self.read_csv(stability_path)[[
            "PROBEID", "selected_folds", "selection_frequency",
            "mean_coefficient", "MODEL_DIRECTION"
        ]]
        root = root.merge(stability, on="PROBEID", how="left")

        for row in root.to_dict(orient="records"):
            yield {
                "experiment_slug": "lasso-logistic-nested-cv",
                "selection_context": "root_lasso_fold",
                "fold": int(row["fold"]),
                "probe_id": str(row["PROBEID"]),
                "coefficient": clean_value(row["coefficient"]),
                "mean_coefficient": clean_value(row["mean_coefficient"]),
                "selected_folds": int(row["selected_folds"]),
                "selection_frequency": clean_value(row["selection_frequency"]),
                "coefficient_direction": clean_value(row["MODEL_DIRECTION"]),
                "source_path": root_path,
                "source_fields": {
                    "fold": "fold",
                    "probe_id": "PROBEID",
                    "coefficient": "coefficient",
                    "mean_coefficient": {
                        "path": stability_path, "field": "mean_coefficient"
                    },
                    "selected_folds": {
                        "path": stability_path, "field": "selected_folds"
                    },
                    "selection_frequency": {
                        "path": stability_path, "field": "selection_frequency"
                    },
                    "coefficient_direction": {
                        "path": stability_path, "field": "MODEL_DIRECTION"
                    }
                }
            }

        balanced_path = (
            "results/lasso_balanced_rf/selected_probes_by_fold.csv"
        )
        balanced = self.read_csv(balanced_path)

        for row in balanced.to_dict(orient="records"):
            yield {
                "experiment_slug": "balanced-rf-nested-cv",
                "selection_context": "balanced_rf_fold_lasso",
                "fold": int(row["fold"]),
                "probe_id": str(row["probe_id"]),
                "coefficient": None,
                "mean_coefficient": None,
                "selected_folds": None,
                "selection_frequency": None,
                "coefficient_direction": None,
                "source_path": balanced_path,
                "source_fields": {
                    "fold": "fold",
                    "probe_id": "probe_id"
                }
            }

        final_path = "results/final_model_gse25055/final_selected_probes.csv"
        final = self.read_csv(final_path)

        for row in final.to_dict(orient="records"):
            coefficient = clean_value(row["lasso_coefficient"])
            yield {
                "experiment_slug": "final-model-gse25055",
                "selection_context": "full_training_lasso",
                "fold": None,
                "probe_id": str(row["probe_id"]),
                "coefficient": coefficient,
                "mean_coefficient": coefficient,
                "selected_folds": None,
                "selection_frequency": None,
                "coefficient_direction": (
                    "Higher value associated with pCR prediction"
                    if coefficient > 0 else
                    "Higher value associated with RD prediction"
                ),
                "source_path": final_path,
                "source_fields": {
                    "probe_id": "probe_id",
                    "coefficient": "lasso_coefficient",
                    "coefficient_direction": "derived from coefficient sign"
                }
            }

    def cv_sources(self):
        balanced = self.balanced_experiment
        shared_rf_configuration = {
            key: clean_value(balanced[key])
            for key in [
                "number_of_trees", "max_depth", "min_samples_split",
                "classification_threshold", "class_weight", "random_state",
                "outer_folds", "inner_folds", "lasso_parameter_grid"
            ]
        }

        return [
            {
                "experiment_slug": "l2-logistic-nested-cv",
                "model_key": "l2_logistic",
                "display_name": "L2 Logistic Regression",
                "model_family": "Logistic Regression (L2)",
                "fold_path": "results/l2_logistic_cv_fold_metrics.csv",
                "summary_path": "results/l2_logistic_cv_summary.csv",
                "comparison_path": "results/model_comparison.csv",
                "comparison_model": "L2 Logistic Regression",
                "configuration": {},
                "configuration_source": None
            },
            {
                "experiment_slug": "lasso-logistic-nested-cv",
                "model_key": "lasso_logistic",
                "display_name": "LASSO Logistic Regression",
                "model_family": "Logistic Regression (L1 feature selection)",
                "fold_path": "results/lasso_cv_fold_metrics.csv",
                "summary_path": "results/lasso_cv_summary.csv",
                "comparison_path": "results/model_comparison.csv",
                "comparison_model": "LASSO Logistic Regression",
                "configuration": {},
                "configuration_source": None
            },
            {
                "experiment_slug": "balanced-rf-nested-cv",
                "model_key": "custom_random_forest",
                "display_name": "Custom Random Forest",
                "model_family": "From-scratch Random Forest",
                "fold_path": "results/lasso_balanced_rf/fold_results.csv",
                "fold_model": "Custom Random Forest",
                "summary_path": None,
                "comparison_path":
                    "results/lasso_balanced_rf/model_comparison.csv",
                "comparison_model": "Custom Random Forest",
                "prediction_column": "custom_prediction",
                "configuration": shared_rf_configuration,
                "configuration_source":
                    "results/lasso_balanced_rf/experiment_results.joblib"
            },
            {
                "experiment_slug": "balanced-rf-nested-cv",
                "model_key": "sklearn_random_forest",
                "display_name": "Scikit-learn Random Forest",
                "model_family": "Matched Scikit-learn Random Forest",
                "fold_path": "results/lasso_balanced_rf/fold_results.csv",
                "fold_model": "Sklearn Random Forest",
                "summary_path": None,
                "comparison_path":
                    "results/lasso_balanced_rf/model_comparison.csv",
                "comparison_model": "Sklearn Random Forest",
                "prediction_column": "sklearn_prediction",
                "configuration": shared_rf_configuration,
                "configuration_source":
                    "results/lasso_balanced_rf/experiment_results.joblib"
            }
        ]

    def fold_results(self, source):
        frame = self.read_csv(source["fold_path"])

        if source.get("fold_model"):
            frame = frame[frame["model"] == source["fold_model"]]

        records = []

        for row in frame.to_dict(orient="records"):
            metrics, metric_fields = metric_values(row)
            selected_parameters = {}

            if "best_C" in row:
                selected_parameters["best_C"] = clean_value(row["best_C"])
                selected_parameters["best_class_weight"] = clean_value(
                    row["best_class_weight"]
                )

            records.append({
                "fold": int(row["fold"]),
                "training_patient_count": clean_value(
                    row.get("training_patients")
                ),
                "validation_patient_count": clean_value(
                    row.get("validation_patients")
                ),
                "selected_probe_count": clean_value(
                    row.get("selected_probes")
                ),
                "selected_parameters": selected_parameters,
                "metrics": metrics,
                "source_path": source["fold_path"],
                "source_fields": {
                    "fold": "fold",
                    "training_patient_count": (
                        "training_patients"
                        if "training_patients" in row else None
                    ),
                    "validation_patient_count": (
                        "validation_patients"
                        if "validation_patients" in row else None
                    ),
                    "selected_probe_count": (
                        "selected_probes" if "selected_probes" in row else None
                    ),
                    "selected_parameters": {
                        "best_C": "best_C",
                        "best_class_weight": "best_class_weight"
                    } if selected_parameters else {},
                    "metrics": metric_fields
                }
            })

        return records

    def cv_summary(self, source):
        if source["summary_path"]:
            frame = self.read_csv(source["summary_path"])
            metric_column = frame.columns[0]
            summary = {}
            source_fields = {}

            for row in frame.to_dict(orient="records"):
                source_metric = row[metric_column]
                api_metric = METRIC_FIELDS.get(source_metric)

                if api_metric:
                    summary[api_metric] = {
                        "mean": clean_value(row["Mean"]),
                        "std": clean_value(row["Standard deviation"])
                    }
                    source_fields[api_metric] = {
                        "metric_row": source_metric,
                        "mean": "Mean",
                        "std": "Standard deviation"
                    }

            return {
                "values": summary,
                "source_type": "direct",
                "source_path": source["summary_path"],
                "source_fields": source_fields,
                "derivation": None
            }

        frame = self.read_csv(source["fold_path"])
        frame = frame[frame["model"] == source["fold_model"]]
        summary = {}

        for source_metric, api_metric in METRIC_FIELDS.items():
            if source_metric in frame.columns:
                summary[api_metric] = {
                    "mean": clean_value(frame[source_metric].mean()),
                    "std": clean_value(frame[source_metric].std(ddof=1))
                }

        return {
            "values": summary,
            "source_type": "derived_during_import",
            "source_path": source["fold_path"],
            "source_fields": {
                key: {
                    "rows": f"model == {source['fold_model']}",
                    "field": next(
                        field for field, mapped in METRIC_FIELDS.items()
                        if mapped == key and field in frame.columns
                    )
                }
                for key in summary
            },
            "derivation": (
                "Arithmetic mean and sample standard deviation (ddof=1) "
                "over the model's 10 stored fold rows."
            )
        }

    def overall_result(self, source):
        frame = self.read_csv(source["comparison_path"])
        model_field = (
            "Model" if "Model" in frame.columns else "model"
        )
        row = frame[
            frame[model_field] == source["comparison_model"]
        ]

        if len(row) != 1:
            raise ArtifactValidationError(
                f"Expected one {source['comparison_model']} row in "
                f"{source['comparison_path']}."
            )

        record = row.iloc[0].to_dict()
        metrics, metric_fields = metric_values(record)
        confusion_fields = {
            "true_negative": "True negatives",
            "false_positive": "False positives",
            "false_negative": "False negatives",
            "true_positive": "True positives"
        }
        confusion = None

        if all(field in record for field in confusion_fields.values()):
            confusion = {
                key: int(record[field])
                for key, field in confusion_fields.items()
            }

        return {
            "metrics": metrics,
            "confusion_matrix": confusion,
            "source_path": source["comparison_path"],
            "source_fields": {
                "model": model_field,
                "metrics": metric_fields,
                "confusion_matrix": (
                    confusion_fields if confusion is not None else None
                )
            }
        }

    def cv_confusion(self, source, overall):
        if overall["confusion_matrix"] is not None:
            return {
                "values": overall["confusion_matrix"],
                "source_type": "direct",
                "source_path": overall["source_path"],
                "source_fields": overall["source_fields"]["confusion_matrix"],
                "derivation": None
            }

        prediction_path = "results/lasso_balanced_rf/oof_predictions.csv"
        predictions = self.read_csv(prediction_path)
        actual = predictions["actual_class"].astype(int)
        predicted = predictions[source["prediction_column"]].astype(int)

        return {
            "values": {
                "true_negative": int(((actual == 0) & (predicted == 0)).sum()),
                "false_positive": int(((actual == 0) & (predicted == 1)).sum()),
                "false_negative": int(((actual == 1) & (predicted == 0)).sum()),
                "true_positive": int(((actual == 1) & (predicted == 1)).sum())
            },
            "source_type": "derived_during_import",
            "source_path": prediction_path,
            "source_fields": {
                "actual": "actual_class",
                "predicted": source["prediction_column"]
            },
            "derivation": (
                "Counts of stored actual/predicted label pairs; "
                "probabilities and thresholds are not used."
            )
        }

    def final_configurations(self):
        package = self.final_package
        source_path = "results/final_model_gse25055/final_model_package.joblib"

        return {
            "custom_random_forest": {
                "configuration": {
                    **package["custom_rf_config"],
                    "classification_threshold": package["custom_threshold"],
                    "lasso_best_C": package["lasso_best_C"],
                    "selected_probe_count": package["selected_probe_count"]
                },
                "source_path": source_path,
                "source_fields": {
                    **{
                        key: f"custom_rf_config.{key}"
                        for key in package["custom_rf_config"]
                    },
                    "classification_threshold": "custom_threshold",
                    "lasso_best_C": "lasso_best_C",
                    "selected_probe_count": "selected_probe_count"
                }
            },
            "sklearn_random_forest": {
                "configuration": {
                    **package["sklearn_rf_config"],
                    "classification_threshold": package["sklearn_threshold"],
                    "lasso_best_C": package["lasso_best_C"],
                    "selected_probe_count": package["selected_probe_count"]
                },
                "source_path": source_path,
                "source_fields": {
                    **{
                        key: f"sklearn_rf_config.{key}"
                        for key in package["sklearn_rf_config"]
                    },
                    "classification_threshold": "sklearn_threshold",
                    "lasso_best_C": "lasso_best_C",
                    "selected_probe_count": "selected_probe_count"
                }
            }
        }

    def final_validation(self):
        source_path = (
            "results/final_external_validation_gse25065/external_metrics.csv"
        )
        frame = self.read_csv(source_path)
        model_keys = {
            "Custom Random Forest": "custom_random_forest",
            "Sklearn Random Forest": "sklearn_random_forest"
        }
        records = []

        for row in frame.to_dict(orient="records"):
            metrics, metric_fields = metric_values(row)
            records.append({
                "model_key": model_keys[row["model"]],
                "display_name": row["model"],
                "threshold": clean_value(row["threshold"]),
                "metrics": metrics,
                "confusion_matrix": {
                    "true_negative": int(row["tn"]),
                    "false_positive": int(row["fp"]),
                    "false_negative": int(row["fn"]),
                    "true_positive": int(row["tp"])
                },
                "source_path": source_path,
                "source_fields": {
                    "model": "model",
                    "threshold": "threshold",
                    "metrics": metric_fields,
                    "confusion_matrix": {
                        "true_negative": "tn",
                        "false_positive": "fp",
                        "false_negative": "fn",
                        "true_positive": "tp"
                    }
                }
            })

        return records

    def prediction_records(self):
        assignments = self.read_csv(
            "results/GSE25055_outer_fold_assignments.csv"
        ).set_index("Patient")["validation_fold"].to_dict()
        specifications = [
            {
                "path": "results/l2_logistic_out_of_fold_predictions.csv",
                "experiment_slug": "l2-logistic-nested-cv",
                "model_key": "l2_logistic",
                "patient": "Patient",
                "actual": "Actual_Response",
                "predicted": "Predicted_Response",
                "probability": "pCR_Probability",
                "folds": assignments,
            },
            {
                "path": "results/lasso_out_of_fold_predictions.csv",
                "experiment_slug": "lasso-logistic-nested-cv",
                "model_key": "lasso_logistic",
                "patient": "Patient",
                "actual": "Actual_Response",
                "predicted": "Predicted_Response",
                "probability": "pCR_Probability",
                "folds": assignments,
            },
        ]

        for model_key, predicted, probability in [
            (
                "custom_random_forest", "custom_prediction",
                "custom_probability"
            ),
            (
                "sklearn_random_forest", "sklearn_prediction",
                "sklearn_probability"
            ),
        ]:
            specifications.append({
                "path": "results/lasso_balanced_rf/oof_predictions.csv",
                "experiment_slug": "balanced-rf-nested-cv",
                "model_key": model_key,
                "patient": "patient",
                "actual": "actual_class",
                "predicted": predicted,
                "probability": probability,
                "folds": assignments,
            })
            specifications.append({
                "path": (
                    "results/final_external_validation_gse25065/"
                    "external_predictions.csv"
                ),
                "experiment_slug": "locked-external-validation-gse25065",
                "model_key": model_key,
                "patient": "patient",
                "actual": "actual_class",
                "predicted": predicted,
                "probability": probability,
                "folds": None,
            })

        records = []

        for specification in specifications:
            frame = self.read_csv(specification["path"])

            for row in frame.to_dict(orient="records"):
                patient_id = str(row[specification["patient"]])
                records.append({
                    "experiment_slug": specification["experiment_slug"],
                    "model_key": specification["model_key"],
                    "patient_id": patient_id,
                    "actual_class": int(row[specification["actual"]]),
                    "predicted_class": int(row[specification["predicted"]]),
                    "probability": float(row[specification["probability"]]),
                    "validation_fold": (
                        int(specification["folds"][patient_id])
                        if specification["folds"] is not None else None
                    ),
                    "source_path": specification["path"],
                    "source_fields": {
                        "patient_id": specification["patient"],
                        "actual_class": specification["actual"],
                        "predicted_class": specification["predicted"],
                        "probability": specification["probability"],
                        "validation_fold": (
                            "results/GSE25055_outer_fold_assignments.csv:"
                            "validation_fold"
                            if specification["folds"] is not None else None
                        ),
                    },
                })

        return records

    def fold_feature_similarities(self):
        source_path = "results/lasso_jaccard_stability.csv"
        frame = self.read_csv(source_path)

        return [
            {
                "experiment_slug": "lasso-logistic-nested-cv",
                "fold_a": int(row["fold_a"]),
                "fold_b": int(row["fold_b"]),
                "shared_probes": int(row["shared_probes"]),
                "union_probes": int(row["union_probes"]),
                "jaccard_similarity": float(row["jaccard_similarity"]),
                "source_path": source_path,
                "source_fields": {
                    field: field for field in [
                        "fold_a", "fold_b", "shared_probes",
                        "union_probes", "jaccard_similarity"
                    ]
                },
            }
            for row in frame.to_dict(orient="records")
        ]

    def external_compatibility_metadata(self):
        training_probes = list(self.training_checkpoint["X"].columns)
        external_probes = list(self.external_checkpoint["X"].columns)
        selected = list(self.final_package["selected_probes"])
        external_set = set(external_probes)
        scale = self.external_checkpoint.get("scale_comparison")

        return {
            "technical_check_only": True,
            "aligned_probe_count": len(external_probes),
            "probe_order_matches_development": (
                training_probes == external_probes
            ),
            "required_final_probe_count": len(selected),
            "missing_final_probes": [
                probe for probe in selected if probe not in external_set
            ],
            "scale_percentiles": (
                [
                    {
                        str(key): clean_value(value)
                        for key, value in row.items()
                    }
                    for row in scale.to_dict(orient="records")
                ]
                if scale is not None else []
            ),
            "source_paths": [
                "data/GSE25055_pre_lasso.joblib",
                "data/GSE25065_pre_lasso.joblib",
                "results/final_model_gse25055/final_model_package.joblib",
            ],
        }
