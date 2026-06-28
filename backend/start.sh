#!/bin/bash
set -e

echo "=== CryptoLens API Starting ==="
mkdir -p models

MODEL="${MODEL_PATH:-./models/xgboost_model.joblib}"

if [ ! -f "$MODEL" ]; then
    echo ">>> No model found — backfilling historical data (~2 min)..."
    python scripts/backfill.py
    echo ">>> Training XGBoost model (~30s)..."
    python -m app.ml.train_model
    echo ">>> Model ready!"
fi

echo ">>> Starting API on port ${PORT:-8000}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
