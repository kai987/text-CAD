import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { gzipSync } from 'node:zlib';
import { downloadResource, verifyDownload, loadDownloadManifest, requireDownloadMetadata, DownloadError } from '../src/download-resource.ts';
import { downloadCopy, downloadErrorText, downloadProgressText, formatDownloadBytes } from '../src/download-copy.ts';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const metadata = bytes => ({ bytes: bytes.length, sha256: sha(bytes) });
const code = expected => error => error instanceof DownloadError && error.code === expected;

test('streamed CAD download reports transferred bytes and preserves the exact payload', async () => {
  const source = Buffer.from('glTF exact model payload');
  const updates = [];
  let processing = 0;
  const stream = new ReadableStream({ start(controller) {
    controller.enqueue(source.subarray(0, 4)); controller.enqueue(source.subarray(4)); controller.close();
  } });
  const blob = await downloadResource({ url: '/model.glb', type: 'GLB', metadata: metadata(source),
    fetcher: async () => new Response(stream), onProgress: progress => updates.push(progress), onProcessing: () => processing++ });
  assert.deepEqual(Buffer.from(await blob.arrayBuffer()), source);
  assert.equal(updates[0].loaded, 4);
  assert.equal(updates.at(-1).loaded, source.length);
  assert.equal(updates.at(-1).total, source.length);
  assert.equal(processing, 1);
});

test('same-size corruption and truncation are rejected before a file can be saved', async () => {
  const source = Buffer.from('%PDF-1.7\noriginal');
  for (const changed of [Buffer.from('%PDF-1.7\nmodified'), source.subarray(0, 8)]) {
    await assert.rejects(downloadResource({ url: '/plan.pdf', type: 'PDF', metadata: metadata(source),
      fetcher: async () => new Response(changed) }), code('integrity'));
  }
});

test('HTTP failures and HTTP 200 HTML error pages cannot be saved as CAD', async () => {
  await assert.rejects(downloadResource({ url: '/missing', type: 'DXF', fetcher: async () => new Response('', { status: 404 }) }),
    error => error.code === 'http' && error.status === 404);
  for (const type of ['DXF', 'STEP', 'GLB', 'PDF', 'PY', 'JSON']) {
    await assert.rejects(downloadResource({ url: '/bad', type, fetcher: async () => new Response('<!DOCTYPE html><html>Not found</html>') }), code('format'));
  }
  await assert.rejects(downloadResource({ url: '/bad.json', type: 'JSON', fetcher: async () => new Response('{ invalid') }), code('format'));
});

test('STEP transport checks both compressed and restored bytes, including host auto-decompression', async () => {
  const source = Buffer.from('ISO-10303-21;\nDATA;\n#1=EXACT(1.23456);\nENDSEC;\nEND-ISO-10303-21;');
  const compressed = gzipSync(source);
  const entry = { ...metadata(compressed), decodedBytes: source.length, decodedSha256: sha(source) };
  for (const response of [new Response(compressed), new Response(source, { headers: { 'Content-Encoding': 'gzip' } })]) {
    const blob = await downloadResource({ url: '/house.step.gz?v=release', type: 'STEP', compressedStep: true, metadata: entry,
      fetcher: async url => { assert.equal(url, '/house.step.gz?v=release'); return response; } });
    assert.deepEqual(Buffer.from(await blob.arrayBuffer()), source);
  }
  await assert.rejects(downloadResource({ url: '/house.step.gz', type: 'STEP', compressedStep: true,
    metadata: { ...entry, decodedSha256: '0'.repeat(64) }, fetcher: async () => new Response(compressed) }), code('integrity'));
  await assert.rejects(downloadResource({ url: '/house.step.gz', type: 'STEP', compressedStep: true,
    fetcher: async () => new Response(gzipSync('<html>wrong</html>')) }), code('format'));
});

test('cancel stops a pending stream and does not become an error or trigger a second request', async () => {
  const controller = new AbortController();
  let requests = 0;
  let cancelled = false;
  const stream = new ReadableStream({ start(streamController) { streamController.enqueue(Buffer.from('glTF')); },
    cancel() { cancelled = true; } });
  const promise = downloadResource({ url: '/model.glb', type: 'GLB', signal: controller.signal,
    fetcher: async () => { requests++; return new Response(stream); }, onProgress() { controller.abort(); } });
  await assert.rejects(promise, error => error.name === 'AbortError');
  assert.equal(cancelled, true);
  assert.equal(requests, 1);
});

test('a fresh retry succeeds after cancellation; pre-cancelled requests do not fetch', async () => {
  const controller = new AbortController(); controller.abort();
  let fetched = false;
  await assert.rejects(downloadResource({ url: '/file.json', type: 'JSON', signal: controller.signal,
    fetcher: async () => { fetched = true; return new Response('{}'); } }), error => error.name === 'AbortError');
  assert.equal(fetched, false);
  const blob = await downloadResource({ url: '/file.json', type: 'JSON', fetcher: async () => new Response('{}') });
  assert.equal(await blob.text(), '{}');
});

test('timeout cancels a stalled response and has a separate retryable error', async () => {
  let cancelled = false;
  const stream = new ReadableStream({ cancel() { cancelled = true; } });
  await assert.rejects(downloadResource({ url: '/model.glb', type: 'GLB', timeoutMs: 5,
    fetcher: async () => new Response(stream) }), code('timeout'));
  assert.equal(cancelled, true);
});

test('network failure is retryable; byte validation still works without Web Crypto', async () => {
  await assert.rejects(downloadResource({ url: '/file.json', type: 'JSON', fetcher: async () => { throw new TypeError('Failed to fetch'); } }), code('network'));
  const original = Object.getOwnPropertyDescriptor(globalThis, 'crypto');
  try {
    Object.defineProperty(globalThis, 'crypto', { configurable: true, value: undefined });
    await verifyDownload(new Blob(['{}']), metadata(Buffer.from('{}')));
    await assert.rejects(verifyDownload(new Blob(['{}']), metadata(Buffer.from('{"a":1}'))), code('integrity'));
  } finally { if (original) Object.defineProperty(globalThis, 'crypto', original); }
});

test('download progress and recovery messages are complete in Chinese, Japanese and English', () => {
  for (const locale of ['zh', 'ja', 'en']) {
    assert.equal(formatDownloadBytes(1_500_000, locale), '1.5 MB');
    assert.equal(formatDownloadBytes(500, locale), '500 B');
    assert.match(downloadProgressText({ loaded: 1_500, total: 3_000 }, locale), /1.5 KB \/ 3 KB/);
    assert.match(downloadProgressText({ loaded: 1_500, total: null }, locale), /1.5 KB/);
    for (const value of Object.values(downloadCopy[locale])) {
      if (typeof value === 'string') assert.ok(value.trim());
    }
    for (const code of ['http', 'network', 'timeout', 'integrity', 'format', 'manifest']) {
      const message = downloadErrorText(code, 503, locale);
      assert.ok(message.trim()); assert.ok(!message.includes('{status}'));
      if (code === 'http') assert.ok(message.includes('503'));
    }
  }
});

test('manifest is shared by concurrent downloads; failed metadata can retry and versions have distinct cache keys', async () => {
  const source = Buffer.from('{}');
  let requests = 0;
  const fetcher = async () => { requests++; return Response.json({ 'case.json': metadata(source), invalid: { bytes: -1, sha256: 'wrong' } }); };
  const results = await Promise.all([loadDownloadManifest('/manifest.json?v=one', fetcher), loadDownloadManifest('/manifest.json?v=one', fetcher)]);
  assert.equal(requests, 1);
  assert.equal(results[0], results[1]);
  assert.deepEqual(results[0]['case.json'], metadata(source));
  assert.equal(results[0].invalid, undefined);
  await loadDownloadManifest('/manifest.json?v=two', fetcher);
  assert.equal(requests, 2);
  assert.equal(await loadDownloadManifest('/missing-manifest', async () => new Response('', { status: 503 })), null);
  assert.deepEqual(await loadDownloadManifest('/missing-manifest', fetcher), { 'case.json': metadata(source) });
});

test('download refuses an unavailable manifest or missing file entry, and a later retry can obtain verified metadata', async () => {
  const source = Buffer.from('glTF fixture');
  const entry = metadata(source);
  await assert.rejects(requireDownloadMetadata('/required-manifest', 'house.glb', undefined,
    async () => new Response('', { status: 503 })), code('manifest'));
  assert.deepEqual(await requireDownloadMetadata('/required-manifest', 'house.glb', undefined,
    async () => Response.json({ 'house.glb': entry })), entry);
  await assert.rejects(requireDownloadMetadata('/missing-file-entry', 'absent.glb', undefined,
    async () => Response.json({ 'house.glb': entry })), code('manifest'));
  let fetched = false;
  assert.equal(await requireDownloadMetadata('/unused', 'house.glb', entry,
    async () => { fetched = true; return Response.json({}); }), entry);
  assert.equal(fetched, false);
});
