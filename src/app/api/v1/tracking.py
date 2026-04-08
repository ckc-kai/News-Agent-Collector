import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.repositories.article import ArticleRepository
from src.app.db.repositories.user import UserRepository
from src.app.dependencies import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/track", tags=["tracking"])

CLICK_WEIGHT_INCREMENT = 0.02


class ClickEvent(BaseModel):
    user_id: str
    article_id: str


@router.post("/click")
async def track_click(
    event: ClickEvent,
    session: AsyncSession = Depends(get_db),
):
    """Track article click and adjust domain weight implicitly."""
    article_repo = ArticleRepository(session)
    article = await article_repo.get_by_id(event.article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    if not article.domain:
        return {"status": "ok", "adjusted": False}

    user_repo = UserRepository(session)
    pref = await user_repo.update_domain_preference(
        event.user_id,
        article.domain,
        weight=None,  # we'll handle increment below
    )

    if pref:
        new_weight = min(1.0, pref.weight + CLICK_WEIGHT_INCREMENT)
        pref.weight = new_weight
        await session.flush()
        logger.info(
            "Click: user=%s domain=%s weight=%.2f",
            event.user_id, article.domain, new_weight,
        )
        return {"status": "ok", "adjusted": True, "domain": article.domain, "new_weight": new_weight}

    return {"status": "ok", "adjusted": False}
