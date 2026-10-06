import test from 'node:test';
import assert from 'node:assert/strict';
import { Worker } from 'node:worker_threads';
import { readFile } from 'node:fs/promises';
import { BoxGeometry, BufferGeometry, Float32BufferAttribute, Mesh } from 'three';
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
