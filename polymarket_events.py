import requests
import time
from tqdm import tqdm
import psycopg
from asyncio import Queue
import json


class PolyEvents:
    def __init__(self, shared_queue, interval = 600):
        self.BASE = "https://gamma-api.polymarket.com/events?order=id&ascending=false&closed=false&limit=1000"
        self.shared_queue = shared_queue
        self.interval = interval


    def fetch_all_tokens_events(events):
        all_tokens = []
        for event in events:
            for market in event["markets"]:
                clob_tokens = json.loads(market["clobTokenIds"])
                all_tokens.extend(clob_tokens)
        return all_tokens

    def fetch_all_events(BASE):
        response = requests.get(BASE)
        response.raise_for_status()
        events = response.json()
        return events

    def run(self):
        while True:
            try:
                event = fetch_all_events()
                print("DONE total events:", len(events))

                for (event) in events:
                    packet = {
                        'type': 'polymarket_events',
                        'data': event
                    }

                    await self.shared_queue.put(packet)
            
            except Exception as e:
                print(f"Error with Polymarket events: {str(e)}")
            
            await asyncio.sleep(self.interval)




        