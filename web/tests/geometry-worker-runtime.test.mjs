import test from 'node:test';
import assert from 'node:assert/strict';
import { Worker } from 'node:worker_threads';
import { readFile } from 'node:fs/promises';
import { BoxGeometry, BufferAttribute, BufferGeometry, EdgesGeometry, Float32BufferAttribute,
  InterleavedBuffer, InterleavedBufferAttribute, Mesh, SphereGeometry } from 'three';
import { createGeometryWorkerClient } from '../src/geometry-worker-client.ts';
import { createCadOutlineGeometry } from '../src/cad-outlines.ts';
import { createWasmHorizontalCap, initializeSectionCapsWasm } from '../src/section-caps-wasm.ts';

// A native Node worker runs the actual browser entry and generated WASM. Only
// its event transport and local asset fetch are adapted; no computation is mocked.
function runtimeWorker(fetchFailure = false) {
  const worker = new Worker(`
    const { parentPort, workerData } = require('node:worker_threads');
    const { readFile } = require('node:fs/promises');
    globalThis.postMessage = (message, transfer) => parentPort.postMessage(message, transfer);
    globalThis.addEventListener = (type, listener) => {
      if (type === 'message') parentPort.on('message', data => listener({ data }));
    };
    globalThis.fetch = async url => workerData.fetchFailure
      ? new Response('', { status: 503 })
      : new Response(await readFile(url));
    import(workerData.module).catch(error => parentPort.postMessage({ type: 'error', message: error.message }));
  `, { eval: true, workerData: { module: new URL('../src/geometry-worker.ts', import.meta.url).href, fetchFailure } });
  const wrappers = new Map();
  return {
    postMessage(message, transfer) { worker.postMessage(message, transfer); },
    addEventListener(type, listener) {
      const wrapped = type === 'message' ? data => listener({ data }) : error => listener({ error, message: error.message });
      wrappers.set(listener, wrapped);
      worker.on(type, wrapped);
    },
    removeEventListener(type, listener) {
      const wrapped = wrappers.get(listener);
      if (wrapped) worker.off(type, wrapped);
      wrappers.delete(listener);
    },
    terminate() { void worker.terminate(); },
  };
}

function canonicalSegments(positions) {
  const result = [];
  for (let offset = 0; offset < positions.length; offset += 6) {
    result.push([0, 3].map(start => [...positions.subarray(offset + start, offset + start + 3)]
      .map(value => Math.round(value * 1e5)).join(',')).sort().join(':'));
  }
  return result.sort();
}

test('real worker registers copied geometry once and returns cap plus outline buffers matching existing algorithms', { timeout: 10_000 }, async t => {
  await initializeSectionCapsWasm(await readFile(new URL('../src/wasm/section_caps_bg.wasm', import.meta.url)));
  const failures = [];
  const client = createGeometryWorkerClient({ workerFactory: () => runtimeWorker(), onFailure: error => failures.push(error) });
  t.after(() => client.dispose());
  const geometry = new BoxGeometry(2, 4, 2);
  const positionsBefore = geometry.getAttribute('position').array.slice();
  const indicesBefore = geometry.index.array.slice();
  const geometryId = client.registerGeometry(geometry);
  assert.equal(client.registerGeometry(geometry), geometryId);
  const mesh = new Mesh(geometry);
  mesh.position.set(5, 3, -2);
  mesh.scale.set(2, 1, 0.5);
  mesh.updateWorldMatrix(true, false);
  const outlinePending = client.outlines([{ id: 'box-outline', geometryId, thresholdAngle: 28 }]);
  const capPending = client.sectionCaps([{ id: 'box-cap', geometryId, matrix: mesh.matrixWorld.elements, height: 3 }]);
  await client.ready;
  const [outline] = await outlinePending;
  const [cap] = await capPending;
  const expectedCap = createWasmHorizontalCap(mesh, 3);
  const expectedOutline = createCadOutlineGeometry(geometry);
  assert.deepEqual(cap.positions, expectedCap.getAttribute('position').array);
  assert.deepEqual(cap.normals, expectedCap.getAttribute('normal').array);
  assert.deepEqual(canonicalSegments(outline.positions), canonicalSegments(expectedOutline.getAttribute('position').array));
  assert.deepEqual(geometry.getAttribute('position').array, positionsBefore);
  assert.deepEqual(geometry.index.array, indicesBefore);
  const [outside] = await client.sectionCaps([{ id: 'outside', geometryId, matrix: mesh.matrixWorld.elements, height: 20 }]);
  assert.equal(outside.positions.length, 0, 'worker retains geometry after transferring result buffers');
  assert.deepEqual(failures, []);
  expectedCap.dispose(); expectedOutline.dispose(); geometry.dispose();
});

test('real worker preserves an empty index instead of treating positions as unindexed triangles', { timeout: 10_000 }, async t => {
  const client = createGeometryWorkerClient({ workerFactory: () => runtimeWorker() });
  t.after(() => client.dispose());
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new Float32BufferAttribute([0, 0, 0, 1, 0, 0, 0, 1, 0], 3));
  geometry.setIndex([]);
  const geometryId = client.registerGeometry(geometry);
  const outlines = await client.outlines([{ id: 'empty', geometryId, thresholdAngle: 28 }]);
  assert.equal(outlines[0].positions.length, 0);
  const mesh = new Mesh(geometry);
  mesh.updateWorldMatrix(true, false);
  const caps = await client.sectionCaps([{ id: 'empty', geometryId, matrix: mesh.matrixWorld.elements, height: 0.5 }]);
  assert.equal(caps[0].positions.length, 0);
  assert.equal(caps[0].normals.length, 0);
  geometry.dispose();
});

test('real worker WASM download failure is reported and queued requests resolve for fallback', { timeout: 10_000 }, async t => {
  const failures = [];
  const client = createGeometryWorkerClient({ workerFactory: () => runtimeWorker(true), onFailure: error => failures.push(error) });
  t.after(() => client.dispose());
  const geometry = new BoxGeometry();
  const geometryId = client.registerGeometry(geometry);
  const request = client.outlines([{ id: 'box', geometryId, thresholdAngle: 28 }]);
  await assert.rejects(client.ready, /503/);
  assert.equal(await request, null);
  assert.equal(client.failed, true);
  assert.equal(failures.length, 1);
  geometry.dispose();
});

test('real mesh-edge worker matches Three bytes including precision, degenerate faces and non-manifold winding', { timeout: 10_000 }, async t => {
  const client = createGeometryWorkerClient({ workerFactory: () => runtimeWorker() });
  t.after(() => client.dispose());
  const empty = new BufferGeometry();
  empty.setAttribute('position', new Float32BufferAttribute([0, 0, 0, 1, 0, 0, 0, 1, 0], 3));
  empty.setIndex([]);
  const precise = new BufferGeometry();
  precise.setAttribute('position', new BufferAttribute(new Float64Array([
    0.0000499999999, 0, 0, 1.00005000001, 0, 0, 0, 1, 0,
    0.0000500000001, 0, 0, 1.00005000001, 0, 0, 0, 0, 1,
    0, 0, 0, 0, 0, 0, 0, 1, 0,
    0, 0, 0, 1, 0, 0, 0, -1, 0,
    0, 0, 0, 1, 0, 0, 0, 0, -1,
  ]), 3));
  const normalized = new BufferGeometry();
  normalized.setAttribute('position', new BufferAttribute(new Int16Array([0, 0, 0, 32767, 0, 0, 0, 32767, 0]), 3, true));
  const interleaved = new BufferGeometry();
  interleaved.setAttribute('position', new InterleavedBufferAttribute(
    new InterleavedBuffer(new Float32Array([9, 0, 0, 0, 9, 1, 0, 0, 9, 0, 1, 0]), 4), 3, 1));
  const geometries = [new BoxGeometry(), new BoxGeometry().toNonIndexed(), new SphereGeometry(1, 20, 12),
    empty, precise, normalized, interleaved];
  for (const geometry of geometries) t.after(() => geometry.dispose());
  const expected = new Map();
  const jobs = geometries.flatMap((geometry, index) => {
    const geometryId = client.registerGeometry(geometry, { precision: 'source' });
    assert.equal(client.registerGeometry(geometry), geometryId, 'Float64 consumers reuse exact source snapshot');
    return [0, 28, 90, 180].map(thresholdAngle => {
      const id = `${index}-${thresholdAngle}`;
      const edges = new EdgesGeometry(geometry, thresholdAngle);
      expected.set(id, edges.getAttribute('position').array.slice());
      edges.dispose();
      return { id, geometryId, thresholdAngle };
    });
  });
  const results = await client.meshEdges(jobs);
  for (const result of results) assert.deepEqual(result.positions, expected.get(result.id), result.id);
  // The cache survives transfer and caller mutation of the previous batch.
  results.forEach(result => result.positions.fill(0));
  const repeated = await client.meshEdges([jobs[0], { ...jobs[0], id: 'duplicate' }]);
  assert.deepEqual(repeated[0].positions, expected.get(jobs[0].id));
  assert.equal(repeated[0].positions.buffer, repeated[1].positions.buffer, 'one transferable copy for duplicate geometry jobs');
  assert.equal(client.failed, false);
});

test('source-precision edges then Rust outlines and caps preserve rendering attributes and invalidated snapshots', { timeout: 10_000 }, async t => {
  await initializeSectionCapsWasm(await readFile(new URL('../src/wasm/section_caps_bg.wasm', import.meta.url)));
  const client = createGeometryWorkerClient({ workerFactory: () => runtimeWorker() });
  t.after(() => client.dispose());
  const geometry = new BoxGeometry(2, 4, 2);
  t.after(() => geometry.dispose());
  const originalPositions = geometry.getAttribute('position').array.slice();
  const originalIndex = geometry.index.array.slice();
  const geometryId = client.registerGeometry(geometry, { precision: 'source' });
  await client.meshEdges([{ id: 'edges', geometryId, thresholdAngle: 28 }]);
  const mesh = new Mesh(geometry);
  mesh.updateWorldMatrix(true, false);
  const [outline] = await client.outlines([{ id: 'outline', geometryId: client.registerGeometry(geometry), thresholdAngle: 28 }]);
  const [cap] = await client.sectionCaps([{ id: 'cap', geometryId, matrix: mesh.matrixWorld.elements, height: 0 }]);
  const expectedOutline = createCadOutlineGeometry(geometry);
  const expectedCap = createWasmHorizontalCap(mesh, 0);
  assert.deepEqual(canonicalSegments(outline.positions), canonicalSegments(expectedOutline.getAttribute('position').array));
  assert.deepEqual(cap.positions, expectedCap.getAttribute('position').array);
  assert.deepEqual(geometry.getAttribute('position').array, originalPositions);
  assert.deepEqual(geometry.index.array, originalIndex);
  geometry.getAttribute('position').setX(0, 8);
  geometry.getAttribute('position').needsUpdate = true;
  const changedId = client.registerGeometry(geometry, { precision: 'source' });
  assert.notEqual(changedId, geometryId);
  const [changed] = await client.meshEdges([{ id: 'changed', geometryId: changedId, thresholdAngle: 28 }]);
  const expectedEdges = new EdgesGeometry(geometry, 28);
  assert.deepEqual(changed.positions, expectedEdges.getAttribute('position').array);
  expectedOutline.dispose(); expectedCap.dispose(); expectedEdges.dispose();
});
