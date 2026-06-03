"""
Standalone backfill script.
Run from backend/: python scripts/backfill.py [--symbol BTCUSDT] [--days 730]
"""
import asyncio
import argparse
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.data_collector import backfill_symbol, backfill_all, SUPPORTED_SYMBOLS
from app.database.db import create_tables

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


async def main():
    parser = argparse.ArgumentParser(description="Backfill historical crypto data")
    parser.add_argument("--symbol", type=str, help="Single symbol (e.g. BTCUSDT). Omit for all.")
    parser.add_argument("--days", type=int, default=730, help="Days of history to fetch (default 730)")
    args = parser.parse_args()

    create_tables()

    if args.symbol:
        symbol = args.symbol.upper()
        if symbol not in SUPPORTED_SYMBOLS:
            print(f"Error: {symbol} not supported. Choices: {SUPPORTED_SYMBOLS}")
            sys.exit(1)
        await backfill_symbol(symbol, args.days)
    else:
        print(f"Backfilling all {len(SUPPORTED_SYMBOLS)} symbols for {args.days} days…")
        await backfill_all(args.days)

    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
