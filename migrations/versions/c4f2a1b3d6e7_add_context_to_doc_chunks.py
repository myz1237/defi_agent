"""add context column to doc_chunks (Contextual Retrieval)

Revision ID: c4f2a1b3d6e7
Revises: 79325b4392f5
Create Date: 2026-08-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4f2a1b3d6e7"
down_revision: str | None = "79325b4392f5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("doc_chunks", sa.Column("context", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("doc_chunks", "context")
