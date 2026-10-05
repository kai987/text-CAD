import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { validateApartmentPreviews, validatePlanMetadata, apartmentPlanRequirements } from '../scripts/plan-preview-validation.mjs';

const root = fileURLToPath(new URL('../../', import.meta.url));

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
