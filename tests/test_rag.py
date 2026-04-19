"""Tests for RAG retrieval — uses mocked ChromaDB and embedder."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from deskflow_agent.rag.retriever import query_collection, retrieve_for_ticket


def _make_chroma_result(docs, metadatas, distances):
    return {
        "documents": [docs],
        "metadatas": [metadatas],
        "distances": [distances],
    }


@pytest.mark.asyncio
async def test_query_collection_returns_scored_results():
    mock_collection = MagicMock()
    mock_collection.count.return_value = 5
    mock_collection.query.return_value = _make_chroma_result(
        docs=["Laptop was slow due to Chrome memory leak.", "Disk full caused slowdown."],
        metadatas=[
            {"ticket_id": "TKT-011", "resolution": "Kill Chrome, clear cache.", "category": "hardware", "action_type": "slow_laptop"},
            {"ticket_id": "TKT-014", "resolution": "Clear disk space.", "category": "hardware", "action_type": "slow_laptop"},
        ],
        distances=[0.15, 0.25],  # cosine distances → scores 0.85, 0.75
    )

    with (
        patch("deskflow_agent.rag.retriever.embed_text", new_callable=AsyncMock) as mock_embed,
        patch("deskflow_agent.rag.retriever.get_or_create_collection", return_value=mock_collection),
    ):
        mock_embed.return_value = [0.1] * 1536

        results = await query_collection("past_tickets", "My laptop is very slow", top_k=3)

    assert len(results) == 2
    assert results[0]["score"] == pytest.approx(0.85, abs=0.001)
    assert results[1]["score"] == pytest.approx(0.75, abs=0.001)
    assert results[0]["ticket_id"] == "TKT-011"
    assert "Kill Chrome" in results[0]["resolution"]


@pytest.mark.asyncio
async def test_query_collection_empty_returns_empty():
    mock_collection = MagicMock()
    mock_collection.count.return_value = 0

    with (
        patch("deskflow_agent.rag.retriever.embed_text", new_callable=AsyncMock) as mock_embed,
        patch("deskflow_agent.rag.retriever.get_or_create_collection", return_value=mock_collection),
    ):
        mock_embed.return_value = [0.1] * 1536
        results = await query_collection("past_tickets", "any query", top_k=3)

    assert results == []


@pytest.mark.asyncio
async def test_retrieve_for_ticket_merges_and_deduplicates():
    ticket_chunks = [
        {"text": "doc1", "score": 0.90, "ticket_id": "TKT-001", "resolution": "Fix 1", "category": "hardware", "action_type": "slow_laptop", "source_collection": "past_tickets"},
        {"text": "doc2", "score": 0.75, "ticket_id": "TKT-002", "resolution": "Fix 2", "category": "hardware", "action_type": "slow_laptop", "source_collection": "past_tickets"},
    ]
    runbook_chunks = [
        {"text": "runbook1", "score": 0.80, "ticket_id": "RB-001", "resolution": "Runbook fix", "category": "runbook", "action_type": "setup", "source_collection": "runbooks"},
    ]

    with patch("deskflow_agent.rag.retriever.query_collection") as mock_query:
        mock_query.side_effect = [ticket_chunks, runbook_chunks]

        merged, confidence, resolution = await retrieve_for_ticket("slow laptop")

    assert len(merged) == 3
    assert confidence == pytest.approx(0.90, abs=0.001)
    assert resolution == "Fix 1"
    # Verify sorted by score descending
    scores = [c["score"] for c in merged]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_retrieve_for_ticket_low_confidence():
    low_chunks = [
        {"text": "weak match", "score": 0.40, "ticket_id": "TKT-099", "resolution": "Irrelevant", "category": "hardware", "action_type": "slow_laptop", "source_collection": "past_tickets"},
    ]

    with patch("deskflow_agent.rag.retriever.query_collection") as mock_query:
        mock_query.side_effect = [low_chunks, []]

        merged, confidence, resolution = await retrieve_for_ticket("completely unrelated issue")

    assert confidence == 0.0
    assert resolution == ""


@pytest.mark.asyncio
async def test_retrieve_for_ticket_handles_collection_error():
    """If one collection throws, the other still returns results."""
    good_chunks = [
        {"text": "good doc", "score": 0.88, "ticket_id": "TKT-005", "resolution": "Clear cache.", "category": "software_access", "action_type": "login_error", "source_collection": "past_tickets"},
    ]

    call_count = 0

    async def mock_query(collection_name, query_text, top_k):
        nonlocal call_count
        call_count += 1
        if collection_name == "past_tickets":
            return good_chunks
        raise RuntimeError("Simulated runbook collection error")

    with patch("deskflow_agent.rag.retriever.query_collection", side_effect=mock_query):
        merged, confidence, resolution = await retrieve_for_ticket("login error")

    assert confidence == pytest.approx(0.88, abs=0.001)
    assert resolution == "Clear cache."
