"""Authentication accounts and signup allowlist schema."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "009_auth_accounts_and_allowlist"
down_revision = "008_uc05_visualization_lifecycle"
branch_labels = None
depends_on = None


def _table_names(inspector: sa.Inspector) -> set[str]:
    return set(inspector.get_table_names())


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    table_names = _table_names(inspector)

    if "user_accounts" not in table_names:
        op.create_table(
            "user_accounts",
            sa.Column("user_account_id", sa.String(length=36), primary_key=True),
            sa.Column("email", sa.String(length=320), nullable=False),
            sa.Column("password_hash", sa.Text(), nullable=False),
            sa.Column("roles_json", sa.Text(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_user_accounts_email", "user_accounts", ["email"], unique=True)

    if "signup_allowlist_entries" not in table_names:
        op.create_table(
            "signup_allowlist_entries",
            sa.Column("signup_allowlist_entry_id", sa.String(length=36), primary_key=True),
            sa.Column("email", sa.String(length=320), nullable=False),
            sa.Column("roles_json", sa.Text(), nullable=False),
            sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("registered_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("registered_user_account_id", sa.String(length=36), sa.ForeignKey("user_accounts.user_account_id"), nullable=True),
        )
        op.create_index("ix_signup_allowlist_entries_email", "signup_allowlist_entries", ["email"], unique=True)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    table_names = _table_names(inspector)
    if "signup_allowlist_entries" in table_names:
        op.drop_index("ix_signup_allowlist_entries_email", table_name="signup_allowlist_entries")
        op.drop_table("signup_allowlist_entries")
    if "user_accounts" in table_names:
        op.drop_index("ix_user_accounts_email", table_name="user_accounts")
        op.drop_table("user_accounts")
