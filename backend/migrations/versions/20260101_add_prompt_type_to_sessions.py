"""Add prompt_type to sessions table.

Revision ID: add_prompt_type_to_sessions
Revises: 128f97a468de
Create Date: 2026-01-01 00:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "add_prompt_type_to_sessions"
down_revision = "128f97a468de"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column("prompt_type", sa.String(64), nullable=True),
    )
    # 仅加列，不回填 NULL（旧会话保持无 type）
    op.create_index("ix_sessions_prompt_type", "sessions", ["prompt_type"])


def downgrade() -> None:
    op.drop_index("ix_sessions_prompt_type", table_name="sessions")
    op.drop_column("sessions", "prompt_type")