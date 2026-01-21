from websocket import WebSocketApp
import json
import time
import threading
from pmclient import get_api_Creds, get_client
import requests

MARKET_CHANNEL = "market"
USER_CHANNEL = "user"


class WebSocketOrderBook:
    def __init__(self, channel_type, url, data, auth, message_callback, verbose, tokens):
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

    def on_message(self, ws, message):
        print(message)
        pass

    def on_error(self, ws, error):
        print("Error: ", error)
        exit(1)

    def on_close(self, ws, close_status_code, close_msg):
        print("closing")
        exit(0)

    def on_open(self, ws):
        if self.channel_type == MARKET_CHANNEL:
            ws.send(json.dumps({"assets_ids": self.data, "type": MARKET_CHANNEL}))
            self.subscribe_to_tokens_ids(self.tokens)
        elif self.channel_type == USER_CHANNEL and self.auth:
            ws.send(
                json.dumps(
                    {"markets": self.data, "type": USER_CHANNEL, "auth": self.auth}
                )
            )
        else:
            exit(1)

        thr = threading.Thread(target=self.ping, args=(ws,))
        thr.start()


    def subscribe_to_tokens_ids(self, assets_ids):
        if self.channel_type == MARKET_CHANNEL:
            self.ws.send(json.dumps({"assets_ids": assets_ids, "operation": "subscribe"}))

    def unsubscribe_to_tokens_ids(self, assets_ids):
        if self.channel_type == MARKET_CHANNEL:
            self.ws.send(json.dumps({"assets_ids": assets_ids, "operation": "unsubscribe"}))


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
    
    event_url = "https://gamma-api.polymarket.com/events?active=true&closed=false&limit=100"
    response = requests.get(event_url)
    response.raise_for_status()
    events = response.json()
    all_tokens = []
    limit = 500
    for event in events:
        for market in event["markets"]:
            clob_tokens = json.loads(market["clobTokenIds"])
            all_tokens.extend(clob_tokens)
            if len(all_tokens) >= limit:
                break
            

    print(all_tokens)

    market_connection = WebSocketOrderBook(
        MARKET_CHANNEL, url, asset_ids, auth, None, True, all_tokens
    )
    user_connection = WebSocketOrderBook(
        USER_CHANNEL, url, condition_ids, auth, None, True, all_tokens
    )

    market_connection.run()

    market_connection.subscribe_to_tokens_ids(all_tokens)
    # market_connection.unsubscribe_to_tokens_ids(["123"])


    # user_connection.run()