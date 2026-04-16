import psycopg
from dotenv import load_dotenv
import os

load_dotenv()

DB_config = {
    "host": "arbitrage.c782myq2coht.us-east-2.rds.amazonaws.com",
    "dbname": "Arbitrage",
    "user": "postgres",
    "password": os.getenv("DB_PASSWORD")
}

def create_tables():
    commands = [
        """
        CREATE TABLE IF NOT EXISTS kalshi_events (
            source VARCHAR(20) NOT NULL,
            event_id VARCHAR(50) NOT NULL,
            title VARCHAR(255),
            category VARCHAR(50),
            mutually_exclusive BOOLEAN,
            sub_title VARCHAR(255),
            PRIMARY KEY (source, event_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS kalshi_markets (
            source VARCHAR(20) NOT NULL,
            event_id VARCHAR(50),
            market_id VARCHAR(50) NOT NULL,
            market_type VARCHAR(50),
            title VARCHAR(255),
            open_time TIMESTAMPTZ,
            close_time TIMESTAMPTZ,
            expiration_time TIMESTAMPTZ,
            status VARCHAR(50),
            result VARCHAR(50),
            rules_primary VARCHAR(255),
            can_close_early BOOLEAN,
            early_close_condition VARCHAR(255),
            rules_secondary VARCHAR(255),
            subtitle VARCHAR(255),
            PRIMARY KEY (source, market_id),
            FOREIGN KEY (source, event_id) REFERENCES kalshi_events(source, event_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS polymarket_events (
            source VARCHAR(20) NOT NULL,
            event_id VARCHAR(50) NOT NULL,
            title VARCHAR(255),
            description VARCHAR(255),
            calc_exp_date TIMESTAMPTZ,
            status VARCHAR(50),
            PRIMARY KEY (source, event_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS polymarket_markets (
            source VARCHAR(20),
            event_id VARCHAR(50),
            market_id VARCHAR(50),
            market_type VARCHAR(50),
            title VARCHAR(255),
            open_time TIMESTAMPTZ,
            close_time TIMESTAMPTZ,
            status VARCHAR(50),
            rules_primary VARCHAR(255),
            PRIMARY KEY (source, market_id),
            FOREIGN KEY (source, event_id) REFERENCES polymarket_events(source, event_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS polymarket_latest_prices (
            source VARCHAR(20) NOT NULL,
            market_id VARCHAR(50) NOT NULL,
            yes_bid_doll DOUBLE PRECISION,
            yes_ask_doll DOUBLE PRECISION,
            price_doll DOUBLE PRECISION,
            ts TIMESTAMPTZ,
            PRIMARY KEY (source, market_id),
            FOREIGN KEY (source, market_id) REFERENCES polymarket_markets(source, market_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS kalshi_latest_prices (
            source VARCHAR(20) NOT NULL,
            market_id VARCHAR(50) NOT NULL,
            yes_bid_doll DOUBLE PRECISION,
            yes_ask_doll DOUBLE PRECISION,
            price_doll DOUBLE PRECISION,
            ts TIMESTAMPTZ,
            volume int4,
            vol_doll DOUBLE PRECISION,
            open_interest int4,
            PRIMARY KEY (source, market_id),
            FOREIGN KEY (source, market_id) REFERENCES kalshi_markets(source, market_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS kalshi_tick_history (
            id SERIAL PRIMARY KEY,
            source VARCHAR(20) NOT NULL,
            market_id VARCHAR(50) NOT NULL,
            yes_bid_doll DOUBLE PRECISION,
            yes_ask_doll DOUBLE PRECISION,
            price_doll DOUBLE PRECISION,
            ts TIMESTAMPTZ,
            volume int4,
            vol_doll DOUBLE PRECISION,
            open_interest int4,
            FOREIGN KEY (source, market_id) REFERENCES kalshi_markets(source, market_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS polymarket_tick_history (
            id SERIAL PRIMARY KEY,
            source VARCHAR(20) NOT NULL,
            market_id VARCHAR(50) NOT NULL,
            yes_bid_doll DOUBLE PRECISION,
            yes_ask_doll DOUBLE PRECISION,
            price_doll DOUBLE PRECISION,
            ts TIMESTAMPTZ,
            FOREIGN KEY (source, market_id) REFERENCES polymarket_markets(source, market_id)
        )
        """

    ]
    return commands

if __name__ == "__main__":
    try:
        commands = create_tables()
        with psycopg.connect(**DB_config) as conn:
            with conn.cursor() as cur:
                for command in commands:
                    cur.execute(command)
            conn.commit()
        print("Tables created successfully")
    except Exception as e:
        print(e)