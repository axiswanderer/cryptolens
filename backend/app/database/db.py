from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_market_data_symbol_timestamp", "symbol", "timestamp"),
    )


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    recommendation = Column(String(10), nullable=False)  # BUY / HOLD / SELL
    confidence = Column(Float, nullable=False)
    score = Column(Float, nullable=False)
    rsi = Column(Float)
    macd = Column(Float)
    ema20 = Column(Float)
    ema50 = Column(Float)
    bb_upper = Column(Float)
    bb_lower = Column(Float)
    current_price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_predictions_symbol", "symbol"),
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)
