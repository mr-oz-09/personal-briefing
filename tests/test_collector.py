"""Tests for article collector using Tavily."""

from unittest.mock import MagicMock, patch

from personal_briefing.collector import ArticleCollector
from personal_briefing.models import Config, TopicConfig


class TestArticleCollector:
    def test_init_defaults(self) -> None:
        collector = ArticleCollector()
        assert collector.search_provider == "tavily"
        assert collector.max_results == 15
        assert collector.max_articles == 8

    def test_init_custom(self) -> None:
        collector = ArticleCollector(
            search_provider="tavily",
            max_results_per_topic=20,
            max_articles_per_topic=10,
        )
        assert collector.search_provider == "tavily"
        assert collector.max_results == 20
        assert collector.max_articles == 10

    @patch("personal_briefing.collector.requests.post")
    @patch.dict("os.environ", {"TAVILY_API_KEY": "test-key"})
    def test_search_tavily(self, mock_post: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "title": "AI Breakthrough from GitHub Engineering",
                    "url": "https://github.blog/ai-article",
                    "content": "Major advancement in AI technology with code examples and implementation details for production systems.",
                    "score": 0.9,
                },
                {
                    "title": "LLM Update from AWS Blog",
                    "url": "https://aws.amazon.com/llm-update",
                    "content": "New language model released with detailed architecture breakdown and API documentation for developers.",
                    "score": 0.85,
                },
            ]
        }
        mock_post.return_value = mock_response

        topic = TopicConfig(
            name="AI & ML",
            description="Latest in AI and machine learning",
        )

        collector = ArticleCollector()
        articles = collector.collect_for_topic(topic)

        assert len(articles) == 2
        assert "AI Breakthrough" in articles[0].title
        assert articles[0].topic == "AI & ML"
        assert "github.blog" in articles[0].link or "aws.amazon.com" in articles[0].link

    @patch("personal_briefing.collector.requests.post")
    @patch.dict("os.environ", {"TAVILY_API_KEY": "test-key"})
    def test_search_handles_errors(self, mock_post: MagicMock) -> None:
        mock_post.side_effect = Exception("API error")

        topic = TopicConfig(name="Test", description="Test topic")
        collector = ArticleCollector()
        articles = collector.collect_for_topic(topic)

        assert articles == []

    @patch.dict("os.environ", {}, clear=True)
    def test_no_api_key(self) -> None:
        topic = TopicConfig(name="Test", description="Test topic")
        collector = ArticleCollector()
        articles = collector.collect_for_topic(topic)

        assert articles == []

    @patch("personal_briefing.collector.requests.post")
    @patch.dict("os.environ", {"TAVILY_API_KEY": "test-key"})
    def test_collect_all(self, mock_post: MagicMock, sample_config: Config) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "title": "Test Article",
                    "url": "https://example.com/test",
                    "content": "Test content",
                }
            ]
        }
        mock_post.return_value = mock_response

        collector = ArticleCollector()
        results = collector.collect_all(sample_config.topics)

        assert len(results) == 2
        assert "AI & ML" in results
        assert "Kubernetes" in results

    @patch("personal_briefing.collector.requests.post")
    @patch.dict("os.environ", {"TAVILY_API_KEY": "test-key"})
    def test_limits_results(self, mock_post: MagicMock) -> None:
        # Return more results than max_articles - use high-quality sources
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "title": f"Technical Article {i} from GitHub Engineering Blog",
                    "url": f"https://github.blog/article-{i}",
                    "content": f"Detailed technical content {i} with code examples, architecture patterns, implementation details, and API documentation for developers.",
                    "score": 0.9,
                }
                for i in range(20)
            ]
        }
        mock_post.return_value = mock_response

        topic = TopicConfig(name="Test", description="Test topic")
        collector = ArticleCollector(max_articles_per_topic=5)
        articles = collector.collect_for_topic(topic)

        # Should be limited to max_articles
        assert len(articles) == 5
