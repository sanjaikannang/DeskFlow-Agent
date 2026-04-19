from __future__ import annotations

import json
import logging
import time

from deskflow_agent.llm import chat_completion
from deskflow_agent.prompts.classifier_prompt import (
    CLASSIFIER_SYSTEM_PROMPT,
    CLASSIFIER_USER_TEMPLATE,
)
from deskflow_agent.state import AgentState

logger = logging.getLogger(__name__)


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

        raw_json = await chat_completion(
            [
                {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            json_mode=True,
            temperature=0.0,
        )
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
