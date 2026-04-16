# Arbitrage

This project is an **arbitrage data engine**: it collects live market data from **two prediction markets** (Kalshi and Polymarket), stores it in a PostgreSQL database, and is built so you can analyze, compare prices, and spot arbitrage opportunities (same outcome, different price on each site).

Recently, the overarching architecture was expanded into distinct modules to support forecasting, cross-market automated matching via NLP, and news ingestion for sentiment analysis.

---

## 🏗️ Project Architecture

### 1. `data_ingestion/` - The Core Engine
This directory houses the primary asynchronous engine that powers the data collection.
- **`main.py`**: The entry point. Creates a shared queue to process all data packets.
- **`clients.py` / `db_worker.py`**: A database worker that listens to the shared queue and efficiently writes market events and live ticks to PostgreSQL using `psycopg`.
- **Kalshi Subsystem (`kalshi_innit.py`, `kalshi_events_api.py`)**: Fetches upcoming events and price updates through Kalshi's REST and WebSocket interfaces.
- **Polymarket Subsystem (`poly_innit.py`, `polymarket_events.py`, `polymarket_api.py`)**: Connects to Polymarket's Gamma API and WebSocket Orderbook.
  
**Data Flow**: Kalshi and Polymarket send events and prices into an in-memory shared queue. The database worker continuously persists everything to Postgres. I/O runs mostly via `asyncio`.

### 2. `cross_market_arb/` - Automated Market Matching
Since Polymarket and Kalshi often name the same event differently, this module tries to automatically map and pair equivalent markets using NLP.
- **`market_pairs.py`**: Uses a multi-stage pipeline algorithm to find identical active markets:
  1. Time filtering (matches close times).
  2. Keyword analysis (extracting heavily weighted keywords like "fed", "CPI", "trump").
  3. Feature extraction (extracting and normalizing numbers from titles).
  4. Fuzzy string matching (`rapidfuzz`).
  5. **AI Cross-Encoder**: Final pipeline step routes potential matches through `cross-encoder/ms-marco-MiniLM-L-6-v2` (`sentence-transformers`) to compute semantic similarity. Identified pairs are inserted into the `market_pairs` Postgres table.

### 3. `News_ingestion/` - Real-Time Sentiment & Feeds
Monitors live news feeds to help inform prediction market forecasts.
- **`squaker_scraper.py`**: Connects to news APIs (like CryptoPanic) yielding up-to-the-minute updates and squawks.
- **`finbert.ipynb` / `BT.py`**: Leverages FinBERT for running financial sentiment analysis against the ingested text data, labeling events as positive, negative, or neutral for market impact.

### 4. `Market_Analyisis/` - Data Science & Modeling
A standalone space for working with historical data, evaluating opportunities, and testing theories.
- **`forecasting.ipynb`**: Modeling and forecasting on timeseries data for outcomes.
- Contains various diagnostic notebooks (`markets_diag.ipynb`, `analysis.ipynb`) mapping out odds, trends, and market lifecycles.

---

## 🚀 Setup & Requirements

1. **Python Dependencies:** Requires `httpx`, `websockets`, `cryptography`, `psycopg`, `rapidfuzz`, `sentence-transformers`, `torch`, `pandas`, `requests`, and standard data science libraries for the notebooks.
2. **Environment Variables (.env)**:
   - **Kalshi**: API Key + Private Key Path.
   - **Polymarket**: Appropriate API Keys if trading/querying authenticated endpoints.
   - **Postgres**: Connection string pointing to your local/remote database (e.g. `postgresql://user@localhost:5432/db`).
3. **Database Setup**: Start Postgres and ensure the tables exist. You can usually bootstrap these using `create_tables.py` located in `data_ingestion/`.
4. **Running the Engine**: Navigate to the `data_ingestion/` folder and execute `python main.py` to start syncing live events and prices.

---

## 📈 Goals
With the latest additions, the project natively scales from pure **data streaming** to sophisticated **NLP-based market pairing** and **news-driven statistical forecasting**, laying out the perfect foundational pipeline for real-time risk-free prediction arbitrage.
