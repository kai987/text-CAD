import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, readFile, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { gunzipSync } from 'node:zlib';
import { randomBytes } from 'node:crypto';
import { artifactTransport, verifyArtifactTransports, verifyStaticBuildBudget, STATIC_FILE_LIMIT, STATIC_BUILD_LIMIT } from '../scripts/artifact-transport.mjs';

async function directory(t, files) {
  const root = await mkdtemp(join(tmpdir(), 'cad-artifact-transport-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  for (const [name, bytes] of files) await writeFile(join(root, name), bytes);
  return root;
}
test('oversized GLB and editable DXF host only gzip while retaining exact original catalog bindings', async t => {
  const glb = Buffer.alloc(STATIC_FILE_LIMIT + 1024, 0x20);
  glb.write('glTF'); glb.writeUInt32LE(2, 4); glb.writeUInt32LE(glb.length, 8);
  const dxf = Buffer.from('0\nSECTION\n2\nENTITIES\n' + '999\nNamed CAD member\n'.repeat(STATIC_FILE_LIMIT / 19 + 100) + '0\nENDSEC\n0\nEOF\n');
  for (const [name, original] of [['tower.glb', glb], ['tower.dxf', dxf]]) {
    assert.ok(original.length > STATIC_FILE_LIMIT);
    const result = artifactTransport(name, original);
    assert.deepEqual(result.files.map(([path]) => path), [`${name}.gz`]);
    assert.equal(result.records[name].transport, 'gzip');
    assert.equal(result.records[`${name}.gz`].decodedBytes, original.length);
    assert.equal(result.records[`${name}.gz`].decodedSha256, result.records[name].sha256);
    assert.deepEqual(gunzipSync(result.files[0][1]), original);
    const root = await directory(t, result.files);
    assert.equal(await verifyArtifactTransports(root, result.records), 1);
  }
});
test('under-limit native STEP, GLB and DXF publish only useful gzip with exact native bindings', async t => {
  for (const name of ['model.step', 'model.glb', 'drawing.dxf']) {
    const payload = Buffer.from('Exact named CAD source and coordinates.\n'.repeat(100));
    assert.ok(payload.length < STATIC_FILE_LIMIT);
    const result = artifactTransport(name, payload);
    assert.deepEqual(result.files.map(([path]) => path), [`${name}.gz`]);
    assert.equal(result.records[name].transport, 'gzip');
    assert.equal(result.records[name].bytes, payload.length);
    assert.equal(result.records[`${name}.gz`].decodedSha256, result.records[name].sha256);
    assert.deepEqual(gunzipSync(result.files[0][1]), payload);
    const root = await directory(t, result.files);
    await assert.rejects(readFile(join(root, name)), { code: 'ENOENT' });
    assert.equal(await verifyArtifactTransports(root, result.records), 1);
  }
});
test('small native files retain only raw bytes when gzip offers no saving', async t => {
  for (const name of ['small.step', 'small.glb', 'small.dxf']) {
    const payload = Buffer.from('tiny');
    const result = artifactTransport(name, payload);
    assert.equal(result.records[name].transport, undefined);
    assert.deepEqual(result.files, [[name, payload]]);
    assert.equal(result.records[`${name}.gz`], undefined);
    const root = await directory(t, result.files);
    assert.equal(await verifyArtifactTransports(root, result.records), 1);
  }
});
test('expanded hosting budget counts nested physical bytes and permits only the exact boundary', async t => {
  assert.equal(STATIC_BUILD_LIMIT, 256 * 1024 * 1024);
  const root = await directory(t, [['index.html', Buffer.alloc(11)]]);
  await mkdir(join(root, 'artifacts'));
  await writeFile(join(root, 'artifacts', 'native.step.gz'), Buffer.alloc(21));
  assert.deepEqual(await verifyStaticBuildBudget(root, 32), { bytes: 32, files: 2, limitBytes: 32 });
  await assert.rejects(verifyStaticBuildBudget(root, 31), /Expanded static build exceeds hosting byte limit: 32 > 31/);
});
test('missing gzip records, changed transfers and rebound decoded hashes cannot pass build verification', async t => {
  const result = artifactTransport('large.dxf', Buffer.from('0\nSECTION\n' + '999\nframe\n'.repeat(300)), 256);
  const root = await directory(t, result.files);
  const noPayload = structuredClone(result.records); delete noPayload['large.dxf.gz'];
  await assert.rejects(verifyArtifactTransports(root, noPayload), /gzip binding/);
  const missing = structuredClone(result.records); missing['large.dxf.gz'].decodedSha256 = '0'.repeat(64);
  await assert.rejects(verifyArtifactTransports(root, missing), /gzip binding/);
  const noOriginal = structuredClone(result.records); delete noOriginal['large.dxf'];
  await assert.rejects(verifyArtifactTransports(root, noOriginal), /Logical artifact binding differs/);
  const wrongDecoded = structuredClone(result.records);
  wrongDecoded['large.dxf'].sha256 = wrongDecoded['large.dxf.gz'].decodedSha256 = '0'.repeat(64);
  await assert.rejects(verifyArtifactTransports(root, wrongDecoded), /Restored artifact differs/);
  const corrupt = Buffer.from(result.files[0][1]); corrupt[corrupt.length - 1] ^= 1;
  await writeFile(join(root, 'large.dxf.gz'), corrupt);
  await assert.rejects(verifyArtifactTransports(root, result.records), /Published asset differs/);
});
test('unknown logical transports and stale raw copies are rejected explicitly', async t => {
  const result = artifactTransport('large.glb', Buffer.from('glTF' + 'x'.repeat(300)), 128);
  const root = await directory(t, result.files);
  const unknown = structuredClone(result.records); unknown['large.glb'].transport = 'unknown';
  await assert.rejects(verifyArtifactTransports(root, unknown), /Unknown artifact transport/);
  await writeFile(join(root, 'large.glb'), Buffer.from('stale raw model'));
  await assert.rejects(verifyArtifactTransports(root, result.records), /unexpectedly has a raw copy/);
});
test('oversized STEP gzip splits into two bound physical files and verifies both reconstructed layers', async t => {
  const source = Buffer.from('ISO-10303-21;\nDATA;\n' + randomBytes(1024).toString('hex') + '\nENDSEC;\nEND-ISO-10303-21;');
  const result = artifactTransport('large.step', source, 800);
  const encoded = result.records['large.step.gz'];
  assert.equal(encoded.transport, 'chunks'); assert.equal(encoded.parts.length, 2);
  assert.ok(result.files.every(([, payload]) => payload.length <= 800));
  assert.deepEqual(gunzipSync(Buffer.concat(result.files.map(([, payload]) => payload))), source);
  const root = await directory(t, result.files);
  assert.equal(await verifyArtifactTransports(root, result.records, 800), 2);
  for (const changed of ['missing', 'duplicate', 'reordered', 'wrong-binding', 'aggregate']) {
    const manifest = structuredClone(result.records), parts = manifest['large.step.gz'].parts;
    if (changed === 'missing') delete manifest[parts[0].path];
    if (changed === 'duplicate') parts[1] = parts[0];
    if (changed === 'reordered') parts.reverse();
    if (changed === 'wrong-binding') manifest[parts[0].path].sha256 = '0'.repeat(64);
    if (changed === 'aggregate') manifest['large.step.gz'].sha256 = '0'.repeat(64);
    await assert.rejects(verifyArtifactTransports(root, manifest, 800));
  }
  const [name, payload] = result.files[0];
  await writeFile(join(root, name), payload.subarray(0, payload.length - 1));
  await assert.rejects(verifyArtifactTransports(root, result.records, 800), /Published asset differs/);
});
test('unsupported large previews and a viewer gzip needing chunks fail before publication', () => {
  assert.throws(() => artifactTransport('preview.svg', Buffer.alloc(1024), 800), /no gzip-capable reader/);
  assert.throws(() => artifactTransport('model.glb', randomBytes(1024), 800), /Viewer gzip exceeds/);
});

test('larger native CAD uses a bounded ordered chunk set and rejects damage in a later part', async t => {
  const source = Buffer.concat([Buffer.from('ISO-10303-21;\n'), randomBytes(4096)]);
  const result = artifactTransport('larger.step', source, 800);
  const encoded = result.records['larger.step.gz'];
  assert.ok(encoded.parts.length > 2);
  assert.ok(result.files.every(([, payload]) => payload.length <= 800));
  const root = await directory(t, result.files);
  assert.equal(await verifyArtifactTransports(root, result.records, 800), encoded.parts.length);
  const missing = structuredClone(result.records); delete missing[encoded.parts.at(-1).path];
  await assert.rejects(verifyArtifactTransports(root, missing, 800));
  const [name, payload] = result.files.at(-1);
  await writeFile(join(root, name), Buffer.concat([payload.subarray(1), Buffer.from([0])]));
  await assert.rejects(verifyArtifactTransports(root, result.records, 800), /Published asset differs/);
  assert.throws(() => artifactTransport('too-large.step', randomBytes(4096), 100), /chunked static transport limit/);
});
