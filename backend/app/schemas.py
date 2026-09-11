from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class HealthResponse(ApiModel):
    status: str
    database: str
    mode: str


class DatasetResponse(ApiModel):
    accession: str
    role: str
    included_patient_count: int
    original_patient_count: int
    excluded_patient_count: int
    feature_count: int
    label_mapping: dict[str, int]
    class_distribution: dict[str, int]
    source_path: str
    provenance: dict[str, Any]
    compatibility_metadata: dict[str, Any]


class PreprocessingStepResponse(ApiModel):
    order: int
    category: str
    title: str
    detail: str
    source_path: str
    source_cell: str


class AnnotationResponse(ApiModel):
    gene_symbol: str | None
    gene_name: str | None
    entrez_id: str | None
    number_of_genes: int | None
    mapping_status: str
    display_only: bool = True
    source_path: str


class FeatureResponse(ApiModel):
    experiment_slug: str
    experiment_name: str
    selection_context: str
    fold: int | None
    probe_id: str
    coefficient: float | None
    mean_coefficient: float | None
    selected_folds: int | None
    selection_frequency: float | None
    coefficient_direction: str | None
    final_model_member: bool
    source_path: str
    source_fields: dict[str, Any]
    annotation: AnnotationResponse


class FeaturePageResponse(ApiModel):
    total: int
    offset: int
    limit: int
    items: list[FeatureResponse]


class FoldParameterResponse(ApiModel):
    fold: int
    values: dict[str, Any]
    source_path: str


class ModelResponse(ApiModel):
    model_key: str
    display_name: str
    model_family: str
    cv_experiment: str
    cv_configuration: dict[str, Any]
    cv_configuration_source: str | None
    per_fold_parameters: list[FoldParameterResponse]
    final_configuration: dict[str, Any] | None
    final_configuration_source: str | None
    unavailable_fields: list[str]


class FoldResultResponse(ApiModel):
    fold: int
    training_patient_count: int | None
    validation_patient_count: int | None
    selected_probe_count: int | None
    selected_parameters: dict[str, Any]
    metrics: dict[str, float | None]
    result_type: str
    source_path: str
    source_fields: dict[str, Any]


class SummaryResponse(ApiModel):
    metrics: dict[str, dict[str, float | None]]
    result_type: str
    source_type: str
    source_path: str
    source_fields: dict[str, Any]
    derivation: str | None


class ConfusionResponse(ApiModel):
    values: dict[str, int]
    result_type: str
    source_type: str
    source_path: str
    source_fields: dict[str, Any]
    derivation: str | None


class CvModelResponse(ApiModel):
    model_key: str
    model: str
    experiment_slug: str
    experiment_name: str
    dataset: str
    folds: list[FoldResultResponse]
    summary: SummaryResponse
    confusion_matrix: ConfusionResponse


class ComparisonResponse(ApiModel):
    model_key: str
    model: str
    experiment_slug: str
    dataset: str
    result_type: str
    metrics: dict[str, float | None]
    source_path: str
    source_fields: dict[str, Any]


class FinalModelResponse(ApiModel):
    model_key: str
    model: str
    threshold: float
    configuration: dict[str, Any]
    metrics: dict[str, float | None]
    confusion_matrix: dict[str, int]
    source_path: str
    source_fields: dict[str, Any]


class FinalValidationResponse(ApiModel):
    experiment: str
    experiment_slug: str
    dataset: str
    dataset_role: str
    locked: bool
    result_type: str
    evaluated_at: datetime | None
    source_path: str
    isolation_statement: str
    models: list[FinalModelResponse]


class ExperimentModelResponse(ApiModel):
    model_key: str
    display_name: str
    model_family: str
    configuration: dict[str, Any]
    configuration_source_path: str | None
    overall_metrics: dict[str, float | None]
    fold_count: int


class ExperimentResponse(ApiModel):
    slug: str
    name: str
    dataset: str
    evaluation_stage: str
    result_scope: str
    locked: bool
    status: str
    source_path: str
    created_at: datetime | None
    models: list[ExperimentModelResponse]


class PredictionResponse(ApiModel):
    experiment_slug: str
    model_key: str
    model: str
    patient_id: str
    actual_class: int
    predicted_class: int
    probability: float
    validation_fold: int | None
    source_path: str


class PredictionPageResponse(ApiModel):
    total: int
    offset: int
    limit: int
    items: list[PredictionResponse]


class CurvePointResponse(ApiModel):
    x: float
    y: float
    threshold: float | None = None


class ProbabilityBinResponse(ApiModel):
    lower: float
    upper: float
    rd_count: int
    pcr_count: int


class ModelCurveResponse(ApiModel):
    model_key: str
    model: str
    roc: list[CurvePointResponse]
    precision_recall: list[CurvePointResponse]
    probability_distribution: list[ProbabilityBinResponse]
    source_path: str


class CurvesResponse(ApiModel):
    experiment_slug: str
    result_type: str
    models: list[ModelCurveResponse]


class DisagreementResponse(ApiModel):
    patient_id: str
    actual_class: int
    left_model_key: str
    left_prediction: int
    left_probability: float
    right_model_key: str
    right_prediction: int
    right_probability: float


class DisagreementPageResponse(ApiModel):
    total: int
    offset: int
    limit: int
    items: list[DisagreementResponse]


class FoldSimilarityResponse(ApiModel):
    experiment_slug: str
    fold_a: int
    fold_b: int
    shared_probes: int
    union_probes: int
    jaccard_similarity: float
    source_path: str


class FeatureStabilityResponse(ApiModel):
    probe_id: str
    gene_symbol: str | None
    selected_folds: int
    selection_frequency: float
    mean_coefficient: float | None
    coefficient_direction: str | None
    final_model_member: bool
    source_path: str


class FeatureHeatmapResponse(ApiModel):
    probe_id: str
    gene_symbol: str | None
    selection_frequency: float
    selected_folds: list[int]
    source_path: str


class ReportResponse(ApiModel):
    key: str
    title: str
    description: str
    format: str
    download_url: str
    source_paths: list[str]
