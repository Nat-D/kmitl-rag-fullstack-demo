"""The RAG 'agent': retrieve -> augment the system prompt -> generate an answer.

This is the payoff. Read `answer()` and you can see exactly what RAG *is*:
  1. retrieve the chunks relevant to the question,
  2. paste them into the system prompt as CONTEXT (this is the 'augmentation'),
  3. instruct the model to answer using only that context (and to say so when the
     context doesn't contain the answer),
  4. call the model.

Nothing here is magic — the "intelligence" is a normal chat call; RAG is the
prompt engineering around it plus the retrieval that fills it in.
"""
from __future__ import annotations

from app.llm import chat
from app.services.retrieval_service import Hit, RetrievalService

_NO_CONTEXT_SYSTEM = (
    "You are a helpful assistant for a document Q&A demo. The knowledge base "
    "returned no relevant passages for this question. Tell the user you don't have "
    "anything on that in the uploaded documents — do not answer from general "
    "knowledge."
)


def build_system_prompt(hits: list[Hit]) -> str:
    """Assemble the augmented system prompt from the retrieved chunks. Kept as a
    pure function so it's easy to read (and to unit-test) exactly what the model
    receives."""
    if not hits:
        return _NO_CONTEXT_SYSTEM

    blocks = []
    for i, h in enumerate(hits, start=1):
        # Number each source so the model can cite it as [1], [2], …
        blocks.append(f"[{i}] (from {h.filename}, chunk {h.ordinal})\n{h.content}")
    context = "\n\n".join(blocks)

    return (
        "You are a helpful assistant. Answer the user's question using ONLY the "
        "context below. If the answer isn't in the context, say you don't know — "
        "do not use outside knowledge. Cite the sources you use as [1], [2], etc.\n\n"
        "=== CONTEXT ===\n"
        f"{context}\n"
        "=== END CONTEXT ==="
    )


class ChatService:
    def __init__(self, retrieval: RetrievalService) -> None:
        self.retrieval = retrieval

    async def answer(self, question: str) -> tuple[str, list[Hit], str, bool]:
        hits = await self.retrieval.retrieve(question)      # 1. retrieve
        system_prompt = build_system_prompt(hits)           # 2. augment
        answer = await chat(system_prompt, question)        # 3-4. generate
        return answer, hits, system_prompt, bool(hits)
