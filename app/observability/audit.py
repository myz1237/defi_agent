"""Audit log: one row per chat/resume turn in Postgres.

Uses the same Postgres instance as the checkpointer (LANGGRAPH_PG_DSN). No-op when
that DSN is unset. Failures never break the request.
"""

import json

from psycopg_pool import AsyncConnectionPool

_DDL = """
CREATE TABLE IF NOT EXISTS audit_log (
    id          BIGSERIAL PRIMARY KEY,
    ts          TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_id     TEXT,
    kind        TEXT,
    thread_id   TEXT,
    intent      TEXT,
    in_scope    BOOLEAN,
    tools       TEXT,
    latency_ms  INTEGER,
    message     TEXT
);
"""

_INSERT = """
INSERT INTO audit_log (user_id, kind, thread_id, intent, in_scope, tools, latency_ms, message)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""


class AuditLog:
    def __init__(self, dsn: str | None):
        self.dsn = dsn
        self.pool: AsyncConnectionPool | None = None

    async def open(self) -> None:
        if not self.dsn:
            return
        self.pool = AsyncConnectionPool(self.dsn, min_size=1, max_size=4, open=False)
        await self.pool.open()
        async with self.pool.connection() as conn:
            await conn.execute(_DDL)

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()

    async def record(
        self,
        *,
        user_id: str | None,
        kind: str,
        thread_id: str | None,
        intent: str | None,
        in_scope: bool | None,
        tools: list[str],
        latency_ms: int,
        message: str | None,
    ) -> None:
        if not self.pool:
            return
        try:
            async with self.pool.connection() as conn:
                await conn.execute(
                    _INSERT,
                    (user_id, kind, thread_id, intent, in_scope, json.dumps(tools), latency_ms, (message or "")[:2000]),
                )
        except Exception:
            # Auditing must never break the user request.
            pass
