# src/schemas/unstructured_data.py
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class UnstructuredDataItem(BaseModel):
    source: str = Field(description="Source platform")
    text: str = Field(min_length=1)
    timestamp: datetime
    relevance_score: float = Field(ge=0, le=1.0)

class UnstructuredDataOutput(BaseModel):
    items: List[UnstructuredDataItem]
    total_count: int = Field(ge=0)

# src/schemas/market_data.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class MarketMetric(BaseModel):
    symbol: str
    price: float = Field(ge=0)
    volume: int = Field(ge=0)
    volatility: float = Field(ge=0, le=100)
    timestamp: datetime
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None

class MarketDataOutput(BaseModel):
    metrics: List[MarketMetric]

# src/schemas/sentiment.py
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class SentimentAnalysis(BaseModel):
    net_score: float = Field(ge=-1.0, le=1.0)
    confidence: float = Field(ge=0, le=1.0)
    themes: List[str] = Field(max_items=10)
    source_count: int = Field(ge=0)
    timestamp: datetime

# src/schemas/risk.py
from pydantic import BaseModel, Field
from datetime import datetime

class RiskAssessment(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    confidence_interval: float = Field(ge=0, le=1.0, description="90% confidence")
    var_calculation: float
    volatility_index: float
    anomaly_detected: bool
    risk_level: str = Field(pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    timestamp: datetime

# src/schemas/signals.py
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from .sentiment import SentimentAnalysis
from .risk import RiskAssessment
from .market_data import MarketDataOutput

class MarketSignals(BaseModel):
    timestamp: datetime
    assets: List[str]
    net_sentiment: float = Field(ge=-1.0, le=1.0)
    risk_score: float = Field(ge=0.0, le=1.0)
    themes: List[str]
    market_data: MarketDataOutput
    sentiment_details: SentimentAnalysis
    risk_details: RiskAssessment
    alert_triggered: bool
    metadata: dict = Field(default_factory=dict)