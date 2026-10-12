import init, { cad_outline, section_cap } from './wasm/section_caps.js';
import { createMeshEdgePositions } from './mesh-edges.ts';
import type {
  GeometryWorkerRequest, GeometryWorkerResponse, OutlineResult, SectionCapResult, WorkerGeometry,
} from './geometry-worker-protocol.ts';

// DOM and Worker libraries overlap, so keep this small worker-only scope typed
// without adding WebWorker globals to the application's DOM compiler context.
interface GeometryWorkerScope {
  postMessage(message: GeometryWorkerResponse, transfer?: Transferable[]): void;
  addEventListener(type: 'message', listener: (event: MessageEvent<GeometryWorkerRequest>) => void): void;
}
const scope = globalThis as unknown as GeometryWorkerScope;
const geometries = new Map<string, WorkerGeometry>();
const rustPositions = new Map<string, Float64Array>();
const meshEdgeCache = new Map<string, Map<number, Float32Array>>();

function geometryFor(id: string): WorkerGeometry {
  const geometry = geometries.get(id);
  if (!geometry) throw new Error(`Geometry is not registered: ${id}`);
  return geometry;
}

function positionsForRust(geometry: WorkerGeometry): Float64Array {
  if (geometry.positions instanceof Float64Array) return geometry.positions;
  let positions = rustPositions.get(geometry.geometryId);
  if (!positions) {
    positions = new Float64Array(geometry.positions);
    rustPositions.set(geometry.geometryId, positions);
  }
  return positions;
}

function registerGeometry(geometry: WorkerGeometry) {
  if (geometries.has(geometry.geometryId)) throw new Error(`Geometry ID was registered twice: ${geometry.geometryId}`);
  geometries.set(geometry.geometryId, geometry);
}

function transferredBuffers(arrays: Float32Array[]): Transferable[] {
  // A cap's position and normal views share one allocation.
  return [...new Set(arrays.map(array => array.buffer as ArrayBuffer))];
}

const initialization = (async () => {
  const response = await fetch(new URL('./wasm/section_caps_bg.wasm', import.meta.url));
  if (!response.ok) throw new Error(`Geometry WASM download failed (${response.status}).`);
  await init({ module_or_path: await response.arrayBuffer() });
  scope.postMessage({ type: 'ready' });
})();
void initialization.catch(error => {
  scope.postMessage({ type: 'error', message: error instanceof Error ? error.message : String(error) });
});

scope.addEventListener('message', event => {
  void initialization.then(() => {
    const message = event.data;
    if (message.type === 'register') {
      registerGeometry(message);
      return;
    }
    if (message.type === 'register-batch') {
      message.geometries.forEach(registerGeometry);
      return;
    }
    if (message.type === 'sections') {
      const results: SectionCapResult[] = message.jobs.map(job => {
        const geometry = geometryFor(job.geometryId);
        const output = geometry.indexed && geometry.indices.length === 0
          ? new Float32Array()
          : section_cap(positionsForRust(geometry), geometry.indices, job.matrix, job.height);
        const half = output.length / 2;
        return { id: job.id, positions: output.subarray(0, half), normals: output.subarray(half) };
      });
      scope.postMessage({ type: 'sections', requestId: message.requestId, results },
        transferredBuffers(results.flatMap(result => [result.positions, result.normals])));
      return;
    }
    if (message.type === 'mesh-edges') {
      // One transferable copy per geometry/angle in this batch. The retained
      // cache is never detached, so repeated meshes and future requests reuse it.
      const copies = new Map<string, Map<number, Float32Array>>();
      const results: OutlineResult[] = message.jobs.map(job => {
        const geometry = geometryFor(job.geometryId);
        let cache = meshEdgeCache.get(job.geometryId);
        if (!cache) { cache = new Map(); meshEdgeCache.set(job.geometryId, cache); }
        let cached = cache.get(job.thresholdAngle);
        if (!cached) { cached = createMeshEdgePositions(geometry, job.thresholdAngle); cache.set(job.thresholdAngle, cached); }
        let batch = copies.get(job.geometryId);
        if (!batch) { batch = new Map(); copies.set(job.geometryId, batch); }
        let positions = batch.get(job.thresholdAngle);
        if (!positions) { positions = cached.slice(); batch.set(job.thresholdAngle, positions); }
        return { id: job.id, positions };
      });
      scope.postMessage({ type: 'mesh-edges', requestId: message.requestId, results },
        transferredBuffers(results.map(result => result.positions)));
      return;
    }
    if (message.type !== 'outlines') throw new Error('Unknown geometry worker request.');
    const results: OutlineResult[] = message.jobs.map(job => {
      const geometry = geometryFor(job.geometryId);
      const positions = geometry.indexed && geometry.indices.length === 0
        ? new Float32Array()
        : cad_outline(positionsForRust(geometry), geometry.indices, job.thresholdAngle);
      return { id: job.id, positions };
    });
    scope.postMessage({ type: 'outlines', requestId: message.requestId, results },
      transferredBuffers(results.map(result => result.positions)));
  }).catch(error => {
    scope.postMessage({ type: 'error', message: error instanceof Error ? error.message : String(error) });
  });
});
