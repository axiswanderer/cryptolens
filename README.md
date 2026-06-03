# CryptoLens MVP

AI-powered crypto investment signal engine. XGBoost trained on technical indicators from live Binance data.

## Architecture

```
Frontend (Next.js)
     ↓
Backend API (FastAPI)
     ↓
Feature Engineering (RSI, MACD, EMA, BB, Volume)
     ↓
XGBoost Prediction Model
     ↓
PostgreSQL (market_data, predictions)
     ↓
Binance REST API (OHLCV data)
```

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14, Tailwind CSS, lightweight-charts |
| Backend | FastAPI, APScheduler, Pydantic |
| ML | XGBoost, scikit-learn, pandas, ta |
| Database | PostgreSQL 16 + SQLAlchemy |
| Data | Binance REST API |
| Deploy | Docker Compose |

---

## Getting Started

### 1. Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL (or Docker)
- Binance account (free API key — read-only is enough)

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env: set DATABASE_URL and BINANCE_API_KEY
```

### 3. Database

```bash
# With Docker:
docker run -d \
  --name cryptolens-db \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=cryptolens \
  -p 5432:5432 \
  postgres:16-alpine

# Tables are created automatically on first run
```

### 4. Backfill Historical Data

```bash
cd backend

# Backfill all symbols (2 years of daily candles)
python scripts/backfill.py

# Or single symbol
python scripts/backfill.py --symbol BTCUSDT --days 730
```

This takes ~2–3 minutes. Required before training.

### 5. Train the Model

```bash
cd backend
python -m app.ml.train_model
```

Output:
```
Fold 1 accuracy: 0.612
Fold 2 accuracy: 0.598
Fold 3 accuracy: 0.634
Mean CV accuracy: 0.614 ± 0.014
Model saved to ./models/xgboost_model.joblib
```

### 6. Run the Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 7. Run the Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

App: http://localhost:3000

---

## Docker (Full Stack)

```bash
# Copy and fill in API keys
cp backend/.env.example .env

# Build and start everything
docker-compose up --build

# First time only — backfill data
docker-compose exec backend python scripts/backfill.py

# Train model
docker-compose exec backend python -m app.ml.train_model
```

---

## API Endpoints

### `POST /api/v1/analyze`

Run AI prediction for a coin.

```json
// Request
{
  "symbol": "BTCUSDT",
  "timeframe": "7d"
}

// Response
{
  "symbol": "BTCUSDT",
  "timeframe": "7d",
  "current_price": 68420.0,
  "recommendation": "BUY",
  "confidence": 73.4,
  "score": 81,
  "probabilities": { "BUY": 73.4, "HOLD": 18.2, "SELL": 8.4 },
  "reasons": [
    "RSI = 31.2 — oversold, bounce likely",
    "Bullish MACD crossover — positive momentum",
    "EMA20 above EMA50 — short-term uptrend intact"
  ],
  "indicators": {
    "rsi": 31.2,
    "macd": 0.0012,
    "ema20": 67800.0,
    "ema50": 65200.0,
    ...
  }
}
```

### `GET /api/v1/ohlcv/{symbol}?limit=200`

Raw OHLCV data for charting.

### `GET /api/v1/predictions/{symbol}`

Past prediction history for a symbol.

### `GET /api/v1/health`

System health: model loaded, DB connected.

### `POST /api/v1/backfill`

Trigger background data fetch.

---

## Features Used by Model

| Feature | Description |
|---|---|
| `rsi_14` | RSI 14-period |
| `rsi_7` | RSI 7-period |
| `macd` | MACD line |
| `macd_signal` | MACD signal line |
| `macd_hist` | MACD histogram |
| `macd_bullish` | Binary: MACD > signal |
| `ema_cross_20_50` | Binary: EMA20 > EMA50 |
| `price_vs_ema20` | % distance from EMA20 |
| `price_vs_ema50` | % distance from EMA50 |
| `bb_width` | Bollinger band width |
| `bb_pct` | Price position within bands |
| `below_bb_lower` | Binary: below lower band |
| `above_bb_upper` | Binary: above upper band |
| `atr_pct` | ATR as % of price |
| `volume_ratio` | Volume vs 20-day avg |
| `volume_change` | % change in volume |
| `volume_surge` | Binary: volume > 1.5x avg |
| `momentum_5` | 5-day price return |
| `momentum_14` | 14-day price return |
| `momentum_30` | 30-day price return |
| `hl_range` | High-low range / close |
| `price_position` | Where close sits in H-L range |
| `returns` | Daily returns |
| `log_returns` | Log daily returns |

---

## Label Logic

```
future_return = price(t + horizon) / price(t) - 1

if future_return > 3%  → BUY
if future_return < -3% → SELL
else                   → HOLD
```

Default horizon: 7 days. Adjust in `train_model.py`.

---

## Project Structure

```
cryptolens/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes.py       # All FastAPI endpoints
│   │   │   └── schemas.py      # Pydantic models
│   │   ├── database/
│   │   │   └── db.py           # SQLAlchemy models + session
│   │   ├── ml/
│   │   │   └── train_model.py  # XGBoost training pipeline
│   │   ├── services/
│   │   │   ├── data_collector.py    # Binance API + DB storage
│   │   │   ├── feature_engineering.py  # All indicators
│   │   │   └── prediction.py        # Inference + explanations
│   │   ├── config.py
│   │   └── main.py             # FastAPI app + scheduler
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── page.tsx            # Home page
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── ui.tsx              # Shared components
│   │   ├── AnalysisResult.tsx  # Full result display
│   │   ├── PriceChart.tsx      # TradingView-style chart
│   │   └── ProbabilityChart.tsx
│   ├── lib/
│   │   └── api.ts              # API client
│   └── Dockerfile
├── scripts/
│   └── backfill.py
├── notebooks/
│   └── train_explore.ipynb
├── docker-compose.yml
└── README.md
```

---


## Disclaimer

This is for educational and research purposes only. Not financial advice.
Crypto markets are highly volatile. Never invest more than you can afford to lose.
