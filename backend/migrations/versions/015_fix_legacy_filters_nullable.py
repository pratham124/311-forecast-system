"""Fix demand_comparison_requests: make legacy filter columns nullable

Revision ID: 015_fix_legacy_filters_nullable
Revises: 014_fix_demand_comparison_counts
Create Date: 2026-04-01

Root cause (second half of migration drift):
Migration 014 added service_category_count and geography_value_count, but
on databases that were stamped at the old 013 revision, the table also
carries service_category_filters TEXT NOT NULL and geography_filters TEXT NOT NULL
with no server default.  The current ORM model has no mapping for those
columns, so every INSERT from the repository leaves them unpopulated and
Postgres raises:

    psycopg2.errors.NotNullViolation: null value in column
    "service_category_filters" of relation "demand_comparison_requests"
    violates not-null constraint

Fix: drop the NOT NULL constraint on each legacy column when it is present
and still non-nullable.  The check makes the migration idempotent:
  - databases that never had the legacy columns: no-op
  - databases already patched (columns nullable): no-op
  - databases with legacy NOT NULL columns (old-013 path): drops constraint
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "015_fix_legacy_filters_nullable"
down_revision = "014_fix_demand_comparison_counts"
branch_labels = None
depends_on = None

_TABLE = "demand_comparison_requests"
_LEGACY_COLS = ("service_category_filters", "geography_filters")


def _col_info(table: str, column: str) -> dict | None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    for c in insp.get_columns(table):
        if c["name"] == column:
            return c
    return None


def upgrade() -> None:
    for col_name in _LEGACY_COLS:
        info = _col_info(_TABLE, col_name)
        # Only act when the column exists AND still carries NOT NULL
        if info is not None and not info["nullable"]:
            with op.batch_alter_table(_TABLE) as batch_op:
                batch_op.alter_column(col_name, nullable=True)


def downgrade() -> None:
    # Re-adding NOT NULL would fail if any row now has a NULL value in these
    # legacy columns, so the downgrade is intentionally left as a no-op.
    pass
