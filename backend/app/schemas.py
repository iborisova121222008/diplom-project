from datetime import datetime
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


RESEARCHER_ID_VALIDATION_MESSAGE = (
    "Researcher ID трябва да е 3–50 знака, да започва с буква или цифра "
    "и да съдържа само букви, цифри, ., _ и -."
)
PASSWORD_VALIDATION_MESSAGE = (
    "Паролата трябва да съдържа поне 8 символа, малка и главна буква, "
    "цифра и специален символ."
)
PASSWORD_SPECIAL_CHARACTERS = "!@#$%^&*()_+-=[]{};':\"\\|,.<>/?"


def normalize_researcher_id(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError(RESEARCHER_ID_VALIDATION_MESSAGE)
    normalized = value.strip().lower()
    if not 3 <= len(normalized) <= 50 or not re.fullmatch(
        r"[^\W_][\w.-]*",
        normalized,
    ):
        raise ValueError(RESEARCHER_ID_VALIDATION_MESSAGE)
    return normalized


def validate_registration_password(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError(PASSWORD_VALIDATION_MESSAGE)
    valid = (
        8 <= len(value) <= 128
        and value == value.strip()
        and any(character.islower() for character in value)
        and any(character.isupper() for character in value)
        and any(character.isdigit() for character in value)
        and any(character in PASSWORD_SPECIAL_CHARACTERS for character in value)
    )
    if not valid:
        raise ValueError(PASSWORD_VALIDATION_MESSAGE)
    return value


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class HealthResponse(ApiModel):
    status: str
    database: str
    mode: str


class RegistrationRequest(ApiModel):
    researcher_id: str
    password: str

    @field_validator("researcher_id", mode="before")
    @classmethod
    def strip_researcher_id(cls, value: object) -> object:
        return normalize_researcher_id(value)

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, value: object) -> str:
        return validate_registration_password(value)


class LoginRequest(ApiModel):
    researcher_id: str
    password: str = Field(min_length=1, max_length=128)

    @field_validator("researcher_id", mode="before")
    @classmethod
    def normalize_id(cls, value: object) -> str:
        return normalize_researcher_id(value)


class TokenResponse(ApiModel):
    access_token: str
    token_type: str
    researcher_id: str


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


class ExpressionPreviewResponse(ApiModel):
    dataset: str
    total_patients: int
    total_probes: int
    row_offset: int
    column_offset: int
    patients: list[str]
    probes: list[str]
    values: list[list[float]]


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
    correct: int
    incorrect: int
    disagreements: int
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


class FrequencyBucketResponse(ApiModel):
    selected_folds: int
    probe_count: int


class ReportResponse(ApiModel):
    key: str
    title: str
    description: str
    format: str
    download_url: str
    source_paths: list[str]


class TreeFeatureUsageResponse(ApiModel):
    probe_id: str
    split_count: int
    minimum_split_depth: float | None
    mean_split_depth: float | None


class TreeSummaryResponse(ApiModel):
    tree_index: int
    full_depth: int
    node_count: int
    generated_depth: int
    used_probes: list[str]
    feature_usage: list[TreeFeatureUsageResponse]
    asset: str


class ForestFeatureUsageResponse(ApiModel):
    probe_id: str
    trees_using: int
    split_count: int
    minimum_split_depth: float | None
    mean_split_depth: float | None
    tree_indices: list[int]


class ForestManifestResponse(ApiModel):
    derivation: str
    generated_at_utc: str
    model_package: str
    model_package_identity: str
    model_created_at_utc: str | None
    tree_count: int
    custom_tree_count: int
    selected_probes: list[str]
    generated_depth: int
    trees: list[TreeSummaryResponse]
    feature_usage: list[ForestFeatureUsageResponse]


class ForestNodeResponse(ApiModel):
    node_id: int
    parent_id: int | None
    branch: str | None
    depth: int
    position: int
    probe_id: str | None
    split_value: float | None
    probability: float
    prediction: int
    leaf: bool


class ForestStructureResponse(ApiModel):
    implementation: str
    tree_index: int
    visible_depth: int
    full_depth: int
    full_node_count: int
    nodes: list[ForestNodeResponse]
