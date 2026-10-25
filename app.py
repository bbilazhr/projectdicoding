
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

st.set_page_config(
    page_title="Olist E-Commerce Analytics",
    page_icon="📊",
    layout="wide"
)

DATA_DIR = Path(__file__).parent / "dashboard_data"

@st.cache_data
def load_data():
    sales = pd.read_csv(
        DATA_DIR / "monthly_sales.csv"
    )
    delivery = pd.read_csv(
        DATA_DIR / "delivery_summary.csv"
    )
    rfm = pd.read_csv(
        DATA_DIR / "rfm_customers.csv"
    )
    orders = pd.read_csv(
        DATA_DIR / "order_analysis.csv",
        parse_dates=["order_purchase_timestamp"]
    )

    return sales, delivery, rfm, orders

st.title("Olist E-Commerce Analytics")
st.caption(
    "Dashboard analisis penjualan, pengiriman, "
    "dan segmentasi pelanggan"
)

try:
    sales, delivery, rfm, orders = load_data()
except (FileNotFoundError, pd.errors.EmptyDataError):
    st.error(
        "File CSV tidak ditemukan atau kosong. "
        "Pastikan semua file berada di folder dashboard_data."
    )
    st.stop()

# Filter periode
orders = orders.dropna(
    subset=["order_purchase_timestamp"]
).copy()

orders["year"] = (
    orders["order_purchase_timestamp"].dt.year
)

years = sorted(orders["year"].unique().tolist())

if not years:
    st.warning("Tidak ada data tanggal yang valid.")
    st.stop()

selected_year = st.sidebar.selectbox(
    "Pilih tahun",
    years,
    index=len(years) - 1
)

filtered_orders = orders[
    orders["year"] == selected_year
].copy()

# KPI
total_orders = filtered_orders["order_id"].nunique()

revenue = filtered_orders[
    "total_payment"
].sum()

avg_review = filtered_orders[
    "average_review"
].mean()

k1, k2, k3 = st.columns(3)

k1.metric(
    "Total Pesanan",
    f"{total_orders:,}"
)

k2.metric(
    "Total Pembayaran",
    f"R$ {revenue:,.2f}"
)

k3.metric(
    "Rata-rata Ulasan",
    f"{avg_review:.2f}/5"
    if pd.notna(avg_review)
    else "Tidak tersedia"
)

st.divider()

# Tren penjualan
st.subheader("Tren Penjualan Bulanan")

sales["year"] = sales["month"].astype(str).str[:4]

year_sales = sales[
    sales["year"] == str(selected_year)
].copy()

if not year_sales.empty:
    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(
        year_sales["month"],
        year_sales["revenue"],
        marker="o",
        label="Pendapatan"
    )

    ax.set_xlabel("Bulan")
    ax.set_ylabel("Pendapatan (BRL)")
    ax.tick_params(axis="x", rotation=45)
    ax.legend()

    st.pyplot(fig)
    plt.close(fig)
else:
    st.info("Tidak ada data penjualan untuk tahun ini.")

# Pengiriman dan ulasan
st.subheader("Performa Pengiriman dan Ulasan")

delivery_chart = delivery[
    delivery["delivery_status"].isin(
        ["Terlambat", "Tepat waktu"]
    )
]

if not delivery_chart.empty:
    fig, ax = plt.subplots(figsize=(8, 4))

    sns.barplot(
        data=delivery_chart,
        x="delivery_status",
        y="average_review",
        ax=ax
    )

    ax.set_xlabel("Status pengiriman")
    ax.set_ylabel("Rata-rata skor ulasan")
    ax.set_ylim(0, 5)

    st.pyplot(fig)
    plt.close(fig)

# Segmentasi pelanggan
st.subheader("Segmentasi Pelanggan (RFM)")

if not rfm.empty:
    segment_summary = (
        rfm.groupby("segment", as_index=False)
        .agg(
            total_customers=(
                "customer_unique_id", "nunique"
            ),
            total_spending=("Monetary", "sum")
        )
        .sort_values(
            "total_customers",
            ascending=False
        )
    )

    fig, ax = plt.subplots(figsize=(10, 5))

    sns.barplot(
        data=segment_summary,
        x="total_customers",
        y="segment",
        ax=ax
    )

    ax.set_xlabel("Jumlah pelanggan")
    ax.set_ylabel("Segmen")

    st.pyplot(fig)
    plt.close(fig)

    st.dataframe(
        segment_summary,
        use_container_width=True
    )

st.subheader("Data Pesanan")

st.dataframe(
    filtered_orders.head(500),
    use_container_width=True
)
