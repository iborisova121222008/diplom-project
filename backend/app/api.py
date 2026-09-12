import csv
import io
import json
import math
from datetime import date

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import and_, exists, func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, aliased, selectinload
from sklearn.metrics import precision_recall_curve, roc_curve

from app.config import FRONTEND_ORIGINS, PROJECT_DIR
from app.artifacts import ArtifactReader
from app.database import get_session
from app.models import (
    Dataset,
    Experiment,
    FoldFeatureSimilarity,
    FoldMetric,
    ModelRun,
    PredictionRecord,
    ProbeAnnotation,
    SelectedFeature,
)
from app.schemas import (
    ComparisonResponse,
    CurvesResponse,
    CvModelResponse,
    DatasetResponse,
    ExpressionPreviewResponse,
    DisagreementPageResponse,
    ExperimentResponse,
    FeaturePageResponse,
    FeatureHeatmapResponse,
    FeatureStabilityResponse,
    FrequencyBucketResponse,
    FinalValidationResponse,
    FoldSimilarityResponse,
    ForestManifestResponse,
    ForestStructureResponse,
    HealthResponse,
    ModelResponse,
    PredictionPageResponse,
    PreprocessingStepResponse,
    ReportResponse,
)


TREE_ASSET_DIR = PROJECT_DIR / "backend/generated/tree_previews"
ARTIFACT_READER = ArtifactReader(PROJECT_DIR)



FEATURE_EXPERIMENTS = {
    "lasso-logistic-nested-cv",
    "balanced-rf-nested-cv",
    "final-model-gse25055"
}
CV_EXPERIMENTS = {
    "l2-logistic-nested-cv",
    "lasso-logistic-nested-cv",
    "balanced-rf-nested-cv"
}
MODEL_ORDER = {
    "l2_logistic": 1,
    "lasso_logistic": 2,
    "custom_random_forest": 3,
    "sklearn_random_forest": 4
}


app = FastAPI(
    title="Bachelor Thesis Experiment Dashboard API",
    version="1.0.0",
    description=(
        "Read-only access to imported, already-computed machine-learning "
        "results. No prediction or patient-data input is provided."
    )
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"]
)


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(_request, _error):
    return JSONResponse(
        status_code=503,
        content={
            "detail": (
                "The PostgreSQL result store is unavailable. Check the "
                "connection and run the canonical artifact importer."
            )
        }
    )


def require_experiment(session, slug):
    experiment = session.scalar(
        select(Experiment).where(Experiment.slug == slug)
    )

    if experiment is None:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Required experiment '{slug}' is unavailable. Run the "
                "canonical artifact importer."
            )
        )

    return experiment


def read_tree_manifest():
    path = TREE_ASSET_DIR / "manifest.json"
    if not path.is_file():
        raise HTTPException(503, "Generated locked-forest visualization metadata is unavailable.")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise HTTPException(503, "Generated locked-forest visualization metadata is invalid.") from error
    if manifest.get("tree_count") != 30 or manifest.get("custom_tree_count") != 30 or len(manifest.get("selected_probes", [])) != 15:
        raise HTTPException(503, "Generated locked-forest visualization metadata fails its contract.")
    return manifest


@app.get("/api/forest/manifest", response_model=ForestManifestResponse)
def forest_manifest():
    return read_tree_manifest()


@app.get("/api/forest/trees/{tree_index}", response_class=Response)
def forest_tree(tree_index: int):
    if tree_index < 1 or tree_index > 30:
        raise HTTPException(404, "Tree index must be between 1 and 30.")
    manifest = read_tree_manifest()
    record = next(
        (item for item in manifest["trees"] if item["tree_index"] == tree_index),
        None,
    )
    if record is None or record["asset"] != f"tree-{tree_index:02d}.svg":
        raise HTTPException(503, "Requested tree preview is not present in the verified manifest.")
    path = TREE_ASSET_DIR / record["asset"]
    if not path.is_file() or path.parent != TREE_ASSET_DIR:
        raise HTTPException(503, "Requested tree preview is unavailable.")
    return Response(
        content=path.read_text(encoding="utf-8"),
        media_type="image/svg+xml",
        headers={"Content-Disposition": f'inline; filename="locked-sklearn-tree-{tree_index:02d}.svg"'},
    )


def _custom_tree_details(root):
    maximum_depth = 0
    node_count = 0
    stack = [(root, 0)]
    while stack:
        node, depth = stack.pop()
        node_count += 1
        maximum_depth = max(maximum_depth, depth)
        if node.left is not None:
            stack.append((node.left, depth + 1))
        if node.right is not None:
            stack.append((node.right, depth + 1))
    return maximum_depth, node_count


@app.get("/api/forest/structure", response_model=ForestStructureResponse)
def forest_structure(
    implementation: str = Query(default="custom", pattern="^(custom|sklearn)$"),
    tree_index: int = Query(default=1, ge=1, le=30),
    visible_depth: int = Query(default=3, ge=1, le=6),
):
    package = ARTIFACT_READER.final_package
    probes = [str(value) for value in package["selected_probes"]]
    nodes = []
    if implementation == "custom":
        root = package["custom_random_forest"][tree_index - 1]
        full_depth, full_node_count = _custom_tree_details(root)
        stack = [(root, None, None, 0, 0)]
        while stack:
            node, parent_id, branch, depth, position = stack.pop()
            node_id = len(nodes)
            leaf = node.left is None and node.right is None
            feature_index = int(node.feature_index) if not leaf else -1
            nodes.append({
                "node_id": node_id, "parent_id": parent_id, "branch": branch,
                "depth": depth, "position": position,
                "probe_id": probes[feature_index] if feature_index >= 0 else None,
                "split_value": float(node.threshold) if feature_index >= 0 else None,
                "probability": float(node.probability),
                "prediction": int(node.prediction), "leaf": leaf,
            })
            if depth < visible_depth:
                if node.right is not None:
                    stack.append((node.right, node_id, "right", depth + 1, position * 2 + 1))
                if node.left is not None:
                    stack.append((node.left, node_id, "left", depth + 1, position * 2))
    else:
        estimator = package["sklearn_random_forest"].estimators_[tree_index - 1]
        tree = estimator.tree_
        full_depth, full_node_count = int(tree.max_depth), int(tree.node_count)
        stack = [(0, None, None, 0, 0)]
        while stack:
            raw_id, parent_id, branch, depth, position = stack.pop()
            node_id = len(nodes)
            feature_index = int(tree.feature[raw_id])
            leaf = feature_index < 0
            class_values = tree.value[raw_id][0]
            total = float(class_values.sum())
            probability = float(class_values[1] / total) if total else 0.0
            nodes.append({
                "node_id": node_id, "parent_id": parent_id, "branch": branch,
                "depth": depth, "position": position,
                "probe_id": probes[feature_index] if feature_index >= 0 else None,
                "split_value": float(tree.threshold[raw_id]) if feature_index >= 0 else None,
                "probability": probability,
                "prediction": int(class_values.argmax()), "leaf": leaf,
            })
            if not leaf and depth < visible_depth:
                stack.append((int(tree.children_right[raw_id]), node_id, "right", depth + 1, position * 2 + 1))
                stack.append((int(tree.children_left[raw_id]), node_id, "left", depth + 1, position * 2))
    return {
        "implementation": implementation, "tree_index": tree_index,
        "visible_depth": visible_depth, "full_depth": full_depth,
        "full_node_count": full_node_count, "nodes": nodes,
    }


@app.get("/api/health", response_model=HealthResponse)
def health(session: Session = Depends(get_session)):
    session.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "database": "connected",
        "mode": "read_only_results"
    }


@app.get("/api/datasets", response_model=list[DatasetResponse])
def datasets(session: Session = Depends(get_session)):
    records = session.scalars(
        select(Dataset).order_by(Dataset.accession)
    ).all()

    if not records:
        raise HTTPException(503, "No imported dataset records are available.")

    return records


def _expression_window(
    dataset: str,
    patient_search: str | None,
    probe_search: str | None,
    row_offset: int,
    row_limit: int,
    column_offset: int,
    column_limit: int,
):
    checkpoints = {
        "GSE25055": ARTIFACT_READER.training_checkpoint,
        "GSE25065": ARTIFACT_READER.external_checkpoint,
    }
    if dataset not in checkpoints:
        raise HTTPException(400, "Unknown dataset.")
    frame = checkpoints[dataset]["X"]
    if patient_search and patient_search.strip():
        needle = patient_search.strip().casefold()
        frame = frame.loc[
            [needle in str(index).casefold() for index in frame.index]
        ]
    if probe_search and probe_search.strip():
        needle = probe_search.strip().casefold()
        frame = frame.loc[:, [
            needle in str(column).casefold() for column in frame.columns
        ]]
    patients = [str(value) for value in frame.index]
    probes = [str(value) for value in frame.columns]
    window = frame.iloc[
        row_offset:row_offset + row_limit,
        column_offset:column_offset + column_limit,
    ]
    return {
        "dataset": dataset,
        "total_patients": len(patients),
        "total_probes": len(probes),
        "row_offset": row_offset,
        "column_offset": column_offset,
        "patients": [str(value) for value in window.index],
        "probes": [str(value) for value in window.columns],
        "values": [[float(value) for value in row] for row in window.to_numpy()],
    }


@app.get("/api/expression-preview", response_model=ExpressionPreviewResponse)
def expression_preview(
    dataset: str = Query(default="GSE25055", pattern="^GSE250(55|65)$"),
    patient_search: str | None = Query(default=None, max_length=64),
    probe_search: str | None = Query(default=None, max_length=64),
    row_offset: int = Query(default=0, ge=0, le=500),
    row_limit: int = Query(default=8, ge=1, le=20),
    column_offset: int = Query(default=0, ge=0, le=22282),
    column_limit: int = Query(default=8, ge=1, le=20),
):
    return _expression_window(
        dataset, patient_search, probe_search, row_offset, row_limit,
        column_offset, column_limit,
    )


@app.get("/api/expression-preview/export", response_class=Response)
def export_expression_preview(
    dataset: str = Query(default="GSE25055", pattern="^GSE250(55|65)$"),
    format: str = Query(default="csv", pattern="^(csv|xlsx)$"),
    patient_search: str | None = Query(default=None, max_length=64),
    probe_search: str | None = Query(default=None, max_length=64),
    row_offset: int = Query(default=0, ge=0, le=500),
    row_limit: int = Query(default=8, ge=1, le=20),
    column_offset: int = Query(default=0, ge=0, le=22282),
    column_limit: int = Query(default=8, ge=1, le=20),
):
    payload = _expression_window(
        dataset, patient_search, probe_search, row_offset, row_limit,
        column_offset, column_limit,
    )
    frame = pd.DataFrame(
        payload["values"], index=payload["patients"], columns=payload["probes"]
    )
    frame.index.name = "patient_id"
    if format == "xlsx":
        binary = io.BytesIO()
        with pd.ExcelWriter(binary, engine="openpyxl") as writer:
            frame.to_excel(writer, sheet_name="expression_window")
        content = binary.getvalue()
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        content = frame.to_csv()
        media_type = "text/csv; charset=utf-8"
    return Response(content=content, media_type=media_type, headers={
        "Content-Disposition": f'attachment; filename="{dataset}-expression-window.{format}"'
    })


@app.get("/api/preprocessing", response_model=list[PreprocessingStepResponse])
def preprocessing(session: Session = Depends(get_session)):
    dataset = session.scalar(
        select(Dataset).where(Dataset.accession == "GSE25055")
    )

    if dataset is None or not dataset.methodology:
        raise HTTPException(503, "Imported methodology records are unavailable.")

    return dataset.methodology


@app.get("/api/features", response_model=FeaturePageResponse)
def features(
    experiment: str = Query(default="lasso-logistic-nested-cv"),
    fold: int | None = Query(default=None, ge=1, le=10),
    search: str | None = Query(default=None, max_length=100),
    sort_by: str = Query(default="probe_id"),
    sort_order: str = Query(default="asc", pattern="^(asc|desc)$"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session)
):
    if experiment not in FEATURE_EXPERIMENTS:
        raise HTTPException(400, "Unknown or non-canonical feature experiment.")

    experiment_record = require_experiment(session, experiment)
    query = (
        select(SelectedFeature, ProbeAnnotation)
        .join(ProbeAnnotation)
        .where(SelectedFeature.experiment_id == experiment_record.id)
    )
    count_query = (
        select(func.count(SelectedFeature.id))
        .select_from(SelectedFeature)
        .join(ProbeAnnotation)
        .where(SelectedFeature.experiment_id == experiment_record.id)
    )

    if fold is not None:
        query = query.where(SelectedFeature.fold == fold)
        count_query = count_query.where(SelectedFeature.fold == fold)

    if search and search.strip():
        pattern = f"%{search.strip()}%"
        search_filter = (
            SelectedFeature.probe_id.ilike(pattern)
            | ProbeAnnotation.gene_symbol.ilike(pattern)
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    sort_columns = {
        "probe_id": SelectedFeature.probe_id,
        "fold": SelectedFeature.fold,
        "selection_frequency": SelectedFeature.selection_frequency,
        "mean_coefficient": SelectedFeature.mean_coefficient,
        "gene_symbol": ProbeAnnotation.gene_symbol,
    }

    if sort_by not in sort_columns:
        raise HTTPException(400, "Unknown feature sort field.")

    sort_column = sort_columns[sort_by]
    ordering = sort_column.desc() if sort_order == "desc" else sort_column.asc()
    final_experiment = require_experiment(session, "final-model-gse25055")
    final_probes = set(session.scalars(
        select(SelectedFeature.probe_id).where(
            SelectedFeature.experiment_id == final_experiment.id
        )
    ))

    total = session.scalar(count_query) or 0
    rows = session.execute(
        query.order_by(ordering, SelectedFeature.probe_id)
        .offset(offset).limit(limit)
    ).all()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": [
            {
                "experiment_slug": experiment_record.slug,
                "experiment_name": experiment_record.name,
                "selection_context": feature.selection_context,
                "fold": feature.fold,
                "probe_id": feature.probe_id,
                "coefficient": feature.coefficient,
                "mean_coefficient": feature.mean_coefficient,
                "selected_folds": feature.selected_folds,
                "selection_frequency": feature.selection_frequency,
                "coefficient_direction": feature.coefficient_direction,
                "final_model_member": feature.probe_id in final_probes,
                "source_path": feature.source_path,
                "source_fields": feature.source_fields,
                "annotation": {
                    "gene_symbol": annotation.gene_symbol,
                    "gene_name": annotation.gene_name,
                    "entrez_id": annotation.entrez_id,
                    "number_of_genes": annotation.number_of_genes,
                    "mapping_status": annotation.mapping_status,
                    "display_only": True,
                    "source_path": annotation.source_path
                }
            }
            for feature, annotation in rows
        ]
    }


@app.get("/api/models", response_model=list[ModelResponse])
def models(session: Session = Depends(get_session)):
    cv_runs = session.scalars(
        select(ModelRun).join(Experiment)
        .where(Experiment.slug.in_(CV_EXPERIMENTS))
        .options(
            selectinload(ModelRun.experiment),
            selectinload(ModelRun.fold_metrics)
        )
    ).all()
    final_experiment = require_experiment(session, "final-model-gse25055")
    final_runs = {
        run.model_key: run
        for run in session.scalars(
            select(ModelRun).where(
                ModelRun.experiment_id == final_experiment.id
            )
        )
    }

    if len(cv_runs) != 4:
        raise HTTPException(503, "The four canonical models are unavailable.")

    response = []

    for run in sorted(cv_runs, key=lambda item: MODEL_ORDER[item.model_key]):
        final_run = final_runs.get(run.model_key)
        per_fold_parameters = [
            {
                "fold": fold.fold,
                "values": fold.selected_parameters,
                "source_path": fold.source_path
            }
            for fold in sorted(run.fold_metrics, key=lambda item: item.fold)
            if fold.selected_parameters
        ]
        unavailable = []

        if not run.configuration:
            unavailable.append(
                "Global CV configuration; stored per-fold selections are shown."
            )

        if final_run is None:
            unavailable.append("Final locked configuration is not applicable.")

        response.append({
            "model_key": run.model_key,
            "display_name": run.display_name,
            "model_family": run.model_family,
            "cv_experiment": run.experiment.name,
            "cv_configuration": run.configuration,
            "cv_configuration_source": run.configuration_source_path,
            "per_fold_parameters": per_fold_parameters,
            "final_configuration": (
                final_run.configuration if final_run else None
            ),
            "final_configuration_source": (
                final_run.configuration_source_path if final_run else None
            ),
            "unavailable_fields": unavailable
        })

    return response


@app.get("/api/cv-results", response_model=list[CvModelResponse])
def cv_results(
    model: str | None = None,
    session: Session = Depends(get_session)
):
    query = (
        select(ModelRun).join(Experiment)
        .where(Experiment.slug.in_(CV_EXPERIMENTS))
        .options(
            selectinload(ModelRun.experiment).selectinload(Experiment.dataset),
            selectinload(ModelRun.fold_metrics)
        )
    )

    if model:
        query = query.where(ModelRun.model_key == model)

    runs = session.scalars(query).all()

    if not runs:
        raise HTTPException(503, "Cross-validation results are unavailable.")

    return [
        {
            "model_key": run.model_key,
            "model": run.display_name,
            "experiment_slug": run.experiment.slug,
            "experiment_name": run.experiment.name,
            "dataset": run.experiment.dataset.accession,
            "folds": [
                {
                    "fold": fold.fold,
                    "training_patient_count": fold.training_patient_count,
                    "validation_patient_count": fold.validation_patient_count,
                    "selected_probe_count": fold.selected_probe_count,
                    "selected_parameters": fold.selected_parameters,
                    "metrics": fold.metrics,
                    "result_type": "per_fold_cv",
                    "source_path": fold.source_path,
                    "source_fields": fold.source_fields
                }
                for fold in sorted(run.fold_metrics, key=lambda item: item.fold)
            ],
            "summary": {
                "metrics": run.cv_summary,
                "result_type": "fold_mean_and_sample_standard_deviation",
                "source_type": run.cv_summary_source_type,
                "source_path": run.cv_summary_source_path,
                "source_fields": run.cv_summary_source_fields,
                "derivation": run.cv_summary_derivation
            },
            "confusion_matrix": {
                "values": run.confusion_matrix,
                "result_type": "cv_oof_confusion_counts",
                "source_type": run.confusion_source_type,
                "source_path": run.confusion_source_path,
                "source_fields": run.confusion_source_fields,
                "derivation": run.confusion_derivation
            }
        }
        for run in sorted(runs, key=lambda item: MODEL_ORDER[item.model_key])
    ]


@app.get("/api/comparison", response_model=list[ComparisonResponse])
def comparison(session: Session = Depends(get_session)):
    runs = session.scalars(
        select(ModelRun).join(Experiment)
        .where(Experiment.slug.in_(CV_EXPERIMENTS))
        .options(
            selectinload(ModelRun.experiment).selectinload(Experiment.dataset)
        )
    ).all()

    if len(runs) != 4:
        raise HTTPException(503, "The four overall OOF results are unavailable.")

    return [
        {
            "model_key": run.model_key,
            "model": run.display_name,
            "experiment_slug": run.experiment.slug,
            "dataset": run.experiment.dataset.accession,
            "result_type": "overall_oof",
            "metrics": run.overall_metrics,
            "source_path": run.overall_source_path,
            "source_fields": run.overall_source_fields
        }
        for run in sorted(runs, key=lambda item: MODEL_ORDER[item.model_key])
    ]


@app.get("/api/final-validation", response_model=FinalValidationResponse)
def final_validation(session: Session = Depends(get_session)):
    experiment = require_experiment(
        session, "locked-external-validation-gse25065"
    )
    runs = session.scalars(
        select(ModelRun).where(ModelRun.experiment_id == experiment.id)
        .order_by(ModelRun.id)
    ).all()

    if len(runs) != 2:
        raise HTTPException(503, "External-validation results are unavailable.")

    return {
        "experiment": experiment.name,
        "experiment_slug": experiment.slug,
        "dataset": experiment.dataset.accession,
        "dataset_role": experiment.dataset.role,
        "locked": experiment.locked,
        "result_type": "locked_external_validation",
        "evaluated_at": experiment.created_at,
        "source_path": experiment.source_path,
        "isolation_statement": (
            "GSE25065 is external-validation only and was not used for "
            "feature, hyperparameter, model or threshold selection."
        ),
        "models": [
            {
                "model_key": run.model_key,
                "model": run.display_name,
                "threshold": run.configuration["classification_threshold"],
                "configuration": run.configuration,
                "metrics": run.overall_metrics,
                "confusion_matrix": run.confusion_matrix,
                "source_path": run.overall_source_path,
                "source_fields": run.overall_source_fields
            }
            for run in runs
        ]
    }


@app.get("/api/experiments", response_model=list[ExperimentResponse])
def experiments(
    dataset: str | None = None,
    evaluation_stage: str | None = None,
    model: str | None = None,
    locked: bool | None = None,
    session: Session = Depends(get_session),
):
    query = select(Experiment).options(
        selectinload(Experiment.dataset),
        selectinload(Experiment.model_runs).selectinload(ModelRun.fold_metrics),
    )

    if dataset:
        query = query.join(Dataset).where(Dataset.accession == dataset)
    if evaluation_stage:
        query = query.where(Experiment.evaluation_stage == evaluation_stage)
    if model:
        query = query.join(ModelRun).where(ModelRun.model_key == model)
    if locked is not None:
        query = query.where(Experiment.locked == locked)

    records = session.scalars(query.order_by(Experiment.id)).unique().all()

    return [
        {
            "slug": experiment.slug,
            "name": experiment.name,
            "dataset": experiment.dataset.accession,
            "evaluation_stage": experiment.evaluation_stage,
            "result_scope": experiment.result_scope,
            "locked": experiment.locked,
            "status": "locked" if experiment.locked else "completed",
            "source_path": experiment.source_path,
            "created_at": experiment.created_at,
            "models": [
                {
                    "model_key": run.model_key,
                    "display_name": run.display_name,
                    "model_family": run.model_family,
                    "configuration": run.configuration,
                    "configuration_source_path": run.configuration_source_path,
                    "overall_metrics": run.overall_metrics,
                    "fold_count": len(run.fold_metrics),
                }
                for run in sorted(
                    experiment.model_runs,
                    key=lambda item: MODEL_ORDER.get(item.model_key, 99)
                )
            ],
        }
        for experiment in records
    ]


@app.get("/api/predictions", response_model=PredictionPageResponse)
def predictions(
    experiment: str,
    model: str | None = None,
    actual_class: int | None = Query(default=None, ge=0, le=1),
    predicted_class: int | None = Query(default=None, ge=0, le=1),
    correct: bool | None = None,
    disagreement: bool | None = None,
    minimum_probability: float | None = Query(default=None, ge=0, le=1),
    maximum_probability: float | None = Query(default=None, ge=0, le=1),
    fold: int | None = Query(default=None, ge=1, le=10),
    search: str | None = Query(default=None, max_length=64),
    sort_by: str = Query(default="probability", pattern="^(patient_id|probability|actual_class|predicted_class)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    session: Session = Depends(get_session),
):
    query = (
        select(PredictionRecord, ModelRun, Experiment)
        .join(ModelRun, PredictionRecord.model_run_id == ModelRun.id)
        .join(Experiment, ModelRun.experiment_id == Experiment.id)
        .where(Experiment.slug == experiment)
    )
    other_prediction = aliased(PredictionRecord)
    other_run = aliased(ModelRun)
    disagreement_exists = exists(
        select(1)
        .select_from(other_prediction)
        .join(other_run, other_prediction.model_run_id == other_run.id)
        .where(
            other_prediction.patient_id == PredictionRecord.patient_id,
            other_run.experiment_id == Experiment.id,
            other_prediction.model_run_id != PredictionRecord.model_run_id,
            other_prediction.predicted_class != PredictionRecord.predicted_class,
        )
    )
    count_query = (
        select(func.count(PredictionRecord.id))
        .join(ModelRun, PredictionRecord.model_run_id == ModelRun.id)
        .join(Experiment, ModelRun.experiment_id == Experiment.id)
        .where(Experiment.slug == experiment)
    )

    filters = []
    if model:
        filters.append(ModelRun.model_key == model)
    if actual_class is not None:
        filters.append(PredictionRecord.actual_class == actual_class)
    if predicted_class is not None:
        filters.append(PredictionRecord.predicted_class == predicted_class)
    if correct is not None:
        comparison_filter = PredictionRecord.actual_class == PredictionRecord.predicted_class
        filters.append(comparison_filter if correct else ~comparison_filter)
    if minimum_probability is not None:
        filters.append(PredictionRecord.probability >= minimum_probability)
    if maximum_probability is not None:
        filters.append(PredictionRecord.probability <= maximum_probability)
    if fold is not None:
        filters.append(PredictionRecord.validation_fold == fold)
    if search and search.strip():
        filters.append(PredictionRecord.patient_id.ilike(f"%{search.strip()}%"))
    if disagreement is not None:
        filters.append(disagreement_exists if disagreement else ~disagreement_exists)
    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)

    sort_columns = {
        "patient_id": PredictionRecord.patient_id,
        "probability": PredictionRecord.probability,
        "actual_class": PredictionRecord.actual_class,
        "predicted_class": PredictionRecord.predicted_class,
    }
    sort_column = sort_columns[sort_by]
    ordering = sort_column.desc() if sort_order == "desc" else sort_column.asc()
    rows = session.execute(
        query.order_by(ordering, PredictionRecord.patient_id)
        .offset(offset).limit(limit)
    ).all()

    total = session.scalar(count_query) or 0
    correct_count = session.scalar(count_query.where(
        PredictionRecord.actual_class == PredictionRecord.predicted_class
    )) or 0
    disagreement_count = session.scalar(
        count_query.where(disagreement_exists)
    ) or 0
    return {
        "total": total,
        "correct": correct_count,
        "incorrect": total - correct_count,
        "disagreements": disagreement_count,
        "offset": offset,
        "limit": limit,
        "items": [
            {
                "experiment_slug": experiment_record.slug,
                "model_key": run.model_key,
                "model": run.display_name,
                "patient_id": prediction.patient_id,
                "actual_class": prediction.actual_class,
                "predicted_class": prediction.predicted_class,
                "probability": prediction.probability,
                "validation_fold": prediction.validation_fold,
                "source_path": prediction.source_path,
            }
            for prediction, run, experiment_record in rows
        ],
    }


@app.get("/api/curves", response_model=CurvesResponse)
def curves(
    experiment: str,
    session: Session = Depends(get_session),
):
    experiment_record = require_experiment(session, experiment)
    runs = session.scalars(
        select(ModelRun).where(ModelRun.experiment_id == experiment_record.id)
        .order_by(ModelRun.id)
    ).all()
    models = []

    for run in runs:
        records = session.scalars(
            select(PredictionRecord).where(
                PredictionRecord.model_run_id == run.id
            ).order_by(PredictionRecord.patient_id)
        ).all()
        if not records:
            continue

        actual = [record.actual_class for record in records]
        probabilities = [record.probability for record in records]
        false_positive_rate, true_positive_rate, roc_thresholds = roc_curve(
            actual, probabilities
        )
        precision, recall, pr_thresholds = precision_recall_curve(
            actual, probabilities
        )
        bins = []
        for index in range(10):
            lower = index / 10
            upper = (index + 1) / 10
            in_bin = [
                record for record in records
                if lower <= record.probability < upper
                or (index == 9 and record.probability == 1)
            ]
            bins.append({
                "lower": lower,
                "upper": upper,
                "rd_count": sum(item.actual_class == 0 for item in in_bin),
                "pcr_count": sum(item.actual_class == 1 for item in in_bin),
            })

        models.append({
            "model_key": run.model_key,
            "model": run.display_name,
            "roc": [
                {
                    "x": float(x),
                    "y": float(y),
                    "threshold": (
                        float(threshold) if math.isfinite(threshold) else None
                    ),
                }
                for x, y, threshold in zip(
                    false_positive_rate, true_positive_rate, roc_thresholds
                )
            ],
            "precision_recall": [
                {
                    "x": float(x),
                    "y": float(y),
                    "threshold": (
                        float(pr_thresholds[index])
                        if index < len(pr_thresholds) else None
                    ),
                }
                for index, (x, y) in enumerate(zip(recall, precision))
            ],
            "probability_distribution": bins,
            "source_path": records[0].source_path,
        })

    if not models:
        raise HTTPException(503, "Stored prediction records are unavailable.")

    return {
        "experiment_slug": experiment,
        "result_type": (
            "locked_external_validation_curves"
            if experiment_record.evaluation_stage == "external_validation"
            else "out_of_fold_curves"
        ),
        "models": models,
    }


@app.get(
    "/api/model-disagreements",
    response_model=DisagreementPageResponse
)
def model_disagreements(
    experiment: str = "balanced-rf-nested-cv",
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    session: Session = Depends(get_session),
):
    experiment_record = require_experiment(session, experiment)
    runs = session.scalars(
        select(ModelRun).where(ModelRun.experiment_id == experiment_record.id)
        .order_by(ModelRun.id)
    ).all()

    if len(runs) != 2:
        raise HTTPException(400, "This experiment has no paired model results.")

    left = aliased(PredictionRecord)
    right = aliased(PredictionRecord)
    condition = and_(
        left.patient_id == right.patient_id,
        left.model_run_id == runs[0].id,
        right.model_run_id == runs[1].id,
        left.predicted_class != right.predicted_class,
    )
    count_query = select(func.count()).select_from(left).join(right, condition)
    query = (
        select(left, right)
        .join(right, condition)
        .order_by(left.patient_id)
        .offset(offset).limit(limit)
    )
    rows = session.execute(query).all()

    return {
        "total": session.scalar(count_query) or 0,
        "offset": offset,
        "limit": limit,
        "items": [
            {
                "patient_id": left_record.patient_id,
                "actual_class": left_record.actual_class,
                "left_model_key": runs[0].model_key,
                "left_prediction": left_record.predicted_class,
                "left_probability": left_record.probability,
                "right_model_key": runs[1].model_key,
                "right_prediction": right_record.predicted_class,
                "right_probability": right_record.probability,
            }
            for left_record, right_record in rows
        ],
    }


@app.get(
    "/api/fold-feature-similarity",
    response_model=list[FoldSimilarityResponse]
)
def fold_feature_similarity(session: Session = Depends(get_session)):
    records = session.execute(
        select(FoldFeatureSimilarity, Experiment)
        .join(Experiment)
        .order_by(FoldFeatureSimilarity.fold_a, FoldFeatureSimilarity.fold_b)
    ).all()
    return [
        {
            "experiment_slug": experiment.slug,
            "fold_a": item.fold_a,
            "fold_b": item.fold_b,
            "shared_probes": item.shared_probes,
            "union_probes": item.union_probes,
            "jaccard_similarity": item.jaccard_similarity,
            "source_path": item.source_path,
        }
        for item, experiment in records
    ]


def _final_probe_ids(session):
    final_experiment = require_experiment(session, "final-model-gse25055")
    return set(session.scalars(
        select(SelectedFeature.probe_id).where(
            SelectedFeature.experiment_id == final_experiment.id
        )
    ))


@app.get(
    "/api/feature-stability",
    response_model=list[FeatureStabilityResponse]
)
def feature_stability(
    search: str | None = Query(default=None, max_length=100),
    minimum_frequency: int = Query(default=1, ge=1, le=10),
    final_only: bool = False,
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    experiment = require_experiment(session, "lasso-logistic-nested-cv")
    query = (
        select(
            SelectedFeature.probe_id,
            ProbeAnnotation.gene_symbol,
            SelectedFeature.selected_folds,
            SelectedFeature.selection_frequency,
            SelectedFeature.mean_coefficient,
            SelectedFeature.coefficient_direction,
        )
        .join(ProbeAnnotation)
        .where(SelectedFeature.experiment_id == experiment.id)
        .where(SelectedFeature.selected_folds >= minimum_frequency)
        .distinct()
    )
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        query = query.where(
            SelectedFeature.probe_id.ilike(pattern)
            | ProbeAnnotation.gene_symbol.ilike(pattern)
        )
    final_probes = _final_probe_ids(session)
    if final_only:
        query = query.where(SelectedFeature.probe_id.in_(final_probes))
    rows = session.execute(
        query.order_by(
            SelectedFeature.selection_frequency.desc(),
            SelectedFeature.probe_id
        ).limit(limit)
    ).all()
    return [
        {
            "probe_id": row.probe_id,
            "gene_symbol": row.gene_symbol,
            "selected_folds": row.selected_folds,
            "selection_frequency": row.selection_frequency,
            "mean_coefficient": row.mean_coefficient,
            "coefficient_direction": row.coefficient_direction,
            "final_model_member": row.probe_id in final_probes,
            "source_path": "results/lasso_feature_stability.csv",
        }
        for row in rows
    ]


@app.get(
    "/api/feature-heatmap",
    response_model=list[FeatureHeatmapResponse]
)
def feature_heatmap(
    limit: int = Query(default=24, ge=5, le=40),
    minimum_frequency: int = Query(default=1, ge=1, le=10),
    search: str | None = Query(default=None, max_length=100),
    session: Session = Depends(get_session),
):
    experiment = require_experiment(session, "lasso-logistic-nested-cv")
    top_query = (
        select(
            SelectedFeature.probe_id,
            ProbeAnnotation.gene_symbol,
            SelectedFeature.selection_frequency,
        )
        .join(ProbeAnnotation)
        .where(
            SelectedFeature.experiment_id == experiment.id,
            SelectedFeature.selected_folds >= minimum_frequency,
        )
        .distinct()
    )
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        top_query = top_query.where(
            SelectedFeature.probe_id.ilike(pattern)
            | ProbeAnnotation.gene_symbol.ilike(pattern)
        )
    top = session.execute(
        top_query.order_by(
            SelectedFeature.selection_frequency.desc(),
            SelectedFeature.probe_id
        ).limit(limit)
    ).all()
    records = []
    for row in top:
        folds = list(session.scalars(
            select(SelectedFeature.fold).where(
                SelectedFeature.experiment_id == experiment.id,
                SelectedFeature.probe_id == row.probe_id,
            ).order_by(SelectedFeature.fold)
        ))
        records.append({
            "probe_id": row.probe_id,
            "gene_symbol": row.gene_symbol,
            "selection_frequency": row.selection_frequency,
            "selected_folds": folds,
            "source_path": "results/lasso_selected_probes_by_fold.csv",
        })
    return records


@app.get(
    "/api/feature-frequency-distribution",
    response_model=list[FrequencyBucketResponse],
)
def feature_frequency_distribution(session: Session = Depends(get_session)):
    experiment = require_experiment(session, "lasso-logistic-nested-cv")
    rows = session.execute(
        select(SelectedFeature.probe_id, SelectedFeature.selected_folds)
        .where(
            SelectedFeature.experiment_id == experiment.id,
            SelectedFeature.selected_folds.is_not(None),
        )
        .distinct()
    ).all()
    counts = {folds: 0 for folds in range(1, 11)}
    for row in rows:
        counts[row.selected_folds] += 1
    return [
        {"selected_folds": folds, "probe_count": counts[folds]}
        for folds in range(1, 11)
    ]


REPORTS = [
    {
        "key": "external-metrics",
        "title": "Метрики от външната валидация",
        "description": "Заключени резултати за двата финални модела.",
        "format": "CSV",
        "source_paths": [
            "results/final_external_validation_gse25065/external_metrics.csv"
        ],
    },
    {
        "key": "external-predictions",
        "title": "Прогнози от външната валидация",
        "description": "Съхранени вероятности и класове за GSE25065.",
        "format": "CSV",
        "source_paths": [
            "results/final_external_validation_gse25065/"
            "external_predictions.csv"
        ],
    },
    {
        "key": "selected-probes",
        "title": "Финални избрани probe sets",
        "description": "Подреденият набор от 15 входни характеристики.",
        "format": "CSV",
        "source_paths": [
            "results/final_model_gse25055/final_selected_probes.csv"
        ],
    },
    {
        "key": "fold-results",
        "title": "Резултати по fold",
        "description": "Метрики и настройки от кръстосаната валидация.",
        "format": "CSV",
        "source_paths": [
            "results/l2_logistic_cv_fold_metrics.csv",
            "results/lasso_cv_fold_metrics.csv",
            "results/lasso_balanced_rf/fold_results.csv",
        ],
    },
    {
        "key": "model-comparison",
        "title": "Сравнение на моделите",
        "description": "Общи OOF метрики за четирите модела.",
        "format": "CSV",
        "source_paths": [
            "results/model_comparison.csv",
            "results/lasso_balanced_rf/model_comparison.csv",
        ],
    },
    {
        "key": "experiment-manifest",
        "title": "Манифест на експериментите",
        "description": "Набори, етапи, модели, настройки и произход.",
        "format": "JSON",
        "source_paths": [],
    },
]


@app.get("/api/reports", response_model=list[ReportResponse])
def reports():
    return [
        {**item, "download_url": f"/api/exports/{item['key']}"}
        for item in REPORTS
    ]


@app.get("/api/exports/{report_key}", response_class=Response)
def export_report(report_key: str, session: Session = Depends(get_session)):
    if report_key not in {item["key"] for item in REPORTS}:
        raise HTTPException(404, "Unknown report.")

    if report_key == "experiment-manifest":
        payload = experiments(session=session)
        return Response(
            json.dumps(payload, ensure_ascii=False, default=str, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition":
                    'attachment; filename="experiment-manifest.json"'
            },
        )

    output = io.StringIO()
    writer = csv.writer(output)

    if report_key == "external-metrics":
        experiment = require_experiment(
            session, "locked-external-validation-gse25065"
        )
        runs = session.scalars(
            select(ModelRun).where(ModelRun.experiment_id == experiment.id)
            .order_by(ModelRun.id)
        ).all()
        metric_keys = list(runs[0].overall_metrics)
        writer.writerow(["model", *metric_keys, "tn", "fp", "fn", "tp"])
        for run in runs:
            matrix = run.confusion_matrix
            writer.writerow([
                run.display_name,
                *[run.overall_metrics.get(key) for key in metric_keys],
                matrix.get("true_negative"), matrix.get("false_positive"),
                matrix.get("false_negative"), matrix.get("true_positive"),
            ])
    elif report_key == "external-predictions":
        writer.writerow([
            "patient", "actual_class", "model", "probability",
            "predicted_class"
        ])
        rows = session.execute(
            select(PredictionRecord, ModelRun, Experiment)
            .join(ModelRun).join(Experiment)
            .where(Experiment.slug == "locked-external-validation-gse25065")
            .order_by(PredictionRecord.patient_id, ModelRun.model_key)
        ).all()
        for prediction, run, _experiment in rows:
            writer.writerow([
                prediction.patient_id, prediction.actual_class, run.model_key,
                prediction.probability, prediction.predicted_class
            ])
    elif report_key == "selected-probes":
        writer.writerow([
            "probe_id", "gene_symbol", "gene_name", "lasso_coefficient"
        ])
        final = require_experiment(session, "final-model-gse25055")
        rows = session.execute(
            select(SelectedFeature, ProbeAnnotation).join(ProbeAnnotation)
            .where(SelectedFeature.experiment_id == final.id)
            .order_by(SelectedFeature.id)
        ).all()
        for feature, annotation in rows:
            writer.writerow([
                feature.probe_id, annotation.gene_symbol,
                annotation.gene_name, feature.coefficient
            ])
    elif report_key == "fold-results":
        writer.writerow([
            "experiment", "model", "fold", "training_patients",
            "validation_patients", "selected_probes", "parameters", "metrics"
        ])
        rows = session.execute(
            select(FoldMetric, ModelRun, Experiment)
            .join(ModelRun).join(Experiment)
            .order_by(Experiment.id, ModelRun.id, FoldMetric.fold)
        ).all()
        for fold, run, experiment in rows:
            writer.writerow([
                experiment.slug, run.model_key, fold.fold,
                fold.training_patient_count, fold.validation_patient_count,
                fold.selected_probe_count,
                json.dumps(fold.selected_parameters, ensure_ascii=False),
                json.dumps(fold.metrics, ensure_ascii=False),
            ])
    else:
        writer.writerow(["experiment", "model", "result_type", "metrics"])
        rows = session.execute(
            select(ModelRun, Experiment).join(Experiment)
            .where(Experiment.slug.in_(CV_EXPERIMENTS))
            .order_by(Experiment.id, ModelRun.id)
        ).all()
        for run, experiment in rows:
            writer.writerow([
                experiment.slug, run.display_name, "overall_oof",
                json.dumps(run.overall_metrics, ensure_ascii=False),
            ])

    return Response(
        output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{report_key}.csv"'
        },
    )


@app.get("/api/table-exports/{view}", response_class=Response)
def export_filtered_table(
    view: str,
    format: str = Query(default="csv", pattern="^(csv|xlsx)$"),
    experiment: str | None = None,
    model: str | None = None,
    cohort: str | None = Query(default=None, pattern="^(oof|external)$"),
    fold: int | None = Query(default=None, ge=1, le=10),
    actual_class: int | None = Query(default=None, ge=0, le=1),
    predicted_class: int | None = Query(default=None, ge=0, le=1),
    correct: bool | None = None,
    disagreement: bool | None = None,
    minimum_frequency: int = Query(default=1, ge=1, le=10),
    final_only: bool = False,
    minimum_probability: float | None = Query(default=None, ge=0, le=1),
    maximum_probability: float | None = Query(default=None, ge=0, le=1),
    search: str | None = Query(default=None, max_length=100),
    session: Session = Depends(get_session),
):
    if view not in {"fold-results", "features", "feature-stability", "metrics", "predictions"}:
        raise HTTPException(404, "Unknown table export.")
    filters = {
        key: value for key, value in {
            "experiment": experiment, "model": model, "cohort": cohort,
            "fold": fold,
            "actual_class": actual_class, "predicted_class": predicted_class,
            "correct": correct, "disagreement": disagreement,
            "minimum_frequency": minimum_frequency,
            "final_only": final_only,
            "minimum_probability": minimum_probability,
            "maximum_probability": maximum_probability, "search": search,
        }.items() if value not in (None, "")
    }

    if view == "fold-results":
        query = (
            select(FoldMetric, ModelRun, Experiment)
            .select_from(FoldMetric)
            .join(ModelRun, FoldMetric.model_run_id == ModelRun.id)
            .join(Experiment, ModelRun.experiment_id == Experiment.id)
        )
        if experiment:
            query = query.where(Experiment.slug == experiment)
        if model:
            query = query.where(ModelRun.model_key == model)
        if fold:
            query = query.where(FoldMetric.fold == fold)
        records = [{
            "experiment": exp.slug, "model": run.model_key, "fold": item.fold,
            "training_patients": item.training_patient_count,
            "validation_patients": item.validation_patient_count,
            "selected_probes": item.selected_probe_count,
            **item.metrics,
            "parameters": json.dumps(item.selected_parameters, ensure_ascii=False),
        } for item, run, exp in session.execute(query.order_by(Experiment.id, ModelRun.id, FoldMetric.fold))]
    elif view == "feature-stability":
        feature_experiment = require_experiment(session, "lasso-logistic-nested-cv")
        query = (
            select(
                SelectedFeature.probe_id, ProbeAnnotation.gene_symbol,
                SelectedFeature.selected_folds,
                SelectedFeature.selection_frequency,
                SelectedFeature.mean_coefficient,
            )
            .join(ProbeAnnotation)
            .where(
                SelectedFeature.experiment_id == feature_experiment.id,
                SelectedFeature.selected_folds >= minimum_frequency,
            )
            .distinct()
        )
        if fold:
            selected_in_fold = select(SelectedFeature.probe_id).where(
                SelectedFeature.experiment_id == feature_experiment.id,
                SelectedFeature.fold == fold,
            )
            query = query.where(SelectedFeature.probe_id.in_(selected_in_fold))
        if search and search.strip():
            pattern = f"%{search.strip()}%"
            query = query.where(
                SelectedFeature.probe_id.ilike(pattern)
                | ProbeAnnotation.gene_symbol.ilike(pattern)
            )
        final_probes = _final_probe_ids(session)
        if final_only:
            query = query.where(SelectedFeature.probe_id.in_(final_probes))
        records = [{
            "probe_id": row.probe_id, "gene_symbol": row.gene_symbol,
            "selected_folds": row.selected_folds,
            "selection_frequency": row.selection_frequency,
            "mean_coefficient": row.mean_coefficient,
            "final_model_member": row.probe_id in final_probes,
        } for row in session.execute(query.order_by(
            SelectedFeature.selection_frequency.desc(), SelectedFeature.probe_id
        ))]
    elif view == "features":
        query = (
            select(SelectedFeature, ProbeAnnotation, Experiment)
            .select_from(SelectedFeature)
            .join(ProbeAnnotation, SelectedFeature.probe_id == ProbeAnnotation.probe_id)
            .join(Experiment, SelectedFeature.experiment_id == Experiment.id)
        )
        if experiment:
            query = query.where(Experiment.slug == experiment)
        if fold:
            query = query.where(SelectedFeature.fold == fold)
        if search and search.strip():
            pattern = f"%{search.strip()}%"
            query = query.where(SelectedFeature.probe_id.ilike(pattern) | ProbeAnnotation.gene_symbol.ilike(pattern))
        records = [{
            "experiment": exp.slug, "probe_id": item.probe_id,
            "gene_symbol": annotation.gene_symbol, "gene_name": annotation.gene_name,
            "context": item.selection_context, "fold": item.fold,
            "coefficient": item.coefficient, "mean_coefficient": item.mean_coefficient,
            "selected_folds": item.selected_folds, "selection_frequency": item.selection_frequency,
        } for item, annotation, exp in session.execute(query.order_by(Experiment.id, SelectedFeature.id))]
    elif view == "metrics":
        selected_slug = (
            "locked-external-validation-gse25065"
            if cohort == "external" else "balanced-rf-nested-cv"
        )
        query = (
            select(ModelRun, Experiment)
            .select_from(ModelRun)
            .join(Experiment, ModelRun.experiment_id == Experiment.id)
            .where(Experiment.slug == selected_slug)
        )
        if model and model != "comparison":
            query = query.where(ModelRun.model_key == model)
        records = []
        for run, exp in session.execute(query.order_by(ModelRun.model_key)):
            matrix = run.confusion_matrix
            records.append({
                "cohort": exp.dataset.accession,
                "model": run.model_key,
                **run.overall_metrics,
                "tn": matrix.get("true_negative", matrix.get("tn")),
                "fp": matrix.get("false_positive", matrix.get("fp")),
                "fn": matrix.get("false_negative", matrix.get("fn")),
                "tp": matrix.get("true_positive", matrix.get("tp")),
            })
    else:
        query = (
            select(PredictionRecord, ModelRun, Experiment)
            .select_from(PredictionRecord)
            .join(ModelRun, PredictionRecord.model_run_id == ModelRun.id)
            .join(Experiment, ModelRun.experiment_id == Experiment.id)
        )
        if experiment:
            query = query.where(Experiment.slug == experiment)
        if model:
            query = query.where(ModelRun.model_key == model)
        if fold:
            query = query.where(PredictionRecord.validation_fold == fold)
        if actual_class is not None:
            query = query.where(PredictionRecord.actual_class == actual_class)
        if predicted_class is not None:
            query = query.where(PredictionRecord.predicted_class == predicted_class)
        if correct is not None:
            match = PredictionRecord.actual_class == PredictionRecord.predicted_class
            query = query.where(match if correct else ~match)
        if minimum_probability is not None:
            query = query.where(PredictionRecord.probability >= minimum_probability)
        if maximum_probability is not None:
            query = query.where(PredictionRecord.probability <= maximum_probability)
        if search and search.strip():
            query = query.where(PredictionRecord.patient_id.ilike(f"%{search.strip()}%"))
        if disagreement is not None:
            other_prediction = aliased(PredictionRecord)
            other_run = aliased(ModelRun)
            disagreement_exists = exists(
                select(1).select_from(other_prediction)
                .join(other_run, other_prediction.model_run_id == other_run.id)
                .where(
                    other_prediction.patient_id == PredictionRecord.patient_id,
                    other_run.experiment_id == Experiment.id,
                    other_prediction.model_run_id != PredictionRecord.model_run_id,
                    other_prediction.predicted_class != PredictionRecord.predicted_class,
                )
            )
            query = query.where(disagreement_exists if disagreement else ~disagreement_exists)
        records = [{
            "experiment": exp.slug, "model": run.model_key,
            "patient_id": item.patient_id, "actual_class": item.actual_class,
            "predicted_class": item.predicted_class, "probability": item.probability,
            "validation_fold": item.validation_fold,
        } for item, run, exp in session.execute(query.order_by(PredictionRecord.patient_id, ModelRun.model_key))]

    frame = pd.DataFrame(records)
    identity = "_".join(str(filters.get(key, "all")) for key in ("experiment", "model"))
    filename = f"{identity}_{view}_{date.today().isoformat()}.{format}"
    filter_header = json.dumps(filters, ensure_ascii=False, sort_keys=True)
    if format == "xlsx":
        binary = io.BytesIO()
        with pd.ExcelWriter(binary, engine="openpyxl") as writer:
            frame.to_excel(writer, index=False, sheet_name="data")
            pd.DataFrame([{"filters": filter_header}]).to_excel(writer, index=False, sheet_name="metadata")
        content = binary.getvalue()
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        content = frame.to_csv(index=False)
        media_type = "text/csv; charset=utf-8"
    return Response(content=content, media_type=media_type, headers={
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Export-Filters": filter_header.encode("ascii", "backslashreplace").decode("ascii"),
    })
