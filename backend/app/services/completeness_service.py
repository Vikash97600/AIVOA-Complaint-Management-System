import uuid
from typing import Dict, Any, Optional, List
from app.schemas.completeness import CompletenessResponse
from app.core.logging_config import logger

def calculate_completeness(complaint_data: Dict[str, Any]) -> CompletenessResponse:
    """
    Evaluates complaint detail completeness deterministically based on key QMS attributes.
    Scores:
    - 90-100: Complete
    - 75-89: Mostly Complete
    - 50-74: Incomplete
    - 0-49: Highly Incomplete
    """
    if not complaint_data:
        return CompletenessResponse(
            is_complete=False,
            completion_score=0,
            status_label="Highly Incomplete",
            missing_fields=["customer_name", "product_name", "batch_number", "complaint_description", "affected_quantity"],
            warnings=["No complaint details available."],
            recommendations=["Log core complaint information using AI Copilot."]
        )

    field_weights = {
        "customer_name": 15,
        "product_name": 20,
        "batch_number": 20,
        "complaint_description": 20,
        "affected_quantity": 10,
        "expiry_date": 5,
        "manufacturing_date": 5,
        "strength_grade": 5,
    }

    total_weight = sum(field_weights.values())
    earned_score = 0
    missing_fields: List[str] = []
    warnings: List[str] = []
    recommendations: List[str] = []

    for field, weight in field_weights.items():
        val = complaint_data.get(field)
        if val and str(val).strip() and str(val).strip().lower() not in ("none", "null", "not provided"):
            earned_score += weight
        else:
            missing_fields.append(field)

    score = min(100, int((earned_score / total_weight) * 100))

    if score >= 90:
        status_label = "Complete"
        is_complete = True
    elif score >= 75:
        status_label = "Mostly Complete"
        is_complete = True
    elif score >= 50:
        status_label = "Incomplete"
        is_complete = False
    else:
        status_label = "Highly Incomplete"
        is_complete = False

    if "batch_number" in missing_fields:
        warnings.append("Batch / Lot number is missing. Essential for manufacturing genealogy and retention sample analysis.")
        recommendations.append("Obtain batch/lot number from customer or packaging label.")

    if "product_name" in missing_fields:
        warnings.append("Product name is not specified.")
        recommendations.append("Confirm exact product name and dosage form.")

    if "affected_quantity" in missing_fields:
        warnings.append("Affected quantity is missing. Necessary for material impact assessment.")
        recommendations.append("Verify total number of affected units or volume.")

    if "expiry_date" in missing_fields and "batch_number" not in missing_fields:
        recommendations.append("Confirm expiry date if available on packaging.")

    return CompletenessResponse(
        is_complete=is_complete,
        completion_score=score,
        status_label=status_label,
        missing_fields=missing_fields,
        warnings=warnings,
        recommendations=recommendations,
    )
