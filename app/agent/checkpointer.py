"""Session-persistence checkpointer.

With LANGGRAPH_PG_DSN, use Postgres (persistent across processes/restarts, supports interrupt resume);
otherwise fall back to InMemorySaver (current process only).

Note: LangGraph's Postgres checkpointer is backed by psycopg, so the DSN uses plain postgresql://
(without +asyncpg); the business DB with SQLAlchemy is the one that uses +asyncpg.
"""

import os
from contextlib import asynccontextmanager, contextmanager

import app.config  # noqa: F401  ensure .env is loaded


@contextmanager
def get_checkpointer():
    """Synchronous checkpointer (for the CLI)."""
    dsn = os.getenv("LANGGRAPH_PG_DSN")
    if not dsn:
        from langgraph.checkpoint.memory import InMemorySaver

        yield InMemorySaver()
        return

    from langgraph.checkpoint.postgres import PostgresSaver

    with PostgresSaver.from_conn_string(dsn) as cp:
        cp.setup()  # create the checkpoint tables on first run (idempotent)
        yield cp


@asynccontextmanager
async def get_async_checkpointer():
    """Asynchronous checkpointer (for FastAPI). astream requires an async saver."""
    dsn = os.getenv("LANGGRAPH_PG_DSN")
    if not dsn:
        from langgraph.checkpoint.memory import InMemorySaver

        yield InMemorySaver()
        return

    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    async with AsyncPostgresSaver.from_conn_string(dsn) as cp:
        await cp.setup()
        yield cp
