import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# ✅ Local data path on your PC
DATA_DIR = r"C:\Users\PC\OneDrive\Desktop\sqlprojectwithGENAI\data"
CUSTOMERS_CSV = os.path.join(DATA_DIR, "CUSTOMERS.csv")
INVENTORY_CSV = os.path.join(DATA_DIR, "INVENTORY.csv")
SALES_CSV = os.path.join(DATA_DIR, "SALES.csv")

st.set_page_config(page_title="GenAI Data Migration Dashboard", layout="wide")
st.title("GenAI-Assisted Data Migration — Retail Dashboard")
st.markdown("Interactive dashboard showing KPIs and charts from your migrated MySQL/CSV data.")

@st.cache_data
def load_data():
    customers = pd.read_csv(CUSTOMERS_CSV) if os.path.exists(CUSTOMERS_CSV) else pd.DataFrame()
    inventory = pd.read_csv(INVENTORY_CSV) if os.path.exists(INVENTORY_CSV) else pd.DataFrame()
    sales = pd.read_csv(SALES_CSV) if os.path.exists(SALES_CSV) else pd.DataFrame()

    # Normalize column names
    customers.columns = [c.strip() for c in customers.columns]
    inventory.columns = [c.strip() for c in inventory.columns]
    sales.columns = [c.strip() for c in sales.columns]

    # Parse dates
    if "sale_date" in sales.columns:
        sales["sale_date"] = pd.to_datetime(sales["sale_date"], errors="coerce")
    if "join_date" in customers.columns:
        customers["join_date"] = pd.to_datetime(customers["join_date"], errors="coerce")

    # Numeric columns
    if "total_amount" in sales.columns:
        sales["total_amount"] = pd.to_numeric(sales["total_amount"], errors="coerce").fillna(0)
    if "quantity" in sales.columns:
        sales["quantity"] = pd.to_numeric(sales["quantity"], errors="coerce").fillna(0)
    if "price_per_unit" in inventory.columns:
        inventory["price_per_unit"] = pd.to_numeric(inventory["price_per_unit"], errors="coerce").fillna(0)
    if "quantity_in_stock" in inventory.columns:
        inventory["quantity_in_stock"] = pd.to_numeric(inventory["quantity_in_stock"], errors="coerce").fillna(0)

    return customers, inventory, sales

customers, inventory, sales = load_data()

# Sidebar controls
st.sidebar.header("Controls")
if not sales.empty:
    min_date = sales["sale_date"].min()
    max_date = sales["sale_date"].max()
    date_range = st.sidebar.date_input("Sale date range", value=(min_date, max_date))
else:
    date_range = None

if "category" in inventory.columns:
    categories = inventory["category"].dropna().unique().tolist()
    categories.insert(0, "All")
    category_filter = st.sidebar.selectbox("Product category", options=categories)
else:
    category_filter = None

st.sidebar.markdown("---")
st.sidebar.markdown("Data files loaded from `data/`. Make sure CSVs are present there.")

# KPI row
col1, col2, col3, col4 = st.columns(4)
total_sales = sales["total_amount"].sum() if not sales.empty else 0
num_customers = customers.shape[0]
num_products = inventory.shape[0]
total_transactions = sales.shape[0]

col1.metric("Total Sales", f"{total_sales:,.2f}")
col2.metric("Customers", f"{num_customers}")
col3.metric("Products", f"{num_products}")
col4.metric("Transactions", f"{total_transactions}")

st.markdown("---")

# Monthly sales trend
st.header("📈 Monthly Sales Trend")
if not sales.empty:
    df_sales = sales.copy()
    df_sales = df_sales.dropna(subset=["sale_date"]) 
    df_sales["sale_month"] = df_sales["sale_date"].dt.to_period('M').dt.to_timestamp()
    monthly = df_sales.groupby("sale_month")["total_amount"].sum().reset_index()

    fig = px.line(monthly, x="sale_month", y="total_amount", title="Monthly Sales")
    st.plotly_chart(fig, use_container_width=True)

    monthly["ma3"] = monthly["total_amount"].rolling(3, min_periods=1).mean()
    fig2 = px.line(monthly, x="sale_month", y=["total_amount","ma3"], 
                   labels={"value":"Amount","sale_month":"Month"}, 
                   title="Sales vs 3-month Moving Average")
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("No sales data available to plot.")

# Top customers
st.header("👤 Top Customers by Revenue")
if not sales.empty and not customers.empty:
    top_cust = sales.groupby("customer_id")["total_amount"].sum().reset_index()
    top_cust = top_cust.merge(customers, on="customer_id", how="left")
    top_cust = top_cust.sort_values("total_amount", ascending=False).head(10)
    fig3 = px.bar(top_cust, x="customer_name", y="total_amount", title="Top Customers")
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("Customers or sales data missing.")

# Top products
st.header("📦 Top Products by Revenue")
if not sales.empty and not inventory.empty:
    top_prod = sales.groupby("product_id")["total_amount"].sum().reset_index()
    top_prod = top_prod.merge(inventory, on="product_id", how="left")
    top_prod = top_prod.sort_values("total_amount", ascending=False).head(10)
    fig4 = px.bar(top_prod, x="product_name", y="total_amount", title="Top Products")
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.info("Inventory or sales data missing.")

# Low stock
st.header("⚠️ Low Stock Products (<100 qty)")
if not inventory.empty:
    low_stock = inventory[inventory["quantity_in_stock"] < 100].sort_values("quantity_in_stock")
    st.dataframe(low_stock)
    st.download_button("Download low stock CSV", low_stock.to_csv(index=False).encode('utf-8'), file_name="low_stock.csv")
else:
    st.info("Inventory data missing.")

# Quick tests
st.header("🧪 Quick Data Quality Checks")
if st.button("1. Rows count (CSV files)"):
    st.json({
        "customers_rows": int(customers.shape[0]),
        "inventory_rows": int(inventory.shape[0]),
        "sales_rows": int(sales.shape[0])
    })

if st.button("2. Sales with missing customers"):
    if not sales.empty and not customers.empty:
        missing = sales[~sales["customer_id"].isin(customers["customer_id"])][["sale_id","customer_id"]]
        st.dataframe(missing)
    else:
        st.info("Need both sales and customers data.")

if st.button("3. Negative sales amounts"):
    neg = sales[sales["total_amount"] < 0][["sale_id","total_amount"]]
    if not neg.empty:
        st.dataframe(neg)
    else:
        st.success("✅ No negative sales found")

st.markdown("---")
st.write("📌 Report generated from GenAI-assisted migration. Use Power BI for advanced visuals; this dashboard is for quick validation.")
