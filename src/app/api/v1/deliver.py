"""POST /api/v1/deliver — trigger idempotent daily email delivery."""

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.config import settings
from src.app.dependencies import get_db
from src.app.models.user import User
from src.app.db.repositories.user import UserRepository
from src.app.services.delivery import DeliveryService
from src.app.services.open_tracker import OpenTracker

logger = logging.getLogger(__name__)
router = APIRouter()

_open_tracker = OpenTracker(
    worker_url=settings.cloudflare_worker_url,
    worker_secret=settings.cloudflare_worker_secret,
)


async def _get_user(session: AsyncSession):
    result = await session.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if user:
        repo = UserRepository(session)
        return await repo.get_with_preferences(user.id)
    return None


@router.post("/deliver")
async def deliver(session: AsyncSession = Depends(get_db)) -> JSONResponse:
    """Deliver the daily digest email.

    On each call:
    1. Syncs any email click events from the Cloudflare Worker (updates domain weights).
    2. Sends the digest if not already sent today.

    Returns:
      {"status": "sent"}                        — first send of the day
      {"status": "skipped", "reason": "..."}    — already sent or no digest
      500 {"status": "error"}                   — unexpected failure
    """
    user = await _get_user(session)
    if not user:
        return JSONResponse({"status": "skipped", "reason": "no_user"})

    # Sync email click events from Worker before building today's digest
    try:
        synced = await _open_tracker.sync_email_clicks(session, user_id=user.id)
        if synced:
            logger.info("Synced %d email click event(s) from Worker", synced)
    except Exception:
        logger.warning("OpenTracker sync failed — continuing with delivery", exc_info=True)

    svc = DeliveryService()
    try:
        result = await svc.send_digest_email(session, user.id)
        if result.sent:
            return JSONResponse({"status": "sent"})
        return JSONResponse({"status": "skipped", "reason": result.reason})
    except Exception as exc:
        logger.exception("Delivery endpoint error")
        return JSONResponse({"status": "error", "detail": str(exc)}, status_code=500)
