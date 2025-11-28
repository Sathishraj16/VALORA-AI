"""
VALORA Core Configuration
Production-grade settings management with environment isolation
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Application
    APP_NAME: str = "VALORA"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="production", env="ENVIRONMENT")
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = Field(default="your-super-secret-key-change-in-production", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://valora:valora@localhost:5432/valora_db",
        env="DATABASE_URL"
    )
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_CACHE_TTL: int = 3600
    
    # Celery
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    
    # LLM Configuration
    GROQ_API_KEY: Optional[str] = Field(default=None, env="GROQ_API_KEY")
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    LLM_MODEL: str = Field(default="llama-3.1-70b-versatile", env="LLM_MODEL")
    LLM_FALLBACK_MODEL: str = "gpt-4-turbo-preview"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4096
    
    # Simulation Engine
    SIMULATION_TICK_INTERVAL: float = 1.0  # seconds between simulation steps
    MAX_AGENTS_PER_SIMULATION: int = 10000
    DEFAULT_SIMULATION_STEPS: int = 100
    ENABLE_GPU_ACCELERATION: bool = False
    
    # Economic Model Parameters
    INITIAL_GDP: float = 1000000.0  # $1M baseline
    INITIAL_INFLATION: float = 0.02  # 2%
    INITIAL_UNEMPLOYMENT: float = 0.05  # 5%
    NATURAL_UNEMPLOYMENT_RATE: float = 0.045
    INFLATION_TARGET: float = 0.02
    
    # Agent Learning
    AGENT_LEARNING_RATE: float = 0.001
    AGENT_DISCOUNT_FACTOR: float = 0.99
    AGENT_EPSILON_START: float = 1.0
    AGENT_EPSILON_END: float = 0.01
    AGENT_EPSILON_DECAY: float = 0.995
    
    # Blockchain
    GENESIS_BLOCK_HASH: str = "0" * 64
    BLOCK_DIFFICULTY: int = 4
    MAX_TRANSACTIONS_PER_BLOCK: int = 100
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://valora.ai",
        "https://app.valora.ai"
    ]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_BURST: int = 20
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Feature Flags
    ENABLE_BLOCKCHAIN: bool = True
    ENABLE_CREWAI: bool = True
    ENABLE_REALTIME_STREAMING: bool = True
    ENABLE_ADVANCED_ANALYTICS: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


settings = get_settings()
