# deskflow-agent

LangGraph-based IT support agent for **DeskFlow Inc.** — classifies employee IT tickets, retrieves similar past resolutions via RAG, and routes each ticket to the correct resolution path automatically.

---

## Overview

The agent handles three ticket categories:

| Category | Examples |
|---|---|
| Software / Tool Access | New access requests, login errors, admin permissions |
| Laptop / Hardware | Slow laptops, physical damage, peripherals |
| New Employee Onboarding | Full setup, partial setup, offboarding/revocation |

Each ticket is processed through a fixed pipeline:

```
Classifier → RAG Retrieval → Router → [AUTO_RESOLVE | L2_APPROVAL | L1_ESCALATE] → Logger
```

---

## Architecture

```
deskflow-backend
       │
       │ await process_ticket(ticket_data)
       ▼
┌─────────────────────────────────────────────────────┐
│                   deskflow-agent                    │
│                                                     │
│  START                                              │
│    │                                                │
│    ▼                                                │
│  classifier_node  ──── GPT-4o extracts:             │
│    │                   category, action_type,       │
│    │                   tools_mentioned, severity    │
│    ▼                                                │
│  rag_node  ─────────── ChromaDB query:              │
│    │                   past_tickets + runbooks      │
│    │                   → rag_confidence score       │
│    ▼                                                │
│  router_node ──────── Decision matrix (pure Python) │
│    │                                                │
│    ├─ AUTO_RESOLVE ─► resolver_node (GPT-4o fix)    │
│    ├─ L2_APPROVAL  ─► approval_node (payload build) │
│    └─ L1_ESCALATE  ─► escalation_node (brief gen)   │
│                  │                                  │
│                  ▼                                  │
│             logger_node ──── MongoDB trace save     │
│                  │                                  │
│                 END                                 │
└─────────────────────────────────────────────────────┘
```

---

## Setup

### 1. Install uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone and install dependencies

```bash
git clone <repo-url>
cd deskflow-agent
uv sync --dev
```

`uv sync` creates `.venv` automatically, resolves, and installs all dependencies (including dev) from `uv.lock`.

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required:
- `OPENAI_API_KEY` — OpenAI API key (GPT-4o + text-embedding-3-small)
- `GITHUB_TOKEN` — GitHub Personal Access Token with `admin:org` scope
- `GITHUB_ORG` — Your GitHub organization name
- `MONGODB_URI` — MongoDB connection string

### 4. Seed ChromaDB

```bash
uv run python -m deskflow_agent.rag.seed_data
```

This seeds 30+ past resolved tickets and 5 IT runbooks into ChromaDB for RAG retrieval.

---

## Running Tests

```bash
uv run pytest
# With verbose output:
uv run pytest -v
# Single test file:
uv run pytest tests/test_router.py -v
```

Tests use mocked LLM and ChromaDB — no API keys required.

---

## Using from deskflow-backend

```python
from deskflow_agent import process_ticket

ticket_data = {
    "ticket_id": "TKT-20240417-001",
    "employee_id": "EMP-123",
    "employee_name": "Sarah Chen",
    "employee_role": "Developer",
    "department": "Engineering",
    "subject": "Cannot access GitHub",
    "raw_ticket_text": "I just joined the team and need access to the GitHub org. My username is sarah_dev.",
    "priority": "medium",
}

result = await process_ticket(ticket_data)

print(result["route"])           # "L2_APPROVAL"
print(result["status"])          # "pending_approval"
print(result["agent_response"])  # Message sent to employee
print(result["approval_payload"])  # Structured payload for L2 reviewer
```

### Result structure

| Field | Description |
|---|---|
| `route` | `AUTO_RESOLVE`, `L2_APPROVAL`, or `L1_ESCALATE` |
| `status` | `resolved`, `pending_approval`, `escalated`, or `failed` |
| `agent_response` | Message to display to the employee |
| `approval_payload` | Structured data for L2 IT reviewer (when route=L2_APPROVAL) |
| `escalation_payload` | Structured brief for L1 technician (when route=L1_ESCALATE) |
| `rag_confidence` | Float 0.0–1.0, similarity score of best RAG match |
| `category` | `software_access`, `hardware`, or `onboarding` |
| `action_type` | Specific action type (e.g. `new_access`, `slow_laptop`) |

---

## Decision Matrix

| Category | Problem | Route |
|---|---|---|
| Software/Tool | New tool access | L2_APPROVAL always |
| Software/Tool | Tool not launching / login error | AUTO_RESOLVE if RAG ≥ 0.80, else L1_ESCALATE |
| Software/Tool | Elevated/admin access | L2_APPROVAL always |
| Hardware | Slow / freezing | AUTO_RESOLVE if RAG ≥ 0.80, else L1_ESCALATE |
| Hardware | Physical damage / won't turn on | L1_ESCALATE always |
| Hardware | Peripheral not working | L1_ESCALATE always |
| Onboarding | Full onboarding | L2_APPROVAL always |
| Onboarding | Partial onboarding | L2_APPROVAL always |
| Onboarding | Offboarding/revocation | L2_APPROVAL always, high priority |

---

## Project Structure

```
deskflow-agent/
├── deskflow_agent/
│   ├── __init__.py          # process_ticket() entry point
│   ├── graph.py             # LangGraph StateGraph definition
│   ├── state.py             # AgentState TypedDict
│   ├── config.py            # Environment variable loading
│   ├── nodes/               # One file per graph node
│   ├── tools/               # GitHub (real) + mock SaaS tools
│   ├── rag/                 # ChromaDB client, embedder, retriever, seed data
│   └── prompts/             # LLM system prompts + role→tools map
└── tests/                   # pytest test suite (mocked externals)
```
