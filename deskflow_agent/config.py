from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"Required environment variable '{key}' is not set.")
    return value


def _optional(key: str, default: str) -> str:
    return os.getenv(key, default)


# --- Required ---
OPENAI_API_KEY: str = _require("OPENAI_API_KEY")
GITHUB_TOKEN: str = _require("GITHUB_TOKEN")
GITHUB_ORG: str = _require("GITHUB_ORG")
MONGODB_URI: str = _require("MONGODB_URI")

# --- Optional with defaults ---
CHROMA_PERSIST_DIR: str = _optional("CHROMA_PERSIST_DIR", "./chroma_db")
EMBEDDING_MODEL: str = _optional("EMBEDDING_MODEL", "text-embedding-3-small")
LLM_MODEL: str = _optional("LLM_MODEL", "gpt-4o")
RAG_CONFIDENCE_THRESHOLD: float = float(_optional("RAG_CONFIDENCE_THRESHOLD", "0.80"))

MONGO_DB_NAME: str = _optional("MONGO_DB_NAME", "deskflow")
MONGO_TRACES_COLLECTION: str = _optional("MONGO_TRACES_COLLECTION", "agent_traces")

GITHUB_API_BASE: str = "https://api.github.com"
