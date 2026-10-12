"""Add session versions for authenticated account changes.

Revision ID: 8a74c561f903
Revises: 1cf10aa79023
"""

from alembic import context, op
import sqlalchemy as sa

revision = "8a74c561f903"
down_revision = "1cf10aa79023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # A discarded development migration may already have added this column.
    # Adopt it without resetting its values or modifying unrelated tables.
    if context.is_offline_mode():
        raise RuntimeError(
            "This migration requires an online schema check to preserve existing session versions."
        )
    columns = sa.inspect(op.get_bind()).get_columns("users")
    if not any(column["name"] == "auth_version" for column in columns):
        op.add_column(
            "users",
            sa.Column("auth_version", sa.Integer(), nullable=False, server_default=sa.text("0")),
        )


def downgrade() -> None:
    # Retain the version values so restoring an older backend cannot revive sessions
    # if the profile feature is enabled again. The previous schema ignores this column.
    pass
