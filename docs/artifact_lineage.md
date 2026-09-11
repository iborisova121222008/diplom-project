# Canonical artifact lineage

The dashboard is based on immutable, already-generated experiment artifacts.
It does not execute notebooks, fit models, generate predictions or choose
thresholds.

## Canonical flow

```text
data/GSE25055_pre_lasso.joblib
├─> root L2 nested-CV results
├─> root LASSO nested-CV and stability results
└─> results/lasso_balanced_rf/experiment_results.joblib
      └─> GSE25055 OOF threshold selection
           └─> results/final_model_gse25055/final_model_package.joblib
                + data/GSE25065_pre_lasso.joblib
                └─> results/final_external_validation_gse25065/*
```

L2 and root LASSO are compatible by patient set and fold assignment, but they
are parallel experiment branches. The balanced paired-RF run also starts from
the GSE25055 checkpoint and performs its own fold-local LASSO configuration;
it does not consume the root LASSO selected-probe CSV.

## Direct and derived values

Direct values include dataset metadata, stored fold metrics, L2/LASSO CV
summaries, overall OOF comparison metrics, selected probe IDs and
coefficients, configurations in Joblib metadata, and final external metrics
and confusion counts.

Only these values are derived during import:

- dataset included count: `len(X)`;
- dataset feature count: `X.shape[1]`;
- class distribution: counts from checkpoint `y`;
- GSE25055 exclusion count: original count minus included count;
- balanced-RF CV mean: arithmetic mean of each model's ten stored fold rows;
- balanced-RF CV standard deviation: sample standard deviation with `ddof=1`;
- balanced-RF TN/FP/FN/TP: counts of stored actual/predicted OOF label pairs.

FastAPI and React do not recalculate these values.

## Experiment branches that remain separate

The canonical main comparison uses root L2, root LASSO, balanced Custom RF,
and the matched balanced sklearn RF. It excludes:

- `results/lasso_custom_rf_first_run/` — earlier threshold-0.5 experiment;
- `results/lasso_custom_rf_fold1_threshold_030_pilot/` — one-fold pilot;
- root `results/library_rf_*` — separate full-feature, tuned sklearn RF.

The root library RF and balanced sklearn RF share patients and folds but not
features, hyperparameters, threshold behavior, predictions or metrics.

## Final features and thresholds

The ordered final 15 probes come from a new full-GSE25055 LASSO fit stored in
the final package and `final_selected_probes.csv`. They are not a filtered
subset of `lasso_72_stable_features.xlsx`.

The balanced CV experiment stores threshold `0.30`. Final training stores
separate locked thresholds: Custom RF `0.21` and sklearn RF `0.35`. External
validation uses the final thresholds, not the CV threshold.

## External-validation isolation

Stored metadata labels GSE25065 as `external_validation_only`. Notebook source
shows threshold selection from GSE25055 OOF predictions and final LASSO/model
training on GSE25055. GSE25065 is used to check probe availability and then
for the one-time locked evaluation. Available evidence supports isolation,
but cannot independently prove what happened outside the stored source.

## Provenance limitations

- Duplicate LASSO notebooks contain equivalent export cells, so the precise
  producer of some root LASSO files cannot be distinguished.
- Some producer cells lack saved execution counts.
- CSV and Joblib DataFrames can differ around `1e-16` after decimal parsing.
- The external bundle stores a machine-specific absolute model-package path.
- Artifact hashes establish the current bytes, not their full prior history.
