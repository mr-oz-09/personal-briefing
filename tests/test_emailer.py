"""Tests for SES email sender."""

from unittest.mock import MagicMock, patch

from personal_briefing.emailer import EmailSender
from personal_briefing.models import BriefingData


class TestEmailSender:
    @patch("boto3.client")
    def test_init(self, mock_client: MagicMock) -> None:
        sender = EmailSender("sender@test.com", "Test", region="us-east-2")
        assert sender.sender_email == "sender@test.com"
        assert sender.sender_name == "Test"

    @patch("boto3.client")
    def test_format_email_contains_topics(
        self, mock_client: MagicMock, sample_briefing: BriefingData
    ) -> None:
        sender = EmailSender("sender@test.com", "Test")
        subject, html = sender.format_email(sample_briefing)

        assert "Morning Briefing" in subject
        assert "January 15, 2024" in subject
        assert "AI & Machine Learning" in html
        assert "Kubernetes" in html
        assert "AI Breakthrough" in html
        assert "K8s 1.30" in html
        assert "https://example.com/ai-1" in html

    @patch("boto3.client")
    def test_format_email_has_structure(
        self, mock_client: MagicMock, sample_briefing: BriefingData
    ) -> None:
        sender = EmailSender("sender@test.com", "Test")
        _, html = sender.format_email(sample_briefing)

        assert "<!DOCTYPE html>" in html
        assert "Morning Briefing" in html
        assert "Generated" in html
        assert "Powered by" in html

    @patch("boto3.client")
    def test_send_email(self, mock_client: MagicMock) -> None:
        mock_ses = MagicMock()
        mock_ses.send_email.return_value = {"MessageId": "abc-123"}
        mock_client.return_value = mock_ses

        sender = EmailSender("sender@test.com", "Test")
        response = sender.send_email("recipient@test.com", "Subject", "<html>body</html>")

        assert response["MessageId"] == "abc-123"
        mock_ses.send_email.assert_called_once()

        call_kwargs = mock_ses.send_email.call_args
        assert call_kwargs.kwargs["Destination"]["ToAddresses"] == ["recipient@test.com"]
        assert "Test <sender@test.com>" in call_kwargs.kwargs["Source"]

    @patch("boto3.client")
    def test_send_briefing_end_to_end(
        self, mock_client: MagicMock, sample_briefing: BriefingData
    ) -> None:
        mock_ses = MagicMock()
        mock_ses.send_email.return_value = {"MessageId": "xyz-789"}
        mock_client.return_value = mock_ses

        sender = EmailSender("sender@test.com", "Test Briefing")
        response = sender.send_briefing("recipient@test.com", sample_briefing)

        assert response["MessageId"] == "xyz-789"
        call_kwargs = mock_ses.send_email.call_args.kwargs
        html_body = call_kwargs["Message"]["Body"]["Html"]["Data"]
        assert "AI & Machine Learning" in html_body
        assert "Kubernetes" in html_body
