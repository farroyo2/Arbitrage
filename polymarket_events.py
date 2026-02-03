import httpx
from tqdm import tqdm
import json
import asyncio

BASE = "https://gamma-api.polymarket.com/events?order=id&ascending=false&closed=false&limit=100"

async def fetch_all_tokens_events(events):
    all_tokens = []
    for event in events:
        for market in event.get("markets", []):
            raw = market.get("clobTokenIds", "[]")
            if not raw:
                continue
            try:
                clob_tokens = json.loads(raw)
            except json.JSONDecodeError:
                print(f"Error decoding clobTokenIds: {raw}")
                continue
            all_tokens.extend(clob_tokens)
    return all_tokens

async def fetch_all_events(client):
    all_events = []
    offset = 0
    try:
        while True:
            response = await client.get(BASE + f"&offset={offset}")
            response.raise_for_status()
            events = response.json()
            all_events.extend(events)
            offset += 100
            if len(events) < 100:
                break
    except Exception as e:
        print(f"Error with Polymarket events: {str(e)}")
    return all_events

class PolyEvents:
    def __init__(self, shared_queue, interval = 600):
        self.shared_queue = shared_queue
        self.interval = interval

    async def run(self):
        print("Starting Polymarket events fetcher... \n")
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    events = await fetch_all_events(client)
                    print("DONE total Polymarket events:", len(events))

                    packet = {
                        'type': 'polymarket_events',
                        'data': events
                    }

                    await self.shared_queue.put(packet)
            
                except Exception as e:
                    print(f"Error with Polymarket events: {str(e)}")
                
                await asyncio.sleep(self.interval)




        