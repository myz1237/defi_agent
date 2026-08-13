"""Protocol-scoped semantic retrieval over the doc_chunks store (pgvector cosine distance)."""

import asyncio
from dataclasses import dataclass

from sqlalchemy import select

from app.agent.knowledge.embed import embed_query
from app.storage.db import get_sessionmaker
from app.storage.models import DocChunk

# Protocols that scope the search to a single set of docs; anything else searches across all.
_SCOPED = {"lifi", "morpho"}


@dataclass
class RetrievedChunk:
    protocol: str
    title: str | None
    section: str | None
    source_url: str
    content: str


async def search(query: str, protocol: str | None = None, k: int = 5) -> list[RetrievedChunk]:
    """Return the k doc chunks most similar to `query`, scoped to `protocol` when it is lifi/morpho.

    A protocol of "both"/"none"/None (or anything unknown) searches across all protocols.
    """
    sm = get_sessionmaker()
    if sm is None:
        return []
    # Embedding is CPU-heavy (and downloads the model on first use) — keep it off the event loop.
    qvec = await asyncio.to_thread(embed_query, query)
    stmt = select(DocChunk).order_by(DocChunk.embedding.cosine_distance(qvec)).limit(k)
    if (protocol or "").lower() in _SCOPED:
        stmt = stmt.where(DocChunk.protocol == protocol.lower())
    async with sm() as session:
        rows = (await session.execute(stmt)).scalars().all()
    return [RetrievedChunk(r.protocol, r.title, r.section, r.source_url, r.content) for r in rows]
