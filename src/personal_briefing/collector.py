"""Web search-based article collection using Tavily AI."""

import logging
import os
from datetime import UTC, datetime

import requests

from personal_briefing.models import Article, TopicConfig

logger = logging.getLogger(__name__)


class ArticleCollector:
    """Collects articles using Tavily AI web search API."""

    def __init__(
        self,
        search_provider: str = "tavily",
        max_results_per_topic: int = 15,
        max_articles_per_topic: int = 8,
    ) -> None:
        self.search_provider = search_provider
        self.max_results = max_results_per_topic
        self.max_articles = max_articles_per_topic
        self.api_key = os.environ.get("TAVILY_API_KEY", "")

        if not self.api_key:
            logger.warning("No TAVILY_API_KEY found in environment")

    def collect_for_topic(self, topic: TopicConfig) -> list[Article]:
        """Collect articles for a single topic using Tavily search."""
        if not self.api_key:
            logger.warning("No API key - returning empty results for %s", topic.name)
            return []

        try:
            return self._search_tavily(topic)
        except Exception:
            logger.error("Search failed for topic %s", topic.name, exc_info=True)
            return []

    def _search_tavily(self, topic: TopicConfig) -> list[Article]:
        """Search using Tavily AI API."""
        url = "https://api.tavily.com/search"

        # Create highly specific technical query
        # Include keywords that signal technical content
        technical_keywords = {
            "API Design": "REST API GraphQL OpenAPI Swagger microservices endpoints",
            "Kubernetes": "k8s kubectl helm container orchestration pods deployment",
            "Infrastructure as Code": "terraform CDK pulumi cloudformation ansible",
            "AI & Machine Learning": "machine learning LLM GPT neural networks training model",
            "SDLC": "CI/CD github actions jenkins deployment pipeline devops",
            "Infrastructure Architecture": "cloud architecture AWS distributed systems scalability",
        }

        # Get specific keywords or use the topic name
        keywords = technical_keywords.get(topic.name, topic.name)

        # Build query that explicitly asks for technical content
        query = f"{keywords} tutorial blog post technical article developer"

        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": self.max_results,
            "include_domains": [
                # Tier 1: Premium tech publications (highest quality)
                "martinfowler.com",
                "infoq.com",
                "stackoverflow.blog",
                "github.blog",
                "aws.amazon.com",
                "kubernetes.io",
                "blog.cloudflare.com",
                "engineering.fb.com",
                "netflixtechblog.com",
                "slack.engineering",
                "eng.uber.com",
                "medium.com/airbnb-engineering",
                "shopify.engineering",
                # Tier 2: Established tech media
                "thenewstack.io",
                "arstechnica.com",
                "techcrunch.com",
                "wired.com",
                "theverge.com",
                # Tier 3: Quality community platforms (but will need AI filtering)
                "dev.to",
                "medium.com",
                "hashnode.com",
                "devops.com",
                "siliconangle.com",
                "hackaday.com",
            ],
            "exclude_domains": [
                # Exclude general news sites
                "cnn.com",
                "foxnews.com",
                "nytimes.com",
                "apnews.com",
                "reuters.com",
                "bbc.com",
                "theguardian.com",
                "forbes.com",
                "businessinsider.com",
            ],
            "days": 7,  # Expand to 7 days for better results
        }

        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Collect articles with quality scoring
        scored_articles: list[tuple[Article, float]] = []
        for result in data.get("results", []):
            try:
                url = result.get("url", "")
                domain = self._extract_domain(url)
                content = result.get("content", "").strip()

                # Calculate quality score
                quality_score = self._calculate_quality_score(
                    domain=domain,
                    content=content,
                    score=result.get("score", 0.0),  # Tavily's relevance score
                )

                # Skip low-quality articles
                if quality_score < 0.3:
                    logger.debug(
                        "Skipping low-quality article from %s (score: %.2f)", domain, quality_score
                    )
                    continue

                article = Article(
                    title=result.get("title", "").strip(),
                    link=url,
                    summary=content,
                    published=datetime.now(UTC),
                    source=domain,
                    topic=topic.name,
                )
                scored_articles.append((article, quality_score))
            except Exception:
                logger.warning("Failed to parse search result", exc_info=True)
                continue

        # Sort by quality score and take top articles
        scored_articles.sort(key=lambda x: x[1], reverse=True)
        articles = [article for article, _ in scored_articles[: self.max_articles]]

        logger.info(
            "Tavily search for '%s': %d results (from %d candidates)",
            topic.name,
            len(articles),
            len(scored_articles),
        )
        return articles

    def _calculate_quality_score(self, domain: str, content: str, score: float) -> float:
        """Calculate article quality score based on source and content."""
        # Base score from Tavily's relevance
        quality = score

        # Tier 1 sources (engineering blogs, established tech sites) - highest boost
        tier1_domains = {
            "martinfowler.com",
            "infoq.com",
            "stackoverflow.blog",
            "github.blog",
            "aws.amazon.com",
            "kubernetes.io",
            "blog.cloudflare.com",
            "engineering.fb.com",
            "netflixtechblog.com",
            "slack.engineering",
            "eng.uber.com",
            "medium.com/airbnb-engineering",
            "shopify.engineering",
        }

        # Tier 2 sources (established tech media) - moderate boost
        tier2_domains = {
            "thenewstack.io",
            "arstechnica.com",
            "techcrunch.com",
            "wired.com",
            "theverge.com",
        }

        # Source quality boost
        if any(t1 in domain for t1 in tier1_domains):
            quality += 0.4
        elif any(t2 in domain for t2 in tier2_domains):
            quality += 0.2

        # Content depth scoring (longer, detailed content is better)
        content_length = len(content)
        if content_length > 1000:
            quality += 0.15
        elif content_length > 500:
            quality += 0.1
        elif content_length < 200:
            quality -= 0.2  # Penalize very short content

        # Technical depth signals (look for code, technical terms)
        technical_signals = [
            "```",
            "code",
            "implementation",
            "architecture",
            "tutorial",
            "example",
            "api",
            "function",
            "class",
            "method",
            "configuration",
        ]
        technical_count = sum(
            1 for signal in technical_signals if signal.lower() in content.lower()
        )
        quality += min(technical_count * 0.05, 0.2)  # Cap at +0.2

        # Negative signals (marketing speak, clickbait)
        spam_signals = [
            "click here",
            "subscribe now",
            "limited time",
            "sponsored",
            "revolutionary",
            "game-changing",
            "you won't believe",
        ]
        spam_count = sum(1 for signal in spam_signals if signal.lower() in content.lower())
        quality -= spam_count * 0.15

        return max(0.0, min(1.0, quality))  # Clamp between 0-1

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            if "/" in url:
                domain = url.split("/")[2]
                return domain
        except Exception:
            pass
        return "Web"

    def collect_all(self, topics: list[TopicConfig]) -> dict[str, list[Article]]:
        """Collect articles for all configured topics."""
        results: dict[str, list[Article]] = {}
        for topic in topics:
            articles = self.collect_for_topic(topic)
            results[topic.name] = articles
            logger.info("Topic '%s': %d articles collected", topic.name, len(articles))
        return results
