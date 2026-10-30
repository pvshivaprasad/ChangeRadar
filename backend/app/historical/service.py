"""Historical Change Intelligence Service for ChangeRadar 1.0.

Derives evidence-based historical insights from persisted analysis records:
- Frequently modified modules
- Frequently impacted downstream components (blast radius hotspots)
- Recurring dependency paths
- High blast-radius hotspots
- Repeatedly recommended tests
- Analysis-to-analysis comparative intelligence
- Historical timeline and risk trends
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy.orm import Session

from ..models import Analysis, Repository


class HistoricalIntelligenceService:
    """Computes explainable historical patterns across persisted repository change analyses."""

    def __init__(self, db: Session):
        self.db = db

    def get_repository_analyses(
        self,
        repository_id: int,
        user_id: int,
        limit: int = 50,
    ) -> List[Analysis]:
        """Fetches completed analyses for a repository, enforcing strict user ownership."""
        return (
            self.db.query(Analysis)
            .filter(
                Analysis.repository_id == repository_id,
                Analysis.user_id == user_id,
                Analysis.status == "completed",
            )
            .order_by(Analysis.created_at.desc())
            .limit(limit)
            .all()
        )

    def compute_change_patterns(
        self,
        repository_id: int,
        user_id: int,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Analyzes historical change records to discover recurring hotspots,
        frequently affected components, and test recommendation patterns.
        """
        analyses = self.get_repository_analyses(repository_id, user_id, limit=limit)
        total_analyses = len(analyses)

        if total_analyses == 0:
            return {
                "repository_id": repository_id,
                "total_analyses": 0,
                "message": "Insufficient historical data. Run one or more change analyses to build intelligence.",
                "frequently_modified_modules": [],
                "frequently_impacted_components": [],
                "recurring_paths": [],
                "hotspots": [],
                "repeatedly_recommended_tests": [],
                "risk_trend": [],
            }

        file_change_counter: Counter = Counter()
        symbol_impact_counter: Counter = Counter()
        symbol_change_counter: Counter = Counter()
        path_counter: Counter = Counter()
        test_rec_counter: Counter = Counter()
        high_risk_files: Counter = Counter()

        risk_trend = []

        for a in reversed(analyses):  # chronological order for trend
            risk_trend.append({
                "analysis_id": a.id,
                "commit": a.head_commit[:8] if a.head_commit else "HEAD",
                "risk_score": a.risk_score,
                "risk_level": a.risk_level,
                "changed_symbols": a.changed_symbols_count,
                "impacted_symbols": a.impacted_symbols_count,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            })

            # Parse report JSON safely
            report_data = {}
            if a.report_json:
                try:
                    report_data = json.loads(a.report_json)
                except Exception:
                    pass

            changed_files = report_data.get("changed_files", [])
            for f in changed_files:
                file_change_counter[f] += 1
                if a.risk_level in ("elevated", "high"):
                    high_risk_files[f] += 1

            for sym in report_data.get("changed_symbols", []):
                sym_id = sym.get("id") or sym.get("name")
                if sym_id:
                    symbol_change_counter[sym_id] += 1

            for imp in report_data.get("impacted_symbols", []):
                imp_id = imp.get("symbol_id") or imp.get("symbol_name")
                if imp_id:
                    symbol_impact_counter[imp_id] += 1

                # Record path hops
                path = imp.get("path_from_change", [])
                if len(path) >= 2:
                    for i in range(len(path) - 1):
                        hop = f"{path[i]} ➔ {path[i+1]}"
                        path_counter[hop] += 1

            for rec in report_data.get("recommended_tests", []):
                test_key = rec.get("test_file", "")
                if rec.get("test_symbol_id"):
                    test_key = f"{test_key}::{rec['test_symbol_id']}"
                if test_key:
                    test_rec_counter[test_key] += 1

        # Format frequently modified modules
        frequently_modified_modules = [
            {
                "file_path": file_path,
                "change_count": count,
                "percentage": round((count / total_analyses) * 100, 1),
            }
            for file_path, count in file_change_counter.most_common(10)
        ]

        # Format frequently impacted components
        frequently_impacted_components = [
            {
                "symbol_id": sym_id,
                "impact_count": count,
                "percentage": round((count / total_analyses) * 100, 1),
            }
            for sym_id, count in symbol_impact_counter.most_common(10)
        ]

        # Format recurring dependency paths
        recurring_paths = [
            {
                "path": hop,
                "frequency": count,
            }
            for hop, count in path_counter.most_common(10)
        ]

        # Format architectural hotspots (files repeatedly in elevated/high risk changes)
        hotspots = [
            {
                "file_path": f,
                "high_risk_occurrences": count,
                "total_changes": file_change_counter[f],
            }
            for f, count in high_risk_files.most_common(10)
        ]

        # Format repeatedly recommended tests
        repeatedly_recommended_tests = [
            {
                "test": test_identifier,
                "recommendation_count": count,
                "percentage": round((count / total_analyses) * 100, 1),
            }
            for test_identifier, count in test_rec_counter.most_common(10)
        ]

        return {
            "repository_id": repository_id,
            "total_analyses": total_analyses,
            "frequently_modified_modules": frequently_modified_modules,
            "frequently_impacted_components": frequently_impacted_components,
            "recurring_paths": recurring_paths,
            "hotspots": hotspots,
            "repeatedly_recommended_tests": repeatedly_recommended_tests,
            "risk_trend": risk_trend,
        }

    def compare_analyses(
        self,
        analysis_id_a: int,
        analysis_id_b: int,
        user_id: int,
    ) -> Dict[str, Any]:
        """
        Performs a deep comparative diff between two historical change analyses.
        Identifies:
        - Changes in blast radius size and depth
        - Newly affected components vs stabilized components
        - Risk score evolution
        - Shifts in recommended tests
        """
        a = (
            self.db.query(Analysis)
            .filter(Analysis.id == analysis_id_a, Analysis.user_id == user_id)
            .first()
        )
        b = (
            self.db.query(Analysis)
            .filter(Analysis.id == analysis_id_b, Analysis.user_id == user_id)
            .first()
        )

        if not a or not b:
            raise ValueError("One or both analysis records not found or access denied")

        rep_a = json.loads(a.report_json) if a.report_json else {}
        rep_b = json.loads(b.report_json) if b.report_json else {}

        syms_a = {s.get("id"): s for s in rep_a.get("changed_symbols", []) if s.get("id")}
        syms_b = {s.get("id"): s for s in rep_b.get("changed_symbols", []) if s.get("id")}

        imp_a = {s.get("symbol_id"): s for s in rep_a.get("impacted_symbols", []) if s.get("symbol_id")}
        imp_b = {s.get("symbol_id"): s for s in rep_b.get("impacted_symbols", []) if s.get("symbol_id")}

        tests_a = {r.get("test_file") for r in rep_a.get("recommended_tests", []) if r.get("test_file")}
        tests_b = {r.get("test_file") for r in rep_b.get("recommended_tests", []) if r.get("test_file")}

        # Delta metrics
        risk_score_delta = round(b.risk_score - a.risk_score, 1)
        impacted_count_delta = len(imp_b) - len(imp_a)

        return {
            "analysis_a": {
                "id": a.id,
                "commit": a.head_commit[:8] if a.head_commit else "",
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "risk_score": a.risk_score,
                "risk_level": a.risk_level,
                "changed_count": len(syms_a),
                "impacted_count": len(imp_a),
            },
            "analysis_b": {
                "id": b.id,
                "commit": b.head_commit[:8] if b.head_commit else "",
                "created_at": b.created_at.isoformat() if b.created_at else None,
                "risk_score": b.risk_score,
                "risk_level": b.risk_level,
                "changed_count": len(syms_b),
                "impacted_count": len(imp_b),
            },
            "risk_score_delta": risk_score_delta,
            "impacted_count_delta": impacted_count_delta,
            "newly_impacted_symbols": sorted(list(set(imp_b.keys()) - set(imp_a.keys()))),
            "resolved_impacted_symbols": sorted(list(set(imp_a.keys()) - set(imp_b.keys()))),
            "common_impacted_symbols": sorted(list(set(imp_a.keys()).intersection(set(imp_b.keys())))),
            "newly_recommended_tests": sorted(list(tests_b - tests_a)),
            "retained_tests": sorted(list(tests_a.intersection(tests_b))),
        }
