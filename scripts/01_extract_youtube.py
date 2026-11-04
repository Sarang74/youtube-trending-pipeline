from datetime import datetime
from googleapiclient.discovery import build
import pandas as pd
from config import YOUTUBE_API_KEY, REGION_CODE, MAX_RESULTS, DATA_RAW_DIR

def extract_trending_videos():
    """Extracts top trending videos via YouTube Data API v3 and writes to Parquet."""
    print(f"[{datetime.now()}] Connecting to YouTube Data API v3...")
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    print(f"Fetching top {MAX_RESULTS} trending videos for region '{REGION_CODE}'...")
    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        chart="mostPopular",
        regionCode=REGION_CODE,
        maxResults=MAX_RESULTS
    )
    response = request.execute()

    records = []
    extraction_time = datetime.utcnow()
    snapshot_date = extraction_time.strftime("%Y-%m-%d")

    for rank, item in enumerate(response.get("items", []), start=1):
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})

        records.append({
            "video_id": item.get("id"),
            "snapshot_date": snapshot_date,
            "extraction_timestamp": extraction_time,
            "trending_rank": rank,
            "title": snippet.get("title"),
            "channel_id": snippet.get("channelId"),
            "channel_title": snippet.get("channelTitle"),
            "category_id": snippet.get("categoryId"),
            "published_at": snippet.get("publishedAt"),
            "view_count": int(statistics.get("viewCount", 0)),
            "like_count": int(statistics.get("likeCount", 0)),
            "comment_count": int(statistics.get("commentCount", 0)),
            "region_code": REGION_CODE
        })

    df = pd.DataFrame(records)
    print(f"Extracted {len(df)} records.")

    # Standard Partitioned Data Lake Storage: data/raw/date=YYYY-MM-DD/
    output_dir = DATA_RAW_DIR / f"date={snapshot_date}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_filepath = output_dir / "trending_videos.parquet"
    df.to_parquet(output_filepath, engine="pyarrow", index=False)
    print(f"Saved snapshot to: {output_filepath}")

if __name__ == "__main__":
    extract_trending_videos()