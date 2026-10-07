import test from 'node:test';
import assert from 'node:assert/strict';
import {
  initialSceneLighting, readSceneLighting, saveSceneLighting, sceneLightingStorageKey, sceneLightingUrl,
} from '../src/scene-lighting-settings.ts';
import {
  activePreset, groupVisibilityState, isolatePart, isPartVisible, modelLayouts, modelUrl,
  setFurnitureVisible, setGroupVisible, setPartVisible, settingsForPreset,
} from '../src/model-state.ts';
import { locales, messages, selectionLabel } from '../src/localization.ts';

const defaultLighting = { environment: 'day', outdoorLights: true, indoorLights: true };
const storageWith = value => ({ getItem(key) { assert.equal(key, sceneLightingStorageKey); return value; } });

test('saved model illumination remains separate from the page theme and rejects malformed data', () => {
  assert.deepEqual(initialSceneLighting(''), defaultLighting);
  const value = { environment: 'night', outdoorLights: false, indoorLights: true };
  let saved;
  saveSceneLighting({ setItem(key, item) { assert.equal(key, sceneLightingStorageKey); saved = item; } }, value);
  assert.deepEqual(readSceneLighting(storageWith(saved)), value);
  assert.deepEqual(Object.keys(JSON.parse(saved)).sort(), ['environment', 'indoorLights', 'outdoorLights', 'version']);
  for (const invalid of [null, '', '{', 'null', '[]', '"night"', '{"version":2,"environment":"night","outdoorLights":false}',
    '{"version":1,"environment":"dark","outdoorLights":true}',
    '{"version":1,"environment":"night","outdoorLights":"false"}']) {
    assert.deepEqual(readSceneLighting(storageWith(invalid)), defaultLighting, String(invalid));
  }
  assert.deepEqual(readSceneLighting({ getItem() { throw Error('Blocked'); } }), defaultLighting);
  assert.doesNotThrow(() => saveSceneLighting({ setItem() { throw Error('Full'); } }, value));
});

test('explicit shared day/night and lamp state takes precedence over saved preferences independently', () => {
  const storage = storageWith('{"version":1,"environment":"night","outdoorLights":false}');
  assert.deepEqual(initialSceneLighting('?view=3d&environment=day&lights=on', storage), defaultLighting);
  assert.deepEqual(initialSceneLighting('?environment=day', storage), { environment: 'day', outdoorLights: false, indoorLights: true });
  assert.deepEqual(initialSceneLighting('?lights=on', storage), { environment: 'night', outdoorLights: true, indoorLights: true });
  for (const invalid of ['environment=dark&lights=false', 'environment=__proto__&lights=1']) {
    assert.deepEqual(initialSceneLighting(`?${invalid}`, storage), { environment: 'night', outdoorLights: false, indoorLights: true });
  }
});

test('illumination URL updates and house/apartment page links retain structural, section and model inputs', () => {
  const current = 'https://example.com/text-CAD/?view=3d&mode=structure&city=kyoto&system=RC&section=wasm&revision=R07';
  const url = new URL(sceneLightingUrl(current, { environment: 'night', outdoorLights: false, indoorLights: true }));
  assert.equal(url.searchParams.get('city'), 'kyoto');
  assert.equal(url.searchParams.get('system'), 'RC');
  assert.equal(url.searchParams.get('mode'), 'structure');
  assert.equal(url.searchParams.get('revision'), 'R07');
  for (const model of ['house', 'apartment']) for (const page of modelLayouts[model].pages) {
    const next = new URL(modelUrl(url.href, page, model));
    assert.equal(next.searchParams.get('environment'), 'night');
    assert.equal(next.searchParams.get('lights'), 'off');
    assert.equal(next.searchParams.get('section'), 'wasm');
    assert.equal(next.searchParams.get('view'), page);
    assert.equal(next.pathname, '/text-CAD/');
  }
});

test('every house/apartment preset preserves model time and lamp power independently of camera and cut state', () => {
  let previous = { ...settingsForPreset('first'), environment: 'night', outdoorLights: false, cutaway: true, heightMm: 1500 };
  previous = setFurnitureVisible(previous, false);
  for (const layout of Object.values(modelLayouts)) for (const preset of layout.presets) {
    const next = settingsForPreset(preset.id, layout, previous);
    assert.equal(next.environment, 'night', `${layout.id}/${preset.id}`);
    assert.equal(next.outdoorLights, false, `${layout.id}/${preset.id}`);
    assert.equal(activePreset(next, layout), preset.id, 'night or disabled lamps do not turn a preset into a custom view');
    assert.equal(next.partVisibility['F1:furniture'], false);
  }
  assert.equal(previous.cutaway, true, 'preset changes are immutable');
  assert.equal(previous.heightMm, 1500);
});

test('light fixtures are separately selectable, isolateable and hidden by indoor and structural presets', () => {
  const original = { ...settingsForPreset('exterior'), environment: 'night', outdoorLights: false, cutaway: true, heightMm: 3300 };
  const categories = modelLayouts.house.parts.filter(part => part.group === 'lighting');
  assert.deepEqual(categories.map(part => part.id), ['lighting:wall', 'lighting:path', 'lighting:garden', 'lighting:gate']);
  assert.equal(groupVisibilityState(original, 'lighting'), 'all');
  for (const part of categories) {
    const hidden = setPartVisible(original, part.id, false);
    assert.equal(isPartVisible(hidden, part.id), false);
    assert.equal(groupVisibilityState(hidden, 'lighting'), 'some');
    assert.equal(hidden.environment, 'night');
    assert.equal(hidden.outdoorLights, false, 'fixture visibility does not change lamp power');
    assert.equal(hidden.heightMm, 3300);
    assert.equal(hidden.cutaway, true);
    const isolated = isolatePart(hidden, part.id);
    assert.deepEqual(modelLayouts.house.parts.filter(item => isPartVisible(isolated, item.id)).map(item => item.id), [part.id]);
    assert.equal(isolated.environment, 'night');
    assert.equal(isolated.outdoorLights, false);
  }
  const noFixtures = setGroupVisible(original, 'lighting', false);
  assert.equal(noFixtures.outdoorLights, false);
  assert.equal(groupVisibilityState(noFixtures, 'lighting'), 'none');
  for (const preset of ['first', 'second', 'attic', 'structure']) {
    assert.equal(groupVisibilityState(settingsForPreset(preset, modelLayouts.house, original), 'lighting'), 'none', preset);
  }
  assert.ok(!modelLayouts.apartment.groups.some(group => group.id === 'lighting'));
});

test('scene buttons, outdoor lamp switch and all four fixture categories have clear three-language copy', () => {
  for (const locale of locales) {
    const copy = messages[locale];
    assert.notEqual(copy.sceneLighting.day, copy.sceneLighting.night);
    assert.notEqual(copy.sceneLighting.label, copy.theme.label, 'the model setting is distinct from page appearance');
    for (const text of Object.values(copy.sceneLighting)) assert.ok(text.trim());
    const labels = modelLayouts.house.parts.filter(part => part.group === 'lighting').map(part => selectionLabel(copy, part.id));
    assert.equal(new Set(labels).size, 4);
    assert.ok(labels.every(label => label.trim() && !label.includes(':')));
  }
});
