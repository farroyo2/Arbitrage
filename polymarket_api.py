import websockets
import json
import time
import httpx
from datetime import datetime
import asyncio

MARKET_CHANNEL = "market"
USER_CHANNEL = "user"


class WebSocketOrderBook:
    def __init__(self, shared_queue, channel_type, url, data, auth, message_callback, verbose, tokens):
        self.shared_queue = shared_queue
        self.channel_type = channel_type
        self.url = url
        self.data = data
        self.auth = auth
        self.message_callback = message_callback
        self.verbose = verbose
        self.tokens = tokens
        self.furl = url + "/ws/" + channel_type
        self.ws = None
        self.orderbooks = {}

    async def run(self):
        while True:
            try:
                async with websockets.connect(
                self.furl,
                ) as ws:
                    self.ws = ws
                    await self.on_open(ws)
                    await self.handler()
            except Exception as e:
                print("Error in Polymarket run:", e)
                await asyncio.sleep(5)

    async def price_change(self, message):
        try:
            package = {
                "type" : "polymarket_prices",
                "data" : message

            }
            await self.shared_queue.put(package)
        except Exception as e:
            print("Error in Polymarket price_change message:", e)
            await asyncio.sleep(2)

    async def book(self, message):
        pass

    async def best_bid_ask(self, message):
        pass

    async def handler(self):
        try:
            async for message in self.ws:
                await self.on_message(message)
        except websockets.exceptions.ConnectionClosedError:
            await self.on_close()
        except Exception as e:
            await self.on_error(e)
            await asyncio.sleep(2)

    async def on_message(self, message):
        if isinstance(message, dict):
            message = message
        elif isinstance(message, str):
            # Only strip and load if it's a string
            clean_message = message.strip()
            if clean_message.lower() == "ping":
                await self.ws.send("pong")
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
                    await self.on_message(msg)
            else:
                action = message["event_type"]
                match action:
                    case "book":
                        await self.book(message)
                    case "price_change":
                        await self.price_change(message)
                    case "best_bid_ask":
                        await self.best_bid_ask(message)
        except Exception as e:
            print("Error parsing message:", e)
            await asyncio.sleep(2)
 


    async def on_error(self, error):
        print("Error: ", error)
        await asyncio.sleep(2)

    async def on_close(self):
        print("closing Polymarket Websocket")
        await asyncio.sleep(2)

    async def on_open(self, ws):
        try: 
                self.ws = ws
                if self.channel_type == MARKET_CHANNEL:
                    await ws.send(json.dumps({"assets_ids": self.data, "type": MARKET_CHANNEL, "custom_feature_enabled": True}))
                    await self.subscribe_to_tokens_ids(self.tokens)
                elif self.channel_type == USER_CHANNEL and self.auth:
                    await ws.send(
                        json.dumps(
                            {"markets": self.data, "type": USER_CHANNEL, "auth": self.auth, "custom_feature_enabled": True}
                        )
                    )
                else:
                    exit(1)
        except Exception as e:
            print("Error in opening Poly websocket")
            await asyncio.sleep(2)


    async def subscribe_to_tokens_ids(self, assets_ids):
        if self.channel_type == MARKET_CHANNEL:
            await self.ws.send(json.dumps({"assets_ids": assets_ids, "operation": "subscribe", "custom_feature_enabled": True}))

    async def unsubscribe_to_tokens_ids(self, assets_ids):
        if self.channel_type == MARKET_CHANNEL:
            await self.ws.send(json.dumps({"assets_ids": assets_ids, "operation": "unsubscribe", "custom_feature_enabled": True}))



    #user_connection = WebSocketOrderBook(
        # USER_CHANNEL, url, condition_ids, auth, None, True, all_tokens, None, None
    #)

    # market_connection.unsubscribe_to_tokens_ids(["123"])