"""AWS Lambda handler for the personal briefing system."""

import logging
import os
from datetime import UTC, datetime
from typing import Any

import boto3

from personal_briefing import load_config
from personal_briefing.collector import ArticleCollector
from personal_briefing.emailer import EmailSender
from personal_briefing.models import BriefingData
from personal_briefing.summarizer import BedrockSummarizer

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_parameter(name: str, region: str = "us-east-2") -> str:
    """Get parameter from AWS Systems Manager Parameter Store."""
    # Check environment variable first (for local dev)
    env_key = name.replace("/personal-briefing/", "").replace("-", "_").upper()
    if env_value := os.environ.get(env_key):
        return env_value

    # Otherwise get from Parameter Store
    try:
        ssm = boto3.client("ssm", region_name=region)
        response = ssm.get_parameter(Name=name, WithDecryption=True)
        return response["Parameter"]["Value"]
    except Exception:
        logger.warning("Failed to get parameter %s", name, exc_info=True)
        return ""


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda entry point. Triggered by EventBridge on a daily schedule."""
    logger.info("Starting personal briefing generation")

    try:
        config = load_config()
        logger.info("Loaded config with %d topics", len(config.topics))

        # Override config with Parameter Store values
        tavily_key = get_parameter("/personal-briefing/tavily-api-key", config.briefing.region)
        recipient = get_parameter("/personal-briefing/recipient-email", config.briefing.region)
        reply_to = get_parameter("/personal-briefing/sender-email", config.briefing.region)

        # Set environment variable for collector
        if tavily_key:
            os.environ["TAVILY_API_KEY"] = tavily_key

        collector = ArticleCollector(
            search_provider=config.briefing.search_provider,
            max_results_per_topic=config.briefing.search_results_per_topic,
            max_articles_per_topic=config.briefing.max_articles_per_topic,
        )
        summarizer = BedrockSummarizer(
            model_id=config.briefing.bedrock_model_id,
            region=config.briefing.region,
        )
        # Use recipient's Gmail as sender (it's verified in SES)
        # This prevents Gmail spam filters from blocking "spoofed" emails
        sender_email = reply_to or config.briefing.sender_email
        emailer = EmailSender(
            sender_email=sender_email,
            sender_name=config.briefing.sender_name,
            reply_to_email=sender_email,
            region=config.briefing.region,
        )

        # 1. Collect articles from RSS feeds
        logger.info("Collecting articles...")
        articles_by_topic = collector.collect_all(config.topics)
        total = sum(len(v) for v in articles_by_topic.values())
        logger.info("Collected %d articles across %d topics", total, len(articles_by_topic))

        # 2. Summarize with Bedrock
        logger.info("Summarizing with Bedrock...")
        summaries = summarizer.summarize_all(articles_by_topic)
        logger.info("Generated summaries for %d topics", len(summaries))

        # 3. Generate intro and executive summary
        logger.info("Generating intro and executive summary...")
        intro, exec_summary = summarizer.generate_intro_and_summary(summaries)

        # 4. Build briefing and send email
        briefing = BriefingData(
            date=datetime.now(UTC).strftime("%A, %B %d, %Y"),
            intro=intro,
            executive_summary=exec_summary,
            summaries=summaries,
            generation_timestamp=datetime.now(UTC),
        )

        final_recipient = recipient or config.briefing.recipient_email
        logger.info("Sending briefing to %s", final_recipient)
        response = emailer.send_briefing(final_recipient, briefing)

        return {
            "statusCode": 200,
            "body": {
                "message": "Briefing sent successfully",
                "messageId": response["MessageId"],
                "topics": len(summaries),
                "articles": total,
            },
        }

    except Exception:
        logger.error("Failed to generate briefing", exc_info=True)
        return {
            "statusCode": 500,
            "body": {"message": "Failed to generate briefing"},
        }
