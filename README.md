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
- **QMS Commitment:** Formal transition from `DRAFT` status to `COMMITTED` status in the database ledger with frozen payload snapshots.

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
│   │   ├── database/     # SQLAlchemy models & sessions
│   │   ├── schemas/      # Pydantic structured schemas
│   │   ├── ai/           # LangGraph orchestrator & Groq prompts
│   │   └── main.py
│   ├── requirements.txt
│   └── .env.example
│
└── README.md
```

---

## Getting Started

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# Activate virtualenv
# On Windows: venv\Scripts\activate
# On Linux/macOS: source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Configure GROQ_API_KEY in .env

uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
