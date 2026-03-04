"""Amazon SES email generation and sending."""

import logging
from typing import Any

import boto3
from botocore.exceptions import ClientError

from personal_briefing.models import BriefingData

logger = logging.getLogger(__name__)

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Georgia', 'Times New Roman', serif;
            line-height: 1.6;
            color: #2c3e50;
            max-width: 700px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background-color: #ffffff;
            padding: 40px;
            border-radius: 4px;
            border-top: 4px solid #1a365d;
        }}
        .header {{
            border-bottom: 2px solid #1a365d;
            padding-bottom: 16px;
            margin-bottom: 32px;
        }}
        .header h1 {{
            color: #1a365d;
            margin: 0;
            font-size: 26px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}
        .header .date {{
            color: #718096;
            font-size: 14px;
            margin-top: 4px;
            font-style: italic;
        }}
        .intro {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 24px;
            border-radius: 8px;
            margin-bottom: 24px;
            color: #ffffff;
            font-size: 16px;
            line-height: 1.8;
            font-weight: 500;
        }}
        .exec-summary {{
            background-color: #fef5e7;
            padding: 20px;
            border-radius: 6px;
            margin-bottom: 32px;
            border-left: 4px solid #f39c12;
            color: #2d3748;
            font-size: 15px;
            line-height: 1.7;
            font-family: 'Helvetica Neue', Arial, sans-serif;
        }}
        .exec-summary strong {{
            color: #d68910;
            font-weight: 700;
        }}
        .topic {{
            margin-bottom: 32px;
        }}
        .topic-name {{
            color: #1a365d;
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 16px;
            padding-bottom: 6px;
            border-bottom: 1px solid #e2e8f0;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 13px;
        }}
        .article {{
            margin-bottom: 18px;
            padding-left: 16px;
            border-left: 3px solid #cbd5e0;
        }}
        .article-title {{
            font-weight: 700;
            margin-bottom: 4px;
        }}
        .article-title a {{
            color: #2b6cb0;
            text-decoration: none;
        }}
        .article-title a:hover {{
            text-decoration: underline;
        }}
        .article-summary {{
            color: #4a5568;
            font-size: 14px;
            line-height: 1.5;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 16px;
            border-top: 1px solid #e2e8f0;
            color: #a0aec0;
            font-size: 11px;
            text-align: center;
            font-family: 'Helvetica Neue', Arial, sans-serif;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Morning Briefing</h1>
            <div class="date">{date}</div>
        </div>

        {intro_html}

        {summary_html}

        {topics_html}

        <div class="footer">
            Generated {timestamp} | Powered by Amazon Bedrock &amp; SES
        </div>
    </div>
</body>
</html>"""


class EmailSender:
    """Formats and sends briefing emails via Amazon SES."""

    def __init__(
        self,
        sender_email: str,
        sender_name: str,
        region: str = "us-east-2",
        reply_to_email: str | None = None,
    ) -> None:
        self.sender_email = sender_email
        self.sender_name = sender_name
        self.reply_to_email = reply_to_email or sender_email
        self.client = boto3.client("ses", region_name=region)

    def format_email(self, briefing: BriefingData) -> tuple[str, str]:
        """Format briefing data as HTML email. Returns (subject, html_body)."""
        # Format intro
        intro_html = ""
        if briefing.intro:
            intro_html = f'<div class="intro">{briefing.intro}</div>'

        # Format executive summary
        summary_html = ""
        if briefing.executive_summary:
            summary_html = f'<div class="exec-summary"><strong>📋 Executive Summary:</strong> {briefing.executive_summary}</div>'

        topics_html_parts: list[str] = []

        for topic_summary in briefing.summaries:
            articles_html: list[str] = []
            for article in topic_summary.articles:
                articles_html.append(
                    f'<div class="article">'
                    f'<div class="article-title">'
                    f'<a href="{article["link"]}">{article["title"]}</a>'
                    f"</div>"
                    f'<div class="article-summary">{article["summary"]}</div>'
                    f"</div>"
                )

            topics_html_parts.append(
                f'<div class="topic">'
                f'<div class="topic-name">{topic_summary.topic_name}</div>'
                f"{''.join(articles_html)}"
                f"</div>"
            )

        timestamp = briefing.generation_timestamp.strftime("%Y-%m-%d %I:%M %p UTC")
        html_body = HTML_TEMPLATE.format(
            date=briefing.date,
            intro_html=intro_html,
            summary_html=summary_html,
            topics_html="".join(topics_html_parts),
            timestamp=timestamp,
        )

        subject = f"Morning Briefing - {briefing.date}"
        return subject, html_body

    def send_email(self, recipient: str, subject: str, html_body: str) -> dict[str, Any]:
        """Send email via SES with anti-spam headers."""
        try:
            # Add text version to avoid spam filters
            text_body = self._html_to_text(html_body)

            response = self.client.send_email(
                Source=self.sender_email,
                Destination={"ToAddresses": [recipient]},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {
                        "Text": {"Data": text_body, "Charset": "UTF-8"},
                        "Html": {"Data": html_body, "Charset": "UTF-8"},
                    },
                },
                # Add headers to improve deliverability
                ReplyToAddresses=[self.reply_to_email],
            )
            logger.info("Email sent. MessageId: %s", response["MessageId"])
            return dict(response)
        except ClientError:
            logger.error("Failed to send email", exc_info=True)
            raise

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text for spam prevention."""
        import re

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", html)
        # Clean up whitespace
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\n\s*\n", "\n\n", text)
        return text.strip()

    def send_briefing(self, recipient: str, briefing: BriefingData) -> dict[str, Any]:
        """Format and send a complete briefing email."""
        subject, html_body = self.format_email(briefing)
        return self.send_email(recipient, subject, html_body)
