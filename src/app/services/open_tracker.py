"""OpenTracker — syncs email click events from Cloudflare Worker and adjusts interest weights.

On each boot the deliver endpoint calls sync_email_clicks() before building the
digest.  The Worker stores a redirect log of every article link clicked in the
daily email; this service pulls those events and bumps the domain weight for the
corresponding articles (using a smaller increment than a direct UI click, because
an email click is slightly weaker signal).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.repositories.article import ArticleRepository
from src.app.db.repositories.user import UserRepository

logger = logging.getLogger(__name__)

OPEN_CLICK_WEIGHT_INCREMENT = 0.01  # weaker signal than direct UI click (0.02)


class OpenTracker:
    """Fetches click events from the Cloudflare Worker and updates domain weights."""

    def __init__(self, *, worker_url: str, worker_secret: str) -> None:
        self._worker_url = worker_url.rstrip("/")
        self._worker_secret = worker_secret

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def sync_email_clicks(
        self,
        session: AsyncSession,
        *,
        user_id: str,
        since_days: int = 7,
    ) -> int:
        """Fetch recent email clicks from Worker and bump domain weights.

        Returns the number of click events that were processed.
        """
        if not self._worker_url:
            logger.debug("OpenTracker: no Worker URL configured, skipping sync")
            return 0

        events = await self._fetch_worker_events(since_days=since_days)
        if not events:
            return 0

        article_repo = ArticleRepository(session)
        user_repo = UserRepository(session)
        processed = 0

        for event in events:
            article_id = event.get("article_id")
            if not article_id:
                continue

            article = await article_repo.get_by_id(article_id)
            if not article or not article.domain:
                logger.debug("OpenTracker: article %s not found or has no domain", article_id)
                continue

            pref = await user_repo.update_domain_preference(user_id, article.domain, weight=None)
            if pref:
                pref.weight = min(1.0, pref.weight + OPEN_CLICK_WEIGHT_INCREMENT)
                await session.flush()
                logger.info(
                    "Email click: user=%s domain=%s weight=%.2f (article=%s)",
                    user_id, article.domain, pref.weight, article_id,
                )
                processed += 1

        return processed

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _fetch_worker_events(self, *, since_days: int = 7) -> list[dict]:
        """GET /events from the Worker and return the events list.

        Returns [] on any error so a down/slow Worker never blocks delivery.
        """
        since = (datetime.now(timezone.utc) - timedelta(days=since_days)).strftime("%Y-%m-%d")
        url = f"{self._worker_url}/events"
        headers = {"Authorization": f"Bearer {self._worker_secret}"}

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url, headers=headers, params={"since": since})
            if resp.status_code != 200:
                logger.warning("OpenTracker: Worker returned %s", resp.status_code)
                return []
            return resp.json().get("events", [])
        except Exception as exc:
            logger.warning("OpenTracker: failed to fetch events — %s", exc)
            return []
