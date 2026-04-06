from enum import StrEnum


class DomainID(StrEnum):
    AI_ML = "ai_ml"
    TECH = "tech"
    ECON = "econ"
    POLITICS = "politics"
    BIOTECH = "biotech"
    SCIENCE = "science"
    SUSTAINABILITY = "sustainability"
    OSS = "oss"


class MediaType(StrEnum):
    ARTICLE = "article"
    PAPER = "paper"
    POST = "post"
    THREAD = "thread"
    REPO = "repo"


class DepthLevel(StrEnum):
    L1 = "L1"  # Headline: ≤ 15 words
    L2 = "L2"  # Summary: 3-5 sentences
    L3 = "L3"  # Deep Dive: 2-3 paragraphs


class FeedbackType(StrEnum):
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    STAR_RATING = "star_rating"
    MORE_LIKE_THIS = "more_like_this"
    LESS_OF_THIS = "less_of_this"
    NOT_RELEVANT = "not_relevant"
    TOO_TECHNICAL = "too_technical"
    TOO_BASIC = "too_basic"
    NEVER_SHOW_DOMAIN = "never_show_domain"


class DeliveryFrequency(StrEnum):
    DAILY = "daily"
    TWICE_WEEKLY = "twice_weekly"
    WEEKLY = "weekly"


class DeliveryChannel(StrEnum):
    IN_APP = "in_app"
    EMAIL = "email"
    BOTH = "both"


# Domain taxonomy with keywords for classification
DOMAIN_KEYWORDS: dict[str, list[str]] = {
    DomainID.AI_ML: [
        "artificial intelligence", "machine learning", "deep learning", "neural network",
        "LLM", "large language model", "GPT", "transformer", "NLP",
        "natural language processing", "computer vision", "reinforcement learning",
        "generative AI", "diffusion model", "fine-tuning", "training data",
        "benchmark", "BERT", "attention mechanism", "embedding",
    ],
    DomainID.TECH: [
        "software", "startup", "app", "cloud computing", "SaaS",
        "cybersecurity", "data breach", "smartphone", "chip", "semiconductor",
        "5G", "quantum computing", "blockchain", "cryptocurrency", "product launch",
        "tech company", "Apple", "Google", "Microsoft", "Amazon",
    ],
    DomainID.ECON: [
        "economy", "inflation", "interest rate", "GDP", "federal reserve",
        "stock market", "fiscal policy", "monetary policy", "trade",
        "tariff", "recession", "unemployment", "central bank", "bond",
        "commodity", "oil price", "housing market", "debt", "deficit",
    ],
    DomainID.POLITICS: [
        "election", "congress", "senate", "legislation", "regulation",
        "geopolitics", "diplomacy", "sanction", "NATO", "United Nations",
        "foreign policy", "democracy", "political party", "vote",
        "government", "policy", "executive order", "campaign",
    ],
    DomainID.BIOTECH: [
        "biotech", "biotechnology", "drug trial", "clinical trial", "FDA",
        "genomics", "CRISPR", "gene therapy", "vaccine", "pharmaceutical",
        "protein", "cell therapy", "biomarker", "oncology", "immunotherapy",
        "public health", "epidemiology", "WHO", "pandemic",
    ],
    DomainID.SCIENCE: [
        "physics", "chemistry", "biology", "astronomy", "space",
        "NASA", "climate change", "evolution", "particle", "quantum",
        "telescope", "mars", "exoplanet", "fossil", "geology",
        "neuroscience", "mathematics", "experiment", "discovery",
    ],
    DomainID.SUSTAINABILITY: [
        "sustainability", "climate policy", "clean energy", "renewable",
        "solar", "wind power", "carbon", "emission", "ESG",
        "electric vehicle", "EV", "green", "recycling", "biodiversity",
        "conservation", "deforestation", "net zero", "Paris agreement",
    ],
    DomainID.OSS: [
        "open source", "GitHub", "repository", "framework", "library",
        "developer tool", "API", "SDK", "release", "pull request",
        "contribution", "MIT license", "Apache", "Linux", "Rust",
        "Python", "JavaScript", "TypeScript", "Go", "Kubernetes",
    ],
}
