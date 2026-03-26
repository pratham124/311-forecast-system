"""Compatibility mirror for the active UC-06 migration.

The executable migration chain for this repository lives under
`backend/migrations/versions`. This mirror keeps the task-plan path accurate for
UC-06 without changing the active migration ordering.
"""

from __future__ import annotations

from migrations.versions.011_uc06_evaluation_lifecycle import downgrade as active_downgrade
from migrations.versions.011_uc06_evaluation_lifecycle import upgrade as active_upgrade


def upgrade() -> None:
    active_upgrade()


def downgrade() -> None:
    active_downgrade()
