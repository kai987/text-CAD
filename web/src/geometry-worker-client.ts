import { InterleavedBufferAttribute } from 'three';
import type { BufferAttribute, BufferGeometry } from 'three';
import type {
  GeometryWorkerRequest, GeometryWorkerResponse, OutlineJob, OutlineResult,
  SectionCapJob, SectionCapResult, WorkerGeometry, WorkerSectionCapJob,
} from './geometry-worker-protocol.ts';

export type GeometryWorkerTransport = Pick<Worker, 'postMessage' | 'addEventListener' | 'removeEventListener' | 'terminate'>;

export interface GeometryWorkerOptions {
  onFailure?: (error: Error) => void;
  initializeTimeoutMs?: number;
  requestTimeoutMs?: number;
  /** Test injection also makes unsupported Worker environments easy to verify. */
  workerFactory?: () => GeometryWorkerTransport;
}

interface RegisteredInput {
  id: string;
  position: BufferAttribute | InterleavedBufferAttribute;
  positionVersion: number;
  index: BufferAttribute | null;
  indexVersion: number;
}

interface PendingSection {
  requestId: number;
  jobs: WorkerSectionCapJob[];
  resolve: (result: SectionCapResult[] | null) => void;
  superseded: boolean;
  timer?: ReturnType<typeof setTimeout>;
}

interface PendingOutline {
  requestId: number;
  jobs: OutlineJob[];
  resolve: (result: OutlineResult[] | null) => void;
  timer?: ReturnType<typeof setTimeout>;
}

/**
 * WASM loads and computes in a dedicated worker. Only geometry snapshots are
 * transferred. Sections have one in-flight batch and one latest pending batch;
 * superseded results can never be applied to a newer slider position or scene.
 */
export function createGeometryWorkerClient(options: GeometryWorkerOptions = {}) {
  let worker: GeometryWorkerTransport | undefined;
  let initialized = false;
  let failed = false;
  let disposed = false;
  let nextGeometryId = 0;
  let nextRequestId = 0;
  const inputs = new WeakMap<BufferGeometry, RegisteredInput>();
  const uploads = new Map<string, WorkerGeometry>();
  const outlineRequests = new Map<number, PendingOutline>();
  let activeSection: PendingSection | undefined;
  let pendingSection: PendingSection | undefined;
  let initializeTimer: ReturnType<typeof setTimeout> | undefined;
  let resolveReady!: () => void;
  let rejectReady!: (error: Error) => void;
  const ready = new Promise<void>((resolve, reject) => { resolveReady = resolve; rejectReady = reject; });
  // Callers may use only the failure callback; do not emit an unhandled rejection.
  void ready.catch(() => {});

  function detachWorker() {
    if (!worker) return;
    worker.removeEventListener('message', onMessage);
    worker.removeEventListener('error', onError);
    worker.removeEventListener('messageerror', onMessageError);
    worker.terminate();
    worker = undefined;
  }

  function settlePending() {
    clearTimeout(initializeTimer);
    if (activeSection) {
      clearTimeout(activeSection.timer);
      activeSection.resolve(null);
      activeSection = undefined;
    }
    if (pendingSection) { pendingSection.resolve(null); pendingSection = undefined; }
    for (const request of outlineRequests.values()) {
      clearTimeout(request.timer);
      request.resolve(null);
    }
    outlineRequests.clear();
    uploads.clear();
  }

  function fail(reason: unknown) {
    if (failed || disposed) return;
    failed = true;
    const error = reason instanceof Error ? reason : new Error(String(reason));
    rejectReady(error);
    settlePending();
    detachWorker();
    options.onFailure?.(error);
  }

  function post(message: GeometryWorkerRequest, transfer: Transferable[] = []) {
    if (!worker || failed || disposed) return false;
    try { worker.postMessage(message, transfer); return true; }
    catch (error) { fail(error); return false; }
  }

  function startSection() {
    if (!initialized || activeSection || !pendingSection || failed || disposed) return;
    activeSection = pendingSection;
    pendingSection = undefined;
    const request = activeSection;
    request.timer = setTimeout(() => fail(new Error('Geometry section request timed out.')),
      options.requestTimeoutMs ?? 15_000);
    post({ type: 'sections', requestId: request.requestId, jobs: request.jobs },
      request.jobs.map(job => job.matrix.buffer as ArrayBuffer));
  }

  function startOutline(request: PendingOutline) {
    request.timer = setTimeout(() => fail(new Error('Geometry outline request timed out.')),
      options.requestTimeoutMs ?? 15_000);
    post({ type: 'outlines', requestId: request.requestId, jobs: request.jobs });
  }

  function onMessage(event: MessageEvent<GeometryWorkerResponse>) {
    if (failed || disposed) return;
    const message = event.data;
    if (!message || typeof message !== 'object') { fail(new Error('Invalid geometry worker response.')); return; }
    if (message.type === 'error') { fail(new Error(message.message)); return; }
    if (message.type === 'ready') {
      if (initialized) return;
      initialized = true;
      clearTimeout(initializeTimer);
      for (const geometry of uploads.values()) {
        if (!post({ type: 'register', ...geometry }, [geometry.positions.buffer as ArrayBuffer, geometry.indices.buffer as ArrayBuffer])) return;
      }
      uploads.clear();
      resolveReady();
      for (const request of outlineRequests.values()) startOutline(request);
      startSection();
      return;
    }
    if (message.type === 'sections') {
      const request = activeSection;
      if (!request || request.requestId !== message.requestId) return;
      clearTimeout(request.timer);
      activeSection = undefined;
      if (!validSectionResults(message.results, request.jobs)) {
        request.resolve(null);
        fail(new Error('Invalid geometry section result.'));
        return;
      }
      request.resolve(request.superseded ? null : message.results);
      startSection();
      return;
    }
    if (message.type === 'outlines') {
      const request = outlineRequests.get(message.requestId);
      if (!request) return;
      clearTimeout(request.timer);
      outlineRequests.delete(message.requestId);
      if (!validOutlineResults(message.results, request.jobs)) {
        request.resolve(null);
        fail(new Error('Invalid geometry outline result.'));
        return;
      }
      request.resolve(message.results);
      return;
    }
    fail(new Error('Unknown geometry worker response.'));
  }

  function onError(event: ErrorEvent) { fail(event.error ?? new Error(event.message || 'Geometry worker failed.')); }
  function onMessageError() { fail(new Error('Geometry worker response could not be decoded.')); }

  function registerGeometry(geometry: BufferGeometry): string | null {
    if (failed || disposed) return null;
    const position = geometry.getAttribute('position');
    if (!position || position.itemSize < 3 || !Number.isInteger(position.count)) return null;
    const index = geometry.getIndex();
    const positionVersion = position instanceof InterleavedBufferAttribute ? position.data.version : position.version;
    const indexVersion = index?.version ?? 0;
    const previous = inputs.get(geometry);
    if (previous?.position === position && previous.positionVersion === positionVersion &&
      previous.index === index && previous.indexVersion === indexVersion) return previous.id;
    const positions = new Float64Array(position.count * 3);
    for (let i = 0; i < position.count; i++) {
      positions[i * 3] = position.getX(i);
      positions[i * 3 + 1] = position.getY(i);
      positions[i * 3 + 2] = position.getZ(i);
    }
    if (index && !Number.isInteger(index.count)) return null;
    const indices = new Uint32Array(index?.count ?? 0);
    for (let i = 0; i < indices.length; i++) {
      const value = index!.getX(i);
      if (!Number.isInteger(value) || value < 0 || value > 0xffffffff || value >= position.count) return null;
      indices[i] = value;
    }
    const id = `geometry-${++nextGeometryId}`;
    const upload: WorkerGeometry = { geometryId: id, positions, indices, indexed: index !== null };
    inputs.set(geometry, { id, position, positionVersion, index, indexVersion });
    if (initialized) {
      if (!post({ type: 'register', ...upload }, [positions.buffer, indices.buffer])) return null;
    } else uploads.set(id, upload);
    return id;
  }

  function sectionCaps(jobs: SectionCapJob[]): Promise<SectionCapResult[] | null> {
    if (failed || disposed) return Promise.resolve(null);
    if (pendingSection) { pendingSection.resolve(null); pendingSection = undefined; }
    if (activeSection) { activeSection.superseded = true; activeSection.resolve(null); }
    if (!jobs.length) return Promise.resolve([]);
    // Capture transforms now; Three updates matrixWorld while a batch is queued.
    const captured = jobs.map(job => ({ ...job, matrix: new Float64Array(job.matrix) }));
    return new Promise(resolve => {
      pendingSection = { requestId: ++nextRequestId, jobs: captured, resolve, superseded: false };
      startSection();
    });
  }

  function outlines(jobs: OutlineJob[]): Promise<OutlineResult[] | null> {
    if (failed || disposed) return Promise.resolve(null);
    if (!jobs.length) return Promise.resolve([]);
    return new Promise(resolve => {
      const request: PendingOutline = { requestId: ++nextRequestId, jobs: jobs.map(job => ({ ...job })), resolve };
      outlineRequests.set(request.requestId, request);
      if (initialized) startOutline(request);
    });
  }

  function cancelSections() {
    if (pendingSection) { pendingSection.resolve(null); pendingSection = undefined; }
    if (activeSection) { activeSection.superseded = true; activeSection.resolve(null); }
  }

  function dispose() {
    if (disposed) return;
    disposed = true;
    rejectReady(new Error('Geometry worker disposed.'));
    settlePending();
    detachWorker();
  }

  try {
    worker = options.workerFactory?.() ?? new Worker(new URL('./geometry-worker.ts', import.meta.url), { type: 'module' });
    worker.addEventListener('message', onMessage);
    worker.addEventListener('error', onError);
    worker.addEventListener('messageerror', onMessageError);
    initializeTimer = setTimeout(() => fail(new Error('Geometry worker initialization timed out.')),
      options.initializeTimeoutMs ?? 10_000);
  } catch (error) {
    // Let callers receive the client before the fallback callback is delivered.
    queueMicrotask(() => fail(error));
  }

  return { ready, registerGeometry, sectionCaps, outlines, cancelSections, dispose,
    get failed() { return failed; } };
}

function sameResultIds(results: { id: string }[], jobs: { id: string }[]): boolean {
  if (results.length !== jobs.length) return false;
  const ids = new Set(jobs.map(job => job.id));
  return ids.size === jobs.length && results.every(result =>
    result !== null && typeof result === 'object' && typeof result.id === 'string' && ids.delete(result.id));
}

function validSectionResults(results: SectionCapResult[], jobs: WorkerSectionCapJob[]): boolean {
  return Array.isArray(results) && sameResultIds(results, jobs) && results.every(result =>
    result.positions instanceof Float32Array && result.normals instanceof Float32Array &&
    result.positions.length % 9 === 0 && result.positions.length === result.normals.length &&
    result.positions.every(Number.isFinite) && result.normals.every(Number.isFinite));
}

function validOutlineResults(results: OutlineResult[], jobs: OutlineJob[]): boolean {
  return Array.isArray(results) && sameResultIds(results, jobs) && results.every(result =>
    result.positions instanceof Float32Array && result.positions.length % 6 === 0 &&
    result.positions.every(Number.isFinite));
}
