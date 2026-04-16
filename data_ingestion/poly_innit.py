from py_clob_client.client import ClobClient
from polymarket_events import fetch_all_events, fetch_all_tokens_events
import asyncio
import httpx

def get_api_Creds(client):
    api_Creds = client.derive_api_key()
    return api_Creds


def get_client():
    Private_KEYFILE = "/Users/fernandoarroyo/Desktop/Fer&Tayden/poly_key.pem"
    try:
        with open(Private_KEYFILE, "r") as key_file:
            key = key_file.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"Private key file not found at {Private_KEYFILE}")
    except Exception as e:
        raise Exception(f"Error loading private key: {str(e)}")

    host: str = "https://clob.polymarket.com"
    key: str = key #This is your Private Key. If using email login export from https://reveal.magic.link/polymarket otherwise export from your Web3 Application
    chain_id: int = 137 #No need to adjust this
    POLYMARKET_PROXY_ADDRESS: str = '' #This is the address you deposit/send USDC to to FUND your Polymarket account.

    client = ClobClient(host, key=key, chain_id=chain_id, signature_type=1, funder=POLYMARKET_PROXY_ADDRESS)
    return client

async def get_all_tokens():
    async with httpx.AsyncClient() as client:
        events = await fetch_all_events(client)
        all_tokens = await fetch_all_tokens_events(events)
        return all_tokens

async def get_polymarket_keys():
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
    all_tokens = await get_all_tokens()

    return url, asset_ids, auth, all_tokens



