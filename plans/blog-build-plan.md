# Blog Build Plan: shifatsanto.dev

**Author:** Shifat Islam Santo
**Target:** `/home/oneknight/personal/myworkflow/blog/`
**Framework:** Astro 5.x with Content Layer API
**Deploy:** Cloudflare Pages (free tier)
**Date:** 2026-03-04

---

## 1. File/Folder Structure

```
blog/
  astro.config.mjs
  package.json
  tsconfig.json
  tailwind.config.mjs
  src/
    content.config.ts              # Content collections (Astro 5 location)
    data/
      blog/                        # Blog posts (.mdx/.md files)
        hello-world.mdx
        building-vectorvault.mdx
      research/                    # Independent research pieces (.mdx/.md)
        hnsw-index-benchmarks.mdx
      authors/
        santo.json                 # Author data (file() loader)
    pages/
      index.astro                  # Homepage (hero + recent posts)
      blog/
        index.astro                # Blog listing (paginated)
        [...slug].astro            # Individual blog post
      research/
        index.astro                # Research listing
        [...slug].astro            # Individual research piece
      tags/
        index.astro                # All tags page
        [tag].astro                # Posts filtered by tag
      rss.xml.ts                   # RSS feed endpoint
      og/
        [slug].png.ts              # OG image generation endpoint
      api/
        newsletter.ts              # Newsletter signup endpoint
      404.astro
    layouts/
      BaseLayout.astro             # HTML shell, global meta, fonts
      PostLayout.astro             # Blog post layout (TOC, author bio, reading time)
      ResearchLayout.astro         # Research piece layout
      ListLayout.astro             # Paginated listing layout
    components/
      Head.astro                   # <head> meta, OG tags, canonical, JSON-LD
      Header.astro                 # Nav bar
      Footer.astro                 # Footer with links, copyright
      PostCard.astro               # Card for blog/research listings
      TagList.astro                # Tag pills
      TableOfContents.astro        # Sticky sidebar TOC
      ReadingTime.astro            # "X min read" display
      AuthorBio.astro              # Author section at bottom of posts
      NewsletterForm.astro         # Email signup form (posts to /api/newsletter)
      CrossPostNotice.astro        # "Originally published at" banner
      CodeBlock.astro              # Enhanced code block wrapper (copy button)
      Pagination.astro             # Prev/next page navigation
      JsonLd.astro                 # JSON-LD structured data injection
      ThemeToggle.astro            # Optional light/dark toggle (dark default)
      SearchBar.astro              # Client-side fuzzy search (Fuse.js island)
    styles/
      global.css                   # Tailwind directives, custom properties, prose
    utils/
      reading-time.ts              # Calculate reading time from content
      og-template.tsx              # Satori JSX template for OG images
      seo.ts                       # Helper to build meta/OG/JSON-LD objects
      slugify.ts                   # Consistent slug generation
  public/
    fonts/                         # Self-hosted Inter/JetBrains Mono
    favicon.svg
    robots.txt
```

---

## 2. Key Dependencies

### Core
| Package | Purpose |
|---|---|
| `astro` (^5.x) | Framework |
| `@astrojs/mdx` | MDX support in content collections |
| `@astrojs/sitemap` | Auto-generated sitemap at build |
| `@astrojs/rss` | RSS feed generation |
| `@astrojs/tailwind` | Tailwind CSS integration (or `@tailwindcss/vite` with Tailwind v4) |
| `@astrojs/cloudflare` | Cloudflare Pages adapter (for hybrid mode newsletter endpoint) |

### OG Image Generation
| Package | Purpose |
|---|---|
| `satori` | Convert JSX/HTML+CSS to SVG |
| `@resvg/resvg-js` | Convert SVG to PNG (1200x630) |

### Markdown/MDX Processing
| Package | Purpose |
|---|---|
| `rehype-slug` | Add `id` attributes to headings (for TOC) |
| `rehype-autolink-headings` | Clickable anchor links on headings |
| `reading-time` | Word count to minutes calculation |

### Syntax Highlighting
Built into Astro via Shiki. No extra dependency.

### Search
| Package | Purpose |
|---|---|
| `fuse.js` | Lightweight client-side fuzzy search |

### Dev
| Package | Purpose |
|---|---|
| `typescript` | Type safety |
| `@tailwindcss/typography` | Prose styling for rendered markdown |

---

## 3. Page Routes and Layouts

| Route | File | Layout | Description |
|---|---|---|---|
| `/` | `pages/index.astro` | BaseLayout | Hero + 5 recent posts + CTA |
| `/blog` | `pages/blog/index.astro` | ListLayout | Paginated blog listing |
| `/blog/[slug]` | `pages/blog/[...slug].astro` | PostLayout | Individual blog post |
| `/research` | `pages/research/index.astro` | ListLayout | Research pieces listing |
| `/research/[slug]` | `pages/research/[...slug].astro` | ResearchLayout | Individual research piece |
| `/tags` | `pages/tags/index.astro` | BaseLayout | All tags cloud/grid |
| `/tags/[tag]` | `pages/tags/[tag].astro` | ListLayout | Posts filtered by tag |
| `/rss.xml` | `pages/rss.xml.ts` | none | RSS feed |
| `/og/[slug].png` | `pages/og/[slug].png.ts` | none | Dynamic OG image |
| `/api/newsletter` | `pages/api/newsletter.ts` | none | POST endpoint for signups |

**Layout hierarchy:**
- `BaseLayout` wraps everything: HTML doctype, `<Head>`, `<Header>`, `<slot/>`, `<Footer>`
- `PostLayout` extends BaseLayout: TOC sidebar, reading time, author bio, cross-post notice, prev/next nav, JSON-LD BlogPosting
- `ResearchLayout` extends BaseLayout: JSON-LD ScholarlyArticle, abstract section, citation format
- `ListLayout` extends BaseLayout: pagination, tag filter

---

## 4. Content Schema (Frontmatter Fields)

### Blog Collection (`src/content.config.ts`)

```ts
defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "./src/data/blog" }),
  schema: z.object({
    title: z.string(),
    description: z.string().max(160),
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    tags: z.array(z.string()).default([]),
    category: z.enum(["tutorial", "deep-dive", "opinion", "project", "til"]).default("tutorial"),
    draft: z.boolean().default(false),
    featured: z.boolean().default(false),
    heroImage: z.string().optional(),
    heroAlt: z.string().optional(),
    canonicalUrl: z.string().url().optional(),
    originallyPublishedAt: z.string().optional(),
    originalUrl: z.string().url().optional(),
    series: z.string().optional(),
    seriesOrder: z.number().optional(),
  }),
})
```

### Research Collection

```ts
defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "./src/data/research" }),
  schema: z.object({
    title: z.string(),
    description: z.string().max(160),
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    tags: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
    abstract: z.string().optional(),
    methodology: z.string().optional(),
    status: z.enum(["in-progress", "complete", "archived"]).default("complete"),
    relatedPosts: z.array(z.string()).default([]),
  }),
})
```

### Authors Collection

```ts
defineCollection({
  loader: file("./src/data/authors/santo.json"),
  schema: z.object({
    name: z.string(),
    bio: z.string(),
    avatar: z.string(),
    github: z.string().url(),
    twitter: z.string().url(),
    linkedin: z.string().url(),
    website: z.string().url().optional(),
  }),
})
```

---

## 5. Components

| Component | Type | Notes |
|---|---|---|
| `Head.astro` | Static | Props: title, description, ogImage, canonicalUrl, type. Renders `<meta>`, `<link rel="canonical">`, OG tags, Twitter cards |
| `Header.astro` | Static | Logo/name, nav (Blog, Research, Tags, RSS), responsive hamburger |
| `Footer.astro` | Static | GitHub, X, LinkedIn icons. Copyright |
| `PostCard.astro` | Static | Title, date, description, tags, reading time |
| `TagList.astro` | Static | Clickable tag pills linking to `/tags/[tag]` |
| `TableOfContents.astro` | Static | Parses headings, nested list. Sticky desktop, collapsible mobile |
| `ReadingTime.astro` | Static | Displays computed reading time |
| `AuthorBio.astro` | Static | Photo, name, bio, social links. Bottom of every post |
| `NewsletterForm.astro` | Island (`client:visible`) | Email input + submit. Posts to `/api/newsletter` |
| `CrossPostNotice.astro` | Static | "Originally published at [platform]" if frontmatter set |
| `CodeBlock.astro` | Island (`client:idle`) | Language label + copy-to-clipboard button |
| `Pagination.astro` | Static | Prev/next page links |
| `JsonLd.astro` | Static | Renders `<script type="application/ld+json">` |
| `ThemeToggle.astro` | Island (`client:load`) | Dark default, toggle to light |
| `SearchBar.astro` | Island (`client:idle`) | Fuse.js fuzzy search, dialog/modal UI |

---

## 6. OG Image Approach

Build-time generation using Satori + resvg-js:

1. `src/pages/og/[slug].png.ts` exports `getStaticPaths()` iterating all blog + research entries
2. Satori renders JSX template: title, description, author, tags, dark gradient background
3. resvg-js converts SVG to PNG (1200x630px)
4. `Head.astro` sets `og:image` to `/og/[slug].png`
5. Fallback `/og/default.png` for pages without specific OG image

Fonts: Self-host Inter + JetBrains Mono as `.woff2`, load into Satori via `fs.readFileSync`.

---

## 7. Newsletter Signup Approach

Hybrid SSR endpoint on Cloudflare Pages:

- `POST /api/newsletter` accepts `{ email: string }`
- Server-side email validation
- Rate limits by IP (Cloudflare headers)
- Forwards to newsletter service on Hetzner VPS (or writes to Cloudflare D1/KV)
- Honeypot field for bot protection
- No third-party scripts

Placement: Bottom of every blog post + homepage.

---

## 8. Deployment Config

**Cloudflare Pages:**
- Build command: `npm run build`
- Output: `dist/`
- Node: `NODE_VERSION=20`
- Auto-deploys on push to `main`
- Preview deploys on PRs

**Environment variables:**
- `NEWSLETTER_API_URL` -- Hetzner VPS endpoint
- `NEWSLETTER_API_KEY` -- auth token
- `SITE_URL` -- canonical site URL

**Security headers (`public/_headers`):**
```
/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()

/fonts/*
  Cache-Control: public, max-age=31536000, immutable
```

---

## 9. SEO Checklist

### Per-page:
- [ ] Unique `<title>` ("Post Title | Shifat Santo")
- [ ] `<meta name="description">` from frontmatter (max 160 chars)
- [ ] `<link rel="canonical">` (canonicalUrl if cross-posted, else self-referencing)
- [ ] OG tags: og:title, og:description, og:image, og:url, og:type
- [ ] Twitter cards: summary_large_image, twitter:site, twitter:creator
- [ ] JSON-LD: BlogPosting (posts), ScholarlyArticle (research), WebSite (home), CollectionPage (listings)

### Site-wide:
- [ ] `robots.txt` allowing all crawlers, pointing to sitemap
- [ ] `sitemap-index.xml` auto-generated
- [ ] RSS feed at `/rss.xml`
- [ ] Self-hosted fonts (no Google Fonts)
- [ ] All images have `alt` text
- [ ] Semantic HTML (`<article>`, `<nav>`, `<main>`, `<aside>`, `<time>`)
- [ ] Single `<h1>` per page, sequential heading hierarchy
- [ ] `<html lang="en">`
- [ ] Favicon + apple-touch-icon
- [ ] Zero render-blocking JS (Astro default)
- [ ] Core Web Vitals: LCP < 1.5s, CLS < 0.05, INP < 100ms

---

## 10. Build Order

| Phase | What | Estimate |
|---|---|---|
| 1 | Scaffolding + config + content schema | 2 hrs |
| 2 | BaseLayout + Head + Header + Footer + Tailwind + dark theme | 4 hrs |
| 3 | Blog listing + PostCard + Pagination + post pages + PostLayout | 5 hrs |
| 4 | TOC + ReadingTime + AuthorBio + CrossPostNotice + CodeBlock | 3.5 hrs |
| 5 | Tags system + Research collection + pages | 4 hrs |
| 6 | OG images (Satori + resvg) + RSS + Sitemap | 3.5 hrs |
| 7 | Newsletter form + API endpoint | 2 hrs |
| 8 | Search (Fuse.js island) | 2 hrs |
| 9 | SEO audit (JSON-LD, meta, canonical) | 2 hrs |
| 10 | Cloudflare Pages deploy + polish + Lighthouse | 3 hrs |
| 11 | Write 2-3 seed posts | 3 hrs |
| **Total** | | **~34 hrs** |

---

## 11. Design Decisions

**`output: 'hybrid'` over pure static:** Newsletter endpoint needs server-side processing. If preferred, move endpoint to standalone Cloudflare Worker and keep `output: 'static'`.

**Tailwind + `@tailwindcss/typography`:** `prose` class handles rendered markdown. `prose-invert` for dark theme. Utility classes keep styling co-located.

**Self-hosted fonts:** Eliminates external DNS lookups. Faster LCP. Better privacy. Inter + JetBrains Mono are open-source.

**Satori over Puppeteer for OG:** Runs in Node.js without browser dependency. Faster build. No headless Chrome. Works in Cloudflare build env.

**Content in `src/data/` vs `src/content/`:** Astro 5 Content Layer API with `glob()` loader points to any directory. `src/data/` is the Astro 5+ convention.

Sources:
- [Astro Content Collections Docs](https://docs.astro.build/en/guides/content-collections/)
- [Astro MDX Integration](https://docs.astro.build/en/guides/integrations-guide/mdx/)
- [Astro Cloudflare Deployment](https://docs.astro.build/en/guides/deploy/cloudflare/)
- [OG Images with Satori and Astro](https://dietcode.io/p/astro-og/)
- [JSON-LD Structured Data in Astro](https://johndalesandro.com/blog/astro-add-json-ld-structured-data-to-your-website-for-rich-search-results/)
- [Adding TOC in Astro](https://noahflk.com/blog/astro-table-of-contents)
