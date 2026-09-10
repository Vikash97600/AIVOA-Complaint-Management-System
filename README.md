# AIVOA – AI-Powered Customer Complaint Management System
**Industry:** Pharmaceutical Manufacturing  
**Architecture:** React + Redux Toolkit | Python 3.11+ FastAPI | LangGraph | Groq LLM | MySQL  

---

## Overview

AIVOA is an enterprise-grade AI-powered Quality Management System (QMS) prototype designed specifically for pharmaceutical manufacturing environments. It streamlines customer complaint intake, edit management, document extraction, and risk triaging through a conversational AI Copilot.

### Core Workflow Principle
- **Left Column:** Read-only structured pharmaceutical complaint form and AI risk triage card.
- **Right Column:** Conversational AI Copilot interface and PDF document upload tool.
- **Strict Control Flow:** All form entries and updates are driven by interaction with the AI Copilot (`USER -> AI COPILOT -> STRUCTURED FORM`).
- **QMS Commitment:** Formal transition from `DRAFT` status to `COMMITTED` status in the database ledger with frozen JSON payload snapshots.

---

## Groq AI Setup

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=gemma2-9b-it
GROQ_TEMPERATURE=0
GROQ_MAX_TOKENS=2048
GROQ_TIMEOUT=30
```

AIVOA uses **Groq** as the primary LLM provider and `gemma2-9b-it` as the default configured model.

The Groq API key is stored strictly on the backend via environment variables and is never exposed to the React frontend.

### AI Architecture Flow

```text
FastAPI
   ↓
Copilot Service
   ↓
LangGraph
   ↓
AI Nodes (Classifier Node)
   ↓
Groq Service (`GroqService`)
   ↓
Groq API (`gemma2-9b-it`)
```

---

## AI Architecture (LangGraph Orchestration)

AIVOA uses **LangGraph** (`StateGraph`) to manage stateful AI agent workflows.

```text
                         React Frontend
                               |
                               | HTTP POST /api/copilot/message
                               ↓
                         FastAPI API
                               |
                               ↓
                        Copilot Service
                               |
                               ↓
                       ┌─────────────────┐
                       │   LangGraph     │
                       │                 │
                       │ classifier      │───► Groq Service (gemma2-9b-it)
                       │      ↓          │
                       │  conditional    │
                       │    routing      │
                       │      ↓          │
                       │ ┌────┼─────┐    │
                       │ ↓    ↓     ↓    │
                       │Log  Edit Document
                       │ │    │      │   │
                       │ └────┼──────┘   │
                       │      ↓          │
                       │ Risk Assessment │
                       │      ↓          │
                       │ Response        │
                       │ Synthesis       │
                       └─────────────────┘
                               |
                               ↓
                       Structured Response
                               |
                               ↓
                          React UI
```

### Log Complaint AI Tool (Prompt 7)

The **Log Complaint AI Tool** parses natural-language user messages via Groq (`gemma2-9b-it`) and extracts structured pharmaceutical complaint attributes into validated Pydantic schemas (`ExtractedComplaintData`).

```text
User Natural Language Message
          ↓
React Copilot UI & Redux
          ↓
FastAPI (`POST /api/copilot/message`)
          ↓
LangGraph (`compiled_graph`)
          ↓
Intent Classifier (`LOG_COMPLAINT`)
          ↓
Log Complaint Node (`log_complaint_node`)
          ↓
Groq LLM Service (`GroqService` / `gemma2-9b-it`)
          ↓
Pydantic Validation (`ExtractedComplaintData`)
          ↓
MySQL Persistence (`ComplaintService.create_complaint`)
          ↓
Redux (`complaintSlice`)
          ↓
Left Panel Complaint Form Auto-Population
```

*Note: Risk Assessment is implemented separately in the next phase (Prompt 8).*

### Graph Execution Nodes
1. **`classifier` (`classifier_node`)**: Evaluates incoming message content via `GroqService` to classify user intent (`LOG_COMPLAINT`, `EDIT_COMPLAINT`, `DOCUMENT_EXTRACTION`, `UNKNOWN`) and route to target workflow branch.
2. **`log_complaint` (`log_complaint_node`)**: Log Complaint Tool extracting structured pharmaceutical entities from natural text via `GroqService`.
3. **`edit_complaint` (`edit_complaint_node`)**: Interface for partial delta field extraction and merging (Edit Complaint Tool - Prompt 9).
4. **`document_extraction` (`document_extract_node`)**: Interface for PDF text extraction and entity parsing (Document Extraction Tool - Prompt 10).
5. **`risk_assessment` (`risk_assessment_node`)**: Placeholder interface for quality risk triage scoring (Risk Assessment Tool - Prompt 8).
6. **`response_synthesis` (`response_synthesis_node`)**: Formulates the final natural-language update for the Copilot chat.

---

## Backend & Database Architecture

The AIVOA backend is powered by **Python 3.11+**, **FastAPI**, **SQLAlchemy 2.0 (Async ORM)**, and **MySQL**.

### Key Technologies
- **API Framework:** FastAPI 0.110+ with OpenAPI Swagger (`/docs`) and ReDoc (`/redoc`).
- **Async Database Driver:** `aiomysql` (`mysql+aiomysql://`) for non-blocking FastAPI async I/O.
- **Sync Migration Driver:** `pymysql` (`mysql+pymysql://`) for Alembic database migrations.
- **Data Validation:** Pydantic v2 schemas (`ComplaintCreate`, `ComplaintUpdate`, `ComplaintResponse`, `CopilotMessageRequest`, `CopilotResponse`).
- **Error Handling:** Custom exception handlers (`AIVOAException`, `ComplaintNotFoundError`) that log server errors without leaking database credentials or stack traces to clients.
- **Correlation Tracking:** Middleware injecting unique `X-Request-ID` headers.

### Database Schema (MySQL)

```text
┌────────────────────────────────────────────────────────┐
│                      complaints                        │
├────────────────────────────────────────────────────────┤
│ id: VARCHAR(36) (PK)                                   │
│ status: ComplaintStatus (DRAFT / COMMITTED) [Index]    │
│ qms_reference_number: VARCHAR(50) (Unique)             │
│ customer_name: VARCHAR(255) [Index]                    │
│ product_name: VARCHAR(255) [Index]                     │
│ batch_number: VARCHAR(100) [Index]                     │
│ complaint_source, contact_info, complaint_date         │
│ strength_grade, manufacturing_date, expiry_date        │
│ affected_quantity, manufacturing_facility              │
│ packaging_info, complaint_category, defect_type       │
│ complaint_description: TEXT                            │
│ created_at: DATETIME(tz) [Index]                       │
│ updated_at: DATETIME(tz)                               │
└───────────────────────────┬────────────────────────────┘
                            │
       ┌────────────────────┼────────────────────┐
       │ (1:1)              │ (1:N)              │ (1:1)
       ▼                    ▼                    ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ risk_assessments │  │complaint_docum...│  │    qms_ledger    │
├──────────────────┤  ├──────────────────┤  ├──────────────────┤
│id: VARCHAR(36) PK│  │id: VARCHAR(36) PK│  │id: VARCHAR(36) PK│
│complaint_id (FK) │  │complaint_id (FK) │  │complaint_id (FK) │
│severity: Enum    │  │file_name: VARCHAR│  │qms_ref_num (UQ)  │
│category: VARCHAR │  │file_path: VARCHAR│  │committed_at(tz)  │
│next_action: TEXT │  │file_type: VARCHAR│  │frozen_payload    │
│risk_details: TEXT│  │file_size: INT    │  │  (JSON)          │
│quarantine: BOOL  │  │extracted_text    │  └──────────────────┘
│created_at (tz)   │  │uploaded_at (tz)  │
└──────────────────┘  └──────────────────┘
```

---

## Project Structure

```
AIVOA/
├── frontend/             # React + Redux Toolkit + Vite (Port 5173)
│   ├── src/
│   │   ├── components/   # Split-view components (Form & Copilot)
│   │   ├── store/        # Redux Toolkit slices
│   │   ├── services/     # API integration service
│   │   └── App.jsx
│   └── package.json
│
├── backend/              # Python 3.11+ FastAPI + MySQL (Port 8000)
│   ├── app/
│   │   ├── ai/           # LangGraph state graph, nodes & state definitions
│   │   │   ├── nodes/    # classifier, log_complaint, edit_complaint, etc.
│   │   │   ├── state.py  # AgentState TypedDict & Intent enum
│   │   │   └── graph.py  # build_aivoa_graph() & compiled_graph
│   │   ├── api/          # Central API Router (/api)
│   │   │   ├── routes/   # health.py, complaints.py, copilot.py
│   │   │   └── router.py
│   │   ├── core/         # config.py, exceptions.py, logging_config.py
│   │   ├── database/     # models.py, session.py
│   │   ├── schemas/      # common.py, complaint.py, copilot.py, etc.
│   │   ├── services/     # complaint_service.py, copilot_service.py
│   │   ├── dependencies.py # get_db session generator & request_id
│   │   └── main.py       # FastAPI application entry point
│   ├── alembic/          # Alembic migrations (001_initial_schema)
│   ├── tests/            # Pytest test suite (23 passing tests)
│   ├── requirements.txt
│   └── .env.example
│
└── README.md
```

---

## Getting Started

### 1. Backend Setup & MySQL Migrations
```bash
cd backend
python -m venv venv
# Activate virtualenv
# On Windows: venv\Scripts\activate
# On Linux/macOS: source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Configure GROQ_API_KEY and DATABASE_URL (MySQL) in .env
# Example: DATABASE_URL=mysql+aiomysql://root:password@localhost:3306/aivoa

# Run database migrations
alembic upgrade head

# Run server
uvicorn app.main:app --reload --port 8000
```

- **API Documentation:** `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/redoc` (ReDoc)
- **API Base Route:** `http://localhost:8000/api`
- **Copilot Message API:** `http://localhost:8000/api/copilot/message`
- **Health Check:** `http://localhost:8000/api/health`

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
