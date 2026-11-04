from datetime import datetime
import pandas as pd
from config import DATA_RAW_DIR

def run_quality_gate(snapshot_date: str = None):
    """Enforces critical schema assertions on raw Parquet ingestion."""
    if snapshot_date is None:
        snapshot_date = datetime.now().strftime("%Y-%m-%d")

    parquet_file = DATA_RAW_DIR / f"date={snapshot_date}" / "trending_videos.parquet"
    
    if not parquet_file.exists():
        raise FileNotFoundError(f"Snapshot not found for date {snapshot_date} at {parquet_file}")

    print(f"[{datetime.now()}] Running Quality Gate on {parquet_file.name} (date={snapshot_date})...")
    df = pd.read_parquet(parquet_file)

    # 1. Row Count Check
    assert len(df) > 0, "CRITICAL ERROR: Raw dataset contains 0 records."
    print(f"[PASS] Row count verified: {len(df)} records.")

    # 2. Primary Key Uniqueness Check
    duplicate_ids = df["video_id"].duplicated().sum()
    assert duplicate_ids == 0, f"DATA ERROR: Found {duplicate_ids} duplicate video IDs."
    print("[PASS] Uniqueness assertion passed: video_id is unique across snapshot.")

    # 3. Not Null Checks on Core Columns
    critical_columns = ["video_id", "title", "channel_id", "category_id", "snapshot_date"]
    for col in critical_columns:
        null_count = df[col].isnull().sum()
        assert null_count == 0, f"DATA ERROR: Column '{col}' contains {null_count} null values."
    print(f"[PASS] Not-null assertions passed for: {', '.join(critical_columns)}.")

    # 4. Metric Bounds Check
    negative_views = (df["view_count"] < 0).sum()
    assert negative_views == 0, "DATA ERROR: Negative view count detected."
    print("[PASS] Value threshold assertion passed: All view counts are non-negative.")

    print("\n--- ALL QUALITY GATES PASSED (Data ready for DuckDB warehouse) ---")

if __name__ == "__main__":
    run_quality_gate()