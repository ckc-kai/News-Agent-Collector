"""Topic expansion API — expands user-typed interests into subtopics."""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.app.services.topic_expander import TopicExpander

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/topics", tags=["topics"])

# Singleton expander (in-memory cache lives for the lifetime of the process)
_expander = TopicExpander()


class TopicExpandRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=200)


class TopicExpandResponse(BaseModel):
    topic: str
    suggestions: list[str]
    cached: bool


@router.post("/expand", response_model=TopicExpandResponse)
async def expand_topic(body: TopicExpandRequest):
    """Expand a topic into related subtopics using LLM with caching."""
    try:
        result = await _expander.expand(body.topic)
        return TopicExpandResponse(
            topic=result.parent_topic,
            suggestions=result.suggestions,
            cached=result.cached,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error("Topic expansion failed: %s", e)
        raise HTTPException(status_code=503, detail="LLM unavailable")
