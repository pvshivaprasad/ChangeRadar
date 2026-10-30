import os
from typing import Dict, List, Set

from .models import (
    DependencyEdge,
    ImpactType,
    ImpactedSymbol,
    Symbol,
    TestRecommendation,
)


def is_test_file(file_path: str) -> bool:
    """Detects whether a file path is a Python test module."""
    clean = file_path.replace("\\", "/").lower()
    if not clean.endswith(".py"):
        return False
    base = os.path.basename(clean)
    return (
        base.startswith("test_")
        or base.endswith("_test.py")
        or "/tests/" in clean
        or "/test/" in clean
        or clean.startswith("tests/")
        or clean.startswith("test/")
    )


class TestRecommendationEngine:
    """
    Examines all discovered test symbols and edges to find tests that
    import or execute any symbol in the impacted blast radius.
    """
    __test__ = False

    def __init__(self, all_symbols: List[Symbol], all_edges: List[DependencyEdge]):
        self.all_symbols = all_symbols
        self.all_edges = all_edges

        # Find all test symbols
        self.test_symbols = [
            s for s in all_symbols
            if is_test_file(s.file_path) and (
                s.name.startswith("test_") or s.name.startswith("Test") or s.file_path.endswith(".py")
            )
        ]

        # Map callers: target_symbol_id -> list of test caller edges
        self.test_callers_by_target: Dict[str, List[DependencyEdge]] = {}
        for edge in all_edges:
            if is_test_file(edge.file_path):
                self.test_callers_by_target.setdefault(edge.target_id, []).append(edge)

    def recommend_tests(self, impacted_symbols: List[ImpactedSymbol]) -> List[TestRecommendation]:
        recommendations: List[TestRecommendation] = []
        seen_test_cases: Set[str] = set()
        matched_target_ids: Set[str] = set()

        impacted_ids = {s.symbol_id: s for s in impacted_symbols}

        # 1. Exact dependency edge matching (calls or imports from test modules/functions)
        for sym_id, imp_info in impacted_ids.items():
            matching_edges = list(self.test_callers_by_target.get(sym_id, []))

            # Also check prefix matches if direct symbol calls were not found
            # e.g. test imports 'auth.service' and changed symbol is 'auth.service.validate_token'
            if not matching_edges:
                parts = sym_id.split(".")
                for i in range(len(parts) - 1, 0, -1):
                    prefix = ".".join(parts[:i])
                    edges = self.test_callers_by_target.get(prefix, [])
                    if edges:
                        matching_edges.extend(edges)
                        break

            # Separate function-level test callers from module-level test callers
            func_edges = [
                e for e in matching_edges
                if not e.source_id.endswith(os.path.splitext(os.path.basename(e.file_path))[0])
            ]
            active_edges = func_edges if func_edges else matching_edges

            for edge in active_edges:
                key = f"{edge.file_path}::{edge.source_id}::{sym_id}"
                if key not in seen_test_cases:
                    seen_test_cases.add(key)
                    matched_target_ids.add(sym_id)

                    if imp_info.impact_type == ImpactType.DIRECT_CHANGE:
                        reason = f"Directly tests modified symbol '{imp_info.symbol_name}' in {imp_info.file_path}"
                        priority = "high"
                    else:
                        reason = f"Validates downstream dependent '{imp_info.symbol_name}' (affected at depth {imp_info.depth})"
                        priority = "medium"

                    recommendations.append(
                        TestRecommendation(
                            test_file=edge.file_path,
                            test_symbol_id=edge.source_id,
                            target_symbol_id=sym_id,
                            reason=reason,
                            priority=priority,
                        )
                    )

        # 2. Strict convention heuristic fallback:
        # Only for impacted symbols that have NO matching test edges,
        # match test file if filename strictly equals test_{stem}.py or {stem}_test.py
        for imp in impacted_symbols:
            if imp.symbol_id in matched_target_ids:
                continue

            stem = os.path.splitext(os.path.basename(imp.file_path))[0]
            if stem.startswith("__"):
                continue

            matching_test_files = {
                s.file_path
                for s in self.test_symbols
                if os.path.basename(s.file_path).lower() in (f"test_{stem.lower()}.py", f"{stem.lower()}_test.py")
            }

            for test_file in matching_test_files:
                key = f"{test_file}::{imp.symbol_id}"
                if key not in seen_test_cases:
                    seen_test_cases.add(key)
                    matched_target_ids.add(imp.symbol_id)
                    recommendations.append(
                        TestRecommendation(
                            test_file=test_file,
                            test_symbol_id=None,
                            target_symbol_id=imp.symbol_id,
                            reason=f"Convention naming match: test file corresponds to module '{stem}'",
                            priority="medium" if imp.depth <= 1 else "low",
                        )
                    )

        # Sort recommendations: high priority first, then medium, then low; then by file
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda r: (priority_order.get(r.priority, 1), r.test_file))
        return recommendations
