# PRD v3 — Dynamic Interests & Feed Polish

**Status**: Draft
**Date**: April 2026
**Context**: Based on v2 UX testing. The static domain grid, broken click behavior, and template-looking UI need attention.

---

## Problem

The v2 system works but feels rigid. Users pick from 16 hard-coded categories — if their interest doesn't match one, they're stuck. The feed looks functional but not inviting. Exploration is invisible (baked into `fetch_smart` allocation) rather than presented as a distinct experience. Links don't open on click.

## Goals

1. Let users describe interests in their own words, not pick from a fixed list
2. Surface discovery ("You may also like") as a visible, intentional section
3. Fix click behavior — links open in new tabs on click
4. Redesign the frontend with a magazine/editorial aesthetic

---

## Changes

### 1. Dynamic Interest Input with LLM-Powered Suggestions

**Replace** the static checkbox grid with a text input field.

**Flow:**
1. User types a topic (e.g., "computer science")
2. System calls the LLM (Ollama, Groq fallback) to generate 8-12 related subtopics (e.g., "algorithms", "distributed systems", "AI/ML", "programming languages", "computer vision", "databases", "compilers", "networking")
3. Subtopics appear as selectable chips below the input
4. User taps chips to add them, or types another topic and repeats
5. Selected topics become the user's domain preferences

**Caching (Option C):**
- After the LLM generates subtopics for a parent topic, cache the result in a simple DB table (`topic_suggestions`) or in-memory dict
- Next time any user types the same parent topic, return cached subtopics instantly
- Cache entries expire after 7 days (topics evolve)

**This feature appears in two places:**
- Onboarding (`/onboarding`) — first-time setup
- Preferences (`/preferences`) — add new interests anytime

**Data model impact:**
- `UserDomainPreference.domain_id` is already `String(50)` — no schema change needed, custom topics fit directly
- Remove the `DomainID` StrEnum as a hard constraint. Keep it as a set of "seed" suggestions but the system accepts any string as a domain
- `DOMAIN_KEYWORDS` becomes a fallback/bootstrap — custom domains don't need pre-defined keywords

### 2. Dynamic Query Generation for Custom Domains

When fetching articles for a domain that has no entry in `DOMAIN_SOURCE_PRIORITY` or `DOMAIN_DEFAULT_QUERIES`:

1. Use the LLM to generate 2-3 search queries, e.g.:
   - Input: "computer science"
   - Output: `["latest computer science breakthroughs 2026", "trending CS research papers", "computer science technology news today"]`
2. Cache generated queries alongside topic suggestions (same table or adjacent)
3. Use general-purpose sources (Tavily, Google News, Semantic Scholar) as the default source priority for unknown domains

**Query style:** The LLM prompt should produce queries that find what's popular, latest, and hottest in that topic *today* — not evergreen content.

### 3. "You May Also Like" Section

**Replace** the current invisible exploration mechanism (`exploration_rate` + leftover budget in `fetch_smart`) with a visible section in the feed.

**How it works:**
- During each generation run, `fetch_smart` allocates 1-3 article slots to domains the user has **not** selected
- Pick these exploration domains randomly from: (a) trending topics, (b) adjacent topics to user interests, or (c) purely random from the known domain pool
- In the feed template, render these articles in a visually distinct **"You May Also Like"** section below the main feed
- Articles in this section are tagged with `is_exploration=True` in the digest item

**Feedback behavior:**
- If the user clicks an exploration article, record the domain with a **low initial weight** (0.1 instead of the normal 0.5) because we don't know if they're truly interested
- If the user later explicitly adds that domain via preferences, promote it to normal weight (0.5)
- Do **not** auto-promote exploration domains into the main feed — the user decides

**Remove:** `User.exploration_rate` field (replaced by this systematic approach). The number of exploration articles is fixed at 1-3 per generation, not a percentage.

### 4. Fix Click Behavior

The feed links have `target="_blank"` but htmx's `hx-post` on the same `<a>` tag may be intercepting the native navigation.

**Fix:** Ensure the click tracking fires without blocking the default link behavior. Options:
- Use `hx-trigger="click"` with `hx-swap="none"` and verify htmx doesn't call `preventDefault`
- Or switch click tracking to a vanilla JS `navigator.sendBeacon()` call (fire-and-forget, doesn't block navigation)

This is a bug fix, not a feature — should take minutes.

### 5. Frontend Redesign — Magazine / Editorial Style

**Direction:** Clean, refined, magazine-format news reader. Think Monocle, The Verge longform, or Apple News editorial layout. Not a dashboard. Not a SaaS template.

**Design principles:**
- **Typography-led:** Strong headline hierarchy. Large article titles, subdued metadata
- **Generous whitespace:** Let articles breathe. No dense card grids
- **Muted palette:** Off-white background, near-black text, one accent color for interactive elements. No bright blues or gradients
- **Serif headlines, sans-serif body:** Editorial pairing (e.g., Playfair Display + Inter, or similar free Google Fonts pair)
- **Cards with purpose:** Each article card has clear visual hierarchy — title dominates, summary is secondary, metadata is tertiary
- **Domain badges:** Subtle, not shouty. Pill-shaped, muted background tones per domain category
- **No clutter:** No sidebars, no widget panels, no unnecessary chrome

**Specific page treatments:**

**Feed (`/`):**
- Top article gets a larger treatment (featured card with bigger type)
- Remaining articles in a single-column list with comfortable spacing
- "You May Also Like" section has a distinct visual separator — maybe a subtle horizontal rule with the label, slightly different card style (lighter background, dashed border, or italic heading)
- "Generate" button is understated, not a bright blue block

**Onboarding (`/onboarding`):**
- Centered layout, welcoming headline
- Text input with placeholder "What are you interested in?"
- Suggestion chips appear with a gentle fade-in animation
- Selected interests shown as a growing tag list above or below the input
- Minimal — feels like a conversation, not a form

**Preferences (`/preferences`):**
- Same text input as onboarding for adding new interests
- Existing interests shown as removable tags with weight indicators
- Each tag has a small "x" button to **delete** the interest — removes the `UserDomainPreference` row and stops fetching articles for that domain
- Deletion is immediate (htmx `DELETE` call), no confirmation modal needed for a single-user tool
- Weight shown as subtle text percentage, not a progress bar

**Loading (`/loading`):**
- Keep the step-by-step progress display — it's good
- Refine typography and spacing to match the new style

**Base layout:**
- Navigation: minimal top bar with just the brand name and 2-3 links
- Max content width: 680px (reading-optimized column)
- Custom font loading with `font-display: swap`

---

## Technical Notes

### New LLM endpoint: Topic Expansion

```
POST /api/v1/topics/expand
Body: { "topic": "computer science" }
Response: { "topic": "computer science", "suggestions": ["algorithms", "distributed systems", ...], "cached": false }
```

- Calls Ollama (Groq fallback) with a prompt like: "Given the topic '{topic}', list 8-12 specific subtopics that someone interested in this field would want to follow for daily news. Return as a JSON array of short topic names."
- Cache result in DB or in-memory with 7-day TTL

### New LLM endpoint: Query Generation

When `DOMAIN_DEFAULT_QUERIES` has no entry for a domain:

```python
# Prompt: "Generate 3 search queries to find the most popular, latest, and
# hottest news about '{domain}' happening today. Return as JSON array."
```

- Cache alongside topic suggestions
- Default source priority for unknown domains: `["tavily", "gnews", "newsdata", "hackernews"]`

### Delete Interest

```
DELETE /api/v1/users/me/interests/{domain_id}
Response: 204 No Content
```

- Removes the `UserDomainPreference` row for that domain
- Future generation runs will no longer fetch articles for it
- Articles already in existing digests are unaffected (historical data stays)

### Feed data changes

- Each digest item needs an `is_exploration` boolean (or derive it by checking if the domain is in the user's explicit preferences)
- The frontend groups items: main feed vs. exploration section

### Migration

- Add `topic_suggestions` table: `id`, `parent_topic`, `suggestions` (JSON), `search_queries` (JSON), `created_at`, `expires_at`
- `exploration_rate` column on `users` table can be dropped (or left and ignored — low priority)

---

## Out of Scope (for now)

- Multi-user auth (still single-user)
- YouTube / video integration
- Email delivery
- Polished mobile responsive (keep it functional, but mobile perfection isn't the goal yet)
- Collaborative filtering
- NewsAPI fix (still waiting on co-founder)

---

## Implementation Order

1. **Fix click behavior** — bug fix, do first (minutes)
2. **Frontend redesign** — new base.html, feed.html, onboarding.html, preferences.html styles and layout
3. **Topic expansion endpoint** — LLM-powered suggestions with caching
4. **Dynamic query generation** — for custom domains without hard-coded queries
5. **Rewire onboarding** — text input + suggestion chips, replace checkbox grid
6. **Rewire preferences** — add interest input, removable tags with delete
7. **"You May Also Like" section** — modify `fetch_smart`, tag exploration items, render separate section
8. **Tests** — unit tests for topic expansion, query generation, exploration tagging
