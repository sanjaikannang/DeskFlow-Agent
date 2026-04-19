from __future__ import annotations

import logging

from deskflow_agent.rag.chroma_client import get_or_create_collection
from deskflow_agent.rag.embedder import embed_text

logger = logging.getLogger(__name__)


async def query_collection(
    collection_name: str,
    query_text: str,
    top_k: int = 3,
) -> list[dict]:
    """Query a ChromaDB collection and return results with scores."""
    embedding = await embed_text(query_text)
    collection = get_or_create_collection(collection_name)

    count = collection.count()
    if count == 0:
        logger.warning("Collection '%s' is empty — no results returned.", collection_name)
        return []

    actual_k = min(top_k, count)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=actual_k,
        include=["documents", "metadatas", "distances"],
    )

    chunks: list[dict] = []
    if not results["documents"] or not results["documents"][0]:
        return chunks

    for doc, meta, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        # ChromaDB cosine distance → similarity score (1 - distance)
        score = round(1.0 - distance, 4)
        chunks.append(
            {
                "text": doc,
                "score": score,
                "ticket_id": meta.get("ticket_id", ""),
                "resolution": meta.get("resolution", ""),
                "category": meta.get("category", ""),
                "action_type": meta.get("action_type", ""),
                "source_collection": collection_name,
            }
        )
    return chunks


async def retrieve_for_ticket(query_text: str) -> tuple[list[dict], float, str]:
    """
    Query both past_tickets and runbooks collections.
    Returns (merged_chunks, rag_confidence, rag_resolution).
    """
    ticket_chunks, runbook_chunks = [], []

    try:
        ticket_chunks = await query_collection("past_tickets", query_text, top_k=3)
    except Exception as exc:
        logger.error("Error querying past_tickets: %s", exc)

    try:
        runbook_chunks = await query_collection("runbooks", query_text, top_k=2)
    except Exception as exc:
        logger.error("Error querying runbooks: %s", exc)

    # Merge, deduplicate by ticket_id, sort by score
    seen: set[str] = set()
    merged: list[dict] = []
    for chunk in ticket_chunks + runbook_chunks:
        key = chunk.get("ticket_id") or chunk.get("text", "")[:60]
        if key not in seen:
            seen.add(key)
            merged.append(chunk)

    merged.sort(key=lambda c: c["score"], reverse=True)

    if not merged or merged[0]["score"] < 0.50:
        return merged, 0.0, ""

    best = merged[0]
    return merged, best["score"], best.get("resolution", "")
