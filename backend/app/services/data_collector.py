"""
Data Collection Service
Fetches OHLCV data from CryptoCompare and stores in PostgreSQL.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional

import httpx
import pandas as pd
from sqlalchemy.orm import Session

from app.database.db import MarketData, SessionLocal
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SUPPORTED_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT",
    "XRPUSDT", "DOTUSDT", "AVAXUSDT", "MATICUSDT", "LINKUSDT",
]

_CC_BASE = "https://min-api.cryptocompare.com/data/v2/histoday"

_SYMBOL_MAP = {
    "BTCUSDT":  "BTC",
    "ETHUSDT":  "ETH",
    "SOLUSDT":  "SOL",
    "BNBUSDT":  "BNB",
    "ADAUSDT":  "ADA",
    "XRPUSDT":  "XRP",
    "DOTUSDT":  "DOT",
    "AVAXUSDT": "AVAX",
    "MATICUSDT":"MATIC",
    "LINKUSDT": "LINK",
}


async def _fetch_klines(symbol: str, days: int = 730) -> List[dict]:
    """Fetch daily OHLCV from CryptoCompare."""
    cc_sym = _SYMBOL_MAP.get(symbol, symbol.replace("USDT", ""))

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            _CC_BASE,
            params={"fsym": cc_sym, "tsym": "USD", "limit": days},
        )
        r.raise_for_status()
        data = r.json()

    if data.get("Response") != "Success":
        raise ValueError(f"CryptoCompare error for {symbol}: {data.get('Message')}")

    candles = []
    for row in data["Data"]["Data"]:
        if row["close"] == 0:
            continue
        candles.append({
            "symbol":    symbol,
            "timestamp": datetime.utcfromtimestamp(row["time"]),
            "open":      float(row["open"]),
            "high":      float(row["high"]),
            "low":       float(row["low"]),
            "close":     float(row["close"]),
            "volume":    float(row["volumeto"]),
        })
    return candles


def save_klines(candles: List[dict], db: Session) -> int:
    """Insert candles, skipping duplicates."""
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


async def backfill_symbol(symbol: str, days: int = 730):
    """Backfill daily candles for one symbol."""
    logger.info(f"Backfilling {symbol} for {days} days…")
    candles = await _fetch_klines(symbol, days)
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
    """Load OHLCV from DB into a sorted DataFrame."""
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

        df = pd.DataFrame([
            {
                "timestamp": r.timestamp,
                "open": r.open, "high": r.high,
                "low":  r.low,  "close": r.close,
                "volume": r.volume,
            }
            for r in rows
        ]).sort_values("timestamp").reset_index(drop=True)
        return df
    finally:
        if close_db:
            db.close()


async def scheduled_fetch():
    """APScheduler hook — runs every hour to keep data fresh."""
    logger.info("Scheduled fetch starting…")
    for symbol in SUPPORTED_SYMBOLS:
        try:
            candles = await _fetch_klines(symbol, days=5)
            db = SessionLocal()
            try:
                saved = save_klines(candles, db)
                if saved:
                    logger.info(f"[{symbol}] +{saved} new candles")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"[{symbol}] Scheduled fetch error: {e}")
    logger.info("Scheduled fetch complete")
