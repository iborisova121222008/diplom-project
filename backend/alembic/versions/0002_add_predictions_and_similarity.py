"""Add approved prediction and fold-similarity storage."""

from alembic import op
import sqlalchemy as sa


revision = "0002_results_storage"
down_revision = "0001_existing_schema"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "datasets",
        sa.Column(
            "compatibility_metadata",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json")
        )
    )
    op.add_column(
        "selected_features",
        sa.Column("mean_coefficient", sa.Float(), nullable=True)
    )
    op.create_table(
        "prediction_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model_run_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.String(64), nullable=False),
        sa.Column("actual_class", sa.Integer(), nullable=False),
        sa.Column("predicted_class", sa.Integer(), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False),
        sa.Column("validation_fold", sa.Integer(), nullable=True),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("source_fields", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["model_run_id"], ["model_runs.id"]),
        sa.UniqueConstraint(
            "model_run_id", "patient_id",
            name="uq_prediction_record_run_patient"
        ),
    )
    op.create_table(
        "fold_feature_similarity",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("experiment_id", sa.Integer(), nullable=False),
        sa.Column("fold_a", sa.Integer(), nullable=False),
        sa.Column("fold_b", sa.Integer(), nullable=False),
        sa.Column("shared_probes", sa.Integer(), nullable=False),
        sa.Column("union_probes", sa.Integer(), nullable=False),
        sa.Column("jaccard_similarity", sa.Float(), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("source_fields", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["experiment_id"], ["experiments.id"]),
        sa.UniqueConstraint(
            "experiment_id", "fold_a", "fold_b",
            name="uq_fold_feature_similarity_pair"
        ),
    )


def downgrade():
    op.drop_table("fold_feature_similarity")
    op.drop_table("prediction_records")
    op.drop_column("selected_features", "mean_coefficient")
    op.drop_column("datasets", "compatibility_metadata")
