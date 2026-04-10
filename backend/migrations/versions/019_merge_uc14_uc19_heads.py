"""merge uc14 and uc19 alembic heads

Revision ID: 019_merge_uc14_uc19_heads
Revises: 018_uc14_forecast_accuracy, 018_uc19_feedback_reporting
Create Date: 2026-04-10 00:00:01.000000
"""

from __future__ import annotations


revision = "019_merge_uc14_uc19_heads"
down_revision = ("018_uc14_forecast_accuracy", "018_uc19_feedback_reporting")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
