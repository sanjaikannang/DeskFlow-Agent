from __future__ import annotations

import asyncio
import logging
import random
import time

logger = logging.getLogger(__name__)


def _now_ms() -> int:
    return int(time.time() * 1000)


def _fake_id(prefix: str) -> str:
    return f"{prefix}-{random.randint(100000, 999999)}"


async def provision_salesforce_access(
    email: str,
    role: str,
    department: str,
) -> dict:
    start = time.monotonic()
    await asyncio.sleep(random.uniform(0.08, 0.18))

    user_id = _fake_id("SF")
    elapsed = round((time.monotonic() - start) * 1000)
    result = {
        "success": True,
        "tool": "Salesforce",
        "action": "provision_access",
        "user_id": user_id,
        "email": email,
        "role": role,
        "department": department,
        "message": f"Salesforce account created for {email} with '{role}' role in {department}.",
        "timestamp_ms": _now_ms(),
        "duration_ms": elapsed,
    }
    logger.info("[mock_tools] Salesforce provisioned for %s in %dms", email, elapsed)
    return result


async def provision_jira_access(
    email: str,
    project_key: str,
    permission_level: str,
) -> dict:
    start = time.monotonic()
    await asyncio.sleep(random.uniform(0.05, 0.15))

    account_id = _fake_id("JIRA")
    elapsed = round((time.monotonic() - start) * 1000)
    result = {
        "success": True,
        "tool": "Jira",
        "action": "provision_access",
        "account_id": account_id,
        "email": email,
        "project_key": project_key,
        "permission_level": permission_level,
        "message": f"Jira account created for {email} with '{permission_level}' access to project {project_key}.",
        "timestamp_ms": _now_ms(),
        "duration_ms": elapsed,
    }
    logger.info("[mock_tools] Jira provisioned for %s in %dms", email, elapsed)
    return result


async def send_slack_invite(
    email: str,
    workspace: str,
    channels: list[str],
) -> dict:
    start = time.monotonic()
    await asyncio.sleep(random.uniform(0.06, 0.12))

    member_id = _fake_id("U")
    elapsed = round((time.monotonic() - start) * 1000)
    result = {
        "success": True,
        "tool": "Slack",
        "action": "send_invite",
        "member_id": member_id,
        "email": email,
        "workspace": workspace,
        "channels_added": channels,
        "message": f"Slack invite sent to {email} for workspace '{workspace}'. Added to {len(channels)} channels.",
        "timestamp_ms": _now_ms(),
        "duration_ms": elapsed,
    }
    logger.info("[mock_tools] Slack invite sent to %s in %dms", email, elapsed)
    return result


async def provision_notion_access(
    email: str,
    workspace: str,
    permission: str,
) -> dict:
    start = time.monotonic()
    await asyncio.sleep(random.uniform(0.07, 0.14))

    member_id = _fake_id("NTN")
    elapsed = round((time.monotonic() - start) * 1000)
    result = {
        "success": True,
        "tool": "Notion",
        "action": "provision_access",
        "member_id": member_id,
        "email": email,
        "workspace": workspace,
        "permission": permission,
        "message": f"Notion access granted to {email} in workspace '{workspace}' with '{permission}' permission.",
        "timestamp_ms": _now_ms(),
        "duration_ms": elapsed,
    }
    logger.info("[mock_tools] Notion provisioned for %s in %dms", email, elapsed)
    return result


async def provision_okta_account(
    email: str,
    first_name: str,
    last_name: str,
    role: str,
) -> dict:
    start = time.monotonic()
    await asyncio.sleep(random.uniform(0.10, 0.20))

    okta_id = _fake_id("00u")
    elapsed = round((time.monotonic() - start) * 1000)
    result = {
        "success": True,
        "tool": "Okta",
        "action": "provision_account",
        "okta_id": okta_id,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "role": role,
        "message": f"Okta account created for {first_name} {last_name} ({email}) with role '{role}'.",
        "timestamp_ms": _now_ms(),
        "duration_ms": elapsed,
    }
    logger.info("[mock_tools] Okta account created for %s in %dms", email, elapsed)
    return result


async def revoke_all_access(
    email: str,
    tools_list: list[str],
) -> dict:
    start = time.monotonic()
    await asyncio.sleep(random.uniform(0.15, 0.25))

    revoked = []
    failed = []
    for tool in tools_list:
        # Simulate rare failure (5% chance per tool)
        if random.random() < 0.05:
            failed.append(tool)
        else:
            revoked.append(tool)

    elapsed = round((time.monotonic() - start) * 1000)
    result = {
        "success": len(failed) == 0,
        "tool": "ALL",
        "action": "revoke_access",
        "email": email,
        "revoked_tools": revoked,
        "failed_tools": failed,
        "message": (
            f"Access revoked for {email} from {len(revoked)} tools."
            + (f" WARNING: Failed to revoke from: {failed}" if failed else "")
        ),
        "timestamp_ms": _now_ms(),
        "duration_ms": elapsed,
    }
    logger.info("[mock_tools] Access revoked for %s (%d tools) in %dms", email, len(revoked), elapsed)
    return result


async def create_hardware_support_ticket(
    employee_name: str,
    issue: str,
    location: str,
) -> dict:
    start = time.monotonic()
    await asyncio.sleep(random.uniform(0.05, 0.10))

    hw_ticket_id = _fake_id("HW")
    elapsed = round((time.monotonic() - start) * 1000)
    result = {
        "success": True,
        "tool": "HardwareSupport",
        "action": "create_ticket",
        "hw_ticket_id": hw_ticket_id,
        "employee_name": employee_name,
        "issue": issue,
        "location": location,
        "sla_hours": 24,
        "message": f"Hardware support ticket {hw_ticket_id} created for {employee_name}. L1 technician will contact within 24 hours.",
        "timestamp_ms": _now_ms(),
        "duration_ms": elapsed,
    }
    logger.info("[mock_tools] Hardware ticket %s created for %s in %dms", hw_ticket_id, employee_name, elapsed)
    return result
