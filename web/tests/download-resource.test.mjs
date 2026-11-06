import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash, randomBytes } from 'node:crypto';
import { gzipSync } from 'node:zlib';
import { downloadResource, verifyDownload, loadDownloadManifest, requireDownloadMetadata, DownloadError } from '../src/download-resource.ts';
import { downloadCopy, downloadErrorText, downloadProgressText, formatDownloadBytes } from '../src/download-copy.ts';
import { artifactTransport, STATIC_FILE_LIMIT } from '../scripts/artifact-transport.mjs';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const metadata = bytes => ({ bytes: bytes.length, sha256: sha(bytes) });
const code = expected => error => error instanceof DownloadError && error.code === expected;

test('streamed CAD download reports transferred bytes and preserves the exact payload', async () => {
  const source = Buffer.alloc(32); source.write('glTF'); source.writeUInt32LE(2, 4); source.writeUInt32LE(source.length, 8);
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

test('gzip-only large GLB and DXF downloads restore exact originals and handle transparent host decompression', async () => {
  const glb = Buffer.alloc(STATIC_FILE_LIMIT + 1024, 0x20);
  glb.write('glTF'); glb.writeUInt32LE(2, 4); glb.writeUInt32LE(glb.length, 8);
  const dxf = Buffer.from('0\nSECTION\n2\nENTITIES\n' + '999\nreference member\n'.repeat(STATIC_FILE_LIMIT / 19 + 100) + '0\nENDSEC\n0\nEOF\n');
  for (const [name, type, source] of [['tower.glb', 'GLB', glb], ['tower.dxf', 'DXF', dxf]]) {
    const transfer = artifactTransport(name, source);
    const entry = transfer.records[`${name}.gz`], encoded = transfer.files[0][1];
    assert.equal(transfer.records[name].transport, 'gzip');
    for (const response of [new Response(encoded), new Response(source, { headers: { 'Content-Encoding': 'gzip' } })]) {
      const progress = [];
      const result = await downloadResource({ url: `/${name}.gz`, type, compression: 'gzip', metadata: entry,
        fetcher: async () => response, onProgress: update => progress.push(update) });
      assert.deepEqual(Buffer.from(await result.arrayBuffer()), source);
      assert.equal(progress.at(-1).total, response.headers.has('Content-Encoding') ? source.length : entry.bytes);
    }
    await assert.rejects(downloadResource({ url: `/${name}.gz`, type, compression: 'gzip',
      metadata: { ...entry, sha256: '0'.repeat(64) }, fetcher: async () => new Response(encoded) }), code('integrity'));
    await assert.rejects(downloadResource({ url: `/${name}.gz`, type, compression: 'gzip',
      metadata: { ...entry, decodedSha256: '0'.repeat(64) }, fetcher: async () => new Response(encoded) }), code('integrity'));
  }
});

test('generic gzip requires decoded integrity and checks the restored original format', async () => {
  const source = Buffer.from('<html>not a CAD file</html>'), packed = gzipSync(source);
  for (const type of ['GLB', 'DXF']) {
    const entry = { ...metadata(packed), decodedBytes: source.length, decodedSha256: sha(source) };
    await assert.rejects(downloadResource({ url: '/bad.gz', type, compression: 'gzip', metadata: entry,
      fetcher: async () => new Response(packed) }), code('format'));
    await assert.rejects(downloadResource({ url: '/bad.gz', type, compression: 'gzip', metadata: metadata(packed),
      fetcher: async () => new Response(packed) }), code('manifest'));
  }
});

function chunkedStep() {
  const source = Buffer.from('ISO-10303-21;\nDATA;\n#1=NAME(\'' + randomBytes(1024).toString('hex') + '\');\nENDSEC;\nEND-ISO-10303-21;');
  const transport = artifactTransport('large.step', source, 800), metadata = transport.records['large.step.gz'];
  assert.equal(metadata.transport, 'chunks');
  const parts = metadata.parts.map(part => ({ url: `/${part.path}?v=${part.sha256}`, metadata: transport.records[part.path] }));
  return { source, transport, options: { url: '/large.step.gz', type: 'STEP', compression: 'gzip', metadata, parts } };
}
test('chunked STEP verifies ordered pieces and both whole hashes, with aggregate progress and exact restored bytes', async () => {
  const { source, transport, options } = chunkedStep(), paths = [], progress = [];
  const result = await downloadResource({ ...options, onProgress: update => progress.push(update), fetcher: async url => {
    paths.push(url);
    const index = options.parts.findIndex(part => part.url === url); assert.ok(index >= 0);
    return new Response(transport.files[index][1]);
  } });
  assert.deepEqual(paths, options.parts.map(part => part.url));
  assert.deepEqual(Buffer.from(await result.arrayBuffer()), source);
  assert.equal(progress.at(-1).loaded, options.metadata.bytes); assert.equal(progress.at(-1).total, options.metadata.bytes);
});
test('chunked compressed fallback assembles an exact gzip without requiring browser decompression', async () => {
  const { transport, options } = chunkedStep(), original = globalThis.DecompressionStream;
  try {
    globalThis.DecompressionStream = undefined;
    const result = await downloadResource({ ...options, decompress: false,
      fetcher: async url => new Response(transport.files[options.parts.findIndex(part => part.url === url)][1]) });
    assert.deepEqual(Buffer.from(await result.arrayBuffer()), Buffer.concat(transport.files.map(([, payload]) => payload)));
  } finally { globalThis.DecompressionStream = original; }
});
test('missing, duplicate, reordered and mismatched chunk requests fail before any transfer', async () => {
  for (const changed of ['missing', 'duplicate', 'reordered', 'wrong-path']) {
    const { options } = chunkedStep(); let fetched = false;
    if (changed === 'missing') options.parts.pop();
    if (changed === 'duplicate') options.parts[1] = options.parts[0];
    if (changed === 'reordered') options.parts.reverse();
    if (changed === 'wrong-path') options.parts[0].url = '/other.step.gz.part-001';
    await assert.rejects(downloadResource({ ...options, fetcher: async () => { fetched = true; return new Response('bad'); } }), code('manifest'));
    assert.equal(fetched, false);
  }
});
test('chunk corruption, truncation and aggregate rebinding cannot produce a saved STEP', async () => {
  for (const changed of ['corrupt', 'truncate', 'aggregate']) {
    const { transport, options } = chunkedStep();
    if (changed === 'aggregate') options.metadata.sha256 = '0'.repeat(64);
    await assert.rejects(downloadResource({ ...options, fetcher: async url => {
      const index = options.parts.findIndex(part => part.url === url);
      let bytes = Buffer.from(transport.files[index][1]);
      if (index === 0 && changed === 'corrupt') bytes[10] ^= 1;
      if (index === 0 && changed === 'truncate') bytes = bytes.subarray(0, bytes.length - 1);
      return new Response(bytes);
    } }), code('integrity'));
  }
});
test('cancelling chunked STEP after its first part never requests the next part', async () => {
  const { transport, options } = chunkedStep(), controller = new AbortController(), paths = [];
  await assert.rejects(downloadResource({ ...options, signal: controller.signal,
    onProgress: update => { if (update.loaded >= options.parts[0].metadata.bytes) controller.abort(); },
    fetcher: async url => { paths.push(url); return new Response(transport.files[0][1]); } }), error => error.name === 'AbortError');
  assert.deepEqual(paths, [options.parts[0].url]);
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
  assert.equal(await loadDownloadManifest('/manifest.json?v=one', fetcher), results[0]);
  assert.equal(requests, 1, 'successful catalogs remain deduplicated by default');
  await loadDownloadManifest('/manifest.json?v=two', fetcher);
  assert.equal(requests, 2);
  assert.equal(await loadDownloadManifest('/missing-manifest', async () => new Response('', { status: 503 })), null);
  assert.deepEqual(await loadDownloadManifest('/missing-manifest', fetcher), { 'case.json': metadata(source) });
});

test('explicit manifest reload replaces cached success and bypasses the HTTP cache', async () => {
  const url = '/manifest.json?v=explicit-reload', original = metadata(Buffer.from('old')), latest = metadata(Buffer.from('new catalog'));
  const cacheModes = []; let requests = 0;
  const fetcher = async (requested, options) => {
    assert.equal(requested, url); assert.ok(options.signal instanceof AbortSignal);
    cacheModes.push(options.cache); requests++;
    return Response.json({ 'case.json': requests === 1 ? original : latest });
  };
  const first = loadDownloadManifest(url, fetcher);
  assert.deepEqual(await first, { 'case.json': original });
  assert.equal(loadDownloadManifest(url, fetcher), first);
  const refreshed = loadDownloadManifest(url, fetcher, { reload: true });
  assert.notEqual(refreshed, first);
  assert.equal(loadDownloadManifest(url, fetcher), refreshed, 'ordinary callers share the reload while it is pending');
  assert.deepEqual(await refreshed, { 'case.json': latest });
  assert.equal(loadDownloadManifest(url, fetcher, { reload: false }), refreshed);
  assert.equal(requests, 2); assert.deepEqual(cacheModes, [undefined, 'reload']);
});

test('a superseded failing manifest request cannot evict a successful forced reload', async () => {
  const url = '/manifest.json?v=superseded-failure', latest = { 'case.json': metadata(Buffer.from('fresh catalog')) };
  let failOld;
  const oldFailure = new Promise(resolve => { failOld = resolve; });
  let oldStarted;
  const started = new Promise(resolve => { oldStarted = resolve; });
  const old = loadDownloadManifest(url, async () => {
    oldStarted(); await oldFailure; throw new TypeError('Superseded network request failed late');
  });
  await started;
  const fresh = loadDownloadManifest(url, async (_url, options) => {
    assert.equal(options.cache, 'reload'); return Response.json(latest);
  }, { reload: true });
  try {
    assert.notEqual(fresh, old, 'an explicit reload bypasses a pending older request');
    assert.deepEqual(await fresh, latest);
    failOld(); assert.equal(await old, null);
    let unexpectedRequest = false;
    const retained = loadDownloadManifest(url, async () => { unexpectedRequest = true; return Response.json({}); });
    assert.equal(retained, fresh, 'the late failure leaves the latest cached promise intact');
    assert.deepEqual(await retained, latest); assert.equal(unexpectedRequest, false);
  } finally { failOld(); await old; }
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
