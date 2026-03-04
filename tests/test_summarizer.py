"""Tests for Bedrock summarizer."""

import json
from unittest.mock import MagicMock, patch

from personal_briefing.models import Article
from personal_briefing.summarizer import BedrockSummarizer


def _mock_bedrock_response(summaries: list[dict[str, str]]) -> dict:
    """Build a mock Bedrock response body."""
    return {
        "content": [{"text": json.dumps({"summaries": summaries})}],
    }


class TestBedrockSummarizer:
    @patch("boto3.client")
    def test_init(self, mock_client: MagicMock) -> None:
        summarizer = BedrockSummarizer(model_id="test-model", region="us-east-2")
        assert summarizer.model_id == "test-model"

    @patch("boto3.client")
    def test_summarize_empty_articles(self, mock_client: MagicMock) -> None:
        summarizer = BedrockSummarizer(model_id="test-model")
        result = summarizer.summarize_topic("Empty", [])
        assert result is None

    @patch("boto3.client")
    def test_summarize_topic_success(self, mock_client: MagicMock, sample_article: Article) -> None:
        expected_summaries = [
            {
                "title": "Test Article About AI",
                "summary": "A concise AI summary.",
                "link": "https://example.com/ai-article",
            }
        ]

        mock_bedrock = MagicMock()
        mock_bedrock.invoke_model.return_value = {
            "body": MagicMock(
                read=lambda: json.dumps(_mock_bedrock_response(expected_summaries)).encode()
            )
        }
        mock_client.return_value = mock_bedrock

        summarizer = BedrockSummarizer(model_id="test-model")
        result = summarizer.summarize_topic("AI & ML", [sample_article])

        assert result is not None
        assert result.topic_name == "AI & ML"
        assert len(result.articles) == 1
        assert result.articles[0]["title"] == "Test Article About AI"

    @patch("boto3.client")
    def test_summarize_topic_handles_bedrock_error(
        self, mock_client: MagicMock, sample_article: Article
    ) -> None:
        mock_bedrock = MagicMock()
        mock_bedrock.invoke_model.side_effect = Exception("Bedrock unavailable")
        mock_client.return_value = mock_bedrock

        summarizer = BedrockSummarizer(model_id="test-model")
        result = summarizer.summarize_topic("AI & ML", [sample_article])

        # Should return fallback, not raise
        assert result is not None
        assert result.topic_name == "AI & ML"
        assert len(result.articles) > 0

    @patch("boto3.client")
    def test_summarize_topic_handles_bad_json(
        self, mock_client: MagicMock, sample_article: Article
    ) -> None:
        mock_bedrock = MagicMock()
        mock_bedrock.invoke_model.return_value = {
            "body": MagicMock(
                read=lambda: json.dumps({"content": [{"text": "This is not JSON at all"}]}).encode()
            )
        }
        mock_client.return_value = mock_bedrock

        summarizer = BedrockSummarizer(model_id="test-model")
        result = summarizer.summarize_topic("AI & ML", [sample_article])

        # Should fall back to original summaries
        assert result is not None
        assert len(result.articles) == 1

    @patch("boto3.client")
    def test_summarize_topic_handles_markdown_fences(
        self, mock_client: MagicMock, sample_article: Article
    ) -> None:
        json_with_fences = '```json\n{"summaries": [{"title": "AI", "summary": "Summary", "link": "https://example.com"}]}\n```'

        mock_bedrock = MagicMock()
        mock_bedrock.invoke_model.return_value = {
            "body": MagicMock(
                read=lambda: json.dumps({"content": [{"text": json_with_fences}]}).encode()
            )
        }
        mock_client.return_value = mock_bedrock

        summarizer = BedrockSummarizer(model_id="test-model")
        result = summarizer.summarize_topic("AI & ML", [sample_article])

        assert result is not None
        assert result.articles[0]["title"] == "AI"

    @patch("boto3.client")
    def test_summarize_all(self, mock_client: MagicMock, sample_articles: list[Article]) -> None:
        summaries_response = [{"title": "t", "summary": "s", "link": "https://example.com"}]

        mock_bedrock = MagicMock()
        mock_bedrock.invoke_model.return_value = {
            "body": MagicMock(
                read=lambda: json.dumps(_mock_bedrock_response(summaries_response)).encode()
            )
        }
        mock_client.return_value = mock_bedrock

        summarizer = BedrockSummarizer(model_id="test-model")
        results = summarizer.summarize_all(
            {"AI": [sample_articles[0]], "K8s": [sample_articles[1]]}
        )

        assert len(results) == 2
