# Arbitrage

This project is an **arbitrage data engine**: it collects live market data from **two prediction markets** (Kalshi and Polymarket), stores it in a database, and is built so you can later **compare prices** and spot arbitrage opportunities (same outcome, different price on each site).

---

## The Big Picture

```
┌─────────────────┐     ┌─────────────────┐
│     KALSHI      │     │   POLYMARKET     │
│  (API + WS)     │     │  (API + WS)      │
└────────┬────────┘     └────────┬────────┘
         │                        │
         │   events + prices      │   events + prices
         ▼                        ▼
    ┌─────────────────────────────────────┐
    │         SHARED QUEUE (in-memory)     │
    │   All data flows here as "packets"   │
    └────────────────────┬────────────────┘
                         │
                         ▼
    ┌─────────────────────────────────────┐
    │     DATABASE WORKER / LIBRARIAN      │
    │   Writes events & prices to Postgres │
    └─────────────────────────────────────┘
```

- **Kalshi** and **Polymarket** are prediction markets (you bet on events like "Will X happen?").
---

## What Each Piece Does

### 1. **`main.py`** — The "engine"

- Creates a **shared queue** (like a conveyor belt for data).
- Starts several **tasks** that run at the same time (async):
  - **Kalshi WebSocket** — live price updates from Kalshi.
  - **Kalshi events** — list of events/markets from Kalshi (on a timer).
  - **Polymarket WebSocket** — live order book / prices from Polymarket.
  - **Polymarket events** — list of events/markets from Polymarket (on a timer).
  - **Database worker** — reads from the queue and writes everything to the database.

Everything runs together; when any component gets new data, it puts a **packet** (type + data) on the queue, and the DB worker stores it.

---

### 2. **Kalshi side**

- **`clients.py`**
  - **KalshiHttpClient** — one-off API calls (e.g. balance, trades).
  - **KalshiWebSocketClient** — stays connected and gets **live ticker (price) updates**; each update is pushed to the shared queue as a `kalshi_prices` packet.
- **`kalshi_innit.py`** — loads your Kalshi API key and private key from env / key file (for auth).
- **`kalshi_events_api.py`**
  - **Kalshi_event_client** — periodically fetches **all events (and their markets)** from Kalshi's API and puts them on the queue as `kalshi_events` packets.

So: **events** = what you can trade; **prices** = live bid/ask from the WebSocket.

---

### 3. **Polymarket side**

- **`polymarket_events.py`**
  - **PolyEvents** — periodically fetches **all (open) events** from Polymarket's Gamma API and puts them on the queue as `polymarket_events` packets.
- **`polymarket_api.py`**
  - **WebSocketOrderBook** — connects to Polymarket's WebSocket, gets **price / order book updates** (e.g. `price_change`), and can write them to Postgres (in the current code it uses a direct DB connection for that).
- **`pmclient.py`** — Polymarket API client setup (credentials, etc.) for authenticated calls if needed.

So again: **events** = list of markets; **WebSocket** = live prices/order book.

---

### 4. **Database**

- **`db_worker.py`**
  - **DatabaseWorker** — runs a loop: take a packet from the shared queue, then:
    - `kalshi_events` → insert/update **Kalshi events and markets**.
    - `polymarket_events` → insert/update **Polymarket events and markets**.
    - `kalshi_prices` → insert **Kalshi price ticks** (and latest price).
    - `polymarket_prices` → (placeholder for Polymarket price ticks).

So the DB is the **single place** where both platforms' events and prices are stored, which is what you need to compare and find arbitrage.

---

## Data Flow in One Sentence

**Kalshi and Polymarket send events and prices into a shared queue; a database worker reads that queue and writes everything to Postgres so you can later compare prices across the two sites.**

---

## What You Need to Run It

- **Python** with the dependencies (e.g. `httpx`, `websockets`, `cryptography`, `psycopg`, etc.).
- **Kalshi**: API key + private key (in `.env` / key file, see `kalshi_innit.py`).
- **Polymarket**: API credentials if you use authenticated endpoints (see `pmclient.py`).
- **PostgreSQL**: running locally (or wherever the connection strings point) with the expected tables (e.g. `kalshi_events`, `kalshi_markets`, `kalshi_tick_history`, `kalshi_latest_prices`, and the Polymarket equivalents).

---

## Note About `main.py` and Module Names

`main.py` imports:

- `KalshiEvents` from `kalshi_events`
- `DatabaseLibrarian` from `database_librarian`
- `WebSocketOrderBook(shared_queue)` (only one argument)

In the repo you have:

- **Kalshi events**: class `Kalshi_event_client` in **`kalshi_events_api.py`** (no file named `kalshi_events.py`).
- **DB worker**: class `DatabaseWorker` in **`db_worker.py`** (no file named `database_librarian.py`).
- **Polymarket WebSocket**: `WebSocketOrderBook` in **`polymarket_api.py`** expects many arguments (channel type, url, data, auth, etc.), not just `shared_queue`.

So to run the "engine" as in `main.py`, you'd need to either add thin modules that match those names (e.g. `kalshi_events.py` exporting `KalshiEvents` = `Kalshi_event_client`, `database_librarian.py` exporting `DatabaseLibrarian` = `DatabaseWorker`) and a small wrapper that builds `WebSocketOrderBook` with the right arguments and feeds a `shared_queue`, or change `main.py` to use the existing modules and class names directly. The **behavior** described above is how the repo is designed to work once those pieces are wired up.

---

## Summary

| Part            | Role |
|-----------------|------|
| **main.py**     | Starts the engine: queue + Kalshi/Polymarket data tasks + DB writer. |
| **Kalshi**      | Events (what to trade) + live prices via WebSocket → queue. |
| **Polymarket**  | Events (what to trade) + live prices via WebSocket → queue (and some direct DB writes in current code). |
| **DB worker**   | Reads queue, writes events and prices to Postgres. |
| **Goal**        | Centralized data so you can **compare Kalshi vs Polymarket prices** and find arbitrage opportunities. |
