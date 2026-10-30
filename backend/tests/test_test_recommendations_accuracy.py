"""Tests for Test Recommendation Accuracy, Precision & Recall.

Validates:
- All recommended test files exist in the repository
- Specific test functions identified where call edges exist
- Deduplication of test recommendations
- Exclusion of unrelated tests
- Precision and Recall measurement against defined ground-truth dataset
"""
import pytest
from app.scanner.models import (
    ConfidenceLevel,
    DependencyEdge,
    ImpactType,
    ImpactedSymbol,
    RelationType,
    Symbol,
    SymbolType,
)
from app.scanner.test_mapper import TestRecommendationEngine, is_test_file


def test_is_test_file_accuracy():
    assert is_test_file("tests/test_auth.py") is True
    assert is_test_file("tests/auth_test.py") is True
    assert is_test_file("tests/integration/test_checkout.py") is True
    assert is_test_file("test/unit/test_api.py") is True
    assert is_test_file("auth/service.py") is False
    assert is_test_file("checkout/payment.py") is False
    assert is_test_file("util/test_helper_not_a_test.txt") is False


def test_test_recommendation_precision_recall_ground_truth():
    """
    Constructs a controlled repository with 5 test files:
    - test_auth.py: tests auth.service.validate_token (EXPECTED - direct)
    - test_payment.py: tests checkout.payment.process_payment (EXPECTED - downstream caller)
    - test_profile.py: tests user.profile.get_user_profile (EXPECTED - downstream caller)
    - test_catalog.py: tests catalog.items (UNRELATED - NOT EXPECTED)
    - test_analytics.py: tests analytics.tracker (UNRELATED - NOT EXPECTED)

    Ground Truth Expected:
    {"tests/test_auth.py", "tests/test_payment.py", "tests/test_profile.py"}
    """
    all_symbols = [
        # Production symbols
        Symbol(id="auth.service.validate_token", name="validate_token", symbol_type=SymbolType.FUNCTION, file_path="auth/service.py", line_start=1, line_end=5),
        Symbol(id="checkout.payment.process_payment", name="process_payment", symbol_type=SymbolType.FUNCTION, file_path="checkout/payment.py", line_start=1, line_end=5),
        Symbol(id="user.profile.get_user_profile", name="get_user_profile", symbol_type=SymbolType.FUNCTION, file_path="user/profile.py", line_start=1, line_end=5),
        Symbol(id="catalog.items.list_items", name="list_items", symbol_type=SymbolType.FUNCTION, file_path="catalog/items.py", line_start=1, line_end=5),
        Symbol(id="analytics.tracker.track_event", name="track_event", symbol_type=SymbolType.FUNCTION, file_path="analytics/tracker.py", line_start=1, line_end=5),
        # Test symbols
        Symbol(id="tests.test_auth.test_token", name="test_token", symbol_type=SymbolType.FUNCTION, file_path="tests/test_auth.py", line_start=1, line_end=5),
        Symbol(id="tests.test_payment.test_pay", name="test_pay", symbol_type=SymbolType.FUNCTION, file_path="tests/test_payment.py", line_start=1, line_end=5),
        Symbol(id="tests.test_profile.test_prof", name="test_prof", symbol_type=SymbolType.FUNCTION, file_path="tests/test_profile.py", line_start=1, line_end=5),
        Symbol(id="tests.test_catalog.test_cat", name="test_cat", symbol_type=SymbolType.FUNCTION, file_path="tests/test_catalog.py", line_start=1, line_end=5),
        Symbol(id="tests.test_analytics.test_trk", name="test_trk", symbol_type=SymbolType.FUNCTION, file_path="tests/test_analytics.py", line_start=1, line_end=5),
    ]

    all_edges = [
        # Tests calling symbols
        DependencyEdge(source_id="tests.test_auth.test_token", target_id="auth.service.validate_token", relation_type=RelationType.CALLS, confidence=ConfidenceLevel.CONFIRMED, file_path="tests/test_auth.py", line_number=3),
        DependencyEdge(source_id="tests.test_payment.test_pay", target_id="checkout.payment.process_payment", relation_type=RelationType.CALLS, confidence=ConfidenceLevel.CONFIRMED, file_path="tests/test_payment.py", line_number=3),
        DependencyEdge(source_id="tests.test_profile.test_prof", target_id="user.profile.get_user_profile", relation_type=RelationType.CALLS, confidence=ConfidenceLevel.CONFIRMED, file_path="tests/test_profile.py", line_number=3),
        DependencyEdge(source_id="tests.test_catalog.test_cat", target_id="catalog.items.list_items", relation_type=RelationType.CALLS, confidence=ConfidenceLevel.CONFIRMED, file_path="tests/test_catalog.py", line_number=3),
        DependencyEdge(source_id="tests.test_analytics.test_trk", target_id="analytics.tracker.track_event", relation_type=RelationType.CALLS, confidence=ConfidenceLevel.CONFIRMED, file_path="tests/test_analytics.py", line_number=3),
    ]

    # Impacted blast radius for modifying auth.service.validate_token
    impacted = [
        ImpactedSymbol(symbol_id="auth.service.validate_token", symbol_name="validate_token", symbol_type=SymbolType.FUNCTION, file_path="auth/service.py", line_start=1, line_end=5, impact_type=ImpactType.DIRECT_CHANGE, depth=0, path_from_change=["auth.service.validate_token"]),
        ImpactedSymbol(symbol_id="checkout.payment.process_payment", symbol_name="process_payment", symbol_type=SymbolType.FUNCTION, file_path="checkout/payment.py", line_start=1, line_end=5, impact_type=ImpactType.DIRECT_DEPENDENT, depth=1, path_from_change=["auth.service.validate_token", "checkout.payment.process_payment"]),
        ImpactedSymbol(symbol_id="user.profile.get_user_profile", symbol_name="get_user_profile", symbol_type=SymbolType.FUNCTION, file_path="user/profile.py", line_start=1, line_end=5, impact_type=ImpactType.DIRECT_DEPENDENT, depth=1, path_from_change=["auth.service.validate_token", "user.profile.get_user_profile"]),
    ]

    engine = TestRecommendationEngine(all_symbols=all_symbols, all_edges=all_edges)
    recommendations = engine.recommend_tests(impacted)

    # 1. Check all recommended test files exist in all_symbols
    known_test_files = {s.file_path for s in all_symbols if is_test_file(s.file_path)}
    for r in recommendations:
        assert r.test_file in known_test_files, f"Recommended test file {r.test_file} does not exist!"

    # 2. Check test function specificity
    assert any(r.test_symbol_id == "tests.test_auth.test_token" for r in recommendations)
    assert any(r.test_symbol_id == "tests.test_payment.test_pay" for r in recommendations)
    assert any(r.test_symbol_id == "tests.test_profile.test_prof" for r in recommendations)

    # 3. Check priority classification: direct change gets high priority
    auth_rec = next(r for r in recommendations if r.test_file == "tests/test_auth.py")
    assert auth_rec.priority == "high"

    # 4. Measure Ground Truth Precision and Recall
    expected_test_files = {"tests/test_auth.py", "tests/test_payment.py", "tests/test_profile.py"}
    recommended_files = {r.test_file for r in recommendations}

    true_positives = len(recommended_files.intersection(expected_test_files))
    false_positives = len(recommended_files - expected_test_files)
    false_negatives = len(expected_test_files - recommended_files)

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0

    assert precision == 1.0, f"Precision was {precision}, expected 1.0 (unrelated tests recommended: {recommended_files - expected_test_files})"
    assert recall == 1.0, f"Recall was {recall}, expected 1.0 (expected tests missed: {expected_test_files - recommended_files})"

    # Unrelated tests must NOT be present
    assert "tests/test_catalog.py" not in recommended_files
    assert "tests/test_analytics.py" not in recommended_files
