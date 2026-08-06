"""Data access for documents + chunks. The ONLY layer that writes SQL / touches
the ORM. Services call these methods; they never see a query.

The interesting method is `search_chunks`: the vector similarity search. Note it
returns a plain (Chunk, score) tuple — the retrieval math lives in the DB, via
pgvector's cosine-distance operator, not in Python.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import Chunk, Document


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ---- writes (ingestion) ----

    async def add_document(
        self,
        filename: str,
        n_chars: int,
        chunks: list[tuple[str, list[float]]],
    ) -> Document:
        """Insert one document and all its (content, embedding) chunks in a unit."""
        doc = Document(filename=filename, n_chars=n_chars)
        doc.chunks = [
            Chunk(ordinal=i, content=content, embedding=embedding)
            for i, (content, embedding) in enumerate(chunks)
        ]
        self.session.add(doc)
        await self.session.flush()  # assigns ids without ending the transaction
        return doc

    async def delete_document(self, document_id: int) -> bool:
        doc = await self.session.get(Document, document_id)
        if doc is None:
            return False
        await self.session.delete(doc)  # cascade removes its chunks
        return True

    # ---- reads ----

    async def list_documents(self) -> list[tuple[Document, int]]:
        """All documents, newest first, each with its chunk count."""
        stmt = (
            select(Document, func.count(Chunk.id))
            .outerjoin(Chunk, Chunk.document_id == Document.id)
            .group_by(Document.id)
            .order_by(Document.id.desc())
        )
        rows = await self.session.execute(stmt)
        return [(doc, count) for doc, count in rows.all()]

    async def search_chunks(
        self, query_embedding: list[float], top_k: int
    ) -> list[tuple[Chunk, float]]:
        """THE retrieval step. Rank every chunk by cosine similarity to the query
        vector and return the top_k, most-similar first.

        pgvector's `<=>` is cosine *distance* (0 = identical, 2 = opposite), so we
        convert to a similarity score = 1 - distance for an intuitive [-1, 1] range.
        """
        distance = Chunk.embedding.cosine_distance(query_embedding)
        stmt = (
            select(Chunk, (1 - distance).label("score"))
            # eager-load the parent document so the service can read
            # chunk.document.filename without a (illegal, in async) lazy load
            .options(joinedload(Chunk.document))
            .order_by(distance)  # ascending distance = descending similarity
            .limit(top_k)
        )
        rows = await self.session.execute(stmt)
        return [(chunk, float(score)) for chunk, score in rows.all()]
