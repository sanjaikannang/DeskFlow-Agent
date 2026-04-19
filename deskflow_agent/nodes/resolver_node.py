from __future__ import annotations

import logging
import time

from openai import AsyncOpenAI

from deskflow_agent.config import LLM_MODEL, OPENAI_API_KEY
from deskflow_agent.prompts.resolver_prompt import (
    RESOLVER_SYSTEM_PROMPT,
    RESOLVER_USER_TEMPLATE,
)
from deskflow_agent.state import AgentState

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    return _client


async def resolver_node(state: AgentState) -> AgentState:
    start = time.monotonic()
    logger.info("[resolver_node] START — ticket_id=%s", state.get("ticket_id"))

    try:
        tools_mentioned = state.get("tools_mentioned") or []
        tools_str = ", ".join(tools_mentioned) if tools_mentioned else "Not specified"

        rag_resolution = state.get("rag_resolution") or "No similar past resolution found."

        user_message = RESOLVER_USER_TEMPLATE.format(
            employee_name=state.get("employee_name", ""),
            employee_role=state.get("employee_role", ""),
            subject=state.get("subject", ""),
            raw_ticket_text=state.get("raw_ticket_text", ""),
            tools_mentioned=tools_str,
            rag_resolution=rag_resolution,
        )

        response = await _get_client().chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": RESOLVER_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
        )

        agent_response = response.choices[0].message.content or ""

        elapsed = round((time.monotonic() - start) * 1000)
        logger.info("[resolver_node] DONE in %dms — response length=%d", elapsed, len(agent_response))

        return {
            **state,
            "agent_response": agent_response,
            "status": "resolved",
        }

    except Exception as exc:
        elapsed = round((time.monotonic() - start) * 1000)
        logger.error("[resolver_node] Error in %dms: %s", elapsed, exc)
        return {
            **state,
            "agent_response": (
                f"Hi {state.get('employee_name', 'there')}, we encountered an issue generating "
                "your resolution. A support agent will follow up with you shortly."
            ),
            "status": "failed",
            "error": f"Resolver error: {exc}",
        }
