"""
XGBoost Model Training Pipeline
Run: python -m app.ml.train_model
"""
import logging
import os
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple

from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
import xgboost as xgb

from app.services.feature_engineering import (
    build_features,
    get_feature_columns,
    create_labels,
)
from app.services.data_collector import load_ohlcv
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT",
    "XRPUSDT", "DOTUSDT", "AVAXUSDT",
]

LABEL_MAP = {"BUY": 0, "HOLD": 1, "SELL": 2}
INV_LABEL_MAP = {0: "BUY", 1: "HOLD", 2: "SELL"}


def load_all_data() -> pd.DataFrame:
    """Load and combine OHLCV data for all symbols."""
    frames = []
    for symbol in SYMBOLS:
        df = load_ohlcv(symbol, limit=1000)
        if len(df) < 100:
            logger.warning(f"Not enough data for {symbol}, skipping")
            continue
        df["symbol"] = symbol
        frames.append(df)

    if not frames:
        raise ValueError("No training data found. Run backfill_all() first.")

    combined = pd.concat(frames, ignore_index=True)
    logger.info(f"Loaded {len(combined)} total rows across {len(frames)} symbols")
    return combined


def prepare_dataset(
    df: pd.DataFrame,
    horizon: int = 7,
    threshold: float = 0.03,
) -> Tuple[pd.DataFrame, pd.Series]:
    """Build features + labels from raw OHLCV."""
    all_X = []
    all_y = []
    feature_cols = get_feature_columns()

    for symbol, group in df.groupby("symbol"):
        group = group.sort_values("timestamp").reset_index(drop=True)
        if len(group) < 100:
            continue
        try:
            feat = build_features(group)
            labels = create_labels(group, horizon, threshold)
            valid = feat.dropna(subset=feature_cols)
            valid_labels = labels.loc[valid.index].dropna()
            valid = valid.loc[valid_labels.index]

            # Remove last `horizon` rows (no future data to label)
            valid = valid.iloc[:-horizon]
            valid_labels = valid_labels.iloc[:-horizon]

            all_X.append(valid[feature_cols])
            all_y.append(valid_labels)
        except Exception as e:
            logger.warning(f"Feature error for {symbol}: {e}")
            continue

    X = pd.concat(all_X, ignore_index=True)
    y = pd.concat(all_y, ignore_index=True)
    return X, y


def train(horizon: int = 7, threshold: float = 0.03) -> dict:
    """Full training pipeline. Returns metrics."""
    logger.info("Loading data…")
    df = load_all_data()

    logger.info("Building features and labels…")
    X, y = prepare_dataset(df, horizon, threshold)

    label_dist = y.value_counts().to_dict()
    logger.info(f"Label distribution: {label_dist}")

    # Encode labels
    y_encoded = y.map(LABEL_MAP)

    # Time-series cross-validation
    tscv = TimeSeriesSplit(n_splits=5)
    cv_scores = []

    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=5,
        gamma=0.1,
        use_label_encoder=False,
        eval_metric="mlogloss",
        random_state=42,
        n_jobs=-1,
    )

    logger.info("Running time-series cross-validation…")
    for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y_encoded.iloc[train_idx], y_encoded.iloc[val_idx]

        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )
        preds = model.predict(X_val)
        acc = accuracy_score(y_val, preds)
        cv_scores.append(acc)
        logger.info(f"Fold {fold + 1} accuracy: {acc:.3f}")

    logger.info(f"Mean CV accuracy: {np.mean(cv_scores):.3f} ± {np.std(cv_scores):.3f}")

    # Final model on all data
    logger.info("Training final model on full dataset…")
    model.fit(X, y_encoded)

    # Feature importance
    importance = dict(zip(get_feature_columns(), model.feature_importances_))
    top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]
    logger.info("Top features:")
    for feat, imp in top_features:
        logger.info(f"  {feat}: {imp:.4f}")

    # Save
    model_path = Path(settings.MODEL_PATH)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        "model": model,
        "feature_cols": get_feature_columns(),
        "label_map": LABEL_MAP,
        "inv_label_map": INV_LABEL_MAP,
        "cv_scores": cv_scores,
        "horizon": horizon,
        "threshold": threshold,
    }, model_path)
    logger.info(f"Model saved to {model_path}")

    final_preds = model.predict(X)
    report = classification_report(y_encoded, final_preds, target_names=["BUY", "HOLD", "SELL"])
    logger.info(f"\n{report}")

    return {
        "cv_mean": float(np.mean(cv_scores)),
        "cv_std": float(np.std(cv_scores)),
        "train_samples": len(X),
        "label_distribution": label_dist,
        "model_path": str(model_path),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    metrics = train()
    print("\n=== Training Complete ===")
    for k, v in metrics.items():
        print(f"{k}: {v}")
