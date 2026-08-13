"""Protocol-scoped retrieval tests. Embeddings are mocked; runs against the local Postgres/pgvector
(skipped when doc_chunks isn't reachable, e.g. no docker / migration not applied).

Each test does all its async work in a single asyncio.run and disposes the engine at the end, because the
shared async engine's pooled connections are bound to the event loop that created them. Results are filtered
to our own seeded rows (source_url marker) so pre-existing ingested chunks don't affect the assertions.
"""

import asyncio
import math

import pytest
from sqlalchemy import delete, text

import app.agent.knowledge.store as store
from app.storage.db import get_engine, get_sessionmaker
from app.storage.models import DocChunk

_MARK = "__test__"  # source_url marker so we only assert on our own rows


def _mix(idxs: list[int]) -> list[float]:
    """A normalized 384-dim vector with 1.0 at the given indices (so cosine distances are predictable)."""
    v = [0.0] * 384
    for i in idxs:
        v[i] = 1.0
    n = math.sqrt(len(idxs))
    return [x / n for x in v]


def _run(coro):
    async def _wrapped():
        try:
            return await coro()
        finally:
            engine = get_engine()
            if engine is not None:
                await engine.dispose()

    return asyncio.run(_wrapped())


def _db_reachable() -> bool:
    if get_sessionmaker() is None:
        return False

    async def _ping():
        async with get_sessionmaker()() as s:
            await s.execute(text("select 1 from doc_chunks limit 1"))  # fails if migration not applied

    try:
        _run(_ping)
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _db_reachable(), reason="doc_chunks not reachable")


async def _seed(rows: list[tuple[str, str, list[int]]]) -> None:
    """rows: (protocol, title, vector_indices)."""
    async with get_sessionmaker()() as s:
        await s.execute(delete(DocChunk).where(DocChunk.source_url == _MARK))
        s.add_all(
            [
                DocChunk(
                    protocol=p, source_url=_MARK, title=t, section=None, chunk_index=i, content=t, embedding=_mix(idxs)
                )
                for i, (p, t, idxs) in enumerate(rows)
            ]
        )
        await s.commit()


async def _cleanup() -> None:
    async with get_sessionmaker()() as s:
        await s.execute(delete(DocChunk).where(DocChunk.source_url == _MARK))
        await s.commit()


def _mine(res) -> list:
    return [r for r in res if r.source_url == _MARK]


def test_search_orders_by_cosine_similarity(monkeypatch):
    # query ~ idx5. Distances: B(=idx5)=0 < A(idx5,idx0)=0.29 < C(idx9)=1.0 — strictly increasing, no tie.
    monkeypatch.setattr(store, "embed_query", lambda _q: _mix([5]))

    async def run():
        await _seed([("lifi", "A", [5, 0]), ("lifi", "B", [5]), ("lifi", "C", [9])])
        res = await store.search("anything", protocol="lifi", k=50)
        await _cleanup()
        return res

    titles = [r.title for r in _mine(_run(run))]
    assert titles[:2] == ["B", "A"]


def test_protocol_filter_and_fallback(monkeypatch):
    monkeypatch.setattr(store, "embed_query", lambda _q: _mix([5]))

    async def run():
        await _seed([("lifi", "L", [5]), ("morpho", "M", [5])])
        only_morpho = _mine(await store.search("q", protocol="morpho", k=50))
        both = _mine(await store.search("q", protocol="both", k=50))  # unknown/both -> no filter
        await _cleanup()
        return only_morpho, both

    only_morpho, both = _run(run)
    assert {r.protocol for r in only_morpho} == {"morpho"}
    assert {r.protocol for r in both} == {"lifi", "morpho"}


def test_protocol_scope_is_case_insensitive(monkeypatch):
    monkeypatch.setattr(store, "embed_query", lambda _q: _mix([5]))

    async def run():
        await _seed([("lifi", "L", [5]), ("morpho", "M", [5])])
        upper = _mine(await store.search("q", protocol="Morpho", k=50))  # mixed case still scopes
        await _cleanup()
        return upper

    assert {r.protocol for r in _run(run)} == {"morpho"}
