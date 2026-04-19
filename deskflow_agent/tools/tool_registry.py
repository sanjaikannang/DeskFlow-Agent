from __future__ import annotations

from typing import Callable

from deskflow_agent.tools.github_tool import invite_to_github_org
from deskflow_agent.tools.mock_tools import (
    create_hardware_support_ticket,
    provision_jira_access,
    provision_notion_access,
    provision_okta_account,
    provision_salesforce_access,
    revoke_all_access,
    send_slack_invite,
)

TOOL_REGISTRY: dict[str, Callable] = {
    "github_invite": invite_to_github_org,
    "salesforce_provision": provision_salesforce_access,
    "jira_provision": provision_jira_access,
    "slack_invite": send_slack_invite,
    "notion_provision": provision_notion_access,
    "okta_provision": provision_okta_account,
    "revoke_all_access": revoke_all_access,
    "hardware_ticket": create_hardware_support_ticket,
}


def get_tool(tool_name: str) -> Callable | None:
    return TOOL_REGISTRY.get(tool_name)


def list_tools() -> list[str]:
    return list(TOOL_REGISTRY.keys())
