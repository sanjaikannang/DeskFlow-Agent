"""
Seed ChromaDB with past resolved tickets and IT runbooks.
Run: python -m deskflow_agent.rag.seed_data
"""
from __future__ import annotations

import asyncio
import logging

from deskflow_agent.rag.chroma_client import get_or_create_collection
from deskflow_agent.rag.embedder import embed_texts

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Past resolved tickets (30+)
# ---------------------------------------------------------------------------

PAST_TICKETS: list[dict] = [
    # ---- SOFTWARE / TOOL ACCESS (10) ----
    {
        "ticket_id": "TKT-001",
        "ticket_text": "I need access to GitHub. I just joined the engineering team and my manager Alex asked me to get it set up. My GitHub username is john_dev.",
        "category": "software_access",
        "subcategory": "new tool access",
        "action_type": "new_access",
        "resolution": "Sent a GitHub org invitation to john_dev via the GitHub API. User accepted the invitation and was added to the Engineering team with member-level access.",
        "resolved_by": "L2_APPROVAL",
    },
    {
        "ticket_id": "TKT-002",
        "ticket_text": "Salesforce keeps saying my login credentials are invalid. I'm able to log into other tools fine. I've reset my password twice but still get the error.",
        "category": "software_access",
        "subcategory": "login error",
        "action_type": "login_error",
        "resolution": "1. Clear browser cache and cookies. 2. Try incognito mode. 3. Navigate to https://login.salesforce.com (not company subdomain). 4. Use the 'Forgot Password' flow to reset credentials. 5. If SSO is enabled, use the company SSO portal to log in instead. Issue was stale SSO session — resolved by logging in via Okta dashboard.",
        "resolved_by": "AUTO_RESOLVE",
    },
    {
        "ticket_id": "TKT-003",
        "ticket_text": "Jira won't let me log in. It shows 'Your account has been deactivated' even though I was using it yesterday.",
        "category": "software_access",
        "subcategory": "login error",
        "action_type": "login_error",
        "resolution": "1. Check with your Jira admin if the account was accidentally deactivated. 2. Log into the Atlassian admin portal. 3. Go to Users > find the affected user > click Activate. 4. If using SSO, verify that the Okta-Jira sync is active. Account was re-activated by IT admin within 10 minutes.",
        "resolved_by": "AUTO_RESOLVE",
    },
    {
        "ticket_id": "TKT-004",
        "ticket_text": "I need admin access to Jira to manage project settings for the Q3 release. Currently I only have member access.",
        "category": "software_access",
        "subcategory": "elevated access",
        "action_type": "elevated_access",
        "resolution": "L2 reviewer approved the admin access request. Jira project admin role granted by IT admin. User notified via email.",
        "resolved_by": "L2_APPROVAL",
    },
    {
        "ticket_id": "TKT-005",
        "ticket_text": "Slack is not opening. I click the icon and it just spins and crashes. I've tried restarting my computer.",
        "category": "software_access",
        "subcategory": "tool not launching",
        "action_type": "login_error",
        "resolution": "1. Fully quit Slack (Cmd+Q on Mac / right-click tray icon > Quit on Windows). 2. Clear Slack cache: delete ~/Library/Application Support/Slack/Cache on Mac. 3. Reinstall Slack from https://slack.com/downloads. 4. Sign in again via your workspace URL. Corrupted cache was the root cause.",
        "resolved_by": "AUTO_RESOLVE",
    },
    {
        "ticket_id": "TKT-006",
        "ticket_text": "I need access to Notion for my team's documentation. I'm a new developer and my team uses it for sprint planning.",
        "category": "software_access",
        "subcategory": "new tool access",
        "action_type": "new_access",
        "resolution": "Notion workspace invitation sent to employee email. User joined the Engineering workspace with Editor access. Team pages shared by manager.",
        "resolved_by": "L2_APPROVAL",
    },
    {
        "ticket_id": "TKT-007",
        "ticket_text": "AWS console is showing 'AccessDeniedException' when I try to access the S3 buckets. I need this for my deployment work.",
        "category": "software_access",
        "subcategory": "login error",
        "action_type": "login_error",
        "resolution": "1. Verify your IAM role has S3 permissions — go to AWS IAM > Roles. 2. Check if your session has expired: log out and log back in. 3. If using assumed roles, re-run: aws sts assume-role. 4. Contact IT to verify the S3BucketAccess policy is attached to your IAM user. Policy was missing — IT admin re-attached the S3ReadWrite policy.",
        "resolved_by": "AUTO_RESOLVE",
    },
    {
        "ticket_id": "TKT-008",
        "ticket_text": "I need access to HubSpot CRM. I'm on the sales team and need to manage my leads pipeline.",
        "category": "software_access",
        "subcategory": "new tool access",
        "action_type": "new_access",
        "resolution": "HubSpot Sales Hub invitation sent. User added to Sales team with Sales Rep permissions. Manager notified.",
        "resolved_by": "L2_APPROVAL",
    },
    {
        "ticket_id": "TKT-009",
        "ticket_text": "Zoom isn't connecting to video calls. I get 'Unable to connect' error every time. Audio works but video fails.",
        "category": "software_access",
        "subcategory": "tool not launching",
        "action_type": "login_error",
        "resolution": "1. Check camera permissions: System Preferences > Privacy & Security > Camera > enable Zoom. 2. Test your camera in Zoom Settings > Video. 3. Quit Zoom fully and restart. 4. Update Zoom to the latest version. 5. If on a company device, check if MDM policy is blocking camera access — submit to IT. Camera permission was blocked by macOS privacy settings — resolved by enabling in System Preferences.",
        "resolved_by": "AUTO_RESOLVE",
    },
    {
        "ticket_id": "TKT-010",
        "ticket_text": "I need admin access to our AWS account to manage IAM roles and set up CI/CD pipelines for the team.",
        "category": "software_access",
        "subcategory": "elevated access",
        "action_type": "elevated_access",
        "resolution": "L2 reviewed and approved limited admin access. IAM PowerUser policy attached (not full admin). Approval documented in the IT access log.",
        "resolved_by": "L2_APPROVAL",
    },

    # ---- HARDWARE (10) ----
    {
        "ticket_id": "TKT-011",
        "ticket_text": "My MacBook Pro is extremely slow. It freezes for 10-15 seconds every few minutes. The fan is running loudly all the time.",
        "category": "hardware",
        "subcategory": "performance issue",
        "action_type": "slow_laptop",
        "resolution": "1. Open Activity Monitor > CPU tab — sort by CPU usage and kill runaway processes. 2. Check RAM usage in Activity Monitor > Memory tab. 3. Run: sudo purge in Terminal to clear RAM cache. 4. Disable Login Items: System Settings > General > Login Items. 5. Run Disk Utility > First Aid to check disk health. 6. Consider upgrading to 16GB RAM if currently on 8GB. Issue was a memory leak in the browser — resolved by restarting Chrome and disabling heavy extensions.",
        "resolved_by": "AUTO_RESOLVE",
    },
    {
        "ticket_id": "TKT-012",
        "ticket_text": "Laptop won't turn on at all. Pressed the power button multiple times, nothing happens. It was working fine yesterday.",
        "category": "hardware",
        "subcategory": "power failure",
        "action_type": "physical_damage",
        "resolution": "L1 support dispatched to employee location. Diagnosed as failed logic board. Laptop sent to Apple Authorized Service. Loaner laptop issued within 24 hours.",
        "resolved_by": "L1_ESCALATE",
    },
    {
        "ticket_id": "TKT-013",
        "ticket_text": "My laptop screen has a large crack after it fell off the desk. The display is partially working but hard to see.",
        "category": "hardware",
        "subcategory": "physical damage",
        "action_type": "physical_damage",
        "resolution": "L1 support created hardware replacement ticket. IT provided loaner device. Original laptop sent for screen repair. Insurance claim filed.",
        "resolved_by": "L1_ESCALATE",
    },
    {
        "ticket_id": "TKT-014",
        "ticket_text": "My laptop is running very slow after the latest macOS update. Everything takes forever to load.",
        "category": "hardware",
        "subcategory": "performance issue",
        "action_type": "slow_laptop",
        "resolution": "1. Restart in Safe Mode (hold Shift during boot) to test if performance improves. 2. Go to System Settings > Software Update and check for any additional patches. 3. Disable heavy login items. 4. Run: brew cleanup if Homebrew is installed. 5. Reset NVRAM: restart and hold Option+Cmd+P+R. Post-update kernel extension conflict resolved after NVRAM reset.",
        "resolved_by": "AUTO_RESOLVE",
    },
    {
        "ticket_id": "TKT-015",
        "ticket_text": "My external keyboard is not being recognized. USB keyboard works fine on other computers but not mine.",
        "category": "hardware",
        "subcategory": "peripheral issue",
        "action_type": "peripheral",
        "resolution": "Attempted: 1. Try different USB port. 2. Restart keyboard receiver. 3. Reset SMC. L1 support was dispatched as these steps did not resolve the issue. IT replaced USB hub.",
        "resolved_by": "L1_ESCALATE",
    },
    {
        "ticket_id": "TKT-016",
        "ticket_text": "My external monitor stopped working. It was fine before. Now it just says 'No Signal' even though the cable is connected.",
        "category": "hardware",
        "subcategory": "peripheral issue",
        "action_type": "peripheral",
        "resolution": "Attempted: 1. Try different display cable (HDMI/DisplayPort). 2. Test monitor with another laptop. 3. Reset display settings: System Settings > Displays > Detect Displays. L1 dispatched to test with replacement cable and inspect GPU output. Faulty DisplayPort cable replaced.",
        "resolved_by": "L1_ESCALATE",
    },
    {
        "ticket_id": "TKT-017",
        "ticket_text": "My laptop keeps overheating and shutting down unexpectedly. This happens every 30-45 minutes.",
        "category": "hardware",
        "subcategory": "performance issue",
        "action_type": "slow_laptop",
        "resolution": "1. Clean laptop vents with compressed air. 2. Use a laptop stand to improve airflow. 3. Install TG Pro or iStatMenus to monitor temperature. 4. Reduce CPU-intensive tasks running in background. 5. Reset SMC: shut down, hold Ctrl+Option+Shift+Power for 10 seconds. Thermal paste replacement recommended if overheating persists after these steps.",
        "resolved_by": "AUTO_RESOLVE",
    },
    {
        "ticket_id": "TKT-018",
        "ticket_text": "I spilled coffee on my laptop keyboard. Some keys are sticking and a few aren't working at all.",
        "category": "hardware",
        "subcategory": "physical damage",
        "action_type": "physical_damage",
        "resolution": "L1 support instructed employee to immediately power off the laptop. Device retrieved by IT for liquid damage assessment. Keyboard replacement ordered. Loaner device provided.",
        "resolved_by": "L1_ESCALATE",
    },
    {
        "ticket_id": "TKT-019",
        "ticket_text": "My mouse isn't working properly. The scroll wheel is not responding and the cursor jumps around randomly.",
        "category": "hardware",
        "subcategory": "peripheral issue",
        "action_type": "peripheral",
        "resolution": "Attempted: 1. Replace mouse batteries. 2. Clean the optical sensor with compressed air. 3. Try on a different surface/mousepad. L1 dispatched as basic steps insufficient. New mouse issued by IT.",
        "resolved_by": "L1_ESCALATE",
    },
    {
        "ticket_id": "TKT-020",
        "ticket_text": "My laptop battery drains very fast — from 100% to dead in under 2 hours. Used to last 8 hours.",
        "category": "hardware",
        "subcategory": "performance issue",
        "action_type": "slow_laptop",
        "resolution": "1. Check Battery Health: System Settings > Battery > Battery Health. 2. Identify battery-draining apps: Activity Monitor > Energy tab. 3. Disable features: reduce screen brightness, turn off WiFi when not needed. 4. Reset SMC to recalibrate battery readings. If battery health is below 80%, IT will approve a battery replacement.",
        "resolved_by": "AUTO_RESOLVE",
    },

    # ---- ONBOARDING / OFFBOARDING (10) ----
    {
        "ticket_id": "TKT-021",
        "ticket_text": "Hi IT team, we have a new developer joining next Monday — Sarah Chen. She'll need full developer setup including GitHub, AWS, Jira, and Slack.",
        "category": "onboarding",
        "subcategory": "new hire setup",
        "action_type": "full_onboarding",
        "resolution": "Full Developer onboarding checklist approved by L2. Provisioned: GitHub org invite, AWS IAM account, Jira Software account, Slack workspace invite, Notion access, Zoom license. All completed 1 day before start date.",
        "resolved_by": "L2_APPROVAL",
    },
    {
        "ticket_id": "TKT-022",
        "ticket_text": "New sales rep Michael Torres is joining on Friday. Please set up his Salesforce, HubSpot, Slack, and Zoom accounts.",
        "category": "onboarding",
        "subcategory": "new hire setup",
        "action_type": "full_onboarding",
        "resolution": "Sales onboarding approved. Provisioned: Salesforce Sales Cloud account, HubSpot CRM access, Slack workspace invite, Zoom Pro license, Notion workspace access. Manager notified of completion.",
        "resolved_by": "L2_APPROVAL",
    },
    {
        "ticket_id": "TKT-023",
        "ticket_text": "Emily Rodriguez from HR is starting Monday. She needs BambooHR admin access, Google Workspace, Slack, and Notion set up.",
        "category": "onboarding",
        "subcategory": "new hire setup",
        "action_type": "full_onboarding",
        "resolution": "HR onboarding completed. Provisioned: BambooHR admin account, Google Workspace account with company email, Slack invite, Notion HR workspace access, Zoom license.",
        "resolved_by": "L2_APPROVAL",
    },
    {
        "ticket_id": "TKT-024",
        "ticket_text": "I started 3 weeks ago but I still don't have GitHub access. I've been using my personal account but need the org access.",
        "category": "onboarding",
        "subcategory": "partial setup",
        "action_type": "partial_onboarding",
        "resolution": "Partial onboarding — missing GitHub access. L2 approved retroactive GitHub org invitation. User added to Engineering team. Manager reminded to submit full onboarding tickets at start date.",
        "resolved_by": "L2_APPROVAL",
    },
    {
        "ticket_id": "TKT-025",
        "ticket_text": "New tester David Kim starts this Thursday. He'll need Jira, TestRail, and Slack. Please set this up ASAP.",
        "category": "onboarding",
        "subcategory": "new hire setup",
        "action_type": "full_onboarding",
        "resolution": "QA onboarding completed. Provisioned: Jira Software account with QA project access, TestRail account, Slack workspace invite, Notion workspace, Zoom license.",
        "resolved_by": "L2_APPROVAL",
    },
    {
        "ticket_id": "TKT-026",
        "ticket_text": "Please revoke all access for James Wilson who is leaving the company today. This is urgent.",
        "category": "onboarding",
        "subcategory": "offboarding",
        "action_type": "offboarding",
        "resolution": "URGENT offboarding completed. Revoked: GitHub org membership, AWS IAM account disabled, Jira account deactivated, Slack account deactivated, Salesforce account suspended, Notion access removed, Okta account disabled. All revocations completed within 2 hours of request. Hardware return scheduled.",
        "resolved_by": "L2_APPROVAL",
    },
    {
        "ticket_id": "TKT-027",
        "ticket_text": "Offboarding request for Lisa Park — last day is tomorrow. Please disable all her accounts.",
        "category": "onboarding",
        "subcategory": "offboarding",
        "action_type": "offboarding",
        "resolution": "Offboarding completed for Lisa Park. All SaaS accounts disabled, Okta account deactivated, company email forwarding set up for 30 days, laptop return scheduled for last day.",
        "resolved_by": "L2_APPROVAL",
    },
    {
        "ticket_id": "TKT-028",
        "ticket_text": "Contractor Robert Brown is finishing his engagement next week. Please remove his access to GitHub, Jira, and Slack by Friday.",
        "category": "onboarding",
        "subcategory": "offboarding",
        "action_type": "offboarding",
        "resolution": "Contractor offboarding completed ahead of schedule. GitHub org membership removed, Jira contractor account deactivated, Slack deactivated. No hardware return needed (contractor used own equipment).",
        "resolved_by": "L2_APPROVAL",
    },
    {
        "ticket_id": "TKT-029",
        "ticket_text": "New developer joining tomorrow — Alex Patel. Very last minute, sorry! Needs GitHub, Slack, AWS, Jira at minimum.",
        "category": "onboarding",
        "subcategory": "new hire setup",
        "action_type": "full_onboarding",
        "resolution": "Expedited Developer onboarding completed same day. Critical tools provisioned: GitHub, Slack, AWS IAM (read-only initially), Jira. Remaining tools (Notion, Zoom) provisioned next day.",
        "resolved_by": "L2_APPROVAL",
    },
    {
        "ticket_id": "TKT-030",
        "ticket_text": "I transferred from Sales to Engineering last week. I still have my Salesforce and HubSpot accounts but need GitHub and AWS set up now.",
        "category": "onboarding",
        "subcategory": "partial setup",
        "action_type": "partial_onboarding",
        "resolution": "Role transfer handled. Added: GitHub org invite (Engineering team), AWS IAM account. Queued for L2 review: Salesforce/HubSpot access revocation (separate ticket). Employee notified of timeline.",
        "resolved_by": "L2_APPROVAL",
    },
    {
        "ticket_id": "TKT-031",
        "ticket_text": "VS Code license has expired for our dev team. Multiple developers can't use the licensed extensions.",
        "category": "software_access",
        "subcategory": "tool access",
        "action_type": "new_access",
        "resolution": "IT requested license renewal via software procurement. Temporary developer licenses issued. New annual license activated within 24 hours.",
        "resolved_by": "L2_APPROVAL",
    },
    {
        "ticket_id": "TKT-032",
        "ticket_text": "TestRail shows 403 Forbidden when I try to open any test suite. This started after the IT maintenance window.",
        "category": "software_access",
        "subcategory": "login error",
        "action_type": "login_error",
        "resolution": "1. Log out of TestRail and clear browser cache. 2. Try logging in via the TestRail direct URL. 3. If using SSO, trigger re-authentication via Okta. 4. IT admin verified that the TestRail API token was rotated during maintenance — updated the integration token in Okta. Issue resolved.",
        "resolved_by": "AUTO_RESOLVE",
    },
]

# ---------------------------------------------------------------------------
# IT Runbooks (5)
# ---------------------------------------------------------------------------

RUNBOOKS: list[dict] = [
    {
        "ticket_id": "RB-001",
        "ticket_text": "VPN Setup Guide: How to configure DeskFlow VPN access for remote employees. Install the Cisco AnyConnect client from the IT portal. Enter the VPN server address vpn.deskflow.internal. Authenticate with your Okta credentials. Use split tunneling for better performance. If connection fails, check firewall settings and try the backup VPN server vpn2.deskflow.internal.",
        "category": "runbook",
        "subcategory": "vpn",
        "action_type": "setup",
        "resolution": "VPN setup runbook: Install Cisco AnyConnect > configure vpn.deskflow.internal > authenticate with Okta > enable split tunneling if needed.",
        "resolved_by": "IT_RUNBOOK",
    },
    {
        "ticket_id": "RB-002",
        "ticket_text": "New Employee Onboarding SOP: Standard operating procedure for onboarding all new DeskFlow employees. Step 1: Manager submits onboarding ticket 5 days before start. Step 2: IT provisions Okta account and sends welcome email. Step 3: Role-based tools provisioned (see ROLE_TOOLS_MAP). Step 4: Hardware shipped to employee address or available at office. Step 5: IT sends onboarding pack with credentials. Step 6: New hire completes Okta setup on day 1.",
        "category": "runbook",
        "subcategory": "onboarding",
        "action_type": "full_onboarding",
        "resolution": "Onboarding SOP: Submit ticket 5 days early > IT creates Okta > provisions role tools > hardware ready day 1 > employee completes Okta setup.",
        "resolved_by": "IT_RUNBOOK",
    },
    {
        "ticket_id": "RB-003",
        "ticket_text": "Software Access Request Process: How to request access to new tools at DeskFlow. Submit a ticket with the tool name, business justification, and manager approval. IT reviews requests within 1 business day. Standard tools (Slack, Zoom, Notion) auto-approved. Non-standard tools require L2 review. Admin/elevated access requires VP approval. Access provisioned within 2 business days of approval.",
        "category": "runbook",
        "subcategory": "access_request",
        "action_type": "new_access",
        "resolution": "Access request process: Submit ticket with justification > IT reviews (1 day) > standard tools auto-approved > elevated access needs VP sign-off > provisioned within 2 days.",
        "resolved_by": "IT_RUNBOOK",
    },
    {
        "ticket_id": "RB-004",
        "ticket_text": "Hardware Replacement Process: How IT handles hardware repair and replacement at DeskFlow. For physical damage: submit ticket with photos > IT assesses within 24 hours > loaner issued if work-blocking > repair/replacement authorized by IT manager. For performance issues: L1 remote triage first > if hardware fault confirmed, replacement ordered. SLA: loaner within 24 hours, replacement within 5 business days.",
        "category": "runbook",
        "subcategory": "hardware_replacement",
        "action_type": "physical_damage",
        "resolution": "Hardware replacement: Submit ticket with photos > IT assesses 24h > loaner issued > repair authorized > SLA 5 business days for replacement.",
        "resolved_by": "IT_RUNBOOK",
    },
    {
        "ticket_id": "RB-005",
        "ticket_text": "Employee Offboarding Checklist: Standard offboarding procedure for departing DeskFlow employees. Day 0 (last day): Disable Okta account, revoke all SaaS access, remove from GitHub org, suspend email account. Day 1: Data export and archive (manager's responsibility). Day 7: Permanent account deletion. Hardware: laptop and accessories returned to IT on last day. Badge access revoked by HR on last day.",
        "category": "runbook",
        "subcategory": "offboarding",
        "action_type": "offboarding",
        "resolution": "Offboarding checklist: Day 0 - disable Okta + all SaaS + GitHub removal + email suspend. Day 7 - permanent deletion. Return hardware on last day.",
        "resolved_by": "IT_RUNBOOK",
    },
]


async def seed_past_tickets() -> None:
    collection = get_or_create_collection("past_tickets")
    existing_ids = set(collection.get()["ids"])

    texts = [t["ticket_text"] for t in PAST_TICKETS]
    ids = [t["ticket_id"] for t in PAST_TICKETS]
    metadatas = [
        {
            "ticket_id": t["ticket_id"],
            "category": t["category"],
            "subcategory": t["subcategory"],
            "action_type": t["action_type"],
            "resolution": t["resolution"],
            "resolved_by": t["resolved_by"],
        }
        for t in PAST_TICKETS
    ]

    new_indices = [i for i, tid in enumerate(ids) if tid not in existing_ids]
    if not new_indices:
        logger.info("past_tickets collection already seeded — skipping.")
        return

    new_texts = [texts[i] for i in new_indices]
    new_ids = [ids[i] for i in new_indices]
    new_metadatas = [metadatas[i] for i in new_indices]

    logger.info("Embedding %d past tickets...", len(new_texts))
    embeddings = await embed_texts(new_texts)

    collection.add(
        documents=new_texts,
        embeddings=embeddings,
        ids=new_ids,
        metadatas=new_metadatas,
    )
    logger.info("Seeded %d past tickets into ChromaDB.", len(new_ids))


async def seed_runbooks() -> None:
    collection = get_or_create_collection("runbooks")
    existing_ids = set(collection.get()["ids"])

    texts = [r["ticket_text"] for r in RUNBOOKS]
    ids = [r["ticket_id"] for r in RUNBOOKS]
    metadatas = [
        {
            "ticket_id": r["ticket_id"],
            "category": r["category"],
            "subcategory": r["subcategory"],
            "action_type": r["action_type"],
            "resolution": r["resolution"],
            "resolved_by": r["resolved_by"],
        }
        for r in RUNBOOKS
    ]

    new_indices = [i for i, rid in enumerate(ids) if rid not in existing_ids]
    if not new_indices:
        logger.info("runbooks collection already seeded — skipping.")
        return

    new_texts = [texts[i] for i in new_indices]
    new_ids = [ids[i] for i in new_indices]
    new_metadatas = [metadatas[i] for i in new_indices]

    logger.info("Embedding %d runbooks...", len(new_texts))
    embeddings = await embed_texts(new_texts)

    collection.add(
        documents=new_texts,
        embeddings=embeddings,
        ids=new_ids,
        metadatas=new_metadatas,
    )
    logger.info("Seeded %d runbooks into ChromaDB.", len(new_ids))


async def seed_all() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logger.info("Starting ChromaDB seed...")
    await seed_past_tickets()
    await seed_runbooks()
    logger.info("ChromaDB seed complete.")


if __name__ == "__main__":
    asyncio.run(seed_all())
