# Architecture (initial modular monolith)

## Components
- React + TypeScript frontend
- FastAPI application/API
- Repository integration adapter
- Scanner and parser package
- Symbol index and dependency graph builder
- Git diff processor
- Impact traversal engine
- Rule-based risk and test recommendation engine
- PostgreSQL persistence
- Background worker (introduced when scan duration requires it)

## Analysis pipeline
`repository revision -> safe checkout/read -> file discovery -> parser -> symbols -> dependency edges -> diff -> impacted graph traversal -> findings -> report`

## Important implementation constraints
- Pin every scan to a commit SHA.
- Ignore generated/vendor directories by default.
- Enforce file count, file size and scan time limits.
- Do not execute project code during static analysis.
- Store provenance for every graph edge: file, line, relation type and confidence.
- Keep direct/static edges separate from heuristic/inferred edges.

## Initial API
- `GET /health`
- `GET /api/v1/status`

Planned next endpoints: workspaces, repositories, scans, analyses and reports.
