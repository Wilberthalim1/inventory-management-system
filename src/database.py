"""
database.py - Lapisan akses data menggunakan SQLite
"""
import sqlite3
from contextlib import contextmanager
from typing import Optional


class Database:
    def __init__(self, db_path: str = "inventory.db"):
        self.db_path = db_path
        self._init_schema()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS products (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT    NOT NULL,
                    sku         TEXT    NOT NULL UNIQUE,
                    category    TEXT    NOT NULL,
                    price       REAL    NOT NULL DEFAULT 0,
                    stock       INTEGER NOT NULL DEFAULT 0,
                    min_stock   INTEGER NOT NULL DEFAULT 5
                );

                CREATE TABLE IF NOT EXISTS transactions (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id  INTEGER NOT NULL REFERENCES products(id),
                    type        TEXT    NOT NULL CHECK(type IN ('IN','OUT')),
                    quantity    INTEGER NOT NULL,
                    note        TEXT    NOT NULL,
                    created_at  TEXT    NOT NULL
                );
            """)

    # ── Products ───────────────────────────────────────────────────────────────
    def add_product(self, name, sku, category, price, stock, min_stock=5) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO products (name,sku,category,price,stock,min_stock) VALUES (?,?,?,?,?,?)",
                (name, sku, category, price, stock, min_stock),
            )
            return cur.lastrowid

    def get_product(self, product_id: int) -> Optional[sqlite3.Row]:
        with self._conn() as conn:
            return conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()

    def get_product_by_sku(self, sku: str) -> Optional[sqlite3.Row]:
        with self._conn() as conn:
            return conn.execute("SELECT * FROM products WHERE sku=?", (sku,)).fetchone()

    def list_products(self) -> list:
        with self._conn() as conn:
            return conn.execute("SELECT * FROM products ORDER BY name").fetchall()

    def update_stock(self, product_id: int, delta: int):
        with self._conn() as conn:
            conn.execute(
                "UPDATE products SET stock = stock + ? WHERE id=?", (delta, product_id)
            )

    def update_product(self, product_id: int, name, category, price, min_stock):
        with self._conn() as conn:
            conn.execute(
                "UPDATE products SET name=?,category=?,price=?,min_stock=? WHERE id=?",
                (name, category, price, min_stock, product_id),
            )

    def search_products(self, keyword: str) -> list:
        kw = f"%{keyword}%"
        with self._conn() as conn:
            return conn.execute(
                "SELECT * FROM products WHERE name LIKE ? OR sku LIKE ? OR category LIKE ?",
                (kw, kw, kw),
            ).fetchall()

    def list_low_stock(self) -> list:
        with self._conn() as conn:
            return conn.execute(
                "SELECT * FROM products WHERE stock <= min_stock"
            ).fetchall()

    # ── Transactions ───────────────────────────────────────────────────────────
    def add_transaction(self, product_id, tx_type, quantity, note, created_at) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO transactions (product_id,type,quantity,note,created_at) VALUES (?,?,?,?,?)",
                (product_id, tx_type, quantity, note, created_at),
            )
            return cur.lastrowid

    def get_transaction(self, tx_id: int) -> Optional[sqlite3.Row]:
        with self._conn() as conn:
            return conn.execute("SELECT * FROM transactions WHERE id=?", (tx_id,)).fetchone()

    def list_transactions(self, product_id: Optional[int] = None) -> list:
        with self._conn() as conn:
            if product_id:
                return conn.execute(
                    "SELECT * FROM transactions WHERE product_id=? ORDER BY created_at DESC",
                    (product_id,),
                ).fetchall()
            return conn.execute(
                "SELECT * FROM transactions ORDER BY created_at DESC"
            ).fetchall()

    def get_inventory_value(self) -> float:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(price * stock), 0) as total FROM products"
            ).fetchone()
            return round(row["total"], 2)
