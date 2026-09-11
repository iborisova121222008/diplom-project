# Bachelor's thesis experiment dashboard

This project is a research-results information system for inspecting stored
machine-learning experiments on the GSE25055 and GSE25065 gene-expression
datasets. It is not a clinical diagnostic tool and has no patient prediction
endpoint.

The machine-learning work remains offline. The web system imports existing,
trusted results and presents them without retraining models, regenerating
predictions, or changing thresholds.

## Architecture

```text
trusted CSV/XLSX/Joblib artifacts
        -> explicit idempotent importer
        -> native PostgreSQL
        -> read-only FastAPI REST API
        -> React/TypeScript dashboard
```

PostgreSQL stores small structured metadata, metrics, configurations,
selected probe IDs and display annotations. Full expression matrices, NumPy
arrays and fitted model objects remain in the existing artifacts.

## Project structure

```text
backend/     FastAPI API, SQLAlchemy schema, importer and system tests
frontend/    Preserved original React/TypeScript dashboard
frontend-v2/ Read-only post-experiment React/TypeScript dashboard
docs/        Experiment-lineage documentation
data/        Trusted dataset checkpoints (read-only)
notebooks/   Offline experimental workflow (read-only)
results/     Generated experiment artifacts (read-only)
src/models/  Custom tree and forest implementations (read-only)
```

## Canonical sources

The main dashboard uses:

- `data/GSE25055_pre_lasso.joblib`
- `data/GSE25065_pre_lasso.joblib`
- `results/GSE25055_outer_fold_assignments.csv`
- root `results/l2_logistic_*` files
- root LASSO CSV files and the two supporting LASSO workbooks
- `results/model_comparison.csv`
- `results/lasso_balanced_rf/*`
- `results/final_model_gse25055/*`
- `results/final_external_validation_gse25065/*`

The following historical branches never feed the main dashboard:

- `results/lasso_custom_rf_first_run/`
- `results/lasso_custom_rf_fold1_threshold_030_pilot/`
- root `results/library_rf_*` files

The root library RF is a separate experiment and is not the matched sklearn
RF from the balanced paired-RF experiment.

## Result semantics

The API keeps four result types distinct:

1. Per-fold GSE25055 cross-validation metrics.
2. Fold arithmetic mean and sample standard deviation.
3. Overall GSE25055 out-of-fold metrics.
4. Locked GSE25065 external-validation metrics.

L2 and root-LASSO summaries and overall OOF results are imported directly
from their stored summary/comparison files. Balanced-RF fold summaries are
calculated once by the importer from the model's ten stored fold rows:

```text
mean = arithmetic mean of the ten stored values
std  = sample standard deviation with ddof=1
```

Balanced-RF confusion counts are calculated once during import by counting
the stored `(actual_class, custom_prediction)` and
`(actual_class, sklearn_prediction)` label pairs. Probabilities are not used
and predictions are not regenerated. FastAPI and React only read the imported
values.

## Feature identities and annotation

Affymetrix probe-set IDs remain the actual feature identities. Gene symbol,
gene name, Entrez ID, number of genes and mapping status are stored as a
separate display-only annotation lookup.

Three selection contexts remain separate:

- root LASSO fold selections and stability values;
- balanced-RF fold-local LASSO selections;
- the ordered final 15-probe full-training selection.

The final 15 probes were produced by a new full-GSE25055 LASSO fit. They were
not obtained by filtering the 72-feature stability workbook.

## PostgreSQL prerequisites

Use the already-installed native PostgreSQL server at `localhost:5432`. The
expected database is `diplom_project` and the application user is
`diplom_app`. The project does not create the server, database, user or
password.

The complete connection URL is required through the process environment or
the ignored `backend/.env` file. There is no normal-runtime SQLite fallback.

Copy the placeholder file and edit only the ignored copy:

```powershell
Copy-Item backend\.env.example backend\.env
notepad backend\.env
```

Expected form inside `backend/.env`:

```text
DATABASE_URL=postgresql+psycopg://diplom_app:<password>@localhost:5432/diplom_project
FRONTEND_ORIGIN=http://localhost:5173
```

Never commit `backend/.env`. The root `.env`, `backend/.env`, and
`frontend/.env` are ignored.

## Manual setup and startup

Run these commands from a PowerShell terminal at the repository root.

### 1. Create the backend environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

### 2. Configure the local connection

```powershell
Copy-Item backend\.env.example backend\.env
notepad backend\.env
```

Enter the real password only in the ignored file.

### 3. Verify PostgreSQL manually

The following command prompts for the password and does not place it in the
command or source code:

```powershell
psql -h localhost -p 5432 -U diplom_app -d diplom_project -W -c "SELECT current_database(), current_user;"
```

### 4. Apply database migrations

For a new, empty application database:

```powershell
$env:PYTHONPATH = "backend"
python -m alembic -c alembic.ini upgrade head
```

For the approved existing database, verify its six-table baseline before
stamping it, then apply the additive migration:

```powershell
$env:PYTHONPATH = "backend"
python backend\scripts\verify_schema_baseline.py
python -m alembic -c alembic.ini stamp 0001_existing_schema
python -m alembic -c alembic.ini upgrade head
```

Do not stamp an empty or unverified database. The migrations preserve the six
scientific tables and add only `prediction_records` and
`fold_feature_similarity`; Alembic also owns its technical
`alembic_version` table.

### 5. Import canonical artifacts

```powershell
$env:PYTHONPATH = "backend"
python backend\scripts\import_results.py
```

The script validates all canonical paths, required columns/keys, patient and
fold integrity, final probe order and threshold consistency before changing
experiment rows. It then replaces only its five known experiment records in
one transaction. Failure rolls the transaction back. Repeated successful
runs do not create duplicate rows.

On an already imported, verified database, populate only the approved Phase 2
records without replacing the existing experiment rows:

```powershell
python backend\scripts\backfill_phase2_results.py
```

### 6. Start FastAPI

```powershell
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

### 7. Install and start the new dashboard in another PowerShell terminal

```powershell
Set-Location D:\diplom-project\frontend-v2
npm install
Copy-Item .env.example .env
npm run dev
```

## Local URLs

- API: `http://localhost:8000`
- Swagger/OpenAPI: `http://localhost:8000/docs`
- React dashboard: `http://localhost:5173`

## Read-only API

```text
GET /api/health
GET /api/datasets
GET /api/preprocessing
GET /api/features
GET /api/models
GET /api/cv-results
GET /api/comparison
GET /api/final-validation
GET /api/experiments
GET /api/predictions
GET /api/curves
GET /api/model-disagreements
GET /api/fold-feature-similarity
GET /api/feature-stability
GET /api/feature-heatmap
GET /api/reports
GET /api/exports/{report_key}
```

The API does not accept expression matrices, artifact paths or patient data.
It has no prediction route. It does not read scientific artifacts as a
runtime fallback when PostgreSQL is unavailable.

## Automated checks

Backend and existing ML tests use an isolated in-memory database configured
only by the test suite. They do not connect to native PostgreSQL:

```powershell
$env:PYTHONPATH = "backend"
$env:PYTHONDONTWRITEBYTECODE = "1"
python -m pytest backend\tests src\models\tests
```

Frontend checks:

```powershell
Set-Location frontend-v2
npm run lint
npm run typecheck
npm run build
```

## Reproducibility and leakage protections

- Joblib loading is restricted to a fixed project-owned allowlist.
- The API cannot accept user-supplied paths or Joblib files.
- Import validation happens before database replacement.
- Root and balanced LASSO feature contexts are stored separately.
- Historical, pilot and library-RF results are excluded.
- Stored overall OOF metrics are never labelled as fold means.
- GSE25065 is labelled external-validation only.
- Final probes, configurations and thresholds come from the locked final
  package and are checked against external results.
- GSE25065 does not change displayed model configuration.

## Final-validation locking

Threshold selection in the recorded workflow uses GSE25055 OOF predictions.
The final package stores the locked Custom RF and sklearn RF thresholds. The
importer verifies that `external_metrics.csv` uses the same values before it
imports the one-time GSE25065 results.

## Known limitations

- Artifact lineage is supported by stored metadata and notebook source, but
  the files do not contain cryptographic links to their producer notebooks.
- Alembic's baseline must be verified before an existing database is stamped;
  the verifier intentionally rejects missing tables, columns, or audited row
  counts.
- Joblib deserialization is safe only for the fixed, trusted repository
  artifacts because loading arbitrary Joblib files can execute code.
- The system reports experimental evidence; it does not establish clinical
  validity or performance outside the stored datasets.
