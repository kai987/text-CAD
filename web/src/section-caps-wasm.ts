import { BufferAttribute, BufferGeometry, InterleavedBufferAttribute } from 'three';
import type { Mesh } from 'three';
import init, { section_cap } from './wasm/section_caps.js';

let initialization: Promise<void> | undefined;

/** Byte input also allows the exact browser binary to be tested in Node. */
export function initializeSectionCapsWasm(bytes?: Uint8Array): Promise<void> {
  initialization ??= (async () => {
    let input: ArrayBuffer;
    if (bytes) input = new Uint8Array(bytes).buffer;
    else {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 10_000);
      try {
        const response = await fetch(new URL('./wasm/section_caps_bg.wasm', import.meta.url), { signal: controller.signal });
        if (!response.ok) throw new Error(`Section WASM download failed (${response.status}).`);
        input = await response.arrayBuffer();
      } finally { clearTimeout(timeout); }
    }
    await init({ module_or_path: input });
  })();
  return initialization;
}

interface MeshInput {
  position: BufferAttribute | InterleavedBufferAttribute;
  positionVersion: number;
  index: BufferAttribute | null;
  indexVersion: number;
  positions: Float64Array;
  indices: Uint32Array;
}
const inputs = new WeakMap<BufferGeometry, MeshInput>();

function inputFor(geometry: BufferGeometry): MeshInput | null {
  const position = geometry.getAttribute('position');
  if (!position || position.itemSize < 3 || !Number.isInteger(position.count)) return null;
  const index = geometry.getIndex();
  const positionVersion = position instanceof InterleavedBufferAttribute ? position.data.version : position.version;
  const indexVersion = index?.version ?? 0;
  const previous = inputs.get(geometry);
  if (previous?.position === position && previous.positionVersion === positionVersion &&
      previous.index === index && previous.indexVersion === indexVersion) return previous;
  // Copy, rather than transfer or detach the arrays Three.js is still rendering.
  const positions = new Float64Array(position.count * 3);
  for (let i = 0; i < position.count; i++) {
    positions.set([position.getX(i), position.getY(i), position.getZ(i)], i * 3);
  }
  if (index && !Number.isInteger(index.count)) return null;
  const indices = new Uint32Array(index?.count ?? 0);
  for (let i = 0; i < indices.length; i++) {
    const value = index!.getX(i);
    if (!Number.isInteger(value) || value < 0 || value > 0xffffffff || value >= position.count) return null;
    indices[i] = value;
  }
  const input = { position, positionVersion, index, indexVersion, positions, indices };
  inputs.set(geometry, input);
  return input;
}

/** Same synchronous contract as the TypeScript implementation, after initialization. */
export function createWasmHorizontalCap(mesh: Mesh, worldHeight: number): BufferGeometry | null {
  if (!Number.isFinite(worldHeight)) return null;
  mesh.updateWorldMatrix(true, false);
  if (mesh.matrixWorld.determinant() === 0) return null;
  const input = inputFor(mesh.geometry);
  if (!input) return null;
  const output = section_cap(input.positions, input.indices, new Float64Array(mesh.matrixWorld.elements), worldHeight);
  if (!output.length) return null;
  const half = output.length / 2;
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new BufferAttribute(output.subarray(0, half), 3));
  geometry.setAttribute('normal', new BufferAttribute(output.subarray(half), 3));
  geometry.computeBoundingBox(); geometry.computeBoundingSphere();
  return geometry;
}
