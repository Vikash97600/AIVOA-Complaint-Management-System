# AIVOA – AI-Powered Customer Complaint Management System

> **Enterprise Quality Management System (QMS) for Pharmaceutical Manufacturing**  
> *Driven by React 18, Redux Toolkit, FastAPI, LangGraph State Machines, Groq LLM (`gemma2-9b-it`), and MySQL Persistence.*

---

## 📋 Executive Overview

**AIVOA** is an enterprise-grade AI-powered Customer Complaint Management System designed specifically for regulated pharmaceutical manufacturing environments. It streamlines customer complaint intake, conversational edits, document extraction (PDF, EML, TXT), quality risk triaging, and formal QMS ledger commitment.

### 🌟 Core Design Principles
- **Dual-Pane Interface**: Left panel houses the structured read-only pharmaceutical complaint form & AI risk triage card, while the right panel provides the interactive AI Copilot and document dropzone.
- **AI-Driven Data Pipeline**: Strict control flow where all complaint form entries and delta updates are executed via natural-language conversation with the AI Copilot (`User Input → AI Agent → Validated Form`).
- **Immutable QMS Commitment**: Formal transition from `DRAFT` status to `COMMITTED` status in the database ledger with server-side generated QMS reference numbers and frozen JSON payload snapshots.
- **Database Source of Truth**: All complaint history, active records, and document metadata are stored persistently in MySQL.

---

## 🤖 AI Architecture (LangGraph & Groq LLM)

AIVOA utilizes **LangGraph** (`StateGraph`) to orchestrate multi-node stateful AI workflows, leveraging **Groq** (`gemma2-9b-it`) for low-latency structured extraction, classification, and risk evaluation.

### High-Level Agent Workflow

```text
                                  React UI & Redux
                                         │
                                         │ HTTP POST /api/copilot/message
                                         ▼
                                    FastAPI Router
                                         │
                                         ▼
                                  Copilot Service
                                         │
                                         ▼
                        ┌─────────────────────────────────┐
                        │      LangGraph Agent Graph      │
                        │                                 │
                        │        Intent Classifier        │───► Groq LLM (`gemma2-9b-it`)
                        │                │                │
                        │      Conditional Routing        │
                        │                │                │
                        │   ┌────────────┼────────────┐   │
                        │   ▼            ▼            ▼   │
                        │  Log          Edit       Document│
                        │Complaint   Complaint   Extraction│
                        │   │            │            │   │
                        │   └────────────┼────────────┘   │
                        │                ▼                │
                        │      AI Risk Assessment         │
                        │                │                │
                        │       Response Synthesis        │
                        └─────────────────────────────────┘
                                         │
                                         ▼
                              Structured JSON Response
                                         │
                                         ▼
                             React UI & State Update
```

---

### 1. Automated Complaint Logging
Parses natural-language user reports via Groq (`gemma2-9b-it`) and extracts structured pharmaceutical attributes into validated Pydantic schemas (`ExtractedComplaintData`).

```text
User Natural Language Message (e.g., "Apollo Pharmacy reported 12 discolored capsules...")
          │
          ▼
FastAPI (`POST /api/copilot/message`) ──► LangGraph (`LOG_COMPLAINT` Intent)
          │
          ▼
Groq LLM Service (`gemma2-9b-it`) ──► Pydantic Entity Extraction
          │
          ▼
MySQL Persistence (`ComplaintService.create_complaint` -> DRAFT)
          │
          ▼
Redux Hydration & Form Auto-Population
```

---

### 2. AI Risk Assessment & Triage
Performs preliminary quality risk evaluation on complaint data, determining suggested severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), next actions, risk rationales, and quarantine recommendations.

```text
Validated Complaint Data
          │
          ▼
LangGraph Risk Node (`risk_assessment_node`) ──► Groq LLM Evaluation
          │
          ▼
Pydantic Validation (`RiskAssessmentOutput`)
          │
          ▼
MySQL Persistence (`save_or_update_risk_assessment`) ──► UI Triage Card Update
```

*Note: All AI risk evaluations represent preliminary quality triage recommendations ("AI-assisted preliminary assessment — QA review required") and do not replace formal human QA investigation or regulatory decisions.*

---

### 3. Conversational Complaint Editing
Supports partial delta updates to existing draft complaints. Only explicitly requested fields (e.g. batch number or affected quantity) are modified while all unmentioned fields remain preserved.

```text
Natural-Language Edit Prompt (e.g., "Change batch number to BMX240602 and quantity to 48 capsules")
          │
          ▼
FastAPI (`POST /api/copilot/message` + active `complaint_id`)
          │
          ▼
LangGraph Agent (`EDIT_COMPLAINT` Intent) ──► Groq Structured Output
          │
          ▼
Deterministic Merging (Updates requested fields only) ──► MySQL Delta Update
          │
          ▼
AI Risk Re-Assessment (Automatically re-evaluates risk on updated complaint data)
```

---

### 4. Intelligent Document Extraction
Parses customer complaint documents (PDF, EML, TXT) uploaded directly through the Copilot interface.

```text
Uploaded File (.pdf / .eml / .txt) ──► File Validation & Storage (UUID Filename)
          │
          ▼
Document Extraction Service (`pypdf` / Email Parser / UTF-8 Reader)
          │
          ▼
LangGraph Agent (`DOCUMENT_EXTRACTION` Intent) ──► Groq Entity Extraction
          │
          ▼
MySQL Storage (`Complaint`, `ComplaintDocument`, `RiskAssessment`)
          │
          ▼
Form Auto-Population & Risk Triage Display
```

**Security & Safety Controls:**
- **File Restrictions**: Allowed formats `.pdf`, `.eml`, `.txt`; max file size `10 MB`.
- **Path Traversal Protection**: Stored with randomized server UUID filenames (`uploads/<uuid>.<ext>`).
- **Prompt Injection Defense**: Extracted file text is isolated as untrusted data input, preventing instruction overrides.
- **Hallucination Prevention**: Absent fields remain `null` and are not hallucinated.

---

### 5. Bonus AI Assistance Tools

1. **Complaint Completeness Checker**: Evaluates complaint data against required QMS fields, producing a **0–100% Completeness Score** with missing field alerts.
2. **Duplicate Complaint Detection**: Scans MySQL records for matching products, batches, customers, or defect descriptions to surface candidate duplicates.
3. **Executive Complaint Summary**: Generates concise summaries using `gemma2-9b-it` for QA review and executive handoffs.
4. **Quality Risk Classification**: Visual risk triage badges (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), quarantine recommendations, and rationales.

---

## 🔒 QMS Ledger Commit & Immutability

AIVOA enforces strict lifecycle management for pharmaceutical complaints:

```text
                    ┌─────────────────────────┐
                    │      DRAFT Status       │
                    │                         │
                    │ - Editable via Copilot  │
                    │ - Deletable by User     │
                    └────────────┬────────────┘
                                 │
                                 │ Confirm & Commit
                                 ▼
                    ┌─────────────────────────┐
                    │    COMMITTED Status     │
                    │                         │
                    │ - Assigned QMS-YYYY-XXX │
                    │ - Frozen Ledger JSON    │
                    │ - View-Only / Immutable │
                    └─────────────────────────┘
```

1. **DRAFT Status**: Newly logged complaints remain editable and can be updated conversationally.
2. **Commit to QMS Ledger**:
   - Generates a unique server-side QMS Reference Number (`QMS-2026-XXXXXX`).
   - Freezes a full JSON snapshot (`frozen_payload_json`) of complaint data, risk assessment, and document metadata into the `qms_ledger` table.
   - Transitions complaint status to `COMMITTED`.
3. **Immutability Protection**: `PATCH` updates, `DELETE` calls, or Copilot edit attempts targeting committed records are rejected with `HTTP 409 Conflict`.

---

## 📂 Complaint History, Persistence & Lifecycle Management

All complaints are persisted in MySQL (`complaints`, `risk_assessments`, `complaint_documents`, `qms_ledger`).

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

### Key Capabilities:
- **Complaint History Drawer**: Slide-over panel for browsing, searching, and filtering complaints by status (`ALL`, `DRAFT`, `COMMITTED`).
- **URL & Refresh State Hydration**: Selected complaints sync with URL query parameter (`?complaintId=<uuid>`). Browser refresh automatically re-hydrates Redux and UI state directly from MySQL.
- **Draft Deletion**: Users can delete accidental draft complaints via the UI (with a confirmation modal dialog). Deletion is transactional and cleans up dependent draft records in MySQL.
- **Committed Record Safety**: Committed complaints display an enterprise locked view-only banner; deletion buttons are hidden and backend-blocked.

---

## 🏛️ Database & Backend Architecture

Powered by **Python 3.11+**, **FastAPI**, **SQLAlchemy 2.0 (Async ORM)**, and **MySQL**.

### Key Tech Stack
- **API Framework:** FastAPI 0.110+ with OpenAPI Swagger (`/docs`) & ReDoc (`/redoc`).
- **Async Database Driver:** `aiomysql` (`mysql+aiomysql://`) for FastAPI async handlers.
- **Sync Migration Driver:** `pymysql` (`mysql+pymysql://`) for Alembic database migrations.
- **Validation:** Pydantic v2 schemas.

### Database ER Diagram

```text
┌────────────────────────────────────────────────────────┐
│                      complaints                        │
├────────────────────────────────────────────────────────┤
│ id: UUID (PK)                                          │
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
│id: UUID (PK)     │  │complaint_id (FK) │  │id: UUID (PK)     │
│complaint_id (FK) │  │file_name: VARCHAR│  │complaint_id (FK) │
│severity: Enum    │  │file_path: VARCHAR│  │qms_ref_num (UQ)  │
│category: VARCHAR │  │file_type: VARCHAR│  │committed_at(tz)  │
│next_action: TEXT │  │file_size: INT    │  │frozen_payload    │
│risk_details: TEXT│  │extracted_text    │  └──────────────────┘
│quarantine: BOOL  │  │uploaded_at (tz)  │
│created_at (tz)   │  │uploaded_at (tz)  │
└──────────────────┘  └──────────────────┘
```

---

## 🛠️ Repository Structure

```text
AIVOA/
├── frontend/             # React 18 + Redux Toolkit + Vite (Port 5173)
│   ├── src/
│   │   ├── components/   # Form, Copilot, History Drawer & Risk components
│   │   ├── store/        # Redux Toolkit slices, thunks, selectors
│   │   ├── services/     # API integration client
│   │   └── App.jsx
│   └── package.json
│
├── backend/              # Python 3.11+ FastAPI + MySQL (Port 8000)
│   ├── app/
│   │   ├── ai/           # LangGraph graph, nodes & prompt definitions
│   │   │   ├── nodes/    # classifier, log_complaint, edit_complaint, etc.
│   │   │   ├── state.py  # AgentState TypedDict & Intent enum
│   │   │   └── graph.py  # AIVOA compiled state graph
│   │   ├── api/          # REST API Routes (/api)
│   │   ├── core/         # Config, custom exceptions, logging
│   │   ├── database/     # SQLAlchemy models & database session
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic services
│   │   └── main.py       # FastAPI application entry point
│   ├── alembic/          # Database migrations
│   ├── tests/            # Pytest suite (74 passing tests)
│   ├── requirements.txt
│   └── .env.example
│
└── README.md
```

---

## 🌐 REST API Specification

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health check |
| `POST` | `/api/copilot/message` | Process natural language message via LangGraph AI Agent |
| `POST` | `/api/copilot/document` | Extract complaint details from uploaded PDF, TXT, or EML |
| `POST` | `/api/complaints` | Create a new DRAFT complaint record |
| `GET` | `/api/complaints` | List complaints with pagination, status filter (`?status=DRAFT|COMMITTED`), and search (`?search=query`) |
| `GET` | `/api/complaints/{id}` | Retrieve complete complaint detail, risk assessment, and documents |
| `PATCH` | `/api/complaints/{id}` | Update partial complaint delta fields (blocked with `409` if COMMITTED) |
| `DELETE` | `/api/complaints/{id}` | Permanently delete DRAFT complaint (blocked with `409` if COMMITTED) |
| `POST` | `/api/complaints/{id}/commit` | Formally commit DRAFT complaint to QMS Ledger |
| `GET` | `/api/complaints/{id}/qms` | Retrieve frozen QMS Ledger snapshot |
| `POST` | `/api/complaints/{id}/completeness` | Evaluate AI Complaint Completeness score |
| `POST` | `/api/complaints/{id}/duplicates` | Search candidate duplicate complaints in MySQL |
| `POST` | `/api/complaints/{id}/summary` | Generate executive complaint summary |

---

## 🎬 Demo Script Walkthrough

### Scenario 1: Log Complaint via Chat
1. Open `http://localhost:5173`.
2. In the Copilot chat, enter:
   > *"Apollo Pharmacy reported 12 discolored capsules in Amoxicillin Capsules 500 mg, batch AMX240602, manufacturing March 2026, expiry February 2028."*
3. Observe the left-hand **Complaint Form** auto-populate with extracted fields and the **AI Risk Triage Card** display **HIGH** severity and quarantine recommendation.

### Scenario 2: Edit Complaint Conversationally
1. In the chat, type:
   > *"Change batch number to BMX240602 and affected quantity to 48 capsules."*
2. Confirm the form updates only the batch number and quantity while preserving all customer/product fields.

### Scenario 3: Upload Complaint Document
1. Drag & drop a `.pdf`, `.eml`, or `.txt` complaint document into the Copilot Document Upload area.
2. Observe auto-extracted metadata, text, and preliminary risk triage.

### Scenario 4: Commit to QMS Ledger
1. Click **🔒 Commit to QMS Ledger** in the left panel.
2. Confirm assigned **QMS Reference Number** (e.g. `QMS-2026-000001`) and read-only committed state.

---

## 🚀 Quick Start & Installation

### 1. Database Setup (MySQL)
Ensure local MySQL server is running and create the database:
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

# Configure environment variables (.env)
# GROQ_API_KEY=gsk_your_key_here
# DATABASE_URL=mysql+pymysql://root:password@localhost:3306/aivoa

# Run database migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 4. Automated Testing & Verification
```bash
# Run backend pytest suite (74 tests)
cd backend
pytest -v

# Run frontend linter & production build
cd frontend
npm run lint
npm run build
```
