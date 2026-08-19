/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Terminal (dark) theme
        'term-bg': '#0A0A0B',
        'term-fg': '#F5F2EA',
        'term-muted': '#6B6862',
        'term-card': '#131316',
        'term-border': '#2A2A2E',
        'accent-red': '#C8402A',
        // Prose (light) theme
        'prose-bg': '#FAF8F3',
        'prose-fg': '#1A1A18',
        'prose-muted': '#6B6862',
        'prose-border': '#E5E1D8',
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        serif: ['"Noto Serif SC"', 'ui-serif', 'Georgia', 'serif'],
      },
      maxWidth: {
        prose: '68ch',
      },
      lineHeight: {
        relaxed: '1.8',
      },
    },
  },
  plugins: [],
};
