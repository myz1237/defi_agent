"""Download the curated LI.FI & Morpho concept pages as markdown into the vendored `docs/` corpus.

Both sites are Mintlify: appending `.md` to a page URL returns markdown. We keep the raw `.md` under
`docs/<protocol>/<slug>.md` (version-controlled, so ingestion is reproducible and doesn't drift when the
sites change) plus `docs/manifest.json` mapping each file to its canonical URL (LI.FI's `.md` doesn't embed
its own source URL, so the manifest is the authoritative source for citations).

Run this only to (re)fresh the corpus; day-to-day ingestion reads the local files.
Run: uv run python scripts/fetch_docs.py
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402

DOCS_DIR = pathlib.Path(__file__).resolve().parent.parent / "docs"
LIFI_BASE = "https://docs.li.fi"
MORPHO_BASE = "https://docs.morpho.org"

# Curated conceptual pages (mechanics, not API reference).
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


def _slug(url: str) -> str:
    """A filename-safe, collision-free slug from the URL path (the full path, so the two 'liquidation'
    pages don't clash)."""
    path = url.split("://", 1)[-1].split("/", 1)[-1]  # drop scheme + domain
    return path.strip("/").replace("/", "-")


def main() -> None:
    manifest: dict[str, str] = {}
    ok = 0
    for protocol, url in PAGES:
        rel = f"{protocol}/{_slug(url)}.md"
        try:
            resp = httpx.get(f"{url}.md", timeout=30, follow_redirects=True)
            if resp.status_code != 200 or not resp.text.strip():
                print(f"  skip {url} (HTTP {resp.status_code})")
                continue
        except Exception as e:  # noqa: BLE001
            print(f"  skip {url} ({e})")
            continue
        dest = DOCS_DIR / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(resp.text, encoding="utf-8")
        manifest[rel] = url
        ok += 1
        print(f"  ok   {rel}")

    (DOCS_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"\nFetched {ok}/{len(PAGES)} pages into {DOCS_DIR} (+ manifest.json)")


if __name__ == "__main__":
    main()
