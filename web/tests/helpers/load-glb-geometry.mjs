import { readFile } from 'node:fs/promises';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const GLB_MAGIC = 0x46546c67;
const JSON_CHUNK = 0x4e4f534a;

// Node geometry regressions do not decode images. Remove only material texture
// references from an in-memory GLB copy before using Three's actual GLTFLoader.
// Positions, indices, UVs, original node names, material factors, images and the
// complete binary chunks remain intact. Texture/PNG validity and rendered
// appearance are checked separately against the original downloadable asset.
export function withoutMaterialTexturesForGeometry(input) {
  const original = input instanceof ArrayBuffer ? new Uint8Array(input) : input;
  const view = new DataView(original.buffer, original.byteOffset, original.byteLength);
  if (original.byteLength < 20 || view.getUint32(0, true) !== GLB_MAGIC ||
    view.getUint32(4, true) !== 2 || view.getUint32(8, true) !== original.byteLength ||
    view.getUint32(16, true) !== JSON_CHUNK) {
    throw new Error('Geometry test loader requires a complete GLB 2.0 with a JSON first chunk');
  }
  const originalJsonLength = view.getUint32(12, true);
  const originalJsonEnd = 20 + originalJsonLength;
  if (originalJsonEnd > original.byteLength) throw new Error('Truncated GLB JSON chunk');
  const document = JSON.parse(new TextDecoder().decode(original.subarray(20, originalJsonEnd)));
  function stripTextureReferences(value) {
    if (!value || typeof value !== 'object') return;
    for (const [key, nested] of Object.entries(value)) {
      if (key.endsWith('Texture') && nested && typeof nested === 'object' && Number.isInteger(nested.index)) {
        delete value[key];
      } else stripTextureReferences(nested);
    }
  }
  for (const material of document.materials ?? []) stripTextureReferences(material);
  const json = new TextEncoder().encode(JSON.stringify(document));
  const paddedLength = Math.ceil(json.byteLength / 4) * 4;
  const result = new Uint8Array(20 + paddedLength + original.byteLength - originalJsonEnd);
  const resultView = new DataView(result.buffer);
  result.set(original.subarray(0, 12));
  resultView.setUint32(8, result.byteLength, true);
  resultView.setUint32(12, paddedLength, true);
  resultView.setUint32(16, JSON_CHUNK, true);
  result.fill(0x20, 20, 20 + paddedLength);
  result.set(json, 20);
  result.set(original.subarray(originalJsonEnd), 20 + paddedLength);
  return result.buffer;
}

export async function loadGlbGeometry(url) {
  const bytes = await readFile(url);
  return new GLTFLoader().parseAsync(withoutMaterialTexturesForGeometry(bytes), '');
}
