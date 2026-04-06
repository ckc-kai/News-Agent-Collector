from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # --- Application ---
    app_name: str = "News Agent Collector"
    debug: bool = False

    # --- Database ---
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/news_agent"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/news_agent"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- News & Search APIs ---
    tavily_api_key: str = ""
    newsapi_api_key: str = ""
    gnews_api_key: str = ""
    newsdata_api_key: str = ""

    # --- LLM / Summarization ---
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # --- Social Platforms ---
    github_token: str = ""

    # --- Academic ---
    semantic_scholar_api_key: str = ""

    # --- Rate Limits (per day, from PRD) ---
    tavily_daily_limit: int = 15
    newsapi_daily_limit: int = 100
    gnews_daily_limit: int = 100
    newsdata_daily_limit: int = 200
    arxiv_daily_limit: int = 100
    semantic_scholar_daily_limit: int = 5000
    github_daily_limit: int = 480  # 20/hr * 24
    hackernews_daily_limit: int = 1000  # effectively unlimited

    # --- Recommendation Weights (PRD Section 10.5) ---
    weight_content: float = 0.45
    weight_freshness: float = 0.20
    weight_source_diversity: float = 0.10
    weight_exploration: float = 0.15
    weight_importance: float = 0.10

    # --- Digest Defaults ---
    digest_max_items: int = 10
    digest_max_domain_pct: float = 0.40
    digest_max_source_pct: float = 0.30
    default_exploration_rate: float = 0.15
    min_exploration_rate: float = 0.05

    # --- Feature Flags ---
    enable_lda_classification: bool = False
    enable_drift_notification: bool = True

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
