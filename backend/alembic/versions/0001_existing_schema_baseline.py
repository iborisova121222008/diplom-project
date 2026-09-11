"""Baseline for the six audited scientific tables."""

from alembic import op
import sqlalchemy as sa


revision = "0001_existing_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "datasets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("accession", sa.String(32), nullable=False),
        sa.Column("role", sa.String(64), nullable=False),
        sa.Column("included_patient_count", sa.Integer(), nullable=False),
        sa.Column("original_patient_count", sa.Integer(), nullable=False),
        sa.Column("excluded_patient_count", sa.Integer(), nullable=False),
        sa.Column("feature_count", sa.Integer(), nullable=False),
        sa.Column("label_mapping", sa.JSON(), nullable=False),
        sa.Column("class_distribution", sa.JSON(), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("methodology", sa.JSON(), nullable=False),
        sa.UniqueConstraint("accession", name="datasets_accession_key"),
    )
    op.create_table(
        "experiments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.Column("evaluation_stage", sa.String(50), nullable=False),
        sa.Column("result_scope", sa.String(50), nullable=False),
        sa.Column("locked", sa.Boolean(), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"]),
        sa.UniqueConstraint("slug", name="experiments_slug_key"),
    )
    op.create_table(
        "model_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("experiment_id", sa.Integer(), nullable=False),
        sa.Column("model_key", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("model_family", sa.String(100), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("configuration_source_path", sa.Text(), nullable=True),
        sa.Column("configuration_source_fields", sa.JSON(), nullable=False),
        sa.Column("cv_summary", sa.JSON(), nullable=False),
        sa.Column("cv_summary_source_type", sa.String(40), nullable=True),
        sa.Column("cv_summary_source_path", sa.Text(), nullable=True),
        sa.Column("cv_summary_source_fields", sa.JSON(), nullable=False),
        sa.Column("cv_summary_derivation", sa.Text(), nullable=True),
        sa.Column("overall_metrics", sa.JSON(), nullable=False),
        sa.Column("overall_source_path", sa.Text(), nullable=True),
        sa.Column("overall_source_fields", sa.JSON(), nullable=False),
        sa.Column("confusion_matrix", sa.JSON(), nullable=True),
        sa.Column("confusion_source_type", sa.String(40), nullable=True),
        sa.Column("confusion_source_path", sa.Text(), nullable=True),
        sa.Column("confusion_source_fields", sa.JSON(), nullable=False),
        sa.Column("confusion_derivation", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["experiment_id"], ["experiments.id"]),
        sa.UniqueConstraint(
            "experiment_id", "model_key",
            name="uq_model_run_experiment_model"
        ),
    )
    op.create_table(
        "fold_metrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model_run_id", sa.Integer(), nullable=False),
        sa.Column("fold", sa.Integer(), nullable=False),
        sa.Column("training_patient_count", sa.Integer(), nullable=True),
        sa.Column("validation_patient_count", sa.Integer(), nullable=True),
        sa.Column("selected_probe_count", sa.Integer(), nullable=True),
        sa.Column("selected_parameters", sa.JSON(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("source_fields", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["model_run_id"], ["model_runs.id"]),
        sa.UniqueConstraint(
            "model_run_id", "fold", name="uq_fold_metric_model_fold"
        ),
    )
    op.create_table(
        "probe_annotations",
        sa.Column("probe_id", sa.String(64), primary_key=True),
        sa.Column("gene_symbol", sa.String(300), nullable=True),
        sa.Column("gene_name", sa.Text(), nullable=True),
        sa.Column("entrez_id", sa.String(300), nullable=True),
        sa.Column("number_of_genes", sa.Integer(), nullable=True),
        sa.Column("mapping_status", sa.String(40), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("source_fields", sa.JSON(), nullable=False),
    )
    op.create_table(
        "selected_features",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("experiment_id", sa.Integer(), nullable=False),
        sa.Column("selection_context", sa.String(64), nullable=False),
        sa.Column("fold", sa.Integer(), nullable=True),
        sa.Column("probe_id", sa.String(64), nullable=False),
        sa.Column("coefficient", sa.Float(), nullable=True),
        sa.Column("selected_folds", sa.Integer(), nullable=True),
        sa.Column("selection_frequency", sa.Float(), nullable=True),
        sa.Column("coefficient_direction", sa.String(120), nullable=True),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("source_fields", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["experiment_id"], ["experiments.id"]),
        sa.ForeignKeyConstraint(["probe_id"], ["probe_annotations.probe_id"]),
        sa.UniqueConstraint(
            "experiment_id", "selection_context", "fold", "probe_id",
            name="uq_selected_feature_context_fold_probe"
        ),
    )


def downgrade():
    op.drop_table("selected_features")
    op.drop_table("probe_annotations")
    op.drop_table("fold_metrics")
    op.drop_table("model_runs")
    op.drop_table("experiments")
    op.drop_table("datasets")
