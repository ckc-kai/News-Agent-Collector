import asyncio
import logging
from collections import defaultdict
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)

EventHandler = Callable[..., Coroutine[Any, Any, None]]


class EventBus:
    """In-process async event bus. Swappable to Redis pub/sub in Phase 2."""

    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        self._handlers[event_type].remove(handler)

    async def publish(self, event_type: str, **kwargs: Any) -> None:
        for handler in self._handlers.get(event_type, []):
            try:
                await handler(**kwargs)
            except Exception:
                logger.exception(
                    "Event handler %s failed for event %s",
                    handler.__name__,
                    event_type,
                )


# Singleton event bus
event_bus = EventBus()

# Event type constants
FEEDBACK_RECEIVED = "feedback.received"
PREFERENCE_UPDATED = "preference.updated"
PREFERENCE_DRIFT_DETECTED = "preference.drift_detected"
DIGEST_GENERATED = "digest.generated"
SOURCE_HEALTH_CHANGED = "source.health_changed"
