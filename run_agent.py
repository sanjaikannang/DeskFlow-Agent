"""
DeskFlow Agent — hardcoded test runner.

Run:
    uv run python run_agent.py

What this does:
  1. Runs 4 hardcoded tickets through the full agent pipeline
  2. Prints a detailed breakdown of input → output for each ticket
  3. Saves agent_flow.png (LangGraph node diagram) to the project root
"""
from __future__ import annotations

import asyncio
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

# ── Hardcoded test tickets ────────────────────────────────────────────────────

TICKETS = [
    # {
    #     "label": "Ticket 1 — GitHub access request  →  expected: L2_APPROVAL",
    #     "input": {
    #         "ticket_id": "TKT-DEMO-001",
    #         "employee_id": "EMP-101",
    #         "employee_name": "Sarah Chen",
    #         "employee_role": "Developer",
    #         "department": "Engineering",
    #         "subject": "Need access to GitHub org",
    #         "raw_ticket_text": (
    #             "Hi IT team, I just joined the engineering team and need to be added "
    #             "to the company GitHub org. My GitHub username is sarah_chen_dev. "
    #             "My manager is Alex Rodriguez."
    #         ),
    #         "priority": "medium",
    #     },
    # },
    # {
    #     "label": "Ticket 2 — Slack crashes on launch  →  expected: AUTO_RESOLVE or L1_ESCALATE (RAG-dependent)",
    #     "input": {
    #         "ticket_id": "TKT-DEMO-002",
    #         "employee_id": "EMP-202",
    #         "employee_name": "Mike Torres",
    #         "employee_role": "Sales Rep",
    #         "department": "Sales",
    #         "subject": "Slack crashes every time I open it",
    #         "raw_ticket_text": (
    #             "Slack keeps crashing when I try to open it. I click the icon and it "
    #             "just spins and crashes immediately. I've restarted my computer multiple "
    #             "times but the problem persists. Other apps work fine."
    #         ),
    #         "priority": "high",
    #     },
    # },
    {
        "label": "Ticket 3 — Cracked laptop screen  →  expected: L1_ESCALATE",
        "input": {
            "ticket_id": "TKT-DEMO-003",
            "employee_id": "EMP-303",
            "employee_name": "Emily Johnson",
            "employee_role": "Designer",
            "department": "Marketing",
            "subject": "Laptop screen cracked after drop",
            "raw_ticket_text": (
                "My laptop fell off my desk and the screen is now cracked. "
                "There's a large crack running across the display. The screen is "
                "partially visible but very hard to use. I need this fixed ASAP."
            ),
            "priority": "high",
        },
    },
    # {
    #     "label": "Ticket 4 — New employee full onboarding  →  expected: L2_APPROVAL",
    #     "input": {
    #         "ticket_id": "TKT-DEMO-004",
    #         "employee_id": "EMP-HR-001",
    #         "employee_name": "Lisa Park",
    #         "employee_role": "HR Manager",
    #         "department": "HR",
    #         "subject": "New developer onboarding — James Wilson",
    #         "raw_ticket_text": (
    #             "We have a new backend developer James Wilson starting next Monday. "
    #             "He will need GitHub org access, AWS console access, Jira, and Slack "
    #             "set up before his first day. His role is Senior Backend Engineer."
    #         ),
    #         "priority": "medium",
    #     },
    # },
]

# ── Pretty-print helpers ──────────────────────────────────────────────────────

ROUTE_ICON = {
    "AUTO_RESOLVE": "✅ AUTO_RESOLVE",
    "L2_APPROVAL":  "🔒 L2_APPROVAL",
    "L1_ESCALATE":  "🔧 L1_ESCALATE",
}

SEP  = "=" * 72
DASH = "-" * 72


def _print_input(ticket: dict) -> None:
    print(f"  ticket_id    : {ticket['ticket_id']}")
    print(f"  employee     : {ticket['employee_name']}  |  {ticket['employee_role']}  |  {ticket['department']}")
    print(f"  subject      : {ticket['subject']}")
    print(f"  priority     : {ticket['priority']}")
    print(f"  text         : {ticket['raw_ticket_text'][:140]}{'...' if len(ticket['raw_ticket_text']) > 140 else ''}")


def _print_output(result: dict) -> None:
    route = result.get("route", "")
    print(f"  route        : {ROUTE_ICON.get(route, route)}")
    print(f"  status       : {result.get('status')}")
    print(f"  category     : {result.get('category')}  /  {result.get('action_type')}")
    print(f"  severity     : {result.get('severity')}")
    print(f"  rag_conf     : {result.get('rag_confidence', 0.0):.2f}")
    print(f"  route_reason : {(result.get('route_reason') or '')[:100]}")
    print()

    agent_resp = result.get("agent_response") or ""
    print("  AGENT RESPONSE:")
    for line in agent_resp.splitlines():
        print(f"    {line}")

    ap = result.get("approval_payload") or {}
    if ap.get("agent_summary"):
        print(f"\n  APPROVAL SUMMARY:")
        print(f"    {ap['agent_summary']}")
    checklist = ap.get("onboarding_checklist") or []
    if checklist:
        print(f"\n  ONBOARDING CHECKLIST  ({len(checklist)} items):")
        for item in checklist[:6]:
            print(f"    •  {item.get('tool', '')}  →  {item.get('action', '')}")
        if len(checklist) > 6:
            print(f"    ... and {len(checklist) - 6} more")

    ep = result.get("escalation_payload") or {}
    if ep.get("issue_summary"):
        print(f"\n  ESCALATION BRIEF:")
        print(f"    issue     : {ep.get('issue_summary', '')}")
        print(f"    tried     : {ep.get('what_was_tried', '')}")
        print(f"    action    : {ep.get('recommended_action', '')}")

    if result.get("error"):
        print(f"\n  ⚠  ERROR: {result['error']}")


# ── Agent runner ──────────────────────────────────────────────────────────────

async def run_all() -> None:
    from deskflow_agent import process_ticket

    print(f"\n{SEP}")
    print("  DeskFlow Agent — Hardcoded Test Run")
    print(f"  {len(TICKETS)} tickets queued")
    print(SEP)

    for entry in TICKETS:
        print(f"\n{DASH}")
        print(f"  {entry['label']}")
        print(DASH)
        print("\n  INPUT:")
        _print_input(entry["input"])
        print()

        result = await process_ticket(entry["input"])

        print("  OUTPUT:")
        _print_output(result)

    print(f"\n{SEP}")


# ── Graph PNG generator ───────────────────────────────────────────────────────

def save_flow_png() -> None:
    print("\n  Generating agent_flow.png ...")
    try:
        from deskflow_agent.graph import build_graph
        compiled = build_graph().compile()
        png_bytes = compiled.get_graph().draw_mermaid_png()
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_flow.png")
        with open(out_path, "wb") as f:
            f.write(png_bytes)
        print(f"  Saved → {out_path}")
    except Exception as exc:
        print(f"  Could not generate PNG: {exc}")
        print("  To enable PNG export run:  uv add playwright && uv run playwright install chromium")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    asyncio.run(run_all())
    save_flow_png()
    print(f"\n{SEP}\n  All done.\n{SEP}\n")
