import { defineCollection, z } from 'astro:content';

const research = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    lang: z.enum(['zh', 'en']),
    translation: z.string().optional(),
    draft: z.boolean().default(false),
    description: z.string().optional(),
  }),
});

const docs = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    lang: z.enum(['zh', 'en']),
    version: z.string().default('0.1'),
    lastUpdated: z.coerce.date().optional(),
  }),
});

export const collections = { research, docs };
