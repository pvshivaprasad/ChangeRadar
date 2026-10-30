# ChangeRadar — Product Requirements (v0.1)

## Product vision
Help engineering teams understand the potential impact of code changes before they merge or deploy.

## Initial users
- Software developers
- QA engineers
- Engineering leads

## MVP workflow
1. Create a workspace.
2. Connect a GitHub repository (read-only access first).
3. Scan a supported repository revision.
4. Extract files, symbols, imports and dependency edges.
5. Compare two Git revisions.
6. Trace direct and indirect dependencies from changed symbols.
7. Produce an evidence-backed impact report and test suggestions.

## MVP scope
- Python repository scanning
- Python AST-based symbol extraction
- Import and statically resolvable call relationships
- Git diff ingestion
- Dependency graph traversal
- Explainable rule-based risk indicators
- Suggested tests based on changed modules and repository test layout

## Explicit non-goals for v0.1
- Claiming to predict bugs with certainty
- Executing arbitrary repository code
- Automatic code modification or merging
- Enterprise SSO / SCIM
- Full multi-language semantic analysis

## Product principles
1. Evidence before AI-generated explanations.
2. Clearly distinguish confirmed relationships from inferred relationships.
3. Never present a potential impact as a confirmed defect.
4. Respect repository permissions and minimize stored source data.
5. Every analysis is tied to immutable base and head commit SHAs.

## Success criteria
- Repeatable scan output for the same commit SHA.
- Correct extraction on a curated Python fixture repository.
- Dependency edges include source locations and relationship type.
- Impact findings explain the path from changed symbol to affected symbol.
- Unsupported or unresolved relationships are labeled honestly.
