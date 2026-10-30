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

5. **Regression Test Recommendations**:
   - Maps impacted blast-radius symbols to test suites using both explicit AST call edges and naming heuristics.
   - Prioritizes tests as High (directly tests modified symbol) or Medium (validates downstream callers).

6. **Explainable Risk Scoring**:
   - Calculates a deterministic risk score from direct changes, caller fanout, depth, and affected file count.
   - Categorizes risk into `low`, `medium`, `elevated`, or `high`. No fabricated metrics.

---

## Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS / custom tokens, Framer Motion, Lucide icons.
- **Backend**: Python 3.11+, FastAPI, Pydantic 2.0, SQLAlchemy 2.0.
- **Analysis**: Python standard library `ast`, NetworkX 3.4+.
- **Database**: SQLite (default local development) / PostgreSQL (production configured via `DATABASE_URL`).

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

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service status, environment, and masked database connection diagnostics. |
| `GET` | `/api/v1/status` | API operational readiness check. |
| `POST` | `/api/v1/scan` | Scans a local repository directory, returning all AST symbols and dependency edges. |
| `POST` | `/api/v1/analyze` | Executes change impact analysis between `base_commit` and `head_commit`. |
| `GET` | `/api/v1/sample/scan` | Returns scanned symbols and call graph for the verified synthetic test fixture. |
| `GET` | `/api/v1/sample/run` | Executes live end-to-end impact analysis on the verified synthetic test fixture. |

---

## Automated Verification & Test Results

The platform includes an automated pytest suite covering units, edge cases, safety boundaries, and integration flows:

```bash
# Run backend test suite
cd backend
python -m pytest pytest.ini tests -v
```

**Results:**
- **30 Total Tests**: **29 passed**, 1 skipped (OS symlink privilege check on Windows).
- **Test Modules**:
  - `test_ast_parser.py`: Class, method, function extraction, docstrings, and call edges.
  - `test_scanner.py`: Local repository traversal, commit detection, and edge normalization.
  - `test_git_diff_cases.py`: Added, deleted, renamed files, multiple hunks, and empty diffs.
  - `test_scanner_safety.py`: `.gitignore` rules, hidden folders/files, oversized file cap (> 2MB), and syntax/null-byte resilience.
  - `test_api_security.py`: Rejection of drive roots (`C:\`), Windows system directories (`C:\Windows`), and invalid git revisions.
  - `test_impact_engine.py`: Full impact analysis on synthetic fixture (`HEAD~1` to `HEAD`).
  - `test_independent_repo.py`: Impact analysis on an independent multi-service repository (`orders`, `inventory`, `notifications`).

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

## Limitations

1. **Language Support**: MVP v0.1.1 is focused on Python (3.8 - 3.13) AST analysis. Multi-language support (JavaScript/TypeScript via Tree-sitter) is scheduled for Milestone 3.
2. **Local Repositories**: Scanning operates against accessible local repository paths on the host filesystem. Direct GitHub REST API & Webhook synchronization will build on this static engine.
3. **Dynamic Reflection**: Pure static AST parsing deliberately excludes runtime dynamic metaprogramming (e.g. `getattr(mod, dynamic_var)()`) to maintain zero-execution safety. Dynamic edges are recorded with `confidence="inferred"`.

---

## License

Proprietary — ChangeRadar Enterprise Intelligence Platform.
