"""Automated validation test using a SECOND INDEPENDENT Python repository
(order processing, inventory management, and notification system).
Validates change impact analysis, dependency depths, test mapper, and risk scoring.
"""
import subprocess
from app.scanner.engine import run_impact_analysis
from app.scanner.models import ImpactType
from app.scanner.scanner import RepositoryScanner


def test_independent_repository_impact_analysis(tmp_path):
    repo_dir = tmp_path / "ecommerce_service"
    repo_dir.mkdir()

    inv_dir = repo_dir / "inventory"
    orders_dir = repo_dir / "orders"
    notif_dir = repo_dir / "notifications"
    tests_dir = repo_dir / "tests"

    for d in (inv_dir, orders_dir, notif_dir, tests_dir):
        d.mkdir()

    # 1. Base files
    (inv_dir / "stock.py").write_text('''class StockService:
    def __init__(self, warehouse_id: str):
        self.warehouse_id = warehouse_id

    def check_stock(self, item_id: str) -> int:
        """Returns quantity available in warehouse."""
        return 100

    def reserve_stock(self, item_id: str, qty: int) -> bool:
        return qty <= self.check_stock(item_id)
''', encoding="utf-8")

    (orders_dir / "processor.py").write_text('''from inventory.stock import StockService

def process_order(order_id: str, item_id: str, qty: int) -> bool:
    """Processes order by checking stock availability."""
    stock_svc = StockService("WH-EAST")
    available = stock_svc.check_stock(item_id)
    return available >= qty
''', encoding="utf-8")

    (notif_dir / "dispatcher.py").write_text('''from orders.processor import process_order

def notify_customer(order_id: str, item_id: str, qty: int) -> str:
    """Dispatches order notification after executing order processing."""
    success = process_order(order_id, item_id, qty)
    return "confirmed" if success else "failed"
''', encoding="utf-8")

    (tests_dir / "test_inventory.py").write_text('''from inventory.stock import StockService

def test_stock_check():
    svc = StockService("WH-1")
    assert svc.check_stock("item_123") == 100
''', encoding="utf-8")

    (tests_dir / "test_orders.py").write_text('''from orders.processor import process_order

def test_order_flow():
    assert process_order("ord_1", "item_123", 5) is True
''', encoding="utf-8")

    # 2. Git init and commit 1
    r_str = str(repo_dir)
    subprocess.run(["git", "init"], cwd=r_str, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Ecom Tester"], cwd=r_str, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "ecom@tester.dev"], cwd=r_str, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=r_str, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "feat: initial ecommerce service"], cwd=r_str, check=True, capture_output=True)

    # 3. Modify check_stock to add warehouse status check in commit 2
    (inv_dir / "stock.py").write_text('''class StockService:
    def __init__(self, warehouse_id: str):
        self.warehouse_id = warehouse_id

    def check_stock(self, item_id: str) -> int:
        """Returns quantity available in warehouse with safety buffer."""
        base_stock = 100
        safety_buffer = 10
        return max(0, base_stock - safety_buffer)

    def reserve_stock(self, item_id: str, qty: int) -> bool:
        return qty <= self.check_stock(item_id)
''', encoding="utf-8")

    subprocess.run(["git", "add", "inventory/stock.py"], cwd=r_str, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "feat: apply safety buffer to check_stock"], cwd=r_str, check=True, capture_output=True)

    # 4. Execute Scanner
    scanner = RepositoryScanner(r_str)
    scan_summary = scanner.scan()
    assert scan_summary.file_count == 5
    assert scan_summary.symbol_count >= 8
    assert scan_summary.edge_count >= 5

    # 5. Execute Impact Analysis
    report = run_impact_analysis(
        repo_path=r_str,
        base_commit="HEAD~1",
        head_commit="HEAD",
    )

    # Validate changed files and symbols
    assert len(report.changed_files) == 1
    assert "inventory/stock.py" in report.changed_files[0].replace("\\", "/")

    changed_ids = [s.id for s in report.changed_symbols]
    assert "inventory.stock.StockService.check_stock" in changed_ids

    # Validate blast radius: direct vs transitive
    impacted_map = {s.symbol_id: s for s in report.impacted_symbols}

    # Direct change at depth 0
    assert "inventory.stock.StockService.check_stock" in impacted_map
    assert impacted_map["inventory.stock.StockService.check_stock"].impact_type == ImpactType.DIRECT_CHANGE
    assert impacted_map["inventory.stock.StockService.check_stock"].depth == 0

    # Direct caller at depth 1: orders.processor.process_order and tests.test_inventory
    assert "orders.processor.process_order" in impacted_map
    assert impacted_map["orders.processor.process_order"].impact_type == ImpactType.DIRECT_DEPENDENT
    assert impacted_map["orders.processor.process_order"].depth == 1

    # Transitive caller at depth 2: notifications.dispatcher.notify_customer and tests.test_orders
    assert "notifications.dispatcher.notify_customer" in impacted_map
    assert impacted_map["notifications.dispatcher.notify_customer"].impact_type == ImpactType.TRANSITIVE_DEPENDENT
    assert impacted_map["notifications.dispatcher.notify_customer"].depth == 2

    # Validate recommended tests
    test_files = [t.test_file.replace("\\", "/") for t in report.recommended_tests]
    assert any("test_inventory.py" in f for f in test_files)
    assert any("test_orders.py" in f for f in test_files)

    # Validate non-fabricated risk score
    assert report.risk_level in ("low", "medium", "elevated", "high")
    assert 0.0 < report.risk_score <= 100.0
