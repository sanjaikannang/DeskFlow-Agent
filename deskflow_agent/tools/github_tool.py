from __future__ import annotations

import logging
import time

import httpx

from deskflow_agent.config import GITHUB_API_BASE, GITHUB_ORG, GITHUB_TOKEN

logger = logging.getLogger(__name__)


async def invite_to_github_org(
    username: str,
    org: str | None = None,
    team_slug: str | None = None,
) -> dict:
    """
    Sends a real GitHub org invitation using the GitHub REST API.
    POST https://api.github.com/orgs/{org}/invitations
    Returns: {success: bool, message: str, invitation_id: str}
    """
    target_org = org or GITHUB_ORG
    start = time.monotonic()

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # First resolve the username to a GitHub user ID
    async with httpx.AsyncClient(timeout=15.0) as client:
        # Step 1: Look up the user
        user_resp = await client.get(
            f"{GITHUB_API_BASE}/users/{username}",
            headers=headers,
        )

        if user_resp.status_code == 404:
            elapsed = round((time.monotonic() - start) * 1000)
            logger.warning("[github_tool] User '%s' not found — %dms", username, elapsed)
            return {
                "success": False,
                "message": f"GitHub user '{username}' does not exist.",
                "invitation_id": "",
            }

        if user_resp.status_code == 403:
            return {
                "success": False,
                "message": "GitHub API rate limit exceeded or insufficient token permissions.",
                "invitation_id": "",
            }

        user_resp.raise_for_status()
        user_id = user_resp.json()["id"]

        # Step 2: Check if user is already a member
        member_resp = await client.get(
            f"{GITHUB_API_BASE}/orgs/{target_org}/members/{username}",
            headers=headers,
        )
        if member_resp.status_code == 204:
            logger.info("[github_tool] User '%s' already in org '%s'.", username, target_org)
            return {
                "success": True,
                "message": f"User '{username}' is already a member of the '{target_org}' org.",
                "invitation_id": "",
            }

        # Step 3: Send invitation
        payload: dict = {"invitee_id": user_id}
        if team_slug:
            # Resolve team ID
            team_resp = await client.get(
                f"{GITHUB_API_BASE}/orgs/{target_org}/teams/{team_slug}",
                headers=headers,
            )
            if team_resp.status_code == 200:
                payload["team_ids"] = [team_resp.json()["id"]]

        invite_resp = await client.post(
            f"{GITHUB_API_BASE}/orgs/{target_org}/invitations",
            headers=headers,
            json=payload,
        )

        elapsed = round((time.monotonic() - start) * 1000)

        if invite_resp.status_code == 201:
            invitation_id = str(invite_resp.json().get("id", ""))
            logger.info(
                "[github_tool] Invitation sent to '%s' for org '%s' — id=%s (%dms)",
                username, target_org, invitation_id, elapsed,
            )
            return {
                "success": True,
                "message": f"GitHub org invitation sent to '{username}' for org '{target_org}'.",
                "invitation_id": invitation_id,
            }

        if invite_resp.status_code == 422:
            error_msg = invite_resp.json().get("message", "Unprocessable entity")
            logger.warning("[github_tool] 422 for '%s': %s (%dms)", username, error_msg, elapsed)
            return {
                "success": False,
                "message": f"Invitation failed: {error_msg}",
                "invitation_id": "",
            }

        invite_resp.raise_for_status()
        return {
            "success": False,
            "message": f"Unexpected status {invite_resp.status_code}",
            "invitation_id": "",
        }
