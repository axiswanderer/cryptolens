"""
Data Collection Service
Fetches OHLCV data from Binance and stores in PostgreSQL.
Runs on a schedule via APScheduler.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd
import httpx
from sqlalchemy.orm import Session

from app.database.db import MarketData, SessionLocal
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SUPPORTED_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT",
    "XRPUSDT", "DOTUSDT", "AVAXUSDT", "MATICUSDT", "LINKUSDT",
]

BINANCE_BASE = "https://api.binance.com"

INTERVAL_MAP = {
    "1h": "1h",
    "4h": "4h",
    "1d": "1d",
}


async def fetch_klines(
    symbol: str,
    interval: str = "1d",
    limit: int = 500,
    start_time: Optional[int] = None,
) -> List[dict]:
    """Fetch candlestick data from Binance REST API."""
    url = f"{BINANCE_BASE}/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
    }
    if start_time:
        params["startTime"] = start_time

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        raw = response.json()

    candles = []
    for k in raw:
        candles.append({
            "symbol": symbol,
            "timestamp": datetime.utcfromtimestamp(k[0] / 1000),
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
        })
    return candles


def save_klines(candles: List[dict], db: Session) -> int:
    """Save klines to DB, skip duplicates."""
    saved = 0
    for c in candles:
        exists = (
            db.query(MarketData)
            .filter(
                MarketData.symbol == c["symbol"],
                MarketData.timestamp == c["timestamp"],
            )
            .first()
        )
        if not exists:
            db.add(MarketData(**c))
            saved += 1
    db.commit()
    return saved


async def fetch_and_store(symbol: str, interval: str = "1d", limit: int = 500):
    """Fetch latest klines for a symbol and persist them."""
    db = SessionLocal()
    try:
        candles = await fetch_klines(symbol, interval, limit)
        saved = save_klines(candles, db)
        logger.info(f"[{symbol}] Saved {saved} new candles ({interval})")
        return saved
    except Exception as e:
        logger.error(f"[{symbol}] Fetch error: {e}")
        raise
    finally:
        db.close()


async def backfill_symbol(symbol: str, days: int = 730):
    """Backfill 2 years of daily candles for a symbol."""
    logger.info(f"Backfilling {symbol} for {days} days…")
    start_ts = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)
    candles = await fetch_klines(symbol, "1d", limit=1000, start_time=start_ts)
    db = SessionLocal()
    try:
        saved = save_klines(candles, db)
        logger.info(f"[{symbol}] Backfilled {saved} candles")
    finally:
        db.close()


async def backfill_all(days: int = 730):
    """Backfill all supported symbols."""
    for symbol in SUPPORTED_SYMBOLS:
        await backfill_symbol(symbol, days)


def load_ohlcv(symbol: str, limit: int = 200, db: Session = None) -> pd.DataFrame:
    """Load OHLCV from DB into a DataFrame."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        rows = (
            db.query(MarketData)
            .filter(MarketData.symbol == symbol)
            .order_by(MarketData.timestamp.desc())
            .limit(limit)
            .all()
        )
        if not rows:
            return pd.DataFrame()

        data = [
            {
                "timestamp": r.timestamp,
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.volume,
            }
            for r in rows
        ]
        df = pd.DataFrame(data).sort_values("timestamp").reset_index(drop=True)
        return df
    finally:
        if close_db:
            db.close()


async def scheduled_fetch():
    """Called by APScheduler every hour."""
    logger.info("Scheduled fetch starting…")
    for symbol in SUPPORTED_SYMBOLS:
        await fetch_and_store(symbol, interval="1d", limit=10)
    logger.info("Scheduled fetch complete")
