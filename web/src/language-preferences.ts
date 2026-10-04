import { resolveLocale } from './localization.ts';
import type { Locale } from './localization.ts';

export const languageStorageKey = 'text-cad.locale';

// Storage can be unavailable in private browsers or embedded viewers.
export function readLanguage(storage: Pick<Storage, 'getItem'>): Locale {
  try { return resolveLocale(storage.getItem(languageStorageKey)); }
  catch { return resolveLocale(null); }
}

export function saveLanguage(storage: Pick<Storage, 'setItem'>, locale: Locale): void {
  try { storage.setItem(languageStorageKey, locale); }
  catch { /* The current language still works when persistence is unavailable. */ }
}
