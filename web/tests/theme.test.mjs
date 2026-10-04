import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { runInNewContext } from 'node:vm';
import { isThemePreference, resolveTheme, readThemePreference, saveThemePreference, themeStorageKey } from '../src/theme-preferences.ts';

test('system preference responds to appearance changes while explicit choices stay fixed', () => {
  assert.equal(resolveTheme('system', false), 'light');
  assert.equal(resolveTheme('system', true), 'dark');
  for (const systemDark of [false, true]) {
    assert.equal(resolveTheme('light', systemDark), 'light');
    assert.equal(resolveTheme('dark', systemDark), 'dark');
  }
});

test('invalid or inaccessible storage falls back to system and never prevents switching', () => {
  for (const value of ['system', 'light', 'dark']) {
    assert.ok(isThemePreference(value));
    let saved = null;
    const storage = {
      getItem(key) { assert.equal(key, themeStorageKey); return saved; },
      setItem(key, item) { assert.equal(key, themeStorageKey); saved = item; },
    };
    saveThemePreference(storage, value);
    assert.equal(readThemePreference(storage), value);
  }
  for (const value of [null, 'Dark', 'auto', '__proto__', '']) {
    assert.equal(isThemePreference(value), false);
    assert.equal(readThemePreference({ getItem: () => value }), 'system');
  }
  assert.equal(readThemePreference({ getItem() { throw new Error('Blocked'); } }), 'system');
  assert.doesNotThrow(() => saveThemePreference({ setItem() { throw new Error('Full'); } }, 'dark'));
});

test('first-paint initialization matches runtime resolution, including unavailable storage', async () => {
  const html = await readFile(new URL('../index.html', import.meta.url), 'utf8');
  const bootstrap = html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
  assert.ok(bootstrap);
  for (const saved of [null, 'system', 'light', 'dark', 'invalid']) for (const systemDark of [false, true]) {
    const root = { dataset: {}, style: {} };
    runInNewContext(bootstrap, { localStorage: { getItem: () => saved }, matchMedia: () => ({ matches: systemDark }), document: { documentElement: root } });
    const preference = isThemePreference(saved) ? saved : 'system';
    assert.equal(root.dataset.theme, resolveTheme(preference, systemDark));
    assert.equal(root.style.colorScheme, root.dataset.theme);
  }
  const root = { dataset: {}, style: {} };
  runInNewContext(bootstrap, { localStorage: { getItem() { throw new Error('Blocked'); } }, matchMedia: () => ({ matches: true }), document: { documentElement: root } });
  assert.equal(root.dataset.theme, 'dark');
});
