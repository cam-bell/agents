from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List, Dict
from uuid import UUID, uuid4
from enum import Enum


class RiskLevel(str, Enum):
    """Risk level enumeration."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class NewsArticle(BaseModel):
    """Individual news article."""
    source: str
    title: str
    url: str
    snippet: str = Field(max_length=500)
    timestamp: datetime
    ticker_mentions: List[str] = []
    toxicity_score: float = Field(default=0.0, ge=0, le=1)


class NewsCorpus(BaseModel):
    """Collection of news articles."""
    articles: List[NewsArticle]
    fetch_timestamp: datetime = Field(default_factory=datetime.now)
    source: str = "SerperDevTool"


class SocialPost(BaseModel):
    """Individual social media post."""
    platform: str
    post_id: str
    snippet: str = Field(max_length=300)
    timestamp: datetime
    ticker_mentions: List[str] = []
    engagement_score: float = Field(default=0.0, ge=0, le=1)


class SocialCorpus(BaseModel):
    """Collection of social media posts."""
    posts: List[SocialPost]
    fetch_timestamp: datetime = Field(default_factory=datetime.now)
    platforms: List[str] = []


class MarketDataSnapshot(BaseModel):
    """Market data snapshot for a ticker."""
    ticker: str
    timestamp: datetime
    last_price: float = Field(gt=0)
    pct_change_24h: float = Field(ge=-1.0, le=1.0)
    volume_24h: int = Field(ge=0)
    realized_volatility_30d: float = Field(ge=0, le=2.0)
    options_iv_30d: Optional[float] = Field(None, ge=0, le=3.0)
    avg_volume_30d: float = Field(gt=0)
    z_score_volume: float
    stale_data_flag: bool = False

    @field_validator('timestamp')
    @classmethod
    def check_staleness(cls, v):
        """Warn if data is stale."""
        from loguru import logger
        age_minutes = (datetime.now() - v).total_seconds() / 60
        if age_minutes > 5:
            logger.warning(f"Data is {age_minutes:.1f} minutes old")
        return v


class SentimentProfile(BaseModel):
    """Synthesized sentiment profile."""
    ticker: str
    timestamp: datetime = Field(default_factory=datetime.now)
    news_sentiment_raw: float = Field(ge=-5, le=5)
    news_sentiment_normalized: float = Field(ge=-1, le=1)
    social_sentiment_raw: float = Field(ge=-5, le=5)
    social_sentiment_normalized: float = Field(ge=-1, le=1)
    blended_sentiment: float = Field(ge=-1, le=1)
    sentiment_confidence: float = Field(ge=0, le=1)
    key_themes: List[str] = Field(default_factory=list, max_length=5)
    theme_embeddings: Optional[List[float]] = None


class RiskAssessment(BaseModel):
    """Risk assessment for a ticker."""
    ticker: str
    timestamp: datetime = Field(default_factory=datetime.now)
    risk_score: float = Field(ge=0, le=100)
    risk_level: RiskLevel
    component_scores: Dict[str, float]
    anomaly_flags: List[str] = []
    risk_rationale: str = Field(max_length=500)


class Signal(BaseModel):
    """Individual market signal."""
    ticker: str
    risk_score: float
    risk_level: RiskLevel
    sentiment_summary: str
    volatility_summary: str
    key_drivers: List[str]
    recommended_actions: List[str]


class MarketSignals(BaseModel):
    """Complete market signals output."""
    run_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.now)
    signals: List[Signal]
    metadata: Dict = Field(default_factory=dict)


class ComplianceValidation(BaseModel):
    """Compliance validation result."""
    approved: bool
    violations: List[str] = []
    risk_disclosures: List[str] = []
    audit_trail: str = ""


class AlertResult(BaseModel):
    """Alert dispatch result."""
    alerts_triggered: int
    alerts_blocked: int
    channel_results: Dict[str, str]
    status: str


class RunConfig(BaseModel):
    """Configuration for a run."""
    tickers: List[str]
    lookback_hours: int = 6
    alert_config: "AlertConfig"


class AlertConfig(BaseModel):
    """Alert configuration."""
    threshold_high: float = 60.0
    threshold_critical: float = 80.0
    channels: List[str] = Field(default=["slack", "webhook"])