"""Tests for Impact Analysis Traversal, Path Provenance & Blast Radius Accuracy.

Validates:
- Valid path provenance from changed root for all impacted symbols
- Strict direct vs transitive depth classification
- Prevention of duplicate nodes in blast radius
- Deterministic cycle termination in circular dependency graphs
- Multi-source shortest path BFS across multiple changed roots
- Verification that no paths or relationships are fabricated
"""
import pytest
from app.scanner.models import (
    ConfidenceLevel,
    DependencyEdge,
    ImpactType,
    RelationType,
    Symbol,
    SymbolType,
)
from app.scanner.graph import DependencyGraphEngine


def build_test_graph():
    """
    Constructs a controlled dependency hierarchy:
    root -> direct_caller_1 -> transitive_1 -> transitive_2
    root -> direct_caller_2
    """
    symbols = [
        Symbol(id="app.core.root", name="root", symbol_type=SymbolType.FUNCTION, file_path="app/core.py", line_start=1, line_end=5),
        Symbol(id="app.service.direct_1", name="direct_1", symbol_type=SymbolType.FUNCTION, file_path="app/service.py", line_start=1, line_end=5),
        Symbol(id="app.service.direct_2", name="direct_2", symbol_type=SymbolType.FUNCTION, file_path="app/service.py", line_start=10, line_end=15),
        Symbol(id="app.api.trans_1", name="trans_1", symbol_type=SymbolType.FUNCTION, file_path="app/api.py", line_start=1, line_end=5),
        Symbol(id="app.web.trans_2", name="trans_2", symbol_type=SymbolType.FUNCTION, file_path="app/web.py", line_start=1, line_end=5),
    ]

    # Caller -> Callee edges:
    # direct_1 calls root
    # direct_2 calls root
    # trans_1 calls direct_1
    # trans_2 calls trans_1
    edges = [
        DependencyEdge(source_id="app.service.direct_1", target_id="app.core.root", relation_type=RelationType.CALLS, confidence=ConfidenceLevel.CONFIRMED, file_path="app/service.py", line_number=3),
        DependencyEdge(source_id="app.service.direct_2", target_id="app.core.root", relation_type=RelationType.CALLS, confidence=ConfidenceLevel.CONFIRMED, file_path="app/service.py", line_number=12),
        DependencyEdge(source_id="app.api.trans_1", target_id="app.service.direct_1", relation_type=RelationType.CALLS, confidence=ConfidenceLevel.CONFIRMED, file_path="app/api.py", line_number=3),
        DependencyEdge(source_id="app.web.trans_2", target_id="app.api.trans_1", relation_type=RelationType.CALLS, confidence=ConfidenceLevel.CONFIRMED, file_path="app/web.py", line_number=3),
    ]

    return DependencyGraphEngine(symbols=symbols, edges=edges)


def test_path_provenance_and_depth_accuracy():
    engine = build_test_graph()

    impacted = engine.find_impacted_symbols(["app.core.root"])

    # 1. Total symbols should be exactly 5
    assert len(impacted) == 5

    # 2. Check no duplicates
    ids = [s.symbol_id for s in impacted]
    assert len(ids) == len(set(ids))

    by_id = {s.symbol_id: s for s in impacted}

    # 3. Check root
    root = by_id["app.core.root"]
    assert root.depth == 0
    assert root.impact_type == ImpactType.DIRECT_CHANGE
    assert root.path_from_change == ["app.core.root"]

    # 4. Check direct callers (depth 1)
    d1 = by_id["app.service.direct_1"]
    assert d1.depth == 1
    assert d1.impact_type == ImpactType.DIRECT_DEPENDENT
    assert d1.path_from_change == ["app.core.root", "app.service.direct_1"]

    d2 = by_id["app.service.direct_2"]
    assert d2.depth == 1
    assert d2.impact_type == ImpactType.DIRECT_DEPENDENT
    assert d2.path_from_change == ["app.core.root", "app.service.direct_2"]

    # 5. Check transitive callers (depth 2 and 3)
    t1 = by_id["app.api.trans_1"]
    assert t1.depth == 2
    assert t1.impact_type == ImpactType.TRANSITIVE_DEPENDENT
    assert t1.path_from_change == ["app.core.root", "app.service.direct_1", "app.api.trans_1"]

    t2 = by_id["app.web.trans_2"]
    assert t2.depth == 3
    assert t2.impact_type == ImpactType.TRANSITIVE_DEPENDENT
    assert t2.path_from_change == ["app.core.root", "app.service.direct_1", "app.api.trans_1", "app.web.trans_2"]

    # 6. Verify path edges: Every hop in path_from_change must be a valid reverse dependency edge
    for sym in impacted:
        path = sym.path_from_change
        for i in range(len(path) - 1):
            src, dst = path[i], path[i + 1]
            # dst depends on src, meaning in reverse graph src -> dst
            assert engine.reverse_graph.has_edge(src, dst), f"Fabricated edge detected between {src} and {dst}!"


def test_multi_source_shortest_path_bfs():
    """
    Verify multi-source BFS:
    Root A -> Node X via 3 hops: Root A -> M1 -> M2 -> Node X
    Root B -> Node X via 1 hop: Root B -> Node X
    If both Root A and Root B are modified, Node X MUST be recorded at depth 1 via Root B,
    not overwritten or delayed by Root A.
    """
    symbols = [
        Symbol(id="root_a", name="root_a", symbol_type=SymbolType.FUNCTION, file_path="a.py", line_start=1, line_end=2),
        Symbol(id="root_b", name="root_b", symbol_type=SymbolType.FUNCTION, file_path="b.py", line_start=1, line_end=2),
        Symbol(id="m1", name="m1", symbol_type=SymbolType.FUNCTION, file_path="m1.py", line_start=1, line_end=2),
        Symbol(id="m2", name="m2", symbol_type=SymbolType.FUNCTION, file_path="m2.py", line_start=1, line_end=2),
        Symbol(id="target_x", name="target_x", symbol_type=SymbolType.FUNCTION, file_path="x.py", line_start=1, line_end=2),
    ]

    edges = [
        # Call edges: m1 calls root_a, m2 calls m1, target_x calls m2
        DependencyEdge(source_id="m1", target_id="root_a", relation_type=RelationType.CALLS, confidence=ConfidenceLevel.CONFIRMED, file_path="m1.py", line_number=1),
        DependencyEdge(source_id="m2", target_id="m1", relation_type=RelationType.CALLS, confidence=ConfidenceLevel.CONFIRMED, file_path="m2.py", line_number=1),
        DependencyEdge(source_id="target_x", target_id="m2", relation_type=RelationType.CALLS, confidence=ConfidenceLevel.CONFIRMED, file_path="x.py", line_number=1),
        # Direct call edge: target_x calls root_b
        DependencyEdge(source_id="target_x", target_id="root_b", relation_type=RelationType.CALLS, confidence=ConfidenceLevel.CONFIRMED, file_path="x.py", line_number=2),
    ]

    engine = DependencyGraphEngine(symbols=symbols, edges=edges)

    # When both root_a and root_b are changed
    impacted = engine.find_impacted_symbols(["root_a", "root_b"])

    by_id = {s.symbol_id: s for s in impacted}
    assert "target_x" in by_id
    # target_x should have depth 1 via root_b (shortest path), not depth 3 via root_a
    assert by_id["target_x"].depth == 1
    assert by_id["target_x"].path_from_change == ["root_b", "target_x"]
    assert by_id["target_x"].impact_type == ImpactType.DIRECT_DEPENDENT


def test_cycle_termination_in_complex_cyclic_mesh():
    """Verify clean cycle termination in an interconnected circular graph."""
    symbols = [
        Symbol(id=f"node_{i}", name=f"node_{i}", symbol_type=SymbolType.FUNCTION, file_path=f"mod_{i}.py", line_start=1, line_end=5)
        for i in range(6)
    ]

    edges = [
        # Ring 0 -> 1 -> 2 -> 0
        DependencyEdge(source_id="node_1", target_id="node_0", relation_type=RelationType.CALLS, confidence=ConfidenceLevel.CONFIRMED, file_path="mod_1.py", line_number=1),
        DependencyEdge(source_id="node_2", target_id="node_1", relation_type=RelationType.CALLS, confidence=ConfidenceLevel.CONFIRMED, file_path="mod_2.py", line_number=1),
        DependencyEdge(source_id="node_0", target_id="node_2", relation_type=RelationType.CALLS, confidence=ConfidenceLevel.CONFIRMED, file_path="mod_0.py", line_number=1),
        # Cross chords
        DependencyEdge(source_id="node_3", target_id="node_1", relation_type=RelationType.CALLS, confidence=ConfidenceLevel.CONFIRMED, file_path="mod_3.py", line_number=1),
        DependencyEdge(source_id="node_4", target_id="node_3", relation_type=RelationType.CALLS, confidence=ConfidenceLevel.CONFIRMED, file_path="mod_4.py", line_number=1),
        DependencyEdge(source_id="node_5", target_id="node_4", relation_type=RelationType.CALLS, confidence=ConfidenceLevel.CONFIRMED, file_path="mod_5.py", line_number=1),
        DependencyEdge(source_id="node_2", target_id="node_5", relation_type=RelationType.CALLS, confidence=ConfidenceLevel.CONFIRMED, file_path="mod_2.py", line_number=2),
    ]

    engine = DependencyGraphEngine(symbols=symbols, edges=edges)
    impacted = engine.find_impacted_symbols(["node_0"])

    # Traversal terminates and discovers all connected nodes without re-visiting or crashing
    assert len(impacted) == 6
    visited_ids = [s.symbol_id for s in impacted]
    assert len(visited_ids) == len(set(visited_ids))
