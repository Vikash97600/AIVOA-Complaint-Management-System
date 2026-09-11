import uuid
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.state import AgentState, Intent
from app.schemas.copilot import CopilotMessageRequest, CopilotResponse
from app.schemas.complaint import ComplaintResponse, ComplaintCreate, ComplaintUpdate
from app.schemas.risk import RiskAssessmentCreate, RiskAssessmentResponse
from app.services import complaint_service
from app.services.risk_assessment_service import save_or_update_risk_assessment
from app.core.logging_config import logger


async def process_copilot_message(
    db: AsyncSession,
    request: CopilotMessageRequest
) -> CopilotResponse:
    """
    Orchestrates user messages through the LangGraph AI Copilot state graph,
    persisting/updating DRAFT complaints and preliminary AI Risk Assessments in MySQL.
    """
    current_complaint_dict: Optional[Dict[str, Any]] = None
    existing_complaint_obj: Optional[ComplaintResponse] = None
    risk_assessment_obj: Optional[RiskAssessmentResponse] = None

    # Fetch active complaint if complaint_id is provided
    if request.complaint_id:
        try:
            complaint_entity = await complaint_service.get_complaint_by_id(db, request.complaint_id)
            existing_complaint_obj = ComplaintResponse.model_validate(complaint_entity)
            current_complaint_dict = existing_complaint_obj.model_dump(mode="json")
            if existing_complaint_obj.risk_assessment:
                risk_assessment_obj = existing_complaint_obj.risk_assessment

            from app.database.models import ComplaintStatus
            if complaint_entity.status == ComplaintStatus.COMMITTED:
                return CopilotResponse(
                    success=False,
                    message="This complaint has already been committed to the QMS Ledger and cannot be edited.",
                    intent="COMPLAINT_COMMITTED",
                    complaint=existing_complaint_obj,
                    risk_assessment=risk_assessment_obj,
                    updated_fields=[],
                    error="Complaint is committed to QMS Ledger and immutable."
                )
        except Exception as e:
            logger.warning(f"Could not load active complaint '{request.complaint_id}' for Copilot context: {e}")

    # Construct initial AgentState
    initial_state: AgentState = {
        "messages": [{"role": "user", "content": request.message}],
        "complaint_id": request.complaint_id,
        "current_complaint": current_complaint_dict,
        "risk_assessment": risk_assessment_obj.model_dump(mode="json") if risk_assessment_obj else None,
        "updated_fields": [],
    }

    try:
        logger.info(f"Invoking AIVOA LangGraph Agent for message: '{request.message[:50]}...'")
        from app.ai.graph import compiled_graph

        final_state: AgentState = await compiled_graph.ainvoke(initial_state)

        detected_intent = final_state.get("intent", Intent.UNKNOWN)
        intent_str = detected_intent.value if isinstance(detected_intent, Intent) else str(detected_intent)
        response_msg = final_state.get("response_message") or "AIVOA Copilot request processed."
        extracted_complaint = final_state.get("current_complaint")
        extracted_risk = final_state.get("risk_assessment")
        updated_fields = final_state.get("updated_fields") or []
        err_msg = final_state.get("error")

        saved_entity = None

        # Database Persistence 1: Create or Update DRAFT complaint
        if extracted_complaint and isinstance(extracted_complaint, dict):
            try:
                if request.complaint_id:
                    # Partial DB delta update containing ONLY modified fields
                    if updated_fields:
                        update_payload = {f: extracted_complaint[f] for f in updated_fields if f in extracted_complaint}
                    else:
                        update_payload = {k: v for k, v in extracted_complaint.items() if v is not None}

                    if update_payload:
                        update_in = ComplaintUpdate(**update_payload)
                        saved_entity = await complaint_service.update_complaint(
                            db, request.complaint_id, update_in
                        )
                        logger.info(f"Updated active complaint ID '{request.complaint_id}' fields: {list(update_payload.keys())}")
                elif detected_intent == Intent.LOG_COMPLAINT:
                    clean_payload = {k: v for k, v in extracted_complaint.items() if v is not None}
                    if clean_payload:
                        create_in = ComplaintCreate(**clean_payload)
                        saved_entity = await complaint_service.create_complaint(db, create_in)
                        logger.info(f"Persisted new DRAFT complaint ID '{saved_entity.id}' from Log Complaint AI workflow.")
                elif existing_complaint_obj and existing_complaint_obj.id:
                    saved_entity = await complaint_service.get_complaint_by_id(db, existing_complaint_obj.id)
            except Exception as db_err:
                logger.error(f"Failed to persist complaint data to database: {db_err}", exc_info=True)
                err_msg = err_msg or "Failed to save complaint state to database."

        # Database Persistence 2: Create or Update RiskAssessment
        if extracted_risk and isinstance(extracted_risk, dict) and (saved_entity or request.complaint_id):
            target_complaint_id = saved_entity.id if saved_entity else request.complaint_id
            try:
                risk_create_in = RiskAssessmentCreate(**extracted_risk)
                saved_risk_entity = await save_or_update_risk_assessment(
                    db, target_complaint_id, risk_create_in
                )
                risk_assessment_obj = RiskAssessmentResponse.model_validate(saved_risk_entity)
                logger.info(f"Persisted RiskAssessment for complaint ID '{target_complaint_id}'.")
            except Exception as risk_db_err:
                logger.error(f"Failed to persist RiskAssessment to database: {risk_db_err}", exc_info=True)

        # Refresh existing_complaint_obj if entity was updated or created
        if saved_entity:
            refreshed = await complaint_service.get_complaint_by_id(db, saved_entity.id)
            existing_complaint_obj = ComplaintResponse.model_validate(refreshed)
            if refreshed.risk_assessment:
                risk_assessment_obj = RiskAssessmentResponse.model_validate(refreshed.risk_assessment)

        return CopilotResponse(
            message=response_msg,
            intent=intent_str,
            complaint=existing_complaint_obj,
            risk_assessment=risk_assessment_obj,
            updated_fields=updated_fields,
            error=err_msg,
        )

    except Exception as e:
        logger.error(f"LangGraph execution failed for message '{request.message}': {e}", exc_info=True)
        return CopilotResponse(
            message="I couldn't process the request due to an internal workflow error.",
            intent=Intent.UNKNOWN.value,
            complaint=existing_complaint_obj,
            risk_assessment=risk_assessment_obj,
            updated_fields=[],
            error="AI workflow execution failed",
        )


async def process_copilot_document(
    db: AsyncSession,
    file: "UploadFile",
    complaint_id: Optional[str] = None
) -> CopilotResponse:
    """
    Handles uploaded document processing: file validation, text extraction,
    LangGraph execution, DRAFT complaint persistence, ComplaintDocument DB record creation,
    and preliminary risk assessment generation.
    """
    from fastapi import UploadFile
    from app.schemas.document import ComplaintDocumentCreate, ComplaintDocumentResponse
    from app.services import document_extraction_service
    from app.core.exceptions import AIVOAException

    try:
        doc_data = await document_extraction_service.process_document_upload(file)
    except AIVOAException as exc:
        logger.warning(f"Document upload validation/extraction failed: {exc.message}")
        return CopilotResponse(
            success=False,
            message=exc.message,
            intent=Intent.DOCUMENT_EXTRACTION.value,
            complaint=None,
            risk_assessment=None,
            document=None,
            updated_fields=[],
            error=exc.message,
        )

    current_complaint_dict: Optional[Dict[str, Any]] = None
    existing_complaint_obj: Optional[ComplaintResponse] = None
    risk_assessment_obj: Optional[RiskAssessmentResponse] = None

    if complaint_id:
        try:
            entity = await complaint_service.get_complaint_by_id(db, complaint_id)
            existing_complaint_obj = ComplaintResponse.model_validate(entity)
            current_complaint_dict = existing_complaint_obj.model_dump(mode="json")
            if existing_complaint_obj.risk_assessment:
                risk_assessment_obj = existing_complaint_obj.risk_assessment

            from app.database.models import ComplaintStatus
            if entity.status == ComplaintStatus.COMMITTED:
                return CopilotResponse(
                    success=False,
                    message="This complaint has already been committed to the QMS Ledger and cannot be edited.",
                    intent=Intent.DOCUMENT_EXTRACTION.value,
                    complaint=existing_complaint_obj,
                    risk_assessment=risk_assessment_obj,
                    document=None,
                    updated_fields=[],
                    error="Complaint is committed to QMS Ledger and immutable."
                )
        except Exception as e:
            logger.warning(f"Could not load active complaint '{complaint_id}' for document upload: {e}")

    initial_state: AgentState = {
        "messages": [{"role": "user", "content": f"Extract complaint data from uploaded document '{doc_data['file_name']}'."}],
        "intent": Intent.DOCUMENT_EXTRACTION,
        "document_text": doc_data["extracted_text"],
        "document_metadata": {
            "file_name": doc_data["file_name"],
            "file_path": doc_data["file_path"],
            "file_type": doc_data["file_type"],
            "file_size": doc_data["file_size"],
        },
        "complaint_id": complaint_id,
        "current_complaint": current_complaint_dict,
        "risk_assessment": risk_assessment_obj.model_dump(mode="json") if risk_assessment_obj else None,
        "updated_fields": [],
    }

    try:
        from app.ai.graph import compiled_graph
        final_state: AgentState = await compiled_graph.ainvoke(initial_state)

        response_msg = final_state.get("response_message") or "Document extraction completed."
        extracted_complaint = final_state.get("current_complaint")
        extracted_risk = final_state.get("risk_assessment")
        updated_fields = final_state.get("updated_fields") or []
        err_msg = final_state.get("error")

        saved_entity = None

        if extracted_complaint and isinstance(extracted_complaint, dict):
            try:
                if complaint_id:
                    update_payload = {k: v for k, v in extracted_complaint.items() if v is not None}
                    if update_payload:
                        update_in = ComplaintUpdate(**update_payload)
                        saved_entity = await complaint_service.update_complaint(db, complaint_id, update_in)
                else:
                    clean_payload = {k: v for k, v in extracted_complaint.items() if v is not None}
                    if clean_payload:
                        create_in = ComplaintCreate(**clean_payload)
                        saved_entity = await complaint_service.create_complaint(db, create_in)
            except Exception as db_err:
                logger.error(f"Failed to persist complaint from document: {db_err}", exc_info=True)
                err_msg = err_msg or "Failed to save complaint data to database."

        target_complaint_id = saved_entity.id if saved_entity else (complaint_id or None)

        # Persist ComplaintDocument record if complaint target exists
        doc_obj = None
        if target_complaint_id:
            try:
                doc_in = ComplaintDocumentCreate(
                    file_name=doc_data["file_name"],
                    file_path=doc_data["file_path"],
                    file_type=doc_data["file_type"],
                    file_size=doc_data["file_size"],
                    extracted_text=doc_data["extracted_text"],
                )
                doc_entity = await complaint_service.create_complaint_document(db, target_complaint_id, doc_in)
                doc_obj = ComplaintDocumentResponse.model_validate(doc_entity)
            except Exception as doc_db_err:
                logger.error(f"Failed to persist ComplaintDocument record: {doc_db_err}", exc_info=True)

        # Persist RiskAssessment record if available
        if extracted_risk and isinstance(extracted_risk, dict) and target_complaint_id:
            try:
                risk_create_in = RiskAssessmentCreate(**extracted_risk)
                saved_risk = await save_or_update_risk_assessment(db, target_complaint_id, risk_create_in)
                risk_assessment_obj = RiskAssessmentResponse.model_validate(saved_risk)
            except Exception as risk_err:
                logger.error(f"Failed to save RiskAssessment for document complaint: {risk_err}", exc_info=True)

        if saved_entity:
            refreshed = await complaint_service.get_complaint_by_id(db, saved_entity.id)
            existing_complaint_obj = ComplaintResponse.model_validate(refreshed)
            if refreshed.risk_assessment:
                risk_assessment_obj = RiskAssessmentResponse.model_validate(refreshed.risk_assessment)

        return CopilotResponse(
            success=True,
            message=response_msg,
            intent=Intent.DOCUMENT_EXTRACTION.value,
            complaint=existing_complaint_obj,
            risk_assessment=risk_assessment_obj,
            document=doc_obj,
            updated_fields=updated_fields,
            error=err_msg,
        )

    except Exception as e:
        logger.error(f"Document extraction flow execution failed: {e}", exc_info=True)
        return CopilotResponse(
            success=False,
            message="Failed to process complaint document due to an internal workflow error.",
            intent=Intent.DOCUMENT_EXTRACTION.value,
            complaint=existing_complaint_obj,
            risk_assessment=risk_assessment_obj,
            document=None,
            updated_fields=[],
            error=str(e),
        )

