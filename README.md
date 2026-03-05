# myworkflow

Personal content pipeline -- from research to published blog posts, social distribution, and newsletter delivery. Built from scratch, no SaaS dependencies.

## Structure

```
myworkflow/
  blog/                  # Astro 5 blog (static, Cloudflare Pages)
  tools/
    content-cli/         # Unified Python CLI (Typer + Rich)
      myworkflow/        #   cross-post, repurpose, social, newsletter
    analytics/           # Go TUI dashboard (Cobra + SQLite)
  research/              # Deep research docs
  plans/                 # Build plans
  .github/workflows/     # CI/CD (deploy + cross-post on merge)
```

## Stack

| Layer | Tech | Cost |
|---|---|---|
| Blog | Astro 5 + MDX | $0 (Cloudflare Pages) |
| Automation | Custom Python/Go services | $0 |
| Newsletter | Resend API + SQLite | $0 (free tier) |
| Analytics | Umami (self-hosted) | $0 |
| AI | Claude/OpenAI API | ~$5-10/mo |
| Infra | Hetzner VPS CX22 | ~$4/mo |
