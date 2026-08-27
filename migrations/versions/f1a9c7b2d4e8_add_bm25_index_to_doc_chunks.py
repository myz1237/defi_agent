"""add pg_search BM25 index to doc_chunks (hybrid search)

Revision ID: f1a9c7b2d4e8
Revises: c4f2a1b3d6e7
Create Date: 2026-08-14

Creates a BM25 index over title/context/content for hybrid (dense + BM25) retrieval. Guarded so it is a
no-op where the pg_search extension isn't available (plain pgvector) — retrieval then degrades to dense-only.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "f1a9c7b2d4e8"
down_revision: str | None = "c4f2a1b3d6e7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'pg_search') THEN
            CREATE EXTENSION IF NOT EXISTS pg_search;
            CREATE INDEX IF NOT EXISTS ix_doc_chunks_bm25 ON doc_chunks
              USING bm25 (id, content, context, protocol, title) WITH (key_field='id');
          ELSE
            RAISE NOTICE 'pg_search not available; skipping BM25 index (hybrid search degrades to dense-only)';
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_doc_chunks_bm25")
