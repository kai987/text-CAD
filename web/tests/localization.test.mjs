import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { locales, messages, resolveLocale, htmlLanguages, selectionLabel } from '../src/localization.ts';
import { languageStorageKey, readLanguage, saveLanguage } from '../src/language-preferences.ts';
import { modelCopy } from '../src/model-copy.ts';
import { modelLayouts } from '../src/model-state.ts';

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

test('apartment copy covers its own rooms and every recorded assumption in all three languages', async () => {
  const apartment = JSON.parse(await readFile(new URL('../../output/review/apartment_2ldk_manifest.json', import.meta.url), 'utf8'));
  const reference = new Map(leaves(modelCopy(messages.zh, 'zh', 'apartment')));
  for (const locale of locales) {
    const copy = modelCopy(messages[locale], locale, 'apartment');
    const translated = new Map(leaves(copy));
    assert.deepEqual([...translated.keys()].sort(), [...reference.keys()].sort());
    for (const [key, text] of translated) {
      assert.ok(text.trim(), `${locale}.${key}`);
      assert.deepEqual(placeholders(text), placeholders(reference.get(key)), `${locale}.${key}`);
    }
    for (const room of apartment.floors[0].rooms) assert.ok(copy.rooms[room.id], `${locale}.${room.id}`);
    assert.equal(copy.assumptions.length, apartment.assumptions.length, locale);
    assert.match(copy.app.title, /2LDK/);
    assert.notEqual(copy.plan.title, messages[locale].plan.title);
  }
});
test('attic controls translate groups, parts, preset and the deployed ladder limitation', () => {
  for (const locale of locales) {
    const copy = messages[locale];
    for (const group of modelLayouts.house.groups) assert.ok(selectionLabel(copy, group.id)?.trim(), `${locale}: ${group.id}`);
    for (const part of modelLayouts.house.parts) assert.ok(selectionLabel(copy, part.id)?.trim(), `${locale}: ${part.id}`);
    assert.ok(copy.presets.attic.trim());
    assert.ok(copy.model.atticNote.trim());
    assert.notEqual(copy.groups.attic, copy.groups.roof);
    assert.notEqual(copy.groups.attic_access, copy.groups.stairs);
    assert.deepEqual(modelLayouts.apartment.groups.map(group => group.id), ['F1', 'ceiling', 'balcony']);
    assert.ok(modelLayouts.apartment.parts.every(part => part.group === 'F1' && !part.id.endsWith(':guardrails')));
  }
  assert.match(messages.zh.model.atticNote, /仅表示展开状态.*二层走廊/);
  assert.match(messages.ja.model.atticNote, /展開状態のみ.*2階廊下/);
  assert.match(messages.en.model.atticNote, /deployed state.*second-floor hall/);
});

test('site controls and supplementary downloads have distinct names in all three languages', () => {
  for (const locale of locales) {
    const copy = messages[locale];
    for (const group of ['foundation', 'yard', 'fence']) {
      assert.ok(selectionLabel(copy, group)?.trim(), `${locale}: ${group}`);
      const categories = modelLayouts.house.parts.filter(part => part.group === group);
      const labels = categories.map(part => selectionLabel(copy, part.id));
      assert.ok(labels.every(label => label?.trim()), `${locale}: site category labels are present`);
      assert.equal(new Set(labels).size, categories.length, `${locale}: site categories are distinct`);
    }
    assert.ok(copy.downloads.files.site.title.trim() && copy.downloads.files.site.detail.trim());
    assert.ok(copy.downloads.files.sitePdf.title.trim() && copy.downloads.files.sitePdf.detail.trim());
    assert.notEqual(copy.downloads.files.site.title, copy.downloads.files.sitePdf.title);
  }
});


test('R06 structural controls and pending demonstration status are translated separately from apartment copy', () => {
  for (const locale of locales) {
    const copy = modelCopy(messages[locale], locale, 'house');
    for (const key of ['columns', 'beams', 'sills', 'attic_joists', 'attic_headers', 'roof_framing', 'bearing_walls', 'existing_plinth', 'internal_supports']) assert.ok(copy.partKinds[key].trim());
    assert.ok(copy.groups.structure.trim());
    assert.ok(copy.presets.structure.trim());
    assert.ok(copy.model.structureNote.trim());
    assert.ok(copy.model.demoNote.trim());
    assert.match(copy.model.atticNote, /1350/);
    for (const id of ['structure', 'structurePdf']) {
      assert.ok(copy.downloads.files[id].title.trim());
      assert.ok(copy.downloads.files[id].detail.trim());
    }
    assert.equal(modelLayouts.apartment.presets.some(preset => preset.id === 'structure'), false);
  }
});
