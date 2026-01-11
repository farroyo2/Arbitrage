import requests
import time
from tqdm import tqdm
import sqlite3

BASE = "https://api.elections.kalshi.com/trade-api/v2/events"

def fetch_all_events(limit=200, sleep_s=0.5, with_nested_markets=True):
    cursor = None
    events = []
    page_num = 0

    with tqdm(desc="Fetching events", unit="events") as pbar:
        while page_num < 10:
            page_num += 1
            params = {"limit": limit, "with_nested_markets": with_nested_markets}
            if cursor:
                params["cursor"] = cursor

            resp = requests.get(BASE, params=params, timeout=30)

            if resp.status_code != 200:
                raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:500]}")

            page = resp.json()

            batch = page.get("events")
            if batch is None:
                raise RuntimeError(f"Missing 'events' in response: keys={list(page.keys())}")

            events.extend(batch)
            pbar.update(len(batch))

            cursor = page.get("cursor")
            if not cursor:
                break

            time.sleep(sleep_s)

    return events

def parse_event(event):
    try:
       cursor.execute("""
       INSERT INTO events (source, event_ticker, title, sub_title, category, mutually_exclusive, available_on_brokers) 
       VALUES ('Kalshi', ?, ?, ?, ?, ?, ?)
       ON CONFLICT (source,event_ticker) DO UPDATE SET
       title = COALESCE(events.title, excluded.title),
       sub_title = COALESCE(events.sub_title, excluded.sub_title),
       category = COALESCE(events.category, excluded.category),
       mutually_exclusive = COALESCE(events.mutually_exclusive, excluded.mutually_exclusive),
       available_on_brokers = COALESCE(events.available_on_brokers, excluded.available_on_brokers)
       """, (event.get("event_ticker", None),   event.get("title", None), event.get("sub_title", None), event.get("category", None), event.get("mutually_exclusive", None), event.get("available_on_brokers", None)))
    

       for market in event.get("markets", []):
           cursor.execute("""
           INSERT INTO markets (source, market_id, market_ticker, event_ticker, market_type, title, subtitle, yes_sub_title, no_sub_title, created_time, open_time, close_time, expiration_time, expected_expiration_time, latest_expiration_time, status, result, settlement_ts, settlement_value, rules_primary, rules_secondary,can_close_early, early_close_condition, strike_type, floor_strike, cap_strike, functional_strike ) 
           VALUES ('Kalshi', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT (source, market_ticker) DO UPDATE SET
           event_ticker = COALESCE(markets.event_ticker, excluded.event_ticker),
           market_type = COALESCE(markets.market_type, excluded.market_type),
           title = COALESCE(markets.title, excluded.title),
           subtitle = COALESCE(markets.subtitle, excluded.subtitle),
           yes_sub_title = COALESCE(markets.yes_sub_title, excluded.yes_sub_title),
           no_sub_title = COALESCE(markets.no_sub_title, excluded.no_sub_title),
           created_time = COALESCE(markets.created_time, excluded.created_time),
           open_time = COALESCE(markets.open_time, excluded.open_time),
           close_time = COALESCE(markets.close_time, excluded.close_time),
           expiration_time = COALESCE(markets.expiration_time, excluded.expiration_time),
           expected_expiration_time = COALESCE(markets.expected_expiration_time, excluded.expected_expiration_time),
           latest_expiration_time = COALESCE(markets.latest_expiration_time, excluded.latest_expiration_time),
           status = COALESCE(markets.status, excluded.status),
           result = COALESCE(markets.result, excluded.result),
           settlement_ts = COALESCE(markets.settlement_ts, excluded.settlement_ts),
           settlement_value = COALESCE(markets.settlement_value, excluded.settlement_value),
           rules_primary = COALESCE(markets.rules_primary, excluded.rules_primary),
           rules_secondary = COALESCE(markets.rules_secondary, excluded.rules_secondary),
           can_close_early = COALESCE(markets.can_close_early, excluded.can_close_early),
           early_close_condition = COALESCE(markets.early_close_condition, excluded.early_close_condition),
           strike_type = COALESCE(markets.strike_type, excluded.strike_type),
           floor_strike = COALESCE(markets.floor_strike, excluded.floor_strike),
           cap_strike = COALESCE(markets.cap_strike, excluded.cap_strike),
           functional_strike = COALESCE(markets.functional_strike, excluded.functional_strike)
           """, (None, market["ticker"], event.get("event_ticker", None), market.get("market_type", None), market.get ("title", None), market.get("subtitle", None), market.get("yes_sub_title", None), market.get("no_sub_title", None), market.get("created_time", None), market.get("open_time", None), market.get("close_time", None), market.get("expiration_time", None), market.get("expected_expiration_time", None), market.get("latest_expiration_time", None), market.get("status", None), market.get("result", None), market.get("settlement_ts", None), market.get("settlement_value", None), market.get("rules_primary", None), market.get("rules_secondary", None), market.get("can_close_early", None), market.get("early_close_condition", None), market.get("strike_type", None), market.get("floor_strike", None), market.get("cap_strike", None), market.get("functional_strike", None)))


    except Exception as e:
        conn.rollback()
        print(f"Error parsing event {event.get('event_ticker', None)}: {str(e)}")

events = fetch_all_events()
print("DONE total events:", len(events))

db_path = "/Users/fernandoarroyo/Desktop/Fer&Tayden/Arbitrage/Kalshi.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()
cursor.execute("PRAGMA journal_mode = WAL;")


for (event) in events:
    parse_event(event)

conn.commit()
conn.close()
