import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pydeck as pdk
import os
from utils import clean_column_names, drop_missing, plot_bar_top, plot_scatter
import plotly.express as px

# --- Page Setup ---
st.set_page_config(page_title="SSDC 2025 E-Commerce Dashboard", layout="wide")
st.title("📊 E-Commerce Business Insight - SSDC 2025")
st.markdown("Dashboard ini dirancang untuk memberikan insight mendalam dari data transaksi e-commerce untuk mendukung pengambilan keputusan strategis.")

# --- Branding & Logo ---
logo_path = "data/logo_ssdc.png"
if os.path.exists(logo_path):
    st.image(logo_path, width=120, caption="SSDC 2025", output_format="PNG")
st.markdown("<h4 style='text-align:center; color:#1a237e;'>SSDC 2025 E-Commerce Dashboard</h4>", unsafe_allow_html=True)

# --- Fungsi Load ---
@st.cache_data
def load_data(file_name):
    return pd.read_csv(os.path.join("data", file_name))

# --- 1. Executive Summary ---
st.subheader("📈 Executive Summary")
st.markdown("""
Dataset ini mencakup lebih dari 100.000 transaksi dari platform e-commerce Brasil, dengan informasi:

- Pembayaran dan jenis cicilan
- Ongkos kirim dan harga barang
- Ulasan pelanggan
- Lokasi pelanggan dan penjual
- Kategori dan karakteristik produk

**Tujuan Analisis:**
- Meningkatkan pengalaman pembeli
- Mengoptimalkan strategi produk dan promosi
- Mengidentifikasi pasar potensial
""")

# --- 2. Purchase & Payment ---
st.subheader("\U0001F4B3 Analisis Pembayaran dan Pembelian")
payments = load_data("order_payments_dataset.csv")

fig = px.histogram(
    payments,
    x="payment_value",
    nbins=30,
    color_discrete_sequence=["skyblue"],
    title="Distribusi Nilai Pembayaran",
    labels={"payment_value": "Nilai Pembayaran (R$)"},
    hover_data=payments.columns
)
fig.update_traces(marker_line_color="black", marker_line_width=1)
st.plotly_chart(fig, use_container_width=True)

st.markdown("""
**Insight:**
- Sebagian besar transaksi dibayar tunai atau dengan cicilan ringan.
- Peluang untuk **meningkatkan AOV** dengan promosi cicilan.

**Rekomendasi:**
- Perbanyak promosi cicilan 3–6x.
- Segmentasi pelanggan berdasarkan kemampuan bayar.
""")

# --- 3. Delivery & Satisfaction ---
st.subheader("\U0001F69A Keterlambatan & Kepuasan Pelanggan")
orders = load_data("orders_dataset.csv")
reviews = load_data("order_reviews_dataset.csv")
merged = orders.merge(reviews, on="order_id")
merged['delay'] = (pd.to_datetime(merged['order_delivered_customer_date']) -
                   pd.to_datetime(merged['order_estimated_delivery_date'])).dt.days
merged = merged.dropna(subset=['delay', 'review_score'])
merged = merged[merged['delay'] >= 0]  # hanya ambil yang terlambat atau tepat waktu


fig3 = px.box(
    merged,
    x="review_score",
    y="delay",
    points="all",
    color="review_score",
    color_discrete_sequence=px.colors.qualitative.Set2,
    title="Keterlambatan vs Skor Review",
    labels={"review_score": "Skor Review", "delay": "Keterlambatan (hari)"},
    hover_data=merged.columns
)
fig3.update_traces(jitter=0.3, marker_opacity=0.5)
st.plotly_chart(fig3, use_container_width=True)

corr = merged[['delay', 'review_score']].corr().iloc[0, 1]
st.markdown(f"**Korelasi antara delay & review:** `{corr:.2f}`")

st.markdown("""
**Insight:**
- Keterlambatan signifikan berdampak pada review buruk.

**Rekomendasi:**
- Optimalkan estimasi pengiriman.
- Beri kompensasi saat delay terjadi.
""")

# --- 4. Product Insight ---
st.subheader("📦 Analisis Produk dan Review")
items = load_data("order_items_dataset.csv")
products = load_data("products_dataset.csv")
reviews = load_data("order_reviews_dataset.csv")
prod_cat = load_data("product_category_name_translation.csv")
# Cleaning kolom
items = clean_column_names(items)
products = clean_column_names(products)
reviews = clean_column_names(reviews)
prod_cat = clean_column_names(prod_cat)
# Merge
df = items.merge(products, on="product_id").merge(reviews, on="order_id")
df = df.merge(prod_cat, on="product_category_name", how="left")
df = drop_missing(df)

# Top 10 Kategori Produk (Penjualan)
top_cat = df.groupby("product_category_name_english")["price"].sum().sort_values(ascending=False).head(10)
top_cat_df = top_cat.reset_index().sort_values("price")
fig4 = px.bar(
    top_cat_df,
    x="price",
    y="product_category_name_english",
    orientation='h',
    labels={'price': 'Total Penjualan (R$)', 'product_category_name_english': 'Kategori Produk'},
    title="Top 10 Kategori Produk berdasarkan Penjualan",
    text_auto=True,
    hover_data={"price": True, "product_category_name_english": True}
)
fig4.update_traces(marker_color='royalblue', hovertemplate='%{y}: %{x}<extra></extra>')
st.plotly_chart(fig4, use_container_width=True)

st.markdown("""
**Insight:**
- Kategori tertentu mendominasi penjualan.
- Deskripsi yang lebih panjang berpotensi menaikkan kepuasan.

**Rekomendasi:**
- Fokus promosi pada kategori top.
- Perbaiki deskripsi dan foto produk.
- Kurasi ulang kategori berat ekstrem.
""")

# --- 5. Market Geography ---
st.subheader("\U0001F5FA\uFE0F Persebaran Pelanggan")
customers = load_data("customers_dataset.csv")
geo = load_data("geolocation_dataset.csv")

geo_group = geo.groupby('geolocation_zip_code_prefix').agg({
    'geolocation_lat': 'mean',
    'geolocation_lng': 'mean'
}).reset_index()

cust_geo = customers.merge(geo_group, left_on='customer_zip_code_prefix', right_on='geolocation_zip_code_prefix', how='left')
cust_geo = cust_geo.dropna(subset=['geolocation_lat', 'geolocation_lng'])

fig_map = px.scatter_mapbox(
    cust_geo.sample(n=min(2000, len(cust_geo)), random_state=42),
    lat="geolocation_lat",
    lon="geolocation_lng",
    hover_name="customer_city",
    hover_data={"customer_state": True, "customer_id": False},
    color_discrete_sequence=["royalblue"],
    zoom=3.5,
    height=500,
    title="Persebaran Pelanggan di Brasil"
)
fig_map.update_layout(mapbox_style="carto-positron", margin={"r":0,"t":40,"l":0,"b":0})
st.plotly_chart(fig_map, use_container_width=True)

st.markdown("""
**Insight:**
- Sebaran pelanggan terkonsentrasi di wilayah perkotaan besar.
- Wilayah tertentu menunjukkan potensi pertumbuhan.

**Rekomendasi:**
- Target promosi wilayah padat.
- Eksplorasi wilayah dengan penetrasi rendah.
""")

# --- 6. Business Recommendations ---
st.subheader("🧠 Rekomendasi Strategis")
st.markdown("""
Berdasarkan keseluruhan insight:

1. **Ongkos Kirim:** Subsidi ongkir atau pembulatan biaya untuk mendorong review positif.
2. **Cicilan:** Tambahkan opsi cicilan 3-6 bulan untuk segmen menengah.
3. **Deskripsi Produk:** Panjang dan detail deskripsi memiliki dampak positif terhadap review.
4. **Keterlambatan:** Perbaikan estimasi pengiriman, atau sistem kompensasi.
5. **Pasar Baru:** Promosi khusus untuk wilayah dengan penetrasi rendah namun padat penduduk.

Semua strategi ini bertujuan untuk **meningkatkan kepuasan, memperluas pasar**, dan **menaikkan konversi penjualan**.
""")

# --- Analisis Pengaruh Status Order ---
st.subheader("📉 Analisis Order Sukses vs Gagal & Faktor Penyebab")

orders = load_data("orders_dataset.csv")
items = load_data("order_items_dataset.csv")

# Gabungkan harga per order
total_price = items.groupby("order_id")["price"].sum().reset_index()
orders_price = orders.merge(total_price, on="order_id", how="left")

# Kategorikan status: sukses vs gagal
orders_price["order_status_group"] = orders_price["order_status"].apply(lambda x: "Sukses" if x=="delivered" else "Tidak Sukses")

# 1. Distribusi harga produk per status order
fig_status_price = px.box(
    orders_price,
    x="order_status_group",
    y="price",
    color="order_status_group",
    points="outliers",
    title="Distribusi Harga Produk per Status Order",
    labels={"order_status_group": "Status Order", "price": "Total Harga per Order (R$)"}
)
st.plotly_chart(fig_status_price, use_container_width=True)

st.markdown("""
**Insight tambahan:**
- Order yang gagal cenderung memiliki harga lebih rendah (atau sebaliknya, bisa dilihat dari boxplot).
- Analisis lebih lanjut bisa dilakukan dengan menambahkan jarak seller-customer jika dibutuhkan.
""")

# --- Analisis Lanjutan Order Gagal: Ongkir, Kategori, Jumlah Item ---
st.subheader("🔎 Faktor Lain Order Gagal: Ongkir, Kategori, Jumlah Item")

# Gabung ongkir per order
total_freight = items.groupby("order_id")["freight_value"].sum().reset_index()
orders_freight = orders.merge(total_freight, on="order_id", how="left")
orders_freight["order_status_group"] = orders_freight["order_status"].apply(lambda x: "Sukses" if x=="delivered" else "Tidak Sukses")

fig_freight = px.box(
    orders_freight,
    x="order_status_group",
    y="freight_value",
    color="order_status_group",
    points="outliers",
    title="Distribusi Ongkos Kirim per Status Order",
    labels={"order_status_group": "Status Order", "freight_value": "Total Ongkir per Order (R$)"}
)
st.plotly_chart(fig_freight, use_container_width=True)

# Kategori produk pada order gagal
items_status = items.merge(orders[["order_id", "order_status"]], on="order_id", how="left")
items_status["order_status_group"] = items_status["order_status"].apply(lambda x: "Sukses" if x=="delivered" else "Tidak Sukses")
cat_fail = items_status[items_status["order_status_group"]=="Tidak Sukses"]["product_id"].value_counts().head(10)
st.markdown("**Top 10 Produk pada Order Gagal:**")
st.write(cat_fail)

# Jumlah item per order
item_count = items.groupby("order_id").size().reset_index(name="item_count")
orders_itemcount = orders.merge(item_count, on="order_id", how="left")
orders_itemcount["order_status_group"] = orders_itemcount["order_status"].apply(lambda x: "Sukses" if x=="delivered" else "Tidak Sukses")
fig_item = px.box(
    orders_itemcount,
    x="order_status_group",
    y="item_count",
    color="order_status_group",
    points="outliers",
    title="Distribusi Jumlah Item per Order berdasarkan Status",
    labels={"order_status_group": "Status Order", "item_count": "Jumlah Item per Order"}
)
st.plotly_chart(fig_item, use_container_width=True)

st.markdown("""
**Insight tambahan:**
- Cek apakah ongkir tinggi, jumlah item, atau produk tertentu lebih sering muncul pada order gagal.
- Jika tidak ada pola signifikan, kemungkinan faktor eksternal (stok, pembayaran, dsb).
""")
