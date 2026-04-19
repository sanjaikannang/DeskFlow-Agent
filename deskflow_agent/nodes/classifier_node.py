from __future__ import annotations

import json
import logging
import time

from openai import AsyncOpenAI

from deskflow_agent.config import LLM_MODEL, OPENAI_API_KEY
from deskflow_agent.prompts.classifier_prompt import (
    CLASSIFIER_SYSTEM_PROMPT,
    CLASSIFIER_USER_TEMPLATE,
)
from deskflow_agent.state import AgentState

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    return _client


async def classifier_node(state: AgentState) -> AgentState:
    start = time.monotonic()
    logger.info("[classifier_node] START — ticket_id=%s", state.get("ticket_id"))

    try:
        user_message = CLASSIFIER_USER_TEMPLATE.format(
            subject=state.get("subject", ""),
            raw_ticket_text=state.get("raw_ticket_text", ""),
            employee_name=state.get("employee_name", ""),
            employee_role=state.get("employee_role", ""),
            department=state.get("department", ""),
            priority=state.get("priority", "medium"),
        )

        response = await _get_client().chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )

        raw_json = response.choices[0].message.content or "{}"
        classification = json.loads(raw_json)

        elapsed = round((time.monotonic() - start) * 1000)
        logger.info(
            "[classifier_node] DONE in %dms — category=%s action_type=%s",
            elapsed,
            classification.get("category"),
            classification.get("action_type"),
        )

        return {
            **state,
            "category": classification.get("category", ""),
            "subcategory": classification.get("subcategory", ""),
            "severity": classification.get("severity", "medium"),
            "tools_mentioned": classification.get("tools_mentioned", []),
            "action_type": classification.get("action_type", ""),
            "new_hire_name": classification.get("new_hire_name", ""),
            "new_hire_role": classification.get("new_hire_role", ""),
            "status": "processing",
        }

    except json.JSONDecodeError as exc:
        logger.error("[classifier_node] JSON parse error: %s", exc)
        return {
            **state,
            "status": "failed",
            "error": f"Classifier JSON parse error: {exc}",
        }
    except Exception as exc:
        logger.error("[classifier_node] Unexpected error: %s", exc)
        return {
            **state,
            "status": "failed",
            "error": f"Classifier error: {exc}",
        }
