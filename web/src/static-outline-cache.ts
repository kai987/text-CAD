import { REVISION } from 'three';

export type CachedOutlineKind = 'edges' | 'cad';
export interface StaticOutlineEntry { node: number; kind: CachedOutlineKind; positions: Float32Array }
interface CacheMetadata {
  sourceSha256: string;
  thresholdAngle: number;
  threeRevision: string;
  cadAlgorithm: number;
  entries: { node: number; kind: CachedOutlineKind; offset: number; count: number }[];
}
const MAGIC = 0x31434445; // EDC1, JSON metadata followed by aligned float32 endpoints.
const VERSION = 1;
const CAD_ALGORITHM = 1;
export const STATIC_OUTLINE_ANGLE = 28;

/** Build-time output is keyed by exact GLB bytes and the two outline algorithms. */
export function encodeStaticOutlineCache(sourceSha256: string, entries: readonly StaticOutlineEntry[]): ArrayBuffer {
  let count = 0;
  const metadata: CacheMetadata = {
    sourceSha256, thresholdAngle: STATIC_OUTLINE_ANGLE, threeRevision: REVISION, cadAlgorithm: CAD_ALGORITHM,
    entries: entries.map(entry => {
      const record = { node: entry.node, kind: entry.kind, offset: count, count: entry.positions.length };
      count += entry.positions.length;
      return record;
    }),
  };
  const json = new TextEncoder().encode(JSON.stringify(metadata));
  const aligned = Math.ceil(json.length / 4) * 4;
  const buffer = new ArrayBuffer(16 + aligned + count * 4);
  const header = new DataView(buffer);
  header.setUint32(0, MAGIC, true); header.setUint32(4, VERSION, true);
  header.setUint32(8, aligned, true); header.setUint32(12, count, true);
  const bytes = new Uint8Array(buffer);
  bytes.fill(0x20, 16, 16 + aligned); bytes.set(json, 16);
  const values = new Float32Array(buffer, 16 + aligned, count);
  for (const [index, entry] of entries.entries()) values.set(entry.positions, metadata.entries[index].offset);
  // Also run the runtime validation so a malformed build cannot be published.
  decodeStaticOutlineCache(buffer, sourceSha256);
  return buffer;
}

export function decodeStaticOutlineCache(bytes: ArrayBuffer, sourceSha256: string): ReadonlyMap<number, StaticOutlineEntry> {
  if (bytes.byteLength < 16 || bytes.byteLength > 64 * 1024 * 1024 || !/^[a-f0-9]{64}$/.test(sourceSha256)) {
    throw new Error('Invalid static outline cache.');
  }
  const header = new DataView(bytes);
  const jsonLength = header.getUint32(8, true), count = header.getUint32(12, true);
  if (header.getUint32(0, true) !== MAGIC || header.getUint32(4, true) !== VERSION ||
    jsonLength % 4 !== 0 || 16 + jsonLength + count * 4 !== bytes.byteLength) {
    throw new Error('Invalid static outline cache layout.');
  }
  const metadata = JSON.parse(new TextDecoder().decode(new Uint8Array(bytes, 16, jsonLength))) as CacheMetadata;
  if (metadata.sourceSha256 !== sourceSha256 || metadata.thresholdAngle !== STATIC_OUTLINE_ANGLE ||
    metadata.threeRevision !== REVISION || metadata.cadAlgorithm !== CAD_ALGORITHM || !Array.isArray(metadata.entries)) {
    throw new Error('Static outlines belong to a different model or algorithm.');
  }
  const positions = new Float32Array(bytes, 16 + jsonLength, count);
  if (!positions.every(Number.isFinite)) throw new Error('Static outlines contain invalid coordinates.');
  const entries = new Map<number, StaticOutlineEntry>();
  let end = 0;
  for (const entry of metadata.entries) {
    if (!Number.isSafeInteger(entry.node) || entry.node < 0 || entries.has(entry.node) ||
      (entry.kind !== 'edges' && entry.kind !== 'cad') || entry.offset !== end ||
      !Number.isSafeInteger(entry.count) || entry.count < 0 || entry.count % 6 !== 0 || end + entry.count > count) {
      throw new Error('Invalid static outline entry.');
    }
    entries.set(entry.node, { node: entry.node, kind: entry.kind, positions: positions.subarray(end, end + entry.count) });
    end += entry.count;
  }
  if (end !== count) throw new Error('Unreferenced static outline coordinates.');
  return entries;
}

export function outlineKindForCadName(name: string): CachedOutlineKind {
  return /:wall_(?:external|partition)_|^roof:.*gable_wall$|:cladding:/.test(name) ? 'cad' : 'edges';
}
