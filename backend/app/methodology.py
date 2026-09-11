METHODOLOGY_STEPS = [
    {
        "order": 1,
        "category": "Dataset preparation",
        "title": "Load GEO expression and clinical data",
        "detail": (
            "Load the stored GEO sources and retain Affymetrix probe-set "
            "IDs as feature identities."
        ),
        "source_path": "notebooks/01_data_preparation.ipynb",
        "source_cell": "data loading and preparation cells"
    },
    {
        "order": 2,
        "category": "Dataset preparation",
        "title": "Clean identifiers and align samples",
        "detail": (
            "Clean identifiers and align expression rows, clinical records "
            "and response labels by sample ID."
        ),
        "source_path": "notebooks/01_data_preparation.ipynb",
        "source_cell": "pre-checkpoint preparation cells"
    },
    {
        "order": 3,
        "category": "Dataset preparation",
        "title": "Map labels and exclude unusable samples",
        "detail": (
            "Map RD to 0 and pCR to 1 and exclude samples without a usable "
            "response label."
        ),
        "source_path": "data/GSE25055_pre_lasso.joblib",
        "source_cell": "label_mapping and aligned X/y fields"
    },
    {
        "order": 4,
        "category": "Dataset preparation",
        "title": "Run integrity and compatibility checks",
        "detail": (
            "Check finite values, unique identifiers, aligned X/y indices "
            "and compatible probe order."
        ),
        "source_path": "notebooks/GSE25065_data_preparation.ipynb",
        "source_cell": "compatibility checks and cells 22, 27"
    },
    {
        "order": 5,
        "category": "Fold-local model processing",
        "title": "Fit scaling inside the outer training fold",
        "detail": (
            "StandardScaler is part of each logistic pipeline and is fitted "
            "only with outer-training data."
        ),
        "source_path": "notebooks/02_lasso_cross_validation.ipynb",
        "source_cell": "cells 4-5"
    },
    {
        "order": 6,
        "category": "Fold-local model processing",
        "title": "Fit LASSO selection inside each outer fold",
        "detail": (
            "Search and non-zero coefficient selection use only outer-"
            "training data; validation data uses the fitted pipeline."
        ),
        "source_path": "notebooks/04_lasso_custom_random_forest.ipynb",
        "source_cell": "cells 0-1"
    },
    {
        "order": 7,
        "category": "Fold-local model processing",
        "title": "Train both Random Forest implementations",
        "detail": (
            "Train the custom and matched scikit-learn forests on each "
            "outer-training fold's selected probes."
        ),
        "source_path": "notebooks/04_lasso_custom_random_forest.ipynb",
        "source_cell": "cells 0-1"
    },
    {
        "order": 8,
        "category": "Cross-validation",
        "title": "Store out-of-fold predictions",
        "detail": (
            "Each development patient receives a probability only from the "
            "outer fold in which that patient was held out."
        ),
        "source_path": "results/lasso_balanced_rf/oof_predictions.csv",
        "source_cell": "stored canonical OOF prediction rows"
    },
    {
        "order": 9,
        "category": "Threshold selection",
        "title": "Select thresholds from GSE25055 OOF predictions",
        "detail": (
            "Candidate thresholds are evaluated using development-cohort OOF "
            "predictions only; GSE25065 is not opened for this selection."
        ),
        "source_path": "notebooks/05_final_model_external_validation.ipynb",
        "source_cell": "cell 2"
    },
    {
        "order": 10,
        "category": "Final training",
        "title": "Fit and lock the final GSE25055 package",
        "detail": (
            "Fit full-training LASSO and both final forests, then store the "
            "ordered probes, configurations and locked thresholds."
        ),
        "source_path": (
            "results/final_model_gse25055/final_model_package.joblib"
        ),
        "source_cell": "notebook 05, cells 3-5"
    },
    {
        "order": 11,
        "category": "Locked final evaluation",
        "title": "Evaluate the locked package on GSE25065 once",
        "detail": (
            "Use the stored probe order, models and thresholds without "
            "feature, parameter, model or threshold selection."
        ),
        "source_path": "notebooks/05_final_model_external_validation.ipynb",
        "source_cell": "cell 6"
    }
]
