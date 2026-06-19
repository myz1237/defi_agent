"""会话持久化 checkpointer。

有 LANGGRAPH_PG_DSN 则用 Postgres(跨进程/重启持久,支持 interrupt 恢复);
否则回落 InMemorySaver(仅当前进程)。

注意:LangGraph 的 Postgres checkpointer 底层是 psycopg,DSN 用纯 postgresql://
(不带 +asyncpg);业务库 SQLAlchemy 才用 +asyncpg。
"""

import os
from contextlib import contextmanager

import app.config  # noqa: F401  确保 .env 已加载


@contextmanager
def get_checkpointer():
    dsn = os.getenv("LANGGRAPH_PG_DSN")
    if not dsn:
        from langgraph.checkpoint.memory import InMemorySaver

        yield InMemorySaver()
        return

    from langgraph.checkpoint.postgres import PostgresSaver

    with PostgresSaver.from_conn_string(dsn) as cp:
        cp.setup()  # 首次创建 checkpoint 表(幂等)
        yield cp
