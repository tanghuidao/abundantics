import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';

export async function GET(context: APIContext) {
  const posts = await getCollection('research', ({ data }) => !data.draft);
  const sorted = posts.sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf());

  return rss({
    title: 'Abundantics · 丰裕学',
    description: 'Post-Scarcity Social Science: Theory, Models, and Evidence. TEPI index and research articles.',
    site: context.site ?? 'https://abundantics.pages.dev',
    items: sorted.map((post) => ({
      title: post.data.title,
      description: post.data.description ?? '',
      pubDate: post.data.date,
      link: `/${post.data.lang}/research/${post.slug.replace(/^(zh|en)\//, '')}/`,
    })),
    customData: '<language>zh-CN</language>',
  });
}
