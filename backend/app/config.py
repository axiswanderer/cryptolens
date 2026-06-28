from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/cryptolens"
    BINANCE_API_KEY: str = ""
    BINANCE_SECRET_KEY: str = ""
    ENV: str = "development"
    MODEL_PATH: str = "./models/xgboost_model.joblib"
    LOG_LEVEL: str = "INFO"
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
