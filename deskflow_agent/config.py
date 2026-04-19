from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"Required environment variable '{key}' is not set.")
    return value


def _optional(key: str, default: str) -> str:
    return os.getenv(key) or default


# --- LLM Provider (auto-detected from whichever API key is set) ---
GROQ_API_KEY: str = _optional("GROQ_API_KEY", "")
GEMINI_API_KEY: str = _optional("GEMINI_API_KEY", "")

if GROQ_API_KEY:
    LLM_PROVIDER: str = "groq"
    LLM_MODEL: str = _optional("LLM_MODEL", "llama-3.3-70b-versatile")
elif GEMINI_API_KEY:
    LLM_PROVIDER: str = "gemini"
    LLM_MODEL: str = _optional("LLM_MODEL", "gemini-2.0-flash")
else:
    LLM_PROVIDER: str = ""
    LLM_MODEL: str = _optional("LLM_MODEL", "")

# --- Embeddings via Ollama (local) ---
OLLAMA_BASE_URL: str = _optional("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL: str = _optional("EMBEDDING_MODEL", "qwen3-embedding:0.6b")

# --- Runtime-only (validated inside the feature that uses them) ---
GITHUB_TOKEN: str = _optional("GITHUB_TOKEN", "")
GITHUB_ORG: str = _optional("GITHUB_ORG", "")
MONGODB_URI: str = _optional("MONGODB_URI", "")

# --- Storage ---
CHROMA_PERSIST_DIR: str = _optional("CHROMA_PERSIST_DIR", "./chroma_db")
RAG_CONFIDENCE_THRESHOLD: float = float(_optional("RAG_CONFIDENCE_THRESHOLD", "0.80"))

MONGO_DB_NAME: str = _optional("MONGO_DB_NAME", "deskflow")
MONGO_TRACES_COLLECTION: str = _optional("MONGO_TRACES_COLLECTION", "agent_traces")

GITHUB_API_BASE: str = "https://api.github.com"
