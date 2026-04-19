from __future__ import annotations

import asyncio
from functools import lru_cache

from deskflow_agent.config import EMBEDDING_MODEL, OLLAMA_BASE_URL


@lru_cache(maxsize=1)
def _get_client():
    from ollama import AsyncClient
    return AsyncClient(host=OLLAMA_BASE_URL)


async def embed_text(text: str) -> list[float]:
    response = await _get_client().embed(model=EMBEDDING_MODEL, input=text)
    return response.embeddings[0]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    response = await _get_client().embed(model=EMBEDDING_MODEL, input=texts)
    return response.embeddings


def embed_text_sync(text: str) -> list[float]:
    return asyncio.run(embed_text(text))


def embed_texts_sync(texts: list[str]) -> list[list[float]]:
    return asyncio.run(embed_texts(texts))
