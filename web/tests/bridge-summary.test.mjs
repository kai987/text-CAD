import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { tmpdir } from 'node:os';
import { buildBridgeSummary, verifyBridgeSummary, verifyBridgeSummaryAssets, bridgeManifestPath, bridgeSummaryPath } from '../scripts/bridge-summary.mjs';
import { bridgeSummaryByteLimit } from '../scripts/bridge-summary-contract.mjs';
import { parseBridgeSummary } from '../src/bridge-metadata.ts';

const bytes = await readFile(new URL('../../output/review/seto_ohashi_manifest.json', import.meta.url));
const source = JSON.parse(bytes.toString());
const sha = value => createHash('sha256').update(value).digest('hex');
const record = value => ({ bytes: value.length, sha256: sha(value) });
const recordsFor = (full, small) => ({ [bridgeManifestPath]: record(full), [bridgeSummaryPath]: record(small) });
const edit = (value, action) => { const next = structuredClone(value); action(next); return next; };

test('compact bridge metadata retains every displayed fact and binds exact downloadable source bytes', () => {
  const result = buildBridgeSummary(bytes), summary = parseBridgeSummary(result.summary);
  assert.equal(summary.source_manifest_sha256, sha(bytes));
  assert.equal(summary.revision, source.revision);
  assert.equal(summary.units, 'mm');
  assert.deepEqual(Object.keys(summary.parameters).sort(), ['north_length_mm', 'south_length_mm', 'north_main_span_mm', 'south_main_span_mm'].sort());
  for (const [key, value] of Object.entries(summary.parameters)) assert.equal(value, source.parameters[key]);
  assert.deepEqual(summary.references, source.references.map(({ title, url }) => ({ title, url })));
  assert.deepEqual(summary.assumptions, source.assumptions);
  assert.ok(!('components' in summary) && !('activity' in summary));
  assert.ok(result.bytes.length < 20_000, 'current bridge display metadata should stay below20KB');
  assert.ok(result.bytes.length < bytes.length / 100, 'this is a projection, not a copy of all components');
  assert.deepEqual(verifyBridgeSummary(bytes, result.bytes, recordsFor(bytes, result.bytes)), summary);
  // Millimetre model controls may retain sub-millimetre precision; projection
  // must not add a new integer-only restriction to the original UI contract.
  const precise = Buffer.from(JSON.stringify(edit(source, next => { next.parameters.north_length_mm += .5; })));
  assert.equal(parseBridgeSummary(buildBridgeSummary(precise).summary).parameters.north_length_mm,
    source.parameters.north_length_mm + .5);
});

test('runtime rejects full manifests, mixed identities and expanded unknown fields instead of falling back', () => {
  const { summary } = buildBridgeSummary(bytes);
  assert.throws(() => parseBridgeSummary(source), /identity, schema or source binding/);
  for (const action of [
    value => { value.schema_version = 2; }, value => { value.model_id = 'river'; },
    value => { value.revision = 'BRIDGE-R00'; }, value => { value.units = 'm'; },
    value => { value.source_manifest_sha256 = ''; }, value => { value.components = source.components; },
  ]) assert.throws(() => parseBridgeSummary(edit(summary, action)), /identity, schema or source binding/);
});

test('malformed dimensions, source links and missing translations cannot populate the compact UI', () => {
  const { summary } = buildBridgeSummary(bytes);
  for (const value of [0, -1, NaN, Infinity, '1538000']) {
    assert.throws(() => parseBridgeSummary(edit(summary, next => { next.parameters.north_length_mm = value; })), /dimensions/);
  }
  assert.throws(() => parseBridgeSummary(edit(summary, next => { next.parameters.extra = 1; })), /dimensions/);
  for (const url of ['javascript:alert(1)', 'http://example.com/source', 'not-a-url']) {
    assert.throws(() => parseBridgeSummary(edit(summary, next => { next.references[0].url = url; })), /HTTPS/);
  }
  assert.throws(() => parseBridgeSummary(edit(summary, next => { delete next.assumptions[0].ja; })), /every language/);
  assert.throws(() => parseBridgeSummary(edit(summary, next => { next.assumptions[0].en = ' '; })), /every language/);
  assert.throws(() => parseBridgeSummary(edit(summary, next => { next.assumptions = []; })), /every language/);
});

test('source changes invalidate the projection even if displayed controls and model revision do not change', () => {
  const result = buildBridgeSummary(bytes);
  const changed = Buffer.from(JSON.stringify(edit(source, next => { next.components[0].color = '#112233'; })));
  const regenerated = buildBridgeSummary(changed);
  assert.deepEqual(regenerated.summary.parameters, result.summary.parameters);
  assert.notEqual(regenerated.summary.source_manifest_sha256, result.summary.source_manifest_sha256);
  assert.notEqual(sha(regenerated.bytes), sha(result.bytes));
  assert.throws(() => verifyBridgeSummary(changed, result.bytes, recordsFor(changed, result.bytes)), /exact projection/);
});

test('rebinding transport hashes cannot bless a modified summary dimension or assumption', () => {
  const result = buildBridgeSummary(bytes);
  for (const action of [
    next => { next.parameters.north_length_mm += 1; },
    next => { next.assumptions[0].ja = 'Edited model assumption'; },
    next => { next.references[0].title = 'Edited source title'; },
    next => { next.source_manifest_sha256 = '0'.repeat(64); },
  ]) {
    const modified = Buffer.from(JSON.stringify(edit(result.summary, action)));
    assert.throws(() => verifyBridgeSummary(bytes, modified, recordsFor(bytes, modified)), /exact projection/);
  }
});

test('the prepared summary needs both original and compact artifact integrity entries', async t => {
  const { bytes: small } = buildBridgeSummary(bytes);
  const root = await mkdtemp(resolve(tmpdir(), 'text-cad-bridge-summary-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  await mkdir(dirname(resolve(root, bridgeManifestPath)), { recursive: true });
  await writeFile(resolve(root, bridgeManifestPath), bytes);
  await writeFile(resolve(root, bridgeSummaryPath), small);
  assert.equal((await verifyBridgeSummaryAssets(root, recordsFor(bytes, small))).revision, source.revision);
  for (const path of [bridgeManifestPath, bridgeSummaryPath]) {
    const records = recordsFor(bytes, small); delete records[path];
    await assert.rejects(verifyBridgeSummaryAssets(root, records), /artifact binding/);
  }
  await writeFile(resolve(root, bridgeSummaryPath), Buffer.from('{}'));
  await assert.rejects(verifyBridgeSummaryAssets(root, recordsFor(bytes, small)), /artifact binding/);
});

test('unbounded reference metadata fails before creating an oversized browser summary', () => {
  const huge = Buffer.from(JSON.stringify(edit(source, next => { next.assumptions[0].ja = 'x'.repeat(bridgeSummaryByteLimit); })));
  assert.throws(() => buildBridgeSummary(huge), /compact metadata budget/);
});
