"""HTTP edge for ingestion + document management. Handlers stay thin: parse the
request, call a service, shape the response. No business logic here.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile
from openai import OpenAIError

from app.chunking import ChunkSpan
from app.config import settings
from app.routers.deps import IngestServiceDep
from app.schemas import ChunkPreview, DocumentOut, IngestResult

router = APIRouter(prefix="/api", tags=["documents"])

# Cap uploads so a huge paste can't blow up the demo (and your token budget).
_MAX_BYTES = 1_000_000  # 1 MB


def _previews(spans: list[ChunkSpan]) -> list[ChunkPreview]:
    out: list[ChunkPreview] = []
    for i, s in enumerate(spans):
        prev_end = spans[i - 1].end if i > 0 else s.start
        overlap = max(0, prev_end - s.start)  # chars shared with the previous chunk
        out.append(
            ChunkPreview(
                ordinal=s.ordinal,
                start=s.start,
                end=s.end,
                overlap_prev=overlap,
                n_chars=s.n_chars,
                content=s.content,
            )
        )
    return out


@router.post("/ingest", response_model=IngestResult)
async def ingest(file: UploadFile, svc: IngestServiceDep) -> IngestResult:
    """Upload one text/markdown file. It's chunked, embedded, and stored. The
    response includes the chunk breakdown so the UI can show how it was split."""
    raw = await file.read()
    if len(raw) > _MAX_BYTES:
        raise HTTPException(413, f"File too large (max {_MAX_BYTES // 1000} KB).")
    try:
        doc, spans = await svc.ingest_file(file.filename or "untitled.txt", raw)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    except OpenAIError as e:
        # Embedding call failed (e.g. missing/invalid OPENAI_API_KEY) — clean 502.
        raise HTTPException(502, f"Embedding call failed: {e}") from e

    return IngestResult(
        document=DocumentOut(
            id=doc.id,
            filename=doc.filename,
            n_chars=doc.n_chars,
            n_chunks=len(spans),
            created_at=doc.created_at,
        ),
        message=f"Ingested '{doc.filename}' into {len(spans)} chunks.",
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        chunks=_previews(spans),
    )


@router.get("/documents", response_model=list[DocumentOut])
async def list_documents(svc: IngestServiceDep) -> list[DocumentOut]:
    rows = await svc.list_documents()
    return [
        DocumentOut(
            id=doc.id,
            filename=doc.filename,
            n_chars=doc.n_chars,
            n_chunks=count,
            created_at=doc.created_at,
        )
        for doc, count in rows
    ]


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(document_id: int, svc: IngestServiceDep) -> None:
    if not await svc.delete_document(document_id):
        raise HTTPException(404, "Document not found.")
