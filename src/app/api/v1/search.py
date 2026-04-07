from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.dependencies import get_db
from src.app.pipeline.context import PipelineContext
from src.app.pipeline.orchestrator import PipelineOrchestrator
from src.app.pipeline.stages.normalizer import NormalizerStage
from src.app.pipeline.stages.deduplicator import DeduplicatorStage
from src.app.pipeline.stages.classifier import ClassifierStage
from src.app.schemas.search import SearchQuery
from src.app.services.aggregation import AggregationService

router = APIRouter(prefix="/search", tags=["search"])


@router.post("")
async def search_articles(
    query: SearchQuery,
    session: AsyncSession = Depends(get_db),
):
    """Multi-source search with deduplication."""
    aggregator = AggregationService()
    raw_articles = await aggregator.search(query.query, max_results=query.max_results)

    # Run lightweight pipeline (normalize + dedup + classify, no summarization)
    pipeline = (
        PipelineOrchestrator()
        .add_stage(NormalizerStage())
        .add_stage(DeduplicatorStage())
        .add_stage(ClassifierStage())
    )
    context = PipelineContext()
    processed = await pipeline.run(raw_articles, context)

    # Filter by domain if requested
    if query.domains:
        processed = [a for a in processed if a.domain in query.domains]

    return {
        "query": query.query,
        "total_results": len(processed),
        "articles": [
            {
                "id": a.id,
                "title": a.title,
                "source_url": a.source_url,
                "source_adapter": a.source_adapter,
                "domain": a.domain,
                "published_at": a.published_at,
                "tags": a.tags,
                "media_type": a.media_type,
            }
            for a in processed[:query.max_results]
        ],
        "sources_queried": list({a.source_adapter for a in processed}),
    }
