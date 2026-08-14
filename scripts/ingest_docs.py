"""Ingest the vendored LI.FI & Morpho docs (docs/) into the pgvector doc_chunks store.

Reads the local `docs/<protocol>/*.md` corpus and `docs/manifest.json` (file -> canonical URL) — no network,
so ingestion is reproducible. For each file: clean MDX/HTML noise, heading-aware chunk with overlap, embed
locally (bge-small), and write per protocol (rebuild — delete that protocol's chunks then insert), so
re-running is idempotent. A protocol is only rebuilt when all of its files ingest OK, so a partial failure
keeps the existing corpus rather than silently shrinking it.

Refresh the corpus with scripts/fetch_docs.py first. Run: uv run python scripts/ingest_docs.py
"""

import asyncio
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from sqlalchemy import delete  # noqa: E402

from app.agent.knowledge.embed import embed_passages  # noqa: E402
from app.agent.knowledge.ingest import chunk_markdown, extract_title, strip_mdx  # noqa: E402
from app.storage.db import get_sessionmaker  # noqa: E402
from app.storage.models import DocChunk  # noqa: E402

DOCS_DIR = pathlib.Path(__file__).resolve().parent.parent / "docs"


def _rows_for_page(protocol: str, url: str, raw_md: str, slug: str) -> list[dict]:
    md = strip_mdx(raw_md)
    title = extract_title(md, slug)
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
    manifest_path = DOCS_DIR / "manifest.json"
    if not manifest_path.exists():
        print(f"No {manifest_path}; run scripts/fetch_docs.py first.")
        return
    manifest: dict[str, str] = json.loads(manifest_path.read_text())

    by_protocol: dict[str, list[dict]] = {}
    failed: set[str] = set()  # protocols with at least one missing/empty file
    pages_ok = 0
    for rel, url in sorted(manifest.items()):
        protocol = rel.split("/", 1)[0]
        path = DOCS_DIR / rel
        if not path.exists():
            print(f"  skip {rel} (missing)")
            failed.add(protocol)
            continue
        rows = _rows_for_page(protocol, url, path.read_text(encoding="utf-8"), pathlib.Path(rel).stem)
        if rows:
            by_protocol.setdefault(protocol, []).extend(rows)
            pages_ok += 1
            print(f"  ok   {rel} -> {len(rows)} chunks")
        else:
            print(f"  warn {rel} (no chunks)")
            failed.add(protocol)

    sm = get_sessionmaker()
    if sm is None:
        print("No DATABASE_URL configured; aborting.")
        return
    async with sm() as session:
        for protocol, rows in by_protocol.items():
            if protocol in failed:
                # A partial ingest would make the rebuild shrink the corpus — keep the existing chunks instead.
                print(f"  WARN {protocol}: some files failed; keeping existing chunks (not rebuilt)")
                continue
            await session.execute(delete(DocChunk).where(DocChunk.protocol == protocol))  # rebuild
            session.add_all([DocChunk(**r) for r in rows])
        await session.commit()

    written = {p: len(r) for p, r in by_protocol.items() if p not in failed}
    print(f"\nIngested {pages_ok}/{len(manifest)} pages; wrote {sum(written.values())} chunks:")
    for protocol, n in written.items():
        print(f"  {protocol}: {n} chunks")
    for protocol in failed:
        print(f"  {protocol}: NOT rebuilt (failures)")


if __name__ == "__main__":
    asyncio.run(main())
