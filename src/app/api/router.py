from fastapi import APIRouter

from src.app.api.v1 import health, articles, users, feedback, digest, search, preferences, tracking, topics

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(articles.router)
api_router.include_router(users.router)
api_router.include_router(feedback.router)
api_router.include_router(digest.router)
api_router.include_router(search.router)
api_router.include_router(preferences.router)
api_router.include_router(tracking.router)
api_router.include_router(topics.router)
