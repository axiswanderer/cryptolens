"""
Data Collection Service
Fetches OHLCV data from Yahoo Finance and stores in PostgreSQL.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd
import yfinance as yf
from sqlalchemy.orm import Session

from app.database.db import MarketData, SessionLocal
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SUPPORTED_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT",
    "XRPUSDT", "DOTUSDT", "AVAXUSDT", "MATICUSDT", "LINKUSDT",
]

_SYMBOL_MAP = {
    "BTCUSDT":  "BTC-USD",
    "ETHUSDT":  "ETH-USD",
    "SOLUSDT":  "SOL-USD",
    "BNBUSDT":  "BNB-USD",
    "ADAUSDT":  "ADA-USD",
    "XRPUSDT":  "XRP-USD",
    "DOTUSDT":  "DOT-USD",
    "AVAXUSDT": "AVAX-USD",
    "MATICUSDT":"MATIC-USD",
    "LINKUSDT": "LINK-USD",
}


def _fetch_klines_sync(symbol: str, days: int = 730) -> List[dict]:
    """Fetch daily OHLCV from Yahoo Finance (runs in thread pool)."""
    yf_symbol = _SYMBOL_MAP.get(symbol, symbol)
    start_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

    ticker = yf.Ticker(yf_symbol)
    df = ticker.history(start=start_date, interval="1d", auto_adjust=True)

    if df.empty:
        logger.warning(f"[{symbol}] No data from Yahoo Finance")
        return []

    candles = []
    for ts, row in df.iterrows():
        candles.append({
            "symbol": symbol,
            "timestamp": ts.to_pydatetime().replace(tzinfo=None),
            "open":   float(row["Open"]),
            "high":   float(row["High"]),
            "low":    float(row["Low"]),
            "close":  float(row["Close"]),
            "volume": float(row["Volume"]),
        })
    return candles


def save_klines(candles: List[dict], db: Session) -> int:
    """Upsert candles — skip rows that already exist."""
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
    """Backfill daily candles for a symbol."""
    logger.info(f"Backfilling {symbol} for {days} days…")
    candles = await asyncio.to_thread(_fetch_klines_sync, symbol, days)
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
                "low": r.low,  "close": r.close,
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
            candles = await asyncio.to_thread(_fetch_klines_sync, symbol, 5)
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
