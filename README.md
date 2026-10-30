# ChangeRadar

**See the impact before it happens.**

ChangeRadar is a software change impact intelligence platform. It aims to help engineering teams understand code dependencies, assess potential change impact and identify relevant tests before merging.

> Current status: v0.1 foundation. The landing page, workspace shell and API health endpoint are implemented. Repository scanning, GitHub authorization and real impact analysis are not implemented yet.

## Stack
- Frontend: React, TypeScript, Vite, custom CSS, Lucide icons
- Backend: Python, FastAPI, Pydantic Settings
- Database: PostgreSQL (Docker Compose)

## Run locally

### Prerequisites
- Node.js 20+
- Python 3.11+
- Docker Desktop (optional, for PostgreSQL)

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173.

### Backend
```bash
cd backend
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Health check: http://localhost:8000/health  
API docs: http://localhost:8000/docs

### PostgreSQL + API with Docker
From the project root:
```bash
docker compose up --build -d
```
PostgreSQL is exposed on port 5432 and the API on port 8000. The frontend is run separately with `cd frontend && npm install && npm run dev`.

## Current UI behavior
- Landing page routes into a local workspace preview.
- Workspace navigation is interactive.
- Repository connection dialog is currently a UI placeholder; it does not yet authorize GitHub or store a repository.
- Empty states are intentional. No sample analytics are fabricated.

## Product principles
1. Evidence before AI explanations.
2. Potential impact is not a confirmed defect.
3. Never execute untrusted repository code during static analysis.
4. Every analysis must be reproducible against immutable commit SHAs.

## Roadmap
1. Python repository scanner and AST symbol extraction.
2. Import and call dependency graph with source provenance.
3. Git diff and changed-symbol detection.
4. Impact traversal and explainable reports.
5. Test recommendations and GitHub PR integration.
