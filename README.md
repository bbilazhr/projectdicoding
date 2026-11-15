# Proyek Analisis Data: E-Commerce Public Dataset (Olist)

Proyek akhir analisis data menggunakan dataset publik e-commerce Brasil (Olist). Isi proyek:
analisis data (`notebook.ipynb`) dan dashboard interaktif Streamlit (`dashboard/dashboard.py`).

## Pertanyaan Bisnis
1. Kategori produk apa saja yang menjadi 10 penyumbang revenue terbesar (pesanan *delivered*, Januari 2017 – Agustus 2018) dan berapa kontribusinya?
2. Bagaimana tren pesanan dan revenue bulanan (MoM) pada Januari 2017 – Agustus 2018, serta kapan lonjakan tertinggi dan penurunan tertajam?
3. State mana yang memiliki durasi pengiriman terlama dan persentase keterlambatan tertinggi pada Januari 2017 – Agustus 2018?

Analisis lanjutan: **RFM Analysis** dengan *manual grouping* (Loyal, High-Value Recent, New, Need Attention, Lost).

## Struktur Direktori
```
folder-utama-proyek
├───dashboard
│   ├───main_data.csv
│   └───dashboard.py
├───data
│   ├───olist_orders_dataset.csv
│   ├───olist_order_items_dataset.csv
│   ├───olist_customers_dataset.csv
│   ├───olist_products_dataset.csv
│   └───product_category_name_translation.csv
├───notebook.ipynb
├───README.md
├───requirements.txt
└───url.txt
```

## Setup Environment
```
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```
Untuk membuka notebook, pasang juga Jupyter: `pip install jupyter`.

Tautan dashboard yang sudah di-deploy ada pada berkas `url.txt`.

## Menjalankan Notebook
Buka `notebook.ipynb` dengan Jupyter / VS Code / Colab. Jalankan dari folder utama proyek agar path `data/` dan `dashboard/` terbaca.
```
jupyter notebook notebook.ipynb
```

## Menjalankan Dashboard
```
cd <folder utama proyek>
streamlit run dashboard/dashboard.py
```
Dashboard terbuka di `http://localhost:8501`. Gunakan filter pada sidebar (rentang tanggal, state, kategori).
