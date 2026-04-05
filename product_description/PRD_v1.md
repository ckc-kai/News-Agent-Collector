# Product Requirements Document (PRD)

## Personalized News Discovery & Recommendation Module — "Discovery Feed"

| Field             | Detail                                                                                                                                                                                                                                            |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Author**        | Product Team                                                                                                                                                                                                                                      |
| **Version**       | 2.0 (Consolidated — Cross-Team Review)                                                                                                                                                                                                            |
| **Status**        | Draft — Open for Review                                                                                                                                                                                                                           |
| **Created**       | April 2026                                                                                                                                                                                                                                        |
| **Last Updated**  | April 2026                                                                                                                                                                                                                                        |
| **Parent Module** | Research Module (existing, Tavily-powered, stock-focused)                                                                                                                                                                                         |
| **Change Log**    | v2.0: Consolidated inputs from 4 independent PRD drafts. Added per-topic depth, static/dynamic interest modeling, sample-article onboarding, open-source search alternatives, noise filtering, tech stack specifics, and expanded future roadmap. |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Goals & Success Metrics](#3-goals--success-metrics)
4. [User Personas & Stories](#4-user-personas--stories)
5. [Scope Definition](#5-scope-definition)
6. [System Architecture Overview](#6-system-architecture-overview)
7. [Functional Requirements](#7-functional-requirements)
   - 7.1 Multi-Source Aggregation Engine
   - 7.2 Content Processing Pipeline
   - 7.3 User Preference & Onboarding System
   - 7.4 Recommendation Engine (ML-Powered)
   - 7.5 Feedback Loop System
   - 7.6 Delivery & Notification System
   - 7.7 Social Platform Connector (Experimental)
   - 7.8 Research Module Integration
8. [Non-Functional Requirements](#8-non-functional-requirements)
9. [Data Sources & API Strategy](#9-data-sources--api-strategy)
10. [Recommendation Algorithm Design](#10-recommendation-algorithm-design)
11. [Social Platform Integration Strategy](#11-social-platform-integration-strategy)
12. [Extensibility & Plugin Architecture](#12-extensibility--plugin-architecture)
13. [Wireframes & User Flows](#13-wireframes--user-flows)
14. [Recommended Tech Stack](#14-recommended-tech-stack)
15. [Technical Constraints & Risks](#15-technical-constraints--risks)
16. [Phased Rollout Plan](#16-phased-rollout-plan)
17. [Appendix](#17-appendix)

---

## 1. Executive Summary

The **Discovery Feed** module extends the existing Research Module (stock-focused, Tavily-only) into a general-purpose, personalized news discovery system. It aggregates content from multiple free APIs and web sources across diverse domains—AI/ML research, technology, economics, politics, biotech, sustainability, and more—then uses an adaptive recommendation engine to deliver a tailored daily digest to each user.

The core innovation lies in solving four problems simultaneously:

1. **Discovery Overload** — Users don't know _where_ to look or _what_ to search for in unfamiliar domains.
2. **Depth Calibration** — Not every user needs research-paper depth; some need executive summaries, others want links to full papers. Critically, **depth preference varies per topic**: a user may want deep dives on AI but only headlines on politics.
3. **Preference Evolution** — User interests shift over time; the system must learn and adapt continuously through explicit and implicit feedback, while separating long-term stable interests from short-term curiosity.
4. **Filter Bubble & Fatigue** — Relentless same-topic content causes burnout; the system must proactively inject intellectually broadening content while defending against information cocoons.

This module is designed with a **plugin-first architecture** so new data sources, content processors, recommendation strategies, and delivery channels can be added without modifying core logic.

---

## 2. Problem Statement

### 2.1 Current State

The existing Research Module uses a single Tavily API integration to search for stock-market information. While effective within its narrow scope, it has the following limitations:

- **Single-domain focus**: Only covers stock/financial information.
- **Single-source dependency**: Relies entirely on Tavily, creating a single point of failure and limited diversity.
- **No personalization**: Every user receives the same type of results; there is no learning from user behavior.
- **No proactive discovery**: The user must initiate searches; the system never pushes relevant content.
- **No integration point**: Results found in a general search cannot be saved back to the Research module for further analysis.

### 2.2 User Pain Points

| Pain Point                           | Description                                                                                                                                                         |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **"I don't know what I don't know"** | A master's student in AI wants to stay current with breakthroughs but doesn't know which conferences, arxiv categories, or blogs to follow.                         |
| **Depth mismatch**                   | A user interested in biotech but not a domain expert doesn't want to read a 30-page paper—they want a 3-sentence summary with a "read more" option.                 |
| **Per-topic depth variance**         | The same user may want full technical depth on AI papers but only a TL;DR on economic policy. The system must support per-topic depth, not a single global setting. |
| **Content fatigue**                  | Receiving only tech news daily leads to burnout; users want intellectual breadth (economics, politics, science) but have no way to express this.                    |
| **Stale preferences**                | Initial interest in LLMs might evolve toward robotics after six months; the system must track this drift.                                                           |
| **Platform fragmentation**           | Valuable content lives on WeChat public accounts, RedNote, GitHub trending, Instagram infographics—not just traditional news APIs.                                  |

---

## 3. Goals & Success Metrics

### 3.1 Product Goals

| #   | Goal                            | Description                                                                                                                   |
| --- | ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| G1  | **Multi-domain coverage**       | Support ≥ 6 content domains at launch (AI/ML, Tech, Economics, Politics, Biotech, General Science, Sustainability).           |
| G2  | **Source diversity**            | Aggregate from ≥ 3 independent data sources/APIs to reduce single-source bias.                                                |
| G3  | **Adaptive personalization**    | The recommendation engine should measurably improve content relevance over 2 weeks of user interaction.                       |
| G4  | **Per-topic depth flexibility** | Every piece of content available at 3 depth levels; each user can set different depth preferences for different domains.      |
| G5  | **Zero cost at MVP**            | All APIs and data sources must have a usable free tier or be fully open-source.                                               |
| G6  | **Extensibility**               | Adding a new data source or delivery channel should require implementing a single interface/adapter, not modifying core code. |
| G7  | **Research Module integration** | Users can save any discovery item back to the existing Research module for further deep-dive analysis.                        |

### 3.2 Success Metrics (KPIs)

| Metric                         | Target (3-month)                                   | Measurement Method                   |
| ------------------------------ | -------------------------------------------------- | ------------------------------------ |
| Daily Active Digest Opens      | ≥ 60% of subscribed users                          | Open tracking / click tracking       |
| Content Relevance Score        | ≥ 3.5 / 5 average user rating                      | In-digest feedback widget            |
| Digest Open Frequency          | ≥ 3x/week for 70%+ of active users                 | User logs                            |
| Preference Prediction Accuracy | ≥ 70% (predicted interest vs. actual click)        | Offline A/B evaluation               |
| Source Diversity Index         | ≥ 0.6 Shannon entropy across sources per digest    | Automated log analysis               |
| Feedback Submission Rate       | ≥ 30% of digest recipients provide feedback weekly | Feedback system logs                 |
| Average Read Dwell Time        | ≥ 90 seconds per session                           | Frontend event tracking              |
| Negative Feedback Rate         | ≤ 5% of delivered items                            | Thumbs down / "not interested" ratio |
| 30-Day User Retention          | ≥ 40%                                              | Cohort analysis                      |
| Email Unsubscribe Rate         | < 5%                                               | Email service logs                   |

---

## 4. User Personas & Stories

### 4.1 Personas

#### Persona A — "The Curious Student" (Primary)

- **Name**: Kai
- **Profile**: Master's student in AI/CS.
- **Behavior**: Reads 2-3 papers/week, follows Twitter/X for ML news, browses Reddit r/MachineLearning.
- **Need**: Automated discovery of trending papers, new model releases, benchmark results—summarized at varying depth. Wants **deep dives on AI, but only summaries on economics and politics**.
- **Pain**: Misses important papers because they're published on arxiv categories they don't follow; doesn't have time to read everything.

#### Persona B — "The T-Shaped Professional" (Secondary)

- **Profile**: Software engineer, mid-career, intellectually curious.
- **Behavior**: Primarily reads tech news but feels trapped in a filter bubble.
- **Need**: Curated exposure to economics, biotech, geopolitics, and science—at a level understandable to a non-expert. Wants the equivalent of a smart friend who says "you should know about this."
- **Pain**: Tech-only feeds cause fatigue; wants breadth but doesn't want to configure 20 RSS feeds manually.

#### Persona C — "The Passive Consumer" (Tertiary)

- **Profile**: Business professional, limited time.
- **Behavior**: Scans headlines during commute, rarely clicks through.
- **Need**: Ultra-concise summaries (1-2 sentences), with the option to deep-dive only when something catches their eye.
- **Pain**: Long articles feel like a chore; wants a "TL;DR of the world" scannable in 60 seconds.

### 4.2 User Stories

| ID    | Story                                                                                                                                                      | Priority | Acceptance Criteria                                                                                                               |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------- |
| US-01 | As a **Curious Student**, I want the system to find and summarize the top AI/ML papers and news from this week so I don't miss important breakthroughs.    | P0       | Digest includes ≥ 5 AI/ML items sourced from ≥ 2 different providers; each item has a headline and a 3-sentence summary.          |
| US-02 | As a **T-Shaped Professional**, I want my daily digest to include topics _outside_ my primary interest area so I can broaden my knowledge without burnout. | P0       | At least 10-20% of digest items are from domains the user has not explicitly selected as primary interests ("exploration quota"). |
| US-03 | As a **new user**, I want a quick onboarding flow (including sample article ratings) so the system can start sending relevant content immediately.         | P0       | Onboarding collects domain preferences, per-topic depth, delivery frequency, and optional sample ratings in ≤ 2 minutes.          |
| US-04 | As a **returning user**, I want to rate/react to each digest item so the system learns what I actually like over time.                                     | P0       | Each item supports: thumbs up/down, "more like this"/"less of this", "never show this domain", and optional 1-5 star rating.      |
| US-05 | As a **Passive Consumer**, I want a "Headlines Only" mode that gives me 1-line summaries I can scan in 60 seconds.                                         | P1       | Digest has a compact mode toggled in settings; compact mode shows ≤ 15 words per item.                                            |
| US-06 | As a user, I want the system to detect that my interests have shifted (e.g., from NLP to Robotics) and adjust automatically.                               | P1       | Recommendation model detects interest drift within 2 weeks of behavioral change and surfaces a confirmation prompt.               |
| US-07 | As a user, I want to set **different depth levels per topic** (e.g., AI = Deep Dive, Politics = Headlines Only).                                           | P0       | Settings allow per-domain depth selection; digest renders each item at its domain-specific depth level.                           |
| US-08 | As a user, I want to discover content from social platforms (RedNote, GitHub trending, WeChat public accounts) that traditional news APIs miss.            | P2       | System includes ≥ 1 social/community source in aggregation pipeline.                                                              |
| US-09 | As a user, I want to control delivery frequency (daily, twice-weekly, weekly) and delivery time.                                                           | P1       | Settings page allows frequency and preferred delivery time selection.                                                             |
| US-10 | As a user who rated mostly biotech content highly for 2 weeks, I want to see the system's "understanding" of my preferences so I can correct it if wrong.  | P2       | A "My Interests" dashboard shows current inferred preference weights with manual override sliders.                                |
| US-11 | As a user, I want to **save interesting items back to the Research module** for deeper analysis alongside my stock research.                               | P1       | "Save to Research" button on each item persists it to the existing Research module's data store with metadata.                    |
| US-12 | As a user, I want to search any topic freely (not just stocks) and get diverse, multi-source results with optional AI summaries.                           | P0       | Unified search bar with filters (topic, date, source type); results from ≥ 2 sources, deduplicated and ranked.                    |

---

## 5. Scope Definition

### 5.1 In Scope (MVP — Phase 1)

- Multi-source news aggregation (Tavily + NewsAPI + RSS + arxiv + Hacker News)
- Content processing pipeline (deduplication, summarization at 3 depth levels)
- User onboarding (interest selection wizard with sample-article rating)
- **Per-topic depth preferences**
- Basic recommendation engine (content-based filtering + exploration)
- Explicit feedback collection (thumbs up/down, 1-5 rating, "never show domain X")
- Daily digest generation and delivery (in-app)
- "Save to Research" integration with existing module
- Unified search bar (multi-source, unrestricted)
- Admin/user preference dashboard

### 5.2 In Scope (Phase 2)

- Collaborative filtering (learn from similar users)
- Implicit feedback tracking (click-through, read time, scroll depth)
- Static vs. dynamic interest separation modeling
- Social platform connectors (GitHub Trending, Reddit, RSS-bridged platforms)
- Email / push notification delivery channels
- "Explain Like I'm 5" mode for cross-domain content
- Trend/burst detection for emerging topics

### 5.3 Out of Scope (Future Consideration)

- Real-time breaking news alerts
- Full social media platform API integrations requiring business verification
- Multi-language content translation
- Audio digest / personalized podcast (TTS)
- Community features (user-shared digests / "Packs")
- Export to Notion/Obsidian
- Knowledge graph construction from consumed content
- Paid API tiers

---

## 6. System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        DISCOVERY FEED MODULE                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────────────┐  │
│  │   Source     │   │   Content    │   │   Recommendation     │  │
│  │  Aggregation │──▶│  Processing  │──▶│      Engine           │  │
│  │   Layer      │   │   Pipeline   │   │                      │  │
│  └──────┬──────┘   └──────────────┘   └──────────┬───────────┘  │
│         │                                         │              │
│  ┌──────┴──────────────────────────┐   ┌─────────┴────────┐    │
│  │       Source Adapters           │   │  User Profile &   │    │
│  │  ┌───────┐ ┌───────┐ ┌──────┐  │   │  Feedback Store   │    │
│  │  │Tavily │ │NewsAPI│ │ RSS  │  │   └──────────────────┘    │
│  │  └───────┘ └───────┘ └──────┘  │              │              │
│  │  ┌───────┐ ┌───────┐ ┌──────┐  │   ┌─────────┴────────┐    │
│  │  │arxiv  │ │GitHub │ │SearX │  │   │  Digest Builder   │    │
│  │  └───────┘ └───────┘ └──────┘  │   │  & Delivery       │    │
│  └─────────────────────────────────┘   └────────┬─────────┘    │
│                                                  │              │
│                                        ┌─────────┴────────┐    │
│                                        │  Research Module  │    │
│                                        │  Bridge ("Save")  │    │
│                                        └──────────────────┘    │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│  Shared: Event Bus · Content Store · Config Mgr · Task Queue     │
└──────────────────────────────────────────────────────────────────┘
```

### Key Architectural Principles

1. **Adapter Pattern for Sources**: Each data source implements a `SourceAdapter` interface. Adding a new source = adding one adapter class. This also applies to open-source search alternatives (SearXNG, OrioSearch) as drop-in replacements for Tavily if needed.
2. **Pipeline Pattern for Processing**: Content goes through pluggable stages: `fetch → normalize → deduplicate → classify → enrich → summarize → store`.
3. **Strategy Pattern for Recommendations**: The recommendation algorithm is swappable. Start with content-based; swap to hybrid when collaborative data is sufficient.
4. **Event-Driven Feedback**: User interactions emit events consumed asynchronously by the recommendation engine—decoupling UI from ML.
5. **Research Module Bridge**: A lightweight adapter that maps Discovery Feed items to the Research module's data schema, enabling cross-module workflows.

---

## 7. Functional Requirements

### 7.1 Multi-Source Aggregation Engine

#### FR-1.1: Source Adapter Interface

Every data source must implement the following interface:

```
interface SourceAdapter {
    name: string                        // e.g., "tavily", "newsapi", "arxiv"
    supportedDomains: string[]          // e.g., ["ai", "tech", "general"]
    rateLimitPerDay: number             // free-tier constraint
    fetch(query: Query): RawArticle[]   // pull content
    healthCheck(): boolean              // is the source reachable?
}
```

**Rationale**: This enables adding/removing sources without touching aggregation logic. If a free API is deprecated, a new one appears, or funding arrives for a paid Bloomberg feed, only the adapter changes.

#### FR-1.2: Query Strategy

- For each content domain the user is subscribed to, the system generates **domain-specific queries** using a keyword/topic mapping table.
- Queries are distributed across sources to maximize diversity:
  - **Primary source**: Best source for that domain (e.g., arxiv for AI papers, PubMed for biotech).
  - **Secondary source**: Broader source for cross-validation (e.g., Tavily or NewsAPI).
  - **Exploration source**: A random or rotating source to discover unexpected content.
- The aggregator runs 3-5 parallel queries per topic and merges/reranks results.

#### FR-1.3: Rate Limit Manager

- Maintains a daily budget for each source's free tier.
- Distributes API calls across the day (staggered cron jobs) to avoid burst exhaustion.
- Falls back to cached content if all sources are exhausted.
- Supports **multi-key rotation** for APIs that allow multiple free-tier accounts.

| Source                | Free Tier Limit                   | Allocation Strategy                                                  |
| --------------------- | --------------------------------- | -------------------------------------------------------------------- |
| Tavily                | 1,000 searches/month (~33/day)    | Reserve 15/day for Discovery Feed; rest for existing Research module |
| NewsAPI               | 100 requests/day (dev plan)       | 50 for scheduled fetches; 50 for on-demand                           |
| GNews                 | 100 requests/day                  | 40 for digest; 60 for on-demand search                               |
| NewsData.io           | 200 credits/day                   | 100 for scheduled; 100 for search                                    |
| arxiv API             | No hard limit (polite usage)      | ≤ 100 requests/day with 3s delay between calls                       |
| Semantic Scholar      | 1,000 requests/5min (shared)      | Scheduled batches with backoff                                       |
| PubMed                | No hard limit (polite usage)      | ≤ 50 requests/day for biotech domain                                 |
| RSS Feeds             | Unlimited (self-hosted polling)   | Poll every 2-4 hours                                                 |
| GitHub API            | 60 req/hr (unauth) / 5,000 (auth) | 20 for trending; rest reserved                                       |
| Hacker News           | Unlimited (Firebase)              | Poll top/new/best every 2 hours                                      |
| SearXNG (self-hosted) | Unlimited                         | Fallback for Tavily when quota exhausted                             |

#### FR-1.4: Open-Source Search Alternative

To reduce Tavily dependency and provide unlimited fallback search, the system should support **SearXNG** (or OrioSearch) as a self-hosted meta-search engine. This aggregates 70+ search engines and has no rate limit when self-hosted.

- Deployed as a Docker container alongside the main application.
- Implements the same `SourceAdapter` interface.
- Used as: (a) fallback when Tavily quota is exhausted, (b) primary search for lower-priority domains, (c) social platform trend discovery via web queries like "trending on Xiaohongshu [topic]".

---

### 7.2 Content Processing Pipeline

#### FR-2.1: Normalization

All raw articles from different sources are converted to a unified schema:

```
interface NormalizedArticle {
    id: string                  // UUID
    sourceAdapter: string       // origin adapter name
    sourceUrl: string           // original URL
    title: string
    authors: string[]
    publishedAt: Date
    rawContent: string          // full text or abstract
    domain: string              // classified domain (primary)
    secondaryDomains: string[]  // articles can span multiple domains
    tags: string[]              // extracted keywords
    language: string            // ISO 639-1
    mediaType: "article" | "paper" | "post" | "thread" | "repo"
    importanceScore: number     // 0.0-1.0, computed during processing
}
```

#### FR-2.2: Deduplication

- **Title similarity**: Cosine similarity on TF-IDF vectors of titles; threshold ≥ 0.85 = duplicate.
- **URL canonicalization**: Strip tracking parameters, normalize domains.
- **Cross-source merge**: If the same story appears in multiple sources, merge metadata (keep all source URLs) but count as one item. Source diversity is tracked for ranking.

#### FR-2.3: Domain Classification

- Classify each article into one or more domains using a keyword-based classifier (Phase 1), upgradable to **LDA topic modeling** (Phase 1.5) or a lightweight ML classifier (Phase 2).
- **LDA approach** (from PRD3): Map articles to a low-dimensional topic probability distribution for interpretable interest modeling. Topics like "tech-artificial-intelligence" and "finance-macroeconomics" provide human-readable category labels that can be shown on the preference dashboard.
- Predefined domain taxonomy (extensible):

| Domain ID        | Label                        | Example Topics                                                      |
| ---------------- | ---------------------------- | ------------------------------------------------------------------- |
| `ai_ml`          | AI & Machine Learning        | LLMs, computer vision, reinforcement learning, new models           |
| `tech`           | Technology                   | Software releases, hardware, startups, product launches             |
| `econ`           | Economics & Finance          | Macro trends, policy, markets (complement to existing stock module) |
| `politics`       | Politics & Policy            | Regulation, elections, geopolitics                                  |
| `biotech`        | Biotech & Health             | Drug trials, genomics, public health                                |
| `science`        | General Science              | Physics, climate, space exploration                                 |
| `sustainability` | Environment & Sustainability | Climate policy, clean energy, ESG                                   |
| `oss`            | Open Source & Dev            | GitHub trending, new frameworks, developer tools                    |

#### FR-2.4: Multi-Level Summarization

Each article is processed into three depth levels:

| Level | Name      | Target Length                                             | Use Case                                |
| ----- | --------- | --------------------------------------------------------- | --------------------------------------- |
| L1    | Headline  | ≤ 15 words (~80 chars)                                    | Scan mode, push notifications           |
| L2    | Summary   | 3-5 sentences (~200-300 words)                            | Daily digest default view               |
| L3    | Deep Dive | 2-3 paragraphs (~500-800 words) + key findings + citation | Expand on tap; for deeply curious users |

**Implementation (Phase 1)**: Use existing LLM integration or free-tier options (Groq, Gemini API free tier, or local open-source models) with **dynamic prompting**: the prompt adjusts based on the user's per-topic depth preference. If the user marked a domain as "not my core area," the prompt generates an accessible TL;DR; if it's a core interest, it extracts key methodologies, findings, and links.

**Summarization quality**: Consider adopting **NER-guided summarization** techniques (inspired by the NewsLensAI framework) that use named entity recognition to anchor summaries in factual content, reducing hallucination risk. For academic papers: always include abstract, key findings, and citation link.

**Implementation (Phase 2)**: Fine-tune summarization with user feedback (which summaries were rated "helpful") and explore multi-model voting for quality control.

---

### 7.3 User Preference & Onboarding System

#### FR-3.1: Onboarding Wizard (Cold Start Solution)

**Step 1 — Domain Selection** (required)

- Show all available domains as selectable cards.
- User selects 2-5 domains of interest.
- At least 1 domain is mandatory.

**Step 2 — Per-Topic Depth Preference** (required) _(key improvement from PRD2)_

- For each selected domain, user chooses their preferred depth:
  - `Headlines only` → Default to L1
  - `Short summaries` → Default to L2
  - `Deep dives` → Default to L3
- **Rationale**: A user studying AI may want full paper analysis (L3) for AI/ML but only brief summaries (L1) for politics. This per-domain depth setting is a core differentiator.

**Step 3 — Frequency & Delivery** (required)

- Daily / Twice per week (Mon & Thu) / Weekly (Monday)
- Preferred delivery time (morning, midday, evening).
- Channel: In-app only, Email, or Both.

**Step 4 — Sample Article Rating** (optional but strongly recommended) _(from PRD3)_

- Show 3-5 representative articles from the user's selected domains.
- User rates each: "Interesting" / "Not for me."
- These ratings seed the initial user embedding for the recommendation engine, significantly improving Day-1 relevance.
- If skipped, system falls back to domain weights only.

**Step 5 — Seed Topics & Source Preferences** (optional)

- Free-text input: "Name a few things you're curious about recently."
- Trusted/excluded sources checklist.

**Design Constraint**: Entire wizard must complete in < 2 minutes. Steps 4 and 5 can be skipped with a "Set up later" button.

#### FR-3.2: Preference Profile Schema

```
interface UserPreferenceProfile {
    userId: string
    domains: {
        domainId: string
        weight: number              // 0.0 - 1.0, initialized from onboarding
        depthPreference: "L1" | "L2" | "L3"    // PER-DOMAIN depth
        isExplicit: boolean         // true if user selected; false if inferred
    }[]
    globalDepthFallback: "L1" | "L2" | "L3"    // default for unset domains
    deliverySchedule: {
        frequency: "daily" | "twice_weekly" | "weekly"
        preferredTime: string       // e.g., "08:00"
        timezone: string
        channel: "in_app" | "email" | "both"
    }
    seedTopics: string[]
    sampleArticleRatings: {         // from onboarding Step 4
        articleId: string
        rating: "interested" | "not_for_me"
    }[]
    trustedSources: string[]
    excludedSources: string[]
    blockedDomains: string[]        // "never show domain X" (hard block)
    explorationRate: number         // 0.0 - 1.0, default 0.15
    createdAt: Date
    updatedAt: Date
}
```

#### FR-3.3: Preference Dashboard ("My Interests")

- Visual display of current domain weights as a bar chart or slider set.
- **Side-by-side view**: "Your Explicit Settings" vs. "System's Understanding" — so users can see where the algorithm has drifted from their stated preferences and correct it.
- Per-domain depth toggles (L1/L2/L3) visible and adjustable.
- Exploration rate slider with plain-language label: "How adventurous should your feed be?"
- Users can manually adjust weights at any time (overrides algorithm).
- "Reset to defaults" and "Re-run onboarding" options.

---

### 7.4 Recommendation Engine (ML-Powered)

> Full algorithm design in [Section 10](#10-recommendation-algorithm-design).

#### FR-4.1: Content Scoring

For each candidate article, compute a **relevance score** combining:

- **Domain match score**: How well does the article's domain match the user's domain weights?
- **Topic similarity score**: Cosine similarity between article embedding and user's interest embedding.
- **Freshness score**: Exponential decay based on publish time.
- **Source diversity bonus**: Boost articles from under-represented sources in recent digests.
- **Exploration bonus**: Random boost for articles outside the user's primary domains (controlled by `explorationRate`).
- **Importance score**: Article-level signal derived from engagement proxies (e.g., citation count for papers, upvotes for HN/Reddit posts).

#### FR-4.2: Digest Assembly

- Select top-N articles (N configurable, default 10; user-configurable max items to prevent fatigue).
- Enforce diversity constraints:
  - No more than 40% of items from a single domain.
  - No more than 30% of items from a single source.
  - At least `explorationRate × N` items from non-primary domains.
- **Each item is rendered at its domain-specific depth level** (not a uniform depth).
- Order by: highest-scored items first, with domain interleaving (avoid 5 AI articles in a row).
- Include one "Trending This Week" section: GitHub trending repos, arxiv hot papers, HN top stories.

#### FR-4.3: Cold Start Strategy

| Phase     | Available Data                                 | Strategy                                                                                                             |
| --------- | ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Day 0     | Onboarding selections + sample article ratings | Content-based filtering using domain weights + seed topics + sample ratings. Exploration rate elevated to 0.25-0.30. |
| Days 1-7  | Onboarding + first explicit feedback           | Blend onboarding priors with initial feedback. Bayesian update on domain weights.                                    |
| Days 8-30 | Sufficient individual feedback                 | Full content-based model with learned user embedding. Reduce exploration rate toward user's setting.                 |
| Day 30+   | Rich feedback history + similar user data      | Introduce collaborative filtering component (Phase 2). Begin static/dynamic interest separation.                     |

---

### 7.5 Feedback Loop System

#### FR-5.1: Explicit Feedback Mechanisms

**Per-item feedback** (shown on every digest item):

| Mechanism                     | Input   | Signal Strength                                                         |
| ----------------------------- | ------- | ----------------------------------------------------------------------- |
| Thumbs Up / Down              | Binary  | Strong positive/negative                                                |
| 1-5 Star Rating               | Numeric | Granular preference signal                                              |
| "More Like This"              | Button  | Strong positive + topic expansion signal                                |
| "Less of This"                | Button  | Strong negative + topic suppression signal                              |
| "Not Relevant"                | Button  | Domain mismatch signal (not a quality judgment)                         |
| "Too Technical" / "Too Basic" | Button  | Per-domain depth calibration signal                                     |
| **"Never Show This Domain"**  | Button  | Hard block — permanently removes domain from feed until user re-enables |

**Periodic preference review** (triggered bi-weekly or on-demand):

- Multi-choice survey: "Which domains have you enjoyed most in the past 2 weeks?"
- Slider: "How adventurous do you want your feed to be?" (maps to `explorationRate`).
- Open text: "Any new topics you'd like to see?"

#### FR-5.2: Implicit Feedback Signals (Phase 2)

| Signal            | Collection Method                        | Interpretation            |
| ----------------- | ---------------------------------------- | ------------------------- |
| Click-through     | Track "Read Full Article" clicks         | Interest in topic         |
| Dwell time        | Time between summary open and close/next | Deep engagement vs. skim  |
| Scroll depth      | Percentage of summary read               | Content length preference |
| Digest completion | How many items read before closing       | Fatigue threshold         |
| Share action      | "Share this item" button                 | High-value content        |

#### FR-5.3: Implicit Feedback Noise Filtering _(from PRD3)_

Not all non-clicks represent negative feedback. A user may skip an article because they're busy, not because they dislike the topic. The system must:

- **Identify "preference noise"**: Distinguish genuine disinterest from contextual skips.
- **Rule**: An article only counts as implicit negative feedback if (a) dwell time < 5 seconds AND (b) the user viewed ≥ 3 other items in the same session (proving they were actively reading, not just closing the app).
- **Latent interest detection**: If a user never clicks biotech articles but does click articles about "CRISPR" (tagged biotech), the system should boost CRISPR-specific content rather than suppressing all biotech.

#### FR-5.4: Feedback-to-Model Pipeline

```
User Action → Event Bus → Feedback Processor → Noise Filter → Preference Updater → Model Re-scorer
                                                                       │
                                                                       ▼
                                                              UserPreferenceProfile
                                                              (domain weights, per-topic
                                                               depth, interest vectors)
```

- **Real-time lightweight updates**: Thumbs up/down immediately adjusts article-topic affinity scores in cache.
- **Batch model updates**: Nightly re-computation of user embedding and domain weights using all accumulated feedback.
- **Drift detection**: If 60%+ of recent feedback is for a domain with < 0.2 weight, auto-surface a prompt: "It looks like you're enjoying biotech content — want to increase it in your feed?"

---

### 7.6 Delivery & Notification System

#### FR-6.1: In-App Digest View (Phase 1)

- Rendered as a scrollable feed within the application.
- Each item shows: domain tag, headline (L1), summary at domain-specific depth, source attribution, publish date, feedback buttons.
- "Compact Mode" toggle: Switches to L1-only view.
- User-configurable max items per digest to prevent fatigue.

#### FR-6.2: Email Digest (Phase 2)

- HTML email template with responsive design.
- Includes top 5 items (L1 + L2) with "Read More" links.
- Preference-change and unsubscribe links in footer.
- Provider: SendGrid free tier (100 emails/day) or equivalent.

#### FR-6.3: Scheduling Engine

- Cron-based digest generation (Celery + Redis recommended).
- Per-user schedule based on `deliverySchedule` in profile.
- Digest pre-generation: Build digests 30 min before delivery time to avoid latency spikes.

---

### 7.7 Social Platform Connector (Experimental)

> Full strategy in [Section 11](#11-social-platform-integration-strategy).

#### FR-7.1: Social Source Adapter Interface

Extends the base `SourceAdapter` with social-specific fields:

```
interface SocialSourceAdapter extends SourceAdapter {
    platform: string                    // "github" | "reddit" | "rss_bridge"
    contentType: "post" | "thread" | "repo" | "comment"
    engagementMetrics: boolean          // can we get likes/stars/upvotes?
    fetchTrending(domain: string): RawArticle[]
}
```

#### FR-7.2: Supported Social Sources (Phased)

| Platform                   | Method                            | Phase    | Feasibility                           |
| -------------------------- | --------------------------------- | -------- | ------------------------------------- |
| **GitHub Trending**        | GitHub API (REST v3)              | Phase 1  | High — free, public API               |
| **Reddit**                 | Reddit API (OAuth, PRAW library)  | Phase 1  | High — well-documented                |
| **Hacker News**            | Official HN Firebase API          | Phase 1  | High — free, no auth                  |
| **RSS Feeds** (general)    | Direct polling of public RSS/Atom | Phase 1  | High — unlimited                      |
| **Mastodon**               | Public API (per-instance)         | Phase 2  | High — federated, many ML researchers |
| **RedNote (Xiaohongshu)**  | RSSHub or community scrapers      | Phase 2  | Medium — no official API              |
| **WeChat Public Accounts** | RSSHub / Sogou WeChat search      | Phase 2  | Low-Medium — restricted               |
| **Twitter/X**              | RSS bridges, free API tier        | Phase 2  | Low — API expensive, bridges fragile  |
| **Instagram**              | No free content discovery API     | Phase 3+ | Low — requires business verification  |

#### FR-7.3: Tavily-as-Bridge Strategy

For platforms without APIs (Phase 1 workaround), use Tavily/SearXNG web search with social-platform-specific queries:

- Query pattern: `"trending on Xiaohongshu [topic]"`, `"WeChat public account [topic] this week"`.
- Low reliability but zero additional cost; provides a signal until proper adapters are built.

---

### 7.8 Research Module Integration

#### FR-8.1: "Save to Research" Action

- Every digest item and search result includes a "Save to Research" button.
- Clicking saves the item (title, URL, summary, domain tags, source) to the existing Research module's data store.
- Creates a bidirectional link: Research module can surface related Discovery Feed items; Discovery Feed can deprioritize items the user already saved.

#### FR-8.2: Cross-Module Search

- The unified search bar in Discovery Feed also searches the user's saved Research items, enabling a single entry point for all knowledge retrieval.

---

## 8. Non-Functional Requirements

| Category           | Requirement                  | Target                                                                                                                                                 |
| ------------------ | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Performance**    | Search response time         | ≤ 3 seconds (p95)                                                                                                                                      |
| **Performance**    | Per-article summarization    | ≤ 3 seconds                                                                                                                                            |
| **Performance**    | Full daily digest generation | ≤ 5 minutes total; ≤ 30 seconds per user                                                                                                               |
| **Scalability**    | Concurrent users supported   | ≥ 1,000 (Phase 1); horizontally scalable to 100K                                                                                                       |
| **Reliability**    | Source failure tolerance     | System must function with ≥ 1 source online; graceful degradation with "limited results" fallback                                                      |
| **Availability**   | Service uptime               | ≥ 99% (self-hosted open-source stack)                                                                                                                  |
| **Data Privacy**   | User preference data         | Encrypted at rest; stored locally only; never shared with third parties. User can export or delete all preference data (GDPR / privacy law compliant). |
| **Data Retention** | Feedback history             | Retained for 12 months; user-deletable on request                                                                                                      |
| **Cost**           | Monthly external API cost    | $0 (free tiers only); strict budget enforcement                                                                                                        |
| **Extensibility**  | New source integration time  | ≤ 1 developer-day (≤ 2 hours for simple RSS adapters)                                                                                                  |
| **Accessibility**  | Digest readability           | Mobile-friendly cards; dark mode support; WCAG 2.1 AA compliant                                                                                        |
| **Error Handling** | API failures                 | Backoff + cache fallback; user sees "limited results" not errors                                                                                       |

---

## 9. Data Sources & API Strategy

### 9.1 Free-Tier API Inventory

| Source                    | Type                 | Coverage                    | Free Tier                      | Auth           | Notes                                         |
| ------------------------- | -------------------- | --------------------------- | ------------------------------ | -------------- | --------------------------------------------- |
| **Tavily** (existing)     | Search API           | General web + news          | 1,000 req/mo                   | API key        | Remove stock-only filter for Discovery Feed   |
| **NewsAPI.org**           | News aggregator      | 80K+ sources, global        | 100 req/day (dev)              | API key        | Strong general news coverage                  |
| **GNews.io**              | News aggregator      | 60K+ sources                | 100 req/day                    | API key        | Good historical search                        |
| **NewsData.io**           | News aggregator      | 87K+ sources, 206 countries | 200 credits/day                | API key        | Broadest geographic coverage                  |
| **MediaStack**            | News aggregator      | 7K+ sources                 | 500 req/mo                     | API key        | Stable, good for scheduled pulls              |
| **TheNewsAPI**            | News aggregator      | Global                      | Free tier available            | API key        | Additional diversity source                   |
| **arxiv API**             | Academic papers      | All arxiv categories        | Unlimited (polite)             | None           | Primary for AI/ML papers                      |
| **Semantic Scholar**      | Academic + citations | 200M+ papers                | 1K req/5min                    | API key (free) | Citation graphs, influence scores             |
| **PubMed API**            | Biomedical papers    | 35M+ citations              | Unlimited (polite)             | None           | Primary for biotech domain                    |
| **OpenAlex**              | Academic papers      | 250M+ works                 | Unlimited                      | None           | Open alternative to Semantic Scholar          |
| **RSS Feeds**             | Various              | Any site with RSS           | Unlimited                      | None           | Backbone for scheduled polling                |
| **Hacker News API**       | Tech community       | Tech/startup                | Unlimited                      | None           | Firebase JSON API                             |
| **Reddit API**            | Social platform      | All subreddits              | 100 req/min (OAuth)            | OAuth          | Via PRAW library                              |
| **GitHub API**            | Code repos           | Open source                 | 60 req/hr (unauth) / 5K (auth) | Optional       | Trending repos, release notes                 |
| **EventRegistry**         | News + events        | Global                      | 2K articles/mo                 | API key        | Trending event detection                      |
| **SearXNG** (self-hosted) | Meta-search          | 70+ engines                 | Unlimited                      | None           | Open-source Tavily alternative; Docker deploy |

### 9.2 Source Allocation Strategy

To maximize diversity within free-tier limits:

```
Daily Budget Allocation (per active domain):
├── Domain: AI/ML
│   ├── Primary:   arxiv API (2-3 queries)
│   ├── Secondary: Semantic Scholar (2 queries)
│   ├── Tertiary:  Hacker News top + Reddit r/MachineLearning
│   └── Fallback:  Tavily (1 query) or SearXNG
├── Domain: Tech
│   ├── Primary:   Hacker News API (1 query)
│   ├── Secondary: NewsAPI (2 queries)
│   ├── Tertiary:  GitHub Trending (1 query)
│   └── Fallback:  RSS (TechCrunch, Ars Technica, The Verge)
├── Domain: Economics
│   ├── Primary:   NewsAPI (2 queries, finance category)
│   ├── Secondary: GNews (1 query)
│   └── Tertiary:  RSS (Reuters, Bloomberg free, FT free)
├── Domain: Politics
│   ├── Primary:   NewsAPI (2 queries)
│   ├── Secondary: NewsData.io (1 query)
│   └── Tertiary:  RSS (AP, BBC, NPR)
├── Domain: Biotech
│   ├── Primary:   PubMed API (2 queries)
│   ├── Secondary: Semantic Scholar (2 queries, bio filter)
│   └── Tertiary:  NewsAPI (1 query, health category)
├── Domain: Sustainability
│   ├── Primary:   NewsAPI (1 query, environment category)
│   ├── Secondary: RSS (Nature Climate, Carbon Brief)
│   └── Tertiary:  GNews (1 query)
└── Exploration Pool
    ├── SearXNG (2-3 broad queries)
    └── EventRegistry (1 query, trending events)
```

### 9.3 Source Redundancy & Fallback

```
if primary_source.healthCheck() fails:
    use secondary_source
    if secondary_source.healthCheck() fails:
        use tertiary_source
        if tertiary_source.healthCheck() fails:
            use cached_content (max 24h old)
            flag source_degradation alert
```

If Tavily budget is exhausted mid-month, SearXNG (self-hosted, unlimited) takes over as the primary general search engine automatically.

---

## 10. Recommendation Algorithm Design

### 10.1 Architecture Overview

```
                    ┌─────────────────────────┐
                    │    Candidate Articles    │
                    │    (from aggregation)    │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Feature Extraction     │
                    │  - TF-IDF / Embeddings   │
                    │  - Domain tags / LDA     │
                    │  - Freshness + Importance│
                    │  - Source metadata        │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                   ▼
    ┌─────────────────┐ ┌──────────────┐ ┌──────────────────┐
    │  Content-Based   │ │ Collaborative│ │   Exploration    │
    │  Filtering       │ │ Filtering    │ │   Component      │
    │  (Phase 1)       │ │ (Phase 2)    │ │   (Always on)    │
    └────────┬────────┘ └──────┬───────┘ └────────┬─────────┘
             │                 │                    │
             └────────┬────────┘                    │
                      ▼                             │
            ┌─────────────────┐                     │
            │  Score Blender   │◀────────────────────┘
            │  (weighted sum)  │
            └────────┬────────┘
                     │
            ┌────────▼────────┐
            │ Diversity Filter │
            │ & Digest Builder │
            └─────────────────┘
```

### 10.2 Content-Based Filtering (Phase 1 — Primary)

**User Representation**:

Each user is represented as a vector in topic space:

```
user_vector = α × explicit_preference_vector + (1-α) × learned_behavior_vector
```

Where:

- `explicit_preference_vector`: Derived from onboarding selections, sample article ratings, and manual weight adjustments.
- `learned_behavior_vector`: Updated daily from feedback (positive items increase vector components, negative items decrease them).
- `α`: Decays from 1.0 (day 0) to 0.3 (day 30+) as behavioral data accumulates. This ensures onboarding priors dominate early but gracefully yield to learned behavior.

**Article Representation**:

Phase 1: TF-IDF vectors with LDA topic distributions for interpretable domain signals.
Phase 2: Dense embeddings from a pre-trained model like `all-MiniLM-L6-v2` via sentence-transformers.

**Scoring**:

```
content_score = cosine_similarity(user_vector, article_vector)
```

### 10.3 Static vs. Dynamic Interest Separation _(from PRD3)_

Phase 2 introduces a dual-interest model:

- **Static (long-term) interests**: Stable preferences that rarely change (e.g., "I'm an AI researcher, I'll always want AI papers"). Modeled as a slowly-decaying weighted average of all historical feedback.
- **Dynamic (short-term) interests**: Current curiosities that shift week-to-week (e.g., "I'm following the Fed rate decision this month"). Modeled using a **GRU (Gated Recurrent Unit)** over recent feedback sequences to capture temporal patterns.

```
final_user_vector = β × static_interest + (1-β) × dynamic_interest
```

Where `β` is tuned per user based on how stable their behavior has been (high stability → higher β).

**Rationale**: This prevents the system from over-rotating toward a temporary curiosity. If a user spends a week reading about a political crisis but is fundamentally an AI researcher, the system should return to AI-heavy content after the crisis passes.

### 10.4 Exploration Component (ε-Greedy with Decay)

```
exploration_score = {
    explorationRate × random(0, 1)    if article.domain NOT IN user.primaryDomains
    0                                  otherwise
}
```

Default `explorationRate` = 0.15 (15% novel content), user-adjustable 0.10 to 0.30. This ensures that even exploitation-heavy users still discover content outside their bubble. A fixed minimum of 5% exploration is enforced regardless of user setting ("filter bubble defense").

### 10.5 Final Score Computation

```
final_score = w1 × content_score
            + w2 × freshness_score
            + w3 × source_diversity_bonus
            + w4 × exploration_score
            + w5 × importance_score

Default weights:
  w1 = 0.45  (relevance)
  w2 = 0.20  (recency)
  w3 = 0.10  (source diversity)
  w4 = 0.15  (exploration)
  w5 = 0.10  (importance / engagement proxy)
```

### 10.6 Feedback Integration

| Feedback Signal       | Update Action                                                          |
| --------------------- | ---------------------------------------------------------------------- |
| Thumbs Up             | Increase weight of article's domain and topic tags by +0.05            |
| Thumbs Down           | Decrease weight by -0.05                                               |
| "More Like This"      | Add article's topic vector to user's positive exemplar set             |
| "Less of This"        | Add to negative exemplar set                                           |
| "Not Relevant"        | Decrease domain weight by -0.10 (stronger signal)                      |
| "Never Show Domain X" | Set domain weight to 0.0; add to `blockedDomains` list                 |
| "Too Technical"       | Shift that domain's depth preference toward L1/L2                      |
| "Too Basic"           | Shift that domain's depth preference toward L2/L3                      |
| 1-5 Star Rating       | Weighted update: `(rating - 3) × 0.03` applied to domain/topic weights |

### 10.7 Preference Drift Detection

- Compute a rolling 14-day average of domain engagement.
- If a domain's 14-day average engagement score diverges > 0.3 from its stored weight, trigger a **drift notification**:
  - "We noticed you've been enjoying more Biotech content lately. Want to see more?"
  - User can accept (auto-adjust weights), dismiss, or snooze for 1 week.
- Drift detection also monitors per-topic depth signals: if a user consistently clicks "Too Basic" on economics summaries, auto-prompt to upgrade that domain to L3.

### 10.8 Recommended Libraries (Phase 1)

| Library               | Purpose                                                           |
| --------------------- | ----------------------------------------------------------------- |
| scikit-learn          | TF-IDF, cosine similarity, basic classifiers                      |
| gensim                | LDA topic modeling                                                |
| Surprise / implicit    | Lightweight recommendation engine (content-based + collaborative). Note: LightFM was replaced by `implicit` due to build incompatibility with modern setuptools. |
| sentence-transformers | Dense embeddings (Phase 2)                                        |

---

## 11. Social Platform Integration Strategy

### 11.1 The Challenge

Many valuable content sources live on platforms without free/public APIs: RedNote (Xiaohongshu), WeChat, Instagram, etc. Direct API access is either expensive, restricted to business accounts, or entirely unavailable.

### 11.2 Feasible Approaches (Ranked by Viability)

#### Tier 1 — Direct Free APIs (Use Immediately)

| Platform       | Approach                               | Notes                                         |
| -------------- | -------------------------------------- | --------------------------------------------- |
| GitHub         | REST API v3 (authenticated: 5K req/hr) | Trending repos, release notes, README changes |
| Reddit         | OAuth API (PRAW library)               | Subreddit top/rising posts, comments          |
| Hacker News    | Firebase API                           | Top, new, best stories; comment threads       |
| Stack Overflow | Public API                             | Trending questions by tag                     |
| Mastodon       | Public API (per-instance)              | Federated; many ML researchers present        |

#### Tier 2 — RSS Bridge / Self-Hosted Proxies (Phase 2)

For platforms without APIs, use open-source RSS generators:

- **RSSHub** (docs.rsshub.app): Community-maintained. Supports Weibo, Bilibili, Zhihu, Douban, Xiaohongshu (partial), WeChat (via Sogou). Self-hosted or public instances available.
- **RSS-Bridge** (github.com/RSS-Bridge/rss-bridge): Generates RSS for Twitter/X (via Nitter), Instagram (public profiles), Telegram channels, YouTube.
- **Risk**: Platform-side blocking, maintenance burden, scraping instability.

#### Tier 3 — Web Search as Social Bridge (Phase 1 Workaround)

Use Tavily/SearXNG with targeted queries:

- `"trending on Xiaohongshu AI 2026"`
- `"WeChat public account machine learning this week"`
- Low reliability but zero cost; provides directional signal until proper adapters exist.

#### Tier 4 — User-Contributed Links (Always Available)

- Allow users to submit URLs manually ("I found this interesting").
- System processes them through the same pipeline (normalize, summarize, classify).
- Popular user-submitted links can be surfaced to similar users (collaborative signal).

**Legal/ethical note**: All social platform data acquisition must strictly follow platform Terms of Service. Prioritize official APIs; if scraping is necessary, only collect fully public content and respect robots.txt and rate limits.

### 11.3 Recommended Phasing

```
Phase 1: GitHub + Reddit + HN + RSS feeds + Tavily/SearXNG web bridge
Phase 2: RSSHub/RSS-Bridge for Chinese/social platforms (self-hosted Docker)
Phase 3: Evaluate paid aggregators or partnerships for WeChat/RedNote
Always:  User-contributed links as supplementary source
```

---

## 12. Extensibility & Plugin Architecture

### 12.1 Extension Points

The system is designed with the following extension points, each requiring only the implementation of a defined interface:

| Extension Point                 | Interface                               | Example Use Case                                                            |
| ------------------------------- | --------------------------------------- | --------------------------------------------------------------------------- |
| **New Data Source**             | `SourceAdapter` / `SocialSourceAdapter` | Adding Bloomberg RSS, a new free API, or a paid source when funding arrives |
| **New Content Processor**       | `ProcessingStage`                       | Adding translation, sentiment analysis, bias detection, or NER enrichment   |
| **New Recommendation Strategy** | `RecommendationStrategy`                | Swapping in BERT4Rec, neural collaborative filter, or bandit algorithms     |
| **New Delivery Channel**        | `DeliveryChannel`                       | Adding Slack bot, Telegram bot, SMS, or WeChat template messages            |
| **New Feedback Type**           | `FeedbackHandler`                       | Adding bookmark, highlight, annotation, or share as feedback signals        |
| **New Domain**                  | `DomainConfig` (config file)            | Adding "Sports", "Art", "Law", "Crypto" as content domains                  |
| **Search Engine Swap**          | `SearchBackend`                         | Replacing Tavily with SearXNG, OrioSearch, or a paid provider               |

### 12.2 Plugin Manifest Schema

Third-party or future extensions register themselves via a manifest:

```yaml
# Example: plugin-manifest.yaml
plugin:
  name: "pubmed-biotech-source"
  version: "1.0.0"
  type: "source_adapter"
  author: "internal"
  config:
    api_url: "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    poll_interval_minutes: 240
    supported_domains: ["biotech"]
    rate_limit_per_day: 50
  dependencies: []
```

### 12.3 Feature Flags

All experimental features are gated behind feature flags:

| Flag                              | Default | Description                                          |
| --------------------------------- | ------- | ---------------------------------------------------- |
| `enable_social_sources`           | `false` | Enable social platform adapters                      |
| `enable_collaborative_filtering`  | `false` | Enable user-user similarity in recommendations       |
| `enable_implicit_feedback`        | `false` | Track read-time, scroll depth, etc.                  |
| `enable_noise_filtering`          | `false` | Apply implicit feedback noise filtering              |
| `enable_email_digest`             | `false` | Send digests via email                               |
| `enable_depth_auto_adjust`        | `false` | Auto-detect preferred depth from behavior per domain |
| `enable_drift_notification`       | `true`  | Prompt user when interest drift is detected          |
| `enable_user_submissions`         | `true`  | Allow users to submit URLs                           |
| `enable_searxng_fallback`         | `true`  | Use SearXNG when Tavily quota exhausted              |
| `enable_lda_classification`       | `false` | Use LDA topic modeling instead of keyword classifier |
| `enable_static_dynamic_interests` | `false` | Split user model into static/dynamic components      |
| `enable_trending_section`         | `true`  | Include "Trending This Week" in digest               |
| `enable_research_bridge`          | `true`  | "Save to Research" button                            |

### 12.4 User-Configurable Extensions

- **Custom RSS feeds**: Users can add their own RSS URLs via settings. The system creates a personal `SourceAdapter` instance for each.
- **API endpoint for manual digest**: Trigger an on-demand digest refresh outside the scheduled time.
- **Webhook endpoints**: For future integration with external automation tools (Zapier, IFTTT, n8n).

---

## 13. Wireframes & User Flows

### 13.1 Onboarding Flow

```
[Welcome Screen]
    │
    ▼
[Step 1: Select Domains]──────────────────────────────────────┐
  "What topics interest you? Pick 2-5."                        │
  ┌──────┐ ┌──────┐ ┌──────┐ ┌────────┐ ┌───────┐ ┌──────┐  │
  │ AI/ML│ │ Tech │ │ Econ │ │Politics│ │Biotech│ │ Env. │  │
  └──────┘ └──────┘ └──────┘ └────────┘ └───────┘ └──────┘  │
  [+ Add custom topic ___________]                            │
    │                                                         │
    ▼                                                         │
[Step 2: Per-Topic Depth]                                     │
  "How deep for each topic?"                                  │
  AI/ML:    ○ Headlines  ○ Summaries  ● Deep Dives            │
  Econ:     ○ Headlines  ● Summaries  ○ Deep Dives            │
  Politics: ● Headlines  ○ Summaries  ○ Deep Dives            │
    │                                                         │
    ▼                                                         │
[Step 3: Delivery Preference]                                 │
  "How often?"                                                │
  ○ Daily  ○ Twice a week  ○ Weekly                           │
  "Best time?" [Morning ▾]                                    │
  "Where?" ○ In-app  ○ Email  ○ Both                          │
    │                                                         │
    ▼                                                         │
[Step 4: Rate Sample Articles] (optional, strongly suggested) │
  "Help us learn your taste — rate a few articles."           │
  ┌──────────────────────────────────────┐                    │
  │ "GPT-5 Architecture Revealed..."     │ [👍] [👎]         │
  │ "Fed Holds Rates Steady..."          │ [👍] [👎]         │
  │ "CRISPR Trial Shows Promise..."      │ [👍] [👎]         │
  │ "New Solar Cell Efficiency Record.." │ [👍] [👎]         │
  └──────────────────────────────────────┘                    │
  [Skip for now]                                              │
    │                                                         │
    ▼                                                         │
[Step 5: Seed Topics & Sources] (optional)                    │
  "Any specific topics you're curious about?"                 │
  [transformer architectures          ]                       │
  [CRISPR                             ]                       │
  "Trusted sources?" ☑ arxiv ☐ TechCrunch ☑ Reuters          │
  "Sources to exclude?" [___________]                         │
    │                                                         │
    ▼                                                         │
[Done! Your first digest is being prepared...]                │
  "Expected delivery: Tomorrow at 8:00 AM"                    │
└─────────────────────────────────────────────────────────────┘
```

### 13.2 Digest Item Layout (with per-topic depth)

```
┌──────────────────────────────────────────────────────────┐
│  [AI/ML · Deep Dive] 🕐 2h ago             [arxiv + HN] │
│                                                          │
│  New Mixture-of-Agents Architecture Achieves SOTA        │
│  on Multi-Task Benchmarks                                │
│                                                          │
│  A team from [Lab] published a technical report showing  │
│  that their mixture-of-agents approach with specialized  │
│  sub-models for reasoning, code, and retrieval achieves  │
│  state-of-the-art results on 12 benchmarks. Key method:  │
│  hierarchical routing with learned gating functions.      │
│  The approach reduces inference cost by 40% compared to  │
│  dense models of equivalent capability...                 │
│                                     [▼ Show full analysis]│
│                                                          │
│  👍  👎  [More like this]  [Less of this]  ⭐⭐⭐⭐☆    │
│  [Save to Research]              [Open source ↗]         │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  [Economics · Headline] 🕐 5h ago          [NewsAPI]     │
│                                                          │
│  Fed Signals Potential Rate Cut in Q3 2026               │
│                                                          │
│  👍  👎  [More like this]  [Less of this]  [Too basic?]  │
│  [Save to Research]              [Open source ↗]         │
└──────────────────────────────────────────────────────────┘
```

### 13.3 Preference Dashboard Layout

```
┌──────────────────────────────────────────────────────────┐
│  MY INTERESTS                          [Reset] [Re-onboard]│
│                                                          │
│  Your Settings            System's Understanding         │
│  ─────────────            ─────────────────────          │
│  AI/ML    ████████░░ 0.80  AI/ML    ██████████ 0.95     │
│   Depth: [Deep Dive ▾]     Suggested: Deep Dive ✓       │
│  Tech     ██████░░░░ 0.60  Biotech  ████████░░ 0.75     │
│   Depth: [Summary ▾]       Suggested: Summary → Deep?   │
│  Econ     ████░░░░░░ 0.40  Tech     ██████░░░░ 0.55     │
│   Depth: [Summary ▾]       Suggested: Summary ✓         │
│  Biotech  ███░░░░░░░ 0.30  Econ     ████░░░░░░ 0.35     │
│   Depth: [Summary ▾]       Suggested: Headline → Sum?   │
│  Politics ██░░░░░░░░ 0.20  Politics █░░░░░░░░░ 0.10     │
│   Depth: [Headline ▾]      Suggested: Headline ✓        │
│                                                          │
│  ⚡ Drift Alert: You've been engaging with Biotech       │
│     content 3x more than your setting suggests.          │
│     Also, your depth on Econ may be too shallow—you've   │
│     clicked "Too basic" 4 times recently.                │
│     [Adjust automatically] [Dismiss] [Snooze 1 week]    │
│                                                          │
│  Exploration Rate: [═══════●═══] 15%                     │
│  "How adventurous should your feed be?"                  │
│                                                          │
│  Max items per digest: [10 ▾]                            │
│  Blocked domains: [None]                                 │
│                                                          │
│  Delivery: [Daily ▾] at [8:00 AM ▾] [PST ▾] [Both ▾]  │
│                                                          │
│  🔒 Privacy: [Export my data] [Delete all my data]       │
└──────────────────────────────────────────────────────────┘
```

---

## 14. Recommended Tech Stack _(consolidated from PRD3 + team input)_

| Layer                    | Technology                                                            | Rationale                                                                           |
| ------------------------ | --------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| **Backend Framework**    | Python FastAPI (primary) + Node.js (existing)                         | FastAPI is lightweight, async-native, ideal for API aggregation and ML integration  |
| **Data Storage**         | PostgreSQL                                                            | User profiles, preference history, article metadata, feedback logs                  |
| **Cache / Real-time**    | Redis                                                                 | API response caching, rate limit tracking, real-time feedback scores, Celery broker |
| **Task Scheduling**      | Celery + Redis (broker)                                               | Async task queue for scheduled fetches, digest generation, model retraining         |
| **Search Fallback**      | SearXNG (Docker)                                                      | Self-hosted meta-search; 70+ engines; unlimited; no API key                         |
| **ML / NLP**             | scikit-learn, gensim, Surprise/implicit                               | TF-IDF, LDA, cosine similarity, lightweight recommendation                          |
| **Embeddings (Phase 2)** | sentence-transformers (`all-MiniLM-L6-v2`)                            | Dense article/user embeddings for improved similarity                               |
| **Summarization**        | Existing LLM integration / Groq free tier / local model               | Dynamic prompting with per-topic depth                                              |
| **Email Delivery**       | SendGrid free tier (100/day) or equivalent                            | Phase 2 email digest delivery                                                       |
| **Containerization**     | Docker + Docker Compose                                               | Reproducible deployment; easy addition of SearXNG, Redis, etc.                      |
| **Open-source tools**    | ClawFeed (content aggregation), NewsLensAI (NER-guided summarization) | Community-proven frameworks to accelerate development                               |

---

## 15. Technical Constraints & Risks

### 15.1 Constraints

| Constraint                       | Impact                                          | Mitigation                                                                                   |
| -------------------------------- | ----------------------------------------------- | -------------------------------------------------------------------------------------------- |
| **$0 budget**                    | Cannot use paid APIs                            | Maximize free tiers; SearXNG as unlimited fallback; RSS as backbone; multi-key rotation      |
| **Free-tier rate limits**        | May not support > 100 users without caching     | Aggressive caching (Redis); shared content pool across users with similar interests          |
| **No GPU**                       | Cannot run large local ML models                | Use lightweight models (TF-IDF, LDA, small sentence-transformers); defer heavy ML to Phase 2 |
| **Single Tavily allocation**     | Must share with existing Research Module        | Allocate ≤ 50% to Discovery Feed; SearXNG handles overflow                                   |
| **Social platform restrictions** | No official APIs for RedNote, WeChat, Instagram | Tier 3 web-search bridge (Phase 1); RSSHub (Phase 2); graceful degradation                   |

### 15.2 Risks

| Risk                                              | Likelihood | Impact        | Mitigation                                                                                         |
| ------------------------------------------------- | ---------- | ------------- | -------------------------------------------------------------------------------------------------- |
| Free API deprecation or policy change             | Medium     | High          | Adapter pattern ensures quick swap; ≥ 3 sources per domain; SearXNG as universal fallback          |
| Cold start produces poor Day-1 recommendations    | High       | Medium        | Rich onboarding with sample article ratings; elevated exploration rate; fast feedback loops        |
| User feedback fatigue (stop rating)               | High       | Medium        | Make feedback frictionless (single tap); Phase 2 implicit signals; bi-weekly surveys               |
| Implicit feedback noise (non-click ≠ disinterest) | Medium     | Medium        | Noise filtering rules (dwell time + session activity thresholds); latent interest detection        |
| Social platform scraping blocked                  | High       | Low (Phase 2) | RSSHub is community-maintained; Tavily web bridge as fallback; degrade gracefully                  |
| Content quality variance across sources           | Medium     | Medium        | Source trust scoring; user-reported quality flags; importance score weighting                      |
| Summarization hallucination                       | Medium     | Medium        | NER-guided summarization; for papers always include original abstract; human-eval QA               |
| Filter bubble despite exploration                 | Low        | High          | Mandatory minimum 5% exploration; periodic "wildcard" items; drift alerts                          |
| Privacy/legal compliance gaps                     | Low        | High          | Local-only data storage; GDPR export/delete; no unauthorized scraping; Terms of Service compliance |

---

## 16. Phased Rollout Plan

### Phase 1 — Foundation (Weeks 1-6)

**Goal**: Working end-to-end pipeline with content-based personalization and per-topic depth.

| Week | Deliverable                                                                                                                                                  |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1-2  | Source adapters: Tavily, NewsAPI, GNews, arxiv, HN, 5+ RSS feeds. SearXNG Docker deployment. Aggregation engine with rate limit manager and Redis caching.   |
| 2-3  | Content processing pipeline: normalization, deduplication, keyword-based domain classification. Multi-level summarization (L1/L2/L3) with dynamic prompting. |
| 3-4  | Onboarding wizard (5 steps including sample article rating and per-topic depth). User preference profile storage (PostgreSQL).                               |
| 4-5  | Content-based recommendation engine (TF-IDF + LDA). Digest builder with diversity constraints and per-topic depth rendering. "Save to Research" bridge.      |
| 5-6  | Explicit feedback collection (all buttons). In-app digest view with compact mode. Preference dashboard (side-by-side view). Unified search bar.              |
| 6    | Internal dogfooding. Bug fixes. Performance optimization. Rate limit stress testing.                                                                         |

### Phase 2 — Intelligence (Weeks 7-12)

**Goal**: Smarter recommendations, more sources, richer feedback, drift detection.

| Week  | Deliverable                                                                                                                                             |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 7-8   | Implicit feedback tracking (clicks, dwell time). Noise filtering logic. Preference drift detection and notification system.                             |
| 8-9   | Social source adapters: GitHub Trending, Reddit (PRAW), Mastodon. RSSHub Docker deployment for broader social coverage.                                 |
| 9-10  | Upgrade to dense embeddings (`all-MiniLM-L6-v2`). Static/dynamic interest separation prototype. Collaborative filtering exploration (Surprise/implicit). |
| 10-11 | Email digest delivery (SendGrid). Scheduling engine improvements. Per-domain depth auto-adjustment based on feedback patterns.                          |
| 11-12 | "Explain Like I'm 5" depth level. User-submitted URL processing. Trend/burst detection for emerging topics. A/B testing framework.                      |

### Phase 3 — Scale & Polish (Weeks 13-18)

**Goal**: Production reliability, advanced personalization, broader reach.

| Week  | Deliverable                                                                                                                                                                 |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 13-14 | RSSHub integration for Chinese platforms (WeChat, Weibo, Zhihu, Xiaohongshu). Multi-language content detection and filtering.                                               |
| 15-16 | Advanced analytics dashboard (admin). Source quality scoring system. Audio digest / TTS prototype.                                                                          |
| 16-17 | User "Packs" (shareable algorithm configurations). Community digest sharing. Export to Notion/Obsidian.                                                                     |
| 17-18 | API for third-party integrations. Telegram / Slack bot delivery channels. Knowledge graph construction from consumed content (experimental). Plugin marketplace (internal). |

---

## 17. Appendix

### A. Glossary

| Term                 | Definition                                                                                       |
| -------------------- | ------------------------------------------------------------------------------------------------ |
| **Digest**           | A curated set of articles assembled for a specific user based on their preferences.              |
| **Domain**           | A high-level content category (e.g., AI/ML, Economics, Biotech).                                 |
| **Exploration Rate** | The percentage of digest items intentionally drawn from outside the user's primary interests.    |
| **Source Adapter**   | A standardized module that connects to one external data source and returns normalized articles. |
| **Cold Start**       | The period when the system has insufficient feedback to personalize effectively.                 |
| **Preference Drift** | A gradual change in user interests, detected by comparing recent feedback to stored preferences. |
| **Depth Level**      | The detail provided per article: L1 (headline), L2 (summary), L3 (deep dive).                    |
| **Per-Topic Depth**  | The ability to set different depth levels for different domains (e.g., AI=L3, Politics=L1).      |
| **Noise Filtering**  | Logic to prevent misinterpreting non-engagement as negative feedback.                            |
| **Static Interest**  | Long-term stable preferences (e.g., "I'm always interested in AI").                              |
| **Dynamic Interest** | Short-term, shifting curiosities (e.g., "following the election this month").                    |
| **SearXNG**          | Open-source, self-hosted meta-search engine aggregating 70+ search engines.                      |

### B. Competitive Landscape

| Product                | Strengths                        | Weaknesses (vs. our goals)                                         |
| ---------------------- | -------------------------------- | ------------------------------------------------------------------ |
| Google News            | Massive coverage, strong ranking | No per-topic depth, limited explicit feedback, no academic content |
| Feedly                 | Good RSS management              | User must curate own feeds; no ML recommendations by default       |
| Pocket Recommendations | Good discovery                   | Skews longform; no domain-balancing or depth control               |
| Arxiv Sanity           | Great for ML papers              | Only arxiv; no broader news                                        |
| Morning Brew / TLDR    | Well-written summaries           | One-size-fits-all; no personalization; no per-topic depth          |
| Perplexity Discover    | AI-powered discovery             | Closed ecosystem; limited preference controls; not free            |
| ClawFeed               | Open-source, multi-platform      | No personalization engine; aggregation only                        |

### C. Cross-PRD Synthesis Notes

This v2.0 document incorporates the best ideas from four independent PRD drafts:

| Contribution                                           | Origin          | Section Integrated |
| ------------------------------------------------------ | --------------- | ------------------ |
| Per-topic depth preferences                            | PRD2 (OmniNews) | §7.3, §13.1, §13.2 |
| Sample article rating during onboarding                | PRD3 (智能资讯) | §7.3 FR-3.1 Step 4 |
| Static vs. dynamic interest separation (GRU)           | PRD3 (智能资讯) | §10.3              |
| Implicit feedback noise filtering                      | PRD3 (智能资讯) | §7.5 FR-5.3        |
| SearXNG / OrioSearch as open-source Tavily alternative | PRD3 (智能资讯) | §7.1 FR-1.4, §9.1  |
| LDA topic modeling for classification                  | PRD3 (智能资讯) | §7.2 FR-2.3, §10.2 |
| NER-guided summarization (NewsLensAI)                  | PRD3 (智能资讯) | §7.2 FR-2.4        |
| "Save to Research" module integration                  | PRD1 (Insights) | §7.8               |
| "Never show domain X" hard block                       | PRD1 (Insights) | §7.5 FR-5.1        |
| PubMed API for biotech domain                          | PRD1 (Insights) | §9.1               |
| Tavily-as-bridge for social platforms                  | PRD1 (Insights) | §7.7 FR-7.3        |
| Specific tech stack recommendations                    | PRD3 (智能资讯) | §14                |
| Audio digest / personalized podcast                    | PRD2 (OmniNews) | §5.3, §16 Phase 3  |
| User "Packs" (shareable configurations)                | PRD2 (OmniNews) | §5.3, §16 Phase 3  |
| Export to Notion/Obsidian                              | PRD1 (Insights) | §5.3, §16 Phase 3  |
| GDPR / privacy law compliance details                  | PRD1 + PRD3     | §8, §13.3          |
| Sustainability as a domain                             | PRD1 (Insights) | §7.2 FR-2.3        |
| ClawFeed as open-source tool reference                 | PRD3 (智能资讯) | §14                |

### D. Open Questions for Discussion

| #   | Question                                                               | Status                                                                |
| --- | ---------------------------------------------------------------------- | --------------------------------------------------------------------- |
| 1   | Should per-topic depth be part of MVP or deferred?                     | **Included in MVP** — it's a core differentiator.                     |
| 2   | Minimum viable number of sample article ratings to improve cold start? | Proposed: 3-5 articles. Needs A/B testing.                            |
| 3   | Should exploration be purely random or "adjacent interest" weighted?   | Start random (Phase 1); move to adjacent (Phase 2).                   |
| 4   | How to handle paywalled content detected in results?                   | Mark as "paywalled" in metadata; show available summary only.         |
| 5   | Which free LLM tier is most reliable for summarization at scale?       | Evaluate Groq, Gemini free, local models in Phase 1.                  |
| 6   | Should we support group/team digests?                                  | Deferred to Phase 3 ("Packs" feature).                                |
| 7   | Is SearXNG stable enough for production fallback?                      | Deploy during Phase 1; monitor for 4 weeks before relying on it.      |
| 8   | How to handle multi-language content?                                  | Phase 1: English only. Phase 3: detect language, filter or translate. |
| 9   | Should the "Trending This Week" section be personalized or universal?  | Start universal (Phase 1); personalize in Phase 2.                    |

### E. Reference Links

- Tavily API: https://docs.tavily.com
- NewsAPI: https://newsapi.org/docs
- GNews: https://gnews.io/docs
- NewsData.io: https://newsdata.io/documentation
- arxiv API: https://info.arxiv.org/help/api
- Semantic Scholar: https://api.semanticscholar.org
- PubMed / NCBI E-utilities: https://www.ncbi.nlm.nih.gov/books/NBK25501/
- OpenAlex: https://docs.openalex.org
- Hacker News API: https://github.com/HackerNews/API
- SearXNG: https://docs.searxng.org
- RSSHub: https://docs.rsshub.app
- RSS-Bridge: https://github.com/RSS-Bridge/rss-bridge
- ClawFeed: https://github.com/clawfeed (open-source aggregation)
- Sentence-Transformers: https://www.sbert.net
- Surprise Library: https://surpriselib.com
- implicit: https://github.com/benfred/implicit (replaced LightFM — build incompatibility with modern setuptools)
- Celery: https://docs.celeryq.dev
- SendGrid: https://sendgrid.com (free tier: 100 emails/day)

---

_This is a living document consolidating inputs from four independent PRD drafts. All contributions are attributed in Appendix C. Next review scheduled for: [TBD]._
