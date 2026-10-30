import ast
import builtins
import os
from typing import Dict, List, Optional, Set, Tuple

from .models import (
    ConfidenceLevel,
    DependencyEdge,
    RelationType,
    Symbol,
    SymbolType,
)

# Standard library built-ins to ignore from dependency graph resolution
BUILTIN_NAMES = set(dir(builtins)) | {
    "__import__",
    "print",
    "len",
    "range",
    "str",
    "int",
    "float",
    "bool",
    "list",
    "dict",
    "set",
    "tuple",
    "enumerate",
    "zip",
    "isinstance",
    "issubclass",
    "super",
    "getattr",
    "setattr",
    "hasattr",
    "min",
    "max",
    "sum",
    "any",
    "all",
    "open",
    "type",
    "id",
}

DYNAMIC_CALL_NAMES = {
    "getattr",
    "setattr",
    "hasattr",
    "eval",
    "exec",
    "__import__",
    "globals",
    "locals",
}


def module_name_from_file_path(rel_path: str) -> str:
    """Convert relative file path (e.g., 'auth/service.py' or 'auth/__init__.py') to module name."""
    clean = rel_path.replace("\\", "/").strip("/")
    if clean.endswith(".py"):
        clean = clean[:-3]
    if clean.endswith("/__init__"):
        clean = clean[:-9]
    return clean.replace("/", ".")


def _get_start_line(node: ast.AST) -> int:
    """Returns the starting line number including leading decorators."""
    decorators = getattr(node, "decorator_list", [])
    if decorators:
        return min([d.lineno for d in decorators] + [node.lineno])
    return getattr(node, "lineno", 1)


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
        self.seen_edges: Set[Tuple[str, str, str]] = set()
        self.unresolved_calls_count: int = 0

        # Local alias map: local_name -> imported_target_id
        # e.g., 'validate_token' -> 'auth.service.validate_token'
        # e.g., 'AuthService' -> 'auth.service.AuthService'
        # e.g., 's' -> 'auth.service'
        self.import_map: Dict[str, str] = {}

    def parse(self) -> Tuple[List[Symbol], List[DependencyEdge]]:
        try:
            tree = ast.parse(self.source_code, filename=self.rel_path)
        except (SyntaxError, ValueError, TypeError):
            # If a file has syntax errors, null bytes, or malformed AST, return empty lists gracefully
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

        # 2. Extract imports (scans all compound statements: try, if, etc.)
        self._extract_imports(tree)

        # 3. Extract classes and functions (including nested functions)
        self._extract_definitions(tree, parent_symbol_id=self.module_name)

        return self.symbols, self.edges

    def _extract_imports(self, tree: ast.AST):
        """Scans the AST for all import statements, including those inside compound blocks."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    local_alias = alias.asname or alias.name
                    target = alias.name
                    self.import_map[local_alias] = target
                    self._add_edge(
                        source_id=self.module_name,
                        target_id=target,
                        relation_type=RelationType.IMPORTS,
                        confidence=ConfidenceLevel.CONFIRMED,
                        line_number=node.lineno,
                    )
            elif isinstance(node, ast.ImportFrom):
                base_mod = ""
                if node.level and node.level > 0:
                    # Relative import resolution
                    parts = self.module_name.split(".")
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
                    self._add_edge(
                        source_id=self.module_name,
                        target_id=target,
                        relation_type=RelationType.IMPORTS,
                        confidence=ConfidenceLevel.CONFIRMED,
                        line_number=node.lineno,
                    )

    def _add_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        confidence: ConfidenceLevel,
        line_number: int,
    ):
        """Adds a dependency edge preventing duplicate source->target edges."""
        key = (source_id, target_id, relation_type.value)
        if key not in self.seen_edges:
            self.seen_edges.add(key)
            self.edges.append(
                DependencyEdge(
                    source_id=source_id,
                    target_id=target_id,
                    relation_type=relation_type,
                    confidence=confidence,
                    file_path=self.rel_path,
                    line_number=line_number,
                )
            )

    def _extract_definitions(self, node: ast.AST, parent_symbol_id: str, enclosing_class_id: Optional[str] = None):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                class_id = f"{parent_symbol_id}.{child.name}"
                doc = ast.get_docstring(child)
                class_symbol = Symbol(
                    id=class_id,
                    name=child.name,
                    symbol_type=SymbolType.CLASS,
                    file_path=self.rel_path,
                    line_start=_get_start_line(child),
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
                        self._add_edge(
                            source_id=class_id,
                            target_id=target_id,
                            relation_type=RelationType.INHERITS,
                            confidence=ConfidenceLevel.CONFIRMED if base_name in self.import_map else ConfidenceLevel.INFERRED,
                            line_number=child.lineno,
                        )

                # Process methods and nested definitions within the class
                self._extract_definitions(child, parent_symbol_id=class_id, enclosing_class_id=class_id)

            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                is_method = enclosing_class_id is not None
                func_id = f"{parent_symbol_id}.{child.name}"
                doc = ast.get_docstring(child)
                func_symbol = Symbol(
                    id=func_id,
                    name=child.name,
                    symbol_type=SymbolType.METHOD if is_method else SymbolType.FUNCTION,
                    file_path=self.rel_path,
                    line_start=_get_start_line(child),
                    line_end=getattr(child, "end_lineno", child.lineno),
                    docstring=doc,
                    parent_id=parent_symbol_id,
                )
                self.symbols.append(func_symbol)

                # Extract calls inside this function/method
                self._extract_calls(child, caller_id=func_id, enclosing_class_id=enclosing_class_id)

                # Extract nested functions inside this function
                self._extract_definitions(child, parent_symbol_id=func_id, enclosing_class_id=enclosing_class_id)

    def _extract_calls(self, scope_node: ast.AST, caller_id: str, enclosing_class_id: Optional[str] = None):
        # 1. Track local variable instantiations in this scope: var_name -> class_id
        local_instances: Dict[str, str] = {}
        for child in ast.walk(scope_node):
            if isinstance(child, ast.Assign):
                if isinstance(child.value, ast.Call):
                    callee_name = self._resolve_name_node(child.value.func)
                    if callee_name:
                        resolved_cls = self._resolve_target(callee_name, enclosing_class_id)[0]
                        for target in child.targets:
                            if isinstance(target, ast.Name):
                                local_instances[target.id] = resolved_cls

        # 2. Extract calls
        for node in ast.walk(scope_node):
            if isinstance(node, ast.Call):
                call_target_name = self._resolve_name_node(node.func)
                if not call_target_name:
                    # Dynamic invocation like (func or other)()
                    self.unresolved_calls_count += 1
                    continue

                # Check if it is a dynamic call keyword
                if call_target_name in DYNAMIC_CALL_NAMES:
                    self.unresolved_calls_count += 1
                    continue

                # Check if it is a Python builtin without a matching local symbol
                if call_target_name in BUILTIN_NAMES:
                    # Builtin functions are primitives, not repository dependency edges
                    continue

                target_id, confidence = self._resolve_call(
                    call_target_name=call_target_name,
                    enclosing_class_id=enclosing_class_id,
                    local_instances=local_instances,
                )

                if target_id is None:
                    self.unresolved_calls_count += 1
                    continue

                self._add_edge(
                    source_id=caller_id,
                    target_id=target_id,
                    relation_type=RelationType.CALLS,
                    confidence=confidence,
                    line_number=node.lineno,
                )

    def _resolve_target(self, name: str, enclosing_class_id: Optional[str]) -> Tuple[str, ConfidenceLevel]:
        """Resolves a class or function name to its target ID."""
        if name in self.import_map:
            return self.import_map[name], ConfidenceLevel.CONFIRMED

        # Check aliased prefix
        if "." in name:
            head, rest = name.split(".", 1)
            if head in self.import_map:
                return f"{self.import_map[head]}.{rest}", ConfidenceLevel.CONFIRMED

        if enclosing_class_id and (name.startswith("self.") or name.startswith("cls.")):
            rest = name.split(".", 1)[1]
            return f"{enclosing_class_id}.{rest}", ConfidenceLevel.CONFIRMED

        # Fallback to current module
        return f"{self.module_name}.{name}", ConfidenceLevel.INFERRED

    def _resolve_call(
        self,
        call_target_name: str,
        enclosing_class_id: Optional[str],
        local_instances: Dict[str, str],
    ) -> Tuple[Optional[str], ConfidenceLevel]:
        """
        Resolves a call target string into a fully qualified symbol ID.
        Distinguishes CONFIRMED, INFERRED, and UNRESOLVED.
        """
        # Exact match in import map
        if call_target_name in self.import_map:
            return self.import_map[call_target_name], ConfidenceLevel.CONFIRMED

        # Intra-class method calls via self.xxx or cls.xxx
        if enclosing_class_id and (call_target_name.startswith("self.") or call_target_name.startswith("cls.")):
            method_name = call_target_name.split(".", 1)[1]
            return f"{enclosing_class_id}.{method_name}", ConfidenceLevel.CONFIRMED

        # Calls on tracked local instances: e.g. service.validate_token()
        if "." in call_target_name:
            receiver, attr = call_target_name.split(".", 1)
            if receiver in local_instances:
                inferred_class = local_instances[receiver]
                return f"{inferred_class}.{attr}", ConfidenceLevel.INFERRED

            # Calls via imported module alias: e.g. s.validate_token()
            if receiver in self.import_map:
                imported_mod = self.import_map[receiver]
                return f"{imported_mod}.{attr}", ConfidenceLevel.CONFIRMED

            # Unknown object attribute call (e.g. token.endswith, data.get)
            # Not an imported symbol, not a known local instance
            return None, ConfidenceLevel.UNRESOLVED

        # Direct function call within current module (e.g. hash_password())
        return f"{self.module_name}.{call_target_name}", ConfidenceLevel.CONFIRMED

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
