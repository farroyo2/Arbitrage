from clients import KalshiWebSocketClient
from polymarket_events import PolyEvents
from polymarket_api import WebSocketOrderBook
import pmclient
from kalshi_innit import get_keys
from kalshi_events import KalshiEvents
from database_librarian import DatabaseLibrarian
import asyncio

async def main():
    shared_queue = asyncio.Queue(maxsize=1000)
    
    db_librarian = DatabaseLibrarian(shared_queue)

    KEYID, private_key, env = get_keys()

    kalshi_ws = KalshiWebSocketClient(shared_queue, KEYID, private_key, env)
    kalshi_events = KalshiEvents(shared_queue)
    polymarket_ws = WebSocketOrderBook(shared_queue)
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
            pass

    

