"""
CryptoLens Backend — FastAPI Application
Run: uvicorn app.main:app --reload --port 8000
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.api.routes import router
from app.database.db import create_tables
from app.services.data_collector import scheduled_fetch
from app.services.prediction import load_model
from app.config import get_settings

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting CryptoLens API…")
    create_tables()
    logger.info("Database tables ensured")

    try:
        load_model()
    except FileNotFoundError:
        logger.warning(
            "Model not found — run `python -m app.ml.train_model` after backfilling data"
        )

    # Schedule hourly data fetch
    scheduler.add_job(scheduled_fetch, "interval", hours=1, id="market_data_fetch")
    scheduler.start()
    logger.info("Scheduler started — fetching market data every hour")

    yield

    # Shutdown
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
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
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
