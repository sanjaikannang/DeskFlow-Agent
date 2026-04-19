from __future__ import annotations

ROLE_TOOLS_MAP: dict[str, list[str]] = {
    "Developer": ["GitHub", "AWS", "Jira", "Slack", "Zoom", "Notion", "VS Code license"],
    "Tester": ["Jira", "TestRail", "Slack", "Notion", "Zoom"],
    "Sales": ["Salesforce", "HubSpot", "Slack", "Zoom", "Notion"],
    "HR": ["BambooHR", "Slack", "Google Workspace", "Notion", "Zoom"],
    "default": ["Slack", "Zoom", "Notion", "Google Workspace"],
}


def get_tools_for_role(role: str) -> list[str]:
    return ROLE_TOOLS_MAP.get(role, ROLE_TOOLS_MAP["default"])


def build_onboarding_checklist(role: str, new_hire_name: str) -> list[dict]:
    tools = get_tools_for_role(role)
    return [
        {
            "tool": tool,
            "action": "provision_access",
            "assignee": new_hire_name,
            "status": "pending",
        }
        for tool in tools
    ]


def build_offboarding_checklist(employee_name: str) -> list[dict]:
    all_tools = list(
        {tool for tools in ROLE_TOOLS_MAP.values() for tool in tools}
    )
    return [
        {
            "tool": tool,
            "action": "revoke_access",
            "assignee": employee_name,
            "status": "pending",
        }
        for tool in sorted(all_tools)
    ]
