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

# --- Insight Bisnis Utama Berdasarkan Dataset ---
st.markdown("""
#### Insight Bisnis Utama
- **⬆️ Meningkatkan penjualan:** Analisis kategori produk, metode pembayaran, dan nilai transaksi untuk mengetahui produk/layanan dan metode pembayaran yang paling berkontribusi pada penjualan.
- **😊 Kepuasan pelanggan:** Evaluasi pengaruh ongkir, keterlambatan, dan harga terhadap review buruk untuk meningkatkan kepuasan pelanggan.
- **🌍 Perluasan pasar:** Identifikasi kota/provinsi dengan konsentrasi pelanggan tinggi dan wilayah yang masih kosong untuk strategi ekspansi.
- **🎯 Produk yang lebih relevan:** Temukan kategori produk yang paling banyak dibeli dan mendapat review bagus untuk pengembangan produk.
- **💡 Preferensi pembeli:** Analisis preferensi metode pembayaran/cicilan dan produk dengan review tinggi untuk segmentasi promosi.
- **✅ Kualitas produk:** Tinjau pengaruh panjang deskripsi dan jumlah foto produk terhadap review untuk meningkatkan kualitas konten produk.
- **🚚 Kinerja pengiriman:** Analisis dampak keterlambatan dan ongkir terhadap review untuk perbaikan logistik dan pengalaman belanja.
- **🖼️ Optimalkan konten produk:** Evaluasi apakah produk dengan konten lebih lengkap (deskripsi/foto) lebih dipilih dan mendapat review bagus untuk strategi pemasaran.
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

# Urutkan skor review
review_order = [1, 2, 3, 4, 5]
merged['review_score'] = pd.Categorical(merged['review_score'], categories=review_order, ordered=True)

fig3 = px.box(
    merged,
    x="review_score",
    y="delay",
    points="all",
    color="review_score",
    color_discrete_sequence=px.colors.qualitative.Set2,
    category_orders={"review_score": review_order},
    title="Keterlambatan vs Skor Review",
    labels={"review_score": "Skor Review", "delay": "Keterlambatan (hari)"},
    hover_data=merged.columns
)
fig3.update_traces(jitter=0.3, marker_opacity=0.5)
st.plotly_chart(fig3, use_container_width=True)

corr = merged[['delay', 'review_score']].corr().iloc[0, 1]
st.markdown(f"**Korelasi antara delay & review:** `{corr:.2f}`")

# Tampilkan total order terlambat per skor review
late_count = merged.groupby('review_score').apply(lambda x: (x['delay'] > 0).sum()).reset_index(name='Total Terlambat')
st.markdown("**Total Order Terlambat per Skor Review:**")
st.dataframe(late_count, hide_index=True)

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

# Map interaktif seluruh dunia (zoom, pan, drag bebas)
fig_map = px.scatter_mapbox(
    cust_geo.sample(n=min(2000, len(cust_geo)), random_state=42),
    lat="geolocation_lat",
    lon="geolocation_lng",
    hover_name="customer_city",
    hover_data={"customer_state": True, "customer_id": False},
    color_discrete_sequence=["royalblue"],
    zoom=2.5,  # Lebih global
    height=500,
    title="Persebaran Pelanggan di Dunia (Interaktif)"
)
fig_map.update_layout(
    mapbox_style="open-street-map",
    mapbox_zoom=3.5,
    mapbox_center={"lat": -14.2350, "lon": -51.9253},
    margin={"r": 0, "t": 40, "l": 0, "b": 0},
    dragmode="pan",                  # agar bisa langsung geser tanpa klik 2x
    uirevision='map-reset',          # agar tidak reset saat interaksi
)

# Aktifkan scroll zoom (tambahan khusus)
fig_map.update_layout(
    mapbox=dict(
        accesstoken=None,
        bearing=0,
        pitch=0,
        style="open-street-map"
    )
)

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

# --- Visualisasi Insight Bisnis Utama ---
st.markdown("""
### Visualisasi Insight Bisnis Utama
""")

# 1. Top Kategori Produk Berdasarkan Penjualan (⬆️ Meningkatkan penjualan)
st.markdown("""
**Insight:** Kategori produk dengan total penjualan tertinggi menunjukkan fokus utama bisnis dan peluang promosi.
""")
top_cat_sales = df.groupby("product_category_name_english")["price"].sum().sort_values(ascending=False).head(10)
top_cat_sales_df = top_cat_sales.reset_index().sort_values("price")
fig_top_cat = px.bar(
    top_cat_sales_df,
    x="price",
    y="product_category_name_english",
    orientation='h',
    labels={'price': 'Total Penjualan (R$)', 'product_category_name_english': 'Kategori Produk'},
    title="Top 10 Kategori Produk Berdasarkan Penjualan",
    text_auto=True,
    hover_data={"price": True, "product_category_name_english": True}
)
fig_top_cat.update_traces(marker_color='royalblue', hovertemplate='%{y}: %{x}<extra></extra>')
st.plotly_chart(fig_top_cat, use_container_width=True)
st.caption("Kategori produk dengan total penjualan tertinggi menunjukkan fokus utama bisnis dan peluang promosi.")
st.markdown("""
**Solusi:** Fokuskan promosi, bundling, dan stok pada kategori produk teratas untuk memaksimalkan penjualan dan ROI. Evaluasi kategori terbawah untuk efisiensi portofolio produk.
""")

# 2. Distribusi Metode Pembayaran (⬆️ Meningkatkan penjualan, 💡 Preferensi pembeli)
st.markdown("""
**Insight:** Metode pembayaran yang paling sering digunakan dapat menjadi acuan strategi promosi pembayaran/cicilan.
""")
payments = load_data("order_payments_dataset.csv")
pay_type = payments["payment_type"].value_counts().reset_index()
pay_type.columns = ["payment_type", "count"]
fig_pay_type = px.bar(
    pay_type,
    x="payment_type",
    y="count",
    color="payment_type",
    title="Distribusi Metode Pembayaran",
    labels={"count": "Jumlah Transaksi", "payment_type": "Metode Pembayaran"},
    text_auto=True
)
st.plotly_chart(fig_pay_type, use_container_width=True)
st.caption("Metode pembayaran yang paling sering digunakan dapat menjadi acuan strategi promosi pembayaran/cicilan.")
st.markdown("""
**Solusi:** Tawarkan promo khusus pada metode pembayaran favorit dan edukasi pelanggan tentang opsi cicilan untuk meningkatkan konversi.
""")

# 3. Boxplot Review Score vs Ongkir (😊 Kepuasan pelanggan, 🚚 Kinerja pengiriman)
st.markdown("""
**Insight:** Ongkir tinggi cenderung berasosiasi dengan review lebih rendah, penting untuk strategi subsidi ongkir.
""")
fig_review_freight = px.box(
    df,
    x="review_score",
    y="freight_value",
    color="review_score",
    category_orders={"review_score": [1,2,3,4,5]},
    title="Distribusi Ongkir per Skor Review",
    labels={"review_score": "Skor Review", "freight_value": "Ongkir (R$)"},
    points="outliers"
)
st.plotly_chart(fig_review_freight, use_container_width=True)
st.caption("Ongkir tinggi cenderung berasosiasi dengan review lebih rendah, penting untuk strategi subsidi ongkir.")
st.markdown("""
**Solusi:** Terapkan subsidi ongkir atau promo gratis ongkir pada segmen sensitif harga untuk meningkatkan kepuasan dan review positif.
""")

# 4. Boxplot Review Score vs Delay (😊 Kepuasan pelanggan, 🚚 Kinerja pengiriman)
st.markdown("""
**Insight:** Keterlambatan pengiriman berdampak signifikan pada review buruk, perlu perbaikan logistik.
""")
fig_review_delay = px.box(
    merged,
    x="review_score",
    y="delay",
    color="review_score",
    category_orders={"review_score": [1,2,3,4,5]},
    title="Keterlambatan Pengiriman per Skor Review",
    labels={"review_score": "Skor Review", "delay": "Keterlambatan (hari)"},
    points="outliers"
)
st.plotly_chart(fig_review_delay, use_container_width=True)
st.caption("Keterlambatan pengiriman berdampak signifikan pada review buruk, perlu perbaikan logistik.")
st.markdown("""
**Solusi:** Optimalkan estimasi pengiriman, monitoring real-time, dan berikan kompensasi untuk order yang terlambat agar reputasi tetap terjaga.
""")

# 5. Boxplot Review Score vs Harga (😊 Kepuasan pelanggan)
st.markdown("""
**Insight:** Harga produk dapat memengaruhi kepuasan/review, terutama pada segmen harga tertentu.
""")
fig_review_price = px.box(
    df,
    x="review_score",
    y="price",
    color="review_score",
    category_orders={"review_score": [1,2,3,4,5]},
    title="Distribusi Harga Produk per Skor Review",
    labels={"review_score": "Skor Review", "price": "Harga Produk (R$)"},
    points="outliers"
)
st.plotly_chart(fig_review_price, use_container_width=True)
st.caption("Harga produk dapat memengaruhi kepuasan/review, terutama pada segmen harga tertentu.")
st.markdown("""
**Solusi:** Lakukan segmentasi harga dan pastikan value for money pada tiap segmen. Tawarkan promo pada produk dengan review rendah di segmen harga sensitif.
""")

# 6. Top Kategori Produk dengan Review Bagus (🎯 Produk relevan)
st.markdown("""
**Insight:** Kategori produk dengan review bagus (4/5) terbanyak adalah peluang untuk pengembangan produk unggulan.
""")
top_cat_good_review = df[df["review_score"]>=4].groupby("product_category_name_english")["review_score"].count().sort_values(ascending=False).head(10)
top_cat_good_review_df = top_cat_good_review.reset_index().sort_values("review_score")
fig_top_cat_good = px.bar(
    top_cat_good_review_df,
    x="review_score",
    y="product_category_name_english",
    orientation='h',
    labels={'review_score': 'Jumlah Review Bagus (4/5)', 'product_category_name_english': 'Kategori Produk'},
    title="Top 10 Kategori Produk dengan Review Bagus",
    text_auto=True
)
st.plotly_chart(fig_top_cat_good, use_container_width=True)
st.caption("Kategori produk dengan review bagus (4/5) terbanyak adalah peluang untuk pengembangan produk unggulan.")
st.markdown("""
**Solusi:** Kembangkan dan promosikan produk di kategori dengan review bagus sebagai produk unggulan dan referensi best practice kategori lain.
""")

# 7. Kota/provinsi padat pelanggan (🌍 Perluasan pasar)
st.markdown("""
**Insight:** Kota/provinsi dengan pelanggan terbanyak adalah target utama ekspansi dan promosi.
""")
cust_city = customers["customer_city"].value_counts().head(10).reset_index()
cust_city.columns = ["customer_city", "count"]
fig_city = px.bar(
    cust_city,
    x="count",
    y="customer_city",
    orientation='h',
    title="Top 10 Kota dengan Jumlah Pelanggan Terbanyak",
    labels={"count": "Jumlah Pelanggan", "customer_city": "Kota"},
    text_auto=True
)
st.plotly_chart(fig_city, use_container_width=True)
st.caption("Kota/provinsi dengan pelanggan terbanyak adalah target utama ekspansi dan promosi.")
st.markdown("""
**Solusi:** Prioritaskan kampanye marketing dan ekspansi logistik di kota/provinsi dengan pelanggan terbanyak untuk pertumbuhan pesat.
""")

cust_state = customers["customer_state"].value_counts().head(10).reset_index()
cust_state.columns = ["customer_state", "count"]
fig_state = px.bar(
    cust_state,
    x="count",
    y="customer_state",
    orientation='h',
    title="Top 10 Provinsi dengan Jumlah Pelanggan Terbanyak",
    labels={"count": "Jumlah Pelanggan", "customer_state": "Provinsi"},
    text_auto=True
)
st.plotly_chart(fig_state, use_container_width=True)
st.caption("Provinsi dengan pelanggan terbanyak adalah target utama ekspansi dan promosi.")
st.markdown("""
**Solusi:** Perkuat distribusi dan layanan pelanggan di provinsi utama, serta lakukan riset pasar untuk ekspansi ke provinsi potensial berikutnya.
""")

# 8. Preferensi pembeli: Distribusi cicilan & review per metode pembayaran
if "installments" in payments.columns:
    st.markdown("""
    **Insight:** Distribusi cicilan memperlihatkan preferensi tenor pembayaran pelanggan.
    """)
    inst_count = payments["installments"].value_counts().sort_index().reset_index()
    inst_count.columns = ["installments", "count"]
    fig_inst = px.bar(
        inst_count,
        x="installments",
        y="count",
        title="Distribusi Jumlah Cicilan",
        labels={"count": "Jumlah Transaksi", "installments": "Jumlah Cicilan"},
        text_auto=True
    )
    st.plotly_chart(fig_inst, use_container_width=True)
    st.caption("Distribusi cicilan memperlihatkan preferensi tenor pembayaran pelanggan.")
    st.markdown("""
    **Solusi:** Sediakan opsi cicilan yang paling diminati (misal 3/6/12x) dan edukasi pelanggan tentang manfaat cicilan untuk meningkatkan AOV.
    """)

if "order_id" in payments.columns and "order_id" in df.columns:
    st.markdown("""
    **Insight:** Rata-rata skor review per metode pembayaran dapat menjadi acuan strategi pembayaran yang meningkatkan kepuasan.
    """)
    pay_review = payments.merge(df[["order_id", "review_score"]], on="order_id", how="left")
    pay_review_group = pay_review.groupby("payment_type")["review_score"].mean().reset_index()
    fig_pay_review = px.bar(
        pay_review_group,
        x="payment_type",
        y="review_score",
        color="payment_type",
        title="Rata-rata Skor Review per Metode Pembayaran",
        labels={"review_score": "Rata-rata Skor Review", "payment_type": "Metode Pembayaran"},
        text_auto=True
    )
    st.plotly_chart(fig_pay_review, use_container_width=True)
    st.caption("Rata-rata skor review per metode pembayaran dapat menjadi acuan strategi pembayaran yang meningkatkan kepuasan.")
    st.markdown("""
    **Solusi:** Dorong metode pembayaran dengan review tertinggi dan evaluasi metode dengan review rendah untuk perbaikan layanan.
    """)

# 9. Kualitas produk: Panjang deskripsi & jumlah foto vs review
if "product_description_lenght" in df.columns:
    st.markdown("""
    **Insight:** Produk dengan deskripsi lebih panjang cenderung mendapat review lebih baik.
    """)
    fig_desc_len = px.box(
        df,
        x="review_score",
        y="product_description_lenght",
        color="review_score",
        category_orders={"review_score": [1,2,3,4,5]},
        title="Panjang Deskripsi Produk per Skor Review",
        labels={"review_score": "Skor Review", "product_description_lenght": "Panjang Deskripsi"},
        points="outliers"
    )
    st.plotly_chart(fig_desc_len, use_container_width=True)
    st.caption("Produk dengan deskripsi lebih panjang cenderung mendapat review lebih baik.")
    st.markdown("""
    **Solusi:** Standarisasi panjang dan kualitas deskripsi produk minimal sesuai best practice untuk semua produk.
    """)
if "product_photos_qty" in df.columns:
    st.markdown("""
    **Insight:** Produk dengan jumlah foto lebih banyak cenderung mendapat review lebih baik.
    """)
    fig_photo_qty = px.box(
        df,
        x="review_score",
        y="product_photos_qty",
        color="review_score",
        category_orders={"review_score": [1,2,3,4,5]},
        title="Jumlah Foto Produk per Skor Review",
        labels={"review_score": "Skor Review", "product_photos_qty": "Jumlah Foto"},
        points="outliers"
    )
    st.plotly_chart(fig_photo_qty, use_container_width=True)
    st.caption("Produk dengan jumlah foto lebih banyak cenderung mendapat review lebih baik.")
    st.markdown("""
    **Solusi:** Wajibkan minimal 3-5 foto berkualitas untuk setiap produk agar meningkatkan kepercayaan dan review positif.
    """)
