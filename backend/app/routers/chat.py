"""HTTP edge for the RAG question-answering endpoint.

Returns not just the answer but the *evidence* — the ranked retrieved chunks and
the exact augmented system prompt — so the frontend can show the whole pipeline,
not just the final text.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from openai import OpenAIError

from app.routers.deps import ChatServiceDep
from app.schemas import AskRequest, AskResponse, RetrievedChunk

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest, svc: ChatServiceDep) -> AskResponse:
    try:
        answer, hits, system_prompt, used_context = await svc.answer(req.question)
    except OpenAIError as e:
        # The proxy/key failed — surface a clean 502 instead of a stack trace.
        raise HTTPException(502, f"LLM call failed: {e}") from e

    return AskResponse(
        question=req.question,
        answer=answer,
        used_context=used_context,
        retrieved=[
            RetrievedChunk(
                chunk_id=h.chunk_id,
                document_id=h.document_id,
                filename=h.filename,
                ordinal=h.ordinal,
                score=round(h.score, 4),
                content=h.content,
            )
            for h in hits
        ],
        system_prompt=system_prompt,
    )
