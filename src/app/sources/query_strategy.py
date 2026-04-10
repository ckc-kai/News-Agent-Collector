"""Domain-to-source priority mapping from PRD Section 9.2.

Each domain has primary, secondary, and fallback sources.
The aggregation service uses this to decide which adapters to query.
"""

from src.app.core.constants import DomainID


# Priority-ordered source lists per domain
DOMAIN_SOURCE_PRIORITY: dict[str, list[str]] = {
    DomainID.AI_ML: [
        "arxiv",              # Primary: best for papers
        "semantic_scholar",   # Secondary: citations + importance
        "event_registry",     # Tertiary: full-body news + paywall-free
        "hackernews",         # Community signal
        "rss",
    ],
    DomainID.TECH: [
        "event_registry",     # Primary: concept-filtered, full body
        "hackernews",         # Secondary: community signal
        "github_trending",    # Tertiary: OSS activity
        "rss",
        "gnews",
    ],
    DomainID.ECON: [
        "event_registry",     # Primary: concept-filtered, full body
        "gnews",              # Secondary
        "newsdata",           # Tertiary
        "rss",
    ],
    DomainID.POLITICS: [
        "event_registry",     # Primary: concept-filtered, geo-aware
        "newsdata",           # Secondary
        "gnews",              # Tertiary
        "rss",
    ],
    DomainID.BIOTECH: [
        "semantic_scholar",   # Primary: papers + citations
        "event_registry",     # Secondary: full-body news + PR
        "newsdata",           # Tertiary
        "tavily",
    ],
    DomainID.SCIENCE: [
        "arxiv",              # Primary
        "semantic_scholar",   # Secondary
        "event_registry",     # Tertiary: full-body news
        "rss",
    ],
    DomainID.SUSTAINABILITY: [
        "event_registry",     # Primary: concept-filtered
        "gnews",              # Secondary
        "newsdata",           # Tertiary
        "rss",
    ],
    DomainID.OSS: [
        "github_trending",    # Primary
        "hackernews",         # Secondary
        "event_registry",     # Tertiary: news about open source
        "rss",
    ],
    DomainID.FINANCE: [
        "event_registry",     # Primary: concept-filtered, full body
        "newsdata",           # Secondary
        "gnews",              # Tertiary
        "rss",
    ],
    DomainID.CRYPTO: [
        "event_registry",     # Primary: concept-filtered
        "newsdata",           # Secondary
        "gnews",              # Tertiary
        "rss",
    ],
    DomainID.HEALTH: [
        "event_registry",     # Primary: concept-filtered
        "newsdata",           # Secondary
        "gnews",              # Tertiary
        "rss",
    ],
    DomainID.SPORTS: [
        "event_registry",     # Primary: concept-filtered
        "newsdata",           # Secondary
        "gnews",              # Tertiary
        "rss",
    ],
    DomainID.ENTERTAINMENT: [
        "event_registry",     # Primary: concept-filtered
        "newsdata",           # Secondary
        "gnews",              # Tertiary
        "rss",
    ],
    DomainID.EDUCATION: [
        "event_registry",     # Primary: concept-filtered
        "tavily",             # Secondary
        "gnews",              # Tertiary
        "rss",
    ],
    DomainID.STARTUPS: [
        "event_registry",     # Primary: concept-filtered + PR data type
        "hackernews",         # Secondary: community signal
        "tavily",             # Tertiary
        "rss",
    ],
    DomainID.CYBERSECURITY: [
        "event_registry",     # Primary: concept-filtered
        "hackernews",         # Secondary: community signal
        "newsdata",           # Tertiary
        "rss",
    ],
}

# Default domain-specific queries
DOMAIN_DEFAULT_QUERIES: dict[str, list[str]] = {
    DomainID.AI_ML: [
        "latest artificial intelligence research",
        "new machine learning models",
        "LLM breakthroughs",
    ],
    DomainID.TECH: [
        "technology news today",
        "software releases",
        "startup launches",
    ],
    DomainID.ECON: [
        "economic policy news",
        "financial markets today",
    ],
    DomainID.POLITICS: [
        "political news today",
        "policy and regulation",
    ],
    DomainID.BIOTECH: [
        "biotechnology research",
        "drug trials clinical",
    ],
    DomainID.SCIENCE: [
        "scientific discoveries",
        "space exploration news",
    ],
    DomainID.SUSTAINABILITY: [
        "climate change policy",
        "renewable energy news",
    ],
    DomainID.OSS: [
        "trending open source projects",
        "new developer tools",
    ],
    DomainID.FINANCE: [
        "stock market news today",
        "investment and banking news",
    ],
    DomainID.CRYPTO: [
        "cryptocurrency news today",
        "bitcoin ethereum blockchain",
    ],
    DomainID.HEALTH: [
        "health and wellness news",
        "medical news today",
    ],
    DomainID.SPORTS: [
        "sports news today",
        "latest game results and highlights",
    ],
    DomainID.ENTERTAINMENT: [
        "entertainment news today",
        "movie music streaming news",
    ],
    DomainID.EDUCATION: [
        "education news today",
        "higher education EdTech",
    ],
    DomainID.STARTUPS: [
        "startup funding news",
        "new startup launches today",
    ],
    DomainID.CYBERSECURITY: [
        "cybersecurity news today",
        "data breach vulnerability news",
    ],
}
