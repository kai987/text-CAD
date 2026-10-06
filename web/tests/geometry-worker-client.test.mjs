import test from 'node:test';
import assert from 'node:assert/strict';
import { BufferGeometry, Float32BufferAttribute, InterleavedBuffer, InterleavedBufferAttribute } from 'three';
import { createGeometryWorkerClient } from '../src/geometry-worker-client.ts';

class FakeWorker {
  messages = [];
  listeners = new Map();
  terminated = 0;
  postMessage(message, transfer = []) {
    // Real transfer semantics are essential: accidentally transferring a Three
    // rendering attribute would detach it and make subsequent draws disappear.
    this.messages.push(structuredClone(message, { transfer }));
  }
  addEventListener(type, listener) {
    const listeners = this.listeners.get(type) ?? new Set();
    listeners.add(listener);
    this.listeners.set(type, listeners);
  }
  removeEventListener(type, listener) { this.listeners.get(type)?.delete(listener); }
  terminate() { this.terminated++; }
  emit(type, data) {
    for (const listener of this.listeners.get(type) ?? []) listener(type === 'message' ? { data } : data);
  }
  ready() { this.emit('message', { type: 'ready' }); }
  requests(type) { return this.messages.filter(message => message.type === type); }
  replySections(request, value = 1) {
    this.emit('message', { type: 'sections', requestId: request.requestId, results: request.jobs.map(job => ({
      id: job.id, positions: new Float32Array(9).fill(value), normals: new Float32Array(9).fill(1),
    })) });
  }
}

function sourceGeometry(indexed = true) {
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new Float32BufferAttribute([0, 0, 0, 1, 0, 0, 0, 1, 0], 3));
  if (indexed) geometry.setIndex([0, 1, 2]);
  return geometry;
}

function fixture(options = {}) {
  const worker = new FakeWorker();
  const failures = [];
  const client = createGeometryWorkerClient({ workerFactory: () => worker, onFailure: error => failures.push(error), ...options });
  const geometry = sourceGeometry();
  const geometryId = client.registerGeometry(geometry);
  const matrix = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
  const jobs = height => [{ id: 'wall', geometryId, matrix, height }];
  return { worker, failures, client, geometry, geometryId, matrix, jobs };
}

test('deferred initialization sends copied registrations before jobs and keeps render buffers attached', async t => {
  const { worker, client, geometry, geometryId, matrix, jobs } = fixture();
  t.after(() => client.dispose());
  const originalPositions = geometry.getAttribute('position').array.slice();
  const originalIndices = geometry.index.array.slice();
  assert.equal(client.registerGeometry(geometry), geometryId);
  const pending = client.sectionCaps(jobs(1.4));
  matrix[12] = 99;
  assert.equal(worker.messages.length, 0, 'no work reaches an uninitialized worker');
  worker.ready();
  await client.ready;
  assert.deepEqual(worker.messages.map(message => message.type), ['register', 'sections']);
  const input = worker.requests('register')[0];
  assert.ok(input.positions instanceof Float64Array);
  assert.ok(input.indices instanceof Uint32Array);
  assert.equal(input.indexed, true);
  assert.deepEqual([...input.positions], [...originalPositions]);
  assert.deepEqual([...input.indices], [...originalIndices]);
  assert.equal(worker.requests('sections')[0].jobs[0].matrix[12], 0, 'queued matrix is a snapshot');
  assert.deepEqual(geometry.getAttribute('position').array, originalPositions);
  assert.deepEqual(geometry.index.array, originalIndices);
  assert.equal(matrix.length, 16, 'caller matrix remains attached');
  worker.replySections(worker.requests('sections')[0]);
  assert.equal((await pending)[0].positions.length, 9);
});

test('geometry versions invalidate registration, including interleaved attribute versions and index replacement', async t => {
  const { worker, client, geometry } = fixture();
  t.after(() => client.dispose());
  worker.ready();
  const first = client.registerGeometry(geometry);
  geometry.getAttribute('position').setX(1, 2);
  geometry.getAttribute('position').needsUpdate = true;
  const second = client.registerGeometry(geometry);
  assert.notEqual(second, first);
  assert.equal(client.registerGeometry(geometry), second);
  geometry.setIndex([0, 2, 1]);
  assert.notEqual(client.registerGeometry(geometry), second);
  const interleaved = new BufferGeometry();
  const buffer = new InterleavedBuffer(new Float32Array([9, 0, 0, 0, 9, 1, 0, 0, 9, 0, 1, 0]), 4);
  interleaved.setAttribute('position', new InterleavedBufferAttribute(buffer, 3, 1));
  const interleavedFirst = client.registerGeometry(interleaved);
  assert.deepEqual([...worker.requests('register').at(-1).positions], [0, 0, 0, 1, 0, 0, 0, 1, 0]);
  buffer.needsUpdate = true;
  assert.notEqual(client.registerGeometry(interleaved), interleavedFirst);
});

test('empty indexed geometry stays distinct from non-indexed geometry and invalid indices fall back', async t => {
  const { worker, client } = fixture();
  t.after(() => client.dispose());
  worker.ready();
  const emptyIndexed = sourceGeometry();
  emptyIndexed.setIndex([]);
  assert.ok(client.registerGeometry(emptyIndexed));
  assert.equal(worker.requests('register').at(-1).indexed, true);
  assert.equal(worker.requests('register').at(-1).indices.length, 0);
  assert.ok(client.registerGeometry(sourceGeometry(false)));
  assert.equal(worker.requests('register').at(-1).indexed, false);
  const invalid = sourceGeometry();
  invalid.setIndex([0, 1, 20]);
  assert.equal(client.registerGeometry(invalid), null);
  assert.equal(client.registerGeometry(new BufferGeometry()), null);
});

test('dragging keeps one active and one latest pending section; intermediate and stale replies cannot apply', async t => {
  const { worker, client, jobs } = fixture();
  t.after(() => client.dispose());
  worker.ready();
  const first = client.sectionCaps(jobs(1.2));
  const second = client.sectionCaps(jobs(1.3));
  const latest = client.sectionCaps(jobs(1.4));
  assert.equal(await first, null);
  assert.equal(await second, null);
  assert.equal(worker.requests('sections').length, 1);
  worker.replySections({ requestId: 999, jobs: jobs(9) });
  assert.equal(worker.requests('sections').length, 1, 'unknown stale reply does not free the active slot');
  worker.replySections(worker.requests('sections')[0]);
  assert.equal(worker.requests('sections').length, 2);
  assert.equal(worker.requests('sections')[1].jobs[0].height, 1.4);
  worker.replySections(worker.requests('sections')[0]);
  worker.replySections(worker.requests('sections')[1], 4);
  assert.equal((await latest)[0].positions[0], 4);
});

test('queued cuts coalesce even while WASM initialization is pending', async t => {
  const { worker, client, jobs } = fixture();
  t.after(() => client.dispose());
  const first = client.sectionCaps(jobs(1));
  const latest = client.sectionCaps(jobs(2));
  assert.equal(await first, null);
  worker.ready();
  assert.equal(worker.requests('sections').length, 1);
  assert.equal(worker.requests('sections')[0].jobs[0].height, 2);
  worker.replySections(worker.requests('sections')[0]);
  assert.equal((await latest).length, 1);
});

test('canceling a scene invalidates caps without starting overlapping work', async t => {
  const { worker, client, jobs } = fixture();
  t.after(() => client.dispose());
  worker.ready();
  const active = client.sectionCaps(jobs(1));
  const pending = client.sectionCaps(jobs(2));
  client.cancelSections();
  assert.equal(await active, null);
  assert.equal(await pending, null);
  const nextScene = client.sectionCaps(jobs(3));
  assert.equal(worker.requests('sections').length, 1);
  worker.replySections(worker.requests('sections')[0]);
  assert.equal(worker.requests('sections').length, 2);
  worker.replySections(worker.requests('sections')[1], 3);
  assert.equal((await nextScene)[0].positions[0], 3);
});

test('empty section batch cancels previous caps and resolves immediately', async t => {
  const { worker, client, jobs } = fixture();
  t.after(() => client.dispose());
  worker.ready();
  const previous = client.sectionCaps(jobs(1));
  assert.deepEqual(await client.sectionCaps([]), []);
  assert.equal(await previous, null);
  worker.replySections(worker.requests('sections')[0]);
  assert.equal(worker.requests('sections').length, 1);
});

test('outline batches and caps have independent result IDs; results can arrive in either order', async t => {
  const { worker, client, jobs, geometryId } = fixture();
  t.after(() => client.dispose());
  const outline = client.outlines([{ id: 'east-wall', geometryId, thresholdAngle: 28 }]);
  const section = client.sectionCaps(jobs(1));
  worker.ready();
  assert.deepEqual(worker.messages.map(message => message.type), ['register', 'outlines', 'sections']);
  worker.replySections(worker.requests('sections')[0]);
  const request = worker.requests('outlines')[0];
  const positions = new Float32Array([0, 0, 0, 1, 0, 0]);
  worker.emit('message', { type: 'outlines', requestId: request.requestId, results: [{ id: 'east-wall', positions }] });
  assert.equal((await outline)[0].positions, positions);
  assert.equal((await section)[0].id, 'wall');
  assert.deepEqual(await client.outlines([]), []);
});

test('WASM initialization failure drains all requests and signals fallback once', async () => {
  const { worker, client, failures, jobs, geometryId } = fixture();
  const section = client.sectionCaps(jobs(1));
  const outline = client.outlines([{ id: 'outline', geometryId, thresholdAngle: 28 }]);
  worker.emit('message', { type: 'error', message: 'WASM download failed (503).' });
  await assert.rejects(client.ready, /503/);
  assert.equal(await section, null);
  assert.equal(await outline, null);
  assert.equal(client.failed, true);
  assert.equal(worker.terminated, 1);
  assert.equal(failures.length, 1);
  assert.equal(await client.sectionCaps(jobs(2)), null);
  assert.equal(await client.outlines([{ id: 'again', geometryId, thresholdAngle: 28 }]), null);
  assert.equal(client.registerGeometry(sourceGeometry()), null);
  worker.emit('error', { message: 'duplicate failure' });
  assert.equal(failures.length, 1);
  client.dispose();
});

test('worker errors and decoding failures settle active jobs and terminate the worker', async () => {
  for (const event of ['error', 'messageerror']) {
    const { worker, client, failures, jobs } = fixture();
    worker.ready();
    const active = client.sectionCaps(jobs(1));
    const pending = client.sectionCaps(jobs(2));
    worker.emit(event, { message: 'script blocked' });
    assert.equal(await active, null);
    assert.equal(await pending, null);
    assert.equal(failures.length, 1);
    assert.equal(worker.terminated, 1);
    client.dispose();
  }
});

test('unsupported Worker construction reports fallback after returning the client', async () => {
  const failures = [];
  const client = createGeometryWorkerClient({
    workerFactory() { throw new Error('Worker unavailable'); },
    onFailure(error) { failures.push(error); },
  });
  assert.equal(failures.length, 0);
  await assert.rejects(client.ready, /unavailable/);
  assert.equal(failures.length, 1);
  assert.equal(client.failed, true);
  client.dispose();
});

test('invalid results trigger fallback instead of leaving a pending batch or applying corrupt geometry', async () => {
  for (const results of [[null], [{ id: 'wall', positions: new Float32Array(3), normals: new Float32Array(3) }], [],
    [{ id: 'wall', positions: new Float32Array(9).fill(NaN), normals: new Float32Array(9) }],
    [{ id: 'wall', positions: new Float32Array(9), normals: new Float32Array(9).fill(Infinity) }],
  ]) {
    const { worker, client, failures, jobs } = fixture();
    worker.ready();
    const pending = client.sectionCaps(jobs(1));
    worker.emit('message', { type: 'sections', requestId: worker.requests('sections')[0].requestId, results });
    assert.equal(await pending, null);
    assert.equal(failures.length, 1);
    client.dispose();
  }
});

test('non-finite outlines trigger the same safe fallback as non-finite caps', async () => {
  const { worker, client, failures, geometryId } = fixture();
  worker.ready();
  const pending = client.outlines([{ id: 'wall', geometryId, thresholdAngle: 28 }]);
  worker.emit('message', { type: 'outlines', requestId: worker.requests('outlines')[0].requestId,
    results: [{ id: 'wall', positions: new Float32Array(6).fill(Infinity) }] });
  assert.equal(await pending, null);
  assert.equal(failures.length, 1);
  client.dispose();
});

test('a synchronous upload failure while handling ready rejects initialization and drains every queued job', async () => {
  const { worker, client, failures, jobs, geometryId } = fixture();
  const section = client.sectionCaps(jobs(1));
  const outline = client.outlines([{ id: 'outline', geometryId, thresholdAngle: 28 }]);
  worker.postMessage = () => { throw new Error('postMessage blocked'); };
  worker.ready();
  await assert.rejects(client.ready, /postMessage blocked/);
  assert.equal(await section, null);
  assert.equal(await outline, null);
  assert.equal(failures.length, 1);
  assert.equal(worker.terminated, 1);
  client.dispose();
});

test('initialization timeout rejects ready, releases queued jobs and terminates the worker', async () => {
  const { worker, client, failures, jobs } = fixture({ initializeTimeoutMs: 10 });
  const pending = client.sectionCaps(jobs(1));
  await assert.rejects(client.ready, /initialization timed out/);
  assert.equal(await pending, null);
  assert.equal(failures.length, 1);
  assert.equal(worker.terminated, 1);
  client.dispose();
});

test('request timeout releases latest pending sections and outlines so TypeScript fallback can run', async () => {
  const { worker, client, failures, jobs, geometryId } = fixture({ requestTimeoutMs: 10 });
  worker.ready();
  const active = client.sectionCaps(jobs(1));
  const pending = client.sectionCaps(jobs(2));
  const outline = client.outlines([{ id: 'wall-outline', geometryId, thresholdAngle: 28 }]);
  assert.equal(await active, null);
  assert.equal(await pending, null);
  assert.equal(await outline, null);
  assert.match(failures[0].message, /timed out/);
  assert.equal(worker.terminated, 1);
  client.dispose();
});

test('dispose is idempotent, settles jobs, removes listeners and ignores late replies', async () => {
  const { worker, client, failures, jobs, geometryId } = fixture();
  const section = client.sectionCaps(jobs(1));
  const outline = client.outlines([{ id: 'outline', geometryId, thresholdAngle: 28 }]);
  client.dispose();
  client.dispose();
  await assert.rejects(client.ready, /disposed/);
  assert.equal(await section, null);
  assert.equal(await outline, null);
  assert.equal(worker.terminated, 1);
  assert.equal([...worker.listeners.values()].reduce((count, set) => count + set.size, 0), 0);
  worker.ready();
  assert.equal(worker.messages.length, 0);
  assert.equal(failures.length, 0, 'normal scene disposal does not claim a WASM error');
  assert.equal(await client.sectionCaps(jobs(2)), null);
});
