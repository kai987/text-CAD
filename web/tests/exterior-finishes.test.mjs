import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { inflateSync } from 'node:zlib';

const bytes = await readFile(new URL('../../GLB/house_3d.glb', import.meta.url));
const jsonLength = bytes.readUInt32LE(12);
const document = JSON.parse(bytes.subarray(20, 20 + jsonLength));
const binary = bytes.subarray(28 + jsonLength);

function crc32(bytes) {
  let value = 0xffffffff;
  for (const byte of bytes) {
    value ^= byte;
    for (let i = 0; i < 8; i++) value = (value >>> 1) ^ (value & 1 ? 0xedb88320 : 0);
  }
  return (value ^ 0xffffffff) >>> 0;
}

test('exterior PNG finishes are valid, self-contained and original procedural assets', () => {
  const source = document.asset.extras.exteriorFinishes;
  assert.match(source.source, /Original deterministic/);
  assert.deepEqual(source.sidingTileMetres, [1.82, .455]);
  assert.deepEqual(source.timberTileMetres, [.15, 2.8]);
  assert.equal(document.images.length, 2);
  for (const image of document.images) {
    assert.equal(image.uri, undefined, 'no external texture URL');
    assert.equal(image.mimeType, 'image/png');
    const view = document.bufferViews[image.bufferView];
    assert.equal(view.buffer, 0);
    const png = binary.subarray(view.byteOffset, view.byteOffset + view.byteLength);
    assert.equal(png.subarray(0, 8).toString('hex'), '89504e470d0a1a0a');
    const compressed = [];
    let header, ended = false;
    for (let offset = 8; offset < png.length;) {
      const length = png.readUInt32BE(offset);
      const type = png.toString('ascii', offset + 4, offset + 8);
      const data = png.subarray(offset + 8, offset + 8 + length);
      assert.equal(crc32(png.subarray(offset + 4, offset + 8 + length)), png.readUInt32BE(offset + 8 + length));
      if (type === 'IHDR') header = data;
      if (type === 'IDAT') compressed.push(data);
      if (type === 'IEND') ended = true;
      offset += length + 12;
    }
    assert.ok(ended && header && compressed.length);
    assert.equal(header.readUInt32BE(0), 256);
    assert.equal(header.readUInt32BE(4), 256);
    assert.equal(header[8], 8); assert.equal(header[9], 2, 'RGB8 texture');
    assert.equal(inflateSync(Buffer.concat(compressed)).length, 256 * (1 + 256 * 3));
  }
});

test('every exterior siding/timber primitive has correctly scaled metre-space UVs', () => {
  const textured = document.nodes.filter(node => node.mesh !== undefined &&
    (node.name.includes(':cladding:') || node.name.includes(':entry_panel:') || node.name === 'F1:D01_door_swing'));
  assert.equal(textured.length, 12, '8 floor siding, 2 gables, entry accent and entry door');
  for (const node of textured) for (const primitive of document.meshes[node.mesh].primitives) {
    const wood = node.name.includes(':entry_panel:') || node.name === 'F1:D01_door_swing';
    const position = document.accessors[primitive.attributes.POSITION];
    const uv = document.accessors[primitive.attributes.TEXCOORD_0];
    assert.equal(uv.componentType, 5126); assert.equal(uv.type, 'VEC2');
    assert.equal(uv.count, position.count);
    const pv = document.bufferViews[position.bufferView], tv = document.bufferViews[uv.bufferView];
    const side = node.name.split(':').at(-1);
    const width = wood ? .15 : 1.82, height = wood ? 2.8 : .455;
    for (let i = 0; i < uv.count; i++) {
      const p = (pv.byteOffset ?? 0) + (position.byteOffset ?? 0) + i * (pv.byteStride ?? 12);
      const t = (tv.byteOffset ?? 0) + (uv.byteOffset ?? 0) + i * (tv.byteStride ?? 8);
      const x = binary.readFloatLE(p), y = binary.readFloatLE(p + 4), z = binary.readFloatLE(p + 8);
      const u = binary.readFloatLE(t), v = binary.readFloatLE(t + 4);
      assert.ok(Number.isFinite(u) && Number.isFinite(v));
      assert.ok(Math.abs(u - (['west', 'east'].includes(side) ? -z : x) / width) < 1e-5, node.name);
      assert.ok(Math.abs(v - y / height) < 1e-5, node.name);
    }
    const pbr = document.materials[primitive.material].pbrMetallicRoughness;
    assert.ok(pbr.baseColorTexture);
    const texture = document.textures[pbr.baseColorTexture.index];
    const sampler = document.samplers[texture.sampler];
    assert.equal(sampler.wrapS, 10497); assert.equal(sampler.wrapT, 10497);
    assert.equal(pbr.metallicFactor, 0);
  }
});
