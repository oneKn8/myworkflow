# Content Automation Tools -- Build Plan

**Target:** `/home/oneknight/personal/myworkflow/tools/`
**Date:** 2026-03-05
**Total Estimate:** 15-20 days

---

## Overview

5 tools, built in dependency order. Python for 4 (shared ecosystem), Go for analytics (TUI + concurrency).

| Tool | Language | Complexity | Estimate | Priority |
|------|----------|------------|----------|----------|
| Cross-Poster | Python | Low-Medium | 2-3 days | P0 |
| Repurposer | Python | Medium | 2-3 days | P1 |
| Social Distribution | Python | Medium-High | 4-5 days | P1 |
| Newsletter | Python | Medium-High | 4-5 days | P2 |
| Analytics | Go | Medium | 3-4 days | P3 |

**Dependency Graph:**
```
cross-poster (standalone)
    |
    v
repurpose (uses sanitize patterns from cross-poster)
    |
    v
social (consumes repurpose output)

newsletter (standalone, uses repurpose newsletter format)

analytics (standalone, read-only)
```

---

## 1. Cross-Poster (`tools/cross-poster/`)

**Language: Python** -- Best markdown parsing ecosystem, I/O-bound work.

### File Structure
```
tools/cross-poster/
  pyproject.toml
  cross_poster/
    __init__.py
    cli.py              # Click CLI entry point
    config.py           # Env var loading, config dataclass
    models.py           # SQLite schema + data access
    sanitize.py         # MDX stripping, image URL resolution
    platforms/
      __init__.py
      devto.py          # Dev.to REST API client
      hashnode.py       # Hashnode GraphQL API client
    db.py               # SQLite connection + migrations
  tests/
    test_sanitize.py
    test_devto.py
    test_hashnode.py
  .env.example
```

### Dependencies
- `click` -- CLI framework
- `python-frontmatter` -- parse YAML frontmatter from markdown
- `httpx` -- async HTTP client
- `python-dotenv` -- env var loading

### API Details

**Dev.to:**
- Endpoint: `POST https://dev.to/api/articles`
- Auth: `api-key: {DEV_TO_API_KEY}` header
- Body: `{"article": {"title": "...", "body_markdown": "...", "published": true, "tags": ["tag1", "tag2"], "canonical_url": "https://yourblog.com/post-slug"}}`
- Max 4 tags, lowercase, no special characters
- Rate limit: HTTP 429 with backoff

**Hashnode:**
- Endpoint: `POST https://gql.hashnode.com`
- Auth: `Authorization: {HASHNODE_PAT}` header
- Mutation: `publishPost(input: PublishPostInput!)` with: `title`, `contentMarkdown`, `publicationId`, `tags`, `originalArticleURL`, `slug`
- Requires `publicationId` (obtained via separate query)

### Content Sanitization Pipeline (`sanitize.py`)
1. Parse frontmatter with `python-frontmatter`
2. Strip MDX import statements: `^import\s+.*$`
3. Replace custom Astro/MDX components with plain markdown or "see original" links
4. Convert `<figure>/<img>` to `![alt](url)` markdown
5. Resolve relative image paths to absolute URLs
6. Strip JSX expressions (`{...}`)

### SQLite Schema
```sql
CREATE TABLE posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  blog_url TEXT NOT NULL,
  devto_id INTEGER,
  devto_url TEXT,
  devto_posted_at TEXT,
  hashnode_id TEXT,
  hashnode_url TEXT,
  hashnode_posted_at TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);
```

### CLI Interface
```
cross-poster post <path-to-mdx>          # Post to all platforms
cross-poster post <path> --platform devto # Post to Dev.to only
cross-poster post <path> --dry-run        # Preview sanitized markdown
cross-poster status <slug>                # Show posting status
cross-poster list                         # List all tracked posts
```

### Error Handling
Retry with exponential backoff (3 attempts, 1s/2s/4s). On partial failure, record the success and allow re-running for failed platform. Never re-post to a platform that already has a recorded URL.

### Config
```
DEVTO_API_KEY=
HASHNODE_PAT=
HASHNODE_PUBLICATION_ID=
BLOG_BASE_URL=https://yourblog.com
CROSS_POSTER_DB_PATH=~/.config/myworkflow/cross-poster.db
```

---

## 2. Content Repurposer (`tools/repurpose/`)

**Language: Python** -- Anthropic/OpenAI SDKs are first-class Python.

### File Structure
```
tools/repurpose/
  pyproject.toml
  repurpose/
    __init__.py
    cli.py
    config.py
    engine.py           # LLM API abstraction (Claude or OpenAI)
    prompts/
      twitter_thread.txt
      linkedin_post.txt
      reddit_post.txt
      newsletter.txt
    formats.py          # Output formatting, character limit validation
    output.py           # Write to files or pipe to social queue
  tests/
    test_engine.py
    test_formats.py
  .env.example
```

### Dependencies
- `anthropic` -- Claude API SDK
- `openai` -- fallback
- `click`
- `python-frontmatter`
- `python-dotenv`

### Prompt Strategy (per platform)

**Twitter Thread:** 5-8 key insights, max 280 chars each, hook first tweet, link in last, no hashtags in body.

**LinkedIn Post:** Professional first-person, strong opening (truncates at ~210 chars), 1,300 char sweet spot, generous line breaks, end with question, 3-5 hashtags at bottom.

**Reddit Post:** Humble "sharing knowledge" tone, brief summary, link naturally not promotionally, vary by subreddit type.

**Newsletter:** Personal intro, bullet takeaways, "why this matters", CTA to full post.

### CLI Interface
```
repurpose <path> --all                          # Generate all formats
repurpose <path> --format twitter               # Twitter thread only
repurpose <path> --format linkedin              # LinkedIn post only
repurpose <path> --all --enqueue --at "2026-03-05 10:00"  # Generate + push to social queue
repurpose <path> --all --output ./output/       # Save to files
repurpose <path> --all --provider openai        # Use OpenAI instead of Claude
```

### Error Handling
LLM API calls retry 2 times with 5s delay. Validate output (tweet count, char limits). If validation fails, re-prompt with correction (1 retry). Save raw LLM output for debugging.

### Config
```
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-20250514
BLOG_BASE_URL=https://yourblog.com
```

---

## 3. Social Distribution (`tools/social/`)

**Language: Python** -- PRAW is Python-only, Tweepy is best X v2 client in Python.

### File Structure
```
tools/social/
  pyproject.toml
  social/
    __init__.py
    cli.py
    config.py
    queue.py            # SQLite queue management
    scheduler.py        # Cron drain logic, time-window posting
    platforms/
      __init__.py
      twitter.py        # X API v2 via tweepy (threads + single tweets)
      linkedin.py       # LinkedIn Posts API via httpx
      reddit.py         # PRAW wrapper
    db.py
  tests/
    test_queue.py
    test_twitter.py
    test_linkedin.py
    test_reddit.py
  .env.example
```

### Dependencies
- `tweepy>=4.14` -- X API v2
- `praw>=7.7` -- Reddit
- `httpx` -- LinkedIn API
- `click`, `python-dotenv`

### API Details

**X/Twitter API v2:**
- Endpoint: `POST https://api.twitter.com/2/tweets`
- Auth: OAuth 1.0a (consumer key/secret, access token/secret)
- Thread: post first tweet, capture `id`, use as `in_reply_to_tweet_id` for next
- Free tier: 1,500 tweets/month, write-only
- Rate limit: ~17 tweets/24h on free tier
- Via Tweepy: `client.create_tweet(text="...", in_reply_to_tweet_id="...")`

**LinkedIn Posts API:**
- Endpoint: `POST https://api.linkedin.com/rest/posts`
- Auth: `Bearer {ACCESS_TOKEN}`, headers: `X-Restli-Protocol-Version: 2.0.0`, `Linkedin-Version: 202602`
- OAuth 2.0 scope: `w_member_social`
- Body: `{"author": "urn:li:person:{MEMBER_ID}", "commentary": "...", "visibility": "PUBLIC", "distribution": {"feedDistribution": "MAIN_FEED"}, "lifecycleState": "PUBLISHED"}`
- Rate limit: ~100 API calls/day
- Token refresh needed (60-day expiry for 3-legged tokens)

**Reddit (PRAW):**
- Auth: "script" app at reddit.com/prefs/apps
- Post: `reddit.subreddit("name").submit(title="...", selftext="...")`
- Rate limit: 60 requests/minute

### SQLite Schema
```sql
CREATE TABLE social_queue (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  post_slug TEXT NOT NULL,
  platform TEXT NOT NULL,            -- 'twitter', 'linkedin', 'reddit'
  content_type TEXT NOT NULL,        -- 'single', 'thread', 'article'
  content TEXT NOT NULL,             -- JSON: for threads, array of tweet texts
  subreddit TEXT,                    -- Reddit only
  scheduled_at TEXT NOT NULL,
  status TEXT DEFAULT 'pending',     -- 'pending', 'posted', 'failed', 'cancelled'
  platform_id TEXT,
  platform_url TEXT,
  error_message TEXT,
  attempts INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')),
  posted_at TEXT
);

CREATE INDEX idx_queue_status_scheduled ON social_queue(status, scheduled_at);
```

### CLI Interface
```
social enqueue <slug> --platform twitter --content "Tweet text" --at "2026-03-05 10:00"
social enqueue <slug> --platform twitter --thread tweets.json --at "2026-03-05 10:00"
social enqueue <slug> --platform linkedin --content "Post text" --at "2026-03-05 12:00"
social enqueue <slug> --platform reddit --subreddit programming --content post.md --at "2026-03-05 14:00"
social drain                          # Process all due items in queue
social list [--status pending]        # Show queue
social cancel <id>                    # Cancel a queued post
social retry <id>                     # Retry a failed post
```

### Cron Setup
```
*/15 * * * * cd ~/personal/myworkflow/tools/social && python -m social drain
```

### Error Handling
Max 3 retries with exponential backoff. On permanent failure (auth error, content policy), mark as `failed`. LinkedIn token refresh: `social auth refresh-linkedin` command.

### Config
```
TWITTER_CONSUMER_KEY=
TWITTER_CONSUMER_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_TOKEN_SECRET=
LINKEDIN_ACCESS_TOKEN=
LINKEDIN_MEMBER_ID=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USERNAME=
REDDIT_PASSWORD=
SOCIAL_DB_PATH=~/.config/myworkflow/social.db
```

---

## 4. Newsletter Sender (`tools/newsletter/`)

**Language: Python** -- Resend has first-class Python SDK, FastAPI for endpoints.

### File Structure
```
tools/newsletter/
  pyproject.toml
  newsletter/
    __init__.py
    cli.py
    config.py
    db.py
    models.py
    api.py              # FastAPI: signup/unsubscribe/confirm endpoints
    sender.py           # Resend API integration
    templates/
      base.html         # HTML email base (Jinja2)
      edition.html
      confirm.html
      welcome.html
    renderer.py         # Markdown to HTML
  tests/
    test_sender.py
    test_api.py
    test_renderer.py
  .env.example
```

### Dependencies
- `resend` -- Resend Python SDK
- `fastapi` + `uvicorn` -- signup/unsubscribe API
- `jinja2` -- HTML email templates
- `markdown` or `markdown-it-py` -- markdown to HTML
- `itsdangerous` -- token generation for confirm/unsubscribe links
- `click`, `python-dotenv`

### API Details

**Resend:**
- Endpoint: `POST https://api.resend.com/emails`
- Auth: `Authorization: Bearer re_xxxxxxxxx`
- Body: `{"from": "Newsletter <newsletter@yourdomain.com>", "to": ["sub@email.com"], "subject": "...", "html": "..."}`
- Free tier: 3,000 emails/month, 100/day
- Batch: `POST /emails/batch` (up to 100 per call)

### SQLite Schema
```sql
CREATE TABLE subscribers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  status TEXT DEFAULT 'pending',     -- 'pending', 'confirmed', 'unsubscribed'
  confirm_token TEXT UNIQUE,
  unsubscribe_token TEXT UNIQUE NOT NULL,
  subscribed_at TEXT,
  unsubscribed_at TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE editions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT UNIQUE NOT NULL,
  subject TEXT NOT NULL,
  markdown_content TEXT NOT NULL,
  html_content TEXT,
  sent_at TEXT,
  recipient_count INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE send_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  edition_id INTEGER NOT NULL REFERENCES editions(id),
  subscriber_id INTEGER NOT NULL REFERENCES subscribers(id),
  resend_id TEXT,
  status TEXT DEFAULT 'sent',
  sent_at TEXT DEFAULT (datetime('now'))
);
```

### Double Opt-In Flow
1. User submits email -> `POST /api/subscribe`
2. Creates subscriber `status='pending'`, generates `confirm_token` via `itsdangerous`
3. Sends confirmation email via Resend with link: `https://yourblog.com/api/confirm?token=xxx`
4. User clicks -> `GET /api/confirm?token=xxx`
5. Validates token (24h expiry), sets `status='confirmed'`, sends welcome email

### CLI Interface
```
newsletter send <slug> <path-to-md>     # Send edition
newsletter send <slug> <path> --dry-run # Preview HTML, show recipient count
newsletter send <slug> <path> --test-email me@example.com
newsletter subscribers list
newsletter subscribers count
newsletter subscribers export           # CSV
newsletter serve                        # Start FastAPI server
```

### Error Handling
Batch sending respecting Resend rate limits. If send fails mid-batch, record in `send_log` and allow resume. Prevent duplicate sends.

### Config
```
RESEND_API_KEY=
NEWSLETTER_FROM_EMAIL=newsletter@yourdomain.com
NEWSLETTER_FROM_NAME=Shifat Islam Santo
BLOG_BASE_URL=https://yourblog.com
NEWSLETTER_DB_PATH=~/.config/myworkflow/newsletter.db
NEWSLETTER_SECRET_KEY=
```

---

## 5. Analytics Aggregator (`tools/analytics/`)

**Language: Go** -- Concurrent API fetches, compiled binary, TUI with bubbletea/lipgloss (same pattern as gitpulse).

### File Structure
```
tools/analytics/
  go.mod
  go.sum
  cmd/
    analytics/
      main.go
  internal/
    config/
      config.go
    sources/
      umami.go
      devto.go
      twitter.go        # If Basic tier, otherwise skip
    aggregator/
      aggregator.go
    models/
      stats.go
    dashboard/
      dashboard.go      # TUI rendering
    db/
      db.go             # SQLite historical storage
  .env.example
```

### Dependencies
- `github.com/spf13/cobra` -- CLI
- `github.com/charmbracelet/bubbletea` -- TUI
- `github.com/charmbracelet/lipgloss` -- TUI styling
- `github.com/charmbracelet/bubbles` -- tables, sparklines
- `modernc.org/sqlite` -- pure Go SQLite
- `github.com/joho/godotenv`

### API Details

**Umami (self-hosted):**
- Auth: `POST /api/auth/login` -> JWT token
- Stats: `GET /api/websites/{id}/stats?startAt={ms}&endAt={ms}`
- Pageviews: `GET /api/websites/{id}/pageviews?startAt={ms}&endAt={ms}&unit=day`
- Top pages: `GET /api/websites/{id}/metrics?type=url`
- Active visitors: `GET /api/websites/{id}/active`

**Dev.to:**
- `GET https://dev.to/api/articles/me/published` with `api-key` header
- Returns: `page_views_count`, `positive_reactions_count`, `comments_count`

### SQLite Schema
```sql
CREATE TABLE snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  metric_type TEXT NOT NULL,
  metric_value INTEGER NOT NULL,
  period_start TEXT NOT NULL,
  period_end TEXT NOT NULL,
  metadata TEXT,
  captured_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE article_stats (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT NOT NULL,
  source TEXT NOT NULL,
  views INTEGER DEFAULT 0,
  reactions INTEGER DEFAULT 0,
  comments INTEGER DEFAULT 0,
  captured_at TEXT DEFAULT (datetime('now'))
);
```

### CLI Interface
```
analytics dashboard                  # Interactive TUI
analytics fetch                      # Pull from all sources
analytics fetch --source umami       # Specific source
analytics report --period 7d         # Summary for last 7 days
analytics report --period 30d --format json
analytics top-posts --period 30d
```

### Dashboard Layout
```
+------------------------------------------+
| Blog Analytics - Last 30 Days            |
+------------------------------------------+
| Pageviews: 12,450  | Visitors: 3,210    |
| Bounce Rate: 42%   | Avg Time: 3:45     |
+------------------------------------------+
| Top Pages          | Dev.to Articles     |
| 1. /post-a  1,200  | Post A  450 views  |
| 2. /post-b    890  | Post B  320 views  |
+------------------------------------------+
| Weekly Trend [sparkline chart]           |
+------------------------------------------+
```

### Config
```
UMAMI_BASE_URL=https://umami.yourdomain.com
UMAMI_USERNAME=
UMAMI_PASSWORD=
UMAMI_WEBSITE_ID=
DEVTO_API_KEY=
ANALYTICS_DB_PATH=~/.config/myworkflow/analytics.db
```

---

## Shared Infrastructure

### Common Config Path
All tools: `~/.config/myworkflow/` for SQLite databases. Shared `.env` at `tools/.env` or per-tool `.env`.

### Shared Python Package (`tools/shared/`)
- Common SQLite utilities
- HTTP retry logic with exponential backoff
- Logging configuration
- Blog URL resolution helper

### GitHub Actions Integration
`.github/workflows/cross-post.yml` triggered on push to `main` when `blog/src/data/` changes:
1. Detect new/modified blog post markdown files
2. Run `cross-poster post <path>`
3. Run `repurpose <path> --all --enqueue`
4. VPS cron handles draining social queue

### Package Management
Use `uv` for fast Python dependency management. Each tool installable as `pip install -e ./tools/cross-poster` etc.

---

## Build Order (Calendar)

| Week | Build | Delivers |
|------|-------|----------|
| 1 | Cross-Poster | Automated Dev.to + Hashnode cross-posting |
| 2 | Repurposer | Blog-to-social content generation |
| 2-3 | Social Distribution | Automated X, LinkedIn, Reddit posting |
| 3-4 | Newsletter | Subscriber management + email delivery |
| 4 | Analytics | Unified metrics dashboard |

Sources:
- [DEV API (Forem Docs)](https://developers.forem.com/api/v0)
- [Hashnode GraphQL API](https://apidocs.hashnode.com/)
- [LinkedIn Posts API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api)
- [X API v2 Free Tier](https://devcommunity.x.com/t/list-of-twitter-api-v2-access-endpoints-in-free-tier/198614)
- [Tweepy Docs](https://docs.tweepy.org/en/stable/client.html)
- [PRAW Docs](https://praw.readthedocs.io/en/stable/)
- [Resend API](https://resend.com/docs/api-reference/emails/send-email)
- [Umami API](https://umami.is/docs/api/website-stats)
