"""Frontend routes serving Jinja2 templates."""

import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.constants import DomainID, DOMAIN_KEYWORDS
from src.app.db.repositories.article import ArticleRepository
from src.app.db.repositories.digest import DigestRepository
from src.app.db.repositories.user import UserRepository
from src.app.db.session import AsyncSessionLocal
from src.app.dependencies import get_db
from src.app.digest.builder import DigestBuilder
from src.app.models.user import User, UserDomainPreference
from src.app.pipeline.context import PipelineContext
from src.app.pipeline.orchestrator import PipelineOrchestrator
from src.app.pipeline.stages.normalizer import NormalizerStage
from src.app.pipeline.stages.deduplicator import DeduplicatorStage
from src.app.pipeline.stages.classifier import ClassifierStage
from src.app.pipeline.stages.enricher import EnricherStage
from src.app.pipeline.stages.summarizer import SummarizerStage
from src.app.pipeline.stages.storer import StorerStage
from src.app.recommendation.engine import RecommendationEngine
from src.app.services.aggregation import AggregationService
from src.app.services.delivery import DeliveryService

logger = logging.getLogger(__name__)

router = APIRouter()

_TEMPLATE_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))

# Human-readable labels for domains
DOMAIN_LABELS: dict[str, str] = {
    DomainID.AI_ML: "AI / Machine Learning",
    DomainID.TECH: "Technology",
    DomainID.ECON: "Economics",
    DomainID.POLITICS: "Politics",
    DomainID.BIOTECH: "Biotech",
    DomainID.SCIENCE: "Science",
    DomainID.SUSTAINABILITY: "Sustainability",
    DomainID.OSS: "Open Source",
    DomainID.FINANCE: "Finance",
    DomainID.CRYPTO: "Crypto",
    DomainID.HEALTH: "Health",
    DomainID.SPORTS: "Sports",
    DomainID.ENTERTAINMENT: "Entertainment",
    DomainID.EDUCATION: "Education",
    DomainID.STARTUPS: "Startups",
    DomainID.CYBERSECURITY: "Cybersecurity",
}

# Simple in-memory generation status (single-user, so this is fine)
_generation_status: dict[str, str] = {"state": "idle", "step": ""}


async def _get_user(session: AsyncSession) -> User | None:
    result = await session.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if user:
        repo = UserRepository(session)
        return await repo.get_with_preferences(user.id)
    return None


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, session: AsyncSession = Depends(get_db)):
    user = await _get_user(session)
    if not user:
        return RedirectResponse(url="/onboarding", status_code=302)

    # Get latest digest
    digest_repo = DigestRepository(session)
    digest = await digest_repo.get_latest_for_user(user.id)

    items = []
    exploration_items = []
    user_domains = {dp.domain_id for dp in user.domain_preferences}

    if digest:
        article_repo = ArticleRepository(session)
        for item in sorted(digest.items, key=lambda i: i.position):
            article = await article_repo.get_by_id(item.article_id)
            if article:
                published = ""
                if article.published_at:
                    published = article.published_at.strftime("%b %d, %H:%M")
                entry = {
                    "title": article.title,
                    "summary": article.summary_l2 or article.summary_l1 or "",
                    "domain": article.domain,
                    "source_url": article.source_url,
                    "source_name": article.source_adapter,
                    "published_at": published,
                    "article_id": article.id,
                }
                # All digest articles go to main feed; exploration articles are
                # those from domains the user didn't explicitly set (if any overlap).
                # We no longer exclude articles just because the classifier assigned
                # a different domain than the raw user preference string.
                items.append(entry)

    return templates.TemplateResponse("feed.html", {
        "request": request,
        "items": items,
        "exploration_items": exploration_items[:3],
        "user_id": user.id,
        "message": None,
    })


@router.get("/onboarding", response_class=HTMLResponse)
async def onboarding_page(request: Request, session: AsyncSession = Depends(get_db)):
    user = await _get_user(session)
    if user:
        return RedirectResponse(url="/", status_code=302)

    popular_topics = [{"id": d.value, "label": DOMAIN_LABELS.get(d, d.value)} for d in DomainID]
    return templates.TemplateResponse("onboarding.html", {
        "request": request,
        "popular_topics": popular_topics,
    })


@router.post("/onboarding")
async def onboarding_submit(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    form = await request.form()
    name = form.get("name", "User")
    interests = form.getlist("interests")

    if not interests:
        popular_topics = [{"id": d.value, "label": DOMAIN_LABELS.get(d, d.value)} for d in DomainID]
        return templates.TemplateResponse("onboarding.html", {
            "request": request,
            "popular_topics": popular_topics,
            "error": "Please select at least one interest.",
        })

    user = User(
        name=name,
        global_depth_fallback="L2",
        exploration_rate=0.15,
        onboarding_completed=True,
    )
    session.add(user)
    await session.flush()

    for interest in interests:
        pref = UserDomainPreference(
            user_id=user.id,
            domain_id=interest,
            weight=0.5,
            depth_preference="L2",
            is_explicit=True,
        )
        session.add(pref)

    await session.flush()
    return RedirectResponse(url="/", status_code=302)


async def _run_generation(
    user_id: str, domains_with_weights: list[tuple[str, float]]
) -> None:
    """Background task: fetch → pipeline → digest. Updates _generation_status."""
    global _generation_status
    try:
        _generation_status = {"state": "running", "step": "Searching the internet..."}

        aggregator = AggregationService()
        all_known = list(DOMAIN_KEYWORDS.keys())
        raw_articles, exploration_articles = await aggregator.fetch_smart_with_exploration(
            domains_with_weights, all_known_domains=all_known
        )
        raw_articles = raw_articles + exploration_articles

        if not raw_articles:
            _generation_status = {"state": "done", "step": "No articles found."}
            return

        _generation_status["step"] = f"Processing {len(raw_articles)} articles..."

        async with AsyncSessionLocal() as session:
            pipeline = (
                PipelineOrchestrator()
                .add_stage(NormalizerStage())
                .add_stage(DeduplicatorStage())
                .add_stage(ClassifierStage())
                .add_stage(EnricherStage())
            )
            context = PipelineContext(db_session=session)
            processed = await pipeline.run(raw_articles, context)

            _generation_status["step"] = f"Summarizing {len(processed)} articles..."

            summarizer = SummarizerStage()
            processed = await summarizer.process(processed, context)

            _generation_status["step"] = "Saving articles..."

            storer = StorerStage()
            await storer.process(processed, context)

            _generation_status["step"] = "Building your feed..."

            repo = UserRepository(session)
            user = await repo.get_with_preferences(user_id)
            article_repo = ArticleRepository(session)
            candidates = await article_repo.get_recent(limit=100, days=7)

            builder = DigestBuilder(engine=RecommendationEngine())
            await builder.build(user, candidates, session)
            await session.commit()

            # Auto-deliver after generation — idempotent, skips if already sent today
            try:
                delivery_svc = DeliveryService()
                delivery_result = await delivery_svc.send_digest_email(session, user_id)
                if delivery_result.sent:
                    logger.info("Digest email delivered automatically")
                elif delivery_result.skipped:
                    logger.info("Email delivery skipped: %s", delivery_result.reason)
            except Exception:
                logger.exception("Auto-delivery failed — digest is still available in browser")

        _generation_status = {"state": "done", "step": "Ready!"}

    except Exception as e:
        logger.exception("Generation failed")
        _generation_status = {"state": "error", "step": f"Error: {e}"}


@router.post("/generate")
async def generate(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    global _generation_status

    if _generation_status["state"] == "running":
        return JSONResponse({"status": "already_running"})

    user = await _get_user(session)
    if not user:
        return RedirectResponse(url="/onboarding", status_code=302)

    domains_with_weights = [
        (dp.domain_id, dp.weight)
        for dp in user.domain_preferences
        if dp.weight > 0
    ]
    if not domains_with_weights:
        return RedirectResponse(url="/preferences", status_code=302)

    _generation_status = {"state": "running", "step": "Starting..."}

    # Fire and forget — runs in the background
    asyncio.create_task(_run_generation(user.id, domains_with_weights))

    return RedirectResponse(url="/loading", status_code=302)


@router.get("/loading", response_class=HTMLResponse)
async def loading_page(request: Request):
    return templates.TemplateResponse("loading.html", {"request": request})


@router.get("/generate/status")
async def generation_status():
    return JSONResponse(_generation_status)


@router.get("/preferences", response_class=HTMLResponse)
async def preferences_page(request: Request, session: AsyncSession = Depends(get_db)):
    user = await _get_user(session)
    if not user:
        return RedirectResponse(url="/onboarding", status_code=302)

    return templates.TemplateResponse("preferences.html", {
        "request": request,
        "preferences": user.domain_preferences,
    })
