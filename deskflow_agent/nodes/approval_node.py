from __future__ import annotations

import logging
import time

from deskflow_agent.llm import chat_completion
from deskflow_agent.prompts.resolver_prompt import APPROVAL_SUMMARY_PROMPT
from deskflow_agent.prompts.onboarding_tools_map import (
    build_offboarding_checklist,
    build_onboarding_checklist,
)
from deskflow_agent.state import AgentState

logger = logging.getLogger(__name__)


async def _generate_summary(state: AgentState) -> str:
    try:
        user_prompt = (
            f"Ticket: {state.get('subject', '')}\n\n"
            f"Description: {state.get('raw_ticket_text', '')}\n\n"
            f"Requested by: {state.get('employee_name', '')} ({state.get('department', '')})\n"
            f"Action type: {state.get('action_type', '')}\n"
            f"Tools: {', '.join(state.get('tools_mentioned') or [])}"
        )
        return await chat_completion(
            [
                {"role": "system", "content": APPROVAL_SUMMARY_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=200,
        )
    except Exception as exc:
        logger.warning("[approval_node] Summary generation failed: %s", exc)
        return f"Access request for {state.get('employee_name', '')} — see ticket for details."


async def approval_node(state: AgentState) -> AgentState:
    start = time.monotonic()
    logger.info("[approval_node] START — ticket_id=%s", state.get("ticket_id"))

    try:
        action_type = state.get("action_type", "")
        new_hire_name = state.get("new_hire_name") or state.get("employee_name", "")
        new_hire_role = state.get("new_hire_role") or state.get("employee_role", "")

        # Build checklist based on onboarding/offboarding type
        onboarding_checklist: list[dict] = []
        if action_type == "full_onboarding":
            onboarding_checklist = build_onboarding_checklist(new_hire_role, new_hire_name)
        elif action_type == "partial_onboarding":
            tools = state.get("tools_mentioned") or []
            onboarding_checklist = [
                {"tool": t, "action": "provision_access", "assignee": new_hire_name, "status": "pending"}
                for t in tools
            ]
        elif action_type == "offboarding":
            onboarding_checklist = build_offboarding_checklist(
                state.get("employee_name", "")
            )

        agent_summary = await _generate_summary(state)

        approval_payload: dict = {
            "ticket_id": state.get("ticket_id", ""),
            "request_type": action_type,
            "requested_by": state.get("employee_name", ""),
            "department": state.get("department", ""),
            "tools_requested": state.get("tools_mentioned") or [],
            "justification": state.get("raw_ticket_text", "")[:500],
            "priority": "high" if action_type == "offboarding" else state.get("priority", "medium"),
            "onboarding_checklist": onboarding_checklist,
            "agent_summary": agent_summary,
            "urgency_flag": action_type == "offboarding",
            "new_hire_name": new_hire_name if action_type in ("full_onboarding", "partial_onboarding") else "",
            "new_hire_role": new_hire_role if action_type in ("full_onboarding", "partial_onboarding") else "",
        }

        elapsed = round((time.monotonic() - start) * 1000)
        logger.info("[approval_node] DONE in %dms", elapsed)

        return {
            **state,
            "approval_payload": approval_payload,
            "agent_response": (
                "Your request has been forwarded to the IT team for approval. "
                "You will be notified once a decision is made."
            ),
            "status": "pending_approval",
        }

    except Exception as exc:
        elapsed = round((time.monotonic() - start) * 1000)
        logger.error("[approval_node] Error in %dms: %s", elapsed, exc)
        return {
            **state,
            "status": "failed",
            "error": f"Approval node error: {exc}",
        }
