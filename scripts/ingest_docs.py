"""Ingest curated LI.FI and Morpho concept docs into the pgvector doc_chunks store.

Both sites are Mintlify: appending `.md` to a page URL returns markdown. We fetch the shortlisted
conceptual pages, clean MDX noise (both sites can ship JSX/imports), heading-aware chunk with overlap,
embed locally (bge-small), and write per protocol (rebuild — delete that protocol's chunks then insert),
so re-running is idempotent. A protocol is only rebuilt when all of its pages fetched OK, so a transient
fetch failure keeps the existing corpus rather than silently shrinking it.

Fetching is sequential and embedding is per-page: fine for a run-once script over ~20 small pages.

Run: uv run python scripts/ingest_docs.py
"""

import asyncio
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402
from sqlalchemy import delete  # noqa: E402

from app.agent.knowledge.embed import embed_passages  # noqa: E402
from app.agent.knowledge.ingest import chunk_markdown, extract_title, strip_mdx  # noqa: E402
from app.storage.db import get_sessionmaker  # noqa: E402
from app.storage.models import DocChunk  # noqa: E402

# Curated conceptual pages (mechanics, not API reference). URL -> fetched as `<url>.md`.
LIFI_BASE = "https://docs.li.fi"
MORPHO_BASE = "https://docs.morpho.org"

PAGES: list[tuple[str, str]] = [
    # --- LI.FI ---
    ("lifi", f"{LIFI_BASE}/introduction/introduction"),
    ("lifi", f"{LIFI_BASE}/introduction/product-stack"),
    ("lifi", f"{LIFI_BASE}/introduction/tools"),
    ("lifi", f"{LIFI_BASE}/introduction/user-flows-and-examples/difference-between-quote-and-route"),
    ("lifi", f"{LIFI_BASE}/introduction/user-flows-and-examples/requesting-route-fetching-quote"),
    ("lifi", f"{LIFI_BASE}/introduction/user-flows-and-examples/status-tracking"),
    ("lifi", f"{LIFI_BASE}/faqs/route-availability"),
    ("lifi", f"{LIFI_BASE}/faqs/slippage-price-impact"),
    ("lifi", f"{LIFI_BASE}/guides/debug-failed-transactions"),
    ("lifi", f"{LIFI_BASE}/introduction/learn-more/security-and-audits"),
    # --- Morpho ---
    ("morpho", f"{MORPHO_BASE}/learn/concepts/blue"),
    ("morpho", f"{MORPHO_BASE}/developers/borrow/concepts/market-mechanics"),
    ("morpho", f"{MORPHO_BASE}/developers/borrow/concepts/ltv"),
    ("morpho", f"{MORPHO_BASE}/learn/concepts/irm"),
    ("morpho", f"{MORPHO_BASE}/developers/borrow/concepts/interest-rates"),
    ("morpho", f"{MORPHO_BASE}/learn/concepts/liquidation"),
    ("morpho", f"{MORPHO_BASE}/developers/borrow/concepts/liquidation"),
    ("morpho", f"{MORPHO_BASE}/learn/concepts/vault-v2"),
    ("morpho", f"{MORPHO_BASE}/developers/earn/concepts/vault-mechanics"),
    ("morpho", f"{MORPHO_BASE}/learn/concepts/oracle"),
    ("morpho", f"{MORPHO_BASE}/learn/resources/risks"),
]


def _fetch_md(url: str) -> str | None:
    try:
        resp = httpx.get(f"{url}.md", timeout=30, follow_redirects=True)
        if resp.status_code != 200 or not resp.text.strip():
            print(f"  skip {url} (HTTP {resp.status_code})")
            return None
        return resp.text
    except Exception as e:  # noqa: BLE001
        print(f"  skip {url} ({e})")
        return None


def _rows_for_page(protocol: str, url: str, md: str) -> list[dict]:
    md = strip_mdx(md)  # both sites are Mintlify; a no-op on already-clean markdown
    title = extract_title(md, url.rstrip("/").rsplit("/", 1)[-1])
    chunks = chunk_markdown(md)
    if not chunks:
        return []
    vectors = embed_passages([c.content for c in chunks])
    return [
        {
            "protocol": protocol,
            "source_url": url,
            "title": title,
            "section": c.section,
            "chunk_index": i,
            "content": c.content,
            "embedding": v,
        }
        for i, (c, v) in enumerate(zip(chunks, vectors, strict=True))
    ]


async def main() -> None:
    by_protocol: dict[str, list[dict]] = {}
    failed: set[str] = set()  # protocols with at least one failed/empty fetch
    pages_ok = 0
    for protocol, url in PAGES:
        md = _fetch_md(url)
        if md is None:
            failed.add(protocol)
            continue
        rows = _rows_for_page(protocol, url, md)
        if rows:
            by_protocol.setdefault(protocol, []).extend(rows)
            pages_ok += 1
            print(f"  ok   {url} -> {len(rows)} chunks")
        else:
            failed.add(protocol)

    sm = get_sessionmaker()
    if sm is None:
        print("No DATABASE_URL configured; aborting.")
        return
    async with sm() as session:
        for protocol, rows in by_protocol.items():
            if protocol in failed:
                # A partial fetch would make the rebuild shrink the corpus — keep the existing chunks instead.
                print(f"  WARN {protocol}: some pages failed to fetch; keeping existing chunks (not rebuilt)")
                continue
            await session.execute(delete(DocChunk).where(DocChunk.protocol == protocol))  # rebuild
            session.add_all([DocChunk(**r) for r in rows])
        await session.commit()

    written = {p: len(r) for p, r in by_protocol.items() if p not in failed}
    print(f"\nIngested {pages_ok}/{len(PAGES)} pages; wrote {sum(written.values())} chunks:")
    for protocol, n in written.items():
        print(f"  {protocol}: {n} chunks")
    for protocol in failed:
        print(f"  {protocol}: NOT rebuilt (fetch failures)")


if __name__ == "__main__":
    asyncio.run(main())
