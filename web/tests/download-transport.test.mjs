import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { gzipSync } from 'node:zlib';
import { randomBytes } from 'node:crypto';
import { artifactTransport } from '../scripts/artifact-transport.mjs';
import { selectDownloadTransport, isArtifactMetadata } from '../src/download-transport.ts';
import { artifactUrl, artifactDownloadRequests } from '../src/asset-url.ts';
import { requireDownloadTransport, downloadResource, DownloadError } from '../src/download-resource.ts';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
function records(path, source, level = 9) {
  const packed = gzipSync(source, { level });
  return { [path]: { bytes: source.length, sha256: sha(source), transport: 'gzip' },
    [`${path}.gz`]: { bytes: packed.length, sha256: sha(packed), decodedBytes: source.length, decodedSha256: sha(source) } };
}
test('logical GLB and DXF downloads use the gzip entry hash rather than the original hash', () => {
  for (const path of ['GLB/tokyo_skytree.glb', 'DXF/tokyo_skytree_elevation.dxf']) {
    const source = Buffer.from('Exact source names and coordinates.\n'.repeat(300));
    const first = records(path, source, 1), second = records(path, source, 9);
    const urls = [first, second].map(manifest => {
      const selected = selectDownloadTransport(path, manifest);
      assert.equal(selected.path, `${path}.gz`); assert.equal(selected.compression, 'gzip');
      const hashes = Object.fromEntries(Object.entries(manifest).map(([name, entry]) => [name, entry.sha256]));
      const url = artifactUrl('/text-CAD/', selected.path, hashes, 'manifest');
      assert.ok(url.endsWith(`?v=${manifest[`${path}.gz`].sha256}`));
      assert.notEqual(manifest[path].sha256, manifest[`${path}.gz`].sha256);
      return url;
    });
    assert.notEqual(urls[0], urls[1], 're-encoding must invalidate the gzip URL while preserving the original');
  }
});
test('under-limit gzip-only STEP, GLB and DXF downloads restore native bytes without raw requests', async () => {
  for (const type of ['STEP', 'GLB', 'DXF']) {
    const path = `CAD/model.${type.toLowerCase()}`, body = 'Named CAD geometry and exact coordinates.\n'.repeat(100);
    const source = type === 'GLB' ? Buffer.alloc(4096, 0x20)
      : Buffer.from(type === 'STEP' ? `ISO-10303-21;\nDATA;\n${body}ENDSEC;\nEND-ISO-10303-21;`
        : `0\nSECTION\n2\nENTITIES\n999\n${body}0\nENDSEC\n0\nEOF\n`);
    if (type === 'GLB') { source.write('glTF'); source.writeUInt32LE(2, 4); source.writeUInt32LE(source.length, 8); }
    const transfer = artifactTransport(path, source);
    const selected = selectDownloadTransport(path, transfer.records, type === 'STEP');
    assert.equal(transfer.records[path].transport, 'gzip');
    assert.deepEqual(transfer.files.map(([name]) => name), [`${path}.gz`]);
    const requests = artifactDownloadRequests(selected, (name, hash) => artifactUrl('/', name, {}, 'catalog', hash));
    const fetched = [];
    const restored = await downloadResource({ ...requests, type, compression: selected.compression, metadata: selected.metadata,
      fetcher: async url => { fetched.push(url); return new Response(transfer.files[0][1]); } });
    assert.deepEqual(Buffer.from(await restored.arrayBuffer()), source);
    assert.deepEqual(fetched, [`/artifacts/${path}.gz?v=${transfer.records[`${path}.gz`].sha256}`]);
  }
});
test('gzip-only originals cannot fall back to a missing or inconsistently bound payload', async () => {
  const path = 'large.dxf', manifest = records(path, Buffer.from('0\nSECTION\n0\nENDSEC\n'));
  const missing = structuredClone(manifest); delete missing[`${path}.gz`];
  assert.equal(selectDownloadTransport(path, missing), null);
  const stale = structuredClone(manifest); stale[`${path}.gz`].decodedBytes++;
  assert.equal(selectDownloadTransport(path, stale), null);
  await assert.rejects(requireDownloadTransport('/bad-manifest', path, { manifest: stale }),
    error => error instanceof DownloadError && error.code === 'manifest');
});
test('legacy STEP encoded metadata remains compatible and first-click metadata is awaited', async () => {
  const path = 'house.step', manifest = records(path, Buffer.from('ISO-10303-21;\nDATA;\nENDSEC;'));
  delete manifest[path];
  const selected = await requireDownloadTransport('/early-manifest', path, { compressedStep: true,
    fetcher: async () => Response.json(manifest) });
  assert.equal(selected.path, `${path}.gz`); assert.deepEqual(selected.metadata, manifest[`${path}.gz`]);
});
test('ordinary raw metadata and unsupported decoded records retain strict selection rules', () => {
  const raw = { bytes: 5, sha256: sha('plain') };
  assert.deepEqual(selectDownloadTransport('plain.py', { 'plain.py': raw }), { path: 'plain.py', metadata: raw });
  assert.equal(isArtifactMetadata({ ...raw, transport: 'brotli' }), false);
  assert.equal(isArtifactMetadata({ ...raw, decodedBytes: 5 }), false);
  assert.equal(isArtifactMetadata({ ...raw, decodedBytes: 5, decodedSha256: 'wrong' }), false);
});
test('chunked STEP resolves only complete, ordered, matching physical manifest records', () => {
  const { records: manifest } = artifactTransport('large.step', Buffer.from(randomBytes(1024).toString('hex')), 800);
  const selected = selectDownloadTransport('large.step', manifest, true);
  assert.equal(selected.metadata.transport, 'chunks');
  for (const changed of ['missing', 'duplicate', 'reordered', 'mismatched-path']) {
    const bad = structuredClone(manifest), parts = bad['large.step.gz'].parts;
    if (changed === 'missing') delete bad[parts[0].path];
    if (changed === 'duplicate') parts[1] = parts[0];
    if (changed === 'reordered') parts.reverse();
    if (changed === 'mismatched-path') parts[0].path = 'other.step.gz.part-001';
    assert.equal(selectDownloadTransport('large.step', bad, true), null, changed);
  }
});

test('component request and fallback URLs follow the selected gzip encoding despite stale compiled hashes', async () => {
  const path = 'STEP/tower.step';
  const source = Buffer.from('ISO-10303-21;\nDATA;\n' + "#1=NAME('EXACT SOURCE');\n".repeat(100) + 'ENDSEC;\nEND-ISO-10303-21;');
  const oldEncoding = gzipSync(source, { level: 1 }), currentEncoding = gzipSync(source, { level: 9 });
  const previous = records(path, source, 1), current = records(path, source, 9);
  assert.equal(previous[path].sha256, current[path].sha256);
  assert.notEqual(previous[`${path}.gz`].sha256, current[`${path}.gz`].sha256);
  const compiled = Object.fromEntries(Object.entries(previous).map(([name, entry]) => [name, entry.sha256]));
  const selected = selectDownloadTransport(path, current, true);
  for (const base of ['/', '/text-CAD/']) {
    // This is the pure request builder used by DownloadFile for the row href,
    // ordinary downloads and compressed fallback, through asset's resolver.
    const resolve = (name, selectedHash) => artifactUrl(base, name, compiled, 'old-catalog', selectedHash);
    const requests = artifactDownloadRequests(selected, resolve);
    assert.equal(requests.url, `${base}artifacts/${path}.gz?v=${current[`${path}.gz`].sha256}`);
    const fetched = [];
    const fetcher = async url => {
      fetched.push(url);
      return new Response(new URL(url, 'https://cad.example').searchParams.get('v') === sha(currentEncoding)
        ? currentEncoding : oldEncoding);
    };
    const restored = await downloadResource({ ...requests, type: 'STEP', compression: selected.compression,
      metadata: selected.metadata, fetcher });
    assert.deepEqual(Buffer.from(await restored.arrayBuffer()), source);
    const fallback = await downloadResource({ ...requests, type: 'STEP', compression: selected.compression,
      metadata: selected.metadata, decompress: false, fetcher });
    assert.equal(sha(Buffer.from(await fallback.arrayBuffer())), sha(currentEncoding));
    assert.deepEqual(fetched, [requests.url, requests.url]);
  }
  assert.throws(() => artifactUrl('/', path, compiled, 'old-catalog', 'invalid'), /selected artifact hash/);
});

test('component chunk requests use each selected part hash and never fetch the absent aggregate gzip', async () => {
  const path = 'STEP/chunked.step';
  const source = Buffer.from('ISO-10303-21;\nDATA;\n' + randomBytes(1024).toString('hex') + '\nENDSEC;\nEND-ISO-10303-21;');
  const transfer = artifactTransport(path, source, 800), selected = selectDownloadTransport(path, transfer.records, true);
  const compiled = Object.fromEntries(Object.keys(transfer.records).map(name => [name, '0'.repeat(64)]));
  const resolve = (name, selectedHash) => artifactUrl('/text-CAD/', name, compiled, 'old-catalog', selectedHash);
  const requests = artifactDownloadRequests(selected, resolve);
  assert.equal(requests.parts.length, 2);
  const paths = new Map(transfer.files.map(([name, bytes]) => [name, bytes]));
  const fetched = [];
  const fetcher = async url => {
    fetched.push(url);
    assert.notEqual(url, requests.url);
    const parsed = new URL(url, 'https://cad.example'), name = parsed.pathname.replace('/text-CAD/artifacts/', '');
    assert.equal(parsed.searchParams.get('v'), transfer.records[name].sha256);
    return new Response(paths.get(name));
  };
  const restored = await downloadResource({ ...requests, type: 'STEP', compression: selected.compression,
    metadata: selected.metadata, fetcher });
  assert.deepEqual(Buffer.from(await restored.arrayBuffer()), source);
  assert.deepEqual(fetched, requests.parts.map(part => part.url));
  const fallback = await downloadResource({ ...requests, type: 'STEP', compression: selected.compression,
    metadata: selected.metadata, decompress: false, fetcher });
  assert.equal(sha(Buffer.from(await fallback.arrayBuffer())), selected.metadata.sha256);
});

test('native CAD with more than two parts preserves every binding and reconstructs exact bytes', async () => {
  const path = 'STEP/detailed.step';
  const source = Buffer.from('ISO-10303-21;\nDATA;\n' + randomBytes(4096).toString('hex') + '\nENDSEC;\nEND-ISO-10303-21;');
  const transfer = artifactTransport(path, source, 800);
  const selected = selectDownloadTransport(path, transfer.records, true);
  assert.ok(selected.metadata.parts.length > 2);
  for (const damage of ['last-missing', 'last-prefix', 'last-order', 'too-many']) {
    const manifest = structuredClone(transfer.records), parts = manifest[`${path}.gz`].parts;
    if (damage === 'last-missing') delete manifest[parts.at(-1).path];
    if (damage === 'last-prefix') parts.at(-1).path = 'OTHER/detailed.step.gz.part-' + String(parts.length).padStart(3, '0');
    if (damage === 'last-order') [parts[2], parts[3]] = [parts[3], parts[2]];
    if (damage === 'too-many') manifest[`${path}.gz`].parts = Array.from({ length: 33 }, (_, index) => ({ ...parts[0], path: `${path}.gz.part-${String(index + 1).padStart(3, '0')}` }));
    assert.equal(selectDownloadTransport(path, manifest, true), null, damage);
  }
  const requests = artifactDownloadRequests(selected, (name, hash) => artifactUrl('/', name, {}, 'catalog', hash));
  const payloads = new Map(transfer.files), fetched = [];
  const fetcher = async url => {
    const name = new URL(url, 'https://cad.example').pathname.replace('/artifacts/', '');
    fetched.push(name);
    return new Response(payloads.get(name));
  };
  const restored = await downloadResource({ ...requests, type: 'STEP', compression: 'gzip', metadata: selected.metadata, fetcher });
  assert.deepEqual(Buffer.from(await restored.arrayBuffer()), source);
  assert.deepEqual(fetched, selected.metadata.parts.map(part => part.path));
  const badRequests = { ...requests, parts: requests.parts.slice(0, -1) };
  await assert.rejects(downloadResource({ ...badRequests, type: 'STEP', compression: 'gzip', metadata: selected.metadata, fetcher }), error => error instanceof DownloadError && error.code === 'manifest');
});
