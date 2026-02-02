from clients import KalshiWebSocketClient
from polymarket_events import PolyEvents
from polymarket_api import WebSocketOrderBook
from poly_innit import get_polymarket_keys
from kalshi_innit import get_kalshi_keys
from kalshi_events_api import Kalshi_event_client
from db_worker import DatabaseWorker
import asyncio

MARKET_CHANNEL = "market"
USER_CHANNEL = "user"

async def main():
    shared_queue = asyncio.Queue(maxsize=1000)
    
    db_librarian = DatabaseWorker(shared_queue)

    KEYID, private_key, env = get_kalshi_keys()
    url, asset_ids, auth, all_tokens = await get_polymarket_keys()

    kalshi_ws = KalshiWebSocketClient(shared_queue, KEYID, private_key, env)
    kalshi_events = Kalshi_event_client(shared_queue)
    polymarket_ws = WebSocketOrderBook(shared_queue,
        MARKET_CHANNEL, url, asset_ids, auth, None, True, all_tokens
    )
    polymarket_events = PolyEvents(shared_queue)

    print("Starting Arbitrage Data Engine...")

    tasks = [
        asyncio.create_task(db_librarian.run()),
        asyncio.create_task(kalshi_ws.run()),
        asyncio.create_task(polymarket_events.run()),
        asyncio.create_task(polymarket_ws.run()),
        asyncio.create_task(kalshi_events.run()),
    ]

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        print("Shutting down Arbitrage Data Engine...")
    finally:
        print("System offline")
    

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Main loop interrupted")
        pass

    

