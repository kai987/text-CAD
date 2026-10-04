import { createContext, useContext, useEffect, useLayoutEffect, useMemo, useState } from 'react';
import type { Dispatch, ReactNode, SetStateAction } from 'react';
import { readThemePreference, resolveTheme, saveThemePreference } from './theme-preferences';
import type { ResolvedTheme, ThemePreference } from './theme-preferences';

interface ThemeState {
  preference: ThemePreference;
  setPreference: Dispatch<SetStateAction<ThemePreference>>;
  theme: ResolvedTheme;
}
const ThemeContext = createContext<ThemeState | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [preference, setPreference] = useState<ThemePreference>(() => {
    try { return readThemePreference(window.localStorage); }
    catch { return 'system'; }
  });
  const [systemDark, setSystemDark] = useState(() => window.matchMedia('(prefers-color-scheme: dark)').matches);
  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const update = () => setSystemDark(media.matches);
    update();
    media.addEventListener('change', update);
    return () => media.removeEventListener('change', update);
  }, []);
  const theme = resolveTheme(preference, systemDark);
  useLayoutEffect(() => {
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#192331' : '#274d70');
  }, [theme]);
  useEffect(() => {
    try { saveThemePreference(window.localStorage, preference); }
    catch { /* Accessing localStorage itself can throw in embedded browsers. */ }
  }, [preference]);
  const value = useMemo(() => ({ preference, setPreference, theme }), [preference, theme]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const state = useContext(ThemeContext);
  if (!state) throw new Error('ThemeProvider is required.');
  return state;
}
