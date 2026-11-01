import test from 'node:test';
import assert from 'node:assert/strict';
import { defaultReferenceAlignment, referenceAlignment, referenceImageRect, referenceTransform, validReferenceImage, validReferenceDimensions } from '../src/reference-review.ts';

test('photo comparison restricts local raster images and bounded finite transforms', () => {
  for (const type of ['image/png', 'image/jpeg', 'image/webp']) assert.equal(validReferenceImage({ type, size: 12 * 1024 * 1024 }), true);
  for (const file of [{ type: 'image/svg+xml', size: 100 }, { type: 'image/png', size: 0 }, { type: 'image/png', size: 12 * 1024 * 1024 + 1 }]) assert.equal(validReferenceImage(file), false);
  assert.deepEqual(referenceAlignment({ opacity: Infinity, scale: NaN, x: -1000, y: 1000, rotation: 999 }), { ...defaultReferenceAlignment, x: -100, y: 100, rotation: 180 });
  assert.equal(validReferenceDimensions(8000, 4000), true);
  for (const [w, h] of [[8000, 8000], [20000, 100], [0, 100], [NaN, 10], [1.5, 2]]) assert.equal(validReferenceDimensions(w, h), false);
});
test('exported overlay fits the same contain box, percent offsets, scale and rotation as the live overlay', () => {
  const a = { opacity: .3, scale: 2, x: 10, y: -20, rotation: 90 };
  assert.equal(referenceTransform(a), 'translate(10%, -20%) rotate(90deg) scale(2)');
  assert.deepEqual(referenceImageRect(1000, 500, 400, 800, a), { centerX: 600, centerY: 150, width: 500, height: 1000, rotation: Math.PI / 2, opacity: .3 });
  assert.throws(() => referenceImageRect(0, 500, 400, 800, a));
});
