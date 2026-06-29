"""
CryptoLens Backend — FastAPI Application
Run: uvicorn app.main:app --reload --port 8000
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.api.routes import router
from app.database.db import create_tables
from app.services.data_collector import scheduled_fetch, backfill_all
from app.services.prediction import load_model
from app.config import get_settings

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _auto_setup():
    """Backfill data and train model on first boot (runs in background)."""
    from app.ml.train_model import train as run_training
    try:
        logger.info("Auto-setup: backfilling historical data (~2 min)…")
        await backfill_all(730)
        logger.info("Auto-setup: training XGBoost model (~30s)…")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, run_training)
        load_model()
        logger.info("Auto-setup complete — model is ready")
    except Exception:
        logger.exception("Auto-setup failed — use POST /api/v1/backfill then POST /api/v1/train")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting CryptoLens API…")
    create_tables()
    logger.info("Database tables ensured")

    try:
        load_model()
        logger.info("Model loaded")
    except FileNotFoundError:
        logger.warning("Model not found — starting auto-setup in background")
        asyncio.create_task(_auto_setup())

    scheduler.add_job(scheduled_fetch, "interval", hours=1, id="market_data_fetch")
    scheduler.start()
    logger.info("Scheduler started — fetching market data every hour")

    yield

    scheduler.shutdown()
    logger.info("Scheduler stopped")


app = FastAPI(
    title="CryptoLens API",
    description="AI-powered crypto investment signal generation",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.ALLOWED_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "name": "CryptoLens API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
