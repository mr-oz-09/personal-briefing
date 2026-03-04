"""Shared test fixtures."""

import os
from datetime import UTC, datetime

import pytest
from personal_briefing import reset_config_cache
from personal_briefing.models import (
    Article,
    BriefingConfig,
    BriefingData,
    Config,
    TopicConfig,
    TopicSummary,
)


@pytest.fixture(autouse=True)
def _reset_cache() -> None:
    """Reset config cache between tests."""
    reset_config_cache()


@pytest.fixture(autouse=True)
def _aws_credentials() -> None:
    """Set mock AWS credentials for all tests."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-2"


@pytest.fixture
def sample_article() -> Article:
    return Article(
        title="Test Article About AI",
        link="https://example.com/ai-article",
        summary="A breakthrough in large language models has enabled new capabilities.",
        published=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
        source="Test Source",
        topic="AI & Machine Learning",
    )


@pytest.fixture
def sample_articles() -> list[Article]:
    return [
        Article(
            title="AI Breakthrough",
            link="https://example.com/ai-1",
            summary="New model achieves state of the art results.",
            published=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            source="Tech News",
            topic="AI & ML",
        ),
        Article(
            title="Kubernetes 1.30 Released",
            link="https://example.com/k8s-1",
            summary="New features in the latest Kubernetes release.",
            published=datetime(2024, 1, 15, 9, 0, 0, tzinfo=UTC),
            source="K8s Blog",
            topic="Kubernetes",
        ),
    ]


@pytest.fixture
def sample_topic() -> TopicConfig:
    return TopicConfig(
        name="AI & Machine Learning",
        description="Latest developments in AI and machine learning",
    )


@pytest.fixture
def sample_config() -> Config:
    return Config(
        briefing=BriefingConfig(
            schedule="cron(0 11 * * ? *)",
            recipient_email="test@example.com",
            sender_email="briefing@example.com",
            sender_name="Test Briefing",
            max_articles_per_topic=8,
            region="us-east-2",
            bedrock_model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            search_provider="tavily",
            search_results_per_topic=15,
        ),
        topics=[
            TopicConfig(
                name="AI & ML",
                description="Latest in AI and machine learning",
            ),
            TopicConfig(
                name="Kubernetes",
                description="Kubernetes and container orchestration updates",
            ),
        ],
    )


@pytest.fixture
def sample_briefing() -> BriefingData:
    return BriefingData(
        date="Monday, January 15, 2024",
        summaries=[
            TopicSummary(
                topic_name="AI & Machine Learning",
                articles=[
                    {
                        "title": "AI Breakthrough",
                        "summary": "Researchers achieved new SOTA results on benchmarks.",
                        "link": "https://example.com/ai-1",
                    }
                ],
            ),
            TopicSummary(
                topic_name="Kubernetes",
                articles=[
                    {
                        "title": "K8s 1.30",
                        "summary": "New sidecar container support and gateway API improvements.",
                        "link": "https://example.com/k8s-1",
                    }
                ],
            ),
        ],
        generation_timestamp=datetime(2024, 1, 15, 11, 0, 0, tzinfo=UTC),
    )
