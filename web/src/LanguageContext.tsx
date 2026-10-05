import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import type { Dispatch, ReactNode, SetStateAction } from 'react';
import { htmlLanguages, messages } from './localization';
import type { Locale } from './localization';
import { readLanguage, saveLanguage } from './language-preferences';

interface LanguageState {
  locale: Locale;
  setLocale: Dispatch<SetStateAction<Locale>>;
  copy: typeof messages[Locale];
}

const LanguageContext = createContext<LanguageState | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>(() => {
    try { return readLanguage(window.localStorage); }
    catch { return 'zh'; }
  });
  const copy = messages[locale];
  useEffect(() => {
    document.documentElement.lang = htmlLanguages[locale];
    try { saveLanguage(window.localStorage, locale); }
    catch { /* Accessing localStorage itself can also throw. */ }
  }, [locale, copy]);
  // Locale updates never recreate the viewer or replace its model state.
  const value = useMemo(() => ({ locale, setLocale, copy }), [locale, copy]);
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const value = useContext(LanguageContext);
  if (!value) throw new Error('LanguageProvider is required.');
  return value;
}
