import httpx
from tqdm import tqdm
import json
import asyncio

BASE = "https://gamma-api.polymarket.com/events?"

async def fetch_all_tokens_events(events_list):
    all_tokens = []
    for events in events_list:
        cat_tokens = set()
        for event in events:
            event_liq = float(event.get("liquidity", 0))
            if event_liq < 1000:
                continue
            
            for market in event.get("markets", []):
                market_liq = float(market.get("liquidity", 0))
                if market_liq < 100:
                    continue
                raw = market.get("clobTokenIds", "[]")
                if not raw:
                    continue
                try:
                    clob_tokens = json.loads(raw)
                except json.JSONDecodeError:
                    print(f"Error decoding clobTokenIds: {raw}")
                    continue
                cat_tokens.update(clob_tokens)
        all_tokens.extend(cat_tokens)
    return all_tokens

async def fetch_category_events(client, category):
    array = []
    offset = 0
    try:
        while True:
            response = await client.get(BASE + f"&tag_id={category}&ascending=false&closed=false&limit=100&offset={offset}")
            response.raise_for_status()
            events = response.json()
            array.extend(events)
            offset += 100
            if len(events) < 100:
                break
    except Exception as e:
        print(f"Error with Polymarket events: {str(e)}")
    return array

async def fetch_all_events(client):
    categories = ["100639", "2", "596"] # sports, politics, climate
    tasks = [fetch_category_events(client, category) for category in categories]
    all_events = await asyncio.gather(*tasks)
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
                    cat_events = await fetch_all_events(client)
                    events = []
                    for cat in cat_events:
                        events.extend(cat)
                    
                    print("DONE total Polymarket events:", len(events))

                    packet = {
                        'type': 'polymarket_events',
                        'data': events
                    }

                    await self.shared_queue.put(packet)
            
                except Exception as e:
                    print(f"Error with Polymarket events: {str(e)}")
                
                await asyncio.sleep(self.interval)




        