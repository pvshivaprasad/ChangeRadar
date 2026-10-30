# ChangeRadar

<p align="center">
  <strong>Change your code. Understand its impact. Know what to test.</strong><br/>
  A Python-focused change impact intelligence platform for mapping dependencies,
  tracing affected callers, and guiding regression testing.
</p>

<p align="center">
  <a href="https://changeradar-ui.onrender.com"><img src="https://img.shields.io/badge/Live%20App-Open-9BCB65?style=for-the-badge&logo=render&logoColor=111111" alt="Live app"/></a>
  <a href="https://changeradar-api.onrender.com/docs"><img src="https://img.shields.io/badge/API-Docs-24292f?style=for-the-badge&logo=fastapi" alt="API docs"/></a>
  <a href="https://changeradar-api.onrender.com/health"><img src="https://img.shields.io/badge/API-Health-24292f?style=for-the-badge" alt="API health"/></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=111"/>
  <img src="https://img.shields.io/badge/TypeScript-Frontend-3178C6?logo=typescript&logoColor=white"/>
  <img src="https://img.shields.io/badge/Analysis-AST%20%2B%20NetworkX-8A63D2"/>
  <img src="https://img.shields.io/badge/Database-PostgreSQL%20%7C%20SQLite-4169E1?logo=postgresql&logoColor=white"/>
</p>

---

## Why ChangeRadar?

A small code change can affect more than the file you edited. A changed function or dependency can ripple through services and tests.

ChangeRadar inspects a Python codebase, builds a dependency graph, compares Git revisions, and explains which symbols may be affected. It helps developers focus code review and regression testing on the parts of a project that deserve attention.

**The goal:** make change impact easier to see and easier to reason about.

## What it does

| Capability | What you get |
| --- | --- |
| **Codebase mapping** | Python modules, classes, functions, methods, imports, and call relationships |
| **Change detection** | Changed symbols matched against Git diff hunks and AST source ranges |
| **Impact analysis** | Direct and transitive callers, dependency paths, and affected files |
| **Risk context** | Explainable structural blast-radius score and impact classification |
| **Test guidance** | Prioritized regression-test recommendations based on detected relationships |
| **Pull request workflow** | GitHub-connected PR analysis and automated impact summaries |
| **Historical intelligence** | Change hotspots, recurring affected paths, test drift, and snapshot comparisons |

## How it works

<pre>
Python repository ──▶ Safe scanner ──▶ Python AST parser
                                           │
                                           ▼
Git base/head ──▶ Unified diff ──▶ Changed symbol matching
                                           │
Dependency graph ◀─────────────────────────┘
       │
       ▼
Reverse dependency traversal
       │
       ▼
Blast radius + call paths
       │
       ▼
Risk context + test recommendations
       │
       ▼
ChangeRadar workspace and API
</pre>

### Analysis principles

- **Static inspection:** source files are parsed with Python's AST; repository code is not imported or executed by the analysis engine.
- **Traceable impact:** results include affected symbols and dependency paths to help explain why an item was included.
- **Bounded scanning:** safeguards include file-size and repository limits, hidden-file handling, and .gitignore support.
- **Heuristic, not prophecy:** risk scores describe structural blast radius. They are not probabilities that a deployment will fail.
- **Python-first:** ChangeRadar 1.0 focuses on Python source analysis. Dynamic reflection and runtime-only relationships may not be discoverable statically.

## Product workflow

1. **Import a repository** into your workspace.
2. **Scan the codebase** to extract symbols and dependency relationships.
3. **Compare revisions** to identify changed functions, methods, or classes.
4. **Inspect the blast radius** through affected callers, files, and call paths.
5. **Review test recommendations** to guide your regression strategy.
6. **Track changes over time** to discover hotspots and recurring impact patterns.

## Technology

| Layer | Technologies |
| --- | --- |
| Frontend | React 18, TypeScript, Vite |
| API | Python, FastAPI, Pydantic |
| Code analysis | Python ast, NetworkX |
| Persistence | SQLAlchemy, Alembic, SQLite, PostgreSQL |
| GitHub | Git integration, PR workflows, signed webhook validation |
| Deployment | Docker, Nginx, Render |

## Try the live application

<p align="center"><a href="https://changeradar-ui.onrender.com"><strong>Launch ChangeRadar →</strong></a></p>

| Resource | Link |
| --- | --- |
| Web application | https://changeradar-ui.onrender.com |
| API documentation | https://changeradar-api.onrender.com/docs |
| API health | https://changeradar-api.onrender.com/health |

> **Free-hosting note:** the current Render deployment uses free services. Free instances may sleep when idle, so the first request after inactivity can take longer. The free PostgreSQL database is temporary and requires migration before its expiry date.

## Run locally

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm
- Git

### 1. Clone the repository

<pre>git clone https://github.com/pvshivaprasad/ChangeRadar.git
cd ChangeRadar</pre>

### 2. Start the backend

<pre>cd backend
python -m venv .venv</pre>

Windows PowerShell:

<pre>.venv\Scripts\Activate.ps1</pre>

macOS / Linux:

<pre>source .venv/bin/activate</pre>

Install dependencies and start the API:

<pre>pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000</pre>

- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

### 3. Start the frontend

Open another terminal:

<pre>cd frontend
npm install
npm run dev</pre>

Open http://localhost:5173.

### Configuration

Use environment variables for deployment-specific settings. Do not commit real credentials or production secrets.

| Variable | Purpose |
| --- | --- |
| DATABASE_URL | Database connection string |
| ENVIRONMENT | Runtime environment, such as development or production |
| FRONTEND_ORIGIN | Canonical frontend origin |
| CORS_ORIGINS | Comma-separated allowed browser origins |
| COOKIE_SECURE | Secure-cookie behavior for HTTPS |
| ENCRYPTION_KEY | Key used to protect stored integration credentials |
| GITHUB_CLIENT_ID / GITHUB_CLIENT_SECRET | GitHub OAuth configuration, when enabled |
| GITHUB_WEBHOOK_SECRET | GitHub webhook signature verification |

Generate and store secrets securely in your hosting provider's environment settings. Never paste secrets into source code, issues, screenshots, or public commits.

## API overview

The API is versioned under /api/v1. Main route groups include:

| Area | Example routes |
| --- | --- |
| Health and readiness | GET /health, GET /ready |
| Authentication | /api/v1/auth/* |
| Repositories and scanning | /api/v1/repositories, POST /api/v1/scan |
| Change analysis | POST /api/v1/analyze |
| Analysis history | /api/v1/analyses, /api/v1/historical/* |
| GitHub | /api/v1/github/* |
| Background jobs | /api/v1/jobs/* |
| Sample analysis | /api/v1/sample/* |

For request schemas and current route definitions, use the interactive [OpenAPI documentation](https://changeradar-api.onrender.com/docs).

## Tests

Run the backend test suite from the repository root:

<pre>cd backend
python -m pytest tests -v</pre>

The recorded release validation reported **94 passed, 1 skipped, 0 failed** (95 collected). The skipped test depends on an OS symlink permission unavailable in that Windows test environment. See [CHANGE_RADAR_1.0_FINAL_VALIDATION.md](CHANGE_RADAR_1.0_FINAL_VALIDATION.md) for the detailed validation record.

Build the frontend:

<pre>cd frontend
npm install
npm run build</pre>

## Validation example

A controlled validation run against the ScamShield Python repository recorded:

- 10 Python files scanned
- 76 AST symbols extracted
- 395 dependency edges identified
- 19 impacted symbols in the selected change scenario
- 22 regression-test recommendations

These are results from that specific fixture and run, not a performance or accuracy guarantee for arbitrary repositories.

## Scope and limitations

- **Language coverage:** Python-focused in this release; JavaScript and TypeScript analysis are not currently claimed.
- **Static-analysis limits:** dynamic imports, reflection, runtime-generated calls, and framework-specific behavior can be missed.
- **Risk interpretation:** the score is a deterministic heuristic based on observed structural impact, not a statistical failure prediction.
- **Test recommendations:** recommendations are inferred from code relationships; ChangeRadar does not claim those tests were executed.
- **GitHub features:** remote operations depend on valid GitHub credentials, permissions, and webhook configuration.
- **Hosting:** free-tier services can sleep and have resource/persistence constraints. Review the deployment guide before relying on the hosted instance for important work.

## Documentation

- [Deployment guide](DEPLOYMENT.md)
- [Final validation report](CHANGE_RADAR_1.0_FINAL_VALIDATION.md)
- [GitHub repository](https://github.com/pvshivaprasad/ChangeRadar)

## Contributing

Issues, bug reports, and thoughtful improvements are welcome. When reporting a problem, include the affected workflow, expected behavior, actual behavior, and relevant sanitized logs. Never include access tokens, database URLs, or other secrets.

## License

The repository currently describes ChangeRadar as proprietary. No open-source license is granted unless a license file is added to the repository.
