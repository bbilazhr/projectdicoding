import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from matplotlib.ticker import FuncFormatter

st.set_page_config(page_title="Olist E-Commerce Dashboard", page_icon="🛒", layout="wide")
sns.set_theme(style="whitegrid")

def fmt(x, desimal=0):
    # Format angka gaya Indonesia: titik sebagai pemisah ribuan, koma sebagai desimal
    return f"{x:,.{desimal}f}".replace(",", "#").replace(".", ",").replace("#", ".")


BLUE, GREY, RED, ORANGE, GREEN = "#2E86AB", "#C9CED6", "#D1495B", "#E09F3E", "#3B8B5A"


@st.cache_data
def load_data():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main_data.csv")
    df = pd.read_csv(path, parse_dates=["order_purchase_timestamp", "order_delivered_customer_date",
                                        "order_estimated_delivery_date"])
    return df


def create_category_df(df):
    out = (df.groupby("category").agg(revenue=("price", "sum"), orders=("order_id", "nunique"))
           .sort_values("revenue", ascending=False).reset_index())
    out["pct_revenue"] = out["revenue"] / out["revenue"].sum() * 100
    return out


def create_monthly_df(df):
    out = (df.groupby("order_month").agg(orders=("order_id", "nunique"), revenue=("price", "sum"))
           .reset_index())
    out["revenue_mom"] = out["revenue"].pct_change() * 100
    return out


def create_state_df(df):
    od = df.drop_duplicates("order_id")
    out = (od.groupby("customer_state")
           .agg(orders=("order_id", "count"), avg_delivery_days=("delivery_days", "mean"),
                late_pct=("is_late", "mean"), late_orders=("is_late", "sum")).reset_index())
    out["late_pct"] *= 100
    return out


def create_rfm_df(df):
    snapshot = df["order_purchase_timestamp"].max() + pd.Timedelta(days=1)
    rfm = (df.groupby("customer_unique_id")
           .agg(last_purchase=("order_purchase_timestamp", "max"), frequency=("order_id", "nunique"),
                monetary=("price", "sum")).reset_index())
    rfm["recency"] = (snapshot - rfm["last_purchase"]).dt.days
    p75 = rfm["monetary"].quantile(0.75)

    def seg(r):
        if r["frequency"] >= 2:
            return "Loyal Customer"
        if r["recency"] <= 180:
            return "High-Value Recent" if r["monetary"] >= p75 else "New Customer"
        if r["recency"] <= 365:
            return "Need Attention"
        return "Lost Customer"

    rfm["segment"] = rfm.apply(seg, axis=1)
    return rfm


all_df = load_data()

# ----------------------------------------------------------------- SIDEBAR
with st.sidebar:
    st.title("🛒 Filter Data")
    min_date = all_df["order_purchase_timestamp"].min().date()
    max_date = all_df["order_purchase_timestamp"].max().date()
    date_range = st.date_input("Rentang tanggal pembelian", value=(min_date, max_date),
                               min_value=min_date, max_value=max_date)
    states = sorted(all_df["customer_state"].unique())
    sel_states = st.multiselect("State pelanggan", states, placeholder="Semua state")
    cats = sorted(all_df["category"].unique())
    sel_cats = st.multiselect("Kategori produk", cats, placeholder="Semua kategori")
    st.caption("Data: Olist Brazilian E-Commerce, pesanan *delivered* Januari 2017 – Agustus 2018.")

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start, end = date_range
else:
    start = end = date_range[0] if isinstance(date_range, (tuple, list)) else date_range

df = all_df[(all_df["order_purchase_timestamp"].dt.date >= start) & (all_df["order_purchase_timestamp"].dt.date <= end)]
if sel_states:
    df = df[df["customer_state"].isin(sel_states)]
if sel_cats:
    df = df[df["category"].isin(sel_cats)]

st.title("Olist E-Commerce Dashboard")
st.caption("Ringkasan interaktif hasil analisis: kategori produk, tren penjualan, performa pengiriman, dan segmentasi pelanggan.")

if df.empty:
    st.warning("Tidak ada data untuk filter yang dipilih. Ubah filter pada sidebar.")
    st.stop()

order_df = df.drop_duplicates("order_id")

# ----------------------------------------------------------------- KPI
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Revenue", f"R$ {fmt(df['price'].sum()/1e6, 2)} juta")
c2.metric("Total Pesanan", fmt(order_df.shape[0]))
c3.metric("Pelanggan Unik", fmt(df['customer_unique_id'].nunique()))
c4.metric("Rata-rata Durasi Kirim", f"{fmt(order_df['delivery_days'].mean(), 1)} hari")
c5.metric("Pesanan Terlambat", f"{fmt(order_df['is_late'].mean()*100, 1)}%")

tab1, tab2, tab3, tab4 = st.tabs(["📦 Kategori Produk", "📈 Tren Bulanan", "🚚 Pengiriman per State", "👥 Segmentasi RFM"])

# ----------------------------------------------------------------- TAB 1
with tab1:
    st.subheader("Kategori produk dengan revenue terbesar")
    top_n = st.slider("Jumlah kategori ditampilkan", 5, 20, 10)
    cat_df = create_category_df(df)
    top = cat_df.head(top_n).sort_values("revenue")
    fig, ax = plt.subplots(figsize=(11, max(4, top_n * 0.45)))
    colors = [GREY] * max(0, len(top) - 3) + [BLUE] * min(3, len(top))
    ax.barh(top["category"], top["revenue"] / 1e6, color=colors)
    for i, (rev, pct) in enumerate(zip(top["revenue"], top["pct_revenue"])):
        ax.text(rev / 1e6 + top["revenue"].max() / 1e6 * 0.01, i, f"R$ {fmt(rev/1e6, 2)} juta ({fmt(pct, 1)}%)", va="center", fontsize=9)
    ax.set_xlim(0, top["revenue"].max() / 1e6 * 1.3)
    ax.set_xlabel("Revenue (juta R$)")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt(v, 1)))
    ax.set_ylabel("")
    sns.despine(left=True)
    st.pyplot(fig)
    plt.close(fig)
    shown = min(top_n, len(cat_df))
    share = fmt(cat_df.head(top_n)["pct_revenue"].sum(), 1)
    if len(cat_df) <= top_n:
        st.info(f"Seluruh {shown} kategori yang tersedia pada filter ini menyumbang **{share}%** dari total revenue.")
    else:
        st.info(f"{shown} kategori teratas menyumbang **{share}%** dari total revenue pada filter ini.")
    with st.expander("Lihat tabel data"):
        st.dataframe(cat_df.head(top_n))

# ----------------------------------------------------------------- TAB 2
with tab2:
    st.subheader("Tren pesanan dan revenue bulanan")
    monthly = create_monthly_df(df)
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True, gridspec_kw={"height_ratios": [3, 2]})
    x = range(len(monthly))
    axes[0].plot(x, monthly["revenue"] / 1e6, marker="o", color=BLUE, linewidth=2.2)
    axes[0].fill_between(x, monthly["revenue"] / 1e6, alpha=0.12, color=BLUE)
    ip = int(monthly["revenue"].values.argmax())
    axes[0].scatter([ip], [monthly["revenue"].iloc[ip] / 1e6], color=RED, zorder=5)
    axes[0].annotate(f"Puncak: {monthly['order_month'].iloc[ip]}", (ip, monthly["revenue"].iloc[ip] / 1e6),
                     textcoords="offset points", xytext=(10, 8), fontsize=10)
    axes[0].set_ylabel("Revenue (juta R$)")
    axes[0].yaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt(v, 1)))
    axes[1].bar(x, monthly["orders"], color="#9BB7C9")
    axes[1].bar(ip, monthly["orders"].iloc[ip], color=BLUE)
    axes[1].set_ylabel("Jumlah pesanan")
    axes[1].set_xticks(list(x))
    axes[1].set_xticklabels(monthly["order_month"], rotation=60, ha="right")
    sns.despine()
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
    if len(monthly) > 1:
        worst = monthly.iloc[1:].loc[monthly.iloc[1:]["revenue_mom"].idxmin()]
        st.info(f"Revenue tertinggi: **{monthly['order_month'].iloc[ip]}** (R$ {fmt(monthly['revenue'].iloc[ip])}). "
                f"Penurunan MoM tertajam: **{worst['order_month']}** ({fmt(worst['revenue_mom'], 1)}%).")
    with st.expander("Lihat tabel data"):
        st.dataframe(monthly)

# ----------------------------------------------------------------- TAB 3
with tab3:
    st.subheader("Performa pengiriman per state")
    min_orders = st.slider("Minimal jumlah pesanan per state (agar hasil stabil)", 1, 500, 100)
    state_df = create_state_df(df)
    ranked = state_df[state_df["orders"] >= min_orders].sort_values("avg_delivery_days")
    if ranked.empty:
        st.warning("Tidak ada state yang memenuhi batas minimal pesanan.")
    else:
        worst5 = set(ranked.nlargest(5, "avg_delivery_days")["customer_state"])
        colors = [RED if s in worst5 else GREY for s in ranked["customer_state"]]
        fig, axes = plt.subplots(1, 2, figsize=(13, max(4, len(ranked) * 0.32)), sharey=True)
        axes[0].barh(ranked["customer_state"], ranked["avg_delivery_days"], color=colors)
        axes[0].axvline(order_df["delivery_days"].mean(), color="#333", linestyle="--", linewidth=1)
        axes[0].set_xlabel("Rata-rata durasi kirim (hari)")
        axes[1].barh(ranked["customer_state"], ranked["late_pct"], color=colors)
        axes[1].axvline(order_df["is_late"].mean() * 100, color="#333", linestyle="--", linewidth=1)
        axes[1].set_xlabel("Pesanan terlambat (%)")
        sns.despine(left=True)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        st.caption("Merah = 5 state dengan durasi kirim terlama. Garis putus-putus = rata-rata dari data terfilter.")
        with st.expander("Lihat tabel data"):
            st.dataframe(ranked.sort_values("avg_delivery_days", ascending=False))

# ----------------------------------------------------------------- TAB 4
with tab4:
    st.subheader("Segmentasi pelanggan (RFM, manual grouping)")
    st.caption("Catatan: segmen dihitung ulang dari data yang sudah difilter. Tanggal acuan (sehari setelah pembelian terakhir pada data terfilter) "
               "dan persentil 75 belanja ikut berubah mengikuti filter, sehingga jumlah pelanggan dan persentase tiap segmen dapat berbeda dari analisis pada notebook.")
    st.markdown("**Aturan:** Loyal = ≥2 pesanan · High-Value Recent = 1 pesanan, ≤180 hari, belanja ≥ persentil 75 · "
                "New = 1 pesanan, ≤180 hari · Need Attention = 181–365 hari · Lost = >365 hari.")
    rfm = create_rfm_df(df)
    seg = (rfm.groupby("segment").agg(customers=("customer_unique_id", "count"), total=("monetary", "sum"),
                                      avg_recency=("recency", "mean"), avg_monetary=("monetary", "mean")).reset_index())
    seg["pct_customers"] = seg["customers"] / seg["customers"].sum() * 100
    seg["pct_revenue"] = seg["total"] / seg["total"].sum() * 100
    order = [s for s in ["High-Value Recent", "New Customer", "Need Attention", "Lost Customer", "Loyal Customer"] if s in set(seg["segment"])]
    seg = seg.set_index("segment").loc[order].reset_index()
    palette = {"High-Value Recent": BLUE, "New Customer": "#9BB7C9", "Need Attention": ORANGE, "Lost Customer": RED, "Loyal Customer": GREEN}
    cols = [palette[s] for s in seg["segment"]]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5), sharey=True)
    for ax, col, title in [(axes[0], "pct_customers", "Porsi pelanggan (%)"), (axes[1], "pct_revenue", "Kontribusi revenue (%)")]:
        ax.barh(seg["segment"], seg[col], color=cols)
        for i, v in enumerate(seg[col]):
            ax.text(v + 0.4, i, f"{fmt(v, 1)}%", va="center")
        ax.set_title(title, loc="left")
    axes[0].invert_yaxis()
    sns.despine(left=True)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
    st.dataframe(seg.rename(columns={"total": "total_monetary"}))
