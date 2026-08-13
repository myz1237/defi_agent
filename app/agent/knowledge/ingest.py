"""Pure helpers for turning protocol doc markdown into embeddable chunks.

Kept free of I/O so they're unit-testable; the fetch/embed/write orchestration lives in
scripts/ingest_docs.py. All parsing is fenced-code aware — headings, MDX tags, and import/export
statements inside ``` code fences are left untouched.
"""

import re
from dataclasses import dataclass

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
# MDX/JSX component tags use Capitalized names, e.g. <Callout>, <Steps>, <ZoomableImage/>.
_JSX_TAG = re.compile(r"</?[A-Z][A-Za-z0-9]*(?:\s[^>]*?)?/?>")
_IMPORT_EXPORT = re.compile(r"^(?:import|export)\s")
_FENCE = re.compile(r"^\s*```")
_FRONTMATTER = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
_BLANK_RUN = re.compile(r"\n{3,}")


@dataclass
class Chunk:
    section: str | None
    content: str


def strip_mdx(md: str) -> str:
    """Strip Mintlify frontmatter and MDX noise (JSX tags, import/export lines) outside code fences,
    while keeping prose, markdown, and fenced code examples intact."""
    if md.startswith("---\n"):
        md = _FRONTMATTER.sub("", md, count=1)
    out: list[str] = []
    in_fence = False
    for line in md.splitlines():
        if _FENCE.match(line):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        if _IMPORT_EXPORT.match(line):
            continue
        out.append(_JSX_TAG.sub("", line))
    return _BLANK_RUN.sub("\n\n", "\n".join(out)).strip()


def extract_title(md: str, fallback: str) -> str:
    """The first H1 (outside code fences), else the fallback (e.g. the URL slug)."""
    in_fence = False
    for line in md.splitlines():
        if _FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = _HEADING.match(line)
        if m and len(m.group(1)) == 1:
            return m.group(2).strip()
    return fallback


def _sections(md: str) -> list[tuple[str | None, str]]:
    sections: list[tuple[str | None, str]] = []
    head: str | None = None
    body: list[str] = []
    in_fence = False
    for line in md.splitlines():
        if _FENCE.match(line):
            in_fence = not in_fence
            body.append(line)
            continue
        m = _HEADING.match(line)
        if m and not in_fence:
            if body:
                sections.append((head, "\n".join(body).strip()))
            head = m.group(2).strip()
            body = []
        else:
            body.append(line)
    if body:
        sections.append((head, "\n".join(body).strip()))
    return sections


def chunk_markdown(md: str, max_chars: int = 1200, overlap: int = 150) -> list[Chunk]:
    """Heading-aware chunking: split into sections at markdown headings (ignoring headings inside code
    fences), then window long sections with overlap, breaking at whitespace to avoid mid-word cuts.
    Each chunk is prefixed with its heading for standalone context."""
    chunks: list[Chunk] = []
    for section_head, section_body in _sections(md):
        if not section_body:
            continue
        prefix = f"{section_head}\n\n" if section_head else ""
        budget = max(200, max_chars - len(prefix))  # keep chunk within max_chars including the prefix
        if len(section_body) <= budget:
            chunks.append(Chunk(section_head, prefix + section_body))
            continue
        start, n = 0, len(section_body)
        while start < n:
            end = min(start + budget, n)
            if end < n:  # break at the last whitespace before the boundary
                brk = section_body.rfind(" ", start + 1, end)
                if brk <= start:
                    brk = section_body.rfind("\n", start + 1, end)
                if brk > start:
                    end = brk
            piece = section_body[start:end].strip()
            if piece:
                chunks.append(Chunk(section_head, prefix + piece))
            if end >= n:
                break
            start = max(end - overlap, start + 1)
    return chunks
