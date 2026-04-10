"""Tests for OpenTracker — syncs email click events from Cloudflare Worker (TDD RED phase)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.app.services.open_tracker import OpenTracker, OPEN_CLICK_WEIGHT_INCREMENT


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_weight_increment_is_smaller_than_direct_click(self):
        """Email click weight is weaker signal than direct UI click (0.02)."""
        from src.app.api.v1.tracking import CLICK_WEIGHT_INCREMENT
        assert OPEN_CLICK_WEIGHT_INCREMENT < CLICK_WEIGHT_INCREMENT
        assert OPEN_CLICK_WEIGHT_INCREMENT == 0.01


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    return session


def _make_article(domain: str = "ai_ml"):
    article = MagicMock()
    article.domain = domain
    return article


def _make_pref(weight: float = 0.5):
    pref = MagicMock()
    pref.weight = weight
    return pref


# ---------------------------------------------------------------------------
# Worker fetch
# ---------------------------------------------------------------------------

class TestFetchWorkerEvents:
    @pytest.mark.asyncio
    async def test_returns_empty_list_when_worker_has_no_events(self):
        """Returns [] when Worker responds with no events."""
        tracker = OpenTracker(
            worker_url="https://tracker.example.workers.dev",
            worker_secret="test-secret",
        )
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json = MagicMock(return_value={"events": []})

        with patch("src.app.services.open_tracker.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client_cls.return_value = mock_client

            events = await tracker._fetch_worker_events(since_days=7)

        assert events == []

    @pytest.mark.asyncio
    async def test_returns_events_from_worker(self):
        """Returns parsed click events from Worker response."""
        tracker = OpenTracker(
            worker_url="https://tracker.example.workers.dev",
            worker_secret="test-secret",
        )
        raw_events = [
            {"article_id": "abc123", "timestamp": "2026-04-10T10:00:00Z"},
            {"article_id": "def456", "timestamp": "2026-04-10T11:00:00Z"},
        ]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json = MagicMock(return_value={"events": raw_events})

        with patch("src.app.services.open_tracker.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client_cls.return_value = mock_client

            events = await tracker._fetch_worker_events(since_days=7)

        assert len(events) == 2
        assert events[0]["article_id"] == "abc123"

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_worker_unreachable(self):
        """Does not raise when Worker is unreachable — returns [] gracefully."""
        import httpx
        tracker = OpenTracker(
            worker_url="https://tracker.example.workers.dev",
            worker_secret="test-secret",
        )

        with patch("src.app.services.open_tracker.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("unreachable"))
            mock_client_cls.return_value = mock_client

            events = await tracker._fetch_worker_events(since_days=7)

        assert events == []

    @pytest.mark.asyncio
    async def test_sends_auth_header(self):
        """GET /events includes Bearer token in Authorization header."""
        tracker = OpenTracker(
            worker_url="https://tracker.example.workers.dev",
            worker_secret="my-secret",
        )
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json = MagicMock(return_value={"events": []})

        with patch("src.app.services.open_tracker.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client_cls.return_value = mock_client

            await tracker._fetch_worker_events(since_days=7)

        call_kwargs = mock_client.get.call_args
        headers = call_kwargs.kwargs.get("headers", {})
        assert headers.get("Authorization") == "Bearer my-secret"


# ---------------------------------------------------------------------------
# Weight adjustment
# ---------------------------------------------------------------------------

class TestSyncEmailClicks:
    @pytest.mark.asyncio
    async def test_no_weight_change_when_no_events(self):
        """No DB writes when Worker returns no click events."""
        tracker = OpenTracker(
            worker_url="https://tracker.example.workers.dev",
            worker_secret="test-secret",
        )
        session = _make_session()

        with patch.object(tracker, "_fetch_worker_events", new_callable=AsyncMock, return_value=[]):
            await tracker.sync_email_clicks(session, user_id="user-001")

        session.flush.assert_not_called()

    @pytest.mark.asyncio
    async def test_bumps_domain_weight_for_clicked_article(self):
        """Weight increases by OPEN_CLICK_WEIGHT_INCREMENT for the article's domain."""
        tracker = OpenTracker(
            worker_url="https://tracker.example.workers.dev",
            worker_secret="test-secret",
        )
        session = _make_session()
        article = _make_article(domain="ai_ml")
        pref = _make_pref(weight=0.5)

        events = [{"article_id": "abc123", "timestamp": "2026-04-10T10:00:00Z"}]

        with patch.object(tracker, "_fetch_worker_events", new_callable=AsyncMock, return_value=events), \
             patch("src.app.services.open_tracker.ArticleRepository") as mock_article_cls, \
             patch("src.app.services.open_tracker.UserRepository") as mock_user_cls:

            mock_article_repo = AsyncMock()
            mock_article_repo.get_by_id = AsyncMock(return_value=article)
            mock_article_cls.return_value = mock_article_repo

            mock_user_repo = AsyncMock()
            mock_user_repo.update_domain_preference = AsyncMock(return_value=pref)
            mock_user_cls.return_value = mock_user_repo

            await tracker.sync_email_clicks(session, user_id="user-001")

        assert pref.weight == pytest.approx(0.5 + OPEN_CLICK_WEIGHT_INCREMENT)
        session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_unknown_article_without_crashing(self):
        """If article not found in DB, skip it and continue."""
        tracker = OpenTracker(
            worker_url="https://tracker.example.workers.dev",
            worker_secret="test-secret",
        )
        session = _make_session()
        events = [{"article_id": "unknown-id", "timestamp": "2026-04-10T10:00:00Z"}]

        with patch.object(tracker, "_fetch_worker_events", new_callable=AsyncMock, return_value=events), \
             patch("src.app.services.open_tracker.ArticleRepository") as mock_article_cls:

            mock_article_repo = AsyncMock()
            mock_article_repo.get_by_id = AsyncMock(return_value=None)
            mock_article_cls.return_value = mock_article_repo

            # Must not raise
            await tracker.sync_email_clicks(session, user_id="user-001")

        session.flush.assert_not_called()

    @pytest.mark.asyncio
    async def test_weight_capped_at_one(self):
        """Weight never exceeds 1.0 even when already near maximum."""
        tracker = OpenTracker(
            worker_url="https://tracker.example.workers.dev",
            worker_secret="test-secret",
        )
        session = _make_session()
        article = _make_article(domain="ai_ml")
        pref = _make_pref(weight=0.99)

        events = [{"article_id": "abc123", "timestamp": "2026-04-10T10:00:00Z"}]

        with patch.object(tracker, "_fetch_worker_events", new_callable=AsyncMock, return_value=events), \
             patch("src.app.services.open_tracker.ArticleRepository") as mock_article_cls, \
             patch("src.app.services.open_tracker.UserRepository") as mock_user_cls:

            mock_article_repo = AsyncMock()
            mock_article_repo.get_by_id = AsyncMock(return_value=article)
            mock_article_cls.return_value = mock_article_repo

            mock_user_repo = AsyncMock()
            mock_user_repo.update_domain_preference = AsyncMock(return_value=pref)
            mock_user_cls.return_value = mock_user_repo

            await tracker.sync_email_clicks(session, user_id="user-001")

        assert pref.weight <= 1.0

    @pytest.mark.asyncio
    async def test_no_op_when_worker_url_not_configured(self):
        """Silently skips sync when no Worker URL is set."""
        tracker = OpenTracker(worker_url="", worker_secret="")
        session = _make_session()

        await tracker.sync_email_clicks(session, user_id="user-001")

        session.flush.assert_not_called()
