from __future__ import annotations

from typing import List, TypedDict


class AgentState(TypedDict):
    # Ticket identity
    ticket_id: str
    employee_id: str
    employee_name: str
    employee_role: str          # Developer, Tester, Sales, HR
    department: str
    raw_ticket_text: str
    subject: str
    priority: str               # low, medium, high

    # Classifier output
    category: str               # software_access, hardware, onboarding
    subcategory: str
    severity: str
    tools_mentioned: List[str]  # e.g. ["GitHub", "Salesforce"]
    action_type: str            # new_access, login_error, elevated_access,
                                # slow_laptop, physical_damage, peripheral,
                                # full_onboarding, partial_onboarding, offboarding
    new_hire_name: str          # for onboarding tickets
    new_hire_role: str          # for onboarding tickets

    # RAG output
    retrieved_chunks: List[dict]   # [{text, score, ticket_id, resolution}]
    rag_confidence: float          # highest score from retrieval
    rag_resolution: str            # best matched past resolution

    # Router output
    route: str                  # AUTO_RESOLVE, L2_APPROVAL, L1_ESCALATE
    route_reason: str

    # Resolution output
    agent_response: str         # Final message to send to employee
    approval_payload: dict      # For L2 — structured approval request
    escalation_payload: dict    # For L1 — structured escalation context
    tools_called: List[dict]    # [{tool_name, status, result, duration_ms}]

    # Metadata
    processing_start_ms: int
    error: str
    status: str                 # processing, resolved, pending_approval, escalated, failed
