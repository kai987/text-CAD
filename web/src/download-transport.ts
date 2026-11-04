export interface ArtifactPart { path: string; bytes: number; sha256: string }
export interface ArtifactMetadata {
  bytes: number;
  sha256: string;
  transport?: 'gzip' | 'chunks';
  parts?: ArtifactPart[];
  decodedBytes?: number;
  decodedSha256?: string;
}
export type ArtifactManifest = Record<string, ArtifactMetadata>;
const hash = (value: unknown): value is string => typeof value === 'string' && /^[0-9a-f]{64}$/.test(value);
export function hasDecodedIntegrity(entry?: ArtifactMetadata): entry is ArtifactMetadata & { decodedBytes: number; decodedSha256: string } {
  return Boolean(entry && Number.isSafeInteger(entry.decodedBytes) && entry.decodedBytes! > 0 && hash(entry.decodedSha256));
}
export function isArtifactMetadata(value: unknown): value is ArtifactMetadata {
  if (!value || typeof value !== 'object') return false;
  const entry = value as ArtifactMetadata;
  return Number.isSafeInteger(entry.bytes) && entry.bytes > 0 && hash(entry.sha256)
    && (entry.transport === undefined || entry.transport === 'gzip' || entry.transport === 'chunks')
    && ((entry.decodedBytes === undefined && entry.decodedSha256 === undefined) || hasDecodedIntegrity(entry))
    && (entry.transport === 'chunks'
      ? hasDecodedIntegrity(entry) && Array.isArray(entry.parts) && entry.parts.length >= 2 && entry.parts.length <= 32
        && entry.parts.every((part, index) => part && typeof part.path === 'string'
          && part.path.endsWith(`.gz.part-${String(index + 1).padStart(3, '0')}`)
          && Number.isSafeInteger(part.bytes) && part.bytes > 0 && hash(part.sha256))
        && entry.parts.every(part => part.path.slice(0, -3) === entry.parts![0].path.slice(0, -3))
        && entry.parts.reduce((total, part) => total + part.bytes, 0) === entry.bytes
      : entry.parts === undefined);
}
export interface DownloadTransport {
  path: string;
  metadata: ArtifactMetadata;
  compression?: 'gzip';
}
/** Select encoded URLs using the encoded entry's own release hash. */
export function selectDownloadTransport(path: string, manifest: ArtifactManifest, compressedStep = false): DownloadTransport | null {
  const original = manifest[path], encoded = manifest[`${path}.gz`];
  if (isArtifactMetadata(encoded) && encoded.transport !== 'gzip' && hasDecodedIntegrity(encoded)) {
    if (original && (!isArtifactMetadata(original) || original.bytes !== encoded.decodedBytes
      || original.sha256 !== encoded.decodedSha256)) return null;
    if (encoded.transport === 'chunks' && !encoded.parts!.every((part, index) => {
      const target = manifest[part.path];
      return part.path === `${path}.gz.part-${String(index + 1).padStart(3, '0')}` && isArtifactMetadata(target)
        && target.transport === undefined && target.decodedBytes === undefined
        && target.bytes === part.bytes && target.sha256 === part.sha256;
    })) return null;
    return { path: `${path}.gz`, metadata: encoded, compression: 'gzip' };
  }
  if (compressedStep || original?.transport === 'gzip') return null;
  return isArtifactMetadata(original) ? { path, metadata: original } : null;
}

/** Fetch can already have decoded a Content-Encoding:gzip response. */
export async function decodeGzipBlob(input: Blob): Promise<Blob> {
  const prefix = new Uint8Array(await input.slice(0, 2).arrayBuffer());
  if (prefix[0] !== 0x1f || prefix[1] !== 0x8b) return input;
  return new Response(input.stream().pipeThrough(new DecompressionStream('gzip'))).blob();
}
