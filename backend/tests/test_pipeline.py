"""Unit tests for the deterministic pieces of the pipeline — the parts that don't
need a database or the network. Run with:  uv run pytest  (from backend/).
"""
from __future__ import annotations

from app.chunking import split_text
from app.config import settings
from app.services.chat_service import build_system_prompt
from app.services.retrieval_service import Hit


def test_chunking_covers_text_with_overlap():
    text = "x" * 2000
    spans = split_text(text)
    # every character is covered, in order
    assert spans[0].start == 0
    assert spans[-1].end == 2000
    # adjacent chunks overlap by exactly chunk_overlap
    if len(spans) > 1:
        overlap = spans[0].end - spans[1].start
        assert overlap == settings.chunk_overlap
    # no chunk exceeds the window size
    assert all(s.n_chars <= settings.chunk_size for s in spans)


def test_chunking_empty_text():
    assert split_text("   ") == []


def test_system_prompt_with_no_hits_refuses_outside_knowledge():
    prompt = build_system_prompt([])
    assert "no relevant passages" in prompt.lower()


def test_system_prompt_embeds_context_and_citation_markers():
    hits = [
        Hit(chunk_id=1, document_id=1, filename="a.md", ordinal=0, score=0.9, content="Paris is the capital."),
        Hit(chunk_id=2, document_id=1, filename="a.md", ordinal=1, score=0.7, content="France is in Europe."),
    ]
    prompt = build_system_prompt(hits)
    assert "[1]" in prompt and "[2]" in prompt
    assert "Paris is the capital." in prompt
    assert "CONTEXT" in prompt
