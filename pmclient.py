from py_clob_client.client import ClobClient

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



