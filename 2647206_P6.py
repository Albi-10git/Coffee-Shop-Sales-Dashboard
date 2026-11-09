
import streamlit as st
import pandas as pd
from pathlib import Path

# 1. PAGE SETTINGS
st.set_page_config(
    page_title="Coffee Shop Sales Dashboard",
    page_icon="☕",
    layout="wide"
)

st.title("☕ Coffee Shop Sales Analysis Dashboard")
st.write("Explore coffee shop transactions, products and sales trends.")

# 2. LOAD DATASET
DATA_FILE = Path(__file__).parent / "coffee-shop-sales-revenue-100.csv"

@st.cache_data
def load_data():
    data = pd.read_csv(DATA_FILE)
    data["transaction_date"] = pd.to_datetime(data["transaction_date"])
    data["revenue"] = data["transaction_qty"] * data["unit_price"]
    return data

try:
    df = load_data()
except FileNotFoundError:
    st.error("Dataset file not found. Keep the CSV in the same folder.")
    st.stop()

# 3. SIDEBAR FILTERS
st.sidebar.header("Filter Transactions")

date_range = st.sidebar.date_input(
    "Select date range",
    value=(df["transaction_date"].min().date(),
           df["transaction_date"].max().date()),
    min_value=df["transaction_date"].min().date(),
    max_value=df["transaction_date"].max().date()
)

locations = sorted(df["store_location"].dropna().unique())

selected_locations = st.sidebar.multiselect(
    "Select store location",
    locations,
    default=locations
)

categories = sorted(df["product_category"].dropna().unique())

selected_categories = st.sidebar.multiselect(
    "Select product category",
    categories,
    default=categories
)

quantity_range = st.sidebar.slider(
    "Select transaction quantity",
    int(df["transaction_qty"].min()),
    int(df["transaction_qty"].max()),
    (int(df["transaction_qty"].min()),
     int(df["transaction_qty"].max()))
)

product_types = ["All"] + sorted(df["product_type"].dropna().unique())

selected_type = st.sidebar.selectbox(
    "Select product type",
    product_types
)

search_product = st.sidebar.text_input("Search product detail")

# 4. FILTER DATA
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = df["transaction_date"].min().date()
    end_date = df["transaction_date"].max().date()

filtered_df = df[
    (df["transaction_date"].dt.date >= start_date) &
    (df["transaction_date"].dt.date <= end_date) &
    (df["store_location"].isin(selected_locations)) &
    (df["product_category"].isin(selected_categories)) &
    (df["transaction_qty"].between(
        quantity_range[0], quantity_range[1]
    ))
].copy()

if selected_type != "All":
    filtered_df = filtered_df[
        filtered_df["product_type"] == selected_type
    ]

if search_product.strip():
    filtered_df = filtered_df[
        filtered_df["product_detail"].str.contains(
            search_product.strip(), case=False, na=False
        )
    ]

# 5. APPLICATION TABS
tab1, tab2, tab3, tab4 = st.tabs([
    "Dashboard Overview",
    "Dataset",
    "Visualizations",
    "Insights"
])

# 6. DASHBOARD AND KPIs
with tab1:
    st.subheader("Key Performance Indicators")

    if filtered_df.empty:
        st.warning("No records match the selected filters.")
    else:
        total_transactions = len(filtered_df)
        total_quantity = filtered_df["transaction_qty"].sum()
        total_revenue = filtered_df["revenue"].sum()
        average_revenue = filtered_df["revenue"].mean()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Transactions", total_transactions)
        col2.metric("Units Sold", total_quantity)
        col3.metric("Total Revenue", f"${total_revenue:.2f}")
        col4.metric("Average Revenue", f"${average_revenue:.2f}")

        st.divider()
        st.subheader("Category-wise Transaction Count")

        category_count = (
            filtered_df.groupby("product_category")
            .size()
            .reset_index(name="transactions")
        )

        st.bar_chart(
            category_count,
            x="product_category",
            y="transactions"
        )

        with st.expander("More Dataset Information"):
            st.write("Store locations:",
                     filtered_df["store_location"].nunique())
            st.write("Product categories:",
                     filtered_df["product_category"].nunique())
            st.write("Product types:",
                     filtered_df["product_type"].nunique())

# 7. DATASET TAB
with tab2:
    st.subheader("Coffee Shop Transaction Dataset")

    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=450
    )

    with st.expander("Dataset Information"):
        st.write("Total rows:", len(filtered_df))
        st.write("Columns:", list(filtered_df.columns))
        st.write("Missing values:")
        st.dataframe(filtered_df.isnull().sum())

# 8. VISUALIZATIONS
with tab3:
    st.subheader("Sales Visualizations")

    if filtered_df.empty:
        st.warning("No data available for the selected filters.")
    else:
        # BAR CHART
        st.write("### 1. Revenue by Product Category")

        category_revenue = (
            filtered_df.groupby("product_category")["revenue"]
            .sum()
            .reset_index()
            .sort_values("revenue", ascending=False)
        )

        st.bar_chart(
            category_revenue,
            x="product_category",
            y="revenue"
        )

        st.caption("Compares revenue generated by each category.")

        # LINE CHART
        st.write("### 2. Daily Revenue Trend")

        daily_revenue = (
            filtered_df.groupby("transaction_date")["revenue"]
            .sum()
            .reset_index()
            .sort_values("transaction_date")
        )

        st.line_chart(
            daily_revenue,
            x="transaction_date",
            y="revenue"
        )

        st.caption("Shows changes in daily revenue.")

        # SCATTER PLOT
        st.write("### 3. Quantity and Revenue Relationship")

        scatter_data = filtered_df[
            ["transaction_qty", "revenue", "product_category"]
        ]

        st.scatter_chart(
            scatter_data,
            x="transaction_qty",
            y="revenue",
            color="product_category"
        )

        st.caption("Compares transaction quantity with revenue.")

# 9. INSIGHTS
with tab4:
    st.subheader("Business Insights")

    if filtered_df.empty:
        st.warning("No insights available.")
    else:
        category_sales = filtered_df.groupby(
            "product_category"
        )["revenue"].sum()

        location_sales = filtered_df.groupby(
            "store_location"
        )["revenue"].sum()

        product_sales = filtered_df.groupby(
            "product_detail"
        )["transaction_qty"].sum()

        st.write("Highest revenue category:", category_sales.idxmax())
        st.write("Highest revenue location:", location_sales.idxmax())
        st.write("Most sold product:", product_sales.idxmax())

        st.write("Total quantity sold:",
                 int(filtered_df["transaction_qty"].sum()))

        st.write("Average unit price:",
                 f"${filtered_df['unit_price'].mean():.2f}")

        st.divider()
        st.subheader("Store-wise Revenue Summary")

        location_summary = (
            filtered_df.groupby("store_location")
            .agg(
                Transactions=("transaction_id", "count"),
                Units_Sold=("transaction_qty", "sum"),
                Total_Revenue=("revenue", "sum")
            )
            .reset_index()
        )

        st.dataframe(location_summary, use_container_width=True)

        st.subheader("Top 10 Products by Quantity Sold")

        top_products = (
            filtered_df.groupby("product_detail")["transaction_qty"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )

        st.bar_chart(
            top_products,
            x="product_detail",
            y="transaction_qty"
        )

# 10. FOOTER
st.divider()
st.caption("Coffee Shop Sales Analysis | Python, Pandas and Streamlit")
