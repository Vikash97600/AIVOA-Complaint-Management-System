import enum
from typing import TypedDict, Optional, List, Dict, Any

class Intent(str, enum.Enum):
    LOG_COMPLAINT = "LOG_COMPLAINT"
    EDIT_COMPLAINT = "EDIT_COMPLAINT"
    DOCUMENT_EXTRACTION = "DOCUMENT_EXTRACTION"
    CHECK_COMPLETENESS = "CHECK_COMPLETENESS"
    CHECK_DUPLICATE = "CHECK_DUPLICATE"
    GENERATE_SUMMARY = "GENERATE_SUMMARY"
    GENERAL_QUERY = "GENERAL_QUERY"
    UNKNOWN = "UNKNOWN"

class AgentState(TypedDict, total=False):
    messages: List[Dict[str, Any]]
    current_complaint: Optional[Dict[str, Any]]
    risk_assessment: Optional[Dict[str, Any]]
    document_text: Optional[str]
    document_metadata: Optional[Dict[str, Any]]
    intent: Intent
    updated_fields: List[str]
    response_message: Optional[str]
    error: Optional[str]
    complaint_id: Optional[str]
    completeness_result: Optional[Dict[str, Any]]
    duplicate_result: Optional[Dict[str, Any]]
    summary_result: Optional[Dict[str, Any]]
