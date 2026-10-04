import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { validatePlanMetadata, validatePlanPreviews } from '../scripts/plan-preview-validation.mjs';
import { fittedPlanWidth, planViewBox } from '../src/plan-preview.ts';

const root = fileURLToPath(new URL('../../', import.meta.url));

test('vector plans retain both overall dimensions and every required room label in the approved PDF crop', async () => {
  const metadata = await validatePlanPreviews(root);
  assert.deepEqual(metadata.floors.map(item => item.floor), [1, 2]);
  for (const floor of metadata.floors) {
    assert.equal(floor.annotations.filter(item => item.text === '7280').length, 2);
    assert.ok(floor.planViewBox[2] < floor.fullViewBox[2]);
    assert.ok(floor.bytes < 500_000);
  }
});

test('publishing rejects a changed PDF and altered vector previews instead of silently displaying stale plans', async () => {
  const metadata = await validatePlanPreviews(root);
  const pdf = await readFile(`${root}/${metadata.source.path}`);
  const svgs = new Map(await Promise.all(metadata.floors.map(async floor => [
    floor.floor, await readFile(`${root}/${floor.path}`),
  ])));
  assert.throws(() => validatePlanMetadata(metadata, Buffer.concat([pdf, Buffer.from('changed')]), svgs), /stale/);
  const changedSvg = new Map(svgs);
  changedSvg.set(1, Buffer.from('<svg></svg>'));
  assert.throws(() => validatePlanMetadata(metadata, pdf, changedSvg), /differs/);
});

test('fit-to-page uses both viewport dimensions for plan-only and full-sheet views', () => {
  for (const floor of [1, 2]) {
    for (const view of ['plan', 'sheet']) {
      const box = planViewBox(floor, view);
      for (const [width, height] of [[980, 600], [350, 500], [480, 280]]) {
        const fitted = fittedPlanWidth(box, width, height);
        assert.ok(fitted <= width);
        assert.ok(fitted * box[3] / box[2] <= height + 1e-9);
      }
    }
  }
});
