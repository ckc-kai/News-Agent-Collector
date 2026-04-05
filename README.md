# News Agent Collector — Discovery Feed

A personalized news discovery system that finds, summarizes, and delivers articles tailored to your interests across multiple domains.

Instead of checking dozens of websites, this system watches them for you — then sends you a daily digest with only the stuff that matters to you.

> **Status**: Early development. Features and structure will evolve.

---

## What It Does

- **Aggregates** news and articles from multiple sources (news APIs, academic databases, community forums, RSS feeds)
- **Processes** content through a pipeline — removes duplicates, classifies topics, and generates summaries at different depth levels
- **Learns** what you care about through onboarding preferences and ongoing feedback
- **Delivers** a personalized daily digest, mixing your core interests with occasional discoveries to keep things fresh

### Depth Levels

Not everything needs the same level of detail. You can set per-topic depth:

| Level | What You Get | Best For |
|-------|-------------|----------|
| Headline | One-line summary | Quick scanning |
| Summary | 3-5 sentence overview | Daily reading |
| Deep Dive | Full analysis with key findings | Topics you care most about |

---

## Supported Domains

AI/ML, Technology, Economics, Politics, Biotech, General Science, Sustainability, Open Source — with more to come.

---

## Getting Started

### Prerequisites

- Python 3.12
- PostgreSQL
- Redis
- [uv](https://docs.astral.sh/uv/) (Python package manager)

### Setup

```bash
# Clone the repo
git clone <repo-url>
cd News-Agent-Collector

# Create and activate virtual environment
uv venv --python 3.12 news
source news/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your keys (see API Keys section below)
```

### API Keys

The system uses free-tier APIs. You'll need to sign up for keys at:

| Service | What It's For | Sign Up |
|---------|--------------|---------|
| Tavily | Web search | tavily.com |
| NewsAPI | News articles | newsapi.org |
| GNews | News articles | gnews.io |
| Groq | AI summarization | groq.com |

More sources are optional — the system works with whatever keys you provide and skips the rest.

---

## Architecture (High Level)

```
Sources (APIs, RSS, etc.)
    → Content Pipeline (clean, deduplicate, classify, summarize)
        → Recommendation Engine (match content to your interests)
            → Daily Digest
                → Your Feedback → Engine gets smarter
```

Each layer is modular. New sources, processors, or delivery methods can be added independently.

---

## Project Structure

```
News-Agent-Collector/
├── product_description/   # PRD and planning docs
├── requirements.txt       # Pinned dependencies (Python 3.12)
├── .env                   # Your API keys (not committed to git)
└── README.md
```

> Project structure will expand as development progresses.

---

## Roadmap

- [x] Project setup, dependency management
- [ ] Source adapters (Tavily, NewsAPI, arxiv, Hacker News, RSS)
- [ ] Content processing pipeline
- [ ] User onboarding and preference system
- [ ] Recommendation engine
- [ ] Feedback loop
- [ ] Daily digest delivery
- [ ] Social platform connectors

See `product_description/PRD_v1.md` for the full plan.

---

## Contributing

This project is in early development. Contribution guidelines will be added once the core structure is in place.

---

## License

TBD
