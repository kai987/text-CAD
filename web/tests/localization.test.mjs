import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { locales, messages, resolveLocale, htmlLanguages } from '../src/localization.ts';
import { languageStorageKey, readLanguage, saveLanguage } from '../src/language-preferences.ts';

function leaves(value, prefix = '') {
  return Object.entries(value).flatMap(([key, item]) => {
    const path = prefix ? `${prefix}.${key}` : key;
    return typeof item === 'string' ? [[path, item]] : leaves(item, path);
  });
}
const placeholders = text => [...text.matchAll(/\{(\w+)\}/g)].map(match => match[1]).sort();

test('all three languages cover the same nonempty strings and template arguments', () => {
  assert.deepEqual(locales, ['zh', 'ja', 'en']);
  const reference = new Map(leaves(messages.zh));
  for (const locale of locales) {
    const translated = new Map(leaves(messages[locale]));
    assert.deepEqual([...translated.keys()].sort(), [...reference.keys()].sort(), locale);
    for (const [key, text] of translated) {
      assert.ok(text.trim(), `${locale}.${key} is missing`);
      assert.deepEqual(placeholders(text), placeholders(reference.get(key)), `${locale}.${key}`);
    }
  }
  assert.deepEqual(htmlLanguages, { zh: 'zh-CN', ja: 'ja', en: 'en' });
});

test('persisted language is validated and storage failures keep the viewer usable', () => {
  for (const locale of locales) {
    assert.equal(resolveLocale(locale), locale);
    let stored = null;
    const storage = {
      getItem(key) { assert.equal(key, languageStorageKey); return stored; },
      setItem(key, value) { assert.equal(key, languageStorageKey); stored = value; },
    };
    saveLanguage(storage, locale);
    assert.equal(readLanguage(storage), locale);
  }
  for (const invalid of [null, '', 'EN', 'fr', '__proto__', 'constructor']) assert.equal(resolveLocale(invalid), 'zh');
  assert.equal(readLanguage({ getItem() { throw new Error('Storage disabled'); } }), 'zh');
  assert.doesNotThrow(() => saveLanguage({ setItem() { throw new Error('Storage full'); } }, 'en'));
});

test('original plan rooms and every recorded assumption have translations', async () => {
  const plan = JSON.parse(await readFile(new URL('../../output/review/design_manifest.json', import.meta.url), 'utf8'));
  const model = JSON.parse(await readFile(new URL('../../output/review/house_3d_assumptions_R01.json', import.meta.url), 'utf8'));
  const ids = new Set(plan.floors.flatMap(floor => floor.rooms.map(room => room.id)));
  for (const locale of locales) {
    for (const id of ids) assert.ok(messages[locale].rooms[id], `${locale}.${id}`);
    assert.equal(messages[locale].assumptions.length, plan.assumptions.length + model.assumptions.length, locale);
  }
});
