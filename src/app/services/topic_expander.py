"""Topic expansion service: LLM-powered subtopic suggestions with caching.

Speed strategy: Groq (llama-3.1-8b-instant) is primary for topic expansion —
it responds in ~300ms. Ollama is fallback. This is the inverse of summarization,
where quality matters more than latency.
"""

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta

import httpx
from groq import AsyncGroq

from src.app.config import settings

logger = logging.getLogger(__name__)

_OLLAMA_URL = "http://localhost:11434/api/generate"
# Use a smaller, faster model for the lightweight expansion task
_OLLAMA_EXPAND_MODEL = "gemma3:4b"

# Fast Groq model for topic expansion (primary — ~300ms)
_GROQ_EXPAND_MODEL = "llama-3.1-8b-instant"

_EXPAND_PROMPT = """Given the topic '{topic}', list 8-12 specific subtopics for daily news.

Return valid JSON only:
{{"subtopics": ["subtopic1", "subtopic2", "subtopic3"]}}

Rules:
- Each subtopic: 1-4 words, no hyphens, no punctuation
- Be specific (e.g. "machine learning" not "technology")
- Return ONLY the JSON object, nothing else."""

_QUERY_PROMPT = """Generate 3 search queries for the latest news about '{domain}' today.

Return valid JSON only:
{{"queries": ["query1", "query2", "query3"]}}

Rules:
- Find breaking news and recent developments
- Return ONLY the JSON object."""

_NATURE_PROMPT = """Classify this topic into 1-3 source types from the list below.

Return valid JSON only:
{{"natures": ["type1", "type2"]}}

Valid types:
- academic: research papers, algorithms, mathematical theory, scientific discoveries
- industry_news: company news, product launches, business, markets, regulation, policy
- community_tech: developer tools, open source software, programming, GitHub, engineering
- general_news: sports, entertainment, culture, current events, lifestyle

Topic: '{topic}'

Return ONLY the JSON object."""

CACHE_TTL_DAYS = 7
_MAX_SUGGESTION_LEN = 40
_MAX_WORD_REPEAT = 2  # Reject if any word appears more than this many times

# Valid source-affinity nature strings
VALID_NATURES: frozenset[str] = frozenset({
    "academic",        # Research papers, algorithms, science → arxiv, semantic_scholar
    "industry_news",   # Companies, products, markets, policy → event_registry, gnews
    "community_tech",  # Dev tools, OSS, HN-style discussion → hackernews, github_trending
    "general_news",    # Sports, culture, current events → event_registry, newsdata
})


@dataclass
class TopicSuggestionResult:
    parent_topic: str
    suggestions: list[str]
    cached: bool = False


@dataclass
class _CacheEntry:
    data: list[str]
    expires_at: datetime


def _sanitize_suggestions(raw: list[str]) -> list[str]:
    """Remove looping/corrupt suggestions from LLM output."""
    clean = []
    for item in raw:
        if not isinstance(item, str):
            continue
        # Trim whitespace and cap length
        item = item.strip()[:_MAX_SUGGESTION_LEN]
        if not item:
            continue
        # Reject if any word is repeated more than allowed (Lifecycle-Lifecycle bug)
        words = re.split(r"[\s\-]+", item.lower())
        if any(words.count(w) > _MAX_WORD_REPEAT for w in set(words)):
            logger.warning("Rejected looping suggestion: %s", item[:60])
            continue
        # Reject suspiciously long single-word tokens (sign of repetition loop)
        if len(item) > 30 and " " not in item and "-" in item:
            logger.warning("Rejected hyphen-chain suggestion: %s", item[:60])
            continue
        clean.append(item)
    return clean


class TopicExpander:
    """Expands a user-typed topic into related subtopics using LLM, with in-memory caching."""

    def __init__(self) -> None:
        self._suggestion_cache: dict[str, _CacheEntry] = {}
        self._query_cache: dict[str, _CacheEntry] = {}
        self._nature_cache: dict[str, _CacheEntry] = {}
        if settings.groq_api_key:
            self._groq_client = AsyncGroq(api_key=settings.groq_api_key)
        else:
            self._groq_client = None

    async def expand(self, topic: str) -> TopicSuggestionResult:
        """Expand a topic into related subtopics."""
        topic = topic.strip()
        if not topic:
            raise ValueError("Topic cannot be empty")

        cache_key = topic.lower()

        cached = self._suggestion_cache.get(cache_key)
        if cached and cached.expires_at > datetime.utcnow():
            return TopicSuggestionResult(
                parent_topic=cache_key,
                suggestions=cached.data,
                cached=True,
            )

        prompt = _EXPAND_PROMPT.format(topic=topic)
        subtopics = await self._call_llm(prompt, parse_key="subtopics")
        subtopics = _sanitize_suggestions(subtopics)

        self._suggestion_cache[cache_key] = _CacheEntry(
            data=subtopics,
            expires_at=datetime.utcnow() + timedelta(days=CACHE_TTL_DAYS),
        )

        return TopicSuggestionResult(
            parent_topic=cache_key,
            suggestions=subtopics,
            cached=False,
        )

    async def classify_source_affinity(self, topic: str) -> list[str]:
        """Classify a topic into source-affinity natures (cached 7 days).

        Returns a list of nature strings from VALID_NATURES. Falls back to
        ['general_news'] if the LLM returns nothing useful.
        """
        topic = topic.strip()
        if not topic:
            raise ValueError("Topic cannot be empty")

        cache_key = topic.lower()
        cached = self._nature_cache.get(cache_key)
        if cached and cached.expires_at > datetime.utcnow():
            return cached.data

        prompt = _NATURE_PROMPT.format(topic=topic)
        raw_natures = await self._call_llm(prompt, parse_key="natures")
        natures = [n for n in raw_natures if n in VALID_NATURES]
        if not natures:
            natures = ["general_news"]

        self._nature_cache[cache_key] = _CacheEntry(
            data=natures,
            expires_at=datetime.utcnow() + timedelta(days=CACHE_TTL_DAYS),
        )
        return natures

    async def generate_queries(self, domain: str) -> list[str]:
        """Generate search queries for a custom domain."""
        domain = domain.strip()
        if not domain:
            raise ValueError("Domain cannot be empty")

        cache_key = domain.lower()

        cached = self._query_cache.get(cache_key)
        if cached and cached.expires_at > datetime.utcnow():
            return cached.data

        prompt = _QUERY_PROMPT.format(domain=domain)
        queries = await self._call_llm(prompt, parse_key="queries")

        self._query_cache[cache_key] = _CacheEntry(
            data=queries,
            expires_at=datetime.utcnow() + timedelta(days=CACHE_TTL_DAYS),
        )

        return queries

    async def _call_llm(self, prompt: str, parse_key: str) -> list[str]:
        """Groq first (fast ~300ms), Ollama fallback."""
        if self._groq_client:
            try:
                return await self._call_groq(prompt, parse_key)
            except Exception as e:
                logger.warning("Groq failed for topic expansion: %s, trying Ollama", e)

        if await self._check_ollama():
            try:
                return await self._call_ollama(prompt, parse_key)
            except Exception as e:
                logger.warning("Ollama also failed: %s", e)

        raise RuntimeError("No LLM backend available")

    async def _check_ollama(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get("http://localhost:11434/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    async def _call_ollama(self, prompt: str, parse_key: str) -> list[str]:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                _OLLAMA_URL,
                json={
                    "model": _OLLAMA_EXPAND_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 300,
                        "repeat_penalty": 1.3,  # Prevents Lifecycle-Lifecycle loops
                        "stop": ["\n\n", "```"],
                    },
                },
            )
            resp.raise_for_status()
            data = resp.json()
            parsed = json.loads(data["response"])
            return parsed.get(parse_key, [])

    async def _call_groq(self, prompt: str, parse_key: str) -> list[str]:
        response = await self._groq_client.chat.completions.create(
            model=_GROQ_EXPAND_MODEL,  # Fast 8B model, not the 70B used for summarization
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        parsed = json.loads(content)
        return parsed.get(parse_key, [])
