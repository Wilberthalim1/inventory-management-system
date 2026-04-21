"""
test_models.py - Unit test untuk model data
"""
import pytest
from src.models import Product, Transaction, StockAlert


# ─────────────────────────── PRODUCT ────────────────────────────────────────

class TestProduct:
    def _make(self, **kwargs):
        defaults = dict(id=1, name="Laptop ASUS", sku="LPT-001",
                        category="Elektronik", price=8500000, stock=10, min_stock=3)
        return Product(**{**defaults, **kwargs})

    def test_product_created_successfully(self):
        p = self._make()
        assert p.name == "Laptop ASUS"
        assert p.stock == 10

    def test_product_default_min_stock(self):
        p = Product(1, "Meja", "MJ-001", "Furniture", 500000, 20)
        assert p.min_stock == 5

    def test_product_is_low_stock_true(self):
        p = self._make(stock=3, min_stock=3)
        assert p.is_low_stock() is True

    def test_product_is_low_stock_false(self):
        p = self._make(stock=10, min_stock=3)
        assert p.is_low_stock() is False

    def test_product_is_out_of_stock_true(self):
        p = self._make(stock=0)
        assert p.is_out_of_stock() is True

    def test_product_is_out_of_stock_false(self):
        p = self._make(stock=5)
        assert p.is_out_of_stock() is False

    def test_product_total_value(self):
        p = self._make(price=10000, stock=5)
        assert p.total_value() == 50000.0

    def test_product_total_value_zero_stock(self):
        p = self._make(price=10000, stock=0)
        assert p.total_value() == 0.0

    def test_product_to_dict_keys(self):
        p = self._make()
        d = p.to_dict()
        assert set(d.keys()) == {
            "id", "name", "sku", "category", "price",
            "stock", "min_stock", "is_low_stock", "total_value"
        }

    def test_product_raises_empty_name(self):
        with pytest.raises(ValueError, match="Nama produk"):
            self._make(name="")

    def test_product_raises_empty_sku(self):
        with pytest.raises(ValueError, match="SKU"):
            self._make(sku="  ")

    def test_product_raises_empty_category(self):
        with pytest.raises(ValueError, match="Kategori"):
            self._make(category="")

    def test_product_raises_negative_price(self):
        with pytest.raises(ValueError, match="Harga"):
            self._make(price=-1)

    def test_product_raises_negative_stock(self):
        with pytest.raises(ValueError, match="Stok tidak boleh"):
            self._make(stock=-5)

    def test_product_raises_negative_min_stock(self):
        with pytest.raises(ValueError, match="Stok minimum"):
            self._make(min_stock=-1)

    def test_product_price_zero_valid(self):
        p = self._make(price=0)
        assert p.price == 0

    def test_product_low_stock_below_min(self):
        p = self._make(stock=2, min_stock=5)
        assert p.is_low_stock() is True


# ─────────────────────────── TRANSACTION ─────────────────────────────────────

class TestTransaction:
    def _make(self, **kwargs):
        defaults = dict(id=1, product_id=1, type="IN",
                        quantity=10, note="Pembelian supplier")
        return Transaction(**{**defaults, **kwargs})

    def test_transaction_in_created(self):
        tx = self._make(type="IN")
        assert tx.type == "IN"
        assert tx.is_incoming() is True

    def test_transaction_out_created(self):
        tx = self._make(type="OUT")
        assert tx.is_incoming() is False

    def test_transaction_to_dict(self):
        tx = self._make()
        d = tx.to_dict()
        assert "type" in d and "quantity" in d and "created_at" in d

    def test_transaction_raises_invalid_type(self):
        with pytest.raises(ValueError, match="IN atau OUT"):
            self._make(type="TRANSFER")

    def test_transaction_raises_zero_quantity(self):
        with pytest.raises(ValueError, match="lebih dari 0"):
            self._make(quantity=0)

    def test_transaction_raises_negative_quantity(self):
        with pytest.raises(ValueError, match="lebih dari 0"):
            self._make(quantity=-5)

    def test_transaction_raises_empty_note(self):
        with pytest.raises(ValueError, match="Keterangan"):
            self._make(note="")

    def test_transaction_auto_created_at(self):
        tx = self._make()
        assert tx.created_at is not None
        assert len(tx.created_at) > 0


# ─────────────────────────── STOCK ALERT ─────────────────────────────────────

class TestStockAlert:
    def test_alert_severity_low_stock(self):
        alert = StockAlert(1, "Laptop", "LPT-001", current_stock=2, min_stock=5)
        assert alert.severity() == "LOW_STOCK"

    def test_alert_severity_out_of_stock(self):
        alert = StockAlert(1, "Laptop", "LPT-001", current_stock=0, min_stock=5)
        assert alert.severity() == "OUT_OF_STOCK"

    def test_alert_to_dict(self):
        alert = StockAlert(1, "Laptop", "LPT-001", current_stock=1, min_stock=5)
        d = alert.to_dict()
        assert "severity" in d
        assert d["severity"] == "LOW_STOCK"
