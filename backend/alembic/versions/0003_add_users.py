"""Add minimal researcher authentication users table."""

from alembic import op
import sqlalchemy as sa


revision = "0003_add_users"
down_revision = "0002_results_storage"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("researcher_id", sa.String(50), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_users_researcher_id_lower",
        "users",
        [sa.text("lower(researcher_id)")],
        unique=True,
    )


def downgrade():
    op.drop_index("ix_users_researcher_id_lower", table_name="users")
    op.drop_table("users")
