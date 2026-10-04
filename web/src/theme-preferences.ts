export type ThemePreference = 'system' | 'light' | 'dark';
export type ResolvedTheme = 'light' | 'dark';
export const themeStorageKey = 'text-cad.theme';
export const themePalette = {
  light: { canvasBackground: '#f2f4f7', outline: '#535d68' },
  dark: { canvasBackground: '#131b27', outline: '#424b58' },
} as const;

export function isThemePreference(value: unknown): value is ThemePreference {
  return value === 'system' || value === 'light' || value === 'dark';
}
export function resolveTheme(preference: ThemePreference, systemDark: boolean): ResolvedTheme {
  return preference === 'system' ? systemDark ? 'dark' : 'light' : preference;
}
export function readThemePreference(storage: Pick<Storage, 'getItem'>): ThemePreference {
  try {
    const value = storage.getItem(themeStorageKey);
    return isThemePreference(value) ? value : 'system';
  } catch { return 'system'; }
}
export function saveThemePreference(storage: Pick<Storage, 'setItem'>, preference: ThemePreference): void {
  try { storage.setItem(themeStorageKey, preference); }
  catch { /* Theme switching remains available when storage is blocked. */ }
}
