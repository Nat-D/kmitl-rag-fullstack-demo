"""Split a document into overlapping character windows.

Why chunk at all? An embedding is one vector for the whole input, so a 10-page
document embedded as a single vector is too coarse to retrieve a specific fact.
We slice the text into ~chunk_size pieces with a small overlap so a sentence that
straddles a boundary still lands whole in at least one chunk.

This is deliberately the simplest thing that works (fixed-size character windows).
Production systems chunk on sentences/tokens/markdown structure — but the pipeline
around it (embed -> store -> search) is identical.

`split_text` returns spans with character offsets so the ingestion UI can *show*
exactly where each chunk starts, ends, and overlaps its neighbour.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.config import settings


@dataclass
class ChunkSpan:
    ordinal: int
    start: int          # offset into the (stripped) source text, inclusive
    end: int            # exclusive
    content: str

    @property
    def n_chars(self) -> int:
        return len(self.content)


def split_text(text: str) -> list[ChunkSpan]:
    text = text.strip()
    if not text:
        return []

    size = settings.chunk_size
    overlap = settings.chunk_overlap
    step = max(1, size - overlap)

    spans: list[ChunkSpan] = []
    start = 0
    ordinal = 0
    while start < len(text):
        end = min(start + size, len(text))
        content = text[start:end]
        if content.strip():
            spans.append(ChunkSpan(ordinal=ordinal, start=start, end=end, content=content))
            ordinal += 1
        if end >= len(text):
            break
        start += step
    return spans


def chunk_text(text: str) -> list[str]:
    """Convenience: just the chunk strings (what the embedder needs)."""
    return [s.content for s in split_text(text)]
