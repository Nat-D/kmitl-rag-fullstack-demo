"""Ingestion pipeline: raw file bytes -> chunks -> embeddings -> stored rows.

This is the LEFT half of RAG (indexing). Read it top to bottom and you have the
whole "how does my document get into the vector DB" story in one function.
"""
from __future__ import annotations

from app.chunking import ChunkSpan, split_text
from app.llm import embed_texts
from app.models import Document
from app.repositories.document_repository import DocumentRepository


class IngestService:
    def __init__(self, repo: DocumentRepository) -> None:
        self.repo = repo

    async def ingest_file(
        self, filename: str, raw: bytes
    ) -> tuple[Document, list[ChunkSpan]]:
        # 1. Decode to text. (This demo handles plain text / markdown. A real app
        #    would branch on file type here — PDF, docx, HTML — to extract text.)
        text = raw.decode("utf-8", errors="replace")

        # 2. Split into overlapping chunks (spans carry offsets for the UI).
        spans = split_text(text)
        if not spans:
            raise ValueError("File has no readable text to ingest.")

        # 3. Embed every chunk in one batched call (each -> a 1024-dim vector).
        embeddings = await embed_texts([s.content for s in spans])

        # 4. Persist the document + its chunks (content paired with embedding).
        paired = [(s.content, e) for s, e in zip(spans, embeddings, strict=True)]
        doc = await self.repo.add_document(
            filename=filename, n_chars=len(text.strip()), chunks=paired
        )
        return doc, spans

    async def list_documents(self):
        return await self.repo.list_documents()

    async def delete_document(self, document_id: int) -> bool:
        return await self.repo.delete_document(document_id)
