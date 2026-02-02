import httpx
import time
from tqdm import tqdm
import asyncio


class Kalshi_event_client:
    def __init__(self, shared_queue, interval = 600):
        self.BASE = "https://api.elections.kalshi.com/trade-api/v2/events"
        self.shared_queue = shared_queue
        self.interval = interval

    async def fetch_all_events(self, limit=200, sleep_s=0.5, with_nested_markets=True):
        cursor = None
        events = []
        page_num = 0
        async with httpx.AsyncClient() as client:
            with tqdm(desc="Fetching events", unit="events") as pbar:
                while page_num < 100:
                    page_num += 1
                    params = {"limit": limit, "with_nested_markets": with_nested_markets}
                    if cursor:
                        params["cursor"] = cursor
                        
                    try:
                        resp = await client.get(self.BASE, params=params, timeout=30)

                        resp.raise_for_status()
                    except httpx.HTTPStatusError as e: 
                        print(f"Error with API: {str(e.response.status_code)}")
                        break 

                    page = resp.json()

                    batch = page.get("events")
                    if batch is None:
                        raise RuntimeError(f"Missing 'events' in response: keys={list(page.keys())}")

                    events.extend(batch)
                    pbar.update(len(batch))

                    cursor = page.get("cursor")
                    if not cursor:
                        break
                    await asyncio.sleep(sleep_s)



        return events


    async def run(self):
        while True:
            try:
                events = await self.fetch_all_events()
                print("DONE total events:", len(events))
                packet = {
                    'type' : 'kalshi_events',
                    'source' : 'kalshi',
                    'data' : events
                }
                await self.shared_queue.put(packet)

            except Exception as e:
                print(f"Error with Kalshi events: {str(e)}")
                print("Will reconnect in 2s...")
                await asyncio.sleep(5)
                
            await asyncio.sleep(self.interval)
        
