"""Pydantic request/response DTOs — the API's contract.

These are separate from the ORM models on purpose: the wire format (what the
frontend sees) shouldn't leak the database shape (e.g. we never send embeddings
to the browser — they're 1024 floats of noise to a human).
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    id: int
    filename: str
    n_chars: int
    n_chunks: int
    created_at: datetime


class ChunkPreview(BaseModel):
    """One chunk as produced by the chunker — surfaced so the ingestion page can
    VISUALISE how the file was split (size + where adjacent chunks overlap)."""
    ordinal: int
    start: int             # character offset of this chunk in the original text
    end: int               # exclusive end offset
    overlap_prev: int      # characters this chunk shares with the previous one
    n_chars: int
    content: str


class IngestResult(BaseModel):
    document: DocumentOut
    message: str
    chunk_size: int        # the configured window size (chars)
    chunk_overlap: int     # the configured overlap (chars)
    chunks: list[ChunkPreview]


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class RetrievedChunk(BaseModel):
    """One retrieved chunk, with its similarity score — surfaced to the UI so
    students can SEE what retrieval returned and how it was ranked."""
    chunk_id: int
    document_id: int
    filename: str
    ordinal: int
    score: float           # cosine similarity in [-1, 1]; higher = more similar
    content: str


class AskResponse(BaseModel):
    question: str
    answer: str
    used_context: bool                       # did any chunk clear the min_score floor?
    retrieved: list[RetrievedChunk]          # the ranked evidence
    system_prompt: str                       # the augmented prompt we actually sent
