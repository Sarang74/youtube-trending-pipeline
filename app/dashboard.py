import streamlit as st
import duckdb
import pandas as pd
from pathlib import Path

# Setup page config
st.set_page_config(
    page_title="YouTube Trending Analytics",
    page_icon="📊",
    layout="wide"
)

# Database connection
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "warehouse" / "youtube_analytics.duckdb"

@st.cache_data(ttl=300)
def load_data():
    if not DB_PATH.exists():
        return None, None, None
    con = duckdb.connect(str(DB_PATH), read_only=True)
    
    # 1. Fact summary joined with dimensions
    query = """
        SELECT 
            f.snapshot_date,
            f.trending_rank,
            f.title,
            f.view_count,
            f.like_count,
            f.comment_count,
            c.channel_title,
            coalesce(cat.category_name, 'Other') AS category_name
        FROM fct_trending_snapshot f
        LEFT JOIN dim_channel c ON f.channel_id = c.channel_id
        LEFT JOIN dim_category cat ON f.category_id = cat.category_id
        ORDER BY f.snapshot_date DESC, f.trending_rank ASC;
    """
    df = con.execute(query).df()
    con.close()
    return df

df = load_data()

st.title("🎬 YouTube Trending Intelligence Dashboard")
st.markdown("Automated ingestion, Kimball Star Schema data warehouse, and real-time analytical metrics.")

if df is None or df.empty:
    st.warning("No warehouse data found. Please run scripts/03_load_star_schema.py first.")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("Filter Analytics")
available_dates = sorted(df["snapshot_date"].unique(), reverse=True)
selected_date = st.sidebar.selectbox("Snapshot Date", available_dates)

categories = ["All"] + sorted(df["category_name"].unique().tolist())
selected_category = st.sidebar.selectbox("Category", categories)

# Apply filters
filtered_df = df[df["snapshot_date"] == selected_date]
if selected_category != "All":
    filtered_df = filtered_df[filtered_df["category_name"] == selected_category]

# --- Top KPI Summary Cards ---
col1, col2, col3, col4 = st.columns(4)
total_videos = len(filtered_df)
total_views = filtered_df["view_count"].sum()
total_likes = filtered_df["like_count"].sum()
avg_engagement = (
    ((total_likes + filtered_df["comment_count"].sum()) / total_views * 100)
    if total_views > 0 else 0
)

col1.metric("Trending Videos", f"{total_videos:,}")
col2.metric("Total Views", f"{total_views:,.0f}")
col3.metric("Total Likes", f"{total_likes:,.0f}")
col4.metric("Engagement Rate", f"{avg_engagement:.2f}%")

st.divider()

# --- Visual Breakdown ---
v_col1, v_col2 = st.columns([1, 1])

with v_col1:
    st.subheader("Top Categories by View Volume")
    cat_summary = (
        filtered_df.groupby("category_name")["view_count"]
        .sum()
        .reset_index()
        .sort_values(by="view_count", ascending=False)
    )
    st.bar_chart(data=cat_summary, x="category_name", y="view_count", use_container_width=True)

with v_col2:
    st.subheader("Top Channels by Trending Count")
    channel_summary = (
        filtered_df.groupby("channel_title")["title"]
        .count()
        .reset_index()
        .rename(columns={"title": "video_count"})
        .sort_values(by="video_count", ascending=False)
        .head(10)
    )
    st.bar_chart(data=channel_summary, x="channel_title", y="video_count", use_container_width=True)

st.divider()

# --- Detailed Fact Table ---
st.subheader("Trending Video Performance Matrix")
display_cols = ["trending_rank", "title", "channel_title", "category_name", "view_count", "like_count", "comment_count"]
st.dataframe(
    filtered_df[display_cols].reset_index(drop=True),
    use_container_width=True
)










