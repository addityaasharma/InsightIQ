"""initial migration

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2026-03-14
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "a1b2c3d4e5f6"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():

    # Create ENUM type for user roles
    userrole_enum = sa.Enum(
        "student", "teacher", "working_professional",
        name="userrole"
    )
    userrole_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=80), nullable=False, unique=True),
        sa.Column("email", sa.String(length=120), nullable=False, unique=True),
        sa.Column("password", sa.String(length=128), nullable=False),
        sa.Column(
            "role",
            sa.Enum("student", "teacher", "working_professional", name="userrole"),
            nullable=False,
            server_default="student"
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "dataset",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=255), nullable=False),
        sa.Column("file_rows", sa.Integer()),
        sa.Column("file_columns", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "dataset_columns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dataset_id", sa.Integer(), sa.ForeignKey("dataset.id", ondelete="CASCADE"), nullable=False),
        sa.Column("column_name", sa.String(length=100)),
        sa.Column("data_type", sa.String(length=50)),
        sa.Column("is_numeric", sa.Boolean()),
        sa.Column("is_date", sa.Boolean()),
    )

    op.create_table(
        "charts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dataset_id", sa.Integer(), sa.ForeignKey("dataset.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chart_type", sa.String(length=50)),
        sa.Column("chart_data", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dataset_id", sa.Integer(), sa.ForeignKey("dataset.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_used", sa.String(length=50)),
        sa.Column("prediction_data", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "insights",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dataset_id", sa.Integer(), sa.ForeignKey("dataset.id", ondelete="CASCADE"), nullable=False),
        sa.Column("insight_type", sa.String(length=50)),
        sa.Column("insight_data", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "business_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dataset_id", sa.Integer(), sa.ForeignKey("dataset.id", ondelete="CASCADE"), nullable=False),
        sa.Column("profitability_score", sa.Float()),
        sa.Column("growth_score", sa.Float()),
        sa.Column("risk_score", sa.Float()),
        sa.Column("recommendation", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade():

    op.drop_table("business_scores")
    op.drop_table("insights")
    op.drop_table("predictions")
    op.drop_table("charts")
    op.drop_table("dataset_columns")
    op.drop_table("dataset")
    op.drop_table("users")

    # Drop the ENUM type
    sa.Enum(name="userrole").drop(op.get_bind(), checkfirst=True)