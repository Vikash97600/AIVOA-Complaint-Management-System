import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.schemas.summary import ComplaintSummaryResponse
from app.services.groq_service import groq_service
from app.core.logging_config import logger

class SummaryOutputSchema(BaseModel):
    summary_text: str = Field(..., description="2-3 sentence executive summary of customer complaint")
    key_facts: List[str] = Field(default_factory=list, description="Key facts bullet points summarizing customer, product, batch, defect, and severity")

async def generate_complaint_summary(
    complaint_data: Dict[str, Any],
    risk_data: Optional[Dict[str, Any]] = None
) -> ComplaintSummaryResponse:
    """
    Generates a concise, professional executive summary of the customer complaint
    using Groq gemma2-9b-it, with a deterministic fallback template if Groq is unavailable.
    """
    now_iso = datetime.now(timezone.utc).isoformat()

    if not complaint_data:
        return ComplaintSummaryResponse(
            summary_text="No complaint details available to generate summary.",
            key_facts=["No complaint details logged."],
            generated_at=now_iso
        )

    customer = complaint_data.get("customer_name") or "Unspecified Customer"
    product = complaint_data.get("product_name") or "Unspecified Product"
    batch = complaint_data.get("batch_number") or "Unspecified Batch"
    qty = complaint_data.get("affected_quantity") or "Unspecified Quantity"
    desc = complaint_data.get("complaint_description") or "No description provided."
    severity = (risk_data.get("severity_suggested") if risk_data else None) or "Pending Assessment"

    # Deterministic fallback builder
    fallback_summary = (
        f"{customer} reported a customer complaint regarding {product}"
        + (f" (Batch {batch})" if batch != "Unspecified Batch" else "")
        + f". Affected quantity: {qty}. Defect details: {desc}."
        + f" Preliminary AI Risk Assessment status: {severity}."
    )
    fallback_facts = [
        f"Customer: {customer}",
        f"Product: {product}",
        f"Batch Number: {batch}",
        f"Affected Quantity: {qty}",
        f"Suggested Severity: {severity}",
    ]

    try:
        system_prompt = (
            "You are a Quality Assurance Executive summarizer for a pharmaceutical manufacturing QMS.\n"
            "Generate a concise 2-3 sentence executive summary of the customer complaint and list 4-5 key bullet facts.\n"
            "Preserve all facts, numbers, dates, and uncertainty. Do NOT invent fictional facts or investigation conclusions."
        )
        user_prompt = f"Complaint Data: {complaint_data}\nRisk Data: {risk_data}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        llm_res: SummaryOutputSchema = await groq_service.generate_structured(
            messages=messages,
            response_model=SummaryOutputSchema,
            operation="generate_complaint_summary"
        )

        return ComplaintSummaryResponse(
            summary_text=llm_res.summary_text,
            key_facts=llm_res.key_facts or fallback_facts,
            generated_at=now_iso
        )

    except Exception as e:
        logger.warning(f"Groq complaint summary generation failed ({e}). Utilizing deterministic fallback summary.")
        return ComplaintSummaryResponse(
            summary_text=fallback_summary,
            key_facts=fallback_facts,
            generated_at=now_iso
        )
