# Personal Content Automation System: Tech Stack Research (March 2026)

## Executive Summary

This research covers the full stack for a solo developer building their own content automation system: blog engine, workflow automation, social media APIs, content management, analytics, and architecture. The recommended stack is **Astro + n8n + Markdown/Git + Umami**, with targeted API integrations for distribution.

---

## 1. Blog Engine Comparison (2026)

### Recommendation: Astro

Astro is the clear winner for developer blogs in 2026. It is purpose-built for content-focused sites, ships zero JavaScript by default via its "Islands Architecture," and has first-class MDX support with Content Collections.

### Head-to-Head Comparison

| Feature | Astro | Next.js | Hugo | 11ty | Gatsby |
|---|---|---|---|---|---|
| **Build Speed** | Fast (5x faster Markdown in v5) | Moderate | Fastest (ms-level) | Fast | Slow |
| **MDX Support** | Native, first-class | Native | No (Goldmark Markdown) | Plugin-based | Native |
| **JS Shipped** | Zero by default (Islands) | Heavy (React runtime) | Zero | Zero | Heavy (React runtime) |
| **Content Collections** | Built-in typed API | Manual or CMS | Built-in taxonomy | Collections plugin | GraphQL layer |
| **RSS** | @astrojs/rss (MDX needs Container API workaround) | Manual implementation | Built-in | Plugin | Plugin |
| **SEO** | Auto sitemaps, meta components | Manual or next-seo | Built-in | Manual | gatsby-plugin-seo |
| **Learning Curve** | Low (HTML-like .astro files) | Medium (React required) | Medium (Go templates) | Low | High |
| **Framework Lock-in** | None (use React/Vue/Svelte/none) | React only | None | None | React only |
| **Ecosystem Maturity** | Growing rapidly | Very mature | Very mature | Mature | Declining |

### Key Details

**Astro (Winner)**
- Content Layer API caches parsed content between builds, only reprocesses changed files
- Astro 5.0: 5x faster Markdown builds, 2x faster MDX builds, 25-50% reduced memory
- Automatic sitemaps, RSS feeds, pagination
- Use any UI framework or none at all
- Ideal deployment: Cloudflare Pages (free, fast) or Vercel

**Hugo (Runner-up for pure speed)**
- Fastest builds by far (milliseconds for thousands of pages)
- No MDX -- uses Goldmark Markdown with shortcodes
- Kubernetes docs site uses Hugo for thousands of pages
- Best if you want zero JavaScript and pure Markdown

**Next.js (Only if you need app features)**
- ISR, server components, API routes -- overkill for a blog
- Ships React runtime to every page
- Choose only if the blog is part of a larger web application

**11ty (Honorable mention)**
- Minimal, flexible, zero-config
- Good for developers who want maximum control with minimal framework
- Smaller community than Astro

**Gatsby (Avoid)**
- Declining ecosystem, slow builds, heavy GraphQL layer
- Most developers have migrated away by 2026

### Deployment Platforms

| Platform | Free Tier | Edge Network | Build Speed | Best For |
|---|---|---|---|---|
| **Cloudflare Pages** | Unlimited sites, 500 builds/mo | Global (fastest) | Fast | Cost-conscious, performance |
| **Vercel** | Hobby plan, 100GB bandwidth | Global | Fastest (native Astro support) | DX-focused, preview deploys |
| **Netlify** | 100GB bandwidth, 300 build min | Global | Good | Established, form handling |

---

## 2. Self-Hosted Automation Platform

### Recommendation: n8n (self-hosted)

For a solo developer building content automation workflows, n8n offers the best balance of visual editing, pre-built integrations (400+), and extensibility.

### Detailed Comparison

| Criteria | n8n | Windmill | Temporal |
|---|---|---|---|
| **Architecture** | Node.js + Vue.js frontend | Rust binary + PostgreSQL | Java/Go server + event sourcing |
| **Idle Memory** | ~516MB | ~287MB (most efficient) | ~832MB (heaviest) |
| **DB Writes/Workflow** | 50-100 | 5-10 (batch-optimized) | 200+ (event sourcing) |
| **Storage after 10K workflows** | 18GB | 4.2GB | 47GB |
| **Pre-built Integrations** | 400+ | ~50 | 0 (code-only) |
| **Visual Editor** | Excellent drag-and-drop | Good, script-focused | None |
| **Code Support** | JavaScript/Python in nodes | Python, Go, TypeScript, Bash | Go, Java, Python, TypeScript |
| **Failure Recovery** | Manual restart needed | Auto-retry from checkpoint (<5s) | Deterministic replay (immediate) |
| **License** | Sustainable Use License | AGPL-3.0 | MIT/Apache-2.0 |
| **Best For** | API glue, SaaS automation | Polyglot scripts, internal tools | Mission-critical, exactly-once |
| **4GB VPS Viable?** | Yes (tight) | Yes (comfortable) | Marginal |

### Why n8n for Content Automation

1. **490+ social media workflow templates** ready to import
2. **Visual workflow builder** makes iteration fast
3. **Pre-built nodes** for Twitter/X, LinkedIn, RSS, webhooks, HTTP, OpenAI, etc.
4. **Cron triggers** for scheduled content distribution
5. **Community templates** specifically for blog-to-social-media pipelines

### n8n Content Distribution Workflow Architecture

```
[Blog Published] --> [Webhook/RSS Trigger]
        |
        v
[Fetch Post Content] --> [AI Repurpose (OpenAI/Claude)]
        |
        +--> [Twitter/X Post]
        +--> [LinkedIn Post]
        +--> [Reddit Post (via PRAW/HTTP)]
        +--> [Dev.to Cross-post]
        +--> [Hashnode Cross-post]
        +--> [Buffer/Schedule Queue]
```

### n8n Self-Hosting Requirements

- Minimum: 2 vCPU, 4GB RAM VPS (Hetzner CPX21 ~$7/mo)
- Docker Compose deployment
- PostgreSQL + Redis
- Set `EXECUTIONS_DATA_PRUNE=true` to manage storage

### When to Choose Windmill Instead

- If running on a very constrained VPS (uses half the memory of n8n)
- If you prefer writing TypeScript/Python scripts over visual flows
- If you want AGPL open-source license vs n8n's Sustainable Use License

### When to Choose Temporal Instead

- Never, for this use case. Temporal is for payment systems and mission-critical business processes, not content distribution.

---

## 3. API Integrations

### Twitter/X API v2

| Tier | Price | Posts/Month | Read Access | Notes |
|---|---|---|---|---|
| **Free** | $0 | 1,500 | None | Write-only, 1 app |
| **Basic** | $200/mo | 10,000 | Yes | 2 app environments |
| **Pro** | $5,000/mo | 1,000,000 | Full | 3 app environments |

- Authentication: OAuth 2.0 (recommended for all new development)
- Free tier is sufficient for most solo developer content automation (1,500 posts/month)
- Pay-per-use model in closed beta as of late 2025
- n8n has a native Twitter/X node

### LinkedIn API

- **Endpoint**: Posts API via `https://api.linkedin.com/v2/posts`
- **Auth**: OAuth 2.0 with scopes `w_member_social`, `r_liteprofile`
- **Setup**: Create app at LinkedIn Developers Portal
- **Gotcha**: LinkedIn requires app review for production access; the "Community Management" product must be requested
- **Rate limits**: 100 API calls per day for most endpoints
- n8n has a native LinkedIn node

### Reddit API (PRAW)

- **Library**: PRAW (Python Reddit API Wrapper), supports Python 3.9+
- **Auth**: Create app at reddit.com/prefs/apps (script type for personal use)
- **Posting**: `subreddit.submit(title, selftext=body)` or `url` for link posts
- **Cost**: Free for personal/bot use; moderator tools exempt from paid tiers
- **Rate limit**: 60 requests/minute
- **Caution**: Subreddit rules vary; automated posting can trigger spam filters. Post thoughtfully.
- n8n can call PRAW via Python function nodes or HTTP requests to Reddit API directly

### Dev.to API

- **Endpoint**: `POST https://dev.to/api/articles`
- **Auth**: API key from dev.to/settings/extensions, sent as `api-key` header
- **Canonical URL**: Set `canonical_url` field to point back to your blog
- **Tags**: Maximum 4 tags, lowercase, no special characters
- **Rate limiting**: HTTP 429 responses possible; implement backoff

### Hashnode API

- **Endpoint**: GraphQL at `https://gql.hashnode.com`
- **Auth**: Personal Access Token from hashnode.com/settings/developer
- **Publication ID**: Required; retrieve via GraphQL query
- **Canonical URL**: Use `originalArticleURL` field
- **Tags**: Structured as objects with `name` and `slug`

### Medium

- **No API available for programmatic publishing** (deprecated)
- **Workaround**: Use "Import a story" feature manually -- paste your post URL, Medium imports content and auto-sets canonical URL
- **Alternative**: Use Medium's RSS import or third-party tools like Postiz

### OpenAI / Claude API (Content Repurposing)

- Use for: Converting blog posts into tweets, LinkedIn posts, Reddit summaries
- OpenAI: `gpt-4o` or `gpt-4o-mini` for cost-effective repurposing
- Claude: `claude-sonnet-4-20250514` for high-quality content transformation
- n8n has native OpenAI and HTTP nodes (Claude via HTTP/Anthropic node)
- Typical workflow: Feed blog post content --> prompt to generate platform-specific versions

### Unified API Alternatives

If managing individual APIs is too much overhead:

- **Postiz** (self-hosted, open-source): All-in-one social media scheduling with API
- **Late (getlate.dev)**: Unified API for posting to 11+ platforms, starts ~$200/mo
- **Ayrshare**: REST API for multiple platforms, handles OAuth complexity

---

## 4. Database and Content Management

### Recommendation: Markdown + Git (for a solo dev blog)

For a solo developer, a headless CMS adds operational complexity without proportional benefit. Markdown + Git is the optimal choice.

### Why Markdown + Git Wins for Solo Dev

| Factor | Markdown + Git | Headless CMS |
|---|---|---|
| **Complexity** | Zero infrastructure | Database, API server, admin UI |
| **Cost** | $0 | $0-$99/mo (hosting CMS) |
| **Version Control** | Native (git history) | CMS-specific, often limited |
| **Portability** | Universal format | Vendor-specific schemas |
| **Backup** | Git remote = backup | Separate backup strategy needed |
| **Editor** | VS Code, Obsidian, any text editor | CMS admin panel |
| **Build Integration** | Native with Astro Content Collections | API calls at build time |
| **Offline Editing** | Full support | Usually requires connection |

### When You DO Need a Headless CMS

If you later need a non-technical editor, visual previews, or structured content beyond blog posts:

| CMS | Best For | Database | Self-Host | License |
|---|---|---|---|---|
| **Payload CMS** | Developer-first, Next.js native | MongoDB, PostgreSQL, SQLite | Yes | MIT |
| **Strapi** | Quick setup, plugin ecosystem | PostgreSQL, MySQL, SQLite | Yes | MIT (CE) |
| **Sanity** | Real-time collaboration, GROQ queries | Hosted (Sanity Cloud) | No | Proprietary |

**Payload CMS** is the strongest choice if you eventually need a CMS:
- Configuration-as-code approach
- Field-level access control
- Next.js native (same stack as your app)
- Completely free and open-source
- Supports MongoDB, PostgreSQL, and SQLite

**Strapi** is the fallback if you want a more polished admin UI out of the box with a larger plugin marketplace.

### Git-Based CMS Options (Middle Ground)

- **TinaCMS**: Visual editing for Git-backed Markdown/MDX, works with Next.js and Astro
- **Outstatic**: Stores content as Markdown in your repo with a lightweight editing UI
- **Decap CMS** (formerly Netlify CMS): Simple Git-gateway editor

---

## 5. Analytics

### Recommendation: Umami (self-hosted)

| Tool | Type | Self-Host Cost | Complexity | Features |
|---|---|---|---|---|
| **Umami** | Web analytics | Free (unlimited) | Low (Node.js + PostgreSQL) | Pageviews, referrers, UTM, events |
| **Plausible** | Web analytics | Free (self-host) / from 9 EUR/mo (cloud) | Low | Privacy-first, clean dashboard |
| **PostHog** | Product analytics | Free (self-host, complex) | High (Postgres + Redis + ClickHouse + Kafka) | Analytics + feature flags + experiments + surveys |

### Why Umami

- **Free forever** when self-hosted, unlimited sites and events
- **Lightweight**: Single Node.js process + PostgreSQL (you already have PostgreSQL for n8n)
- **Privacy-first**: No cookies, GDPR compliant by default
- **Simple setup**: Docker Compose, minimal config
- **Cloud option**: Free for first 1M events/month if you don't want to self-host
- **API access**: Query analytics data programmatically

### When to Choose Plausible

- If you prefer a slightly more polished dashboard
- If you want paid cloud hosting without self-host overhead (starts at 9 EUR/month)

### When to Choose PostHog

- Only if you're building a SaaS product alongside the blog and need feature flags, A/B testing, session replay
- Overkill for a developer blog
- Self-hosting requires significant infrastructure (ClickHouse, Kafka)

### Social Media Analytics APIs

- **Twitter/X**: Analytics available on Basic tier ($200/mo) and above
- **LinkedIn**: Analytics API available with Marketing Developer Platform access
- **Dev.to**: Article analytics via API (views, reactions, comments)
- **Hashnode**: Analytics via GraphQL API
- Track social performance in a simple PostgreSQL table or Google Sheet via n8n

---

## 6. Architecture: Wiring It All Together

### Recommended Stack Summary

```
CONTENT LAYER
  - Astro (blog engine) + MDX + Content Collections
  - Markdown files in Git repository
  - Deployed to Cloudflare Pages (free)

AUTOMATION LAYER
  - n8n (self-hosted on Hetzner VPS, ~$7/mo)
  - PostgreSQL (shared with Umami)
  - Docker Compose for all services

DISTRIBUTION LAYER
  - n8n workflows triggered by:
    1. Git webhook on blog deploy
    2. RSS feed polling
    3. Scheduled cron jobs
  - API integrations: X, LinkedIn, Reddit, Dev.to, Hashnode
  - AI repurposing via OpenAI/Claude API

ANALYTICS LAYER
  - Umami (self-hosted, shares PostgreSQL with n8n)
  - Social platform native analytics
  - n8n workflow to aggregate metrics weekly

INFRASTRUCTURE
  - Single Hetzner VPS: 4GB RAM, ~$7/mo
    - n8n (Docker)
    - Umami (Docker)
    - PostgreSQL (Docker, shared)
  - Cloudflare Pages: Blog hosting (free)
  - Git repo: Content storage + CI/CD (free)
```

### Workflow: Blog Post to Multi-Platform Distribution

```
1. Write post in MDX in VS Code/Obsidian
2. Git push to main branch
3. Cloudflare Pages auto-deploys blog
4. n8n webhook fires on deploy (or polls RSS feed)
5. n8n fetches new post content
6. n8n sends content to Claude/OpenAI API:
   - Generate tweet thread (280 char chunks)
   - Generate LinkedIn post (professional tone)
   - Generate Reddit summary (community-appropriate)
7. n8n posts to each platform via their APIs:
   - Twitter/X: Free tier (1,500 posts/mo)
   - LinkedIn: Posts API
   - Reddit: PRAW or HTTP
   - Dev.to: REST API with canonical URL
   - Hashnode: GraphQL with originalArticleURL
8. n8n logs results to PostgreSQL tracking table
9. Weekly n8n cron: Aggregate analytics, send digest email
```

### Monthly Cost Estimate

| Service | Cost |
|---|---|
| Hetzner VPS (CPX21: 3 vCPU, 4GB RAM) | ~$7/mo |
| Cloudflare Pages | $0 |
| GitHub/GitLab repo | $0 |
| Twitter/X API (Free tier) | $0 |
| LinkedIn API | $0 |
| Reddit API | $0 |
| Dev.to API | $0 |
| Hashnode API | $0 |
| OpenAI API (content repurposing) | ~$5-15/mo |
| Domain name | ~$1/mo (amortized) |
| **Total** | **~$13-23/mo** |

### Key Implementation Tips

1. **Always set canonical URLs** when cross-posting. Every platform supports it. Without it, Google ranks the platform version higher than your original.

2. **Content sanitization pipeline**: MDX components must be stripped/converted to portable Markdown before cross-posting. Strip imports, custom React components, convert figure/image elements to standard Markdown, resolve relative image paths to absolute URLs.

3. **Rate limiting**: Implement backoff for all API calls. Dev.to returns 429s; Twitter has strict per-app limits.

4. **Tracking**: Maintain a JSON file or database table mapping each post to its cross-posted IDs/URLs per platform to avoid duplicate posting.

5. **Stagger distribution**: Don't post everywhere simultaneously. Schedule: blog first, then Twitter (same day), LinkedIn (next day), Dev.to/Hashnode (2-3 days later), Reddit (when relevant discussion appears).

6. **n8n encryption key**: Back up your n8n encryption key. Losing it means re-entering all API credentials.

7. **GitHub Actions alternative**: For cross-posting specifically (Dev.to, Hashnode), a GitHub Actions workflow triggered on blog content changes can replace n8n for that specific workflow. Use n8n for social media posting where scheduling and AI repurposing add value.

---

## Sources

- [Hygraph: Top 12 SSGs in 2026](https://hygraph.com/blog/top-12-ssgs)
- [CloudCannon: Top Five SSGs for 2025](https://cloudcannon.com/blog/the-top-five-static-site-generators-for-2025-and-when-to-use-them/)
- [Hugo vs Astro Showdown](https://criztec.com/hugo-vs-astro/)
- [Astro Content Collections Guide 2026](https://inhaq.com/blog/getting-started-with-astro-content-collections.html)
- [Astro February 2026 Updates](https://astro.build/blog/whats-new-february-2026/)
- [n8n vs Windmill vs Temporal](https://blog.arcbjorn.com/workflow-automation)
- [Top 5 n8n Alternatives 2026](https://dev.to/lightningdev123/top-5-n8n-alternatives-in-2026-choosing-the-right-workflow-automation-tool-54oi)
- [Windmill vs n8n 2026](https://hostadvice.com/blog/ai/automation/n8n-vs-windmill/)
- [n8n Social Media Workflow Templates](https://n8n.io/workflows/categories/social-media/)
- [X API Pricing 2026](https://getlate.dev/blog/twitter-api-pricing)
- [X API Guide 2026](https://getlate.dev/blog/x-api)
- [LinkedIn Posts API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api)
- [Cross-Publishing to Dev.to, Hashnode, Medium](https://www.nvarma.com/blog/2026-02-10-cross-publishing-blog-posts-devto-hashnode-medium/)
- [PRAW Documentation](https://praw.readthedocs.io/en/stable/getting_started/quick_start.html)
- [Postiz Self-Hosted Social Scheduling](https://postiz.com/)
- [Payload CMS vs Strapi vs Sanity](https://kernelics.com/blog/headless-cms-comparison-guide)
- [Payload CMS vs Other Platforms 2026](https://shakuro.com/blog/payload-vs-other-cms)
- [Solopreneur Analytics Stack 2026](https://f3fundit.com/the-solopreneur-analytics-stack-2026-posthog-vs-plausible-vs-fathom-analytics-and-why-you-should-ditch-google-analytics/)
- [Self-Hosted Analytics Comparison](https://medium.com/@coders.stop/setting-up-self-hosted-analytics-posthog-plausible-umami-comparison-ac4e7e826486)
- [Umami vs Plausible vs Matomo](https://aaronjbecker.com/posts/umami-vs-plausible-vs-matomo-self-hosted-analytics/)
- [Best Open Source Analytics 2026](https://openpanel.dev/articles/open-source-web-analytics)
