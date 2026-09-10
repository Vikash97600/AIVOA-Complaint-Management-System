from pydantic import BaseModel, Field
from typing import Optional

class ExtractedComplaintData(BaseModel):
    """Structured pharmaceutical complaint data model for AI extraction."""
    customer_name: Optional[str] = Field(
        None, description="Organization or entity reporting the complaint (e.g. Apollo Pharmacy, XYZ Hospital)"
    )
    complaint_source: Optional[str] = Field(
        None, description="Channel or entity type (e.g. Pharmacy, Hospital, Distributor, Patient, Internal)"
    )
    contact_info: Optional[str] = Field(
        None, description="Contact info (email, phone, contact person) if explicitly provided"
    )
    complaint_date: Optional[str] = Field(
        None, description="Date of complaint submission if explicitly provided"
    )
    product_name: Optional[str] = Field(
        None, description="Drug or product name WITHOUT strength/grade (e.g. Amoxicillin Capsules, Paracetamol Tablets)"
    )
    strength_grade: Optional[str] = Field(
        None, description="Dosage strength or pharmaceutical grade (e.g. 500 mg, 100 mg, IP/BP, USP)"
    )
    batch_number: Optional[str] = Field(
        None, description="Exact batch or lot number string (e.g. AMX240602). Do not alter or format."
    )
    manufacturing_date: Optional[str] = Field(
        None, description="Manufacturing date as reported (e.g. March 2026). Do NOT fabricate missing days."
    )
    expiry_date: Optional[str] = Field(
        None, description="Expiry date as reported (e.g. February 2028). Do NOT fabricate missing days."
    )
    affected_quantity: Optional[str] = Field(
        None, description="Affected quantity with units (e.g. 12 capsules, 48 capsules, 1 HDPE Drum)"
    )
    manufacturing_facility: Optional[str] = Field(
        None, description="Manufacturing site or facility name if explicitly mentioned"
    )
    packaging_info: Optional[str] = Field(
        None, description="Packaging type or container info if explicitly mentioned (e.g. Blister pack, HDPE Bottle)"
    )
    complaint_category: Optional[str] = Field(
        None, description="Broad defect category (e.g. Product Defect, Packaging Defect, Labeling Defect)"
    )
    defect_type: Optional[str] = Field(
        None, description="Specific quality defect (e.g. Discoloration, Broken Tablets, Contamination, Seal Failure)"
    )
    complaint_description: Optional[str] = Field(
        None, description="Concise, faithful summary of the reported issue without unsupported assumptions"
    )


LOG_COMPLAINT_SYSTEM_PROMPT = """You are an expert pharmaceutical Quality Assurance extraction assistant for AIVOA (AI-Powered Customer Complaint Management System).

Your role is to extract structured pharmaceutical customer complaint details from the user's natural language input.

STRICT EXTRACTION RULES:
1. NO HALLUCINATION: Only extract information that is explicitly stated or directly supported in the user message. If a field is not mentioned or cannot be confidently identified, return null.
2. CUSTOMER NAME vs COMPLAINT SOURCE:
   - "customer_name": The specific organization or entity reporting the complaint (e.g., "Apollo Pharmacy", "City Hospital").
   - "complaint_source": The category/type of reporting channel (e.g., "Pharmacy", "Hospital", "Distributor", "Clinic").
3. PRODUCT NAME vs STRENGTH/GRADE:
   - "product_name": The drug/product name without strength (e.g., "Amoxicillin Capsules").
   - "strength_grade": The dosage strength or pharmacopeial grade (e.g., "500 mg", "IP/BP"). Separate strength from product_name whenever possible.
4. BATCH NUMBER: Extract exact batch/lot numbers (e.g., "AMX240602", "BMX240602"). Preserve characters, numbers, and casing exactly. Never add or remove characters.
5. AFFECTED QUANTITY: Extract human-readable quantities with unit names (e.g., "12 capsules", "48 capsules", "1 HDPE Drum"). Do NOT convert words like "several" into arbitrary numbers.
6. DATES: Extract reported manufacturing and expiry dates as strings (e.g., "March 2026", "February 2028", "2026-03-25"). Do NOT invent a day number (do NOT convert "March 2026" to "2026-03-01").
7. DEFECT TYPE & COMPLAINT CATEGORY: Identify specific defect types (e.g. "Discoloration", "Broken Tablets") and general categories (e.g. "Product Defect") ONLY when described.
8. COMPLAINT DESCRIPTION: Provide a concise, faithful summary of the defect. Do NOT add assumptions about patient injury, regulatory actions, or dissatisfaction unless explicitly stated.
9. DO NOT perform risk severity scoring (e.g. High/Medium/Low risk details).
10. DO NOT generate SQL, code, or access external databases.

You MUST return valid JSON matching the schema.
"""
