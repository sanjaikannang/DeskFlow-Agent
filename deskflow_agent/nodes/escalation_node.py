from __future__ import annotations

import json
import logging
import time

from deskflow_agent.llm import chat_completion
from deskflow_agent.prompts.resolver_prompt import ESCALATION_SUMMARY_PROMPT
from deskflow_agent.state import AgentState

logger = logging.getLogger(__name__)


async def _generate_escalation_brief(state: AgentState) -> dict:
    try:
        rag_resolution = state.get("rag_resolution") or "No similar past resolution found."
        user_prompt = (
            f"Ticket: {state.get('subject', '')}\n\n"
            f"Description: {state.get('raw_ticket_text', '')}\n\n"
            f"Employee: {state.get('employee_name', '')} ({state.get('employee_role', '')}, "
            f"{state.get('department', '')})\n"
            f"Category: {state.get('category', '')} / {state.get('action_type', '')}\n"
            f"RAG confidence: {state.get('rag_confidence', 0.0):.2f}\n"
            f"Closest past resolution found:\n{rag_resolution}"
        )
        raw_json = await chat_completion(
            [
                {"role": "system", "content": ESCALATION_SUMMARY_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            json_mode=True,
            temperature=0.1,
            max_tokens=300,
        )
        return json.loads(raw_json)
    except Exception as exc:
        logger.warning("[escalation_node] Brief generation failed: %s", exc)
        return {
            "issue_summary": f"IT issue reported by {state.get('employee_name', '')} — see original ticket.",
            "what_was_tried": "Automated RAG retrieval attempted; no sufficient match found.",
            "recommended_action": "L1 support to contact employee and perform manual diagnosis.",
        }


async def escalation_node(state: AgentState) -> AgentState:
    start = time.monotonic()
    logger.info("[escalation_node] START — ticket_id=%s", state.get("ticket_id"))

    try:
        brief = await _generate_escalation_brief(state)

        escalation_payload: dict = {
            "ticket_id": state.get("ticket_id", ""),
            "escalation_level": "L1",
            "category": state.get("category", ""),
            "subcategory": state.get("subcategory", ""),
            "action_type": state.get("action_type", ""),
            "employee_name": state.get("employee_name", ""),
            "employee_id": state.get("employee_id", ""),
            "employee_role": state.get("employee_role", ""),
            "department": state.get("department", ""),
            "employee_location": "",  # to be filled by L1 team
            "issue_summary": brief.get("issue_summary", ""),
            "what_was_tried": brief.get("what_was_tried", ""),
            "recommended_action": brief.get("recommended_action", ""),
            "priority": state.get("severity", "medium"),
            "rag_confidence": state.get("rag_confidence", 0.0),
            "retrieved_chunks": state.get("retrieved_chunks") or [],
            "route_reason": state.get("route_reason", ""),
        }

        ticket_id = state.get("ticket_id", "N/A")
        elapsed = round((time.monotonic() - start) * 1000)
        logger.info("[escalation_node] DONE in %dms", elapsed)

        return {
            **state,
            "escalation_payload": escalation_payload,
            "agent_response": (
                f"Your issue has been escalated to our L1 IT support team. "
                f"They will reach out to you shortly. Ticket ID: {ticket_id}"
            ),
            "status": "escalated",
        }

    except Exception as exc:
        elapsed = round((time.monotonic() - start) * 1000)
        logger.error("[escalation_node] Error in %dms: %s", elapsed, exc)
        return {
            **state,
            "status": "failed",
            "error": f"Escalation node error: {exc}",
        }
