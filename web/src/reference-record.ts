import { referenceLimits, validReferenceDimensions } from './reference-review.ts';
import type { ReferenceAlignment } from './reference-review.ts';

export const comparisonRecordLimit = 128 * 1024;
export interface ReferencePoint { x: number; y: number }
export interface ReferenceAnchor { reference: ReferencePoint; model: ReferencePoint }
export interface ReferenceCameraPose {
  position: [number, number, number];
  target: [number, number, number];
  zoom: number;
  verticalSpan?: number;
}
export interface ReferenceViewport { width: number; height: number }
export interface ComparisonOrigin { revision: string; model_sha256: string }
export interface ComparisonRecord {
  schema_version: 1 | 2;
  revision: string;
  model_sha256: string;
  reference: { sha256: string; width: number; height: number };
  comparison_origin?: ComparisonOrigin;
  alignment: ReferenceAlignment;
  overlay_visible: boolean;
  source: string;
  camera: { preset: string; pose: ReferenceCameraPose };
  viewport: ReferenceViewport;
  anchor_points: ReferenceAnchor[];
}
export interface ComparisonIdentity {
  model: string;
  revision: string;
  modelSha256: string;
  photoSha256: string;
  width: number;
  height: number;
  cameras: readonly string[];
}
export class ComparisonRecordError extends Error {
  readonly reason: 'record' | 'model' | 'photo' | 'revision';
  constructor(reason: 'record' | 'model' | 'photo' | 'revision') {
    super(`Invalid comparison ${reason}.`);
    this.reason = reason;
  }
}
const object = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null && !Array.isArray(value);
const finite = (value: unknown, min: number, max: number): value is number => typeof value === 'number' && Number.isFinite(value) && value >= min && value <= max;
const vector = (value: unknown): value is [number, number, number] => Array.isArray(value) && value.length === 3 && value.every(n => finite(n, -1_000_000, 1_000_000));
export function validReferencePoint(value: unknown): value is ReferencePoint {
  return object(value) && finite(value.x, 0, 1) && finite(value.y, 0, 1);
}
export function validReferencePose(value: unknown): value is ReferenceCameraPose {
  return object(value) && vector(value.position) && vector(value.target)
    && value.position.some((n, i) => n !== (value.target as number[])[i])
    && finite(value.zoom, .3, 32)
    && (value.verticalSpan === undefined || finite(value.verticalSpan, .001, 100_000));
}
export function parseComparisonRecord(text: string, identity: ComparisonIdentity, options: { allowRevisionChange?: boolean } = {}): ComparisonRecord {
  if (new TextEncoder().encode(text).length > comparisonRecordLimit) throw new ComparisonRecordError('record');
  let value: unknown;
  try { value = JSON.parse(text); } catch { throw new ComparisonRecordError('record'); }
  if (!object(value) || ![1, 2].includes(value.schema_version as number)
    || !/^[0-9a-f]{64}$/.test(identity.modelSha256) || !/^[0-9a-f]{64}$/.test(identity.photoSha256)) throw new ComparisonRecordError('record');
  if (value.model !== identity.model) throw new ComparisonRecordError('model');
  if (typeof value.revision !== 'string' || !value.revision.length || value.revision.length > 80
    || typeof value.model_sha256 !== 'string' || !/^[0-9a-f]{64}$/.test(value.model_sha256)) throw new ComparisonRecordError('record');
  const reference = value.reference;
  if (!object(reference) || reference.sha256 !== identity.photoSha256 || reference.width !== identity.width || reference.height !== identity.height) {
    throw new ComparisonRecordError('photo');
  }
  if (!validReferenceDimensions(identity.width, identity.height) || typeof reference.source !== 'string' || reference.source.length > 1000
    || !object(value.alignment) || !Object.entries(referenceLimits).every(([key, [min, max]]) => finite((value.alignment as Record<string, unknown>)[key], min, max))
    || typeof value.overlay_visible !== 'boolean' || !object(value.camera) || !identity.cameras.includes(value.camera.preset as string)
    || !validReferencePose(value.camera.pose) || (value.schema_version === 2 && value.camera.pose.verticalSpan === undefined) || !object(value.viewport)
    || !finite(value.viewport.width, 1, 16384) || !finite(value.viewport.height, 1, 16384)) {
    throw new ComparisonRecordError('record');
  }
  const anchors = value.anchor_points ?? [];
  if (!Array.isArray(anchors) || anchors.length > 16 || !anchors.every(a => object(a) && validReferencePoint(a.reference) && validReferencePoint(a.model))) {
    throw new ComparisonRecordError('record');
  }
  const origin = value.comparison_origin;
  if (origin !== undefined && (!object(origin) || typeof origin.revision !== 'string' || !origin.revision.length || origin.revision.length > 80
    || typeof origin.model_sha256 !== 'string' || !/^[0-9a-f]{64}$/.test(origin.model_sha256))) throw new ComparisonRecordError('record');
  if (!options.allowRevisionChange && (value.revision !== identity.revision || value.model_sha256 !== identity.modelSha256)) {
    throw new ComparisonRecordError('revision');
  }
  return {
    schema_version: value.schema_version as 1 | 2,
    revision: value.revision,
    model_sha256: value.model_sha256,
    reference: { sha256: reference.sha256 as string, width: identity.width, height: identity.height },
    ...(object(origin) ? { comparison_origin: { revision: origin.revision as string, model_sha256: origin.model_sha256 as string } } : {}),
    alignment: Object.fromEntries(Object.keys(referenceLimits).map(key => [key, (value.alignment as Record<string, unknown>)[key]])) as unknown as ReferenceAlignment,
    overlay_visible: value.overlay_visible,
    source: reference.source,
    camera: {
      preset: value.camera.preset as string,
      pose: { position: [...value.camera.pose.position], target: [...value.camera.pose.target], zoom: value.camera.pose.zoom,
        ...(value.camera.pose.verticalSpan === undefined ? {} : { verticalSpan: value.camera.pose.verticalSpan }) },
    },
    viewport: { width: value.viewport.width, height: value.viewport.height },
    anchor_points: anchors.map(a => ({ reference: { x: a.reference.x, y: a.reference.y }, model: { x: a.model.x, y: a.model.y } })),
  };
}

// Restored orthographic cameras keep their vertical span and adapt the width.
export function restoreReferenceAnchors(anchors: readonly ReferenceAnchor[], saved: ReferenceViewport, current: ReferenceViewport): ReferenceAnchor[] {
  const factor = saved.width / saved.height / (current.width / current.height);
  return anchors.map(anchor => ({ reference: { ...anchor.reference }, model: { x: .5 + (anchor.model.x - .5) * factor, y: anchor.model.y } }))
    .filter(anchor => validReferencePoint(anchor.model));
}
