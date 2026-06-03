"""
Feature Engineering Service
Computes RSI, MACD, EMA, Bollinger Bands, Volume signals from OHLCV data.
"""
import numpy as np
import pandas as pd
from typing import Optional


# ─── Core Indicator Functions ──────────────────────────────────────────────


def compute_rsi(closes: pd.Series, period: int = 14) -> pd.Series:
    delta = closes.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_macd(
    closes: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    ema_fast = closes.ewm(span=fast, adjust=False).mean()
    ema_slow = closes.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return pd.DataFrame({
        "macd": macd_line,
        "macd_signal": signal_line,
        "macd_hist": histogram,
    })


def compute_ema(closes: pd.Series, period: int) -> pd.Series:
    return closes.ewm(span=period, adjust=False).mean()


def compute_bollinger_bands(
    closes: pd.Series,
    period: int = 20,
    std_dev: float = 2.0,
) -> pd.DataFrame:
    mid = closes.rolling(window=period).mean()
    std = closes.rolling(window=period).std()
    return pd.DataFrame({
        "bb_mid": mid,
        "bb_upper": mid + std_dev * std,
        "bb_lower": mid - std_dev * std,
        "bb_width": (mid + std_dev * std - (mid - std_dev * std)) / mid,
        "bb_pct": (closes - (mid - std_dev * std)) / ((std_dev * 2) * std),
    })


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()


def compute_volume_features(df: pd.DataFrame) -> pd.DataFrame:
    vol = df["volume"]
    vol_ma20 = vol.rolling(20).mean()
    vol_ma5 = vol.rolling(5).mean()
    return pd.DataFrame({
        "volume_ma20": vol_ma20,
        "volume_ratio": vol / vol_ma20,
        "volume_change": vol.pct_change(),
        "volume_surge": (vol > vol_ma20 * 1.5).astype(int),
        "obv": (np.sign(df["close"].diff()) * vol).cumsum(),
    })


# ─── Main Feature Builder ──────────────────────────────────────────────────


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Given a DataFrame with columns [timestamp, open, high, low, close, volume],
    return the same DataFrame enriched with all technical features.
    Requires at least 60 rows for meaningful signals.
    """
    if len(df) < 60:
        raise ValueError(f"Need at least 60 rows, got {len(df)}")

    feat = df.copy()

    # Price-based
    feat["returns"] = feat["close"].pct_change()
    feat["log_returns"] = np.log(feat["close"] / feat["close"].shift(1))
    feat["hl_range"] = (feat["high"] - feat["low"]) / feat["close"]
    feat["price_position"] = (feat["close"] - feat["low"]) / (feat["high"] - feat["low"]).replace(0, np.nan)

    # RSI
    feat["rsi_14"] = compute_rsi(feat["close"], 14)
    feat["rsi_7"] = compute_rsi(feat["close"], 7)

    # MACD
    macd_df = compute_macd(feat["close"])
    feat = pd.concat([feat, macd_df], axis=1)
    feat["macd_bullish"] = (feat["macd"] > feat["macd_signal"]).astype(int)

    # EMAs
    feat["ema9"] = compute_ema(feat["close"], 9)
    feat["ema20"] = compute_ema(feat["close"], 20)
    feat["ema50"] = compute_ema(feat["close"], 50)
    feat["ema200"] = compute_ema(feat["close"], 200)
    feat["ema_cross_20_50"] = (feat["ema20"] > feat["ema50"]).astype(int)
    feat["price_vs_ema20"] = (feat["close"] - feat["ema20"]) / feat["ema20"]
    feat["price_vs_ema50"] = (feat["close"] - feat["ema50"]) / feat["ema50"]

    # Bollinger Bands
    bb_df = compute_bollinger_bands(feat["close"])
    feat = pd.concat([feat, bb_df], axis=1)
    feat["below_bb_lower"] = (feat["close"] < feat["bb_lower"]).astype(int)
    feat["above_bb_upper"] = (feat["close"] > feat["bb_upper"]).astype(int)

    # ATR
    feat["atr_14"] = compute_atr(feat, 14)
    feat["atr_pct"] = feat["atr_14"] / feat["close"]

    # Volume
    vol_df = compute_volume_features(feat)
    feat = pd.concat([feat, vol_df], axis=1)

    # Momentum
    feat["momentum_5"] = feat["close"].pct_change(5)
    feat["momentum_14"] = feat["close"].pct_change(14)
    feat["momentum_30"] = feat["close"].pct_change(30)

    return feat


def get_feature_columns() -> list:
    """Return the ordered list of features used for model training."""
    return [
        "rsi_14", "rsi_7",
        "macd", "macd_signal", "macd_hist", "macd_bullish",
        "ema_cross_20_50", "price_vs_ema20", "price_vs_ema50",
        "bb_width", "bb_pct", "below_bb_lower", "above_bb_upper",
        "atr_pct",
        "volume_ratio", "volume_change", "volume_surge",
        "momentum_5", "momentum_14", "momentum_30",
        "hl_range", "price_position",
        "returns", "log_returns",
    ]


def create_labels(df: pd.DataFrame, horizon: int = 7, threshold: float = 0.03) -> pd.Series:
    """
    Create BUY / HOLD / SELL labels for supervised learning.
    horizon: days into the future to look
    threshold: % move required for directional signal (default 3%)
    """
    future_return = df["close"].shift(-horizon) / df["close"] - 1
    labels = pd.Series("HOLD", index=df.index)
    labels[future_return > threshold] = "BUY"
    labels[future_return < -threshold] = "SELL"
    return labels


def get_latest_features(df: pd.DataFrame) -> Optional[dict]:
    """Get the most recent feature row as a dict for inference."""
    feat = build_features(df)
    cols = get_feature_columns()
    last = feat.dropna(subset=cols).iloc[-1]
    return {col: last[col] for col in cols}
