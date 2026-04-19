"""Tests for router_node — verifies all 9 decision matrix cases."""
from __future__ import annotations

import pytest

from deskflow_agent.nodes.router_node import AUTO_RESOLVE, L1_ESCALATE, L2_APPROVAL, router_node


def _make_state(category: str, action_type: str, rag_confidence: float = 0.0, **overrides) -> dict:
    base = {
        "ticket_id": "TEST-001",
        "employee_id": "EMP-100",
        "employee_name": "Test User",
        "employee_role": "Developer",
        "department": "Engineering",
        "raw_ticket_text": "Test ticket",
        "subject": "Test",
        "priority": "medium",
        "category": category,
        "subcategory": "",
        "severity": "medium",
        "tools_mentioned": [],
        "action_type": action_type,
        "new_hire_name": "",
        "new_hire_role": "",
        "retrieved_chunks": [],
        "rag_confidence": rag_confidence,
        "rag_resolution": "",
        "route": "",
        "route_reason": "",
        "agent_response": "",
        "approval_payload": {},
        "escalation_payload": {},
        "tools_called": [],
        "processing_start_ms": 0,
        "error": "",
        "status": "processing",
    }
    base.update(overrides)
    return base


# ------------------------------------------------------------------ #
# SOFTWARE / TOOL ACCESS                                               #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_software_new_access_always_l2():
    """Software new_access → always L2_APPROVAL regardless of RAG confidence."""
    for rag in [0.0, 0.5, 0.95]:
        state = _make_state("software_access", "new_access", rag_confidence=rag)
        result = await router_node(state)
        assert result["route"] == L2_APPROVAL, f"Expected L2 at rag={rag}, got {result['route']}"


@pytest.mark.asyncio
async def test_software_elevated_access_always_l2():
    """Software elevated_access → always L2_APPROVAL."""
    state = _make_state("software_access", "elevated_access", rag_confidence=0.99)
    result = await router_node(state)
    assert result["route"] == L2_APPROVAL


@pytest.mark.asyncio
async def test_software_login_error_auto_resolve_above_threshold():
    """Software login_error with RAG ≥ 0.80 → AUTO_RESOLVE."""
    state = _make_state("software_access", "login_error", rag_confidence=0.85)
    result = await router_node(state)
    assert result["route"] == AUTO_RESOLVE


@pytest.mark.asyncio
async def test_software_login_error_escalate_below_threshold():
    """Software login_error with RAG < 0.80 → L1_ESCALATE."""
    state = _make_state("software_access", "login_error", rag_confidence=0.60)
    result = await router_node(state)
    assert result["route"] == L1_ESCALATE


@pytest.mark.asyncio
async def test_software_login_error_exact_threshold():
    """Software login_error with RAG exactly 0.80 → AUTO_RESOLVE (≥ threshold)."""
    state = _make_state("software_access", "login_error", rag_confidence=0.80)
    result = await router_node(state)
    assert result["route"] == AUTO_RESOLVE


# ------------------------------------------------------------------ #
# HARDWARE                                                             #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_hardware_physical_damage_always_l1():
    """Hardware physical_damage → always L1_ESCALATE."""
    for rag in [0.0, 0.95]:
        state = _make_state("hardware", "physical_damage", rag_confidence=rag)
        result = await router_node(state)
        assert result["route"] == L1_ESCALATE


@pytest.mark.asyncio
async def test_hardware_peripheral_always_l1():
    """Hardware peripheral → always L1_ESCALATE (even with high RAG)."""
    state = _make_state("hardware", "peripheral", rag_confidence=0.95)
    result = await router_node(state)
    assert result["route"] == L1_ESCALATE


@pytest.mark.asyncio
async def test_hardware_slow_laptop_auto_resolve():
    """Hardware slow_laptop with RAG ≥ 0.80 → AUTO_RESOLVE."""
    state = _make_state("hardware", "slow_laptop", rag_confidence=0.82)
    result = await router_node(state)
    assert result["route"] == AUTO_RESOLVE


@pytest.mark.asyncio
async def test_hardware_slow_laptop_escalate():
    """Hardware slow_laptop with RAG < 0.80 → L1_ESCALATE."""
    state = _make_state("hardware", "slow_laptop", rag_confidence=0.55)
    result = await router_node(state)
    assert result["route"] == L1_ESCALATE


# ------------------------------------------------------------------ #
# ONBOARDING                                                           #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_onboarding_full_always_l2():
    """Onboarding full_onboarding → always L2_APPROVAL."""
    state = _make_state("onboarding", "full_onboarding")
    result = await router_node(state)
    assert result["route"] == L2_APPROVAL


@pytest.mark.asyncio
async def test_onboarding_partial_always_l2():
    """Onboarding partial_onboarding → always L2_APPROVAL."""
    state = _make_state("onboarding", "partial_onboarding")
    result = await router_node(state)
    assert result["route"] == L2_APPROVAL


@pytest.mark.asyncio
async def test_onboarding_offboarding_always_l2():
    """Onboarding offboarding → always L2_APPROVAL."""
    state = _make_state("onboarding", "offboarding")
    result = await router_node(state)
    assert result["route"] == L2_APPROVAL


@pytest.mark.asyncio
async def test_offboarding_sets_high_priority_route_reason():
    """Offboarding route_reason should mention high priority."""
    state = _make_state("onboarding", "offboarding")
    result = await router_node(state)
    assert result["route"] == L2_APPROVAL
    assert "high priority" in result["route_reason"].lower() or "offboard" in result["route_reason"].lower()


# ------------------------------------------------------------------ #
# Edge cases                                                           #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_failed_state_is_passthrough():
    """A failed state is passed through without modification."""
    state = _make_state("software_access", "new_access", status="failed", error="upstream error")
    result = await router_node(state)
    assert result["status"] == "failed"
    assert result["route"] == ""


@pytest.mark.asyncio
async def test_unknown_category_escalates():
    """Unknown category defaults to L1_ESCALATE."""
    state = _make_state("unknown_category", "unknown_action")
    result = await router_node(state)
    assert result["route"] == L1_ESCALATE


@pytest.mark.asyncio
async def test_route_reason_populated():
    """Every valid route decision includes a non-empty route_reason."""
    cases = [
        ("software_access", "new_access", 0.0),
        ("hardware", "slow_laptop", 0.85),
        ("onboarding", "full_onboarding", 0.0),
    ]
    for cat, act, rag in cases:
        state = _make_state(cat, act, rag_confidence=rag)
        result = await router_node(state)
        assert result["route_reason"], f"Empty route_reason for {cat}/{act}"
