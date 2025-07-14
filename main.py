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

# --- Sidebar Branding & Logo ---
with st.sidebar:
    logo_path = "data/logo_ssdc.png"
    if os.path.exists(logo_path):
        st.image(logo_path, width=120, caption="SSDC 2025", output_format="PNG")
    st.markdown("<h4 style='text-align:center; color:#1a237e;'>SSDC 2025 E-Commerce Dashboard</h4>", unsafe_allow_html=True)

# --- Sidebar Navigation ---
page = st.sidebar.selectbox("📌 Pilih Halaman", [
    "1. Executive Summary",
    "2. Purchase & Payment Analysis",
    "3. Delivery & Satisfaction",
    "4. Product Insight",
    "5. Market Geography",
    "6. Business Recommendations"
])

# --- Fungsi Load ---
@st.cache_data
def load_data(file_name):
    return pd.read_csv(os.path.join("data", file_name))

# --- 1. Executive Summary ---
if page == "1. Executive Summary":
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
elif page == "2. Purchase & Payment Analysis":
    st.subheader("\U0001F4B3 Analisis Pembayaran dan Pembelian")
    payments = load_data("order_payments_dataset.csv")

    tab1, tab2 = st.tabs(["Distribusi Pembayaran", "Pola Cicilan"])
    with tab1:
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

    with tab2:
        cicilan_df = payments["payment_installments"].value_counts().sort_index().reset_index()
        cicilan_df.columns = ["payment_installments", "count"]
        fig2 = px.bar(
            cicilan_df,
            x="payment_installments",
            y="count",
            labels={"payment_installments": "Jumlah Cicilan", "count": "Jumlah Transaksi"},
            title="Jumlah Cicilan yang Dipilih",
            text_auto=True,
            hover_data={"payment_installments": True, "count": True}
        )
        fig2.update_traces(marker_color="seagreen", hovertemplate='Cicilan %{x}: %{y} transaksi<extra></extra>')
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("""
    **Insight:**
    - Sebagian besar transaksi dibayar tunai atau dengan cicilan ringan.
    - Peluang untuk **meningkatkan AOV** dengan promosi cicilan.

    **Rekomendasi:**
    - Perbanyak promosi cicilan 3–6x.
    - Segmentasi pelanggan berdasarkan kemampuan bayar.
    """)

# --- 3. Delivery & Satisfaction ---
elif page == "3. Delivery & Satisfaction":
    st.subheader("\U0001F69A Keterlambatan & Kepuasan Pelanggan")

    orders = load_data("orders_dataset.csv")
    reviews = load_data("order_reviews_dataset.csv")
    merged = orders.merge(reviews, on="order_id")
    merged['delay'] = (pd.to_datetime(merged['order_delivered_customer_date']) -
                       pd.to_datetime(merged['order_estimated_delivery_date'])).dt.days
    merged = merged.dropna(subset=['delay', 'review_score'])

    fig = px.box(
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
    fig.update_traces(jitter=0.3, marker_opacity=0.5)
    st.plotly_chart(fig, use_container_width=True)

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
elif page == "4. Product Insight":
    st.subheader("📦 Analisis Produk dan Review")
    items = load_data("order_items_dataset.csv")
    products = load_data("products_dataset.csv")
    reviews = load_data("order_reviews_dataset.csv")
    prod_cat = load_data("product_category_name_translation.csv")
    customers = load_data("customers_dataset.csv")
    # Cleaning kolom
    items = clean_column_names(items)
    products = clean_column_names(products)
    reviews = clean_column_names(reviews)
    prod_cat = clean_column_names(prod_cat)
    customers = clean_column_names(customers)
    # Merge
    df = items.merge(products, on="product_id").merge(reviews, on="order_id")
    df = df.merge(prod_cat, on="product_category_name", how="left")
    df = drop_missing(df)

    tab1, tab2, tab3 = st.tabs([
        "Top 10 Kategori Produk (Penjualan)",
        "Top 10 Kota Pelanggan (Penjualan)",
        "Review vs Berat/Deskripsi"
    ])

    with tab1:
        top_cat = df.groupby("product_category_name_english")["price"].sum().sort_values(ascending=False).head(10)
        top_cat_df = top_cat.reset_index().sort_values("price")  # urutkan agar bar horizontal dari bawah ke atas
        fig = px.bar(
            top_cat_df,
            x="price",
            y="product_category_name_english",
            orientation='h',
            labels={'price': 'Total Penjualan (R$)', 'product_category_name_english': 'Kategori Produk'},
            title="Top 10 Kategori Produk berdasarkan Penjualan",
            text_auto=True,
            hover_data={"price": True, "product_category_name_english": True}
        )
        fig.update_traces(marker_color='royalblue', hovertemplate='%{y}: %{x}<extra></extra>')
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        # Pastikan kolom customer_id ada di df, jika tidak, ambil dari orders
        if 'customer_id' not in df.columns:
            orders = load_data("orders_dataset.csv")
            orders = clean_column_names(orders)
            df = df.merge(orders[['order_id', 'customer_id']], on='order_id', how='left')
        df_cust = df.merge(customers, on="customer_id", how="left")
        price_col = 'price' if 'price' in df_cust.columns else df_cust.columns[df_cust.columns.str.contains('price')][0]
        top_city = df_cust.groupby("customer_city")[price_col].sum().sort_values(ascending=False).head(10)
        top_city_df = top_city.reset_index().sort_values(price_col)
        fig2 = px.bar(
            top_city_df,
            x=price_col,
            y="customer_city",
            orientation='h',
            labels={price_col: 'Total Penjualan (R$)', 'customer_city': 'Kota Pelanggan'},
            title="Top 10 Kota berdasarkan Penjualan",
            text_auto=True,
            hover_data={price_col: True, "customer_city": True}
        )
        fig2.update_traces(marker_color='seagreen', hovertemplate='%{y}: %{x}<extra></extra>')
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        fig3 = px.scatter(df, x="product_weight_g", y="review_score", title="Review vs Berat Produk",
                         labels={"product_weight_g": "Berat Produk (g)", "review_score": "Review Score"},
                         hover_data=df.columns)
        st.plotly_chart(fig3, use_container_width=True)
        fig4 = px.scatter(df, x="product_description_lenght", y="review_score", title="Review vs Panjang Deskripsi", 
                         labels={"product_description_lenght": "Panjang Deskripsi", "review_score": "Review Score"},
                         hover_data=df.columns)
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("""
    **Insight:**
    - Kategori dan kota tertentu mendominasi penjualan.
    - Produk lebih berat cenderung memiliki risiko review lebih rendah.
    - Deskripsi yang lebih panjang berpotensi menaikkan kepuasan.

    **Rekomendasi:**
    - Fokus promosi pada kategori/kota top.
    - Perbaiki deskripsi dan foto produk.
    - Kurasi ulang kategori berat ekstrem.
    """)

# --- 5. Market Geography ---
elif page == "5. Market Geography":
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
elif page == "6. Business Recommendations":
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
