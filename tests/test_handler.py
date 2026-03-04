"""Tests for Lambda handler."""

from unittest.mock import MagicMock, patch

from personal_briefing.handler import lambda_handler
from personal_briefing.models import Config

EVENTBRIDGE_EVENT = {
    "version": "0",
    "id": "test-event-id",
    "detail-type": "Scheduled Event",
    "source": "aws.events",
    "time": "2024-01-15T11:00:00Z",
    "region": "us-east-2",
}


class TestLambdaHandler:
    @patch("personal_briefing.handler.get_parameter")
    @patch("personal_briefing.handler.EmailSender")
    @patch("personal_briefing.handler.BedrockSummarizer")
    @patch("personal_briefing.handler.ArticleCollector")
    @patch("personal_briefing.handler.load_config")
    def test_success(
        self,
        mock_config: MagicMock,
        mock_collector_cls: MagicMock,
        mock_summarizer_cls: MagicMock,
        mock_emailer_cls: MagicMock,
        mock_get_param: MagicMock,
        sample_config: Config,
    ) -> None:
        mock_config.return_value = sample_config
        mock_get_param.return_value = "test-value"

        mock_collector = MagicMock()
        mock_collector.collect_all.return_value = {"AI": [], "K8s": []}
        mock_collector_cls.return_value = mock_collector

        mock_summarizer = MagicMock()
        mock_summarizer.summarize_all.return_value = []
        mock_summarizer.generate_intro_and_summary.return_value = ("intro", "summary")
        mock_summarizer_cls.return_value = mock_summarizer

        mock_emailer = MagicMock()
        mock_emailer.send_briefing.return_value = {"MessageId": "test-id"}
        mock_emailer_cls.return_value = mock_emailer

        result = lambda_handler(EVENTBRIDGE_EVENT, None)

        assert result["statusCode"] == 200
        assert result["body"]["message"] == "Briefing sent successfully"
        assert result["body"]["messageId"] == "test-id"
        mock_collector.collect_all.assert_called_once()
        mock_summarizer.summarize_all.assert_called_once()
        mock_emailer.send_briefing.assert_called_once()

    @patch("personal_briefing.handler.load_config")
    def test_config_error(self, mock_config: MagicMock) -> None:
        mock_config.side_effect = FileNotFoundError("topics.yaml not found")

        result = lambda_handler(EVENTBRIDGE_EVENT, None)

        assert result["statusCode"] == 500
        assert "Failed to generate briefing" in result["body"]["message"]

    @patch("personal_briefing.handler.EmailSender")
    @patch("personal_briefing.handler.BedrockSummarizer")
    @patch("personal_briefing.handler.ArticleCollector")
    @patch("personal_briefing.handler.load_config")
    def test_email_error(
        self,
        mock_config: MagicMock,
        mock_collector_cls: MagicMock,
        mock_summarizer_cls: MagicMock,
        mock_emailer_cls: MagicMock,
        sample_config: Config,
    ) -> None:
        mock_config.return_value = sample_config

        mock_collector = MagicMock()
        mock_collector.collect_all.return_value = {}
        mock_collector_cls.return_value = mock_collector

        mock_summarizer = MagicMock()
        mock_summarizer.summarize_all.return_value = []
        mock_summarizer_cls.return_value = mock_summarizer

        mock_emailer = MagicMock()
        mock_emailer.send_briefing.side_effect = Exception("SES error")
        mock_emailer_cls.return_value = mock_emailer

        result = lambda_handler(EVENTBRIDGE_EVENT, None)

        assert result["statusCode"] == 500
