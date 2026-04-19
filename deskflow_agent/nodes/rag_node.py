from __future__ import annotations

import logging
import time

from deskflow_agent.rag.retriever import retrieve_for_ticket
from deskflow_agent.state import AgentState

logger = logging.getLogger(__name__)


async def rag_node(state: AgentState) -> AgentState:
    start = time.monotonic()
    logger.info("[rag_node] START — ticket_id=%s", state.get("ticket_id"))

    if state.get("status") == "failed":
        logger.warning("[rag_node] Skipping — upstream failure detected.")
        return state

    query = f"{state.get('subject', '')} {state.get('raw_ticket_text', '')}"

    try:
        chunks, rag_confidence, rag_resolution = await retrieve_for_ticket(query)

        elapsed = round((time.monotonic() - start) * 1000)
        logger.info(
            "[rag_node] DONE in %dms — chunks=%d confidence=%.3f",
            elapsed,
            len(chunks),
            rag_confidence,
        )

        return {
            **state,
            "retrieved_chunks": chunks,
            "rag_confidence": rag_confidence,
            "rag_resolution": rag_resolution,
        }

    except Exception as exc:
        elapsed = round((time.monotonic() - start) * 1000)
        logger.error("[rag_node] Error in %dms: %s", elapsed, exc)
        # RAG failure is non-fatal — continue with zero confidence
        return {
            **state,
            "retrieved_chunks": [],
            "rag_confidence": 0.0,
            "rag_resolution": "",
        }
