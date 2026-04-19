from __future__ import annotations

import asyncio

from openai import AsyncOpenAI

from deskflow_agent.config import EMBEDDING_MODEL, OPENAI_API_KEY

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    return _client


async def embed_text(text: str) -> list[float]:
    response = await _get_client().embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding


async def embed_texts(texts: list[str]) -> list[list[float]]:
    response = await _get_client().embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]


def embed_text_sync(text: str) -> list[float]:
    """Synchronous wrapper for use in seeding scripts."""
    return asyncio.run(embed_text(text))


def embed_texts_sync(texts: list[str]) -> list[list[float]]:
    """Synchronous wrapper for use in seeding scripts."""
    return asyncio.run(embed_texts(texts))
