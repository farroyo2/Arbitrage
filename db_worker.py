import psycopg
import asyncio
from datetime import datetime, timezone


class DatabaseWorker:
    def __init__(self, shared_queue):
        self.shared_queue = shared_queue
        self.uri = "postgresql://fernandoarroyo@localhost:5432/fernandoarroyo"
        self.conn = None

    async def insert_kalshi_events(self, events, cursor):
        if not events:
            return
        events_tuple = []
        markets_tuple = []
        for event in events:
            events_tuple.append(
                (event.get("event_ticker", None),   event.get("title", None), event.get("category", None), event.get("mutually_exclusive", None), event.get("sub_title", None))
            )
            for market in event.get("markets", []):
                markets_tuple.append(
                    (event.get("event_ticker", None), market.get("ticker", None), market.get("market_type", None), market.get ("title", None), market.get("open_time", None), market.get("close_time", None), market.get("expiration_time", None), market.get("status", None), market.get("result", None), market.get("rules_primary", None), market.get("can_close_early", None), market.get("early_close_condition", None), market.get("rules_secondary", None))
                )

        sql_events = """
            INSERT INTO kalshi_events (source, event_id, title, category, mutually_exclusive, sub_title) 
            VALUES ('Kalshi', %s, %s, %s, %s, %s)
            ON CONFLICT (source,event_id) DO UPDATE SET
            title = COALESCE(EXCLUDED.title, kalshi_events.title),
            category = COALESCE(EXCLUDED.category, kalshi_events.category),
            mutually_exclusive = COALESCE(EXCLUDED.mutually_exclusive, kalshi_events.mutually_exclusive),
            sub_title = COALESCE(EXCLUDED.sub_title, kalshi_events.sub_title)
            """

        sql_markets = """
            INSERT INTO kalshi_markets (source,event_id, market_id, market_type, title, open_time, close_time, expiration_time, status, result, rules_primary, can_close_early, early_close_condition, rules_secondary) 
            VALUES ('Kalshi', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (source, market_id) DO UPDATE SET
            event_id = COALESCE(EXCLUDED.event_id, kalshi_markets.event_id),
            market_type = COALESCE(EXCLUDED.market_type, kalshi_markets.market_type),
            title = COALESCE(EXCLUDED.title, kalshi_markets.title),
            open_time = COALESCE(EXCLUDED.open_time, kalshi_markets.open_time),
            close_time = COALESCE(EXCLUDED.close_time, kalshi_markets.close_time),
            expiration_time = COALESCE(EXCLUDED.expiration_time, kalshi_markets.expiration_time),
            status = COALESCE(EXCLUDED.status, kalshi_markets.status),
            result = COALESCE(EXCLUDED.result, kalshi_markets.result),
            rules_primary = COALESCE(EXCLUDED.rules_primary, kalshi_markets.rules_primary),
            can_close_early = COALESCE(EXCLUDED.can_close_early, kalshi_markets.can_close_early),
            early_close_condition = COALESCE(EXCLUDED.early_close_condition, kalshi_markets.early_close_condition),
            rules_secondary = COALESCE(EXCLUDED.rules_secondary, kalshi_markets.rules_secondary)
            """
        await cursor.executemany(sql_events, events_tuple)
        await cursor.executemany(sql_markets, markets_tuple)



    async def insert_polymarket_events(self, events, cursor):
        if not events:
            return
        events_tuple = []
        markets_tuple = []
        for event in events:
            events_tuple.append(
                (event.get("id", None), event.get("title", None), event.get("description", None))
            )
            for market in event.get("markets", []):
                markets_tuple.append(
                    (event.get("id", None), market.get("conditionId", None), market.get("market_type", None), market.get ("question", None), event.get("startDate", None), market.get("endDate", None), market.get("active", None), market.get("description", None)))
        event_sql = """
            INSERT INTO polymarket_events (source, event_id, title, description) VALUES ('Polymarket', %s, %s, %s)
            ON CONFLICT (source, event_id) DO UPDATE SET
            title = COALESCE(EXCLUDED.title, polymarket_events.title),
            description = COALESCE(EXCLUDED.description, polymarket_events.description)
            """
        market_sql = """
            INSERT INTO polymarket_markets (source,event_id, market_id, market_type, title, open_time, close_time, status, rules_primary) 
            VALUES ('Polymarket', %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (source, market_id) DO UPDATE SET
            event_id = COALESCE(EXCLUDED.event_id, polymarket_markets.event_id),
            market_id = COALESCE(EXCLUDED.market_id, polymarket_markets.market_id),
            market_type = COALESCE(EXCLUDED.market_type, polymarket_markets.market_type),
            title = COALESCE(EXCLUDED.title, polymarket_markets.title),
            open_time = COALESCE(EXCLUDED.open_time, polymarket_markets.open_time),
            close_time = COALESCE(EXCLUDED.close_time, polymarket_markets.close_time),
            status = COALESCE(EXCLUDED.status, polymarket_markets.status),
            rules_primary = COALESCE(EXCLUDED.rules_primary, polymarket_markets.rules_primary)
            """
        await cursor.executemany(event_sql, events_tuple)
        await cursor.executemany(market_sql, markets_tuple)


    async def insert_kalshi_prices(self, msg, cursor):
        ts = msg['ts']

        await cursor.execute("""
        INSERT INTO kalshi_markets (source, market_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
        """, ('Kalshi', msg['market_id']))

        await cursor.execute(
            "INSERT INTO kalshi_tick_history (source, market_id, yes_bid_doll, yes_ask_doll, price_doll, volume, vol_doll, ts, open_interest) VALUES ('Kalshi', %s, %s, %s, %s, %s, %s, %s, %s)",
            (msg['market_id'], msg['yes_bid_doll'], msg['yes_ask_doll'], msg['price_doll'], msg['volume'], msg['vol_doll'], ts, msg['open_interest'])
        )

        await cursor.execute("""
        INSERT INTO kalshi_latest_prices (source, market_id, yes_bid_doll, yes_ask_doll, price_doll, volume, vol_doll, ts, open_interest)
        VALUES ('Kalshi', %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (source, market_id) DO UPDATE SET yes_bid_doll = excluded.yes_bid_doll, yes_ask_doll = excluded.yes_ask_doll, price_doll = excluded.price_doll, ts = excluded.ts, volume = excluded.volume, vol_doll = excluded.vol_doll, open_interest = excluded.open_interest""",
        (msg['market_id'], msg['yes_bid_doll'], msg['yes_ask_doll'], msg['price_doll'], msg['volume'], msg['vol_doll'], ts, msg['open_interest']))

    
    
    async def insert_polymarket_prices(self, message, cursor):
        try:
            ts = datetime.fromtimestamp(int(message["timestamp"])/1000).strftime("%Y-%m-%d %H:%M:%S")
        except:
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        changes = message.get("price_changes", [])
        for change in changes:
            await cursor.execute("""
            INSERT INTO polymarket_latest_prices (source, market_id, yes_bid_doll, yes_ask_doll, price_doll, ts)
            VALUES ('Polymarket', %s, %s, %s, %s, %s)
            ON CONFLICT (source, market_id) DO UPDATE SET
            yes_bid_doll = COALESCE(EXCLUDED.yes_bid_doll, polymarket_latest_prices.yes_bid_doll),
            yes_ask_doll = COALESCE(EXCLUDED.yes_ask_doll, polymarket_latest_prices.yes_ask_doll),
            price_doll = COALESCE(EXCLUDED.price_doll, polymarket_latest_prices.price_doll),
            ts = COALESCE(EXCLUDED.ts, polymarket_latest_prices.ts)
            """, (message["market"], change["best_bid"], change["best_ask"], change["price"], ts))

            await cursor.execute("""
            INSERT INTO polymarket_tick_history (source, market_id, yes_bid_doll, yes_ask_doll, price_doll, ts)
            VALUES ('Polymarket', %s, %s, %s, %s, %s)
            """, (message["market"], change["best_bid"], change["best_ask"], change["price"], ts))


    async def run(self):
        async with await psycopg.AsyncConnection.connect(self.uri) as conn:
            self.conn = conn
            while True:
                packet = await self.shared_queue.get()
                data = packet['data']
                try:
                    async with conn.cursor() as cur:
                        match packet['type']:
                            case 'kalshi_events':
                                await self.insert_kalshi_events(data, cur)
                            case 'polymarket_events':
                                await self.insert_polymarket_events(data, cur)
                            case 'kalshi_prices':
                                await self.insert_kalshi_prices(data, cur)
                            case 'polymarket_prices':
                                await self.insert_polymarket_prices(data, cur)
                    self.shared_queue.task_done()
                    await conn.commit()
                except Exception as e:
                    print(f"Error in DatabaseWorker: {str(e)}")
                    await conn.rollback()