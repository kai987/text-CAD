/** The worker owns copied geometry; rendering buffers never cross this boundary. */
export interface WorkerGeometry {
  geometryId: string;
  positions: Float64Array;
  indices: Uint32Array;
  indexed: boolean;
}

export interface SectionCapJob {
  id: string;
  geometryId: string;
  matrix: readonly number[];
  height: number;
}

export interface WorkerSectionCapJob extends Omit<SectionCapJob, 'matrix'> {
  matrix: Float64Array;
}

export interface OutlineJob {
  id: string;
  geometryId: string;
  thresholdAngle: number;
}

export interface SectionCapResult {
  id: string;
  positions: Float32Array;
  normals: Float32Array;
}

export interface OutlineResult {
  id: string;
  positions: Float32Array;
}

export type GeometryWorkerRequest =
  | ({ type: 'register' } & WorkerGeometry)
  | { type: 'sections'; requestId: number; jobs: WorkerSectionCapJob[] }
  | { type: 'outlines'; requestId: number; jobs: OutlineJob[] };

export type GeometryWorkerResponse =
  | { type: 'ready' }
  | { type: 'sections'; requestId: number; results: SectionCapResult[] }
  | { type: 'outlines'; requestId: number; results: OutlineResult[] }
  | { type: 'error'; message: string };
