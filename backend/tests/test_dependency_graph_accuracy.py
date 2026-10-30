"""Tests for Dependency Graph Accuracy, Resolution & Confidence Level Distinctions.

Validates:
- Direct function calls
- Indirect/transitive calls
- Imported functions
- Aliased imports (module and function aliases)
- Class methods (self.method(), cls.method(), class inheritance)
- Local variable instance tracking (var = Class(); var.method())
- Nested functions (def outer(): def inner(): ...)
- Recursive calls (fib calling fib)
- Duplicate edge elimination
- Circular dependencies (A -> B -> C -> A)
- Unresolved dynamic calls (getattr, eval)
- Builtin function filtering (len, str, etc.)
- Confirmed vs Inferred vs Unresolved confidence levels
"""
import ast
import pytest
from app.scanner.models import ConfidenceLevel, RelationType, SymbolType
from app.scanner.parser import PythonASTParser
from app.scanner.graph import DependencyGraphEngine


def test_direct_and_indirect_calls():
    code = """
def callee():
    return 42

def caller():
    return callee()

def top_caller():
    return caller()
"""
    parser = PythonASTParser("service/calc.py", code)
    symbols, edges = parser.parse()

    call_edges = [e for e in edges if e.relation_type == RelationType.CALLS]
    # Check caller -> callee
    assert any(
        e.source_id == "service.calc.caller"
        and e.target_id == "service.calc.callee"
        and e.confidence == ConfidenceLevel.CONFIRMED
        for e in call_edges
    )
    # Check top_caller -> caller
    assert any(
        e.source_id == "service.calc.top_caller"
        and e.target_id == "service.calc.caller"
        and e.confidence == ConfidenceLevel.CONFIRMED
        for e in call_edges
    )


def test_imported_functions_and_aliases():
    code = """
import auth.crypto as crypt
from auth.service import validate_token as val_tok
from math import sqrt as square_root

def authenticate_user(token: str):
    is_valid = val_tok(token)
    sig = crypt.sign_payload(token)
    score = square_root(16)
    return is_valid
"""
    parser = PythonASTParser("api/gateway.py", code)
    symbols, edges = parser.parse()

    call_edges = [e for e in edges if e.relation_type == RelationType.CALLS]
    
    # 1. Direct function alias: val_tok -> auth.service.validate_token
    val_edge = next((e for e in call_edges if "val_tok" in e.target_id or "validate_token" in e.target_id), None)
    assert val_edge is not None
    assert val_edge.target_id == "auth.service.validate_token"
    assert val_edge.confidence == ConfidenceLevel.CONFIRMED

    # 2. Dotted module alias: crypt.sign_payload -> auth.crypto.sign_payload
    crypt_edge = next((e for e in call_edges if "sign_payload" in e.target_id), None)
    assert crypt_edge is not None
    assert crypt_edge.target_id == "auth.crypto.sign_payload"
    assert crypt_edge.confidence == ConfidenceLevel.CONFIRMED

    # 3. Standard library import alias: square_root -> math.sqrt
    math_edge = next((e for e in call_edges if "sqrt" in e.target_id), None)
    assert math_edge is not None
    assert math_edge.target_id == "math.sqrt"
    assert math_edge.confidence == ConfidenceLevel.CONFIRMED


def test_class_methods_and_self_calls():
    code = """
from core.base import BaseService

class AuthService(BaseService):
    def __init__(self, key: str):
        self.key = key

    def check_header(self, header: str) -> bool:
        return bool(header)

    def validate_session(self, header: str) -> bool:
        return self.check_header(header)

    @classmethod
    def factory(cls, header: str):
        return cls("auto_key")
"""
    parser = PythonASTParser("auth/service.py", code)
    symbols, edges = parser.parse()

    # 1. Check inheritance
    inherit_edges = [e for e in edges if e.relation_type == RelationType.INHERITS]
    assert len(inherit_edges) == 1
    assert inherit_edges[0].source_id == "auth.service.AuthService"
    assert inherit_edges[0].target_id == "core.base.BaseService"
    assert inherit_edges[0].confidence == ConfidenceLevel.CONFIRMED

    # 2. Check self.check_header inside validate_session
    call_edges = [e for e in edges if e.relation_type == RelationType.CALLS]
    self_call = next((e for e in call_edges if e.source_id == "auth.service.AuthService.validate_session"), None)
    assert self_call is not None
    assert self_call.target_id == "auth.service.AuthService.check_header"
    assert self_call.confidence == ConfidenceLevel.CONFIRMED


def test_local_variable_instance_type_inference():
    code = """
from auth.service import AuthService

def process_checkout(user_token: str):
    auth = AuthService("secret_123")
    is_ok = auth.validate_token(user_token)
    return is_ok
"""
    parser = PythonASTParser("checkout/payment.py", code)
    symbols, edges = parser.parse()

    call_edges = [e for e in edges if e.relation_type == RelationType.CALLS]
    # Check that auth.validate_token() resolves to auth.service.AuthService.validate_token with INFERRED
    inferred_edge = next((e for e in call_edges if e.target_id == "auth.service.AuthService.validate_token"), None)
    assert inferred_edge is not None
    assert inferred_edge.source_id == "checkout.payment.process_checkout"
    assert inferred_edge.confidence == ConfidenceLevel.INFERRED


def test_nested_functions_extraction():
    code = """
def outer_worker(task_id: str):
    multiplier = 2
    
    def inner_step(x: int) -> int:
        return x * multiplier
        
    return inner_step(10)
"""
    parser = PythonASTParser("worker/pipeline.py", code)
    symbols, edges = parser.parse()

    sym_ids = {s.id for s in symbols}
    assert "worker.pipeline.outer_worker" in sym_ids
    assert "worker.pipeline.outer_worker.inner_step" in sym_ids

    inner_sym = next(s for s in symbols if s.id == "worker.pipeline.outer_worker.inner_step")
    assert inner_sym.parent_id == "worker.pipeline.outer_worker"
    assert inner_sym.symbol_type == SymbolType.FUNCTION


def test_recursive_calls_and_duplicate_edge_elimination():
    code = """
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
"""
    parser = PythonASTParser("math/fib.py", code)
    symbols, edges = parser.parse()

    call_edges = [e for e in edges if e.relation_type == RelationType.CALLS]
    # Despite 2 recursive calls in code, only 1 unique caller->callee edge should exist
    assert len(call_edges) == 1
    assert call_edges[0].source_id == "math.fib.fibonacci"
    assert call_edges[0].target_id == "math.fib.fibonacci"


def test_builtins_and_dynamic_calls_filtering():
    code = """
def process_data(items: list, dynamic_name: str, target_obj: object):
    count = len(items)
    txt = str(count)
    mapped = dict(zip(items, items))
    
    # Dynamic calls that cannot be statically resolved:
    method = getattr(target_obj, dynamic_name)
    eval("1 + 1")
    
    # Attribute calls on untracked primitive or local:
    items.sort()
    txt.upper()
"""
    parser = PythonASTParser("util/helpers.py", code)
    symbols, edges = parser.parse()

    # None of len, str, dict, zip, getattr, eval should be emitted as repo dependency edges
    call_edges = [e for e in edges if e.relation_type == RelationType.CALLS]
    for edge in call_edges:
        target = edge.target_id
        assert not target.endswith(".len")
        assert not target.endswith(".str")
        assert not target.endswith(".dict")
        assert not target.endswith(".zip")
        assert not target.endswith(".getattr")
        assert not target.endswith(".eval")

    # Unresolved dynamic calls counter should capture getattr and eval
    assert parser.unresolved_calls_count >= 2


def test_circular_dependency_graph_termination():
    """Verify that graph traversal cleanly terminates when cycles exist."""
    from app.scanner.models import Symbol, DependencyEdge, RelationType, ConfidenceLevel

    sym_a = Symbol(id="pkg.a.func_a", name="func_a", symbol_type=SymbolType.FUNCTION, file_path="pkg/a.py", line_start=1, line_end=5)
    sym_b = Symbol(id="pkg.b.func_b", name="func_b", symbol_type=SymbolType.FUNCTION, file_path="pkg/b.py", line_start=1, line_end=5)
    sym_c = Symbol(id="pkg.c.func_c", name="func_c", symbol_type=SymbolType.FUNCTION, file_path="pkg/c.py", line_start=1, line_end=5)

    # Cycle: func_a calls func_b, func_b calls func_c, func_c calls func_a
    edges = [
        DependencyEdge(source_id="pkg.a.func_a", target_id="pkg.b.func_b", relation_type=RelationType.CALLS, confidence=ConfidenceLevel.CONFIRMED, file_path="pkg/a.py", line_number=3),
        DependencyEdge(source_id="pkg.b.func_b", target_id="pkg.c.func_c", relation_type=RelationType.CALLS, confidence=ConfidenceLevel.CONFIRMED, file_path="pkg/b.py", line_number=3),
        DependencyEdge(source_id="pkg.c.func_c", target_id="pkg.a.func_a", relation_type=RelationType.CALLS, confidence=ConfidenceLevel.CONFIRMED, file_path="pkg/c.py", line_number=3),
    ]

    engine = DependencyGraphEngine(symbols=[sym_a, sym_b, sym_c], edges=edges)

    # Modifying func_a:
    # reverse graph has: func_a is called by func_c, func_c is called by func_b, func_b is called by func_a
    impacted = engine.find_impacted_symbols(["pkg.a.func_a"])

    # Traversal must terminate without infinite loop
    assert len(impacted) == 3
    impacted_ids = [s.symbol_id for s in impacted]
    assert impacted_ids[0] == "pkg.a.func_a"
    assert "pkg.c.func_c" in impacted_ids
    assert "pkg.b.func_b" in impacted_ids

    # Check depth monotonicity
    depths = {s.symbol_id: s.depth for s in impacted}
    assert depths["pkg.a.func_a"] == 0
    assert depths["pkg.c.func_c"] == 1
    assert depths["pkg.b.func_b"] == 2
