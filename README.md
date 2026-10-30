# ChangeRadar — Software Change Impact Intelligence Platform

**See the impact before it happens.**

ChangeRadar is an enterprise-grade Software Change Impact Intelligence platform. It parses source code repositories, extracts function and class dependencies, traverses directed call graphs using NetworkX, intersects unified Git commit diffs with AST line boundaries, and deterministically identifies downstream blast radius and regression test suites before merging or deploying code.

---

## Architecture Overview

```
                      ┌────────────────────────────────────────┐
                      │        Target Git Repository           │
                      │   (e.g., commit HEAD~1 -> HEAD)        │
                      └──────────────────┬─────────────────────┘
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
       ┌───────────────────────┐                   ┌───────────────────────────┐
       │   RepositoryScanner   │                   │     GitDiffProcessor      │
       │ - Walks .py files     │                   │ - git diff -U0 base head  │
       │ - Respects .gitignore │                   │ - Unified hunk parser     │
       │ - Max 2MB file safety │                   │ - Add/Del/Rename handlers │
       └───────────┬───────────┘                   └─────────────┬─────────────┘
                   │                                             │
                   ▼                                             ▼
       ┌───────────────────────┐                   ┌───────────────────────────┐
       │    PythonASTParser    │                   │   Intersect Diff Lines    │
       │ - Pure ast.parse      │                   │ with AST Symbol Range     │
       │ - Zero code execution │                   │ -> Detected Changed Syms  │
       └───────────┬───────────┘                   └─────────────┬─────────────┘
                   │                                             │
                   ▼                                             │
       ┌───────────────────────┐                                 │
       │ DependencyGraphEngine │                                 │
       │ - NetworkX DiGraph    │                                 │
       │ - Reverse graph BFS   │◄────────────────────────────────┘
       └───────────┬───────────┘
                   │
                   ▼
       ┌───────────────────────────────────────────────────────┐
       │               Impact Analysis Pipeline                │
       │ - Blast radius classification (Depth 0, 1, 2+)        │
       │ - Deterministic causal call paths                     │
       │ - TestRecommendationEngine: prioritized test mapping  │
       │ - Transparent, non-fabricated risk scoring formula   │
       └───────────────────────────┬───────────────────────────┘
                                   │
                                   ▼
       ┌───────────────────────────────────────────────────────┐
       │                 FastAPI REST API                      │
       │  POST /api/v1/scan     - Static repository AST scan   │
       │  POST /api/v1/analyze  - Change impact analysis       │
       │  GET  /api/v1/sample/* - Verified fixture demo        │
       │  GET  /health          - Connection diagnostics       │
       └───────────────────────────┬───────────────────────────┘
                                   │
                                   ▼
       ┌───────────────────────────────────────────────────────┐
       │                 ChangeRadar Workspace                 │
       │ - Editorial Light Landing / Obsidian Dark Workspace   │
       │ - Real-time Blast Radius & Call Tree Explorer         │
       │ - AST Symbol Registry with Type Filters               │
       │ - Recommended Regression Test Suites                  │
       └───────────────────────────────────────────────────────┘
```

---

---

## Key Features

1. **Pure Static Code Analysis (Zero Execution Security)**:
   - Uses Python's standard library `ast.parse` in pure inspection mode.
   - Project code is **never imported, executed, or eval'd**, eliminating arbitrary code execution vectors.
   - Enforces a 2MB maximum file size ceiling to prevent memory exhaustion on oversized files.

2. **Scanner Safety & Security**:
   - Parses `.gitignore` rules (wildcards, folder prefixes, and file patterns).
   - Prunes hidden directories (`.git`, `.venv`, `.cache`) and hidden files (`.secret.py`).
   - Traverses directories with `followlinks=False` and drops external symlinks resolving outside the repository.
   - Enforces localhost-only filesystem scanning; rejects drive roots (`C:\`) and protected system directories (`C:\Windows`, `/etc`, etc.) with `HTTP 403 Forbidden`.

3. **Accurate Git Diff Intersect**:
   - Parses unified diff hunks (`git diff -U0 base head`) with support for added files, deleted files, renamed files, and multiple modified functions within a single file.
   - Intersects modification intervals `[start_line, end_line]` against AST symbol boundaries.
   - Strict regex validation on commit references prevents flag or option injection.

4. **NetworkX Directed Call Graphs & Blast Radius**:
   - Constructs directed graphs (`Caller -> Callee`) and reverses them (`Callee -> Caller`).
   - Breadth-first search traverses upstream callers with exact dependency paths (e.g. `auth.service.AuthService -> checkout.payment.process_payment -> tests.test_payment`).
   - Differentiates direct changes (depth 0), direct dependents (depth 1), and transitive dependents (depth 2+).

5. **GitHub Integration (0.4)**:
   - Connect GitHub accounts with AES-128-CBC / Fernet token encryption at rest derived via PBKDF2HMAC.
   - Webhook processing with HMAC-SHA256 signature verification (`X-Hub-Signature-256`) and delivery deduplication (`X-GitHub-Delivery`).
   - Automated Pull Request change impact analysis with sticky markdown PR comments and blast radius summaries.

6. **Historical Change Intelligence (0.5)**:
   - Multi-commit repository tracking across branches and PRs.
   - Change hotspot detection identifying recurring points of instability.
   - Cumulative downstream caller risk profiling and regression test drift analysis.
   - Comparative diff analysis between historical analysis snapshots.

7. **Production Container Deployment & Background Jobs (0.6)**:
   - Multi-stage unprivileged Docker images (`Dockerfile.backend`, `Dockerfile.frontend`).
   - Production Docker Compose orchestration with PostgreSQL 16 and health checks.
   - Nginx reverse proxy with HTTP security headers (`X-Frame-Options`, `CSP`, `nosniff`) and gzip compression.
   - Resilient background job queue with process-restart crash reconciliation and multi-tenant concurrency quotas.

---

## Technology Stack

- **Frontend**: React 18, TypeScript, Vite, custom design system, Framer Motion, Lucide icons.
- **Backend**: Python 3.11+, FastAPI, Pydantic 2.0, SQLAlchemy 2.0, Alembic.
- **Analysis**: Python standard library `ast`, NetworkX 3.4+.
- **Security**: Fernet authenticated encryption, PBKDF2HMAC password & token hashing, HttpOnly session cookies.
- **Database**: SQLite (local development with WAL) / PostgreSQL 16 (production).
- **Deployment**: Docker, Docker Compose, Nginx.

---

## Installation & Quickstart

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- Git

### 1. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Run FastAPI server on localhost:8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
- API Docs & Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Run Vite development server
npm run dev
```
Open [http://localhost:5173/](http://localhost:5173/) in your browser.

### 3. Docker Deployment (Production)
```bash
# Copy example environment
cp .env.production.example .env

# Build and start services
docker compose up -d --build
```
Access the application through the reverse proxy at [http://localhost:80](http://localhost:80).

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service status, environment, and masked database connection diagnostics. |
| `GET` | `/ready` | Production readiness probe verifying database query execution. |
| `GET` | `/api/v1/status` | API operational readiness check. |
| `POST` | `/api/v1/auth/register` | Registers a new user with PBKDF2-hashed password and HttpOnly cookie. |
| `POST` | `/api/v1/auth/login` | Authenticates user credentials and sets HttpOnly session token. |
| `POST` | `/api/v1/auth/logout` | Revokes the active session token in the database. |
| `GET` | `/api/v1/auth/me` | Returns profile of the currently authenticated session. |
| `GET` | `/api/v1/repositories` | Lists all persisted repositories for the authenticated tenant. |
| `POST` | `/api/v1/repositories` | Imports, scans, and persists a repository to SQLite/PostgreSQL. |
| `DELETE`| `/api/v1/repositories/{id}` | Archives or removes a repository and cascaded records. |
| `POST` | `/api/v1/scan` | Scans a local repository directory, returning all AST symbols and edges. |
| `POST` | `/api/v1/analyze` | Executes change impact analysis between base and head commits. |
| `GET` | `/api/v1/analyses` | Lists historical change impact analyses across repositories. |
| `GET` | `/api/v1/historical/{repo_id}/summary` | Aggregated change hotspots, affected callers, and test drift. |
| `GET` | `/api/v1/historical/{repo_id}/compare` | Comparative diff between two analysis snapshots. |
| `GET` | `/api/v1/github/account` | Retrieves connected GitHub account and masked token. |
| `POST` | `/api/v1/github/connect` | Links a GitHub personal access token with Fernet encryption. |
| `POST` | `/api/v1/github/webhook` | Ingests GitHub webhooks with HMAC-SHA256 signature verification. |
| `POST` | `/api/v1/jobs` | Enqueues background repository analysis or GitHub sync job. |
| `GET` | `/api/v1/jobs/{job_id}` | Polls status, progress, and error state of a background job. |
| `GET` | `/api/v1/sample/scan` | Returns scanned symbols and call graph for the verified synthetic test fixture. |
| `GET` | `/api/v1/sample/run` | Executes live end-to-end impact analysis on the verified synthetic test fixture. |

### Default Development Credentials
- **Email**: `dev@changeradar.io`
- **Password**: `changeradar2026`
- **Demo Mode**: Quick-fill button available on the Sign-In interface.

---

## Automated Verification & Test Results

The platform includes an automated pytest suite covering units, edge cases, safety boundaries, and integration flows:

```bash
# Run backend test suite
cd backend
python -m pytest tests -v
```

**Results:**
- **95 Total Tests**: **94 passed**, 1 skipped (OS symlink privilege check on Windows).
- **Test Modules**:
  - `test_github_deep_audit.py`: Fernet token encryption, production key enforcement, path traversal guards, webhook HMAC security matrix, multi-tenant isolation.
  - `test_controlled_historical_repo.py`: End-to-end multi-commit Git repository with AST scans, hotspot detection, and comparative snapshot diffs.
  - `test_background_jobs_deep_audit.py`: Crash reconciliation on startup, duplicate job suppression, per-user concurrency quotas.
  - `test_deployment_and_postgres.py`: PostgreSQL DDL compilation, health/ready probes, job throttling.
  - `test_dependency_graph_accuracy.py`: Direct/indirect calls, imported aliases, class methods, local variable type inference, recursion, cycles.
  - `test_changed_symbol_detection_accuracy.py`: Function additions, deletions, renames, moved functions, per-file specificity.
  - `test_impact_analysis_accuracy.py`: Path provenance, shortest-path BFS, cycle termination in cyclic meshes.
  - `test_risk_score_accuracy.py`: Deterministic score formulas, fanout ceilings, boundary limits.
  - `test_scanner_safety.py`: `.gitignore` rules, hidden folders/files, oversized file cap (> 2MB), syntax/null-byte resilience.
  - `test_security_audit_stage2.py`: Hashed tokens in DB, multi-session coexistence, rate limiting, path traversal blocks.

---

## Real-World Repository Validation

ChangeRadar was validated against **ScamShield**, an existing multi-module Python project:
- **Scan Metrics**: 10 Python files, 76 AST symbols, 395 dependency edges parsed in **13.45 ms**.
- **Impact Analysis**: Modifying `scamshield.rules.analyze` between `master` and `feature/enhance-rules` identified:
  - 1 direct modified function (`scamshield.rules.analyze`)
  - 19 impacted downstream symbols across depth 0, 1, and 2 (`scamshield.model.explain`, `api.analyze_sms`, etc.)
  - 22 targeted regression test recommendations from `tests/test_scamshield.py` and `tests/test_api.py`.
  - Execution completed in **28 ms** with zero runtime code execution.

---

## Limitations & Production Prerequisites

1. **Host Environment Prerequisites**:
   - **PostgreSQL**: Production deployment requires a live PostgreSQL instance configured via `DATABASE_URL`. In local development, SQLite with WAL mode is used.
   - **Docker Engine**: Container builds require Docker 24+ and Docker Compose v2.
   - **GitHub Remote API**: Real PR commenting and repository cloning require `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, and a GitHub access token with `repo` scope.
2. **Language Support**: ChangeRadar 1.0 focuses on Python (3.8 - 3.13) AST analysis. Multi-language support (JavaScript/TypeScript via Tree-sitter) is scheduled for subsequent milestones.
3. **Dynamic Reflection**: Pure static AST parsing intentionally excludes runtime dynamic evaluation (e.g. `eval()`, dynamic `getattr()`) to guarantee zero code execution safety.

---

## License

Proprietary — ChangeRadar Enterprise Change Intelligence Platform.

