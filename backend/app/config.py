from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Service Information
    APP_NAME: str = "CloudSentinel"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False

    # Server Bindings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"

    # Monitoring Frequencies & Timeouts
    HEALTH_INTERVAL: float = 3.0  # seconds between probe cycles
    HEARTBEAT_TIMEOUT: float = 10.0  # seconds before considering missed heartbeat
    RECOVERY_TIMEOUT: float = 15.0  # seconds to wait for recovery stabilization
    MISSED_HEARTBEATS_THRESHOLD: int = 3  # consecutive misses before UNRESPONSIVE

    # Intelligent Health Thresholds
    CPU_WARNING_THRESHOLD: float = 75.0
    CPU_CRITICAL_THRESHOLD: float = 90.0
    MEMORY_WARNING_THRESHOLD: float = 75.0
    MEMORY_CRITICAL_THRESHOLD: float = 90.0
    RESPONSE_TIME_WARNING_MS: float = 400.0
    RESPONSE_TIME_CRITICAL_MS: float = 2000.0

    # Idle & Zombie Workload Detection
    IDLE_CPU_THRESHOLD: float = 5.0  # CPU% below this considered idle
    IDLE_DURATION_SECONDS: float = 120.0  # prolonged duration for zombie classification

    # Configurable Health Score Weights (Total = 1.0)
    WEIGHT_CPU: float = 0.20
    WEIGHT_RAM: float = 0.20
    WEIGHT_NETWORK: float = 0.10
    WEIGHT_RESPONSE_TIME: float = 0.20
    WEIGHT_HEARTBEAT: float = 0.20
    WEIGHT_APPLICATION: float = 0.10

    # Auto Recovery Policies
    AUTO_RECOVERY_ENABLED: bool = True
    HIGH_CONFIDENCE_THRESHOLD: float = 0.80  # >= 80% auto-recovers immediately
    MEDIUM_CONFIDENCE_THRESHOLD: float = 0.50  # 50-79% auto-recovers + generates alert

    # Firebase Credentials
    FIREBASE_PROJECT_ID: Optional[str] = None
    FIREBASE_CLIENT_EMAIL: Optional[str] = None
    FIREBASE_PRIVATE_KEY: Optional[str] = None
    FIREBASE_DATABASE_URL: Optional[str] = None

    # Operational Mode
    DEMO_MODE: bool = True
    DOCKER_SOCKET_PATH: str = os.environ.get("DOCKER_HOST", "unix:///var/run/docker.sock")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"


settings = Settings()
