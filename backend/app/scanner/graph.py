from collections import deque
from typing import Dict, List, Set, Tuple
import networkx as nx

from .models import (
    ConfidenceLevel,
    DependencyEdge,
    ImpactType,
    ImpactedSymbol,
    RelationType,
    Symbol,
    SymbolType,
)


class DependencyGraphEngine:
    """
    Constructs a NetworkX directed graph from symbols and edges,
    and performs reverse traversal to find all upstream callers and dependents
    when a symbol is changed.
    """

    def __init__(self, symbols: List[Symbol], edges: List[DependencyEdge]):
        self.symbols_by_id: Dict[str, Symbol] = {s.id: s for s in symbols}
        self.edges = edges

        # Direct graph: source -> target (e.g. Caller -> Callee)
        self.graph = nx.DiGraph()

        # Populate graph nodes
        for s in symbols:
            self.graph.add_node(
                s.id,
                name=s.name,
                symbol_type=s.symbol_type.value,
                file_path=s.file_path,
                line_start=s.line_start,
                line_end=s.line_end,
                docstring=s.docstring,
            )

        # Populate graph edges
        for e in edges:
            self.graph.add_edge(
                e.source_id,
                e.target_id,
                relation_type=e.relation_type.value,
                confidence=e.confidence.value,
                file_path=e.file_path,
                line_number=e.line_number,
            )

        # Reverse graph: target -> source (e.g. Callee -> Caller)
        # Traversal on the reverse graph traces the blast radius!
        self.reverse_graph = self.graph.reverse(copy=False)

    def find_impacted_symbols(self, changed_symbol_ids: List[str]) -> List[ImpactedSymbol]:
        """
        Given a list of modified symbol IDs, traverses reverse dependencies
        to discover all direct and indirect dependents with exact path provenance.
        """
        impacted: List[ImpactedSymbol] = []
        visited: Set[str] = set()

        for changed_id in changed_symbol_ids:
            # 1. Include the modified symbol itself at depth 0
            if changed_id in self.symbols_by_id and changed_id not in visited:
                sym = self.symbols_by_id[changed_id]
                impacted.append(
                    ImpactedSymbol(
                        symbol_id=sym.id,
                        symbol_name=sym.name,
                        symbol_type=sym.symbol_type,
                        file_path=sym.file_path,
                        line_start=sym.line_start,
                        line_end=sym.line_end,
                        impact_type=ImpactType.DIRECT_CHANGE,
                        depth=0,
                        path_from_change=[sym.id],
                    )
                )
                visited.add(changed_id)

            # 2. BFS traversal on reverse graph (find all callers / importers)
            # Queue stores (current_symbol_id, current_depth, path_so_far)
            queue: deque = deque([(changed_id, 0, [changed_id])])

            while queue:
                curr_id, depth, path = queue.popleft()

                # Find all nodes that depend on curr_id (predecessors in original graph)
                # In reverse_graph, these are successors!
                if curr_id in self.reverse_graph:
                    for dependent_id in self.reverse_graph.neighbors(curr_id):
                        if dependent_id not in visited:
                            visited.add(dependent_id)
                            new_depth = depth + 1
                            new_path = path + [dependent_id]

                            sym_info = self.symbols_by_id.get(dependent_id)
                            if sym_info:
                                imp_type = (
                                    ImpactType.DIRECT_DEPENDENT
                                    if new_depth == 1
                                    else ImpactType.TRANSITIVE_DEPENDENT
                                )
                                impacted.append(
                                    ImpactedSymbol(
                                        symbol_id=sym_info.id,
                                        symbol_name=sym_info.name,
                                        symbol_type=sym_info.symbol_type,
                                        file_path=sym_info.file_path,
                                        line_start=sym_info.line_start,
                                        line_end=sym_info.line_end,
                                        impact_type=imp_type,
                                        depth=new_depth,
                                        path_from_change=new_path,
                                    )
                                )
                                # Queue up to depth 5 to avoid infinite loops in cyclic dependencies
                                if new_depth < 5:
                                    queue.append((dependent_id, new_depth, new_path))

        # Sort by depth ascending so direct changes come first, then direct callers
        impacted.sort(key=lambda x: (x.depth, x.file_path, x.symbol_name))
        return impacted

    def compute_risk(self, impacted_symbols: List[ImpactedSymbol]) -> Tuple[str, float]:
        """
        Calculates an explainable risk level ('low', 'medium', 'elevated', 'high')
        and numerical score (0.0 - 100.0) based on blast radius size and depth.
        """
        if not impacted_symbols:
            return "low", 0.0

        direct_changes = [s for s in impacted_symbols if s.impact_type == ImpactType.DIRECT_CHANGE]
        direct_callers = [s for s in impacted_symbols if s.impact_type == ImpactType.DIRECT_DEPENDENT]
        transitive_callers = [s for s in impacted_symbols if s.impact_type == ImpactType.TRANSITIVE_DEPENDENT]

        # Count affected files
        unique_files = {s.file_path for s in impacted_symbols}

        # Base score components
        score = (
            len(direct_changes) * 10.0
            + len(direct_callers) * 8.0
            + len(transitive_callers) * 4.0
            + (len(unique_files) - 1) * 12.0
        )

        score = min(100.0, max(5.0, score))

        if score < 25.0:
            level = "low"
        elif score < 50.0:
            level = "medium"
        elif score < 75.0:
            level = "elevated"
        else:
            level = "high"

        return level, round(score, 1)
