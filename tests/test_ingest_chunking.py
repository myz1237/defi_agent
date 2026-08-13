"""Unit tests for the pure ingestion helpers (no I/O)."""

from app.agent.knowledge.ingest import chunk_markdown, extract_title, strip_mdx


def test_strip_mdx_removes_jsx_and_imports_keeps_prose():
    md = (
        "import { Callout } from '@/components'\n"
        "export const meta = {}\n"
        "# Title\n\n"
        "<Callout type='warning'>Watch the LLTV.</Callout>\n\n"
        "Liquidation happens above LLTV.\n"
        "<ZoomableImage src='x' />\n"
    )
    out = strip_mdx(md)
    assert "import" not in out
    assert "export" not in out
    assert "<Callout" not in out and "</Callout>" not in out and "ZoomableImage" not in out
    assert "Watch the LLTV." in out
    assert "Liquidation happens above LLTV." in out


def test_extract_title_uses_first_h1_else_fallback():
    assert extract_title("## sub\n# Real Title\n", "slug") == "Real Title"
    assert extract_title("no heading here", "slug") == "slug"


def test_chunk_markdown_splits_by_heading_and_carries_section():
    md = "# Doc\n\n## Alpha\n\nfirst body\n\n## Beta\n\nsecond body\n"
    chunks = chunk_markdown(md)
    sections = [c.section for c in chunks]
    assert "Alpha" in sections and "Beta" in sections
    alpha = next(c for c in chunks if c.section == "Alpha")
    assert "Alpha" in alpha.content and "first body" in alpha.content


def test_strip_mdx_and_headings_are_code_fence_aware():
    md = (
        "---\n"
        "title: Setup\n"
        "description: how to install\n"
        "---\n\n"
        "# Setup\n\n"
        "Install the SDK.\n\n"
        "```bash\n"
        "# install the sdk\n"
        "import x from 'y'\n"
        "npm i @lifi/sdk\n"
        "```\n\n"
        "<Callout>outside the fence</Callout>\n"
    )
    out = strip_mdx(md)
    assert "title: Setup" not in out  # frontmatter stripped
    assert "# install the sdk" in out and "import x from 'y'" in out  # fenced code preserved
    assert "<Callout>" not in out and "outside the fence" in out  # JSX tag stripped, prose kept

    chunks = chunk_markdown(out)
    sections = [c.section for c in chunks]
    assert sections == ["Setup"]  # the '# install the sdk' inside the fence is not a heading
    assert extract_title(out, "slug") == "Setup"


def test_chunk_stays_within_max_chars_including_prefix():
    body = " ".join(["word"] * 400)  # long section with spaces to break on
    md = f"## Section\n\n{body}\n"
    chunks = chunk_markdown(md, max_chars=300, overlap=50)
    assert all(len(c.content) <= 300 for c in chunks)  # prefix accounted for; no mid-word overflow


def test_chunk_markdown_windows_long_sections_with_overlap():
    body = "x" * 3000  # one long section, no internal headings
    md = f"## Big\n\n{body}\n"
    chunks = chunk_markdown(md, max_chars=1000, overlap=200)
    assert len(chunks) >= 3  # 3000 chars / (1000-200 step) -> multiple windows
    assert all(c.section == "Big" for c in chunks)
    # consecutive chunks overlap: end of chunk N shares text with start of chunk N+1 (both are the 'x' body)
    assert all(c.content.startswith("Big\n\n") for c in chunks)
