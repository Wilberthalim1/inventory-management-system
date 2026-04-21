"""
models.py - Data models untuk Sistem Manajemen Inventori
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Product:
    id: int
    name: str
    sku: str
    category: str
    price: float
    stock: int
    min_stock: int = 5  # threshold alert stok minimum

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Nama produk tidak boleh kosong.")
        if not self.sku or not self.sku.strip():
            raise ValueError("SKU tidak boleh kosong.")
        if not self.category or not self.category.strip():
            raise ValueError("Kategori tidak boleh kosong.")
        if self.price < 0:
            raise ValueError("Harga tidak boleh negatif.")
        if self.stock < 0:
            raise ValueError("Stok tidak boleh negatif.")
        if self.min_stock < 0:
            raise ValueError("Stok minimum tidak boleh negatif.")

    def is_low_stock(self) -> bool:
        """Cek apakah stok di bawah atau sama dengan threshold."""
        return self.stock <= self.min_stock

    def is_out_of_stock(self) -> bool:
        return self.stock == 0

    def total_value(self) -> float:
        """Total nilai inventori produk ini (harga × stok)."""
        return round(self.price * self.stock, 2)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "sku": self.sku,
            "category": self.category,
            "price": self.price,
            "stock": self.stock,
            "min_stock": self.min_stock,
            "is_low_stock": self.is_low_stock(),
            "total_value": self.total_value(),
        }


@dataclass
class Transaction:
    id: int
    product_id: int
    type: str           # "IN" atau "OUT"
    quantity: int
    note: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    VALID_TYPES = ("IN", "OUT")

    def __post_init__(self):
        if self.type not in self.VALID_TYPES:
            raise ValueError(f"Tipe transaksi harus IN atau OUT, bukan '{self.type}'.")
        if self.quantity <= 0:
            raise ValueError("Jumlah transaksi harus lebih dari 0.")
        if not self.note or not self.note.strip():
            raise ValueError("Keterangan transaksi tidak boleh kosong.")

    def is_incoming(self) -> bool:
        return self.type == "IN"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "type": self.type,
            "quantity": self.quantity,
            "note": self.note,
            "created_at": self.created_at,
        }


@dataclass
class StockAlert:
    product_id: int
    product_name: str
    sku: str
    current_stock: int
    min_stock: int

    def severity(self) -> str:
        if self.current_stock == 0:
            return "OUT_OF_STOCK"
        return "LOW_STOCK"

    def to_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "sku": self.sku,
            "current_stock": self.current_stock,
            "min_stock": self.min_stock,
            "severity": self.severity(),
        }
