"""Retrieval: a question -> the ranked chunks most relevant to it.

This is the RIGHT half of RAG (query time), step one. Embed the query with the
SAME model used at ingestion (so the vectors live in the same space), search the
store, then drop anything below the min_score floor — an off-topic question
should retrieve *nothing* rather than the "least irrelevant" chunk.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.config import settings
from app.llm import embed_query
from app.repositories.document_repository import DocumentRepository


@dataclass
class Hit:
    chunk_id: int
    document_id: int
    filename: str
    ordinal: int
    score: float
    content: str


class RetrievalService:
    def __init__(self, repo: DocumentRepository) -> None:
        self.repo = repo

    async def retrieve(self, question: str) -> list[Hit]:
        query_vec = await embed_query(question)
        rows = await self.repo.search_chunks(query_vec, top_k=settings.top_k)

        hits: list[Hit] = []
        for chunk, score in rows:
            if score < settings.min_score:
                continue  # below the floor: treat as "not relevant", skip it
            hits.append(
                Hit(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    filename=chunk.document.filename,
                    ordinal=chunk.ordinal,
                    score=score,
                    content=chunk.content,
                )
            )
        return hits
