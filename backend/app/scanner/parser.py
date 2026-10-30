import ast
import os
from typing import Dict, List, Optional, Set, Tuple

from .models import (
    ConfidenceLevel,
    DependencyEdge,
    RelationType,
    Symbol,
    SymbolType,
)


def module_name_from_file_path(rel_path: str) -> str:
    """Convert relative file path (e.g., 'auth/service.py' or 'auth/__init__.py') to module name."""
    clean = rel_path.replace("\\", "/").strip("/")
    if clean.endswith(".py"):
        clean = clean[:-3]
    if clean.endswith("/__init__"):
        clean = clean[:-9]
    return clean.replace("/", ".")


class PythonASTParser:
    """
    Statically inspects Python code using the standard library AST parser.
    Strictly safe: never imports or executes untrusted code.
    """

    def __init__(self, rel_path: str, source_code: str):
        self.rel_path = rel_path.replace("\\", "/")
        self.source_code = source_code
        self.module_name = module_name_from_file_path(self.rel_path)
        self.symbols: List[Symbol] = []
        self.edges: List[DependencyEdge] = []

        # Local alias map: local_name -> imported_target_id
        # e.g., 'validate_token' -> 'auth.service.validate_token'
        # e.g., 'AuthService' -> 'auth.service.AuthService'
        # e.g., 'svc' -> 'auth.service'
        self.import_map: Dict[str, str] = {}

    def parse(self) -> Tuple[List[Symbol], List[DependencyEdge]]:
        try:
            tree = ast.parse(self.source_code, filename=self.rel_path)
        except SyntaxError:
            # If a file has syntax errors, return empty list gracefully without crashing
            return self.symbols, self.edges

        # 1. Module level symbol
        lines = self.source_code.splitlines()
        total_lines = len(lines) if lines else 1
        module_doc = ast.get_docstring(tree)

        mod_symbol = Symbol(
            id=self.module_name,
            name=self.module_name.split(".")[-1],
            symbol_type=SymbolType.MODULE,
            file_path=self.rel_path,
            line_start=1,
            line_end=total_lines,
            docstring=module_doc,
            parent_id=None,
        )
        self.symbols.append(mod_symbol)

        # 2. Extract imports
        self._extract_imports(tree)

        # 3. Extract classes and functions
        self._extract_definitions(tree, parent_symbol_id=self.module_name)

        return self.symbols, self.edges

    def _extract_imports(self, tree: ast.AST):
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    local_alias = alias.asname or alias.name
                    target = alias.name
                    self.import_map[local_alias] = target
                    self.edges.append(
                        DependencyEdge(
                            source_id=self.module_name,
                            target_id=target,
                            relation_type=RelationType.IMPORTS,
                            confidence=ConfidenceLevel.CONFIRMED,
                            file_path=self.rel_path,
                            line_number=node.lineno,
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                base_mod = ""
                if node.level > 0:
                    # Relative import
                    parts = self.module_name.split(".")
                    # level 1 is current package, level 2 is parent
                    slice_len = len(parts) - (node.level - 1)
                    if slice_len > 0:
                        base_mod = ".".join(parts[: max(0, slice_len - 1)])
                    if node.module:
                        base_mod = f"{base_mod}.{node.module}" if base_mod else node.module
                else:
                    base_mod = node.module or ""

                for alias in node.names:
                    local_alias = alias.asname or alias.name
                    target = f"{base_mod}.{alias.name}" if base_mod else alias.name
                    self.import_map[local_alias] = target
                    self.edges.append(
                        DependencyEdge(
                            source_id=self.module_name,
                            target_id=target,
                            relation_type=RelationType.IMPORTS,
                            confidence=ConfidenceLevel.CONFIRMED,
                            file_path=self.rel_path,
                            line_number=node.lineno,
                        )
                    )

    def _extract_definitions(self, node: ast.AST, parent_symbol_id: str):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                class_id = f"{parent_symbol_id}.{child.name}"
                doc = ast.get_docstring(child)
                class_symbol = Symbol(
                    id=class_id,
                    name=child.name,
                    symbol_type=SymbolType.CLASS,
                    file_path=self.rel_path,
                    line_start=child.lineno,
                    line_end=getattr(child, "end_lineno", child.lineno),
                    docstring=doc,
                    parent_id=parent_symbol_id,
                )
                self.symbols.append(class_symbol)

                # Inheritance edges
                for base in child.bases:
                    base_name = self._resolve_name_node(base)
                    if base_name:
                        target_id = self.import_map.get(base_name, base_name)
                        self.edges.append(
                            DependencyEdge(
                                source_id=class_id,
                                target_id=target_id,
                                relation_type=RelationType.INHERITS,
                                confidence=ConfidenceLevel.CONFIRMED if base_name in self.import_map else ConfidenceLevel.INFERRED,
                                file_path=self.rel_path,
                                line_number=child.lineno,
                            )
                        )

                # Process methods within the class
                for item in child.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_id = f"{class_id}.{item.name}"
                        method_doc = ast.get_docstring(item)
                        method_symbol = Symbol(
                            id=method_id,
                            name=item.name,
                            symbol_type=SymbolType.METHOD,
                            file_path=self.rel_path,
                            line_start=item.lineno,
                            line_end=getattr(item, "end_lineno", item.lineno),
                            docstring=method_doc,
                            parent_id=class_id,
                        )
                        self.symbols.append(method_symbol)
                        # Extract calls inside this method
                        self._extract_calls(item, caller_id=method_id)

            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_id = f"{parent_symbol_id}.{child.name}"
                doc = ast.get_docstring(child)
                func_symbol = Symbol(
                    id=func_id,
                    name=child.name,
                    symbol_type=SymbolType.FUNCTION,
                    file_path=self.rel_path,
                    line_start=child.lineno,
                    line_end=getattr(child, "end_lineno", child.lineno),
                    docstring=doc,
                    parent_id=parent_symbol_id,
                )
                self.symbols.append(func_symbol)

                # Extract calls inside this function
                self._extract_calls(child, caller_id=func_id)

    def _extract_calls(self, scope_node: ast.AST, caller_id: str):
        for node in ast.walk(scope_node):
            if isinstance(node, ast.Call):
                call_target_name = self._resolve_name_node(node.func)
                if not call_target_name:
                    continue

                # Check if name is in import map or local scope
                target_id = self.import_map.get(call_target_name)
                confidence = ConfidenceLevel.CONFIRMED if target_id else ConfidenceLevel.INFERRED

                if not target_id:
                    # If called directly like 'helper_func()' in same module
                    target_id = f"{self.module_name}.{call_target_name}"

                self.edges.append(
                    DependencyEdge(
                        source_id=caller_id,
                        target_id=target_id,
                        relation_type=RelationType.CALLS,
                        confidence=confidence,
                        file_path=self.rel_path,
                        line_number=node.lineno,
                    )
                )

    def _resolve_name_node(self, node: ast.AST) -> Optional[str]:
        """Resolves ast.Name, ast.Attribute (e.g. self.method, module.func) to dotted string."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            val = self._resolve_name_node(node.value)
            if val:
                return f"{val}.{node.attr}"
            return node.attr
        return None
