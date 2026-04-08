# PRD v2 — UX Overhaul

**Status**: Draft  
**Date**: April 2026  
**Context**: Based on first-hand testing of the v1 digest API

---

## Problem

The v1 system works end-to-end but feels like a developer tool, not a personal news reader. Onboarding requires weight/depth configuration, output exposes internal scores, and the only interface is curl.

## Goals

1. Feel like a personal news search engine, not an API
2. Zero-config onboarding — pick interests, start reading
3. Learn from usage, not from explicit config
4. Functional web frontend (not curl)

## Changes

### 1. Simplified Onboarding

- Show a grid of interest categories (checkboxes)
- All selected interests start at equal weight (0.5) and default depth (L2)
- No weight sliders or depth pickers on first use
- Weights adjust implicitly over time through reading behavior

### 2. Clean Output

Only show what a reader cares about per article:

- Title
- Summary (Give 1 - 3 simple sentences to describe)
- Domain badge
- Link to original
- Source name + publish time

Remove from consumer view: depth labels, scores, exploration flags, internal IDs.

### 3. Implicit Feedback via Click Tracking

- Track when user clicks through to an article
- Increment that domain's weight slightly (+0.02 per click)
- Over time the digest naturally shifts toward what the user reads

### 4. Expand Domain Taxonomy

Current 8 domains are too narrow for search-like behavior. Add:

- Finance, Crypto, Health, Sports, Entertainment, Education, Startups, Cybersecurity

Total: ~16 domains.

### 5. Broad Content Collection (Search-Engine-Like Coverage)

The system should collect content the way a human searches the internet — casting a wide net across blogs, news sites, arxiv papers, forums, github repositories, and other media types. The user doesn't perform the search; the system does it automatically based on their interests. The digest should feel like the result of a thorough search across the internet, not a narrow pull from a few news APIs.

### 6. Functional Web Frontend

Tech: Jinja2 templates + htmx, served by FastAPI (no separate frontend process).

Pages:

- **Home** (`/`) — Latest digest as a clean feed
- **Onboarding** (`/onboarding`) — Interest picker grid
- **Preferences** (`/preferences`) — Toggle interests, see learned weights

### 7. Fix NewsAPI Integration

The co-founder of Event Registry (NewsAPI) reached out. Wait for the response.

### 8. Local LLM for Summarization

Groq-hosted summarization quality is mediocre. Evaluate running a local model Gemma 4 26B (it should be downloaded locally). Speed is important here, so use the correct quantization to make it fast but keep as much summarization ability as possible.

Benefits:

- No API cost or rate limits
- Full control over prompt/output quality
- Privacy (articles stay local)
- Can iterate on prompts without API latency

Trade-off: requires local GPU/CPU resources. Acceptable for a single-user personal tool.

But this does not mean to remove the API, just as a backup plan when local generation fails.

9. Create User and Login

Currently, it will only be me, the only user to use this tool. You can skip the user authentication for now and create user for now. But the project should remember my domain interests and weights.

## Out of Scope (for now)

- YouTube integration
- Delivery method
- Multi-user auth
- Polished visual design
- Collaborative filtering
