import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { validateApartmentPreviews, validatePlanMetadata, apartmentPlanRequirements } from '../scripts/plan-preview-validation.mjs';
import { modelLayouts } from '../src/model-state.ts';
import { bindCadNodes } from '../src/model-scene.ts';
import { loadGlbGeometry } from './helpers/load-glb-geometry.mjs';

const root = fileURLToPath(new URL('../../', import.meta.url));

test('house and apartment require only groups and parts present in their actual exported GLBs', async () => {
  for (const [model, path] of [['house', 'house_3d.glb'], ['apartment', 'apartment_2ldk.glb']]) {
    const layout = modelLayouts[model];
    const objects = bindCadNodes(await loadGlbGeometry(new URL(`../../GLB/${path}`, import.meta.url)));
    for (const entry of [...layout.groups, ...layout.parts]) {
      assert.ok(objects.has(entry.id), `${model}: missing required CAD node ${entry.id}`);
    }
  }
  assert.ok(modelLayouts.house.parts.some(part => part.id === 'F1:indoor_lights'));
  assert.ok(modelLayouts.apartment.parts.every(part => part.id !== 'F1:indoor_lights'));
});

test('apartment vector drawing retains rooms and both overall dimensions from its own PDF', async () => {
  const metadata = await validateApartmentPreviews(root);
  assert.equal(metadata.source.pages, 1);
  assert.deepEqual(metadata.floors.map(item => item.floor), [1]);
  const floor = metadata.floors[0];
  for (const label of ['LDK', '7800', '8400', '浴室', '玄関', 'トイレ', 'バルコニー']) {
    assert.ok(floor.annotations.some(annotation => annotation.text.includes(label)), `missing ${label}`);
  }
  const pdf = await readFile(`${root}/${metadata.source.path}`);
  const svg = await readFile(`${root}/${floor.path}`);
  assert.throws(() => validatePlanMetadata(metadata, Buffer.concat([pdf, Buffer.from('changed')]),
    new Map([[1, svg]]), apartmentPlanRequirements), /stale/);
  assert.throws(() => validatePlanMetadata(metadata, pdf,
    new Map([[1, Buffer.from('<svg></svg>')]]), apartmentPlanRequirements), /differs/);
  const clipped = structuredClone(metadata);
  clipped.floors[0].planViewBox = [0, 0, 1, 1];
  assert.throws(() => validatePlanMetadata(clipped, pdf,
    new Map([[1, svg]]), apartmentPlanRequirements), /clips/);
});
