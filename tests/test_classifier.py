"""Tests for classifier_node — uses mocked OpenAI responses."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from deskflow_agent.nodes.classifier_node import classifier_node


def _make_state(**overrides) -> dict:
    base = {
        "ticket_id": "TEST-001",
        "employee_id": "EMP-100",
        "employee_name": "Test User",
        "employee_role": "Developer",
        "department": "Engineering",
        "raw_ticket_text": "",
        "subject": "",
        "priority": "medium",
        "category": "",
        "subcategory": "",
        "severity": "",
        "tools_mentioned": [],
        "action_type": "",
        "new_hire_name": "",
        "new_hire_role": "",
        "retrieved_chunks": [],
        "rag_confidence": 0.0,
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


def _mock_llm_response(classification_dict: dict) -> MagicMock:
    mock_message = MagicMock()
    mock_message.content = json.dumps(classification_dict)
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


@pytest.mark.asyncio
async def test_classifier_software_access():
    state = _make_state(
        subject="Need access to GitHub",
        raw_ticket_text="Hi, I just joined the dev team and need access to our GitHub org. My username is dev_user.",
    )
    mock_response = _mock_llm_response({
        "category": "software_access",
        "subcategory": "new tool access",
        "action_type": "new_access",
        "severity": "low",
        "tools_mentioned": ["GitHub"],
        "new_hire_name": "",
        "new_hire_role": "",
        "joining_date": "",
    })

    with patch("deskflow_agent.nodes.classifier_node._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await classifier_node(state)

    assert result["category"] == "software_access"
    assert result["action_type"] == "new_access"
    assert "GitHub" in result["tools_mentioned"]
    assert result["status"] == "processing"


@pytest.mark.asyncio
async def test_classifier_hardware():
    state = _make_state(
        subject="Laptop very slow",
        raw_ticket_text="My MacBook is freezing constantly. The fan runs loud and everything takes forever.",
    )
    mock_response = _mock_llm_response({
        "category": "hardware",
        "subcategory": "performance issue",
        "action_type": "slow_laptop",
        "severity": "high",
        "tools_mentioned": [],
        "new_hire_name": "",
        "new_hire_role": "",
        "joining_date": "",
    })

    with patch("deskflow_agent.nodes.classifier_node._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await classifier_node(state)

    assert result["category"] == "hardware"
    assert result["action_type"] == "slow_laptop"
    assert result["severity"] == "high"


@pytest.mark.asyncio
async def test_classifier_onboarding():
    state = _make_state(
        subject="New hire onboarding",
        raw_ticket_text="We have a new developer joining Monday — Alice Smith. Please set up GitHub, AWS, Jira, and Slack.",
        employee_role="HR",
        department="HR",
    )
    mock_response = _mock_llm_response({
        "category": "onboarding",
        "subcategory": "new hire setup",
        "action_type": "full_onboarding",
        "severity": "medium",
        "tools_mentioned": ["GitHub", "AWS", "Jira", "Slack"],
        "new_hire_name": "Alice Smith",
        "new_hire_role": "Developer",
        "joining_date": "2026-04-21",
    })

    with patch("deskflow_agent.nodes.classifier_node._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await classifier_node(state)

    assert result["category"] == "onboarding"
    assert result["action_type"] == "full_onboarding"
    assert result["new_hire_name"] == "Alice Smith"
    assert result["new_hire_role"] == "Developer"
    assert "GitHub" in result["tools_mentioned"]


@pytest.mark.asyncio
async def test_classifier_json_parse_error():
    """Malformed JSON from LLM sets status=failed."""
    state = _make_state(subject="Test", raw_ticket_text="Test")

    mock_message = MagicMock()
    mock_message.content = "not valid json {{{"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch("deskflow_agent.nodes.classifier_node._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await classifier_node(state)

    assert result["status"] == "failed"
    assert "error" in result
    assert result["error"] != ""


@pytest.mark.asyncio
async def test_classifier_offboarding():
    state = _make_state(
        subject="Please revoke all access for John Doe",
        raw_ticket_text="John Doe is leaving today. Please disable all his accounts immediately.",
    )
    mock_response = _mock_llm_response({
        "category": "onboarding",
        "subcategory": "offboarding",
        "action_type": "offboarding",
        "severity": "high",
        "tools_mentioned": [],
        "new_hire_name": "",
        "new_hire_role": "",
        "joining_date": "",
    })

    with patch("deskflow_agent.nodes.classifier_node._get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        result = await classifier_node(state)

    assert result["category"] == "onboarding"
    assert result["action_type"] == "offboarding"
    assert result["severity"] == "high"
