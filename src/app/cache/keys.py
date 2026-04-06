from datetime import date


def rate_limit_key(source_name: str, day: date | None = None) -> str:
    """Key for tracking daily API call count per source."""
    day = day or date.today()
    return f"rate_limit:{source_name}:{day.isoformat()}"


def article_cache_key(article_id: str) -> str:
    return f"article:{article_id}"


def user_vector_key(user_id: str) -> str:
    return f"user_vector:{user_id}"


def source_health_key(source_name: str) -> str:
    return f"source_health:{source_name}"
