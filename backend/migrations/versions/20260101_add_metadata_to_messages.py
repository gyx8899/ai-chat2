"""Add metadata to messages table.

Revision ID: add_metadata_to_messages
Revises: add_prompt_type_to_sessions
Create Date: 2026-01-01 00:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "add_metadata_to_messages"
down_revision = "add_prompt_type_to_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "messages",
        sa.Column("msg_metadata", sa.JSON, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("messages", "msg_metadata")