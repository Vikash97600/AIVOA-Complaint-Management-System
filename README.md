# AIVOA – AI-Powered Customer Complaint Management System
**Industry:** Pharmaceutical Manufacturing  
**Architecture:** React + Redux Toolkit | Python FastAPI | LangGraph | Groq LLM | PostgreSQL  

---

## Overview

AIVOA is an enterprise-grade AI-powered Quality Management System (QMS) prototype designed specifically for pharmaceutical manufacturing environments. It streamlines customer complaint intake, edit management, document extraction, and risk triaging through a conversational AI Copilot.

### Core Workflow Principle
- **Left Column:** Read-only structured pharmaceutical complaint form and AI risk triage card.
- **Right Column:** Conversational AI Copilot interface and PDF document upload tool.
- **Strict Control Flow:** All form entries and updates are driven by interaction with the AI Copilot (`USER -> AI COPILOT -> STRUCTURED FORM`).
- **QMS Commitment:** Formal transition from `DRAFT` status to `COMMITTED` status in the database ledger with frozen JSONB payload snapshots.

---

## Database Architecture

AIVOA utilizes PostgreSQL managed via SQLAlchemy 2.0 (Async ORM) and Alembic database migrations.

### Key Database Entities

```text
┌────────────────────────────────────────────────────────┐
│                      complaints                        │
├────────────────────────────────────────────────────────┤
│ id: UUID (PK)                                          │
│ status: ComplaintStatus (DRAFT / COMMITTED) [Index]    │
│ qms_reference_number: String (Unique)                  │
│ customer_name: String [Index]                          │
│ product_name: String [Index]                           │
│ batch_number: String [Index]                           │
│ complaint_source, contact_info, complaint_date         │
│ strength_grade, manufacturing_date, expiry_date        │
│ affected_quantity, manufacturing_facility              │
│ packaging_info, complaint_category, defect_type       │
│ complaint_description: Text                            │
│ created_at: DateTime(tz) [Index]                       │
│ updated_at: DateTime(tz)                               │
└───────────────────────────┬────────────────────────────┘
                            │
       ┌────────────────────┼────────────────────┐
       │ (1:1)              │ (1:N)              │ (1:1)
       ▼                    ▼                    ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ risk_assessments │  │complaint_docum...│  │    qms_ledger    │
├──────────────────┤  ├──────────────────┤  ├──────────────────┤
│id: UUID (PK)     │  │id: UUID (PK)     │  │id: UUID (PK)     │
│complaint_id (FK) │  │complaint_id (FK) │  │complaint_id (FK) │
│severity: Enum    │  │file_name: String │  │qms_ref_num (UQ)  │
│category: String  │  │file_path: String │  │committed_at(tz)  │
│next_action: Text │  │file_type: String │  │frozen_payload    │
│risk_details: Text│  │file_size: Int    │  │  (JSON / JSONB)  │
│quarantine: Bool  │  │extracted_text    │  └──────────────────┘
│created_at (tz)   │  │uploaded_at (tz)  │
└──────────────────┘  └──────────────────┘
```

1. **`complaints`**: Primary table for structured complaint data (DRAFT and COMMITTED status).
2. **`risk_assessments`**: 1-to-1 relationship storing AI-assisted risk triage results (Severity: LOW, MEDIUM, HIGH, CRITICAL; recommended next action; quarantine flag).
3. **`complaint_documents`**: 1-to-many relationship storing uploaded PDF complaint file metadata and extracted text.
4. **`qms_ledger`**: 1-to-1 relationship storing immutable JSONB snapshots of committed complaints with unique QMS reference numbers (`QMS-2026-XXXX`).

---

## Project Structure

```
AIVOA/
├── frontend/             # React + Redux Toolkit + Vite
│   ├── src/
│   │   ├── components/   # Split-view components (Form & Copilot)
│   │   ├── store/        # Redux Toolkit slices
│   │   ├── services/     # API integration service
│   │   └── App.jsx
│   └── package.json
│
├── backend/              # Python 3.11+ FastAPI + LangGraph
│   ├── app/
│   │   ├── api/          # REST endpoints
│   │   ├── database/     # SQLAlchemy models & Async session
│   │   ├── schemas/      # Pydantic v2 schemas
│   │   ├── ai/           # LangGraph orchestrator & Groq prompts
│   │   └── main.py
│   ├── alembic/          # Alembic migrations (001_initial_schema)
│   ├── tests/            # Pytest test suite (health check & database tests)
│   ├── requirements.txt
│   └── .env.example
│
└── README.md
```

---

## Getting Started

### 1. Backend Setup & Migrations
```bash
cd backend
python -m venv venv
# Activate virtualenv
# On Windows: venv\Scripts\activate
# On Linux/macOS: source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Configure GROQ_API_KEY and DATABASE_URL in .env

# Run database migrations
alembic upgrade head

# Run server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Run Test Suite
```bash
cd backend
pytest
```
