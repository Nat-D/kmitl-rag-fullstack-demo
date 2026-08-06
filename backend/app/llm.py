"""Thin wrapper around the OpenAI-compatible proxy: embeddings + chat.

One shared AsyncOpenAI client, pointed at the class proxy (settings.openai_base_url)
with your personal key. Both the embed model (bge-m3) and the chat model
(gemma-4-E4B-it) are served by the same endpoint.
"""
from __future__ import annotations

from openai import AsyncOpenAI

from app.config import settings

client = AsyncOpenAI(base_url=settings.openai_base_url, api_key=settings.openai_api_key)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of strings -> one 1024-dim vector each. Used for both
    ingestion (embed every chunk) and retrieval (embed the query)."""
    if not texts:
        return []
    resp = await client.embeddings.create(model=settings.embed_model, input=texts)
    # The API preserves input order; sort by index to be safe.
    return [d.embedding for d in sorted(resp.data, key=lambda d: d.index)]


async def embed_query(text: str) -> list[float]:
    return (await embed_texts([text]))[0]


async def chat(system_prompt: str, user_message: str) -> str:
    """One-shot chat completion. The RAG 'agent' is: put retrieved context in the
    system prompt, then ask the model to answer using only that context."""
    resp = await client.chat.completions.create(
        model=settings.chat_model,
        temperature=0.2,  # low: we want grounded, repeatable answers, not creativity
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return resp.choices[0].message.content or ""
