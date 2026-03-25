"""Scope forecast model artifacts by forecast product."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "007_uc03_model_product_scope"
down_revision = "006_uc04_weekly_forecast"
branch_labels = None
depends_on = None

DEFAULT_PRODUCT = "daily_1_day_demand"


def _column_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "forecast_model_runs" in inspector.get_table_names():
        run_columns = _column_names(inspector, "forecast_model_runs")
        if "forecast_product_name" not in run_columns:
            with op.batch_alter_table("forecast_model_runs") as batch_op:
                batch_op.add_column(sa.Column("forecast_product_name", sa.String(length=64), nullable=True))
            bind.execute(sa.text("UPDATE forecast_model_runs SET forecast_product_name = :product WHERE forecast_product_name IS NULL"), {"product": DEFAULT_PRODUCT})
            with op.batch_alter_table("forecast_model_runs") as batch_op:
                batch_op.alter_column("forecast_product_name", existing_type=sa.String(length=64), nullable=False)

    if "forecast_model_artifacts" in inspector.get_table_names():
        artifact_columns = _column_names(inspector, "forecast_model_artifacts")
        if "forecast_product_name" not in artifact_columns:
            with op.batch_alter_table("forecast_model_artifacts") as batch_op:
                batch_op.add_column(sa.Column("forecast_product_name", sa.String(length=64), nullable=True))
            bind.execute(sa.text("UPDATE forecast_model_artifacts SET forecast_product_name = :product WHERE forecast_product_name IS NULL"), {"product": DEFAULT_PRODUCT})
            with op.batch_alter_table("forecast_model_artifacts") as batch_op:
                batch_op.alter_column("forecast_product_name", existing_type=sa.String(length=64), nullable=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "forecast_model_artifacts" in inspector.get_table_names() and "forecast_product_name" in _column_names(inspector, "forecast_model_artifacts"):
        with op.batch_alter_table("forecast_model_artifacts") as batch_op:
            batch_op.drop_column("forecast_product_name")
    inspector = sa.inspect(bind)
    if "forecast_model_runs" in inspector.get_table_names() and "forecast_product_name" in _column_names(inspector, "forecast_model_runs"):
        with op.batch_alter_table("forecast_model_runs") as batch_op:
            batch_op.drop_column("forecast_product_name")
