# 🎬 YouTube Trending Intelligence Pipeline

**Python • YouTube Data API v3 • DuckDB • Kimball Star Schema • Streamlit**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![DuckDB](https://img.shields.io/badge/DuckDB-1.1+-FFF000?style=for-the-badge&logo=duckdb&logoColor=black)](https://duckdb.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Architecture](https://img.shields.io/badge/Architecture-Kimball_Star_Schema-0A85EA?style=for-the-badge)](#-data-model)

---

## 🎯 Overview

An automated data pipeline that extracts YouTube Trending metadata, validates it against data quality rules, loads it into a DuckDB star schema, and serves insights through an interactive Streamlit dashboard.

**Key Features:**
- Incremental, date-partitioned raw storage in Parquet
- Quality gate that blocks bad data before it reaches the warehouse
- Kimball-style star schema for fast analytical queries
- Interactive dashboard for trending analytics

---

## 🏗️ Architecture

```text
[ YouTube Data API v3 ]
          │
          ▼
[ 01_extract_youtube.py ]  ──>  data/raw/date=YYYY-MM-DD/*.parquet
          │
          ▼
[ 02_validate_data.py ]    ──>  Quality gate (uniqueness, non-nulls, thresholds)
          │
          ▼
[ 03_load_star_schema.py ] ──>  data/warehouse/youtube_analytics.duckdb
          │                     ├── dim_channel
          │                     ├── dim_category
          │                     ├── dim_date
          │                     └── fct_trending_snapshot
          ▼
[ app/dashboard.py ]       ──>  Streamlit dashboard