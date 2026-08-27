"""Pure helpers for turning protocol doc markdown into embeddable chunks.

Kept free of I/O so they're unit-testable; the fetch/embed/write orchestration lives in
scripts/ingest_docs.py. All parsing is fenced-code aware — headings, MDX tags, and import/export
statements inside ``` code fences are left untouched.
"""

import re
from dataclasses import dataclass

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
# HTML/JSX tags, either case — e.g. <Callout>, <ZoomableImage/>, <figure>, <img …>. Kept generic so
# image-only wrappers don't leave empty scaffolding behind after component tags are removed.
_TAG = re.compile(r"</?[a-zA-Z][A-Za-z0-9]*(?:\s[^>]*?)?/?>")
_IMPORT_EXPORT = re.compile(r"^(?:import|export)\s")
_SOURCE_LINE = re.compile(r"^Source:\s+https?://\S+\s*$")  # Morpho .md injects this boilerplate under each H1
# LI.FI .md prepends a blockquote pointing at its llms.txt index — boilerplate on every page.
_LLMS_LINE = re.compile(r"^>\s*.*(?:llms\.txt|Documentation Index|discover all available pages)", re.IGNORECASE)
_ANCHOR = re.compile(r"\s*\[#[A-Za-z0-9_-]+\]")  # Mintlify anchors, on headings & inline: "Foo [#foo]"
_FENCE = re.compile(r"^\s*```")
_FRONTMATTER = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
_BLANK_RUN = re.compile(r"\n{3,}")
_MIN_ALNUM = 3  # drop sections with essentially no text (empty figures / punctuation-only scaffolding)


@dataclass
class Chunk:
    section: str | None
    content: str


def _heading_text(raw: str) -> str:
    return _ANCHOR.sub("", raw).strip()


def _has_text(s: str) -> bool:
    return sum(ch.isalnum() for ch in s) >= _MIN_ALNUM


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
        if _IMPORT_EXPORT.match(line) or _SOURCE_LINE.match(line) or _LLMS_LINE.match(line):
            continue
        out.append(_ANCHOR.sub("", _TAG.sub("", line)))
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
            return _heading_text(m.group(2))
    return fallback


_HEADERS_TO_SPLIT = [("#" * i, f"h{i}") for i in range(1, 7)]  # h1..h6
# Chunk token budget (bge-small caps at 512): kept well under so Contextual Retrieval's context (~60 tok) +
# the heading prefix + chunk still fits without truncation at embed time.
_CHUNK_TOKENS = 400
_OVERLAP_TOKENS = 80
_CHUNK_CHARS = 1500  # char-based fallback (unit tests, or when no tokenizer is supplied)
_OVERLAP_CHARS = 200


def _body_splitter(tokenizer) -> RecursiveCharacterTextSplitter:
    if tokenizer is not None:  # budget by real embedding tokens
        return RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
            tokenizer, chunk_size=_CHUNK_TOKENS, chunk_overlap=_OVERLAP_TOKENS
        )
    return RecursiveCharacterTextSplitter(chunk_size=_CHUNK_CHARS, chunk_overlap=_OVERLAP_CHARS)


def chunk_markdown(md: str, tokenizer=None) -> list[Chunk]:
    """Heading-aware chunking via LangChain splitters: split into sections at markdown headings (fenced-code
    aware), then window long sections by token budget (falls back to a char budget without a tokenizer). The
    section heading is prepended to each chunk for standalone context; sections with no body text are dropped."""
    header_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=_HEADERS_TO_SPLIT, strip_headers=True)
    body_splitter = _body_splitter(tokenizer)
    chunks: list[Chunk] = []
    for doc in header_splitter.split_text(md):
        body = doc.page_content.strip()
        if not _has_text(body):  # drop image-only / scaffolding-only sections (heading with no real body)
            continue
        section = next((doc.metadata[k] for k in ("h6", "h5", "h4", "h3", "h2", "h1") if k in doc.metadata), None)
        prefix = f"{section}\n\n" if section else ""
        for piece in body_splitter.split_text(body):
            if _has_text(piece):
                chunks.append(Chunk(section, prefix + piece))
    return chunks
