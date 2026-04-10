"""Tests for DeliveryService — idempotency and Resend integration (TDD RED phase)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

from src.app.services.delivery import DeliveryService, DeliveryResult


def _make_mock_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    return session


def _make_mock_user():
    user = MagicMock()
    user.id = "user-001"
    user.name = "Test User"
    pref = MagicMock()
    pref.domain_id = "ai_ml"
    user.domain_preferences = [pref]
    return user


def _make_mock_digest(n_items: int = 2):
    digest = MagicMock()
    digest.id = "digest-001"
    items = []
    for i in range(n_items):
        item = MagicMock()
        item.article_id = f"article-{i}"
        item.position = i
        items.append(item)
    digest.items = sorted(items, key=lambda x: x.position)
    return digest


def _make_mock_article(idx: int = 0):
    article = MagicMock()
    article.title = f"Article {idx}"
    article.summary_l2 = f"Summary of article {idx}."
    article.summary_l1 = None
    article.domain = "ai_ml"
    article.source_url = f"https://example.com/{idx}"
    article.source_adapter = "event_registry"
    article.published_at = None
    return article


class TestDeliveryServiceIdempotency:
    @pytest.mark.asyncio
    async def test_skips_when_already_sent_today(self):
        """Returns skipped result if delivery_log already has today's record."""
        svc = DeliveryService()
        mock_session = _make_mock_session()

        with patch.object(svc, "_already_sent_today", new_callable=AsyncMock, return_value=True):
            result = await svc.send_digest_email(mock_session, "user-001")

        assert result.skipped is True
        assert result.reason == "already_sent_today"
        assert result.sent is False

    @pytest.mark.asyncio
    async def test_skips_when_no_digest(self):
        """Returns skipped result if no digest found for user."""
        svc = DeliveryService()
        mock_session = _make_mock_session()

        with patch.object(svc, "_already_sent_today", new_callable=AsyncMock, return_value=False), \
             patch("src.app.services.delivery.DigestRepository") as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.get_latest_for_user = AsyncMock(return_value=None)
            mock_repo_cls.return_value = mock_repo

            result = await svc.send_digest_email(mock_session, "user-001")

        assert result.skipped is True
        assert result.reason == "no_digest"

    @pytest.mark.asyncio
    async def test_sends_email_when_conditions_met(self):
        """Calls Resend and returns sent=True when no prior send and digest exists."""
        svc = DeliveryService()
        mock_session = _make_mock_session()

        with patch.object(svc, "_already_sent_today", new_callable=AsyncMock, return_value=False), \
             patch.object(svc, "_call_resend", new_callable=AsyncMock, return_value=None), \
             patch.object(svc, "_record_send", new_callable=AsyncMock), \
             patch("src.app.services.delivery.DigestRepository") as mock_digest_repo_cls, \
             patch("src.app.services.delivery.ArticleRepository") as mock_article_repo_cls, \
             patch("src.app.services.delivery.UserRepository") as mock_user_repo_cls:

            mock_digest_repo = AsyncMock()
            mock_digest_repo.get_latest_for_user = AsyncMock(return_value=_make_mock_digest())
            mock_digest_repo_cls.return_value = mock_digest_repo

            mock_article_repo = AsyncMock()
            mock_article_repo.get_by_id = AsyncMock(side_effect=lambda aid: _make_mock_article(int(aid.split("-")[-1])))
            mock_article_repo_cls.return_value = mock_article_repo

            mock_user_repo = AsyncMock()
            mock_user_repo.get_with_preferences = AsyncMock(return_value=_make_mock_user())
            mock_user_repo_cls.return_value = mock_user_repo

            result = await svc.send_digest_email(mock_session, "user-001")

        assert result.sent is True
        assert result.skipped is False

    @pytest.mark.asyncio
    async def test_calls_resend_once_on_success(self):
        """_call_resend is invoked exactly once per send."""
        svc = DeliveryService()
        mock_session = _make_mock_session()

        with patch.object(svc, "_already_sent_today", new_callable=AsyncMock, return_value=False), \
             patch.object(svc, "_call_resend", new_callable=AsyncMock, return_value=None) as mock_resend, \
             patch.object(svc, "_record_send", new_callable=AsyncMock), \
             patch("src.app.services.delivery.DigestRepository") as mock_digest_repo_cls, \
             patch("src.app.services.delivery.ArticleRepository") as mock_article_repo_cls, \
             patch("src.app.services.delivery.UserRepository") as mock_user_repo_cls:

            mock_digest_repo = AsyncMock()
            mock_digest_repo.get_latest_for_user = AsyncMock(return_value=_make_mock_digest())
            mock_digest_repo_cls.return_value = mock_digest_repo

            mock_article_repo = AsyncMock()
            mock_article_repo.get_by_id = AsyncMock(side_effect=lambda aid: _make_mock_article(0))
            mock_article_repo_cls.return_value = mock_article_repo

            mock_user_repo = AsyncMock()
            mock_user_repo.get_with_preferences = AsyncMock(return_value=_make_mock_user())
            mock_user_repo_cls.return_value = mock_user_repo

            await svc.send_digest_email(mock_session, "user-001")

        mock_resend.assert_called_once()

    @pytest.mark.asyncio
    async def test_records_failure_on_resend_error(self):
        """_record_send is called with status='failed' when Resend raises."""
        svc = DeliveryService()
        mock_session = _make_mock_session()

        with patch.object(svc, "_already_sent_today", new_callable=AsyncMock, return_value=False), \
             patch.object(svc, "_call_resend", new_callable=AsyncMock, side_effect=Exception("Resend 429")), \
             patch.object(svc, "_record_send", new_callable=AsyncMock) as mock_record, \
             patch("src.app.services.delivery.DigestRepository") as mock_digest_repo_cls, \
             patch("src.app.services.delivery.ArticleRepository") as mock_article_repo_cls, \
             patch("src.app.services.delivery.UserRepository") as mock_user_repo_cls:

            mock_digest_repo = AsyncMock()
            mock_digest_repo.get_latest_for_user = AsyncMock(return_value=_make_mock_digest())
            mock_digest_repo_cls.return_value = mock_digest_repo

            mock_article_repo = AsyncMock()
            mock_article_repo.get_by_id = AsyncMock(side_effect=lambda aid: _make_mock_article(0))
            mock_article_repo_cls.return_value = mock_article_repo

            mock_user_repo = AsyncMock()
            mock_user_repo.get_with_preferences = AsyncMock(return_value=_make_mock_user())
            mock_user_repo_cls.return_value = mock_user_repo

            with pytest.raises(Exception, match="Resend 429"):
                await svc.send_digest_email(mock_session, "user-001")

        mock_record.assert_called_once()
        _, kwargs = mock_record.call_args
        assert kwargs.get("status") == "failed"

    @pytest.mark.asyncio
    async def test_already_sent_today_returns_false_when_no_record(self):
        """_already_sent_today returns False when no delivery_log row for today."""
        from datetime import date
        svc = DeliveryService()
        mock_session = _make_mock_session()

        # Simulate empty result from DB
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await svc._already_sent_today(mock_session, date.today())
        assert result is False

    @pytest.mark.asyncio
    async def test_already_sent_today_returns_true_when_record_exists(self):
        """_already_sent_today returns True when delivery_log row exists."""
        from datetime import date
        svc = DeliveryService()
        mock_session = _make_mock_session()

        mock_log = MagicMock()  # Represents a DeliveryLog row
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_log)
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await svc._already_sent_today(mock_session, date.today())
        assert result is True


class TestResendEmailId:
    @pytest.mark.asyncio
    async def test_call_resend_returns_email_id(self):
        """_call_resend returns the Resend email ID from the API response."""
        import httpx
        from unittest.mock import patch, AsyncMock, MagicMock

        svc = DeliveryService()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json = MagicMock(return_value={"id": "resend-msg-001"})

        with patch("src.app.services.delivery.settings") as mock_settings, \
             patch("src.app.services.delivery.httpx.AsyncClient") as mock_client_cls:

            mock_settings.resend_api_key = "re_test"
            mock_settings.delivery_email_from = "test@example.com"
            mock_settings.delivery_email_to = "to@example.com"

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client_cls.return_value = mock_client

            email_id = await svc._call_resend(subject="Test", html="<p>Hi</p>", text="Hi")

        assert email_id == "resend-msg-001"

    @pytest.mark.asyncio
    async def test_send_digest_email_passes_resend_id_to_record_send(self):
        """send_digest_email passes the Resend email_id to _record_send."""
        svc = DeliveryService()
        mock_session = _make_mock_session()

        with patch.object(svc, "_already_sent_today", new_callable=AsyncMock, return_value=False), \
             patch.object(svc, "_call_resend", new_callable=AsyncMock, return_value="resend-abc-123") as mock_resend, \
             patch.object(svc, "_record_send", new_callable=AsyncMock) as mock_record, \
             patch("src.app.services.delivery.DigestRepository") as mock_digest_repo_cls, \
             patch("src.app.services.delivery.ArticleRepository") as mock_article_repo_cls, \
             patch("src.app.services.delivery.UserRepository") as mock_user_repo_cls:

            mock_digest_repo = AsyncMock()
            mock_digest_repo.get_latest_for_user = AsyncMock(return_value=_make_mock_digest())
            mock_digest_repo_cls.return_value = mock_digest_repo

            mock_article_repo = AsyncMock()
            mock_article_repo.get_by_id = AsyncMock(side_effect=lambda aid: _make_mock_article(0))
            mock_article_repo_cls.return_value = mock_article_repo

            mock_user_repo = AsyncMock()
            mock_user_repo.get_with_preferences = AsyncMock(return_value=_make_mock_user())
            mock_user_repo_cls.return_value = mock_user_repo

            await svc.send_digest_email(mock_session, "user-001")

        _, kwargs = mock_record.call_args
        assert kwargs.get("resend_email_id") == "resend-abc-123"
