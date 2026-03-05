import { defineCollection, z } from "astro:content";
import { glob, file } from "astro/loaders";

const blog = defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "./src/data/blog" }),
  schema: z.object({
    title: z.string(),
    description: z.string().max(160),
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    tags: z.array(z.string()).default([]),
    category: z
      .enum(["tutorial", "deep-dive", "opinion", "project", "til"])
      .default("tutorial"),
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
});

const research = defineCollection({
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
    status: z
      .enum(["in-progress", "complete", "archived"])
      .default("complete"),
    relatedPosts: z.array(z.string()).default([]),
  }),
});

const authors = defineCollection({
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
});

export const collections = { blog, research, authors };
