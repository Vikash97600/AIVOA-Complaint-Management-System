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

### AI Risk Assessment Tool (Prompt 8)

The **AI Risk Assessment Tool** performs preliminary quality risk triage on extracted complaint data using Groq (`gemma2-9b-it`) and output validation via Pydantic (`RiskAssessmentOutput`).

```text
Validated ComplaintData
          ↓
LangGraph Risk Assessment Node (`risk_assessment_node`)
          ↓
Groq LLM Service (`GroqService` / `gemma2-9b-it`)
          ↓
Pydantic Validation (`RiskAssessmentOutput`)
          ↓
MySQL Persistence (`save_or_update_risk_assessment`)
          ↓
Redux Store (`complaintSlice`)
          ↓
React UI (`RiskAssessmentCard.jsx`)
```

*Note: All AI risk assessments represent preliminary triage recommendations ("AI-assisted preliminary assessment — QA review required") and do not replace formal human QA investigation or regulatory decisions.*

### Edit Complaint AI Tool (Prompt 9)

The **Edit Complaint AI Tool** allows modifying active customer complaints through natural-language edit requests via Groq (`gemma2-9b-it`) and partial delta merging (`ComplaintEditOutput`).

```text
User Natural Language Edit Request (e.g. "Batch is BMX240602, quantity is 48 capsules")
          ↓
React Copilot UI & Redux
          ↓
FastAPI (`POST /api/copilot/message` with active `complaint_id`)
          ↓
LangGraph (`compiled_graph`)
          ↓
Intent Classifier (`EDIT_COMPLAINT`)
          ↓
Edit Complaint Node (`edit_complaint_node`)
          ↓
Groq LLM Service (`GroqService` / `gemma2-9b-it`)
          ↓
Pydantic Validation (`ComplaintEditOutput` -> `updated_fields`, `changes`)
          ↓
Python Deterministic Merge (Updates ONLY requested fields; preserves all unmentioned data)
          ↓
MySQL Partial Delta Update (`ComplaintService.update_complaint`)
          ↓
AI Risk Re-Assessment Node (`risk_assessment_node` re-evaluates updated complaint)
          ↓
Redux (`complaintSlice`)
          ↓
Left Panel Complaint Form & Risk Card Real-Time Update
```

*Key Safety Principle: Only explicitly requested complaint fields are modified; all other complaint attributes and system fields remain completely preserved.*

### Document Extraction Tool (Prompt 10)

The **Document Extraction Tool** enables users to upload customer complaint documents (PDF, EML, TXT) directly through the AIVOA Copilot interface.

```text
Uploaded Document (PDF / EML / TXT)
          ↓
React Copilot UI & Redux (`uploadCopilotDocument`)
          ↓
FastAPI (`POST /api/copilot/document`)
          ↓
File Validation & Storage (Path Traversal Prevention + UUID Filename)
          ↓
Document Extraction Service (`extract_text_from_pdf` via `pypdf` / EML / TXT)
          ↓
LangGraph (`compiled_graph` with `DOCUMENT_EXTRACTION` intent)
          ↓
Document Extraction Node (`document_extract_node`)
          ↓
Groq LLM Service (`GroqService` / `gemma2-9b-it`)
          ↓
Pydantic Validation (`ExtractedComplaintData`)
          ↓
MySQL Persistence (`Complaint`, `ComplaintDocument`, `RiskAssessment`)
          ↓
AI Risk Assessment Node (`risk_assessment_node` generates risk triage)
          ↓
Redux & Left Panel Form Auto-Population + Risk Card Update
```

*Supported Document Types:*
- **PDF (`.pdf`):** Extracted via `pypdf`.
- **Email (`.eml`):** Parsed via Python standard library `email` parser (Subject, From, To, Date, Body).
- **Text (`.txt`):** Decoded via UTF-8 string parser.

*Upload Security & Safety Rules:*
- Strict file size limit validation (`MAX_UPLOAD_SIZE` 10 MB).
- Extension & MIME type validation (.pdf, .eml, .txt).
- Path traversal prevention: UUID generated stored filename (`uploads/<uuid>.<ext>`). Original filename retained only as metadata.
- Binary document contents are stored strictly on the server filesystem, never inside MySQL.
- Prompt Injection Resistance: Document text is treated strictly as UNTRUSTED DATA content, preventing prompt injection attacks from overriding AI system instructions.
- Missing field preservation: Unmentioned or absent fields (e.g. missing batch number or expiry date) remain `null` and are not hallucinated.
- *Limitation Notice:* Production-grade OCR for scanned/image-only PDFs is outside current prototype scope. Image-only PDFs return controlled messages asking for text-based documents.

### Graph Execution Nodes
1. **`classifier` (`classifier_node`)**: Evaluates incoming message content via `GroqService` to classify user intent (`LOG_COMPLAINT`, `EDIT_COMPLAINT`, `DOCUMENT_EXTRACTION`, `UNKNOWN`) and route to target workflow branch.
2. **`log_complaint` (`log_complaint_node`)**: Log Complaint Tool extracting structured pharmaceutical entities from natural text via `GroqService`.
3. **`edit_complaint` (`edit_complaint_node`)**: Edit Complaint Tool extracting requested partial field deltas via `GroqService` and applying deterministic Python merging.
4. **`document_extraction` (`document_extract_node`)**: Real Document Extraction Tool parsing text from uploaded PDF/EML/TXT documents via `pypdf` and `GroqService`.
5. **`risk_assessment` (`risk_assessment_node`)**: AI Risk Assessment Tool performing quality risk triage scoring (`severity_suggested`, `suggested_next_action`, `risk_details`, `requires_quarantine`).
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

### Bonus AI Complaint Assistance Tools (Prompt 15)

1. **Complaint Completeness Checker**: Evaluates complaint data against required and optional QMS fields, producing a **0–100% Completeness Score** (e.g. *85% - Mostly Complete*) along with missing field warnings and QA recommendations.
2. **Duplicate Complaint Detection**: Searches existing records in MySQL based on product, batch, customer, and defect similarity without external vector DB dependencies, generating advisory similarity alerts (e.g. *Matches QMS-2026-000001*).
3. **Executive Complaint Summary**: Generates concise, professional summaries using `gemma2-9b-it` / `llama-3.3-70b-versatile` for QA review and executive handoff.
4. **AI Quality Risk Classification**: Visual preliminary quality triage badges (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), quarantine recommendations, and risk rationales.

---

## QMS Ledger Commit Workflow (Prompt 14)

AIVOA enforces strict lifecycle management for customer complaints:
1. **DRAFT Status**: Newly logged complaints remain in `DRAFT` status and can be conversationally edited via the Copilot.
2. **Commit Action**: When the reviewer confirms complaint accuracy and clicks **🔒 Commit to QMS Ledger**:
   - Generates a server-side unique QMS Reference Number (`QMS-YYYY-XXXXXX`).
   - Freezes a full JSON snapshot (`frozen_payload_json`) of complaint details, risk assessment, and document metadata into the `qms_ledger` table.
   - Transitions status to `COMMITTED`.
3. **Immutability Enforcement**: Once committed, subsequent REST edits (`PATCH /api/complaints/{id}`) or Copilot update requests are strictly rejected on both backend and frontend.

---

## API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status check |
| `POST` | `/api/copilot/message` | Process natural language prompts through LangGraph AI Agent |
| `POST` | `/api/copilot/document` | Extract complaint details from uploaded PDF, TXT, or EML document |
| `POST` | `/api/complaints` | Create a new DRAFT complaint directly |
| `GET` | `/api/complaints` | List complaints with pagination, status filter (`?status=DRAFT|COMMITTED`), and search (`?search=query`) |
| `GET` | `/api/complaints/{id}` | Retrieve single complaint by UUID with complete risk and ledger snapshot |
| `PATCH` | `/api/complaints/{id}` | Update partial complaint delta fields (blocked with HTTP 409 if COMMITTED) |
| `DELETE` | `/api/complaints/{id}` | Permanently delete a complaint (permitted ONLY for DRAFT status; blocked with HTTP 409 if COMMITTED) |
| `POST` | `/api/complaints/{id}/commit` | Formally commit DRAFT complaint to QMS Ledger |
| `GET` | `/api/complaints/{id}/qms` | Retrieve frozen QMS Ledger snapshot |
| `POST` | `/api/complaints/{id}/completeness` | Run AI Complaint Completeness assessment |
| `POST` | `/api/complaints/{id}/duplicates` | Search candidate duplicate complaints in MySQL |
| `POST` | `/api/complaints/{id}/summary` | Generate executive complaint summary |

---

## Complaint History, Persistence & Deletion

Complaints are persisted in MySQL (`Complaint`, `RiskAssessment`, `ComplaintDocument`, and `QMSLedger` models).

After a browser refresh, users can:
1. Open the **Complaint History** drawer from the top header or empty state.
2. Search and filter by status (`DRAFT` or `COMMITTED`).
3. Select any existing complaint to re-hydrate the left complaint form, risk triage card, and copilot state directly from MySQL.
4. Continue editing `DRAFT` complaints using the AI Copilot.
5. Delete `DRAFT` complaints using the `[Delete]` button (with confirmation modal) if created accidentally.
6. View `COMMITTED` complaints in strict view-only mode (immutable, modification or deletion attempts rejected by backend with `HTTP 409 Conflict`).
7. Deep link or refresh with `?complaintId=<uuid>` to automatically restore the active complaint workspace on reload.

### Draft Complaint Deletion Lifecycle
```text
                 ┌─────────────┐
                 │    DRAFT    │
                 └──────┬──────┘
                        │
             ┌──────────┼──────────┐
             │          │          │
             ▼          ▼          ▼
           Edit       Delete     Commit
             │          │          │
             │          ▼          ▼
             │       Removed   COMMITTED
             │                     │
             ▼                     ▼
           DRAFT                 View Only
```
- **DRAFT**: Can be edited or permanently deleted after user confirmation in UI.
- **COMMITTED**: Cannot be edited or deleted (strictly immutable in QMS Ledger).

---

## Demo Script Walkthrough

### Scenario 1: Log Apollo Pharmacy Complaint via Chat
1. Open `http://localhost:5173`.
2. In the **AIVOA Copilot** chat input, enter:
   > *"Apollo Pharmacy reported 12 discolored capsules in Amoxicillin Capsules 500 mg, batch AMX240602, manufacturing March 2026, expiry February 2028."*
3. Observe the left-hand **Complaint Form** auto-populate with extracted fields and the **AI Risk Triage Card** display **HIGH** severity and quarantine recommendation.

### Scenario 2: Edit Complaint Details Conversationally
1. In the chat input, type:
   > *"Change batch number to BMX240602 and affected quantity to 48 capsules."*
2. Confirm the form updates only the batch number and quantity while preserving all other customer/product fields.

### Scenario 3: Upload Complaint Document
1. Drag & drop a `.pdf`, `.eml`, or `.txt` complaint document into the Copilot Document Upload area.
2. Verify extracted metadata, text, and preliminary quality risk triage.

### Scenario 4: Commit to QMS Ledger
1. Click **🔒 Commit to QMS Ledger** in the left panel.
2. Confirm assigned **QMS Reference Number** (e.g. `QMS-2026-000001`) and read-only committed state.

---

## Getting Started

### 1. Database Setup (MySQL)
Ensure local MySQL server is running and create the target database:
```sql
CREATE DATABASE IF NOT EXISTS aivoa;
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv

# Activate virtualenv (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure .env file
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 4. Verification & Testing Commands
```bash
# Run backend pytest test suite with coverage
cd backend
pytest --cov=app

# Run frontend linting & production build
cd frontend
npm run lint
npm run build
```

