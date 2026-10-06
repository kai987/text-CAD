import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import {
  modelLayouts, settingsForPreset, activePreset, clampCutHeight, initialModel, initialPage,
  initialPreset, modelUrl, setGroupVisible, setPartVisible, isolatePart, isPartVisible,
  groupVisibilityState, anyVisible,
} from '../src/model-state.ts';
import { messages, locales, selectionLabel, roomLabel } from '../src/localization.ts';
import { modelCopy } from '../src/model-copy.ts';
const layout = modelLayouts.apartment;

test('apartment has one storey, ceiling and balcony; its default immediately reveals the interior', () => {
  assert.deepEqual(layout.pages, ['3d', '1f', 'files']);
  assert.deepEqual(layout.groups.map(group => group.id), ['F1', 'ceiling', 'balcony']);
  assert.ok(layout.parts.every(part => part.group === 'F1'));
  const initial = settingsForPreset(layout.defaultPreset, layout);
  assert.equal(initial.visibility.ceiling, false);
  assert.equal(initial.visibility.balcony, true);
  assert.equal(initial.cutaway, true);
  assert.equal(initial.heightMm, 1800);
  assert.equal(activePreset(initial, layout), 'interior');
  const complete = settingsForPreset('exterior', layout);
  assert.equal(complete.cutaway, false);
  assert.equal(complete.visibility.ceiling, true);
  assert.equal(activePreset(complete, layout), 'exterior');
  assert.equal(clampCutHeight(4200, layout), 2800);
  assert.equal(clampCutHeight(NaN, layout), 1800);
  assert.equal(clampCutHeight(-100, layout), 0);
});

test('apartment hidden, partial and isolated categories use only the active model topology', () => {
  const initial = settingsForPreset('interior', layout);
  const withoutFixtures = setPartVisible(initial, 'F1:fixtures', false, layout);
  assert.equal(groupVisibilityState(withoutFixtures, 'F1', layout), 'some');
  assert.equal(isPartVisible(initial, 'F1:fixtures', layout), true);
  assert.equal(isPartVisible(withoutFixtures, 'F1:fixtures', layout), false);
  const fixtures = isolatePart(withoutFixtures, 'F1:fixtures', layout);
  assert.equal(fixtures.cutaway, false);
  assert.deepEqual(layout.parts.filter(part => isPartVisible(fixtures, part.id, layout)).map(part => part.id), ['F1:fixtures']);
  assert.equal(fixtures.visibility.ceiling, false);
  assert.equal(fixtures.visibility.balcony, false);
  assert.equal(anyVisible(fixtures, layout), true);
  assert.equal(anyVisible(setGroupVisible(fixtures, 'F1', false, layout), layout), false);
  for (const group of ['ceiling', 'balcony']) {
    const isolated = isolatePart(initial, group, layout);
    assert.deepEqual(layout.groups.filter(item => isolated.visibility[item.id]).map(item => item.id), [group]);
    assert.equal(anyVisible(isolated, layout), true);
  }
  assert.equal(setPartVisible(initial, 'F2:doors', true, layout), initial);
  assert.equal(setGroupVisible(initial, 'roof', true, layout), initial);
});

test('apartment and legacy house links resolve valid pages and keep the opt-in WASM flag', () => {
  assert.equal(initialModel('?model=apartment'), 'apartment');
  assert.equal(initialModel('?model=unknown'), 'house');
  assert.equal(initialModel('?file=DXF/apartment_2ldk_plan.dxf'), 'apartment');
  assert.equal(initialPage('?view=2f', layout), '1f');
  assert.equal(initialPage('?view=2f'), '2f');
  assert.equal(initialPreset('?mode=second', layout), 'interior');
  assert.equal(initialPreset('?mode=exterior', layout), 'exterior');
  const current = 'https://example.com/text-CAD/?view=3d&mode=second&section=wasm';
  const plan = new URL(modelUrl(current, '1f', 'apartment'));
  assert.equal(plan.pathname, '/text-CAD/');
  assert.deepEqual(Object.fromEntries(plan.searchParams), { view: '1f', model: 'apartment', section: 'wasm' });
  const house = new URL(modelUrl(plan.href, '3d', 'house'));
  assert.deepEqual(Object.fromEntries(house.searchParams), { view: '3d', section: 'wasm' });
  assert.equal(new URL(modelUrl(current, '2f', 'apartment')).searchParams.get('view'), '1f');
  const diagnostic = current.replace('section=wasm', 'section=typescript');
  const diagnosticPlan = modelUrl(diagnostic, '1f', 'apartment');
  assert.equal(new URL(diagnosticPlan).searchParams.get('section'), 'typescript');
  assert.equal(new URL(modelUrl(diagnosticPlan, '3d', 'house')).searchParams.get('section'), 'typescript');
});

test('apartment labels and all recorded assumptions exist in Chinese, Japanese and English', async () => {
  const manifest = JSON.parse(await readFile(new URL('../../output/review/apartment_2ldk_manifest.json', import.meta.url), 'utf8'));
  for (const locale of locales) {
    const copy = modelCopy(messages[locale], locale, 'apartment');
    assert.notEqual(copy.model.title, messages[locale].model.title);
    assert.ok(copy.model.title.includes('2LDK'));
    assert.notEqual(copy.app.tabs['1f'], messages[locale].app.tabs['1f']);
    for (const group of layout.groups) assert.ok(selectionLabel(copy, group.id)?.trim(), `${locale}.${group.id}`);
    for (const part of layout.parts) assert.ok(selectionLabel(copy, part.id)?.trim(), `${locale}.${part.id}`);
    for (const room of manifest.floors[0].rooms) assert.ok(copy.rooms[room.id], `${locale}.${room.id}`);
    assert.notEqual(roomLabel(copy, 'balcony'), 'balcony');
    assert.equal(copy.assumptions.length, manifest.assumptions.length, `${locale}: every original assumption needs a translation`);
    assert.ok(copy.assumptions.every(text => text.trim()));
    assert.equal(modelCopy(messages[locale], locale, 'house'), messages[locale], 'house copy remains unchanged');
  }
});
