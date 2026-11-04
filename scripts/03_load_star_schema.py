from datetime import datetime
import duckdb
from config import DATA_RAW_DIR, DATA_WAREHOUSE_DIR

# Static mapping for standard YouTube category IDs
CATEGORY_MAPPING = [
    (1, "Film & Animation"),
    (2, "Autos & Vehicles"),
    (10, "Music"),
    (15, "Pets & Animals"),
    (17, "Sports"),
    (19, "Travel & Events"),
    (20, "Gaming"),
    (22, "People & Blogs"),
    (23, "Comedy"),
    (24, "Entertainment"),
    (25, "News & Politics"),
    (26, "Howto & Style"),
    (27, "Education"),
    (28, "Science & Technology"),
]

def load_warehouse():
    DATA_WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)
    db_path = DATA_WAREHOUSE_DIR / "youtube_analytics.duckdb"
    
    print(f"[{datetime.now()}] Connecting to DuckDB at {db_path}...")
    con = duckdb.connect(str(db_path))

    # 1. Create Dimensions and Fact Tables
    con.execute("""
        CREATE TABLE IF NOT EXISTS dim_channel (
            channel_id VARCHAR PRIMARY KEY,
            channel_title VARCHAR,
            first_seen_date DATE
        );

        CREATE TABLE IF NOT EXISTS dim_category (
            category_id INTEGER PRIMARY KEY,
            category_name VARCHAR
        );

        CREATE TABLE IF NOT EXISTS dim_date (
            date_key DATE PRIMARY KEY,
            year INTEGER,
            month INTEGER,
            day INTEGER,
            day_name VARCHAR,
            is_weekend BOOLEAN
        );

        CREATE TABLE IF NOT EXISTS fct_trending_snapshot (
            snapshot_id VARCHAR PRIMARY KEY,
            snapshot_date DATE,
            video_id VARCHAR,
            channel_id VARCHAR,
            category_id INTEGER,
            trending_rank INTEGER,
            view_count BIGINT,
            like_count BIGINT,
            comment_count BIGINT,
            title VARCHAR,
            published_at TIMESTAMP
        );
    """)

    # 2. Seed dim_category
    con.executemany(
        "INSERT OR IGNORE INTO dim_category VALUES (?, ?);",
        CATEGORY_MAPPING
    )

    # 3. Ingest latest Parquet files from data lake partition
    parquet_glob = str(DATA_RAW_DIR / "date=*" / "trending_videos.parquet").replace("\\", "/")
    print(f"Reading raw Parquet partitions from: {parquet_glob}")

    # Upsert dim_channel
    con.execute(f"""
        INSERT INTO dim_channel
        SELECT 
            channel_id,
            channel_title,
            MIN(CAST(snapshot_date AS DATE)) AS first_seen_date
        FROM read_parquet('{parquet_glob}')
        WHERE channel_id NOT IN (SELECT channel_id FROM dim_channel)
        GROUP BY channel_id, channel_title;
    """)

    # Upsert dim_date
    con.execute(f"""
        INSERT INTO dim_date
        SELECT DISTINCT
            CAST(snapshot_date AS DATE) AS date_key,
            EXTRACT(YEAR FROM CAST(snapshot_date AS DATE)) AS year,
            EXTRACT(MONTH FROM CAST(snapshot_date AS DATE)) AS month,
            EXTRACT(DAY FROM CAST(snapshot_date AS DATE)) AS day,
            DAYNAME(CAST(snapshot_date AS DATE)) AS day_name,
            CASE WHEN DAYOFWEEK(CAST(snapshot_date AS DATE)) IN (0, 6) THEN TRUE ELSE FALSE END AS is_weekend
        FROM read_parquet('{parquet_glob}')
        WHERE CAST(snapshot_date AS DATE) NOT IN (SELECT date_key FROM dim_date);
    """)

    # Load fct_trending_snapshot (avoiding duplicate snapshot loads)
    con.execute(f"""
        INSERT INTO fct_trending_snapshot
        SELECT 
            md5(concat(video_id, '_', snapshot_date)) AS snapshot_id,
            CAST(snapshot_date AS DATE) AS snapshot_date,
            video_id,
            channel_id,
            CAST(category_id AS INTEGER) AS category_id,
            trending_rank,
            view_count,
            like_count,
            comment_count,
            title,
            CAST(published_at AS TIMESTAMP) AS published_at
        FROM read_parquet('{parquet_glob}')
        WHERE md5(concat(video_id, '_', snapshot_date)) NOT IN (SELECT snapshot_id FROM fct_trending_snapshot);
    """)

    # 4. Warehouse Summary
    channel_cnt = con.execute("SELECT COUNT(*) FROM dim_channel;").fetchone()[0]
    fact_cnt = con.execute("SELECT COUNT(*) FROM fct_trending_snapshot;").fetchone()[0]
    print(f"[SUCCESS] Warehouse updated:")
    print(f" - dim_channel total rows: {channel_cnt}")
    print(f" - fct_trending_snapshot total rows: {fact_cnt}")

    con.close()

if __name__ == "__main__":
    load_warehouse()