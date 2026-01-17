# app/core/config.py
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Runtime
    ENVIRONMENT: str = "development"

    # Database
    # Default to MySQL if not set in .env
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/aix_system"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # InfluxDB (Optional)
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: Optional[str] = None
    INFLUXDB_ORG: str = "aix-org"
    INFLUXDB_BUCKET: str = "sensor-data"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ML Pipeline
    MODEL_STORAGE_PATH: str = "./models"
    MAX_CONCURRENT_PIPELINES: int = 3

    # Process Parameters (guardrails)
    TEMPERATURE_MIN: float = 840.0
    TEMPERATURE_MAX: float = 860.0
    TEMPERATURE_OPTIMAL: float = 850.0
    PRESSURE_MIN: float = 2.3
    PRESSURE_MAX: float = 2.7
    PRESSURE_OPTIMAL: float = 2.5

    # FDC Parameters
    DRIFT_DETECTION_WINDOW: int = 100
    ALARM_THRESHOLD_SIGMA: float = 2.0

    # AI / LLM (DeepSeek)
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

    # Pydantic v2 config
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
