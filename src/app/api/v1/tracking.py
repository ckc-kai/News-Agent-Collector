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
EXPLORATION_INITIAL_WEIGHT = 0.1


class ClickEvent(BaseModel):
    user_id: str
    article_id: str
    exploration: bool = False


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
        weight=None,
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

    # Exploration click: create a new preference with low weight
    if event.exploration and article.domain:
        from src.app.models.user import UserDomainPreference
        new_pref = UserDomainPreference(
            user_id=event.user_id,
            domain_id=article.domain,
            weight=EXPLORATION_INITIAL_WEIGHT,
            depth_preference="L2",
            is_explicit=False,
        )
        session.add(new_pref)
        await session.flush()
        logger.info(
            "Exploration click: user=%s domain=%s weight=%.2f",
            event.user_id, article.domain, EXPLORATION_INITIAL_WEIGHT,
        )
        return {"status": "ok", "adjusted": True, "domain": article.domain, "new_weight": EXPLORATION_INITIAL_WEIGHT}

    return {"status": "ok", "adjusted": False}
