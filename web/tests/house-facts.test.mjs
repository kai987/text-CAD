import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createHouseFacts, renderFacts } from '../src/house-facts.ts';
import { houseAssumptionsForFacts } from '../src/house-assumptions.ts';
const model = JSON.parse(await readFile(new URL('../../output/review/house_3d_assumptions_R01.json', import.meta.url), 'utf8'));
test('all languages use actual CAD storage heights and derived balcony clear area', () => {
  const facts = createHouseFacts(model), copy = houseAssumptionsForFacts(facts);
  assert.equal(facts.balconyClearArea, 7.191);
  for (const locale of ['zh', 'ja', 'en']) {
    assert.match(copy[locale][14 + 11], /1800.*2000/);
    assert.ok(copy[locale].some(line => line.includes('7.191')));
    assert.ok(copy[locale].every(line => !/\{\w+\}/.test(line)));
  }
});
test('modified source facts propagate into all translations without editing strings', () => {
  const changed = structuredClone(model);
  Object.assign(changed.geometry_parameters, { storage_cabinet_height: 1950, window_frame_depth: 80 });
  Object.assign(changed.plan_parameters, { balcony_depth: 1200, south_living_window_width: 2300 });
  const facts = createHouseFacts(changed), copy = houseAssumptionsForFacts(facts);
  assert.equal(facts.balconyClearArea, 8.789);
  for (const locale of ['zh', 'ja', 'en']) {
    assert.match(copy[locale][14 + 11], /1950/);
    assert.match(copy[locale][5], /2300\/1600\/1800/);
    assert.match(copy[locale][14 + 7], /80/);
  }
});
test('missing or invalid CAD facts cannot silently substitute stale constants', () => {
  const invalid = structuredClone(model); delete invalid.geometry_parameters.storage_cabinet_height;
  assert.throws(() => createHouseFacts(invalid), /Missing CAD fact/);
  assert.throws(() => renderFacts('{unknown}', {}), /Unknown CAD fact/);
});
