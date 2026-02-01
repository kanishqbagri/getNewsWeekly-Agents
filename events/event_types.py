from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

class EventType(Enum):
    """All event types in the system"""
    NEWS_SCRAPED = "news_scraped"
    CONSOLIDATION_READY = "consolidation_ready"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_RECEIVED = "approval_received"
    CONTENT_FORMATTED = "content_formatted"
    AUDIO_GENERATED = "audio_generated"
    READY_TO_PUBLISH = "ready_to_publish"
    TWITTER_PUBLISHED = "twitter_published"
    WEBSITE_PUBLISHED = "website_published"
    ERROR_OCCURRED = "error_occurred"

@dataclass
class Event:
    """Base event class"""
    event_type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    agent_id: str
    correlation_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)

# Implement specific event data classes for type safety
@dataclass
class Article:
    title: str
    summary: str
    url: str
    publish_date: datetime
    source: str
    category: str
    image_url: Optional[str] = None
    raw_content: Optional[str] = None
    relevance_score: Optional[float] = None

@dataclass
class NewsScrapedData:
    category: str
    article_count: int
    date: datetime
    articles: List[Dict[str, Any]]

@dataclass
class RankedArticle:
    article: Article
    rank: int
    category_rank: int
    importance_score: float
    selection_reason: str
