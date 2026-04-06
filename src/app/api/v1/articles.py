from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.repositories.article import ArticleRepository
from src.app.dependencies import get_db
from src.app.schemas.article import ArticleResponse

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("", response_model=list[ArticleResponse])
async def list_articles(
    domain: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    days: int = Query(default=7, ge=1, le=30),
    session: AsyncSession = Depends(get_db),
):
    repo = ArticleRepository(session)
    if domain:
        articles = await repo.get_by_domain(domain, limit=limit, days=days)
    else:
        articles = await repo.get_recent(limit=limit, days=days)
    return articles


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: str,
    session: AsyncSession = Depends(get_db),
):
    repo = ArticleRepository(session)
    article = await repo.get_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article
