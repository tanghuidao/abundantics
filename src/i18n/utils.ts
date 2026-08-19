import zh from './zh.json';
import en from './en.json';

export type Locale = 'zh' | 'en';

const translations: Record<Locale, typeof zh> = { zh, en };

export function getTranslations(locale: Locale) {
  return translations[locale];
}

export function getOppositeLocale(locale: Locale): Locale {
  return locale === 'zh' ? 'en' : 'zh';
}

export function getOppositeLocalePath(currentPath: string, locale: Locale): string {
  const other = getOppositeLocale(locale);
  return currentPath.replace(`/${locale}/`, `/${other}/`).replace(`/${locale}`, `/${other}`);
}

export function localizePath(locale: Locale, path: string): string {
  if (path === '/') return `/${locale}/`;
  return `/${locale}${path}`;
}

export function getNavItems(locale: Locale) {
  const t = getTranslations(locale);
  return [
    { label: t.nav.home, href: localizePath(locale, '/') },
    { label: t.nav.index, href: localizePath(locale, '/index/') },
    { label: t.nav.abundantics, href: localizePath(locale, '/abundantics/') },
    { label: t.nav.research, href: localizePath(locale, '/research/') },
    { label: t.nav.data, href: localizePath(locale, '/data/') },
    { label: t.nav.about, href: localizePath(locale, '/about/') },
  ];
}

export function isActive(currentPath: string, itemHref: string): boolean {
  const cleanPath = currentPath.replace(/\/$/, '') || '/';
  const cleanHref = itemHref.replace(/\/$/, '') || '/';
  if (cleanHref === cleanPath) return true;
  return cleanPath.startsWith(cleanHref + '/');
}
