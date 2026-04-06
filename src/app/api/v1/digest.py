import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.db.repositories.article import ArticleRepository
from src.app.db.repositories.digest import DigestRepository
from src.app.db.repositories.user import UserRepository
from src.app.dependencies import get_db, get_digest_builder
from src.app.digest.builder import DigestBuilder
from src.app.pipeline.context import PipelineContext
from src.app.pipeline.orchestrator import PipelineOrchestrator
from src.app.pipeline.stages.normalizer import NormalizerStage
from src.app.pipeline.stages.deduplicator import DeduplicatorStage
from src.app.pipeline.stages.classifier import ClassifierStage
from src.app.pipeline.stages.enricher import EnricherStage
from src.app.pipeline.stages.summarizer import SummarizerStage
from src.app.pipeline.stages.storer import StorerStage
from src.app.services.aggregation import AggregationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/digest", tags=["digest"])


@router.get("/{user_id}")
async def get_latest_digest(
    user_id: str,
    session: AsyncSession = Depends(get_db),
):
    user_repo = UserRepository(session)
    user = await user_repo.get_with_preferences(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    digest_repo = DigestRepository(session)
    digest = await digest_repo.get_latest_for_user(user_id)
    if not digest:
        raise HTTPException(status_code=404, detail="No digest found for this user")

    # Build response with article data
    article_repo = ArticleRepository(session)
    items = []
    for item in sorted(digest.items, key=lambda i: i.position):
        article = await article_repo.get_by_id(item.article_id)
        if article:
            items.append({
                "position": item.position,
                "rendered_depth": item.rendered_depth,
                "final_score": item.final_score,
                "is_exploration": item.is_exploration,
                "article": {
                    "id": article.id,
                    "title": article.title,
                    "source_url": article.source_url,
                    "source_adapter": article.source_adapter,
                    "authors": article.authors or [],
                    "published_at": article.published_at,
                    "domain": article.domain,
                    "tags": article.tags or [],
                    "media_type": article.media_type,
                    "importance_score": article.importance_score,
                    "summary_l1": article.summary_l1,
                    "summary_l2": article.summary_l2,
                    "summary_l3": article.summary_l3,
                },
            })

    return {
        "id": digest.id,
        "user_id": digest.user_id,
        "generated_at": digest.generated_at,
        "item_count": digest.item_count,
        "items": items,
    }


@router.post("/{user_id}/generate")
async def generate_digest(
    user_id: str,
    session: AsyncSession = Depends(get_db),
    builder: DigestBuilder = Depends(get_digest_builder),
):
    """Full pipeline: fetch → process → recommend → build digest."""
    user_repo = UserRepository(session)
    user = await user_repo.get_with_preferences(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Determine which domains to fetch
    domains = [dp.domain_id for dp in user.domain_preferences if dp.weight > 0]
    if not domains:
        raise HTTPException(status_code=400, detail="User has no active domain preferences")

    # Fetch articles from sources
    aggregator = AggregationService()
    raw_articles = await aggregator.fetch_for_domains(domains, max_per_source=5)

    if not raw_articles:
        raise HTTPException(status_code=404, detail="No articles found from any source")

    # Run pipeline
    pipeline = (
        PipelineOrchestrator()
        .add_stage(NormalizerStage())
        .add_stage(DeduplicatorStage())
        .add_stage(ClassifierStage())
        .add_stage(EnricherStage())
        .add_stage(SummarizerStage())
        .add_stage(StorerStage())
    )
    context = PipelineContext(db_session=session)
    processed = await pipeline.run(raw_articles, context)

    # Need Article model instances for recommendation
    article_repo = ArticleRepository(session)
    candidates = await article_repo.get_recent(limit=100, days=7)

    # Build digest
    digest = await builder.build(user, candidates, session)

    return {
        "digest_id": digest.id,
        "item_count": digest.item_count,
        "pipeline_stats": context.stats,
        "pipeline_errors": context.errors,
    }
