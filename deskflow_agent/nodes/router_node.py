from __future__ import annotations

import logging
import time

from deskflow_agent.config import RAG_CONFIDENCE_THRESHOLD
from deskflow_agent.state import AgentState

logger = logging.getLogger(__name__)

AUTO_RESOLVE = "AUTO_RESOLVE"
L2_APPROVAL = "L2_APPROVAL"
L1_ESCALATE = "L1_ESCALATE"


def _route(state: AgentState) -> tuple[str, str]:
    """
    Pure decision-matrix logic — no LLM.
    Returns (route, route_reason).
    """
    category = state.get("category", "")
    action_type = state.get("action_type", "")
    rag_confidence = state.get("rag_confidence", 0.0)
    threshold = RAG_CONFIDENCE_THRESHOLD

    # ------------------------------------------------------------------ #
    # SOFTWARE / TOOL ACCESS                                               #
    # ------------------------------------------------------------------ #
    if category == "software_access":
        if action_type == "new_access":
            return (
                L2_APPROVAL,
                "New tool access requests always require L2 approval per IT policy.",
            )

        if action_type == "elevated_access":
            return (
                L2_APPROVAL,
                "Elevated/admin access requests always require L2 approval.",
            )

        if action_type == "login_error":
            if rag_confidence >= threshold:
                return (
                    AUTO_RESOLVE,
                    f"Login error with RAG confidence {rag_confidence:.2f} ≥ {threshold} — auto-resolving with past resolution.",
                )
            return (
                L1_ESCALATE,
                f"Login error with RAG confidence {rag_confidence:.2f} < {threshold} — escalating to L1 Support.",
            )

    # ------------------------------------------------------------------ #
    # HARDWARE                                                             #
    # ------------------------------------------------------------------ #
    if category == "hardware":
        if action_type == "physical_damage":
            return (
                L1_ESCALATE,
                "Physical damage (broken hardware / won't power on) always escalates to L1 Support.",
            )

        if action_type == "peripheral":
            return (
                L1_ESCALATE,
                "Peripheral issues are always escalated to L1 Support after RAG context is gathered.",
            )

        if action_type == "slow_laptop":
            if rag_confidence >= threshold:
                return (
                    AUTO_RESOLVE,
                    f"Slow/freezing laptop with RAG confidence {rag_confidence:.2f} ≥ {threshold} — auto-resolving.",
                )
            return (
                L1_ESCALATE,
                f"Slow/freezing laptop with RAG confidence {rag_confidence:.2f} < {threshold} — escalating to L1.",
            )

    # ------------------------------------------------------------------ #
    # ONBOARDING                                                           #
    # ------------------------------------------------------------------ #
    if category == "onboarding":
        if action_type == "offboarding":
            return (
                L2_APPROVAL,
                "Offboarding/access-revocation always requires L2 approval — marked high priority.",
            )

        if action_type in ("full_onboarding", "partial_onboarding"):
            return (
                L2_APPROVAL,
                f"{action_type.replace('_', ' ').title()} always requires L2 approval for provisioning.",
            )

    # ------------------------------------------------------------------ #
    # Fallback — unknown combination → safe escalation                    #
    # ------------------------------------------------------------------ #
    return (
        L1_ESCALATE,
        f"Unrecognized category='{category}' / action_type='{action_type}' — escalating to L1 for manual triage.",
    )


async def router_node(state: AgentState) -> AgentState:
    start = time.monotonic()
    logger.info("[router_node] START — ticket_id=%s", state.get("ticket_id"))

    if state.get("status") == "failed":
        logger.warning("[router_node] Skipping — upstream failure detected.")
        return state

    try:
        route, route_reason = _route(state)

        elapsed = round((time.monotonic() - start) * 1000)
        logger.info(
            "[router_node] DONE in %dms — route=%s", elapsed, route
        )

        return {**state, "route": route, "route_reason": route_reason}

    except Exception as exc:
        elapsed = round((time.monotonic() - start) * 1000)
        logger.error("[router_node] Error in %dms: %s", elapsed, exc)
        return {
            **state,
            "route": L1_ESCALATE,
            "route_reason": f"Router error — defaulting to L1 escalation. Error: {exc}",
            "status": "failed",
            "error": str(exc),
        }
