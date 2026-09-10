import io
import os
import uuid
import re
import email
from email import policy
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from fastapi import UploadFile
import pypdf

from app.core.config import settings
from app.core.exceptions import (
    InvalidDocumentTypeError,
    DocumentOversizedError,
    DocumentExtractionError,
)
from app.core.logging_config import logger

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".eml"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "message/rfc822",
    "application/octet-stream",  # Fallback for some browsers/tools
}


def sanitize_filename(filename: str) -> str:
    """Sanitizes user filename by removing dangerous path separators and special characters."""
    base = os.path.basename(filename)
    clean = re.sub(r"[^\w\s\.-]", "_", base)
    return clean or "document"


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extracts plain text content from PDF file bytes using pypdf."""
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        page_texts = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                page_texts.append(text.strip())
        
        extracted = "\n\n".join(page_texts)
        # Normalize non-printable bytes or null bytes
        clean_text = extracted.replace("\x00", "").strip()
        return clean_text
    except Exception as e:
        logger.error(f"pypdf extraction error: {e}", exc_info=True)
        raise DocumentExtractionError("The PDF could not be processed. Please upload a readable PDF.")


def extract_text_from_txt(file_bytes: bytes) -> str:
    """Extracts text content from plain text file bytes."""
    try:
        # Try UTF-8 first, fallback to latin-1 with character replacement
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = file_bytes.decode("latin-1", errors="replace")
        
        clean_text = text.replace("\x00", "").strip()
        return clean_text
    except Exception as e:
        logger.error(f"Text file extraction error: {e}", exc_info=True)
        raise DocumentExtractionError("The TXT file content could not be decoded.")


def extract_text_from_eml(file_bytes: bytes) -> str:
    """Extracts Subject, From, To, Date and Body content from .eml file bytes."""
    try:
        msg = email.message_from_bytes(file_bytes, policy=policy.default)
        headers = []
        
        if msg["subject"]:
            headers.append(f"Subject: {msg['subject']}")
        if msg["from"]:
            headers.append(f"From: {msg['from']}")
        if msg["to"]:
            headers.append(f"To: {msg['to']}")
        if msg["date"]:
            headers.append(f"Date: {msg['date']}")

        header_block = "\n".join(headers)

        # Extract message body
        body_content = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    body_content = part.get_content()
                    break
            if not body_content:
                # Fallback to text/html if text/plain not found
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        raw_html = part.get_content()
                        # Simple regex HTML tag stripper for EML HTML content
                        body_content = re.sub(r"<[^>]+>", " ", raw_html)
                        break
        else:
            body_content = msg.get_content()

        body_str = str(body_content).strip() if body_content else ""
        combined = f"{header_block}\n\nComplaint Message:\n{body_str}".strip()
        return combined.replace("\x00", "")
    except Exception as e:
        logger.error(f"EML file extraction error: {e}", exc_info=True)
        raise DocumentExtractionError("The EML email file could not be parsed.")


async def process_document_upload(
    file: UploadFile,
    upload_dir_name: str = "uploads"
) -> Dict[str, Any]:
    """
    Validates uploaded file size, extension, prevents path traversal, saves file safely to disk,
    and extracts text content for AI processing.
    """
    original_filename = sanitize_filename(file.filename or "uploaded_document")
    ext = os.path.splitext(original_filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        logger.warning(f"Rejected document upload with unsupported extension '{ext}'.")
        raise InvalidDocumentTypeError(
            f"Unsupported document type '{ext}'. Please upload a PDF, EML, or TXT file."
        )

    # Read bytes to validate file size
    file_bytes = await file.read()
    file_size = len(file_bytes)

    if file_size > settings.MAX_UPLOAD_SIZE:
        max_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
        logger.warning(f"Rejected document upload '{original_filename}' exceeding size limit ({file_size} bytes).")
        raise DocumentOversizedError(
            f"The uploaded file '{original_filename}' exceeds the maximum allowed size of {max_mb:.0f} MB."
        )

    if file_size == 0:
        raise DocumentExtractionError(f"Uploaded file '{original_filename}' is empty.")

    # Save file safely to disk using UUID filename to prevent path traversal
    stored_filename = f"{uuid.uuid4()}{ext}"
    uploads_path = Path(upload_dir_name)
    uploads_path.mkdir(parents=True, exist_ok=True)
    target_path = uploads_path / stored_filename

    try:
        with open(target_path, "wb") as f:
            f.write(file_bytes)
        logger.info(f"Safely stored uploaded document '{original_filename}' to '{target_path}'.")
    except Exception as e:
        logger.error(f"Failed to write uploaded file to disk: {e}", exc_info=True)
        raise DocumentExtractionError("Failed to store uploaded document on server.")

    # Extract readable text based on extension
    if ext == ".pdf":
        extracted_text = extract_text_from_pdf(file_bytes)
    elif ext == ".txt":
        extracted_text = extract_text_from_txt(file_bytes)
    elif ext == ".eml":
        extracted_text = extract_text_from_eml(file_bytes)
    else:
        extracted_text = ""

    if not extracted_text or not extracted_text.strip():
        logger.warning(f"No readable text extracted from document '{original_filename}'.")
        raise DocumentExtractionError("No readable text could be extracted from this document.")

    return {
        "file_name": original_filename,
        "file_path": str(target_path),
        "file_type": ext.lstrip("."),
        "file_size": file_size,
        "extracted_text": extracted_text.strip(),
    }
