import test from 'node:test';
import assert from 'node:assert/strict';
import { createAsyncResourceCache } from '../src/async-resource-cache.ts';

function deferred() {
  let resolve, reject;
  const promise = new Promise((onResolve, onReject) => { resolve = onResolve; reject = onReject; });
  return { promise, resolve, reject };
}

test('concurrent prefetch and view requests share one pending resource', async () => {
  const request = deferred();
  const paths = [];
  const cache = createAsyncResourceCache(path => { paths.push(path); return request.promise; });
  const prefetch = cache.load('house_1f.svg');
  const view = cache.load('house_1f.svg');
  assert.equal(prefetch, view);
  assert.equal(cache.getCached('house_1f.svg'), undefined);
  await Promise.resolve();
  assert.deepEqual(paths, ['house_1f.svg']);
  request.resolve('<g>first floor</g>');
  assert.equal(await prefetch, '<g>first floor</g>');
  assert.equal(await view, '<g>first floor</g>');
});

test('successful resources are synchronously available and reused without loading again', async () => {
  let calls = 0;
  const cache = createAsyncResourceCache(async () => { calls += 1; return ''; });
  const first = cache.load('apartment.svg');
  assert.equal(await first, '');
  assert.equal(cache.getCached('apartment.svg'), '');
  assert.equal(cache.load('apartment.svg'), first);
  assert.equal(calls, 1);
});

test('rejected resources are discarded so opening the plan can retry', async () => {
  let calls = 0;
  const cache = createAsyncResourceCache(async () => {
    calls += 1;
    if (calls === 1) throw new Error('Temporary connection failure');
    return '<g>recovered</g>';
  });
  const first = cache.load('house_2f.svg');
  await assert.rejects(first, /Temporary connection failure/);
  assert.equal(cache.getCached('house_2f.svg'), undefined);
  const retry = cache.load('house_2f.svg');
  assert.notEqual(retry, first);
  assert.equal(await retry, '<g>recovered</g>');
  assert.equal(cache.getCached('house_2f.svg'), '<g>recovered</g>');
  assert.equal(calls, 2);
});

test('independent floors start in parallel and one failure does not block another', async () => {
  const first = deferred(), second = deferred();
  const started = [];
  const cache = createAsyncResourceCache(path => {
    started.push(path);
    return path === 'first.svg' ? first.promise : second.promise;
  });
  const firstLoad = cache.load('first.svg'), secondLoad = cache.load('second.svg');
  const preload = Promise.allSettled([firstLoad, secondLoad]);
  await Promise.resolve();
  assert.deepEqual(started, ['first.svg', 'second.svg']);
  second.resolve('<g>second floor</g>');
  assert.equal(await secondLoad, '<g>second floor</g>');
  assert.equal(cache.getCached('second.svg'), '<g>second floor</g>');
  assert.equal(cache.getCached('first.svg'), undefined);
  first.reject(new Error('First floor missing'));
  assert.deepEqual((await preload).map(result => result.status), ['rejected', 'fulfilled']);
});
