"""Async SQLAlchemy engine/session for the business DB (DATABASE_URL, asyncpg)."""

import os

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

import app.config  # noqa: F401  ensure .env is loaded

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker | None = None


def get_engine() -> AsyncEngine | None:
    global _engine
    if _engine is None:
        url = os.getenv("DATABASE_URL")
        if not url:
            return None
        _engine = create_async_engine(url, pool_size=5, max_overflow=5)
    return _engine


def get_sessionmaker() -> async_sessionmaker | None:
    global _sessionmaker
    engine = get_engine()
    if engine is None:
        return None
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    return _sessionmaker
