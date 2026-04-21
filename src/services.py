"""
services.py - Logika bisnis Sistem Manajemen Inventori
"""
from datetime import datetime
from typing import Optional

from .models import Product, Transaction, StockAlert
from .database import Database


class InventoryService:
    def __init__(self, db: Database):
        self.db = db

    # ── Manajemen Produk ───────────────────────────────────────────────────────

    def add_product(self, name: str, sku: str, category: str,
                    price: float, stock: int, min_stock: int = 5) -> dict:
        """Tambah produk baru ke inventori."""
        # Validasi model terlebih dahulu
        product = Product(
            id=0, name=name, sku=sku.upper(), category=category,
            price=price, stock=stock, min_stock=min_stock,
        )
        if self.db.get_product_by_sku(product.sku):
            raise ValueError(f"Produk dengan SKU '{product.sku}' sudah ada.")
        pid = self.db.add_product(
            product.name, product.sku, product.category,
            product.price, product.stock, product.min_stock,
        )
        return {**product.to_dict(), "id": pid}

    def get_product(self, product_id: int) -> dict:
        row = self.db.get_product(product_id)
        if not row:
            raise ValueError(f"Produk ID {product_id} tidak ditemukan.")
        p = Product(**dict(row))
        return p.to_dict()

    def list_products(self) -> list:
        return [Product(**dict(r)).to_dict() for r in self.db.list_products()]

    def search_products(self, keyword: str) -> list:
        if not keyword or not keyword.strip():
            raise ValueError("Kata kunci pencarian tidak boleh kosong.")
        return [Product(**dict(r)).to_dict() for r in self.db.search_products(keyword.strip())]

    def update_product(self, product_id: int, name: str, category: str,
                       price: float, min_stock: int) -> dict:
        """Update informasi produk (tidak termasuk stok & SKU)."""
        existing = self.get_product(product_id)
        # Validasi via model
        Product(
            id=product_id, name=name, sku=existing["sku"],
            category=category, price=price,
            stock=existing["stock"], min_stock=min_stock,
        )
        self.db.update_product(product_id, name, category, price, min_stock)
        return self.get_product(product_id)

    # ── Transaksi Stok ─────────────────────────────────────────────────────────

    def stock_in(self, product_id: int, quantity: int, note: str) -> dict:
        """Catat penambahan stok (barang masuk)."""
        tx = Transaction(
            id=0, product_id=product_id,
            type="IN", quantity=quantity, note=note,
        )
        product = self.db.get_product(product_id)
        if not product:
            raise ValueError(f"Produk ID {product_id} tidak ditemukan.")

        self.db.update_stock(product_id, quantity)
        tx_id = self.db.add_transaction(
            product_id, "IN", quantity, note, tx.created_at
        )
        return {**tx.to_dict(), "id": tx_id,
                "new_stock": product["stock"] + quantity}

    def stock_out(self, product_id: int, quantity: int, note: str) -> dict:
        """Catat pengurangan stok (barang keluar)."""
        tx = Transaction(
            id=0, product_id=product_id,
            type="OUT", quantity=quantity, note=note,
        )
        product = self.db.get_product(product_id)
        if not product:
            raise ValueError(f"Produk ID {product_id} tidak ditemukan.")
        if product["stock"] < quantity:
            raise ValueError(
                f"Stok tidak mencukupi. Tersedia: {product['stock']}, "
                f"diminta: {quantity}."
            )

        self.db.update_stock(product_id, -quantity)
        tx_id = self.db.add_transaction(
            product_id, "OUT", quantity, note, tx.created_at
        )
        return {**tx.to_dict(), "id": tx_id,
                "new_stock": product["stock"] - quantity}

    def get_transaction_history(self, product_id: Optional[int] = None) -> list:
        return [dict(r) for r in self.db.list_transactions(product_id)]

    # ── Alert & Laporan ────────────────────────────────────────────────────────

    def get_low_stock_alerts(self) -> list:
        """Dapatkan semua produk yang stoknya di bawah atau sama dengan min_stock."""
        rows = self.db.list_low_stock()
        alerts = []
        for r in rows:
            p = Product(**dict(r))
            alert = StockAlert(
                product_id=p.id,
                product_name=p.name,
                sku=p.sku,
                current_stock=p.stock,
                min_stock=p.min_stock,
            )
            alerts.append(alert.to_dict())
        return alerts

    def get_inventory_report(self) -> dict:
        """Laporan ringkasan inventori: total produk, total stok, total nilai."""
        products = self.db.list_products()
        total_products = len(products)
        total_stock = sum(r["stock"] for r in products)
        total_value = self.db.get_inventory_value()
        low_stock_count = len(self.db.list_low_stock())
        out_of_stock = sum(1 for r in products if r["stock"] == 0)

        return {
            "total_products": total_products,
            "total_stock": total_stock,
            "total_value": total_value,
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock,
        }
