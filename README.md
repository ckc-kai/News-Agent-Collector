# News Agent Collector

A personalized news discovery system that aggregates articles from dozens of sources, scores them against your interests, and delivers a daily digest to your inbox — automatically, every morning, on device boot.

No dashboards to check. No feeds to scroll. One email, every day, with only what matters to you.

---

## How It Works

```
Boot
 └─ launchd (macOS) triggers launch.sh
     ├─ Docker Compose starts Postgres + Redis
     ├─ Uvicorn starts the FastAPI app
     ├─ POST /api/v1/deliver
     │    ├─ OpenTracker pulls email click events from Cloudflare Worker
     │    │    └─ Each clicked article → domain weight +0.01
     │    ├─ Aggregation fetches fresh articles from all enabled sources
     │    ├─ Pipeline: normalise → deduplicate → classify → summarise
     │    ├─ Recommendation engine scores and ranks articles
     │    ├─ Digest built and rendered as HTML email
     │    └─ Email sent via Resend API
     └─ Uvicorn shuts down (no process left running all day)

Email
 └─ Article links → Cloudflare Worker /click/{id}?url=…
     ├─ Click event logged to KV (7-day TTL)
     └─ Browser redirected to real article URL

Next Boot
 └─ OpenTracker reads yesterday's clicks → bumps domain weights
     └─ Today's digest reflects what you actually engaged with
```

---

## Features

- **Daily auto-delivery** — boots silently at login, sends the email, shuts down. Zero manual steps.
- **Email click tracking** — article links in the email redirect through a Cloudflare Worker. Each click adjusts your domain interest weights so future digests improve.
- **Multi-source aggregation** — EventRegistry, Tavily, GNews, Newsdata, arXiv, Semantic Scholar, Hacker News, GitHub Trending, and RSS feeds.
- **Two-level summarisation** — brief summary (L1) and deeper analysis (L2) per article, using Groq (Llama 3.3 70B).
- **Interest-aware scoring** — domain weights, freshness, source diversity, and an exploration rate that surfaces adjacent topics.
- **Depth levels** — Headline, Summary, or Deep Dive per topic.
- **Idempotent delivery** — one email per day, enforced at the database level. Boot the machine twice, get one email.
- **Graceful error recovery** — failed delivery leaves the server running so you can debug; successful delivery shuts it down cleanly.

---

## Getting Started

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.12 | spaCy does not support 3.13 |
| [uv](https://docs.astral.sh/uv/) | any | Fast Python package manager |
| Docker Desktop | any | Runs Postgres + Redis |
| Node.js | 18+ | Only needed for deploying the Cloudflare Worker |

### 1. Clone and install

```bash
# Clone into ~/code — do NOT use ~/Desktop (macOS TCC blocks launchd there)
git clone <repo-url> ~/code/News-Agent-Collector
cd ~/code/News-Agent-Collector

# Create venv — must be Python 3.12
uv venv --python 3.12
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — fill in all keys (see API Keys section below)
```

### 3. Start the database

```bash
docker compose up -d
```

### 4. Run database migrations

```bash
alembic upgrade head
```

### 5. Run the app

```bash
uvicorn src.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open `http://localhost:8000` to complete onboarding (set your name, interests, and depth preferences).

### 6. Trigger a delivery (optional manual test)

```bash
curl -X POST http://localhost:8000/api/v1/deliver
```

---

## Auto-Boot Setup (macOS)

The system runs automatically at login via `launchd`. After setting up the app, install the boot script:

### Install the plist

```bash
# Copy the plist to LaunchAgents
cp scripts/com.newsagent.plist ~/Library/LaunchAgents/

# Load it (activates immediately and on all future logins)
launchctl load ~/Library/LaunchAgents/com.newsagent.plist
```

### Verify it's running

```bash
# Check launchd loaded it
launchctl list | grep newsagent

# Watch the boot log live
tail -f ~/Library/Logs/NewsAgent/launch.err

# Check uvicorn output
tail -f ~/Library/Logs/NewsAgent/uvicorn.log
```

### Boot sequence

1. Waits for Docker daemon (up to 60s)
2. Starts `docker compose up -d` (idempotent)
3. Waits for Postgres to accept connections
4. Kills any stale process on port 8000
5. Starts uvicorn with `nohup` + `disown`
6. Waits for `/api/v1/health` to return 200
7. `POST /api/v1/deliver` — aggregates, builds, and sends the digest
8. Shuts down uvicorn if delivery returned `sent` or `skipped`
9. Leaves uvicorn running if delivery returned an error (for debugging)

### Unload

```bash
launchctl unload ~/Library/LaunchAgents/com.newsagent.plist
```

---

## Cloudflare Worker (Click Tracking)

Article links in the email go through a Cloudflare Worker that logs each click to KV storage, then redirects to the real URL. On next boot, OpenTracker reads those events and bumps the domain weights.

### Deploy the Worker (one-time setup)

```bash
cd workers/newsagent-tracker

# Log in to Cloudflare
npx wrangler login

# Edit wrangler.toml — set your account_id
# Create a KV namespace and set its ID in wrangler.toml:
npx wrangler kv namespace create EVENTS_KV

# Deploy
npx wrangler deploy

# Set the auth secret (used by OpenTracker to fetch events)
echo "your-random-secret" | npx wrangler secret put API_SECRET
```

Then set the matching values in `.env`:

```env
CLOUDFLARE_WORKER_URL=https://newsagent-tracker.YOUR_SUBDOMAIN.workers.dev
CLOUDFLARE_WORKER_SECRET=your-random-secret
```

### Worker endpoints

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `GET /click/{article_id}?url={encoded}` | None | Log click → redirect to article |
| `GET /events?since={YYYY-MM-DD}` | Bearer token | Return click events for date range |

### Weight increments

| Signal | Increment | Why |
|--------|-----------|-----|
| In-app UI click | `+0.02` | Strong — deliberate in-app action |
| Email link click | `+0.01` | Weaker — passive engagement |

---

## API Keys

Copy `.env.example` to `.env` and fill in these keys:

| Key | Required | Source |
|-----|----------|--------|
| `EVENT_REGISTRY_API_KEY` | Recommended | [newsapi.ai](https://newsapi.ai) — free tier, 2000 req/day |
| `GROQ_API_KEY` | Yes | [groq.com](https://groq.com) — free tier |
| `RESEND_API_KEY` | Yes | [resend.com](https://resend.com) — free tier |
| `DELIVERY_EMAIL_TO` | Yes | Your email address (free Resend tier: must be your account email) |
| `CLOUDFLARE_WORKER_URL` | Optional | URL of your deployed Worker |
| `CLOUDFLARE_WORKER_SECRET` | Optional | Must match the `API_SECRET` wrangler secret |
| `TAVILY_API_KEY` | Optional | [tavily.com](https://tavily.com) — 15 req/day free |
| `GNEWS_API_KEY` | Optional | [gnews.io](https://gnews.io) |
| `NEWSDATA_API_KEY` | Optional | [newsdata.io](https://newsdata.io) |
| `GITHUB_TOKEN` | Optional | GitHub PAT for GitHub Trending source |
| `SEMANTIC_SCHOLAR_API_KEY` | Optional | [semanticscholar.org](https://api.semanticscholar.org/) |

The system works with whatever keys you provide and skips sources with missing keys.

### Resend free tier note

Without a verified sending domain, Resend only allows sending **to** the email address registered on your Resend account. To send to any address, verify a domain at [resend.com/domains](https://resend.com/domains).

---

## Architecture

```
src/app/
├── api/
│   ├── router.py                    # Route registration
│   └── v1/
│       ├── deliver.py               # POST /deliver — triggers daily digest
│       ├── health.py                # GET /health
│       ├── articles.py              # Article CRUD
│       ├── digest.py                # Digest retrieval
│       ├── feedback.py              # User feedback (click, dismiss, save)
│       ├── tracking.py              # In-app click tracking
│       ├── preferences.py           # Interest/depth preferences
│       ├── search.py                # Article search
│       ├── topics.py                # Topic management
│       └── users.py                 # User management
│
├── services/
│   ├── aggregation.py               # Fetches articles from all enabled sources
│   ├── delivery.py                  # Idempotent email delivery via Resend
│   ├── email_renderer.py            # HTML + plain-text email rendering
│   ├── open_tracker.py              # Pulls email click events from Cloudflare Worker
│   └── topic_expander.py            # Expands topic queries using LLM
│
├── sources/
│   ├── registry.py                  # Source discovery and routing
│   ├── query_strategy.py            # Per-source query building
│   ├── base.py                      # BaseSource interface
│   └── adapters/
│       ├── event_registry.py        # newsapi.ai (primary news source)
│       ├── event_registry_concepts.py
│       ├── tavily.py
│       ├── gnews.py
│       ├── newsdata.py
│       ├── arxiv_source.py
│       ├── semantic_scholar.py
│       ├── hackernews.py
│       ├── github_trending.py
│       └── rss.py
│
├── pipeline/
│   ├── orchestrator.py              # Runs all stages in sequence
│   └── stages/
│       ├── normalizer.py            # Standardise article format
│       ├── deduplicator.py          # Remove near-duplicate articles
│       ├── classifier.py            # Topic classification
│       ├── enricher.py              # Add metadata
│       └── summarizer.py            # Two-level summarisation (Groq)
│
├── recommendation/
│   ├── engine.py                    # Main scoring and ranking
│   ├── scorer.py                    # Per-signal scoring
│   ├── diversity.py                 # Source and topic diversity
│   └── strategies/
│       └── content_based.py
│
├── models/
│   ├── article.py
│   ├── user.py
│   ├── digest.py
│   ├── feedback.py
│   ├── delivery.py                  # DeliveryLog — one record per sent email
│   └── source_health.py
│
├── db/
│   ├── session.py                   # Async SQLAlchemy engine
│   └── repositories/
│       ├── article.py
│       ├── digest.py
│       ├── feedback.py
│       └── user.py
│
├── config.py                        # pydantic-settings (reads .env)
├── main.py                          # FastAPI app + lifespan
├── frontend.py                      # Jinja2 UI routes
└── dependencies.py                  # Shared FastAPI dependencies

workers/newsagent-tracker/
├── src/index.js                     # Cloudflare Worker — click relay + events API
└── wrangler.toml                    # Worker config (KV binding, account ID)

scripts/
├── launch.sh                        # Boot script — run by launchd
└── com.newsagent.plist              # launchd job definition

alembic/
└── versions/                        # Database migrations

tests/
└── unit/                            # pytest unit tests
```

---

## Development

### Run tests

```bash
pytest tests/
```

### Run with coverage

```bash
pytest tests/ --cov=src --cov-report=term-missing
```

### Database migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply pending migrations
alembic upgrade head

# Roll back one step
alembic downgrade -1
```

### Manually trigger the boot script (outside launchd)

```bash
PROJECT_DIR=~/code/News-Agent-Collector bash scripts/launch.sh
```

---

## Supported News Domains

AI/ML · Technology · Economics · Politics · Biotech · General Science · Sustainability · Open Source

Interests are set during onboarding and updated continuously based on your clicks and explicit feedback.

---

## License

TBD
