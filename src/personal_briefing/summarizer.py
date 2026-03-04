"""Amazon Bedrock integration for article summarization."""

import json
import logging
from typing import Any

import boto3

from personal_briefing.models import Article, TopicSummary

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a witty, insightful chief of staff preparing a morning \
intelligence briefing for a senior technology leader. Your summaries should be \
informative, engaging, and actually fun to read.

Each summary should:
- Be 2-3 sentences that actually explain what the article is about
- Highlight the key insight, development, or takeaway
- Use conversational language with personality - occasional wit or interesting observations welcome
- Make technical topics accessible without dumbing them down
- Skip if the article isn't relevant to the topic

Think of this as a presidential daily briefing written by someone who's read too much \
tech Twitter but still respects your time. Information-dense, occasionally cheeky, never boring."""

USER_PROMPT_TEMPLATE = """Review these articles about "{topic}". For EACH article:

1. **Relevance Check**: Is this ACTUALLY about {topic}?
   - If it's general news, politics, or entertainment → SKIP IT
   - If it's tangentially related but not technical → SKIP IT
   - Only include if it's genuinely technical content about {topic}

2. **Quality Check**: Is this TOP-TIER content worth a senior engineer's time?
   - SKIP if: press releases, marketing fluff, clickbait, basic/beginner content
   - SKIP if: "10 tips" listicles, superficial overviews, rehashed news
   - KEEP if: deep technical analysis, novel insights, expert perspectives
   - KEEP if: engineering blog posts from reputable companies
   - KEEP if: detailed tutorials with real implementation details
   - KEEP if: thought leadership from recognized experts (Martin Fowler, etc.)

3. **Author/Source Credibility Check**:
   - Prioritize: Company engineering blogs (Netflix, Uber, AWS, etc.)
   - Prioritize: Known tech authorities (InfoQ, Martin Fowler, Kubernetes.io)
   - Skeptical of: Random Medium posts, unknown authors
   - If source seems questionable, content must be EXCEPTIONAL to pass

4. **Write Summary** (only for articles that passed ALL checks):
   - 2-3 sentences explaining WHAT it's about and WHY it matters
   - Be witty but informative
   - Make it actually interesting to read

Articles:
{articles}

CRITICAL: We're curating for a senior technology leader. Quality over quantity.
An empty list is better than mediocre content. Be merciless.

Respond in JSON format (no markdown):
{{"summaries": [{{"title": "article title", "summary": "your summary", "link": "url"}}]}}"""


class BedrockSummarizer:
    """Summarizes articles using Amazon Bedrock Claude models."""

    def __init__(self, model_id: str, region: str = "us-east-2") -> None:
        self.model_id = model_id
        self.client = boto3.client("bedrock-runtime", region_name=region)

    def summarize_topic(self, topic_name: str, articles: list[Article]) -> TopicSummary | None:
        """Summarize articles for a single topic."""
        if not articles:
            return None

        articles_text = "\n\n".join(
            f"Title: {a.title}\nSource: {a.source}\nURL: {a.link}\nContent: {a.summary[:500]}"
            for a in articles
        )

        user_prompt = USER_PROMPT_TEMPLATE.format(topic=topic_name, articles=articles_text)

        try:
            response = self._invoke_model(user_prompt)
            summaries = self._parse_response(response, articles)
            return TopicSummary(topic_name=topic_name, articles=summaries)
        except Exception:
            logger.error("Failed to summarize topic '%s'", topic_name, exc_info=True)
            return self._fallback_summary(topic_name, articles)

    def _invoke_model(self, user_prompt: str) -> dict[str, Any]:
        """Invoke Bedrock Claude model."""
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "temperature": 0.3,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_prompt}],
        }

        response = self.client.invoke_model(modelId=self.model_id, body=json.dumps(request_body))

        result: dict[str, Any] = json.loads(response["body"].read())
        return result

    def _parse_response(
        self, response: dict[str, Any], original_articles: list[Article]
    ) -> list[dict[str, str]]:
        """Parse structured JSON from model response."""
        try:
            content = response["content"][0]["text"]

            # Strip markdown code fences if present
            if "```" in content:
                parts = content.split("```")
                for part in parts:
                    stripped = part.strip()
                    if stripped.startswith("json"):
                        stripped = stripped[4:].strip()
                    if stripped.startswith("{"):
                        content = stripped
                        break

            parsed = json.loads(content)
            summaries: list[dict[str, str]] = parsed.get("summaries", [])
            if summaries:
                return summaries
        except (json.JSONDecodeError, KeyError, IndexError):
            logger.warning("Failed to parse model response as JSON", exc_info=True)

        return [
            {
                "title": a.title,
                "summary": a.summary[:200] + "..." if len(a.summary) > 200 else a.summary,
                "link": str(a.link),
            }
            for a in original_articles
        ]

    def _fallback_summary(self, topic_name: str, articles: list[Article]) -> TopicSummary:
        """Return truncated original summaries when Bedrock fails."""
        return TopicSummary(
            topic_name=topic_name,
            articles=[
                {
                    "title": a.title,
                    "summary": a.summary[:200] + "..." if len(a.summary) > 200 else a.summary,
                    "link": str(a.link),
                }
                for a in articles[:3]
            ],
        )

    def generate_intro_and_summary(self, summaries: list[TopicSummary]) -> tuple[str, str]:
        """Generate engaging intro and executive summary."""
        topics = [s.topic_name for s in summaries]
        total_articles = sum(len(s.articles) for s in summaries)

        prompt = f"""Write an engaging briefing header with two parts:

1. INTRO (2-3 sentences): A fun, conversational opening that makes someone want to read. \
Morning coffee chat vibes, not corporate memo. We're covering {len(topics)} topics today.

2. EXECUTIVE SUMMARY (3-4 sentences): "Here's what matters today" - highlight the most \
interesting trends/stories across all topics. Punchy and insightful.

Topics: {", ".join(topics)}

Example:
{{"intro": "☕️ Good morning! Pour yourself coffee, we've got spicy tech takes. From AI chaos to infrastructure drama, here's what's worth knowing.", "summary": "The big story? AI is everywhere and everyone has opinions. Kubernetes continues its world tour, someone made API docs readable, and there's IaC drama that'll make you grateful you're not on-call."}}

Write similar for today. Be witty but informative.

JSON only:
{{"intro": "...", "summary": "..."}}"""

        try:
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "temperature": 0.8,
                "messages": [{"role": "user", "content": prompt}],
            }
            response = self.client.invoke_model(
                modelId=self.model_id, body=json.dumps(request_body)
            )
            result: dict[str, Any] = json.loads(response["body"].read())
            content = result["content"][0]["text"].strip()

            # Parse JSON
            if "```" in content:
                parts = content.split("```")
                for part in parts:
                    stripped = part.strip()
                    if stripped.startswith("json"):
                        stripped = stripped[4:].strip()
                    if stripped.startswith("{"):
                        content = stripped
                        break

            parsed = json.loads(content)
            return parsed.get("intro", ""), parsed.get("summary", "")
        except Exception:
            logger.warning("Failed to generate intro/summary", exc_info=True)
            intro = f"☕️ Good morning! Here's your tech briefing - {len(topics)} areas, {total_articles} articles."
            summary = f"Today: {', '.join(topics[:3])} and more. Grab your coffee and dive in."
            return intro, summary

    def summarize_all(self, articles_by_topic: dict[str, list[Article]]) -> list[TopicSummary]:
        """Summarize articles for all topics."""
        summaries: list[TopicSummary] = []
        for topic_name, articles in articles_by_topic.items():
            summary = self.summarize_topic(topic_name, articles)
            if summary and summary.articles:
                summaries.append(summary)
        return summaries
