import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from sqlalchemy.orm import Session

from app.api.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    HealthResponse,
    BackfillRequest,
    OHLCVResponse,
    OHLCVPoint,
)
from app.database.db import get_db, Prediction, MarketData
from app.services.prediction import predict, get_model
from app.services.data_collector import (
    backfill_symbol,
    backfill_all,
    load_ohlcv,
    SUPPORTED_SYMBOLS,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check(db: Session = Depends(get_db)):
    """Check API health, model status, and DB connectivity."""
    model_loaded = False
    db_connected = False

    try:
        get_model()
        model_loaded = True
    except Exception:
        pass

    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_connected = True
    except Exception:
        pass

    return HealthResponse(
        status="ok" if (model_loaded and db_connected) else "degraded",
        model_loaded=model_loaded,
        db_connected=db_connected,
    )


@router.post("/analyze", response_model=AnalyzeResponse, tags=["Predictions"])
def analyze_coin(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
):
    """
    Run AI prediction for a coin.

    Returns BUY / HOLD / SELL with confidence, score, indicators, and reasons.
    """
    symbol = request.symbol.upper()
    if symbol not in [s for s in SUPPORTED_SYMBOLS]:
        raise HTTPException(
            status_code=400,
            detail=f"Symbol {symbol} not supported. Supported: {SUPPORTED_SYMBOLS}"
        )

    try:
        result = predict(symbol, request.timeframe)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception(f"Prediction error for {symbol}")
        raise HTTPException(status_code=500, detail="Prediction failed")

    # Persist prediction
    try:
        pred_record = Prediction(
            symbol=symbol,
            timeframe=request.timeframe,
            recommendation=result["recommendation"],
            confidence=result["confidence"],
            score=result["score"],
            rsi=result["indicators"]["rsi"],
            macd=result["indicators"]["macd"],
            ema20=result["indicators"]["ema20"],
            ema50=result["indicators"]["ema50"],
            bb_upper=result["indicators"]["bb_upper"],
            bb_lower=result["indicators"]["bb_lower"],
            current_price=result["current_price"],
        )
        db.add(pred_record)
        db.commit()
    except Exception:
        logger.warning("Could not persist prediction to DB")

    return AnalyzeResponse(**result)


@router.get("/symbols", tags=["Data"])
def list_symbols():
    """Return all supported trading symbols."""
    return {"symbols": SUPPORTED_SYMBOLS}


@router.get("/ohlcv/{symbol}", response_model=OHLCVResponse, tags=["Data"])
def get_ohlcv(
    symbol: str,
    limit: int = Query(default=200, ge=10, le=1000),
    db: Session = Depends(get_db),
):
    """Fetch historical OHLCV data for a symbol from DB."""
    symbol = symbol.upper()
    df = load_ohlcv(symbol, limit=limit, db=db)
    if df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No data for {symbol}. Run backfill first."
        )
    points = [
        OHLCVPoint(
            timestamp=row.timestamp,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            volume=row.volume,
        )
        for _, row in df.iterrows()
    ]
    return OHLCVResponse(symbol=symbol, data=points, count=len(points))


@router.get("/predictions/{symbol}", tags=["Predictions"])
def get_prediction_history(
    symbol: str,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Fetch past predictions for a symbol."""
    symbol = symbol.upper()
    records = (
        db.query(Prediction)
        .filter(Prediction.symbol == symbol)
        .order_by(Prediction.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "symbol": symbol,
        "predictions": [
            {
                "id": r.id,
                "recommendation": r.recommendation,
                "confidence": r.confidence,
                "score": r.score,
                "current_price": r.current_price,
                "timeframe": r.timeframe,
                "created_at": r.created_at,
            }
            for r in records
        ],
    }


@router.post("/backfill", tags=["Data"])
async def trigger_backfill(
    request: BackfillRequest,
    background_tasks: BackgroundTasks,
):
    """
    Trigger historical data backfill.
    If symbol is omitted, backfills all supported symbols.
    Runs in background.
    """
    if request.symbol:
        symbol = request.symbol.upper()
        background_tasks.add_task(backfill_symbol, symbol, request.days)
        return {"message": f"Backfill started for {symbol}", "days": request.days}
    else:
        background_tasks.add_task(backfill_all, request.days)
        return {"message": "Backfill started for all symbols", "days": request.days}
