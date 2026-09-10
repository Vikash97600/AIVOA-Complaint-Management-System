import pytest
from app.ai.graph import build_aivoa_graph, compiled_graph
from app.ai.state import AgentState, Intent

def test_graph_compilation():
    """Test 1: Verify LangGraph StateGraph builds and compiles without errors."""
    graph = build_aivoa_graph()
    assert graph is not None


@pytest.mark.asyncio
async def test_log_complaint_routing():
    """Test 2: Verify Log Complaint message routes to LOG_COMPLAINT branch."""
    initial_state: AgentState = {
        "messages": [{"role": "user", "content": "Apollo Pharmacy reported discolored capsules in Amoxicillin Capsules 500 mg."}]
    }
    result_state = await compiled_graph.ainvoke(initial_state)
    assert result_state["intent"] == Intent.LOG_COMPLAINT
    assert "Log Complaint workflow selected" in result_state["response_message"]


@pytest.mark.asyncio
async def test_edit_complaint_routing():
    """Test 3: Verify Edit Complaint message routes to EDIT_COMPLAINT branch."""
    initial_state: AgentState = {
        "messages": [{"role": "user", "content": "Sorry, the batch number is BMX240602 and affected quantity is 48 capsules."}]
    }
    result_state = await compiled_graph.ainvoke(initial_state)
    assert result_state["intent"] == Intent.EDIT_COMPLAINT
    assert "Edit Complaint workflow selected" in result_state["response_message"]


@pytest.mark.asyncio
async def test_document_extraction_routing():
    """Test 4: Verify Document Extraction message routes to DOCUMENT_EXTRACTION branch."""
    initial_state: AgentState = {
        "messages": [{"role": "user", "content": "Please extract the complaint information from this PDF."}]
    }
    result_state = await compiled_graph.ainvoke(initial_state)
    assert result_state["intent"] == Intent.DOCUMENT_EXTRACTION
    assert "Document Extraction workflow selected" in result_state["response_message"]


@pytest.mark.asyncio
async def test_unknown_routing():
    """Test 5: Verify General / Unknown message routes to UNKNOWN branch."""
    initial_state: AgentState = {
        "messages": [{"role": "user", "content": "Hello AIVOA"}]
    }
    result_state = await compiled_graph.ainvoke(initial_state)
    assert result_state["intent"] == Intent.UNKNOWN
    assert "AIVOA Copilot is ready" in result_state["response_message"]
