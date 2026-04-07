"""Seed the 8-domain taxonomy. Run once after initial migration."""

import asyncio
import sys
sys.path.insert(0, ".")

from src.app.core.constants import DomainID, DOMAIN_KEYWORDS


async def main():
    print("Domain taxonomy (8 domains):")
    print("-" * 50)
    for domain in DomainID:
        keywords = DOMAIN_KEYWORDS.get(domain, [])
        print(f"  {domain.value:20s} — {len(keywords)} keywords")
    print("-" * 50)
    print(f"Total: {len(DomainID)} domains")
    print("\nDomains are defined in src/app/core/constants.py")
    print("No database seeding needed — domains are used as string IDs.")


if __name__ == "__main__":
    asyncio.run(main())
