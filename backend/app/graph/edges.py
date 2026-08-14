"""
TravelOS LangGraph Conditional Edges
"""

from app.graph.state import AgentGraphState


def route_after_special_handlers(state: AgentGraphState) -> str:
    """
    If a special handler short-circuited (e.g. currency switch, swap),
    route directly to END; otherwise continue to extraction.
    """
    if state.get("special_response") is not None:
        return "end"
    return "extraction_node"


def route_after_query_analysis(state: AgentGraphState) -> str:
    """
    Routes the execution based on query router decision:
    - 'live': calls live_tools_node
    - 'rag': calls rag_knowledge_node
    - 'planning' / default: calls orchestrator_node
    """
    route = state.get("route", "planning")
    if route == "live":
        return "live_tools_node"
    elif route == "rag":
        return "rag_knowledge_node"
    return "orchestrator_node"
