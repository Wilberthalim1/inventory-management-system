"""
test_integration.py - Integration test untuk REST API endpoint
Menguji interaksi langsung antara Flask app, service, dan SQLite database.
"""
import pytest
import json
import tempfile
import os
from src.app import app
from src.database import Database
from src.services import InventoryService


@pytest.fixture
def client():
    """Buat test client dengan database SQLite sementara per test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    import src.app as app_module
    app_module.db = Database(db_path)
    app_module.svc = InventoryService(app_module.db)

    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

    os.unlink(db_path)


def post_json(client, url, data):
    return client.post(url, json=data, content_type="application/json")

def put_json(client, url, data):
    return client.put(url, json=data, content_type="application/json")

PRODUCT_PAYLOAD = dict(name="Laptop ASUS", sku="LPT-001",
                       category="Elektronik", price=8500000, stock=20, min_stock=5)


# ── Product Endpoints ─────────────────────────────────────────────────────────

class TestProductEndpoints:
    def test_add_product_returns_201(self, client):
        resp = post_json(client, "/products", PRODUCT_PAYLOAD)
        assert resp.status_code == 201
        data = json.loads(resp.data)
        assert data["name"] == "Laptop ASUS"
        assert data["sku"] == "LPT-001"
        assert data["id"] >= 1

    def test_add_product_missing_field_returns_400(self, client):
        resp = post_json(client, "/products", {"name": "Laptop"})
        assert resp.status_code == 400
        assert "wajib" in json.loads(resp.data)["error"]

    def test_add_product_duplicate_sku_returns_400(self, client):
        post_json(client, "/products", PRODUCT_PAYLOAD)
        resp = post_json(client, "/products", PRODUCT_PAYLOAD)
        assert resp.status_code == 400
        assert "sudah ada" in json.loads(resp.data)["error"]

    def test_get_product_existing_returns_200(self, client):
        post_json(client, "/products", PRODUCT_PAYLOAD)
        resp = client.get("/products/1")
        assert resp.status_code == 200
        assert json.loads(resp.data)["name"] == "Laptop ASUS"

    def test_get_product_not_found_returns_404(self, client):
        resp = client.get("/products/9999")
        assert resp.status_code == 404

    def test_list_products_empty_returns_200(self, client):
        resp = client.get("/products")
        assert resp.status_code == 200
        assert json.loads(resp.data) == []

    def test_list_products_returns_all(self, client):
        post_json(client, "/products", PRODUCT_PAYLOAD)
        post_json(client, "/products", {**PRODUCT_PAYLOAD, "sku": "LPT-002", "name": "Laptop Lenovo"})
        resp = client.get("/products")
        assert len(json.loads(resp.data)) == 2

    def test_search_products_returns_filtered(self, client):
        post_json(client, "/products", PRODUCT_PAYLOAD)
        resp = client.get("/products?q=Laptop")
        assert resp.status_code == 200
        results = json.loads(resp.data)
        assert any("Laptop" in p["name"] for p in results)

    def test_update_product_returns_200(self, client):
        post_json(client, "/products", PRODUCT_PAYLOAD)
        resp = put_json(client, "/products/1", {
            "name": "Laptop ASUS Updated",
            "category": "Komputer",
            "price": 9000000,
            "min_stock": 3,
        })
        assert resp.status_code == 200
        assert json.loads(resp.data)["name"] == "Laptop ASUS Updated"

    def test_update_product_not_found_returns_400(self, client):
        resp = put_json(client, "/products/9999", {
            "name": "X", "category": "Y", "price": 100, "min_stock": 1
        })
        assert resp.status_code == 400


# ── Transaction Endpoints ─────────────────────────────────────────────────────

class TestTransactionEndpoints:
    def _add_product(self, client, stock=20):
        post_json(client, "/products", {**PRODUCT_PAYLOAD, "stock": stock})

    def test_stock_in_returns_201(self, client):
        self._add_product(client)
        resp = post_json(client, "/transactions/in", {
            "product_id": 1, "quantity": 10, "note": "Restock supplier"
        })
        assert resp.status_code == 201
        data = json.loads(resp.data)
        assert data["new_stock"] == 30
        assert data["type"] == "IN"

    def test_stock_out_returns_201(self, client):
        self._add_product(client, stock=20)
        resp = post_json(client, "/transactions/out", {
            "product_id": 1, "quantity": 5, "note": "Penjualan ke customer"
        })
        assert resp.status_code == 201
        data = json.loads(resp.data)
        assert data["new_stock"] == 15
        assert data["type"] == "OUT"

    def test_stock_out_insufficient_returns_400(self, client):
        self._add_product(client, stock=3)
        resp = post_json(client, "/transactions/out", {
            "product_id": 1, "quantity": 10, "note": "Penjualan"
        })
        assert resp.status_code == 400
        assert "tidak mencukupi" in json.loads(resp.data)["error"]

    def test_stock_in_product_not_found_returns_400(self, client):
        resp = post_json(client, "/transactions/in", {
            "product_id": 9999, "quantity": 5, "note": "Test"
        })
        assert resp.status_code == 400

    def test_transaction_missing_field_returns_400(self, client):
        resp = post_json(client, "/transactions/in", {"product_id": 1})
        assert resp.status_code == 400

    def test_list_transactions_returns_200(self, client):
        resp = client.get("/transactions")
        assert resp.status_code == 200
        assert isinstance(json.loads(resp.data), list)

    def test_full_stock_in_and_out_cycle(self, client):
        """Siklus lengkap: tambah produk → stock in → stock out → cek stok akhir."""
        post_json(client, "/products", {**PRODUCT_PAYLOAD, "stock": 10})
        post_json(client, "/transactions/in",  {"product_id": 1, "quantity": 20, "note": "Restock"})
        post_json(client, "/transactions/out", {"product_id": 1, "quantity": 5,  "note": "Jual"})
        product = json.loads(client.get("/products/1").data)
        assert product["stock"] == 25   # 10 + 20 - 5


# ── Alert & Report Endpoints ──────────────────────────────────────────────────

class TestAlertAndReportEndpoints:
    def test_low_stock_alert_empty_returns_200(self, client):
        resp = client.get("/alerts/low-stock")
        assert resp.status_code == 200
        assert json.loads(resp.data) == []

    def test_low_stock_alert_detects_low(self, client):
        post_json(client, "/products", {**PRODUCT_PAYLOAD, "stock": 2, "min_stock": 5})
        resp = client.get("/alerts/low-stock")
        alerts = json.loads(resp.data)
        assert len(alerts) == 1
        assert alerts[0]["severity"] in ("LOW_STOCK", "OUT_OF_STOCK")

    def test_inventory_report_returns_correct_data(self, client):
        post_json(client, "/products", {**PRODUCT_PAYLOAD, "stock": 10})
        resp = client.get("/reports/inventory")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["total_products"] == 1
        assert data["total_stock"] == 10
        assert data["total_value"] == 8500000 * 10
