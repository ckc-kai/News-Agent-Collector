import json
import logging

from groq import AsyncGroq
from tenacity import retry, stop_after_attempt, wait_exponential

from src.app.config import settings
from src.app.pipeline.base import PipelineStage
from src.app.pipeline.context import PipelineContext
from src.app.schemas.article import NormalizedArticle

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a news article summarizer. Given an article title and content, generate summaries at three depth levels. Return valid JSON only, no markdown.

Output format:
{
  "l1": "Headline summary in ≤ 15 words",
  "l2": "3-5 sentence summary covering key points (200-300 words)",
  "l3": "2-3 paragraph deep dive with key findings, methodology (if applicable), and implications (500-800 words)"
}

Rules:
- L1: Must be ≤ 15 words. Capture the single most important takeaway.
- L2: Cover who, what, when, where, why. Be factual and concise.
- L3: Include context, significance, key data points, and quotes if available.
- For academic papers: always reference the abstract, key findings, and methodology.
- Never hallucinate facts not present in the source material.
- Return ONLY the JSON object, no other text."""


class SummarizerStage(PipelineStage):
    """Generates L1/L2/L3 summaries using Groq API."""

    def __init__(self):
        if settings.groq_api_key:
            self._client = AsyncGroq(api_key=settings.groq_api_key)
        else:
            self._client = None

    @property
    def name(self) -> str:
        return "summarizer"

    async def process(
        self, articles: list[NormalizedArticle], context: PipelineContext
    ) -> list[NormalizedArticle]:
        if not self._client:
            logger.warning("Groq API key not configured, skipping summarization")
            return articles

        summarized = 0
        for article in articles:
            # Skip if already summarized
            if article.summary_l1 and article.summary_l2:
                summarized += 1
                continue

            # Skip articles with no content to summarize
            if not article.raw_content and not article.title:
                continue

            try:
                summaries = await self._summarize(article)
                article.summary_l1 = summaries.get("l1", article.title[:80])
                article.summary_l2 = summaries.get("l2", "")
                article.summary_l3 = summaries.get("l3", "")
                summarized += 1
            except Exception as e:
                context.record_error(self.name, f"Failed to summarize: {article.title[:50]}", str(e))
                # Fall back to title as L1
                article.summary_l1 = article.title[:80]
                logger.warning("Summarization failed for article: %s", article.title[:50])

        context.record_stat(self.name, "summarized", summarized)
        context.record_stat(self.name, "skipped", len(articles) - summarized)
        return articles

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _summarize(self, article: NormalizedArticle) -> dict:
        user_content = f"Title: {article.title}\n\nContent: {article.raw_content[:4000]}"

        response = await self._client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            max_tokens=1500,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        return json.loads(content)
