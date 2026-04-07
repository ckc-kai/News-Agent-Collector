import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.app.api.router import api_router
from src.app.cache.client import close_redis
from src.app.config import settings
from src.app.db.session import engine

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logging.getLogger(__name__).info("Starting %s", settings.app_name)
    yield
    # Shutdown
    await close_redis()
    await engine.dispose()
    logging.getLogger(__name__).info("Shutdown complete")


app = FastAPI(
    title=settings.app_name,
    description="Personalized news discovery and recommendation system",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router)
