from datetime import datetime, timezone
from typing import List, Optional

from .git_diff import GitDiffProcessor
from .graph import DependencyGraphEngine
from .models import ImpactAnalysisReport, ScanSummary
from .scanner import RepositoryScanner
from .test_mapper import TestRecommendationEngine


def run_impact_analysis(
    repo_path: str,
    base_commit: str = "HEAD~1",
    head_commit: str = "HEAD",
) -> ImpactAnalysisReport:
    """
    Executes the full software change impact pipeline:
    1. Scan repository files and extract symbols via pure AST parsing.
    2. Ingest Git diff between base and head commit SHAs to detect changed symbols.
    3. Construct NetworkX dependency graph and traverse callers for blast radius.
    4. Map relevant tests based on call paths.
    5. Compute explainable risk levels and evidence provenance.
    """
    scanner = RepositoryScanner(repo_path)
    scan_summary = scanner.scan()

    diff_processor = GitDiffProcessor(repo_path)
    changed_files, changed_symbols = diff_processor.get_changed_symbols(
        base_commit=base_commit,
        head_commit=head_commit,
        symbols=scan_summary.symbols,
    )

    graph_engine = DependencyGraphEngine(
        symbols=scan_summary.symbols,
        edges=scan_summary.edges,
    )

    changed_symbol_ids = [s.id for s in changed_symbols]
    impacted_symbols = graph_engine.find_impacted_symbols(changed_symbol_ids)

    test_engine = TestRecommendationEngine(
        all_symbols=scan_summary.symbols,
        all_edges=scan_summary.edges,
    )
    recommended_tests = test_engine.recommend_tests(impacted_symbols)

    risk_level, risk_score = graph_engine.compute_risk(impacted_symbols)

    summary_text = (
        f"Analyzed {len(changed_symbols)} changed symbol(s) in {len(changed_files)} file(s). "
        f"Blast radius traversal identified {len(impacted_symbols)} directly or transitively affected symbol(s). "
        f"Selected {len(recommended_tests)} targeted test(s) to validate code changes."
    )

    return ImpactAnalysisReport(
        repo_path=repo_path,
        base_commit=base_commit,
        head_commit=head_commit,
        changed_files=changed_files,
        changed_symbols=changed_symbols,
        impacted_symbols=impacted_symbols,
        graph_nodes_count=scan_summary.symbol_count,
        graph_edges_count=scan_summary.edge_count,
        recommended_tests=recommended_tests,
        risk_level=risk_level,
        risk_score=risk_score,
        summary_text=summary_text,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
