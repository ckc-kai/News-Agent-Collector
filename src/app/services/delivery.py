"""DeliveryService — idempotent daily digest delivery via Resend."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.config import settings
from src.app.db.repositories.article import ArticleRepository
from src.app.db.repositories.digest import DigestRepository
from src.app.db.repositories.user import UserRepository
from src.app.models.delivery import DeliveryLog
from src.app.services.email_renderer import EmailRenderer

logger = logging.getLogger(__name__)


@dataclass
class DeliveryResult:
    sent: bool = False
    skipped: bool = False
    reason: str = ""


class DeliveryService:
    """Sends the daily digest email via Resend with date-level idempotency.

    One email per (sent_date, channel) pair — enforced both at the DB level
    (UNIQUE constraint) and in application logic before any HTTP call is made.
    """

    async def send_digest_email(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> DeliveryResult:
        today = date.today()

        if await self._already_sent_today(session, today):
            logger.info("Delivery skipped: already sent today (%s)", today)
            return DeliveryResult(skipped=True, reason="already_sent_today")

        digest_repo = DigestRepository(session)
        digest = await digest_repo.get_latest_for_user(user_id)
        if digest is None:
            logger.info("Delivery skipped: no digest found for user %s", user_id)
            return DeliveryResult(skipped=True, reason="no_digest")

        user_repo = UserRepository(session)
        user = await user_repo.get_with_preferences(user_id)

        article_repo = ArticleRepository(session)
        items: list[dict] = []
        for di in sorted(digest.items, key=lambda x: x.position):
            article = await article_repo.get_by_id(di.article_id)
            if article:
                published = ""
                if article.published_at:
                    published = article.published_at.strftime("%b %-d, %H:%M")
                items.append(
                    {
                        "title": article.title,
                        "summary": article.summary_l2 or article.summary_l1 or "",
                        "domain": article.domain or "",
                        "source_url": article.source_url,
                        "source_name": article.source_adapter,
                        "published_at": published,
                        "article_id": str(article.id),
                    }
                )

        renderer = EmailRenderer(worker_url=settings.cloudflare_worker_url)
        subject, html, text = renderer.render(items, sent_date=today)

        try:
            resend_email_id = await self._call_resend(subject=subject, html=html, text=text)
            await self._record_send(session, today, status="sent", resend_email_id=resend_email_id)
            logger.info("Digest email sent to %s (id=%s)", settings.delivery_email_to, resend_email_id)
            return DeliveryResult(sent=True)
        except Exception as exc:
            await self._record_send(session, today, status="failed", error_msg=str(exc))
            raise

    # ------------------------------------------------------------------
    # Internal helpers — individually testable
    # ------------------------------------------------------------------

    async def _already_sent_today(self, session: AsyncSession, today: date) -> bool:
        """Return True only if a *successful* send was recorded for today.

        Failed records do not block retries — a failed attempt on the same day
        should be retried on the next boot (or manual trigger).
        """
        stmt = select(DeliveryLog).where(
            DeliveryLog.sent_date == today,
            DeliveryLog.channel == "email",
            DeliveryLog.status == "sent",
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def _call_resend(self, *, subject: str, html: str, text: str) -> str:
        """Send via Resend API and return the Resend email ID."""
        if not settings.resend_api_key:
            raise RuntimeError(
                "RESEND_API_KEY is not set — cannot send email. "
                "Add it to .env and restart."
            )
        payload = {
            "from": settings.delivery_email_from,
            "to": [settings.delivery_email_to],
            "subject": subject,
            "html": html,
            "text": text,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json=payload,
            )
        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"Resend returned {resp.status_code}: {resp.text[:200]}"
            )
        return resp.json().get("id", "")

    async def _record_send(
        self,
        session: AsyncSession,
        sent_date: date,
        *,
        status: str,
        error_msg: str | None = None,
        resend_email_id: str | None = None,
    ) -> None:
        """Upsert a delivery record.

        Uses INSERT … ON CONFLICT DO UPDATE so that a failed record from a
        previous attempt is overwritten on retry, and the UNIQUE(sent_date,
        channel) constraint is never violated.
        """
        stmt = (
            pg_insert(DeliveryLog)
            .values(
                sent_date=sent_date,
                channel="email",
                status=status,
                error_msg=error_msg,
                resend_email_id=resend_email_id,
                created_at=datetime.utcnow(),
            )
            .on_conflict_do_update(
                index_elements=["sent_date", "channel"],
                set_={
                    "status": status,
                    "error_msg": error_msg,
                    "resend_email_id": resend_email_id,
                },
            )
        )
        await session.execute(stmt)
        await session.commit()
