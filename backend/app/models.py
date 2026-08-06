"""SQLAlchemy ORM models — the shape of the two tables.

A **Document** is one uploaded file. It has many **Chunks**; each chunk stores a
slice of the text plus its embedding (a pgvector `vector(1024)` column). Retrieval
is a similarity search over Chunk.embedding.
"""
from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Index, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.config import settings


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str]
    n_chars: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    chunks: Mapped[list[Chunk]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",  # deleting a doc drops its chunks
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    ordinal: Mapped[int]  # position of this chunk within its document (0, 1, 2, …)
    content: Mapped[str]
    # The embedding. bge-m3 -> 1024 dims (settings.embed_dim). Cosine similarity
    # over this column IS the retrieval step.
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embed_dim))

    document: Mapped[Document] = relationship(back_populates="chunks")


# HNSW index for fast approximate nearest-neighbour search under cosine distance.
# For the tiny corpora in this demo a sequential scan is already instant; the
# index is here so you can see how a production store would be set up.
Index(
    "ix_chunks_embedding_hnsw",
    Chunk.embedding,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_cosine_ops"},
)
