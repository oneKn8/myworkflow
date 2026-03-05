"""Platform-specific prompt templates for content repurposing."""

TWITTER_PROMPT = """You are a developer content writer. Convert this blog post into a Twitter/X thread (3-7 tweets).

Rules:
- Each tweet must be under 280 characters
- First tweet should hook the reader
- Last tweet should link back to the full post
- Use line breaks between tweets, separated by ---
- No hashtags (they reduce engagement)
- Write in first person, conversational tone
- Include the blog URL exactly as-is in the last tweet: {blog_url}

Title: {title}

Post content:
{body}

Output only the thread tweets separated by ---"""

LINKEDIN_PROMPT = """You are a developer content writer. Convert this blog post into a LinkedIn post.

Rules:
- 1200-1500 characters max
- Start with a hook (first 2 lines visible before "see more")
- Use short paragraphs and line breaks for readability
- End with a question to encourage engagement
- Professional but not corporate tone -- sound like a real person sharing what they built
- Avoid buzzwords, "excited to share", or anything that reads like a press release
- Include the blog URL exactly as-is at the end: {blog_url}

Title: {title}

Post content:
{body}

Output only the LinkedIn post text."""

REDDIT_PROMPT = """You are a developer writing a Reddit post. Convert this blog post into a Reddit-style text post.

Rules:
- Title should be informative, not clickbaity -- write what you'd click on in r/programming
- Body should be a concise summary (300-500 words)
- Include key findings/takeaways upfront
- End with "Full post: {blog_url}"
- Write for a technical audience
- No marketing language, no self-promotion vibes
- Sound like you're sharing something useful, not selling

Title: {title}

Post content:
{body}

Output format:
TITLE: [reddit title]
---
BODY: [reddit body]"""

DEVTO_TEASER_PROMPT = """You are a developer content writer. Write a short teaser/summary for Dev.to that will appear in the post listing.

Rules:
- 2-3 sentences max
- Highlight the key problem or insight
- Make the reader want to click through

Title: {title}

Post content:
{body}

Output only the teaser text."""

PROMPTS = {
    "twitter": TWITTER_PROMPT,
    "linkedin": LINKEDIN_PROMPT,
    "reddit": REDDIT_PROMPT,
    "devto-teaser": DEVTO_TEASER_PROMPT,
}
