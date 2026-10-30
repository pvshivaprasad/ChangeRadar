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
    """Detects whether a file path is a test module."""
    clean = file_path.replace("\\", "/").lower()
    base = os.path.basename(clean)
    return (
        base.startswith("test_")
        or base.endswith("_test.py")
        or "/tests/" in clean
        or "/test/" in clean
        or clean.startswith("tests/")
    )


class TestRecommendationEngine:
    """
    Examines all discovered test symbols and edges to find tests that
    import or execute any symbol in the impacted blast radius.
    """

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

        impacted_ids = {s.symbol_id: s for s in impacted_symbols}

        for sym_id, imp_info in impacted_ids.items():
            # Check if any test directly calls or imports this symbol
            matching_edges = self.test_callers_by_target.get(sym_id, [])

            # Also check if matching edges exist for module prefix
            # e.g. if test imports 'auth.service' and changed symbol is 'auth.service.validate_token'
            parts = sym_id.split(".")
            for i in range(1, len(parts)):
                prefix = ".".join(parts[:i])
                matching_edges.extend(self.test_callers_by_target.get(prefix, []))

            for edge in matching_edges:
                key = f"{edge.file_path}::{edge.source_id}"
                if key not in seen_test_cases:
                    seen_test_cases.add(key)

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

        # Fallback heuristic: If no specific test edge was matched,
        # but a test file exists with matching module name (e.g. tests/test_auth.py for auth/service.py)
        for imp in impacted_symbols:
            stem = os.path.splitext(os.path.basename(imp.file_path))[0]
            for test_sym in self.test_symbols:
                test_stem = os.path.splitext(os.path.basename(test_sym.file_path))[0]
                if stem in test_stem or test_stem in stem:
                    key = f"{test_sym.file_path}::{test_sym.id}"
                    if key not in seen_test_cases:
                        seen_test_cases.add(key)
                        recommendations.append(
                            TestRecommendation(
                                test_file=test_sym.file_path,
                                test_symbol_id=test_sym.id,
                                target_symbol_id=imp.symbol_id,
                                reason=f"Heuristic test file match for module '{stem}'",
                                priority="medium" if imp.depth <= 1 else "low",
                            )
                        )

        # Sort recommendations: high priority first
        recommendations.sort(key=lambda r: (0 if r.priority == "high" else 1, r.test_file))
        return recommendations
