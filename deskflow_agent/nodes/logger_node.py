from __future__ import annotations

import logging
import time

import motor.motor_asyncio

from deskflow_agent.config import MONGO_DB_NAME, MONGO_TRACES_COLLECTION, MONGODB_URI
from deskflow_agent.state import AgentState

logger = logging.getLogger(__name__)

_mongo_client: motor.motor_asyncio.AsyncIOMotorClient | None = None


def _get_mongo_client() -> motor.motor_asyncio.AsyncIOMotorClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
    return _mongo_client


async def logger_node(state: AgentState) -> AgentState:
    start = time.monotonic()
    logger.info("[logger_node] START — ticket_id=%s", state.get("ticket_id"))

    processing_start_ms = state.get("processing_start_ms", 0)
    now_ms = int(time.time() * 1000)
    total_duration_ms = (now_ms - processing_start_ms) if processing_start_ms else 0

    trace: dict = {
        "ticket_id": state.get("ticket_id"),
        "employee_id": state.get("employee_id"),
        "employee_name": state.get("employee_name"),
        "employee_role": state.get("employee_role"),
        "department": state.get("department"),
        "subject": state.get("subject"),
        "priority": state.get("priority"),
        "category": state.get("category"),
        "subcategory": state.get("subcategory"),
        "action_type": state.get("action_type"),
        "severity": state.get("severity"),
        "tools_mentioned": state.get("tools_mentioned"),
        "new_hire_name": state.get("new_hire_name"),
        "new_hire_role": state.get("new_hire_role"),
        "rag_confidence": state.get("rag_confidence"),
        "retrieved_chunks_count": len(state.get("retrieved_chunks") or []),
        "route": state.get("route"),
        "route_reason": state.get("route_reason"),
        "status": state.get("status"),
        "error": state.get("error"),
        "agent_response": state.get("agent_response"),
        "approval_payload": state.get("approval_payload"),
        "escalation_payload": state.get("escalation_payload"),
        "tools_called": state.get("tools_called"),
        "processing_start_ms": processing_start_ms,
        "processing_end_ms": now_ms,
        "total_duration_ms": total_duration_ms,
        "logged_at": now_ms,
    }

    try:
        client = _get_mongo_client()
        db = client[MONGO_DB_NAME]
        collection = db[MONGO_TRACES_COLLECTION]
        await collection.insert_one(trace)

        elapsed = round((time.monotonic() - start) * 1000)
        logger.info(
            "[logger_node] DONE in %dms — trace saved, total_duration=%dms",
            elapsed,
            total_duration_ms,
        )
    except Exception as exc:
        logger.error("[logger_node] MongoDB write failed: %s", exc)
        # Logging failure must never fail the overall pipeline

    return state
