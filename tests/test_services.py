"""
test_services.py - Unit test untuk logika bisnis (service layer)
"""
import pytest
from unittest.mock import MagicMock, patch
from src.services import InventoryService


@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def svc(mock_db):
    return InventoryService(mock_db)


def _product_row(stock=10, **kwargs):
    base = dict(id=1, name="Laptop", sku="LPT-001", category="Elektronik",
                price=8500000.0, stock=stock, min_stock=3)
    base.update(kwargs)
    return base


# ─────────────────── PRODUCT SERVICE ─────────────────────────────────────────

class TestProductService:
    def test_add_product_success(self, svc, mock_db):
        mock_db.get_product_by_sku.return_value = None
        mock_db.add_product.return_value = 1
        result = svc.add_product("Laptop", "LPT-001", "Elektronik", 8500000, 10)
        assert result["id"] == 1
        assert result["sku"] == "LPT-001"

    def test_add_product_sku_uppercase(self, svc, mock_db):
        mock_db.get_product_by_sku.return_value = None
        mock_db.add_product.return_value = 1
        result = svc.add_product("Laptop", "lpt-001", "Elektronik", 8500000, 10)
        assert result["sku"] == "LPT-001"

    def test_add_product_duplicate_sku_raises(self, svc, mock_db):
        mock_db.get_product_by_sku.return_value = {"id": 1}
        with pytest.raises(ValueError, match="sudah ada"):
            svc.add_product("Laptop", "LPT-001", "Elektronik", 8500000, 10)

    def test_get_product_not_found_raises(self, svc, mock_db):
        mock_db.get_product.return_value = None
        with pytest.raises(ValueError, match="tidak ditemukan"):
            svc.get_product(999)

    def test_search_products_empty_keyword_raises(self, svc, mock_db):
        with pytest.raises(ValueError, match="kosong"):
            svc.search_products("   ")

    def test_list_products_returns_list(self, svc, mock_db):
        mock_db.list_products.return_value = [_product_row()]
        result = svc.list_products()
        assert isinstance(result, list)
        assert len(result) == 1

    def test_update_product_not_found_raises(self, svc, mock_db):
        mock_db.get_product.return_value = None
        with pytest.raises(ValueError, match="tidak ditemukan"):
            svc.update_product(99, "New", "Cat", 1000, 5)


# ─────────────────── TRANSACTION SERVICE ──────────────────────────────────────

class TestTransactionService:
    def test_stock_in_success(self, svc, mock_db):
        mock_db.get_product.return_value = _product_row(stock=10)
        mock_db.add_transaction.return_value = 1
        result = svc.stock_in(1, 5, "Restock dari supplier")
        assert result["new_stock"] == 15
        assert result["type"] == "IN"
        mock_db.update_stock.assert_called_once_with(1, 5)

    def test_stock_in_product_not_found_raises(self, svc, mock_db):
        mock_db.get_product.return_value = None
        with pytest.raises(ValueError, match="tidak ditemukan"):
            svc.stock_in(99, 5, "Test")

    def test_stock_out_success(self, svc, mock_db):
        mock_db.get_product.return_value = _product_row(stock=10)
        mock_db.add_transaction.return_value = 2
        result = svc.stock_out(1, 3, "Penjualan")
        assert result["new_stock"] == 7
        assert result["type"] == "OUT"
        mock_db.update_stock.assert_called_once_with(1, -3)

    def test_stock_out_insufficient_raises(self, svc, mock_db):
        mock_db.get_product.return_value = _product_row(stock=2)
        with pytest.raises(ValueError, match="tidak mencukupi"):
            svc.stock_out(1, 5, "Penjualan")

    def test_stock_out_product_not_found_raises(self, svc, mock_db):
        mock_db.get_product.return_value = None
        with pytest.raises(ValueError, match="tidak ditemukan"):
            svc.stock_out(99, 1, "Test")

    def test_stock_out_exact_quantity_allowed(self, svc, mock_db):
        mock_db.get_product.return_value = _product_row(stock=5)
        mock_db.add_transaction.return_value = 3
        result = svc.stock_out(1, 5, "Ambil semua")
        assert result["new_stock"] == 0

    def test_stock_in_invalid_quantity_raises(self, svc, mock_db):
        mock_db.get_product.return_value = _product_row(stock=10)
        with pytest.raises(ValueError, match="lebih dari 0"):
            svc.stock_in(1, 0, "Test")


# ─────────────────── ALERT & REPORT SERVICE ───────────────────────────────────

class TestAlertAndReportService:
    def test_get_low_stock_alerts_returns_list(self, svc, mock_db):
        mock_db.list_low_stock.return_value = [
            _product_row(stock=2, min_stock=5)
        ]
        alerts = svc.get_low_stock_alerts()
        assert len(alerts) == 1
        assert alerts[0]["severity"] in ("LOW_STOCK", "OUT_OF_STOCK")

    def test_get_low_stock_alerts_empty(self, svc, mock_db):
        mock_db.list_low_stock.return_value = []
        assert svc.get_low_stock_alerts() == []

    def test_inventory_report_correct_totals(self, svc, mock_db):
        mock_db.list_products.return_value = [
            _product_row(stock=10),
            _product_row(id=2, name="Mouse", sku="MOU-001",
                         category="Elektronik", price=150000,
                         stock=0, min_stock=5),
        ]
        mock_db.get_inventory_value.return_value = 85150000.0
        mock_db.list_low_stock.return_value = [
            _product_row(id=2, stock=0, min_stock=5)
        ]
        report = svc.get_inventory_report()
        assert report["total_products"] == 2
        assert report["total_stock"] == 10
        assert report["out_of_stock_count"] == 1
        assert report["low_stock_count"] == 1
        assert report["total_value"] == 85150000.0

    def test_inventory_report_empty(self, svc, mock_db):
        mock_db.list_products.return_value = []
        mock_db.get_inventory_value.return_value = 0.0
        mock_db.list_low_stock.return_value = []
        report = svc.get_inventory_report()
        assert report["total_products"] == 0
        assert report["total_value"] == 0.0
