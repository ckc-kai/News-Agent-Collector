from fastapi import APIRouter

from src.app.sources.registry import source_registry

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/health/sources")
async def sources_health():
    results = {}
    for adapter in source_registry.get_all():
        try:
            healthy = await adapter.health_check()
            results[adapter.name] = {
                "healthy": healthy,
                "domains": adapter.supported_domains,
                "rate_limit_per_day": adapter.rate_limit_per_day,
            }
        except Exception as e:
            results[adapter.name] = {"healthy": False, "error": str(e)}
    return {"sources": results}
