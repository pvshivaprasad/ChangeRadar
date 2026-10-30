from app.scanner.models import SymbolType, RelationType, ConfidenceLevel
from app.scanner.parser import PythonASTParser, module_name_from_file_path


def test_module_name_from_file_path():
    assert module_name_from_file_path("auth/service.py") == "auth.service"
    assert module_name_from_file_path("core/__init__.py") == "core"
    assert module_name_from_file_path("checkout\\payment.py") == "checkout.payment"


def test_ast_parser_extracts_classes_methods_calls():
    code = """
import os
from auth.service import AuthService

class PaymentGateway:
    def __init__(self, key: str):
        self.key = key

    def charge(self, user_token: str, amount: int):
        auth = AuthService()
        status = auth.validate_token(user_token)
        return status
"""
    parser = PythonASTParser(rel_path="checkout/payment.py", source_code=code)
    symbols, edges = parser.parse()

    symbol_ids = {s.id for s in symbols}
    assert "checkout.payment" in symbol_ids
    assert "checkout.payment.PaymentGateway" in symbol_ids
    assert "checkout.payment.PaymentGateway.__init__" in symbol_ids
    assert "checkout.payment.PaymentGateway.charge" in symbol_ids

    # Check imported edge
    import_edges = [e for e in edges if e.relation_type == RelationType.IMPORTS]
    assert any(e.target_id == "auth.service.AuthService" for e in import_edges)

    # Check call edge from charge to AuthService or validate_token
    call_edges = [e for e in edges if e.relation_type == RelationType.CALLS]
    assert len(call_edges) > 0
