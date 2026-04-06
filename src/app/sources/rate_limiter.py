import logging
from datetime import date, timedelta

from src.app.cache.client import get_redis
from src.app.cache.keys import rate_limit_key

logger = logging.getLogger(__name__)


class RateLimiter:
    """Redis-backed daily API call budget tracker per source."""

    async def can_call(self, source_name: str, limit: int) -> bool:
        """Check if the source has remaining budget for today."""
        redis = await get_redis()
        key = rate_limit_key(source_name)
        count = await redis.get(key)
        return count is None or int(count) < limit

    async def record_call(self, source_name: str, limit: int) -> bool:
        """Record an API call. Returns False if budget is exhausted."""
        redis = await get_redis()
        key = rate_limit_key(source_name)
        count = await redis.incr(key)

        # Set expiry to midnight if this is the first call today
        if count == 1:
            tomorrow = date.today() + timedelta(days=1)
            seconds_until_midnight = (
                int(
                    (
                        __import__("datetime").datetime.combine(
                            tomorrow, __import__("datetime").time.min
                        )
                        - __import__("datetime").datetime.now()
                    ).total_seconds()
                )
            )
            await redis.expire(key, seconds_until_midnight)

        if count > limit:
            logger.warning("Rate limit reached for %s (%d/%d)", source_name, count, limit)
            return False
        return True

    async def get_remaining(self, source_name: str, limit: int) -> int:
        """Get remaining calls for today."""
        redis = await get_redis()
        key = rate_limit_key(source_name)
        count = await redis.get(key)
        used = int(count) if count else 0
        return max(0, limit - used)


rate_limiter = RateLimiter()
