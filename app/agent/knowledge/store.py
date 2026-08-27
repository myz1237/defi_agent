"""Protocol-scoped hybrid retrieval over doc_chunks: dense (pgvector cosine) + BM25 (pg_search),
fused with Reciprocal Rank Fusion. BM25 is best-effort — it degrades to dense-only if pg_search is
unavailable, so the search still works on a plain pgvector database."""

import asyncio
import logging
from dataclasses import dataclass

from sqlalchemy import select, text

from app.agent.knowledge.embed import embed_query
from app.storage.db import get_sessionmaker
from app.storage.models import DocChunk

logger = logging.getLogger(__name__)

# Protocols that scope the search to a single set of docs; anything else searches across all.
_SCOPED = {"lifi", "morpho"}
_CANDIDATES = 20  # top-N from each retriever before fusion
_RRF_C = 60  # RRF damping constant (higher = ranks matter less relative to each other)


@dataclass
class RetrievedChunk:
    protocol: str
    title: str | None
    section: str | None
    source_url: str
    content: str


def _rrf(*ranked_lists: list[int], k: int) -> list[int]:
    """Reciprocal Rank Fusion: score each id by the sum of 1/(c + rank) across the lists it appears in,
    then return the top-k ids. Uses ranks (not raw scores), so cosine distance and BM25 scores — on wholly
    different scales — combine without any normalization."""
    scores: dict[int, float] = {}
    for ids in ranked_lists:
        for rank, id_ in enumerate(ids, start=1):
            scores[id_] = scores.get(id_, 0.0) + 1.0 / (_RRF_C + rank)
    return [id_ for id_, _ in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:k]]


async def _dense_ids(session, qvec: list[float], protocol: str | None) -> list[int]:
    stmt = select(DocChunk.id).order_by(DocChunk.embedding.cosine_distance(qvec)).limit(_CANDIDATES)
    if (protocol or "").lower() in _SCOPED:
        stmt = stmt.where(DocChunk.protocol == protocol.lower())
    return list((await session.execute(stmt)).scalars().all())


async def _bm25_ids(session, query: str, protocol: str | None) -> list[int]:
    """BM25 over title/context/content via pg_search's paradedb.match — which treats the query as terms, so
    colons and other Tantivy query-syntax characters are safe. Runs in a savepoint and returns [] on any
    failure, so a BM25 error falls back to dense-only WITHOUT poisoning the surrounding transaction."""
    scope = "AND protocol = :protocol" if (protocol or "").lower() in _SCOPED else ""
    sql = text(
        "SELECT id FROM doc_chunks WHERE ("
        "id @@@ paradedb.match('title', :q) OR id @@@ paradedb.match('context', :q) "
        f"OR id @@@ paradedb.match('content', :q)) {scope} "
        "ORDER BY paradedb.score(id) DESC LIMIT :n"
    )
    params: dict = {"q": query, "n": _CANDIDATES}
    if scope:
        params["protocol"] = protocol.lower()
    try:
        async with session.begin_nested():  # savepoint: a BM25 failure rolls back only this, not the dense query
            return list((await session.execute(sql, params)).scalars().all())
    except Exception:  # noqa: BLE001  BM25 is best-effort; dense still carries the search
        logger.exception("BM25 search failed; falling back to dense-only")
        return []


async def search(query: str, protocol: str | None = None, k: int = 5) -> list[RetrievedChunk]:
    """Return the top-k doc chunks for `query` via hybrid retrieval (dense cosine + BM25, fused with RRF),
    scoped to `protocol` when it is lifi/morpho ("both"/"none"/None searches across all protocols)."""
    sm = get_sessionmaker()
    if sm is None:
        return []
    qvec = await asyncio.to_thread(embed_query, query)  # CPU-heavy; keep off the event loop
    async with sm() as session:
        dense = await _dense_ids(session, qvec, protocol)
        bm25 = await _bm25_ids(session, query, protocol)
        ids = _rrf(dense, bm25, k=k)
        if not ids:
            return []
        rows = (await session.execute(select(DocChunk).where(DocChunk.id.in_(ids)))).scalars().all()
    by_id = {r.id: r for r in rows}
    return [
        RetrievedChunk(r.protocol, r.title, r.section, r.source_url, r.content)
        for r in (by_id[i] for i in ids if i in by_id)
    ]
