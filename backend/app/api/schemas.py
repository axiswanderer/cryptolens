from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class AnalyzeRequest(BaseModel):
    symbol: str = Field(..., example="BTCUSDT", description="Trading pair, e.g. BTCUSDT")
    timeframe: Literal["3d", "7d", "14d", "30d"] = Field(
        default="7d", description="Forecast horizon"
    )


class IndicatorsResponse(BaseModel):
    rsi: float
    macd: float
    macd_signal: float
    ema20: float
    ema50: float
    bb_upper: float
    bb_lower: float
    bb_mid: float
    atr: float
    volume_ratio: float
    momentum_5d: float
    momentum_14d: float


class ProbabilitiesResponse(BaseModel):
    BUY: float
    HOLD: float
    SELL: float


class AnalyzeResponse(BaseModel):
    symbol: str
    timeframe: str
    current_price: float
    recommendation: Literal["BUY", "HOLD", "SELL"]
    confidence: float = Field(..., description="Model confidence 0–100")
    score: float = Field(..., description="Composite signal score 0–100")
    probabilities: ProbabilitiesResponse
    reasons: list[str]
    indicators: IndicatorsResponse
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    db_connected: bool
    version: str = "1.0.0"


class BackfillRequest(BaseModel):
    symbol: Optional[str] = None
    days: int = Field(default=730, ge=30, le=1460)


class OHLCVPoint(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class OHLCVResponse(BaseModel):
    symbol: str
    data: list[OHLCVPoint]
    count: int
