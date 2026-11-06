import test from 'node:test';
import assert from 'node:assert/strict';
import { parseComparisonRecord, comparisonRecordLimit, restoreReferenceAnchors, validReferencePose } from '../src/reference-record.ts';
import { defaultReferenceAlignment, referenceImagePoint, referenceImageCoordinate, referencePointError } from '../src/reference-review.ts';

const identity = {
  model: 'tokyo-tower', revision: 'LANDMARK-R11', modelSha256: 'a'.repeat(64), photoSha256: 'b'.repeat(64),
  width: 640, height: 480, cameras: ['front', 'iso', 'top'],
};
const original = () => ({
  schema_version: 2, model: identity.model, revision: identity.revision, model_sha256: identity.modelSha256,
  reference: { name: 'own.png', sha256: identity.photoSha256, width: 640, height: 480, source: 'Local test image' },
  alignment: { ...defaultReferenceAlignment, x: 4, y: -7 }, overlay_visible: true,
  camera: { preset: 'front', pose: { position: [0, 150, 1000], target: [0, 150, 0], zoom: 2, verticalSpan: 400 } },
  viewport: { width: 1000, height: 500 },
  anchor_points: [{ reference: { x: .2, y: .7 }, model: { x: .3, y: .6 } }],
});
const load = value => parseComparisonRecord(JSON.stringify(value), identity);

test('comparison records round-trip exact bindings, pose and paired points as sanitized values', () => {
  const record = original(), result = load(record);
  assert.deepEqual(result.alignment, record.alignment);
  assert.deepEqual(result.camera, record.camera);
  assert.deepEqual(result.viewport, record.viewport);
  assert.deepEqual(result.anchor_points, record.anchor_points);
  assert.equal(result.source, record.reference.source);
  result.anchor_points[0].model.x = .8;
  assert.equal(record.anchor_points[0].model.x, .3);
});
test('previous schema1 exports restore without newly added framing or anchors', () => {
  const record = original(); record.schema_version = 1;
  delete record.anchor_points; delete record.camera.pose.verticalSpan;
  const result = load(record);
  assert.deepEqual(result.anchor_points, []);
  assert.equal(result.camera.pose.verticalSpan, undefined);
  assert.deepEqual(result.camera.pose.position, record.camera.pose.position);
});
test('comparison import refuses different model, revision, native hash, photograph hash and dimensions', () => {
  const otherModel = original(); otherModel.model = 'tokyo-skytree';
  assert.throws(() => load(otherModel), error => error.reason === 'model');
  for (const field of ['revision', 'model_sha256']) {
    const record = original(); record[field] = field === 'revision' ? 'LANDMARK-R10' : 'c'.repeat(64);
    assert.throws(() => load(record), error => error.reason === 'revision');
  }
  for (const field of ['sha256', 'width', 'height']) {
    const record = original(); record.reference[field] = field === 'sha256' ? 'c'.repeat(64) : 999;
    assert.throws(() => load(record), error => error.reason === 'photo');
  }
});
test('comparison import rejects oversized JSON, malformed transforms, unsupported views and unsafe camera poses', () => {
  assert.throws(() => parseComparisonRecord(' '.repeat(comparisonRecordLimit + 1), identity));
  for (const text of ['', '{', 'null', '[]']) assert.throws(() => parseComparisonRecord(text, identity));
  const bad = [
    r => { r.schema_version = 99; }, r => { r.alignment.x = 101; }, r => { r.alignment.scale = 0; },
    r => { r.reference.source = 'x'.repeat(1001); }, r => { r.camera.preset = 'unsupported'; },
    r => { r.camera.pose.position = [1, 2]; }, r => { delete r.camera.pose.verticalSpan; }, r => { r.camera.pose.zoom = 99; },
    r => { r.camera.pose.position = [...r.camera.pose.target]; }, r => { r.camera.pose.verticalSpan = 0; },
    r => { r.viewport.width = 0; }, r => { r.viewport.height = 1e9; }, r => { r.overlay_visible = 'yes'; },
    r => { r.anchor_points = Array(17).fill(r.anchor_points[0]); },
    r => { r.anchor_points[0].reference.x = -1; }, r => { r.anchor_points[0].model.y = 2; },
  ];
  for (const change of bad) { const record = original(); change(record); assert.throws(() => load(record)); }
  assert.equal(validReferencePose({ position: [Infinity, 1, 2], target: [0, 0, 0], zoom: 1 }), false);
});
test('image-point projection and inverse agree through contain, translation, scale and rotation', () => {
  for (const rotation of [-135, -45, 0, 90, 180]) {
    const alignment = { ...defaultReferenceAlignment, scale: 1.2, x: 11, y: -17, rotation };
    const expected = { x: .23, y: .67 };
    const projected = referenceImagePoint(900, 550, 640, 480, alignment, expected);
    const actual = referenceImageCoordinate(900, 550, 640, 480, alignment, projected);
    assert.ok(Math.abs(expected.x - actual.x) < 1e-12);
    assert.ok(Math.abs(expected.y - actual.y) < 1e-12);
  }
});
test('paired image error reports CSS pixels and viewport-diagonal percentage', () => {
  const error = referencePointError({ x: 53, y: 54 }, { x: .5, y: .5 }, 100, 100);
  assert.equal(error.pixels, 5);
  assert.equal(error.diagonalPercent, 5 / Math.hypot(100, 100) * 100);
});
test('restoring another aspect ratio remaps model points to the adapted orthographic frame and drops offscreen points', () => {
  const anchors = [{ reference: { x: .2, y: .7 }, model: { x: .6, y: .4 } }];
  assert.deepEqual(restoreReferenceAnchors(anchors, { width: 1000, height: 500 }, { width: 500, height: 500 }),
    [{ reference: { x: .2, y: .7 }, model: { x: .7, y: .4 } }]);
  assert.deepEqual(restoreReferenceAnchors([{ reference: { x: .2, y: .7 }, model: { x: .9, y: .4 } }],
    { width: 1000, height: 500 }, { width: 500, height: 500 }), []);
});

test('cross-revision parsing requires explicit opt-in and still enforces exact model and photo bindings', () => {
  const prior = original(); prior.revision = 'LANDMARK-R10'; prior.model_sha256 = 'c'.repeat(64);
  assert.throws(() => load(prior), error => error.reason === 'revision');
  const parsed = parseComparisonRecord(JSON.stringify(prior), identity, { allowRevisionChange: true });
  assert.equal(parsed.revision, 'LANDMARK-R10'); assert.equal(parsed.model_sha256, 'c'.repeat(64));
  for (const change of [r => { r.model = 'tokyo-skytree'; }, r => { r.reference.sha256 = 'd'.repeat(64); }, r => { r.alignment.x = 101; }]) {
    const invalid = original(); change(invalid);
    assert.throws(() => parseComparisonRecord(JSON.stringify(invalid), identity, { allowRevisionChange: true }));
  }
  const inherited = original(); inherited.comparison_origin = { revision: prior.revision, model_sha256: prior.model_sha256 };
  assert.deepEqual(load(inherited).comparison_origin, inherited.comparison_origin);
  inherited.comparison_origin.model_sha256 = 'invalid'; assert.throws(() => load(inherited));
});
