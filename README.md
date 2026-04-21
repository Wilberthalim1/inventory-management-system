# 📦 Inventory Management System

![CI Status](https://github.com/username/inventory-management-system/actions/workflows/ci.yml/badge.svg)
![Coverage](https://codecov.io/gh/username/inventory-management-system/branch/main/graph/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Sistem manajemen inventori berbasis REST API yang dibangun dengan Python dan Flask. Proyek ini dikembangkan sebagai Final Project Mata Kuliah Software Testing.

---

## ✨ Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| **Manajemen Produk** | Tambah, edit, cari produk dengan validasi SKU unik dan harga |
| **Transaksi Stok** | Catat barang masuk (stock in) dan keluar (stock out) dengan riwayat lengkap |
| **Alert & Laporan** | Notifikasi stok rendah otomatis dan laporan ringkasan nilai inventori |

### Aturan Bisnis
- SKU produk bersifat **unik** dan otomatis diubah ke huruf kapital
- Stock out **diblokir** jika stok tidak mencukupi
- Alert stok rendah dipicu ketika `stock ≤ min_stock`
- Alert `OUT_OF_STOCK` dipicu ketika `stock = 0`
- Laporan inventori mencakup: total produk, total stok, total nilai, jumlah produk stok rendah

---

## 🏗️ Arsitektur

```
inventory-management-system/
├── src/
│   ├── models.py       # Data models (Product, Transaction, StockAlert)
│   ├── database.py     # Lapisan akses database SQLite
│   ├── services.py     # Logika bisnis
│   └── app.py          # REST API endpoints (Flask)
├── tests/
│   ├── test_models.py      # Unit test — model & validasi
│   ├── test_services.py    # Unit test — logika bisnis (mock DB)
│   └── test_integration.py # Integration test — endpoint API + DB
├── .github/workflows/
│   └── ci.yml          # GitHub Actions CI pipeline
├── requirements.txt
├── pyproject.toml
└── README.md
```

**Stack Teknologi:** Python 3.11+, Flask 3.x, SQLite, pytest, pytest-cov, GitHub Actions

---

## 🚀 Cara Menjalankan Aplikasi

```bash
# Clone & masuk ke direktori
git clone https://github.com/username/inventory-management-system.git
cd inventory-management-system

# Buat virtual environment
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Jalankan server
python -m src.app
```

Server berjalan di `http://localhost:5000`.

### Contoh Penggunaan API

```bash
# Tambah produk
curl -X POST http://localhost:5000/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Laptop ASUS","sku":"LPT-001","category":"Elektronik","price":8500000,"stock":20}'

# Stock in (barang masuk)
curl -X POST http://localhost:5000/transactions/in \
  -H "Content-Type: application/json" \
  -d '{"product_id":1,"quantity":10,"note":"Restock dari supplier"}'

# Stock out (barang keluar)
curl -X POST http://localhost:5000/transactions/out \
  -H "Content-Type: application/json" \
  -d '{"product_id":1,"quantity":3,"note":"Penjualan ke customer"}'

# Cek alert stok rendah
curl http://localhost:5000/alerts/low-stock

# Laporan inventori
curl http://localhost:5000/reports/inventory
```

---

## 🧪 Cara Menjalankan Test

```bash
# Semua test
pytest -v

# Dengan laporan coverage di terminal
pytest --cov=src --cov-report=term-missing

# Dengan laporan HTML
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Hanya unit test
pytest tests/test_models.py tests/test_services.py -v

# Hanya integration test
pytest tests/test_integration.py -v
```

---

## 📊 Hasil Test & Coverage

```
Name              Stmts   Miss  Cover
-------------------------------------
src/models.py        66      0   100%
src/services.py      66      0   100%
src/app.py           85      5    94%
src/database.py      64      6    91%
-------------------------------------
TOTAL               281     11    96%
```

| Kategori | Jumlah | Hasil |
|----------|--------|-------|
| Unit Test (model) | 28 test | ✅ passed |
| Unit Test (service) | 18 test | ✅ passed |
| Integration Test | 20 test | ✅ passed |
| **Total** | **66 test** | **✅ 66 passed** |
| **Coverage** | | **96%** |

---

## 🔄 CI/CD Pipeline

GitHub Actions berjalan otomatis pada setiap **push** dan **pull request**.

1. ✅ Checkout kode
2. ✅ Setup Python (matrix: 3.11 & 3.12)
3. ✅ Install dependencies
4. ✅ Jalankan semua test + coverage (`--cov-fail-under=60`)
5. ✅ Upload ke Codecov
6. ✅ Simpan artifact

---

## 🧪 Strategi Pengujian

**Unit Test Model** — Validasi data secara langsung tanpa dependency eksternal. Setiap rule validasi (nama kosong, SKU kosong, harga negatif, stok negatif, tipe transaksi tidak valid) diuji secara terpisah.

**Unit Test Service** — Logika bisnis diisolasi menggunakan `unittest.mock.MagicMock`. Memverifikasi aturan bisnis seperti penolakan SKU duplikat, blokir stock out saat stok kurang, dan kalkulasi laporan.

**Integration Test** — Flask test client + SQLite file sementara. Menguji alur lengkap HTTP request → service → database → response, termasuk siklus penuh stock in/out.
