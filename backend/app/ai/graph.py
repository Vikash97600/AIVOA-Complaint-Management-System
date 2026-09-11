from langgraph.graph import StateGraph, START, END
from app.ai.state import AgentState, Intent
from app.ai.nodes import (
    classifier_node,
    log_complaint_node,
    edit_complaint_node,
    document_extract_node,
    risk_assessment_node,
    response_synthesis_node,
    completeness_node,
    duplicate_node,
    summary_node,
)

def route_intent(state: AgentState) -> str:
    """Conditional router function directing flow based on detected intent."""
    intent = state.get("intent", Intent.UNKNOWN)
    if intent == Intent.LOG_COMPLAINT:
        return "log_complaint"
    elif intent == Intent.EDIT_COMPLAINT:
        return "edit_complaint"
    elif intent == Intent.DOCUMENT_EXTRACTION:
        return "document_extraction"
    elif intent == Intent.CHECK_COMPLETENESS:
        return "completeness"
    elif intent == Intent.CHECK_DUPLICATE:
        return "duplicate"
    elif intent == Intent.GENERATE_SUMMARY:
        return "summary"
    else:
        return "response_synthesis"

def build_aivoa_graph():
    """Constructs, configures, and compiles the AIVOA Copilot LangGraph state graph."""
    builder = StateGraph(AgentState)

    # Register graph nodes
    builder.add_node("classifier", classifier_node)
    builder.add_node("log_complaint", log_complaint_node)
    builder.add_node("edit_complaint", edit_complaint_node)
    builder.add_node("document_extraction", document_extract_node)
    builder.add_node("risk_assessment", risk_assessment_node)
    builder.add_node("completeness", completeness_node)
    builder.add_node("duplicate", duplicate_node)
    builder.add_node("summary", summary_node)
    builder.add_node("response_synthesis", response_synthesis_node)

    # Entry point edge
    builder.add_edge(START, "classifier")

    # Conditional routing after intent classification
    builder.add_conditional_edges(
        "classifier",
        route_intent,
        {
            "log_complaint": "log_complaint",
            "edit_complaint": "edit_complaint",
            "document_extraction": "document_extraction",
            "completeness": "completeness",
            "duplicate": "duplicate",
            "summary": "summary",
            "response_synthesis": "response_synthesis",
        }
    )

    # Converge core functional branches into risk assessment
    builder.add_edge("log_complaint", "risk_assessment")
    builder.add_edge("edit_complaint", "risk_assessment")
    builder.add_edge("document_extraction", "risk_assessment")

    # Bonus insight nodes route to response synthesis
    builder.add_edge("completeness", "response_synthesis")
    builder.add_edge("duplicate", "response_synthesis")
    builder.add_edge("summary", "response_synthesis")

    # Synthesis & Exit
    builder.add_edge("risk_assessment", "response_synthesis")
    builder.add_edge("response_synthesis", END)

    return builder.compile()

# Primary compiled agent graph instance
compiled_graph = build_aivoa_graph()
