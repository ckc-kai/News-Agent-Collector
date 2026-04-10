"""EventRegistry domain-to-concept mapping.

Maps each DomainID to EventRegistry filter parameters:
  - conceptUris: Wikipedia URIs for precise topic filtering
  - categoryUri: EventRegistry category URI (optional)
  - keywords: fallback keyword list for domains without a clean concept URI
  - dataType: which EventRegistry data types to include
"""

from src.app.core.constants import DomainID

# Each value is a dict with optional keys:
#   conceptUris: list[str]   — Wikipedia URIs; used when available
#   categoryUri: str         — EventRegistry category URI
#   keywords: list[str]      — fallback for domains without good concept URIs
#   dataType: list[str]      — "news", "pr", "blog" (default: ["news"])
DOMAIN_CONCEPTS: dict[str, dict] = {
    DomainID.AI_ML: {
        "conceptUris": [
            "http://en.wikipedia.org/wiki/Artificial_intelligence",
            "http://en.wikipedia.org/wiki/Machine_learning",
            "http://en.wikipedia.org/wiki/Large_language_model",
        ],
        "keywords": ["artificial intelligence", "machine learning", "LLM", "deep learning"],
        "dataType": ["news", "pr"],
    },
    DomainID.TECH: {
        "conceptUris": [
            "http://en.wikipedia.org/wiki/Technology",
            "http://en.wikipedia.org/wiki/Information_technology",
        ],
        "categoryUri": "dmoz/Computers",
        "keywords": ["technology news", "software", "startup", "cloud computing"],
        "dataType": ["news"],
    },
    DomainID.ECON: {
        "conceptUris": [
            "http://en.wikipedia.org/wiki/Economics",
            "http://en.wikipedia.org/wiki/Macroeconomics",
        ],
        "categoryUri": "dmoz/Business/Economy",
        "keywords": ["economy", "inflation", "interest rates", "GDP", "Federal Reserve"],
        "dataType": ["news"],
    },
    DomainID.POLITICS: {
        "conceptUris": [
            "http://en.wikipedia.org/wiki/Politics",
            "http://en.wikipedia.org/wiki/Political_science",
        ],
        "categoryUri": "dmoz/Society/Politics",
        "keywords": ["politics", "election", "legislation", "government policy", "geopolitics"],
        "dataType": ["news"],
    },
    DomainID.BIOTECH: {
        "conceptUris": [
            "http://en.wikipedia.org/wiki/Biotechnology",
            "http://en.wikipedia.org/wiki/Pharmaceutical_industry",
        ],
        "keywords": ["biotechnology", "drug trial", "genomics", "CRISPR", "pharmaceutical"],
        "dataType": ["news", "pr"],
    },
    DomainID.SCIENCE: {
        "conceptUris": [
            "http://en.wikipedia.org/wiki/Science",
            "http://en.wikipedia.org/wiki/Scientific_research",
        ],
        "categoryUri": "dmoz/Science",
        "keywords": ["scientific discovery", "space exploration", "physics", "astronomy"],
        "dataType": ["news"],
    },
    DomainID.SUSTAINABILITY: {
        "conceptUris": [
            "http://en.wikipedia.org/wiki/Sustainability",
            "http://en.wikipedia.org/wiki/Climate_change",
            "http://en.wikipedia.org/wiki/Renewable_energy",
        ],
        "keywords": ["climate change", "renewable energy", "sustainability", "ESG", "net zero"],
        "dataType": ["news"],
    },
    DomainID.OSS: {
        "conceptUris": [
            "http://en.wikipedia.org/wiki/Open-source_software",
            "http://en.wikipedia.org/wiki/GitHub",
        ],
        "keywords": ["open source software", "developer tools", "GitHub", "open source project"],
        "dataType": ["news", "pr"],
    },
    DomainID.FINANCE: {
        "conceptUris": [
            "http://en.wikipedia.org/wiki/Finance",
            "http://en.wikipedia.org/wiki/Stock_market",
        ],
        "categoryUri": "dmoz/Business/Investing",
        "keywords": ["stock market", "investment", "Wall Street", "IPO", "earnings report"],
        "dataType": ["news"],
    },
    DomainID.CRYPTO: {
        "conceptUris": [
            "http://en.wikipedia.org/wiki/Cryptocurrency",
            "http://en.wikipedia.org/wiki/Bitcoin",
            "http://en.wikipedia.org/wiki/Blockchain",
        ],
        "keywords": ["cryptocurrency", "bitcoin", "ethereum", "blockchain", "DeFi"],
        "dataType": ["news", "pr"],
    },
    DomainID.HEALTH: {
        "conceptUris": [
            "http://en.wikipedia.org/wiki/Health",
            "http://en.wikipedia.org/wiki/Public_health",
        ],
        "categoryUri": "dmoz/Health",
        "keywords": ["health news", "medical news", "wellness", "healthcare", "disease"],
        "dataType": ["news"],
    },
    DomainID.SPORTS: {
        "conceptUris": [
            "http://en.wikipedia.org/wiki/Sport",
            "http://en.wikipedia.org/wiki/Athletics_(sport)",
        ],
        "categoryUri": "dmoz/Sports",
        "keywords": ["sports news", "NBA", "NFL", "FIFA", "Olympic Games"],
        "dataType": ["news"],
    },
    DomainID.ENTERTAINMENT: {
        "conceptUris": [
            "http://en.wikipedia.org/wiki/Entertainment",
            "http://en.wikipedia.org/wiki/Film_industry",
        ],
        "categoryUri": "dmoz/Arts/Movies",
        "keywords": ["entertainment news", "movies", "music", "streaming", "celebrity"],
        "dataType": ["news"],
    },
    DomainID.EDUCATION: {
        "conceptUris": [
            "http://en.wikipedia.org/wiki/Education",
            "http://en.wikipedia.org/wiki/Higher_education",
        ],
        "categoryUri": "dmoz/Reference/Education",
        "keywords": ["education news", "university", "EdTech", "online learning", "school"],
        "dataType": ["news"],
    },
    DomainID.STARTUPS: {
        "conceptUris": [
            "http://en.wikipedia.org/wiki/Startup_company",
            "http://en.wikipedia.org/wiki/Venture_capital",
        ],
        "keywords": ["startup funding", "venture capital", "Series A", "Y Combinator", "unicorn"],
        "dataType": ["news", "pr"],
    },
    DomainID.CYBERSECURITY: {
        "conceptUris": [
            "http://en.wikipedia.org/wiki/Computer_security",
            "http://en.wikipedia.org/wiki/Cybercrime",
        ],
        "keywords": ["cybersecurity", "data breach", "ransomware", "hacking", "zero-day vulnerability"],
        "dataType": ["news"],
    },
}
