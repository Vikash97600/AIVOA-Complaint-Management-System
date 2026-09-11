import re
from typing import Dict, Any

def fallback_extract_complaint_data(text: str) -> Dict[str, Any]:
    """
    Deterministic rule-based NLP extractor fallback for pharmaceutical customer complaints.
    Executes seamlessly if Groq API is rate-limited, offline, or returns an error.
    """
    if not text:
        return {}

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    full_text = " ".join(lines)

    result = {
        "customer_name": None,
        "complaint_source": "Pharmacy",
        "contact_info": None,
        "product_name": None,
        "strength_grade": None,
        "batch_number": None,
        "manufacturing_date": None,
        "expiry_date": None,
        "affected_quantity": None,
        "manufacturing_facility": None,
        "packaging_info": None,
        "complaint_category": "Product Defect",
        "defect_type": None,
        "complaint_description": full_text[:1000],
    }

    # Customer Name Extraction
    cust_match = re.search(
        r"([A-Za-z0-9\s]+(?:Pharmacy|Hospital|Clinic|Distributor|Labs|Formulations|Health|Chemist|Pvt|Ltd|Inc))",
        full_text,
        re.IGNORECASE,
    )
    if cust_match:
        result["customer_name"] = cust_match.group(1).strip()
    elif "reported" in full_text.lower():
        parts = re.split(r"\breported\b", full_text, flags=re.IGNORECASE)
        if len(parts) > 1 and parts[0].strip():
            candidate = parts[0].strip().rstrip(",.")
            if len(candidate) < 50:
                result["customer_name"] = candidate

    # Batch Number Extraction
    batch_match = re.search(
        r"(?:batch|lot|b/#)(?:\s+to|\s+no|\s+number|\s*is)?[:\s]*([A-Za-z0-9\-]+)",
        full_text,
        re.IGNORECASE,
    )
    if batch_match:
        result["batch_number"] = batch_match.group(1).strip()


    # Strength / Grade Extraction
    strength_match = re.search(
        r"(\d+(?:\.\d+)?\s*(?:mg|g|ml|mcg|%|IU|iu))",
        full_text,
        re.IGNORECASE,
    )
    if strength_match:
        result["strength_grade"] = strength_match.group(1).strip()

    # Product Name Extraction
    prod_match = re.search(
        r"(?:in|for|regarding|of)\s+([A-Za-z0-9\s]+(?:Capsules|Tablets|Tablet|Capsule|Injection|Syrup|Solution|Ointment|API|Suspension|Drum))",
        full_text,
        re.IGNORECASE,
    )
    if prod_match:
        result["product_name"] = prod_match.group(1).strip()

    # Affected Quantity Extraction
    qty_match = re.search(
        r"(\d+\s*(?:capsules|tablets|bottles|vials|drums|units|kg|boxes|cartons|packs))",
        full_text,
        re.IGNORECASE,
    )
    if qty_match:
        result["affected_quantity"] = qty_match.group(1).strip()

    # Manufacturing Date Extraction
    mfg_match = re.search(
        r"(?:manufacturing|mfg|mfd|mfg\s*date)[:\s]*([A-Za-z0-9\s,\/\-]+?)(?:,|$|expiry|exp|\.)",
        full_text,
        re.IGNORECASE,
    )
    if mfg_match:
        result["manufacturing_date"] = mfg_match.group(1).strip()

    # Expiry Date Extraction
    exp_match = re.search(
        r"(?:expiry|exp|exp\s*date)[:\s]*([A-Za-z0-9\s,\/\-]+?)(?:,|$|mfg|\.)",
        full_text,
        re.IGNORECASE,
    )
    if exp_match:
        result["expiry_date"] = exp_match.group(1).strip()

    # Defect Type & Category Extraction
    lower = full_text.lower()
    if "discolor" in lower:
        result["defect_type"] = "Discoloration"
    elif "foreign" in lower or "particle" in lower:
        result["defect_type"] = "Foreign Particulate Matter"
    elif "broken" in lower or "damaged" in lower or "chipped" in lower:
        result["defect_type"] = "Physical Damage"
    elif "leak" in lower or "breach" in lower:
        result["defect_type"] = "Container Breach"
    elif "label" in lower:
        result["defect_type"] = "Labeling Defect"
        result["complaint_category"] = "Packaging Defect"
    else:
        result["defect_type"] = "Product Defect"

    return result


def fallback_extract_edit_data(text: str) -> Dict[str, Any]:
    """
    Deterministic rule-based NLP edit delta extractor fallback.
    Identifies requested field changes from conversational edit inputs.
    """
    if not text:
        return {}

    changes = {}
    lower = text.lower()

    # Batch change
    batch_match = re.search(r"(?:batch|lot|b/#)(?:\s+to|\s+no|\s+number|\s*is)?[:\s]*([A-Za-z0-9\-]+)", text, re.IGNORECASE)
    if batch_match:
        changes["batch_number"] = batch_match.group(1).strip()


    # Quantity change
    qty_match = re.search(r"(\d+\s*(?:capsules|tablets|bottles|vials|drums|units|kg|boxes|cartons|packs))", text, re.IGNORECASE)
    if qty_match:
        changes["affected_quantity"] = qty_match.group(1).strip()

    # Customer change
    cust_match = re.search(r"(?:customer|pharmacy|client)[:\s]*([A-Za-z0-9\s]+(?:Pharmacy|Hospital|Clinic|Distributor|Labs|Health))", text, re.IGNORECASE)
    if cust_match:
        changes["customer_name"] = cust_match.group(1).strip()

    # Product change
    prod_match = re.search(r"(?:product)[:\s]*([A-Za-z0-9\s]+)", text, re.IGNORECASE)
    if prod_match:
        changes["product_name"] = prod_match.group(1).strip()

    return changes
