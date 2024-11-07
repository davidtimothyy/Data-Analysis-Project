import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

customers = pd.read_csv(r"D:\Python\E-Commerce Public Dataset\customers_dataset.csv", delimiter=",")
geolocation = pd.read_csv(r"D:\Python\E-Commerce Public Dataset\geolocation_dataset.csv", delimiter=",")
order_items = pd.read_csv(r"D:\Python\E-Commerce Public Dataset\order_items_dataset.csv", delimiter=",")
order_payments = pd.read_csv(r"D:\Python\E-Commerce Public Dataset\order_payments_dataset.csv", delimiter=",")
order_reviews = pd.read_csv(r"D:\Python\E-Commerce Public Dataset\order_reviews_dataset.csv", delimiter=",")
orders = pd.read_csv(r"D:\Python\E-Commerce Public Dataset\orders_dataset.csv", delimiter=",")
product_category_translation = pd.read_csv(r"D:\Python\E-Commerce Public Dataset\product_category_name_translation.csv", delimiter=",")
products = pd.read_csv(r"D:\Python\E-Commerce Public Dataset\products_dataset.csv", delimiter=",")
sellers = pd.read_csv(r"D:\Python\E-Commerce Public Dataset\sellers_dataset.csv", delimiter=",")

orders['order_purchase_timestamp'] = pd.to_datetime(orders['order_purchase_timestamp'])

min_date = orders['order_purchase_timestamp'].min()
max_date = orders['order_purchase_timestamp'].max()

with st.sidebar:

    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

filtered_orders = orders[(orders['order_purchase_timestamp'] >= pd.to_datetime(start_date)) & 
                         (orders['order_purchase_timestamp'] <= pd.to_datetime(end_date))]

filtered_order_items = order_items.merge(filtered_orders[['order_id']], on='order_id')

consolidated_data = geolocation.groupby('geolocation_zip_code_prefix').agg({
    'geolocation_lat': 'mean', 
    'geolocation_lng': 'mean',  
    'geolocation_city': lambda x: x.mode()[0]  
}).reset_index()

products_translated = products.merge(product_category_translation, on='product_category_name', how='left')

# 1. Penjualan Berdasarkan Kategori Produk
sales_by_category = filtered_order_items.merge(products_translated, on='product_id').groupby('product_category_name_english').agg({
    'price': 'sum',  
    'order_item_id': 'count'  
}).rename(columns={'price': 'total_sales', 'order_item_id': 'items_sold'}).sort_values(by='total_sales', ascending=False)

# 2. Distribusi Pelanggan Berdasarkan Kota
customer_location = customers.merge(consolidated_data, left_on='customer_zip_code_prefix', right_on='geolocation_zip_code_prefix', how='left')
orders_by_city = customer_location['geolocation_city'].value_counts()

# 3. Performa Penjual
seller_performance = filtered_order_items.merge(sellers, on='seller_id').merge(order_reviews, on='order_id')
seller_sales_reviews = seller_performance.groupby('seller_id').agg({
    'price': 'sum',       
    'review_score': 'mean' 
}).rename(columns={'price': 'total_sales', 'review_score': 'avg_review_score'}).sort_values(by='total_sales', ascending=False)

# 4. Distribusi Skor Ulasan untuk Pesanan yang Dibatalkan
reviews_orders = order_reviews.merge(filtered_orders, on='order_id')
canceled_reviews = reviews_orders[reviews_orders['order_status'] == 'canceled']
avg_review_score_canceled = canceled_reviews['review_score'].mean()

# 5. Distribusi dan Rata-rata Skor Ulasan Berdasarkan Metode Pembayaran
filtered_payments = order_payments.merge(filtered_orders[['order_id']], on='order_id')
payment_method_counts = filtered_payments['payment_type'].value_counts()
payment_reviews = filtered_payments.merge(order_reviews, on='order_id')
avg_review_score_by_payment = payment_reviews.groupby('payment_type')['review_score'].mean()

st.title('Dashboard Analisis Data E-Commerce')
st.markdown('Visualisasi untuk Menjawab Pertanyaan Bisnis Berdasarkan Data E-Commerce')

# 1. Penjualan Berdasarkan Kategori Produk (Top 20)
st.header('1. Penjualan Berdasarkan Kategori Produk (Top 20)')
top_20_sales = sales_by_category.head(20)
fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(x=top_20_sales.index, y=top_20_sales['total_sales'], palette="viridis", ax=ax)
for p in ax.patches:
    ax.annotate(f'{p.get_height():,.0f}', 
                (p.get_x() + p.get_width() / 2., p.get_height()), 
                xytext=(0, 5), 
                textcoords='offset points', 
                ha='center', va='bottom', 
                fontsize=10, color='black')
ax.set_xticklabels(ax.get_xticklabels(), rotation=50, ha='right')
ax.set_title('Penjualan Berdasarkan Kategori Produk (Top 20)', fontsize=14)
ax.set_xlabel('Kategori Produk (English)', fontsize=12)
ax.set_ylabel('Total Penjualan', fontsize=12)
st.pyplot(fig)

# 2. Distribusi Pelanggan Berdasarkan Kota (Top 10)
st.header('2. 10 Kota dengan Pelanggan Terbanyak')
top_cities = orders_by_city.head(10)
fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(x=top_cities.index, y=top_cities.values, palette="magma", ax=ax)
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
ax.set_title('10 Kota dengan Pelanggan Terbanyak', fontsize=14)
ax.set_xlabel('Kota', fontsize=12)
ax.set_ylabel('Jumlah Pelanggan', fontsize=12)
st.pyplot(fig)

# 3. Performa Penjual Berdasarkan Penjualan dan Skor Ulasan
st.header('3. Performa Penjual Berdasarkan Penjualan dan Skor Ulasan')
top_sellers = seller_sales_reviews.head(10)
fig, ax = plt.subplots(figsize=(10, 6))
sns.scatterplot(data=top_sellers, x='total_sales', y='avg_review_score', hue='avg_review_score', palette="cool", size='total_sales', sizes=(20, 200), legend=False, ax=ax)
ax.set_title('Performa Penjual Berdasarkan Penjualan dan Skor Ulasan', fontsize=14)
ax.set_xlabel('Total Penjualan', fontsize=12)
ax.set_ylabel('Rata-rata Skor Ulasan', fontsize=12)
st.pyplot(fig)

# 4. Distribusi Skor Ulasan Berdasarkan Status Pesanan
st.header('4. Distribusi Skor Ulasan Berdasarkan Status Pesanan')
fig, ax = plt.subplots(figsize=(10, 6))
sns.boxplot(data=reviews_orders, x='order_status', y='review_score', palette="Set2", ax=ax)
ax.set_title('Distribusi Skor Ulasan Berdasarkan Status Pesanan', fontsize=14)
ax.set_xlabel('Status Pesanan', fontsize=12)
ax.set_ylabel('Skor Ulasan', fontsize=12)
st.pyplot(fig)
st.write(f"Rata-rata skor ulasan untuk pesanan yang dibatalkan: {avg_review_score_canceled:.2f}")

# 5. Distribusi dan Rata-rata Skor Ulasan Berdasarkan Metode Pembayaran
st.header('5. Distribusi dan Rata-rata Skor Ulasan Berdasarkan Metode Pembayaran')
fig, axes = plt.subplots(1, 2, figsize=(18, 6))
sns.barplot(x=payment_method_counts.index, y=payment_method_counts.values, palette="pastel", ax=axes[0])
axes[0].set_title('Distribusi Metode Pembayaran', fontsize=14)
axes[0].set_xlabel('Metode Pembayaran', fontsize=12)
axes[0].set_ylabel('Jumlah Penggunaan', fontsize=12)
axes[0].tick_params(axis='x', rotation=45)
sns.barplot(x=avg_review_score_by_payment.index, y=avg_review_score_by_payment.values, palette="coolwarm", ax=axes[1])
axes[1].set_title('Rata-rata Skor Ulasan Berdasarkan Metode Pembayaran', fontsize=14)
axes[1].set_xlabel('Metode Pembayaran', fontsize=12)
axes[1].set_ylabel('Rata-rata Skor Ulasan', fontsize=12)
axes[1].tick_params(axis='x', rotation=45)
st.pyplot(fig)
