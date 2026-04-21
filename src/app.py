"""
app.py - REST API Sistem Manajemen Inventori
"""
import os
from flask import Flask, jsonify, request, render_template
from .database import Database
from .services import InventoryService

# Fix: gunakan path absolut agar template ditemukan saat dijalankan sebagai module
_here = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(_here, "templates"))
db = Database()
svc = InventoryService(db)

def _err(msg: str, code: int = 400):
    return jsonify({"error": msg}), code


def _ok(data, code: int = 200):
    return jsonify(data), code


@app.route("/")
def index():
    return render_template("index.html")


# ── Produk ────────────────────────────────────────────────────────────────────

@app.route("/products", methods=["GET"])
def list_products():
    keyword = request.args.get("q")
    if keyword:
        try:
            return _ok(svc.search_products(keyword))
        except ValueError as e:
            return _err(str(e))
    return _ok(svc.list_products())


@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    try:
        return _ok(svc.get_product(product_id))
    except ValueError as e:
        return _err(str(e), 404)


@app.route("/products", methods=["POST"])
def add_product():
    data = request.get_json(silent=True) or {}
    required = ("name", "sku", "category", "price", "stock")
    missing = [f for f in required if f not in data]
    if missing:
        return _err(f"Field wajib tidak ada: {', '.join(missing)}")
    try:
        product = svc.add_product(
            data["name"], data["sku"], data["category"],
            float(data["price"]), int(data["stock"]),
            int(data.get("min_stock", 5)),
        )
        return _ok(product, 201)
    except (ValueError, TypeError) as e:
        return _err(str(e))


@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.get_json(silent=True) or {}
    required = ("name", "category", "price", "min_stock")
    missing = [f for f in required if f not in data]
    if missing:
        return _err(f"Field wajib tidak ada: {', '.join(missing)}")
    try:
        updated = svc.update_product(
            product_id, data["name"], data["category"],
            float(data["price"]), int(data["min_stock"]),
        )
        return _ok(updated)
    except (ValueError, TypeError) as e:
        return _err(str(e))


# ── Transaksi ─────────────────────────────────────────────────────────────────

@app.route("/transactions", methods=["GET"])
def list_transactions():
    product_id = request.args.get("product_id", type=int)
    return _ok(svc.get_transaction_history(product_id))


@app.route("/transactions/in", methods=["POST"])
def stock_in():
    data = request.get_json(silent=True) or {}
    required = ("product_id", "quantity", "note")
    missing = [f for f in required if f not in data]
    if missing:
        return _err(f"Field wajib tidak ada: {', '.join(missing)}")
    try:
        result = svc.stock_in(int(data["product_id"]), int(data["quantity"]), data["note"])
        return _ok(result, 201)
    except (ValueError, TypeError) as e:
        return _err(str(e))


@app.route("/transactions/out", methods=["POST"])
def stock_out():
    data = request.get_json(silent=True) or {}
    required = ("product_id", "quantity", "note")
    missing = [f for f in required if f not in data]
    if missing:
        return _err(f"Field wajib tidak ada: {', '.join(missing)}")
    try:
        result = svc.stock_out(int(data["product_id"]), int(data["quantity"]), data["note"])
        return _ok(result, 201)
    except (ValueError, TypeError) as e:
        return _err(str(e))


# ── Alert & Laporan ───────────────────────────────────────────────────────────

@app.route("/alerts/low-stock", methods=["GET"])
def low_stock_alerts():
    return _ok(svc.get_low_stock_alerts())


@app.route("/reports/inventory", methods=["GET"])
def inventory_report():
    return _ok(svc.get_inventory_report())


if __name__ == "__main__":
    app.run(debug=True)
