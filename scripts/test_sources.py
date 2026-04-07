"""Health-check all configured source adapters."""

import asyncio
import sys
import time
sys.path.insert(0, ".")

from src.app.sources.registry import source_registry


async def main():
    adapters = source_registry.get_all()
    print(f"Registered adapters: {len(adapters)}")
    print("-" * 60)

    for adapter in adapters:
        start = time.time()
        try:
            healthy = await adapter.health_check()
            elapsed = (time.time() - start) * 1000
            status = "OK" if healthy else "UNHEALTHY"
            print(f"  {adapter.name:25s} {status:10s} ({elapsed:.0f}ms)")
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            print(f"  {adapter.name:25s} ERROR      ({elapsed:.0f}ms) — {e}")

    print("-" * 60)

    # Show which adapters were skipped
    all_names = [
        "tavily", "newsapi", "gnews", "newsdata", "arxiv",
        "semantic_scholar", "hackernews", "github_trending", "rss",
    ]
    registered = source_registry.get_names()
    skipped = [n for n in all_names if n not in registered]
    if skipped:
        print(f"Skipped (missing config): {', '.join(skipped)}")


if __name__ == "__main__":
    asyncio.run(main())
