from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class SymbolType(str, Enum):
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"


class RelationType(str, Enum):
    IMPORTS = "imports"
    CALLS = "calls"
    INHERITS = "inherits"
    INSTANTIATES = "instantiates"


class ConfidenceLevel(str, Enum):
    CONFIRMED = "confirmed"  # Direct AST resolution (e.g. imports, direct class inheritance)
    INFERRED = "inferred"    # Heuristic / dynamic call resolution


class Symbol(BaseModel):
    id: str  # Fully qualified name: e.g. "auth.service.AuthService.login"
    name: str  # Local name: e.g. "login"
    symbol_type: SymbolType
    file_path: str  # Relative path within repo: e.g. "auth/service.py"
    line_start: int
    line_end: int
    docstring: Optional[str] = None
    parent_id: Optional[str] = None


class DependencyEdge(BaseModel):
    source_id: str  # The calling or importing symbol
    target_id: str  # The symbol being called or imported
    relation_type: RelationType
    confidence: ConfidenceLevel
    file_path: str
    line_number: int


class ScanSummary(BaseModel):
    repo_path: str
    commit_sha: Optional[str] = None
    file_count: int
    symbol_count: int
    edge_count: int
    symbols: List[Symbol]
    edges: List[DependencyEdge]
    duration_ms: float


class ImpactType(str, Enum):
    DIRECT_CHANGE = "direct_change"
    DIRECT_DEPENDENT = "direct_dependent"
    TRANSITIVE_DEPENDENT = "transitive_dependent"


class ImpactedSymbol(BaseModel):
    symbol_id: str
    symbol_name: str
    symbol_type: SymbolType
    file_path: str
    line_start: int
    line_end: int
    impact_type: ImpactType
    depth: int  # 0 for direct change, 1 for direct callers, 2+ for transitive callers
    path_from_change: List[str]  # e.g. ["auth.service.login", "checkout.payment.process_payment"]


class TestRecommendation(BaseModel):
    test_file: str
    test_symbol_id: Optional[str] = None
    target_symbol_id: str
    reason: str
    priority: str = "high"  # "high", "medium"


class ImpactAnalysisReport(BaseModel):
    repo_path: str
    base_commit: str
    head_commit: str
    changed_files: List[str]
    changed_symbols: List[Symbol]
    impacted_symbols: List[ImpactedSymbol]
    graph_nodes_count: int
    graph_edges_count: int
    recommended_tests: List[TestRecommendation]
    risk_level: str  # "low", "medium", "elevated", "high"
    risk_score: float  # 0.0 to 100.0
    summary_text: str
    created_at: str
