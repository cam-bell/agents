from pydantic_settings import BaseSettings
from typing import Dict


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # API Keys
    serper_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    financial_api_key: str = ""
    
    # Infrastructure
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    
    # Vector DB
    chroma_db_path: str = "./knowledge/chroma_db"
    
    # Alerting
    slack_webhook_url: str = ""
    alert_webhook_url: str = ""
    
    # Configuration
    log_level: str = "INFO"
    max_queries_per_run: int = 10
    
    # Risk Scoring Weights
    risk_weights: Dict[str, float] = {
        'sentiment': 0.40,
        'volatility': 0.30,
        'volume_anomaly': 0.20,
        'macro': 0.10
    }
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()