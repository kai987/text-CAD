import test from 'node:test';
import assert from 'node:assert/strict';
import { withoutMaterialTexturesForGeometry } from './helpers/load-glb-geometry.mjs';

function glb(document, binary) {
  const json = new TextEncoder().encode(JSON.stringify(document));
  const length = Math.ceil(json.byteLength / 4) * 4;
  const result = new Uint8Array(28 + length + binary.byteLength);
  const view = new DataView(result.buffer);
  view.setUint32(0, 0x46546c67, true); view.setUint32(4, 2, true);
  view.setUint32(8, result.byteLength, true); view.setUint32(12, length, true);
  view.setUint32(16, 0x4e4f534a, true);
  result.fill(0x20, 20, 20 + length); result.set(json, 20);
  view.setUint32(20 + length, binary.byteLength, true);
  view.setUint32(24 + length, 0x004e4942, true); result.set(binary, 28 + length);
  return result;
}

function unpack(bytes) {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const jsonEnd = 20 + view.getUint32(12, true);
  assert.equal(view.getUint32(8, true), bytes.byteLength, 'valid GLB total length');
  assert.equal(view.getUint32(jsonEnd + 4, true), 0x004e4942, 'valid BIN chunk location');
  return { document: JSON.parse(new TextDecoder().decode(bytes.subarray(20, jsonEnd))),
    binary: bytes.subarray(jsonEnd + 8) };
}

test('Node geometry loading strips texture references only and keeps geometry, UVs, CAD names and factors intact', () => {
  const document = {
    asset: { version: '2.0' }, nodes: [{ name: 'F1:exterior:cladding:east', mesh: 0 }],
    meshes: [{ primitives: [{ attributes: { POSITION: 0, TEXCOORD_0: 1 }, indices: 2, material: 0 }] }],
    accessors: [{ type: 'VEC3', count: 3 }, { type: 'VEC2', count: 3 }, { type: 'SCALAR', count: 3 }],
    buffers: [{ byteLength: 8 }], bufferViews: [{ buffer: 0, byteOffset: 0, byteLength: 8 }],
    images: [{ bufferView: 0, mimeType: 'image/png' }], textures: [{ source: 0 }],
    materials: [{ name: 'facade', pbrMetallicRoughness: {
      baseColorFactor: [0.8, 0.7, 0.6, 1], metallicFactor: 0.1, roughnessFactor: 0.9,
      baseColorTexture: { index: 0 }, metallicRoughnessTexture: { index: 0 } },
      normalTexture: { index: 0, scale: 0.5 }, occlusionTexture: { index: 0 },
      emissiveFactor: [0.1, 0.2, 0.3], emissiveTexture: { index: 0 }, alphaMode: 'OPAQUE',
      extensions: { KHR_materials_specular: { specularFactor: 0.7, specularTexture: { index: 0 } } } }],
  };
  const binary = new Uint8Array([1, 3, 7, 15, 31, 63, 127, 255]);
  const original = glb(document, binary), snapshot = original.slice();
  const converted = unpack(new Uint8Array(withoutMaterialTexturesForGeometry(original)));
  assert.deepEqual(original, snapshot, 'the source GLB buffer is never modified');
  assert.deepEqual(converted.binary, binary, 'the entire binary payload is preserved byte for byte');
  const { materials: ignored, ...preserved } = document;
  const { materials, ...actualPreserved } = converted.document;
  assert.deepEqual(actualPreserved, preserved, 'all geometry metadata, names, UVs and embedded images are retained');
  assert.deepEqual(materials, [{ name: 'facade', pbrMetallicRoughness: {
    baseColorFactor: [0.8, 0.7, 0.6, 1], metallicFactor: 0.1, roughnessFactor: 0.9 },
    emissiveFactor: [0.1, 0.2, 0.3], alphaMode: 'OPAQUE',
    extensions: { KHR_materials_specular: { specularFactor: 0.7 } } }],
  'core and extension texture references are removed without changing material factors');
});
