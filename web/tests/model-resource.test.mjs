import test from 'node:test';
import assert from 'node:assert/strict';
import { startModelLoad } from '../src/model-resource.ts';
const tick = () => new Promise(resolve => setImmediate(resolve));
function harness(overrides = {}) {
  const ready = [], errors = [], late = [], progress = [];
  const load = startModelLoad({ url: '/model.glb', parse: async bytes => [...new Uint8Array(bytes)],
    fetcher: async () => new Response(new Uint8Array([1, 2, 3]), { headers: { 'content-length': '3' } }),
    onLoad: value => ready.push(value), onError: error => errors.push(error), disposeLate: value => late.push(value),
    onProgress: value => progress.push(value), ...overrides });
  return { load, ready, errors, late, progress };
}
test('stream download reports progress and decodes the actual bytes once', async () => {
  const h = harness(); await tick();
  assert.deepEqual(h.ready, [[1, 2, 3]]); assert.equal(h.errors.length, 0);
  assert.deepEqual(h.progress.at(-1), { loaded: 3, total: 3 }); h.load.cancel();
});
test('missing length is indeterminate and HTTP/decode errors reach recovery', async () => {
  const noLength = harness({ fetcher: async () => new Response(new Uint8Array([7])) });
  const failed = harness({ fetcher: async () => new Response('', { status: 503 }) });
  const invalid = harness({ parse: async () => { throw new Error('Invalid GLB'); } });
  await tick();
  assert.equal(noLength.progress[0].total, null); assert.equal(failed.errors.length, 1);
  assert.equal(invalid.errors.length, 1); assert.equal(failed.ready.length, 0);
});
test('deadline aborts a stalled request exactly once; a new attempt can succeed', async () => {
  let signal;
  const h = harness({ timeoutMs: 15, fetcher: (_, options) => { signal = options.signal; return new Promise(() => {}); } });
  await new Promise(resolve => setTimeout(resolve, 30));
  assert.ok(signal.aborted); assert.equal(h.errors.length, 1); assert.equal(h.ready.length, 0);
  h.load.cancel(); assert.equal(h.errors.length, 1);
  const retry = harness(); await tick(); assert.deepEqual(retry.ready, [[1, 2, 3]]);
});
test('cancelled or timed-out parses dispose late GPU resources without publishing stale success', async () => {
  for (const cancel of [true, false]) {
    let decode;
    const h = harness({ timeoutMs: cancel ? 1000 : 15, parse: () => new Promise(resolve => { decode = resolve; }) });
    await tick();
    if (cancel) h.load.cancel(); else await new Promise(resolve => setTimeout(resolve, 30));
    decode({ gpu: 'resource' }); await tick();
    assert.equal(h.ready.length, 0); assert.deepEqual(h.late, [{ gpu: 'resource' }]);
    assert.equal(h.errors.length, cancel ? 0 : 1);
  }
});
test('cancellation aborts a body stream and suppresses errors/progress', async () => {
  let signal;
  const h = harness({ fetcher: async (_, options) => { signal = options.signal; return new Response(new ReadableStream({ start() {} })); } });
  await tick(); h.load.cancel();
  assert.ok(signal.aborted); assert.equal(h.errors.length, 0); assert.equal(h.progress.length, 0);
});
