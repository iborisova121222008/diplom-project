from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Index,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    researcher_id: Mapped[str] = mapped_column(
        String(50),
    )
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        Index(
            "ix_users_researcher_id_lower",
            func.lower(researcher_id),
            unique=True,
        ),
    )


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(primary_key=True)
    accession: Mapped[str] = mapped_column(String(32), unique=True)
    role: Mapped[str] = mapped_column(String(64))
    included_patient_count: Mapped[int]
    original_patient_count: Mapped[int]
    excluded_patient_count: Mapped[int]
    feature_count: Mapped[int]
    label_mapping: Mapped[dict] = mapped_column(JSON)
    class_distribution: Mapped[dict] = mapped_column(JSON)
    source_path: Mapped[str] = mapped_column(Text)
    provenance: Mapped[dict] = mapped_column(JSON)
    methodology: Mapped[list] = mapped_column(JSON)
    compatibility_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    experiments: Mapped[list["Experiment"]] = relationship(
        back_populates="dataset"
    )


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(180))
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"))
    evaluation_stage: Mapped[str] = mapped_column(String(50))
    result_scope: Mapped[str] = mapped_column(String(50))
    locked: Mapped[bool] = mapped_column(Boolean, default=False)
    source_path: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    dataset: Mapped[Dataset] = relationship(back_populates="experiments")
    model_runs: Mapped[list["ModelRun"]] = relationship(
        back_populates="experiment",
        cascade="all, delete-orphan"
    )
    selected_features: Mapped[list["SelectedFeature"]] = relationship(
        back_populates="experiment",
        cascade="all, delete-orphan"
    )


class ModelRun(Base):
    __tablename__ = "model_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"))
    model_key: Mapped[str] = mapped_column(String(64))
    display_name: Mapped[str] = mapped_column(String(120))
    model_family: Mapped[str] = mapped_column(String(100))
    configuration: Mapped[dict] = mapped_column(JSON)
    configuration_source_path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    configuration_source_fields: Mapped[dict] = mapped_column(JSON)
    cv_summary: Mapped[dict] = mapped_column(JSON)
    cv_summary_source_type: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True
    )
    cv_summary_source_path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    cv_summary_source_fields: Mapped[dict] = mapped_column(JSON)
    cv_summary_derivation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    overall_metrics: Mapped[dict] = mapped_column(JSON)
    overall_source_path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    overall_source_fields: Mapped[dict] = mapped_column(JSON)
    confusion_matrix: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confusion_source_type: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True
    )
    confusion_source_path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    confusion_source_fields: Mapped[dict] = mapped_column(JSON)
    confusion_derivation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    experiment: Mapped[Experiment] = relationship(back_populates="model_runs")
    fold_metrics: Mapped[list["FoldMetric"]] = relationship(
        back_populates="model_run",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "experiment_id",
            "model_key",
            name="uq_model_run_experiment_model"
        ),
    )


class FoldMetric(Base):
    __tablename__ = "fold_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_run_id: Mapped[int] = mapped_column(ForeignKey("model_runs.id"))
    fold: Mapped[int]
    training_patient_count: Mapped[int | None] = mapped_column(
        nullable=True
    )
    validation_patient_count: Mapped[int | None] = mapped_column(
        nullable=True
    )
    selected_probe_count: Mapped[int | None] = mapped_column(nullable=True)
    selected_parameters: Mapped[dict] = mapped_column(JSON)
    metrics: Mapped[dict] = mapped_column(JSON)
    source_path: Mapped[str] = mapped_column(Text)
    source_fields: Mapped[dict] = mapped_column(JSON)

    model_run: Mapped[ModelRun] = relationship(back_populates="fold_metrics")

    __table_args__ = (
        UniqueConstraint(
            "model_run_id",
            "fold",
            name="uq_fold_metric_model_fold"
        ),
    )


class ProbeAnnotation(Base):
    __tablename__ = "probe_annotations"

    probe_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    gene_symbol: Mapped[str | None] = mapped_column(String(300), nullable=True)
    gene_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    entrez_id: Mapped[str | None] = mapped_column(String(300), nullable=True)
    number_of_genes: Mapped[int | None] = mapped_column(nullable=True)
    mapping_status: Mapped[str] = mapped_column(String(40))
    source_path: Mapped[str] = mapped_column(Text)
    source_fields: Mapped[dict] = mapped_column(JSON)


class SelectedFeature(Base):
    __tablename__ = "selected_features"

    id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"))
    selection_context: Mapped[str] = mapped_column(String(64))
    fold: Mapped[int | None] = mapped_column(nullable=True)
    probe_id: Mapped[str] = mapped_column(ForeignKey("probe_annotations.probe_id"))
    coefficient: Mapped[float | None] = mapped_column(Float, nullable=True)
    mean_coefficient: Mapped[float | None] = mapped_column(Float, nullable=True)
    selected_folds: Mapped[int | None] = mapped_column(nullable=True)
    selection_frequency: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )
    coefficient_direction: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True
    )
    source_path: Mapped[str] = mapped_column(Text)
    source_fields: Mapped[dict] = mapped_column(JSON)

    experiment: Mapped[Experiment] = relationship(
        back_populates="selected_features"
    )
    annotation: Mapped[ProbeAnnotation] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "experiment_id",
            "selection_context",
            "fold",
            "probe_id",
            name="uq_selected_feature_context_fold_probe"
        ),
    )


class PredictionRecord(Base):
    __tablename__ = "prediction_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    model_run_id: Mapped[int] = mapped_column(ForeignKey("model_runs.id"))
    patient_id: Mapped[str] = mapped_column(String(64))
    actual_class: Mapped[int]
    predicted_class: Mapped[int]
    probability: Mapped[float] = mapped_column(Float)
    validation_fold: Mapped[int | None] = mapped_column(nullable=True)
    source_path: Mapped[str] = mapped_column(Text)
    source_fields: Mapped[dict] = mapped_column(JSON)

    model_run: Mapped[ModelRun] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "model_run_id",
            "patient_id",
            name="uq_prediction_record_run_patient"
        ),
    )


class FoldFeatureSimilarity(Base):
    __tablename__ = "fold_feature_similarity"

    id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"))
    fold_a: Mapped[int]
    fold_b: Mapped[int]
    shared_probes: Mapped[int]
    union_probes: Mapped[int]
    jaccard_similarity: Mapped[float] = mapped_column(Float)
    source_path: Mapped[str] = mapped_column(Text)
    source_fields: Mapped[dict] = mapped_column(JSON)

    experiment: Mapped[Experiment] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "experiment_id",
            "fold_a",
            "fold_b",
            name="uq_fold_feature_similarity_pair"
        ),
    )
