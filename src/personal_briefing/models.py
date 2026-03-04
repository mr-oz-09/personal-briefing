"""Data models for the personal briefing system."""

from datetime import datetime

from pydantic import BaseModel, Field


class Article(BaseModel):
    """Represents a single article from an RSS feed."""

    title: str
    link: str
    summary: str = ""
    published: datetime | None = None
    source: str = ""
    topic: str = ""

    model_config = {"frozen": True}


class TopicConfig(BaseModel):
    """Configuration for a single topic."""

    name: str
    description: str


class BriefingConfig(BaseModel):
    """Main briefing configuration."""

    schedule: str
    recipient_email: str
    sender_email: str
    sender_name: str = "Morning Briefing"
    max_articles_per_topic: int = Field(default=8, ge=1, le=20)
    region: str = "us-east-2"
    bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    search_provider: str = "tavily"
    search_results_per_topic: int = Field(default=15, ge=5, le=50)


class Config(BaseModel):
    """Complete configuration model."""

    briefing: BriefingConfig
    topics: list[TopicConfig]


class TopicSummary(BaseModel):
    """Summarized articles for a single topic."""

    topic_name: str
    articles: list[dict[str, str]]


class BriefingData(BaseModel):
    """Complete briefing data ready for email."""

    date: str
    intro: str = ""
    executive_summary: str = ""
    summaries: list[TopicSummary]
    generation_timestamp: datetime
