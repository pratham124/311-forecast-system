"""Fix demand_comparison_requests: add missing count columns

Revision ID: 014_fix_demand_comparison_counts
Revises: 013_uc08_demand_comparisons
Create Date: 2026-04-01

Root cause: some databases were stamped at revision 013 with an earlier
version of that migration that created demand_comparison_requests with
service_category_filters (text) and geography_filters (text) columns
instead of service_category_count (integer) and geography_value_count
(integer).  The current ORM model and repository code write those count
columns on every INSERT, so those databases get a ProgrammingError:
"column service_category_count of relation demand_comparison_requests
does not exist".

Fix: add the two count columns if they are absent and set appropriate
NOT NULL / server-default values so existing rows are backfilled safely.
The existence check makes the migration idempotent for databases that
were migrated from a corrected 013 and already carry the columns.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "014_fix_demand_comparison_counts"
down_revision = "013_uc08_demand_comparisons"
branch_labels = None
depends_on = None

_TABLE = "demand_comparison_requests"


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return any(c["name"] == column for c in insp.get_columns(table))


def upgrade() -> None:
    if not _column_exists(_TABLE, "service_category_count"):
        with op.batch_alter_table(_TABLE) as batch_op:
            batch_op.add_column(
                sa.Column(
                    "service_category_count",
                    sa.Integer(),
                    nullable=False,
                    server_default="1",
                )
            )

    if not _column_exists(_TABLE, "geography_value_count"):
        with op.batch_alter_table(_TABLE) as batch_op:
            batch_op.add_column(
                sa.Column(
                    "geography_value_count",
                    sa.Integer(),
                    nullable=False,
                    server_default="0",
                )
            )


def downgrade() -> None:
    if _column_exists(_TABLE, "geography_value_count"):
        with op.batch_alter_table(_TABLE) as batch_op:
            batch_op.drop_column("geography_value_count")

    if _column_exists(_TABLE, "service_category_count"):
        with op.batch_alter_table(_TABLE) as batch_op:
            batch_op.drop_column("service_category_count")