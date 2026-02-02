from websocket import WebSocketApp
import json
import time
import threading
from pmclient import get_api_Creds, get_client
from polymarket_events import fetch_all_tokens_events, fetch_all_events
import requests
from datetime import datetime
import psycopg2

MARKET_CHANNEL = "market"
USER_CHANNEL = "user"


class WebSocketOrderBook:
    def __init__(self, channel_type, url, data, auth, message_callback, verbose, tokens, cursor, conn):
        self.channel_type = channel_type
        self.url = url
        self.data = data
        self.auth = auth
        self.message_callback = message_callback
        self.verbose = verbose
        self.tokens = tokens
        furl = url + "/ws/" + channel_type
        self.ws = WebSocketApp(
            furl,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
        )
        self.orderbooks = {}
        self.conn = psycopg2.connect(
            dbname="fernandoarroyo",
            user="fernandoarroyo",
            host="localhost",
            port="5432"
        )
        self.cursor = self.conn.cursor()

    def price_change(self, message):
        ts = datetime.fromtimestamp(int(message["timestamp"])/1000).strftime("%Y-%m-%d %H:%M:%S")
        changes = message.get("price_changes", [])
        for change in changes:
            self.cursor.execute("""
            INSERT INTO polymarket_latest_prices (source, market_id, yes_bid_doll, yes_ask_doll, price_doll, ts)
            VALUES ('Polymarket', %s, %s, %s, %s, %s)
            ON CONFLICT (source, market_id) DO UPDATE SET
            yes_bid_doll = COALESCE(EXCLUDED.yes_bid_doll, polymarket_latest_prices.yes_bid_doll),
            yes_ask_doll = COALESCE(EXCLUDED.yes_ask_doll, polymarket_latest_prices.yes_ask_doll),
            price_doll = COALESCE(EXCLUDED.price_doll, polymarket_latest_prices.price_doll),
            ts = COALESCE(EXCLUDED.ts, polymarket_latest_prices.ts)
            """, (message["market"], change["best_bid"], change["best_ask"], change["price"], ts))

            self.cursor.execute("""
            INSERT INTO polymarket_tick_history (source, market_id, yes_bid_doll, yes_ask_doll, price_doll, ts)
            VALUES ('Polymarket', %s, %s, %s, %s, %s)
            """, (message["market"], change["best_bid"], change["best_ask"], change["price"], ts))

        self.conn.commit()

    def book(self, message):
        pass

    def best_bid_ask(self, message):
        pass

    def on_message(self, ws, message):
        if isinstance(message, dict):
            message = message
        elif isinstance(message, str):
            # Only strip and load if it's a string
            clean_message = message.strip()
            if clean_message.lower() == "ping":
                ws.send("pong")
                return
            try:
                message = json.loads(clean_message)
            except:
                return
        else:
            return
        
        try:
            if isinstance(message, list):
                for msg in message:
                    self.on_message(ws, msg)
            else:
                action = message["event_type"]
                match action:
                    case "book":
                        self.book(message)
                    case "price_change":
                        self.price_change(message)
                    case "best_bid_ask":
                        self.best_bid_ask(message)
        except Exception as e:
            print("Error parsing message:", e)
            self.conn.rollback()


    def on_error(self, ws, error):
        print("Error: ", error)
        exit(1)

    def on_close(self, ws, close_status_code, close_msg):
        print("closing")
        exit(0)

    def on_open(self, ws):
        if self.channel_type == MARKET_CHANNEL:
            ws.send(json.dumps({"assets_ids": self.data, "type": MARKET_CHANNEL, "custom_feature_enabled": True}))
            self.subscribe_to_tokens_ids(self.tokens)
        elif self.channel_type == USER_CHANNEL and self.auth:
            ws.send(
                json.dumps(
                    {"markets": self.data, "type": USER_CHANNEL, "auth": self.auth, "custom_feature_enabled": True}
                )
            )
        else:
            exit(1)

        thr = threading.Thread(target=self.ping, args=(ws,))
        thr.start()


    def subscribe_to_tokens_ids(self, assets_ids):
        if self.channel_type == MARKET_CHANNEL:
            self.ws.send(json.dumps({"assets_ids": assets_ids, "operation": "subscribe", "custom_feature_enabled": True}))

    def unsubscribe_to_tokens_ids(self, assets_ids):
        if self.channel_type == MARKET_CHANNEL:
            self.ws.send(json.dumps({"assets_ids": assets_ids, "operation": "unsubscribe", "custom_feature_enabled": True}))


    def ping(self, ws):
        while True:
            ws.send("PING")
            time.sleep(10)

    def run(self):
        self.ws.run_forever()


if __name__ == "__main__":
    url = "wss://ws-subscriptions-clob.polymarket.com"
    #Complete these by exporting them from your initialized client. 
    client = get_client()
    api_Creds = get_api_Creds(client)
    api_key = api_Creds.api_key
    api_secret = api_Creds.api_secret
    api_passphrase = api_Creds.api_passphrase

    asset_ids = [
        "109681959945973300464568698402968596289258214226684818748321941747028805721376",
    ]
    condition_ids = [] # no really need to filter by this one

    auth = {"apiKey": api_key, "secret": api_secret, "passphrase": api_passphrase}
    events = fetch_all_events()
    all_tokens = fetch_all_tokens_events(events)
    
    market_connection = WebSocketOrderBook(
        MARKET_CHANNEL, url, asset_ids, auth, None, True, all_tokens, None, None
    )
    user_connection = WebSocketOrderBook(
        USER_CHANNEL, url, condition_ids, auth, None, True, all_tokens, None, None
    )
    market_connection.run()

    market_connection.subscribe_to_tokens_ids(all_tokens)
    # market_connection.unsubscribe_to_tokens_ids(["123"])


    # user_connection.run()