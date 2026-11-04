import test from 'node:test';
import assert from 'node:assert/strict';
import { gzipSync, gunzipSync } from 'node:zlib';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { startModelLoad } from '../src/model-resource.ts';
import { artifactTransport, STATIC_FILE_LIMIT } from '../scripts/artifact-transport.mjs';

function load(fetcher, extras = {}) {
  const progress = [];
  return new Promise((resolve, reject) => startModelLoad({ url: '/house.glb', compressed: true, fetcher,
    parse: async bytes => [...new Uint8Array(bytes)], onLoad: value => resolve({ value, progress }), onError: reject,
    onProgress: value => progress.push(value), disposeLate() {}, ...extras }));
}
test('compressed viewer download expands losslessly and reports transferred bytes', async () => {
  const bytes = new Uint8Array([1,2,3,4]), gz = gzipSync(bytes), paths=[];
  const result = await load(async path => { paths.push(path); return new Response(gz, { headers: { 'content-length': String(gz.length) } }); });
  assert.deepEqual(paths, ['/house.glb.gz']); assert.deepEqual(result.value, [...bytes]);
  assert.equal(result.progress.at(-1).loaded, gz.length); assert.equal(result.progress.at(-1).total, gz.length);
});
test('unavailable and broken compressed transport falls back to the original model', async () => {
  for (const failure of [new Response('',{status:404}),new Response(new Uint8Array([0x1f,0x8b,0]))]) {
    const paths=[]; const result=await load(async path => { paths.push(path); return path.endsWith('.gz') ? failure : new Response(new Uint8Array([7,8])); });
    assert.deepEqual(paths,['/house.glb.gz','/house.glb']); assert.deepEqual(result.value,[7,8]);
  }
});
test('already decoded host responses are not decompressed twice', async () => {
  const result=await load(async () => new Response(new Uint8Array([0x67,0x6c,0x54,0x46]),{headers:{'content-encoding':'gzip','content-length':'100'}}));
  assert.deepEqual(result.value,[0x67,0x6c,0x54,0x46]); assert.equal(result.progress.at(-1).total,null);
});
test('cancelling compressed downloads never starts a fallback request', async () => {
  let calls=0; let reject;
  const errors=[];
  const request=startModelLoad({url:'/house.glb',compressed:true, fetcher:()=>{calls++;return new Promise((_,r)=>{reject=r;});},parse:async()=>null,onLoad(){},onError:e=>errors.push(e),disposeLate(){}});
  await new Promise(resolve=>setImmediate(resolve)); request.cancel(); reject(new Error('Aborted'));
  await new Promise(resolve=>setImmediate(resolve)); assert.equal(calls,1); assert.deepEqual(errors,[]);
});
test('versioned gzip URL verifies decoded bytes, with an independent raw fallback hash', async () => {
  const native = new Uint8Array([1, 2, 3]), stale = new Uint8Array([4, 5, 6]);
  const expectedSha256 = createHash('sha256').update(native).digest('hex');
  const paths = [];
  const result = await load(async path => {
    paths.push(path);
    return new Response(path.includes('.gz?') ? gzipSync(stale) : native);
  }, { url: '/house.glb?v=native', compressedUrl: '/house.glb.gz?v=encoded', expectedSha256 });
  assert.deepEqual(paths, ['/house.glb.gz?v=encoded', '/house.glb?v=native']);
  assert.deepEqual(result.value, [...native]);
});
test('gzip-only viewer models below and above the file limit never request an absent raw file', async () => {
  for (const [path, size] of [['GLB/tokyo_tower.glb', 4096], ['GLB/tokyo_skytree.glb', STATIC_FILE_LIMIT + 1024]]) {
    const native = Buffer.alloc(size, 0x20);
    native.write('glTF'); native.writeUInt32LE(2, 4); native.writeUInt32LE(native.length, 8);
    const transport = artifactTransport(path, native), paths = [];
    const raw = `/artifacts/${path}?v=${transport.records[path].sha256}`;
    const encoded = `/artifacts/${path}.gz?v=${transport.records[`${path}.gz`].sha256}`;
    const result = await load(async url => {
      paths.push(url); assert.equal(url, encoded, 'healthy loads must not request the logical raw path');
      return new Response(transport.files[0][1]);
    }, { url: raw, compressedUrl: encoded, expectedSha256: transport.records[path].sha256,
      parse: async bytes => createHash('sha256').update(new Uint8Array(bytes)).digest('hex') });
    assert.deepEqual(paths, [encoded]); assert.equal(result.value, transport.records[path].sha256);
  }
});
test('corrupt native bytes are rejected before GLB parsing', async () => {
  let parses = 0;
  await assert.rejects(load(async () => new Response(new Uint8Array([4, 5, 6])), {
    compressed: false, expectedSha256: '0'.repeat(64), parse: async () => { parses++; },
  }), /checksum/);
  assert.equal(parses, 0);
});
test('all five published compressed models retain every original GLB byte', async () => {
  for (const name of ['house_3d','apartment_2ldk','structure_W','structure_S','structure_RC']) {
    const source=await readFile(new URL(`../../GLB/${name}.glb`,import.meta.url));
    const encoded=await readFile(new URL(`../public/artifacts/GLB/${name}.glb.gz`,import.meta.url));
    assert.ok(encoded.length<source.length); assert.deepEqual(gunzipSync(encoded),source);
  }
});
