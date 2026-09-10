from fastapi import APIRouter, Depends, status, File, UploadFile, Form
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.schemas.copilot import CopilotMessageRequest, CopilotResponse
from app.services import copilot_service

router = APIRouter(prefix="/copilot", tags=["AIVOA Copilot"])

@router.post("/message", response_model=CopilotResponse, status_code=status.HTTP_200_OK)
async def process_copilot_message_endpoint(
    payload: CopilotMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Processes natural language prompts through the LangGraph AI Copilot state graph.
    """
    response = await copilot_service.process_copilot_message(db, payload)
    return response

@router.post("/document", response_model=CopilotResponse, status_code=status.HTTP_200_OK)
async def process_copilot_document_endpoint(
    file: UploadFile = File(...),
    complaint_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Processes uploaded complaint document (PDF, TXT, EML) through text extraction,
    LangGraph document extraction AI tool, risk assessment, and MySQL persistence.
    """
    response = await copilot_service.process_copilot_document(db, file, complaint_id)
    return response

