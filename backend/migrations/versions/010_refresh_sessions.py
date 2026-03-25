"""Refresh session persistence schema."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "010_refresh_sessions"
down_revision = "009_auth_accounts_and_allowlist"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "refresh_sessions" not in inspector.get_table_names():
        op.create_table(
            "refresh_sessions",
            sa.Column("refresh_session_id", sa.String(length=36), primary_key=True),
            sa.Column("user_account_id", sa.String(length=36), sa.ForeignKey("user_accounts.user_account_id"), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("rotated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_refresh_sessions_user_account_id", "refresh_sessions", ["user_account_id"], unique=False)
        op.create_index("ix_refresh_sessions_token_hash", "refresh_sessions", ["token_hash"], unique=True)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "refresh_sessions" in inspector.get_table_names():
        op.drop_index("ix_refresh_sessions_token_hash", table_name="refresh_sessions")
        op.drop_index("ix_refresh_sessions_user_account_id", table_name="refresh_sessions")
        op.drop_table("refresh_sessions")
