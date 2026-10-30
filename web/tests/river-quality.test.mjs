import test from 'node:test';
import assert from 'node:assert/strict';
import { riverCopy } from '../src/river-copy.ts';
import { isRiverQuality, readRiverQuality, resolveRiverQuality, riverQualities, riverQualityStorageKey, saveRiverQuality } from '../src/river-quality.ts';

test('river quality persists valid choices and recovers from invalid or unavailable storage', () => {
  for (const choice of riverQualities) {
    let stored = null;
    const storage = {
      getItem(key) { assert.equal(key, riverQualityStorageKey); return stored; },
      setItem(key, value) { assert.equal(key, riverQualityStorageKey); stored = value; },
    };
    assert.ok(isRiverQuality(choice));
    saveRiverQuality(storage, choice);
    assert.equal(readRiverQuality(storage), choice);
  }
  for (const invalid of [null, undefined, '', 'Detailed', 'high', '__proto__', 1, {}]) {
    assert.equal(isRiverQuality(invalid), false);
    assert.equal(readRiverQuality({ getItem: () => invalid }), 'auto');
  }
  for (const unavailable of [null, undefined, { getItem() { throw new Error('Blocked'); } }]) {
    assert.equal(readRiverQuality(unavailable), 'auto');
  }
  for (const unavailable of [null, undefined, { setItem() { throw new Error('Quota exceeded'); } }]) {
    assert.doesNotThrow(() => saveRiverQuality(unavailable, 'smooth'));
  }
});

test('automatic river quality handles compact screens and coarse pointers at the display breakpoint', () => {
  const compact = resolveRiverQuality('auto', 390, false);
  const desktop = resolveRiverQuality('auto', 1280, false);
  assert.deepEqual(resolveRiverQuality('auto', 760, false), compact);
  assert.deepEqual(resolveRiverQuality('auto', 761, false), desktop);
  assert.deepEqual(resolveRiverQuality('auto', 1920, true), compact);
  for (const unmeasured of [0, -1, NaN, Infinity]) assert.deepEqual(resolveRiverQuality('auto', unmeasured, false), compact);
  assert.ok(compact.pixelRatioCap < desktop.pixelRatioCap);
  assert.ok(compact.shadowMapSize < desktop.shadowMapSize);
  assert.ok(compact.detailPixels > desktop.detailPixels);
  assert.ok(desktop.detailPixels > 0);
});

test('explicit river quality is stable across screen changes and detailed mode always keeps full detail', () => {
  for (const choice of ['smooth', 'detailed']) {
    const settings = resolveRiverQuality(choice, 390, true);
    assert.deepEqual(settings, resolveRiverQuality(choice, 1920, false));
    assert.deepEqual(settings, resolveRiverQuality(choice, NaN, true));
    assert.ok(settings.pixelRatioCap >= 1 && settings.pixelRatioCap <= 2);
    assert.ok(settings.shadowMapSize <= 2048);
  }
  const smooth = resolveRiverQuality('smooth', 1280, false);
  const auto = resolveRiverQuality('auto', 1280, false);
  const detailed = resolveRiverQuality('detailed', 1280, false);
  assert.equal(detailed.detailPixels, 0);
  assert.ok(smooth.detailPixels > auto.detailPixels);
  assert.ok(smooth.pixelRatioCap <= auto.pixelRatioCap);
});

test('every river quality choice has matching labels and help in Chinese, Japanese and English', () => {
  for (const locale of ['zh', 'ja', 'en']) {
    const copy = riverCopy[locale];
    assert.ok(copy.qualityLabel.length > 0);
    assert.deepEqual(Object.keys(copy.qualities), riverQualities);
    assert.deepEqual(Object.keys(copy.qualityHelp), riverQualities);
    assert.equal(new Set(Object.values(copy.qualities)).size, riverQualities.length);
    for (const choice of riverQualities) {
      assert.ok(copy.qualities[choice].trim().length > 0);
      assert.ok(copy.qualityHelp[choice].trim().length > 0);
    }
  }
  assert.deepEqual(Object.values(riverCopy.zh.qualities), ['自动', '流畅', '精细']);
  assert.deepEqual(Object.values(riverCopy.en.qualities), ['Auto', 'Smooth', 'Detailed']);
});
