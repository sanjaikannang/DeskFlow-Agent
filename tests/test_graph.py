"""End-to-end graph tests with fully mocked LLM and ChromaDB."""
from __future__ import annotations

import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from deskflow_agent import process_ticket


def _llm_mock(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def _classifier_response(category, action_type, tools=None, severity="medium"):
    return _llm_mock(json.dumps({
        "category": category,
        "subcategory": "test subcategory",
        "action_type": action_type,
        "severity": severity,
        "tools_mentioned": tools or [],
        "new_hire_name": "",
        "new_hire_role": "",
        "joining_date": "",
    }))


def _resolver_response():
    return _llm_mock("## Resolution\n\n1. Clear browser cache.\n2. Re-login via Okta.\n\nContact IT at support@deskflow.com if this persists.")


def _approval_summary_response():
    return _llm_mock("Employee requested new tool access. Manager approval required.")


def _escalation_brief_response():
    return _llm_mock(json.dumps({
        "issue_summary": "Employee laptop is completely broken and won't power on.",
        "what_was_tried": "Basic remote diagnostics — hardware failure confirmed.",
        "recommended_action": "Dispatch L1 technician and issue loaner laptop.",
    }))


def _base_ticket(**overrides) -> dict:
    base = {
        "ticket_id": "TEST-E2E-001",
        "employee_id": "EMP-999",
        "employee_name": "Jane Doe",
        "employee_role": "Developer",
        "department": "Engineering",
        "subject": "Test ticket",
        "raw_ticket_text": "Test description",
        "priority": "medium",
    }
    base.update(overrides)
    return base


def _patch_all(classifier_resp, resolution_resp=None, rag_chunks=None, rag_confidence=0.0):
    """Context manager factory that patches all external dependencies."""
    from contextlib import AsyncExitStack, contextmanager
    return _PatchContext(classifier_resp, resolution_resp, rag_chunks, rag_confidence)


class _PatchContext:
    def __init__(self, classifier_resp, resolution_resp, rag_chunks, rag_confidence):
        self.classifier_resp = classifier_resp
        self.resolution_resp = resolution_resp
        self.rag_chunks = rag_chunks or []
        self.rag_confidence = rag_confidence
        self._patches = []

    async def __aenter__(self):
        # Mock OpenAI client
        self.mock_client = MagicMock()
        call_count = [0]

        async def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return self.classifier_resp
            if self.resolution_resp:
                return self.resolution_resp
            return _approval_summary_response()

        self.mock_client.chat.completions.create = AsyncMock(side_effect=side_effect)

        # Mock RAG
        best_resolution = self.rag_chunks[0]["resolution"] if self.rag_chunks else ""

        import deskflow_agent.nodes.classifier_node as cn
        import deskflow_agent.rag.retriever as rv
        import deskflow_agent.nodes.logger_node as ln

        self.p1 = patch.object(cn, "_get_client", return_value=self.mock_client)
        self.p2 = patch("deskflow_agent.nodes.resolver_node._get_client", return_value=self.mock_client)
        self.p3 = patch("deskflow_agent.nodes.approval_node._get_client", return_value=self.mock_client)
        self.p4 = patch("deskflow_agent.nodes.escalation_node._get_client", return_value=self.mock_client)
        self.p5 = patch.object(
            rv, "retrieve_for_ticket",
            new_callable=AsyncMock,
            return_value=(self.rag_chunks, self.rag_confidence, best_resolution),
        )
        self.p6 = patch.object(ln, "_get_mongo_client", return_value=_make_mock_mongo())

        for p in [self.p1, self.p2, self.p3, self.p4, self.p5, self.p6]:
            p.start()

        return self

    async def __aexit__(self, *args):
        for p in [self.p1, self.p2, self.p3, self.p4, self.p5, self.p6]:
            p.stop()


def _make_mock_mongo():
    mock_collection = MagicMock()
    mock_collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id="fake_id"))
    mock_db = MagicMock()
    mock_db.__getitem__ = MagicMock(return_value=mock_collection)
    mock_client = MagicMock()
    mock_client.__getitem__ = MagicMock(return_value=mock_db)
    return mock_client


# ------------------------------------------------------------------ #
# Test: AUTO_RESOLVE path                                              #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_e2e_auto_resolve_login_error():
    """Software login_error + high RAG score → AUTO_RESOLVE → status=resolved."""
    ticket = _base_ticket(
        subject="Slack won't open",
        raw_ticket_text="Slack crashes on launch. I've tried restarting.",
    )
    good_chunks = [{
        "text": "Slack cache corruption fix",
        "score": 0.87,
        "ticket_id": "TKT-005",
        "resolution": "Delete Slack cache: ~/Library/Application Support/Slack/Cache",
        "category": "software_access",
        "action_type": "login_error",
        "source_collection": "past_tickets",
    }]

    async with _PatchContext(
        classifier_resp=_classifier_response("software_access", "login_error", ["Slack"]),
        resolution_resp=_resolver_response(),
        rag_chunks=good_chunks,
        rag_confidence=0.87,
    ):
        result = await process_ticket(ticket)

    assert result["route"] == "AUTO_RESOLVE"
    assert result["status"] == "resolved"
    assert result["agent_response"] != ""
    assert result["category"] == "software_access"


# ------------------------------------------------------------------ #
# Test: L2_APPROVAL path                                               #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_e2e_l2_approval_new_access():
    """Software new_access → always L2_APPROVAL → status=pending_approval."""
    ticket = _base_ticket(
        subject="Need GitHub access",
        raw_ticket_text="I need access to the company GitHub org.",
    )

    async with _PatchContext(
        classifier_resp=_classifier_response("software_access", "new_access", ["GitHub"]),
        resolution_resp=_approval_summary_response(),
        rag_confidence=0.0,
    ):
        result = await process_ticket(ticket)

    assert result["route"] == "L2_APPROVAL"
    assert result["status"] == "pending_approval"
    assert result["approval_payload"]["request_type"] == "new_access"
    assert "GitHub" in result["approval_payload"]["tools_requested"]
    assert "forwarded" in result["agent_response"].lower()


@pytest.mark.asyncio
async def test_e2e_l2_approval_onboarding():
    """Full onboarding → L2_APPROVAL → approval_payload has checklist."""
    ticket = _base_ticket(
        subject="New developer onboarding",
        raw_ticket_text="New hire Bob Smith joining Monday as Developer. Setup GitHub, AWS, Jira.",
        employee_role="HR",
    )

    async with _PatchContext(
        classifier_resp=_llm_mock(json.dumps({
            "category": "onboarding",
            "subcategory": "new hire setup",
            "action_type": "full_onboarding",
            "severity": "medium",
            "tools_mentioned": ["GitHub", "AWS", "Jira"],
            "new_hire_name": "Bob Smith",
            "new_hire_role": "Developer",
            "joining_date": "2026-04-21",
        })),
        resolution_resp=_approval_summary_response(),
        rag_confidence=0.0,
    ):
        result = await process_ticket(ticket)

    assert result["route"] == "L2_APPROVAL"
    assert result["status"] == "pending_approval"
    checklist = result["approval_payload"]["onboarding_checklist"]
    assert len(checklist) > 0
    tool_names = [item["tool"] for item in checklist]
    assert "GitHub" in tool_names


# ------------------------------------------------------------------ #
# Test: L1_ESCALATE path                                               #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_e2e_l1_escalate_physical_damage():
    """Hardware physical_damage → always L1_ESCALATE → status=escalated."""
    ticket = _base_ticket(
        subject="Laptop won't turn on",
        raw_ticket_text="My laptop is completely dead. Screen cracked after a drop.",
    )

    async with _PatchContext(
        classifier_resp=_classifier_response("hardware", "physical_damage", severity="high"),
        resolution_resp=_escalation_brief_response(),
        rag_confidence=0.0,
    ):
        result = await process_ticket(ticket)

    assert result["route"] == "L1_ESCALATE"
    assert result["status"] == "escalated"
    assert result["escalation_payload"]["escalation_level"] == "L1"
    assert "TEST-E2E-001" in result["agent_response"]


@pytest.mark.asyncio
async def test_e2e_l1_escalate_low_rag_login_error():
    """Software login_error + low RAG → L1_ESCALATE."""
    ticket = _base_ticket(
        subject="Cannot log into Jira",
        raw_ticket_text="Jira shows account deactivated error.",
    )

    async with _PatchContext(
        classifier_resp=_classifier_response("software_access", "login_error", ["Jira"]),
        resolution_resp=_escalation_brief_response(),
        rag_chunks=[{"text": "weak", "score": 0.50, "ticket_id": "TKT-X", "resolution": "not relevant", "category": "software_access", "action_type": "login_error", "source_collection": "past_tickets"}],
        rag_confidence=0.50,
    ):
        result = await process_ticket(ticket)

    assert result["route"] == "L1_ESCALATE"
    assert result["status"] == "escalated"


# ------------------------------------------------------------------ #
# Test: offboarding urgency                                            #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_e2e_offboarding_high_priority():
    """Offboarding → L2_APPROVAL with urgency_flag=True and high priority."""
    ticket = _base_ticket(
        subject="Offboard John Doe immediately",
        raw_ticket_text="John Doe is leaving today. Revoke all access now.",
    )

    async with _PatchContext(
        classifier_resp=_classifier_response("onboarding", "offboarding", severity="high"),
        resolution_resp=_approval_summary_response(),
        rag_confidence=0.0,
    ):
        result = await process_ticket(ticket)

    assert result["route"] == "L2_APPROVAL"
    assert result["approval_payload"]["urgency_flag"] is True
    assert result["approval_payload"]["priority"] == "high"


# ------------------------------------------------------------------ #
# Test: state completeness                                             #
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_e2e_result_has_all_required_keys():
    """All required AgentState keys are present in the final result."""
    ticket = _base_ticket(
        subject="Need Salesforce access",
        raw_ticket_text="I need Salesforce for my sales work.",
        employee_role="Sales",
    )

    async with _PatchContext(
        classifier_resp=_classifier_response("software_access", "new_access", ["Salesforce"]),
        resolution_resp=_approval_summary_response(),
        rag_confidence=0.0,
    ):
        result = await process_ticket(ticket)

    required_keys = [
        "ticket_id", "employee_id", "employee_name", "category", "action_type",
        "route", "route_reason", "status", "agent_response",
        "rag_confidence", "processing_start_ms",
    ]
    for key in required_keys:
        assert key in result, f"Missing key: {key}"
