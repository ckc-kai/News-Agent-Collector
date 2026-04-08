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
        "hackernews",         # Tertiary: community signal
        "tavily",             # Fallback
        "rss",
    ],
    DomainID.TECH: [
        "hackernews",         # Primary
        "newsapi",            # Secondary
        "github_trending",    # Tertiary
        "rss",                # Fallback
        "gnews",
    ],
    DomainID.ECON: [
        "newsapi",            # Primary
        "gnews",              # Secondary
        "newsdata",           # Tertiary
        "rss",                # Fallback
    ],
    DomainID.POLITICS: [
        "newsapi",            # Primary
        "newsdata",           # Secondary
        "gnews",              # Tertiary
        "rss",                # Fallback
    ],
    DomainID.BIOTECH: [
        "semantic_scholar",   # Primary: papers + citations
        "newsapi",            # Secondary
        "newsdata",           # Tertiary
        "tavily",             # Fallback
    ],
    DomainID.SCIENCE: [
        "arxiv",              # Primary
        "semantic_scholar",   # Secondary
        "newsapi",            # Tertiary
        "rss",                # Fallback
    ],
    DomainID.SUSTAINABILITY: [
        "newsapi",            # Primary
        "gnews",              # Secondary
        "newsdata",           # Tertiary
        "rss",                # Fallback
    ],
    DomainID.OSS: [
        "github_trending",    # Primary
        "hackernews",         # Secondary
        "rss",                # Tertiary
    ],
    DomainID.FINANCE: [
        "newsdata",
        "gnews",
        "tavily",
        "rss",
    ],
    DomainID.CRYPTO: [
        "newsdata",
        "gnews",
        "tavily",
        "rss",
    ],
    DomainID.HEALTH: [
        "newsdata",
        "gnews",
        "tavily",
        "rss",
    ],
    DomainID.SPORTS: [
        "newsdata",
        "gnews",
        "rss",
    ],
    DomainID.ENTERTAINMENT: [
        "newsdata",
        "gnews",
        "rss",
    ],
    DomainID.EDUCATION: [
        "tavily",
        "gnews",
        "rss",
    ],
    DomainID.STARTUPS: [
        "hackernews",
        "tavily",
        "gnews",
        "rss",
    ],
    DomainID.CYBERSECURITY: [
        "hackernews",
        "tavily",
        "newsdata",
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
