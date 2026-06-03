"""
Prediction Service
Loads the trained XGBoost model and generates investment signals.
"""
import logging
from pathlib import Path
from typing import Optional
import joblib
import numpy as np

from app.services.feature_engineering import (
    build_features,
    get_feature_columns,
    get_latest_features,
)
from app.services.data_collector import load_ohlcv
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Singleton model cache
_model_bundle = None


def load_model():
    global _model_bundle
    model_path = Path(settings.MODEL_PATH)
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found at {model_path}. "
            "Run: python -m app.ml.train_model"
        )
    _model_bundle = joblib.load(model_path)
    logger.info(f"Model loaded from {model_path}")
    return _model_bundle


def get_model():
    global _model_bundle
    if _model_bundle is None:
        load_model()
    return _model_bundle


TIMEFRAME_DAYS = {
    "3d": 3,
    "7d": 7,
    "14d": 14,
    "30d": 30,
}


def build_explanation(features: dict, recommendation: str) -> list[str]:
    """Rule-based explanation of the signal."""
    reasons = []
    rsi = features.get("rsi_14", 50)
    macd = features.get("macd", 0)
    macd_bullish = features.get("macd_bullish", 0)
    ema_cross = features.get("ema_cross_20_50", 0)
    price_vs_ema20 = features.get("price_vs_ema20", 0)
    bb_pct = features.get("bb_pct", 0.5)
    vol_ratio = features.get("volume_ratio", 1.0)
    momentum_5 = features.get("momentum_5", 0)
    momentum_14 = features.get("momentum_14", 0)

    # RSI
    if rsi < 30:
        reasons.append(f"RSI = {rsi:.1f} — oversold, bounce likely")
    elif rsi > 70:
        reasons.append(f"RSI = {rsi:.1f} — overbought, pullback risk")
    elif rsi < 45 and recommendation == "BUY":
        reasons.append(f"RSI = {rsi:.1f} — room to run upward")
    elif rsi > 55 and recommendation == "SELL":
        reasons.append(f"RSI = {rsi:.1f} — momentum fading")

    # MACD
    if macd_bullish and macd > 0:
        reasons.append("Bullish MACD crossover — positive momentum")
    elif not macd_bullish and macd < 0:
        reasons.append("Bearish MACD crossover — negative momentum")
    elif macd_bullish:
        reasons.append("MACD above signal line — trend turning bullish")

    # EMA alignment
    if ema_cross:
        reasons.append("EMA20 above EMA50 — short-term uptrend intact")
    else:
        reasons.append("EMA20 below EMA50 — short-term downtrend")

    # Bollinger Band position
    if bb_pct < 0.1:
        reasons.append("Price near Bollinger lower band — statistically cheap")
    elif bb_pct > 0.9:
        reasons.append("Price near Bollinger upper band — statistically extended")

    # Volume
    if vol_ratio > 1.5:
        reasons.append(f"Volume surge: {vol_ratio:.1f}x average — conviction behind move")

    # Momentum
    if momentum_5 > 0.05:
        reasons.append(f"Strong 5-day momentum: +{momentum_5*100:.1f}%")
    elif momentum_5 < -0.05:
        reasons.append(f"Weak 5-day momentum: {momentum_5*100:.1f}%")

    return reasons[:5]


def predict(symbol: str, timeframe: str = "7d") -> dict:
    """
    Run full prediction pipeline for a symbol.

    Returns:
        dict with recommendation, confidence, score, reasons, and indicators
    """
    # Load data
    df = load_ohlcv(symbol, limit=300)
    if df.empty or len(df) < 60:
        raise ValueError(f"Insufficient data for {symbol}. Run backfill first.")

    # Build features
    feat_df = build_features(df)
    feature_cols = get_feature_columns()
    latest_row = feat_df.dropna(subset=feature_cols).iloc[-1]
    features = {col: latest_row[col] for col in feature_cols}

    # Run model
    bundle = get_model()
    model = bundle["model"]
    inv_label_map = bundle["inv_label_map"]

    X = np.array([[features[col] for col in feature_cols]])
    proba = model.predict_proba(X)[0]  # [P(BUY), P(HOLD), P(SELL)]
    pred_class = int(np.argmax(proba))
    recommendation = inv_label_map[pred_class]
    confidence = float(round(proba[pred_class] * 100, 1))

    # Score: weighted blend of confidence + indicator alignment
    bullish_signals = sum([
        features.get("rsi_14", 50) < 40,
        features.get("macd_bullish", 0) == 1,
        features.get("ema_cross_20_50", 0) == 1,
        features.get("bb_pct", 0.5) < 0.3,
        features.get("volume_surge", 0) == 1,
        features.get("momentum_5", 0) > 0.02,
    ])
    bearish_signals = sum([
        features.get("rsi_14", 50) > 65,
        features.get("macd_bullish", 0) == 0,
        features.get("ema_cross_20_50", 0) == 0,
        features.get("bb_pct", 0.5) > 0.8,
        features.get("momentum_5", 0) < -0.02,
    ])

    if recommendation == "BUY":
        score = round(50 + (bullish_signals / 6) * 45 + (confidence - 50) * 0.1)
    elif recommendation == "SELL":
        score = round(50 + (bearish_signals / 5) * 45 + (confidence - 50) * 0.1)
    else:
        score = round(40 + (confidence - 40) * 0.5)
    score = max(0, min(100, score))

    # Indicators snapshot
    current_price = float(df["close"].iloc[-1])
    indicators = {
        "rsi": round(float(latest_row["rsi_14"]), 2),
        "macd": round(float(latest_row["macd"]), 4),
        "macd_signal": round(float(latest_row["macd_signal"]), 4),
        "ema20": round(float(latest_row["ema20"]), 4),
        "ema50": round(float(latest_row["ema50"]), 4),
        "bb_upper": round(float(latest_row["bb_upper"]), 4),
        "bb_lower": round(float(latest_row["bb_lower"]), 4),
        "bb_mid": round(float(latest_row["bb_mid"]), 4),
        "atr": round(float(latest_row["atr_14"]), 4),
        "volume_ratio": round(float(latest_row["volume_ratio"]), 2),
        "momentum_5d": round(float(latest_row["momentum_5"]) * 100, 2),
        "momentum_14d": round(float(latest_row["momentum_14"]) * 100, 2),
    }

    # Probabilities for all classes
    probabilities = {
        "BUY": round(float(proba[0]) * 100, 1),
        "HOLD": round(float(proba[1]) * 100, 1),
        "SELL": round(float(proba[2]) * 100, 1),
    }

    reasons = build_explanation(features, recommendation)

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "current_price": current_price,
        "recommendation": recommendation,
        "confidence": confidence,
        "score": score,
        "probabilities": probabilities,
        "reasons": reasons,
        "indicators": indicators,
    }
