import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { EdgesGeometry, Mesh } from 'three';
import { buildStaticOutlines } from '../scripts/static-outlines.mjs';
import { loadGlbGeometry } from './helpers/load-glb-geometry.mjs';
import { createCadOutlineGeometry } from '../src/cad-outlines.ts';
import { decodeStaticOutlineCache, encodeStaticOutlineCache, outlineKindForCadName } from '../src/static-outline-cache.ts';
import { loadStaticOutlines } from '../src/static-outline-resource.ts';

const sha = bytes => createHash('sha256').update(new Uint8Array(bytes)).digest('hex');
const source = 'a'.repeat(64);
const entries = [{ node: 2, kind: 'edges', positions: new Float32Array([0, 1, 2, 3, 4, 5]) },
  { node: 3, kind: 'cad', positions: new Float32Array() }];

test('outline cache pins model bytes and algorithm, retains empty and nonempty endpoints', () => {
  const bytes = encodeStaticOutlineCache(source, entries);
  const decoded = decodeStaticOutlineCache(bytes, source);
  assert.equal(decoded.size, 2);
  assert.deepEqual(decoded.get(2).positions, entries[0].positions);
  assert.equal(decoded.get(3).kind, 'cad');
  assert.equal(decoded.get(3).positions.length, 0);
  assert.equal(decoded.get(2).positions.buffer, bytes, 'display data uses the validated cache buffer');
  assert.throws(() => decodeStaticOutlineCache(bytes, 'b'.repeat(64)), /different model/);
  assert.throws(() => decodeStaticOutlineCache(bytes.slice(0, -4), source), /layout/);
  const changed = bytes.slice(0); new DataView(changed).setUint32(4, 99, true);
  assert.throws(() => decodeStaticOutlineCache(changed, source), /layout/);
  assert.throws(() => encodeStaticOutlineCache(source, [entries[0], entries[0]]), /entry/);
  assert.throws(() => encodeStaticOutlineCache(source, [{ ...entries[0], positions: new Float32Array([Infinity, 0, 0, 0, 0, 0]) }]), /coordinates/);
  assert.throws(() => encodeStaticOutlineCache(source, [{ ...entries[0], positions: new Float32Array(3) }]), /entry/);
});

test('all saved residential and overlay nodes retain the same local outline endpoints', async () => {
  for (const file of ['house_3d.glb', 'apartment_2ldk.glb', 'structure_W.glb', 'structure_S.glb', 'structure_RC.glb']) {
    const input = await readFile(new URL(`../../GLB/${file}`, import.meta.url));
    const output = await buildStaticOutlines(input);
    const buffer = output.bytes.buffer.slice(output.bytes.byteOffset, output.bytes.byteOffset + output.bytes.byteLength);
    const cache = decodeStaticOutlineCache(buffer, sha(input));
    const gltf = await loadGlbGeometry(input);
    let count = 0;
    gltf.scene.traverse(mesh => {
      if (!(mesh instanceof Mesh)) return;
      const node = gltf.parser.associations.get(mesh).nodes;
      const kind = outlineKindForCadName(gltf.parser.json.nodes[node].name);
      const expected = kind === 'cad' ? createCadOutlineGeometry(mesh.geometry, 28) : new EdgesGeometry(mesh.geometry, 28);
      assert.equal(cache.get(node)?.kind, kind, `${file}: node ${node}`);
      assert.deepEqual(cache.get(node).positions, expected.getAttribute('position').array, `${file}: node ${node} endpoints`);
      expected.dispose(); mesh.geometry.dispose();
      (Array.isArray(mesh.material) ? mesh.material : [mesh.material]).forEach(material => material.dispose());
      count++;
    });
    assert.equal(cache.size, count, `${file}: no missing or extra cached meshes`);
    assert.equal(output.entries, count);
  }
});

test('optional cache resource validates checksums and fails closed for stale or cancelled data', async t => {
  const bytes = encodeStaticOutlineCache(source, entries);
  let input = bytes;
  let calls = 0;
  t.mock.method(globalThis, 'fetch', async () => { calls++; return new Response(input); });
  const options = { url: '/edges', compressedUrl: '/edges.gz', expectedSha256: sha(bytes), sourceSha256: source };
  const good = loadStaticOutlines(options);
  assert.deepEqual((await good.ready).get(2).positions, entries[0].positions);
  const before = calls;
  assert.equal(await loadStaticOutlines({ ...options, expectedSha256: undefined }).ready, null);
  assert.equal(calls, before, 'old releases without a cache hash do not request optional files');
  const crypto = t.mock.getter(globalThis, 'crypto', () => undefined);
  assert.equal(await loadStaticOutlines(options).ready, null, 'unverified model bytes must use geometry-based outlines');
  assert.equal(calls, before);
  crypto.mock.restore();
  assert.equal(await loadStaticOutlines({ ...options, sourceSha256: 'b'.repeat(64) }).ready, null);
  input = bytes.slice(0); new Uint8Array(input)[input.byteLength - 1] ^= 1;
  assert.equal(await loadStaticOutlines(options).ready, null, 'tampered cache never supplies outlines');
  input = bytes;
  const cancelled = loadStaticOutlines(options); cancelled.cancel();
  assert.equal(await cancelled.ready, null);
});
