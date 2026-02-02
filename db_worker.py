import psycopg

class DatabaseWorker:
    def __init__(self, shared_queue):
        self.shared_queue = shared_queue
        self.uri = "postgresql://fernandoarroyo@localhost:5432/fernandoarroyo"
        self.conn = None
        self.cursor = None

    async def insert_kalshi_events(self, events):
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
        try:
            await self.cursor.executemany(sql_events, events_tuple)
            await self.cursor.executemany(sql_markets, markets_tuple)
            await self.conn.commit()
        except Exception as e:
            print(f"Error inserting markets: {str(e)}")
            await self.conn.rollback()


    async def insert_polymarket_events(event):
        try:
            self.cursor.execute("""
            INSERT INTO polymarket_events (source, event_id, title, description) VALUES ('Polymarket', %s, %s, %s)
            ON CONFLICT (source, event_id) DO UPDATE SET
            title = COALESCE(EXCLUDED.title, polymarket_events.title),
            description = COALESCE(EXCLUDED.description, polymarket_events.description)
            """, (event.get("id", None), event.get("title", None), event.get("description", None)))
        except Exception as e:
            print("Error parsing event:", e)
            self.conn.rollback()


        for market in event.get("markets", []):
            self.cursor.execute("""
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
            """, (event.get("id", None), market.get("conditionId", None), market.get("market_type", None), market.get ("question", None), event.get("startDate", None), market.get("endDate", None), market.get("active", None), market.get("description", None)))

    async def insert_kalshi_prices(cursor, conn, msg):
        try :
            ts = datetime.fromtimestamp(msg['ts'], tz=timezone.utc)

            self.cursor.execute("""
            INSERT INTO kalshi_markets (source, market_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
            """, ('Kalshi', msg['market_id']))

            self.cursor.execute(
                "INSERT INTO kalshi_tick_history (source, market_id, yes_bid_doll, yes_ask_doll, price_doll, volume, vol_doll, ts, open_interest) VALUES ('Kalshi', %s, %s, %s, %s, %s, %s, %s, %s)",
                (msg['market_id'], msg['yes_bid_dollars'], msg['yes_ask_dollars'], msg['price_dollars'], msg['volume'], msg['dollar_volume'], ts, msg['open_interest'])
            )

            self.cursor.execute("""
            INSERT INTO kalshi_latest_prices (source, market_id, yes_bid_doll, yes_ask_doll, price_doll, volume, vol_doll, ts, open_interest)
            VALUES ('Kalshi', %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (source, market_id) DO UPDATE SET yes_bid_doll = excluded.yes_bid_doll, yes_ask_doll = excluded.yes_ask_doll, price_doll = excluded.price_doll, ts = excluded.ts, volume = excluded.volume, vol_doll = excluded.vol_doll, open_interest = excluded.open_interest""",
            (msg['market_id'], msg['yes_bid_dollars'], msg['yes_ask_dollars'], msg['price_dollars'], msg['volume'], msg['dollar_volume'], ts, msg['open_interest']))

            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print("Error processing message:", e)
    
    
    async def insert_polymarket_prices():
        pass

    async def run(self):
        async with await psycopg.AsyncConnection.connect(self.uri) as conn:
            while True:
                packet = await self.shared_queue.get()
                data = packet['data']
                try:
                    async with conn.cursor() as cur:
                        match packet['type']:
                            case 'kalshi_events':
                                await self.insert_kalshi_events(data)
                            case 'polymarket_events':
                                await self.insert_polymarket_events(data)
                            case 'kalshi_prices':
                                await self.insert_kalshi_prices(data)
                            case 'polymarket_prices':
                                await self.insert_polymarket_prices(data)
                    print(f"Received data: {packet}")
                    self.shared_queue.task_done()
                except Exception as e:
                    print(f"Error in DatabaseWorker: {str(e)}")