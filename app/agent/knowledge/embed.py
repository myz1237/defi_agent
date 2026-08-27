"""Local text embeddings for RAG (bge-small, 384-dim, 512-token context). Loaded lazily and reused.

No external API: retrieval and ingestion both embed on-device. bge retrieval is asymmetric, so the query
gets an instruction prefix while passages do not. The tokenizer is exposed so chunking can budget by real
tokens (chunks are kept small enough that Contextual Retrieval's context + chunk stays under 512).
"""

from functools import lru_cache

MODEL_NAME = "BAAI/bge-small-en-v1.5"
_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def get_tokenizer():
    """The embedding model's HuggingFace tokenizer (for token-budget-aware chunking)."""
    return _model().tokenizer


def embed_passages(texts: list[str]) -> list[list[float]]:
    """Embed document chunks (no instruction), normalized for cosine similarity."""
    vecs = _model().encode(list(texts), normalize_embeddings=True)
    return [v.tolist() for v in vecs]


def embed_query(text: str) -> list[float]:
    """Embed a search query (bge instruction prefix), normalized for cosine similarity."""
    vec = _model().encode(_QUERY_INSTRUCTION + text, normalize_embeddings=True)
    return vec.tolist()
