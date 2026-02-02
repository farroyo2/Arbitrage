import httpx
from tqdm import tqdm
import json
import asyncio

BASE = "https://gamma-api.polymarket.com/events?order=id&ascending=false&closed=false&limit=1000"

async def fetch_all_tokens_events(events):
    all_tokens = []
    for event in events:
        for market in event["markets"]:
            clob_tokens = json.loads(market["clobTokenIds"])
            all_tokens.extend(clob_tokens)
    return all_tokens

async def fetch_all_events(client):
    response = await client.get(BASE)
    response.raise_for_status()
    events = response.json()
    return events

class PolyEvents:
    def __init__(self, shared_queue, interval = 600):
        self.shared_queue = shared_queue
        self.interval = interval

    async def run(self):
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    events = await fetch_all_events(client)
                    print("DONE total events:", len(events))

                    packet = {
                        'type': 'polymarket_events',
                        'data': events
                    }

                    await self.shared_queue.put(packet)
            
                except Exception as e:
                    print(f"Error with Polymarket events: {str(e)}")
                
                await asyncio.sleep(self.interval)




        