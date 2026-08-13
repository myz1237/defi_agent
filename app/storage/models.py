"""SQLAlchemy models for business tables (separate DB layer from the LangGraph checkpointer)."""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Embedding dimension for the local bge-small model (used by the RAG doc_chunks store).
EMBEDDING_DIM = 384


class Base(DeclarativeBase):
    pass


class User(Base):
    """A wallet-authenticated user (created on SIWE sign-in)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    address: Mapped[str] = mapped_column(String(42), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ApiKey(Base):
    """A widget/integration API key, validated against this table (with an env fallback)."""

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Thread(Base):
    """Conversation thread ownership/metadata (the message state itself lives in the checkpointer)."""

    __tablename__ = "threads"

    thread_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_used: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DocChunk(Base):
    """A chunk of protocol documentation with its embedding, for RAG retrieval (pgvector)."""

    __tablename__ = "doc_chunks"
    # Declare the HNSW index on the model so autogenerate stays aware of it (won't emit a spurious DROP).
    __table_args__ = (
        Index(
            "ix_doc_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    protocol: Mapped[str] = mapped_column(String(32), index=True)  # lifi | morpho
    source_url: Mapped[str] = mapped_column(String(512))
    title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    section: Mapped[str | None] = mapped_column(String(256), nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
