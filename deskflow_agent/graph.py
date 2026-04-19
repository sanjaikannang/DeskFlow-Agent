from __future__ import annotations

import logging
import time

from langgraph.graph import END, START, StateGraph

from deskflow_agent.nodes.approval_node import approval_node
from deskflow_agent.nodes.classifier_node import classifier_node
from deskflow_agent.nodes.escalation_node import escalation_node
from deskflow_agent.nodes.logger_node import logger_node
from deskflow_agent.nodes.rag_node import rag_node
from deskflow_agent.nodes.resolver_node import resolver_node
from deskflow_agent.nodes.router_node import router_node
from deskflow_agent.state import AgentState

logger = logging.getLogger(__name__)


def _route_after_router(state: AgentState) -> str:
    """Conditional edge: directs flow based on router_node decision."""
    if state.get("status") == "failed":
        return "escalation_node"
    route = state.get("route", "L1_ESCALATE")
    route_map = {
        "AUTO_RESOLVE": "resolver_node",
        "L2_APPROVAL": "approval_node",
        "L1_ESCALATE": "escalation_node",
    }
    return route_map.get(route, "escalation_node")


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("classifier_node", classifier_node)
    graph.add_node("rag_node", rag_node)
    graph.add_node("router_node", router_node)
    graph.add_node("resolver_node", resolver_node)
    graph.add_node("approval_node", approval_node)
    graph.add_node("escalation_node", escalation_node)
    graph.add_node("logger_node", logger_node)

    graph.add_edge(START, "classifier_node")
    graph.add_edge("classifier_node", "rag_node")
    graph.add_edge("rag_node", "router_node")

    graph.add_conditional_edges(
        "router_node",
        _route_after_router,
        {
            "resolver_node": "resolver_node",
            "approval_node": "approval_node",
            "escalation_node": "escalation_node",
        },
    )

    graph.add_edge("resolver_node", "logger_node")
    graph.add_edge("approval_node", "logger_node")
    graph.add_edge("escalation_node", "logger_node")
    graph.add_edge("logger_node", END)

    return graph


_compiled_graph = None


def _get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph().compile()
    return _compiled_graph


async def run_agent(initial_state: AgentState) -> AgentState:
    """
    Run the full DeskFlow agent graph against an initial AgentState.
    Returns the completed AgentState.
    """
    app = _get_compiled_graph()
    start_ms = int(time.time() * 1000)
    initial_state["processing_start_ms"] = start_ms

    logger.info(
        "[graph] Starting agent for ticket_id=%s employee=%s",
        initial_state.get("ticket_id"),
        initial_state.get("employee_name"),
    )

    result: AgentState = await app.ainvoke(initial_state)

    logger.info(
        "[graph] Agent complete — ticket_id=%s status=%s route=%s duration=%dms",
        result.get("ticket_id"),
        result.get("status"),
        result.get("route"),
        int(time.time() * 1000) - start_ms,
    )
    return result
