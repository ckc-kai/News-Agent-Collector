import asyncio
import json
import logging

import httpx
from groq import AsyncGroq
from tenacity import retry, stop_after_attempt, wait_exponential

from src.app.config import settings
from src.app.pipeline.base import PipelineStage
from src.app.pipeline.context import PipelineContext
from src.app.schemas.article import NormalizedArticle

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a news article summarizer. Given an article title and content, generate a concise summary.

Return valid JSON only:
{
  "summary": "1-3 simple sentences describing the key point of this article."
}

Rules:
- Be factual and concise. 1-3 sentences max.
- Capture who, what, and why.
- For academic papers: state the key finding and method.
- Never hallucinate facts not present in the source.
- Return ONLY the JSON object."""

# Ollama endpoint for local LLM
_OLLAMA_URL = "http://localhost:11434/api/generate"
_OLLAMA_MODEL = "gemma4:26b"


_SUMMARIZE_CONCURRENCY = 4


class SummarizerStage(PipelineStage):
    """Generates summaries using local Ollama (Gemma 4) with Groq API fallback."""

    def __init__(self):
        if settings.groq_api_key:
            self._groq_client = AsyncGroq(api_key=settings.groq_api_key)
        else:
            self._groq_client = None

    @property
    def name(self) -> str:
        return "summarizer"

    async def process(
        self, articles: list[NormalizedArticle], context: PipelineContext
    ) -> list[NormalizedArticle]:
        ollama_available = await self._check_ollama()
        if ollama_available:
            logger.info("Using local Ollama for summarization (%d concurrent)", _SUMMARIZE_CONCURRENCY)
        elif self._groq_client:
            logger.info("Ollama unavailable, falling back to Groq API")
        else:
            logger.warning("No summarization backend available, skipping")
            return articles

        semaphore = asyncio.Semaphore(_SUMMARIZE_CONCURRENCY)

        async def _summarize_one(article: NormalizedArticle) -> bool:
            if article.summary_l2:
                return True
            if not article.raw_content and not article.title:
                return False

            async with semaphore:
                try:
                    summary = await self._summarize(article, ollama_available)
                    article.summary_l1 = summary[:80]
                    article.summary_l2 = summary
                    article.summary_l3 = summary
                    return True
                except Exception as e:
                    context.record_error(
                        self.name, f"Failed: {article.title[:50]}", str(e)
                    )
                    article.summary_l1 = article.title[:80]
                    article.summary_l2 = article.title
                    return False

        results = await asyncio.gather(*[_summarize_one(a) for a in articles])
        summarized = sum(1 for r in results if r)

        context.record_stat(self.name, "summarized", summarized)
        context.record_stat(self.name, "skipped", len(articles) - summarized)
        return articles

    async def _check_ollama(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get("http://localhost:11434/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    async def _summarize(
        self, article: NormalizedArticle, use_ollama: bool
    ) -> str:
        user_content = f"Title: {article.title}\n\nContent: {article.raw_content[:4000]}"

        if use_ollama:
            try:
                return await self._summarize_ollama(user_content)
            except Exception:
                logger.warning("Ollama failed, falling back to Groq")
                if self._groq_client:
                    return await self._summarize_groq(user_content)
                raise

        return await self._summarize_groq(user_content)

    async def _summarize_ollama(self, user_content: str) -> str:
        prompt = f"{_SYSTEM_PROMPT}\n\n{user_content}"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                _OLLAMA_URL,
                json={
                    "model": _OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.3, "num_predict": 300},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            parsed = json.loads(data["response"])
            return parsed.get("summary", "")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _summarize_groq(self, user_content: str) -> str:
        response = await self._groq_client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            max_tokens=300,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        parsed = json.loads(content)
        return parsed.get("summary", "")
