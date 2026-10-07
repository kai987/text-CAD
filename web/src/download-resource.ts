import { decodeStepBlob } from './step-download.ts';

export interface ArtifactMetadata {
  bytes: number;
  sha256: string;
  decodedBytes?: number;
  decodedSha256?: string;
}
export type ArtifactManifest = Record<string, ArtifactMetadata>;
export interface DownloadProgress { loaded: number; total: number | null }
export type DownloadErrorCode = 'http' | 'network' | 'timeout' | 'integrity' | 'format' | 'manifest';
export class DownloadError extends Error {
  code: DownloadErrorCode;
  status?: number;
  constructor(code: DownloadErrorCode, status?: number) {
    super(code === 'http' ? `Download failed (${status}).` : `Download failed: ${code}.`);
    this.name = 'DownloadError';
    this.code = code; this.status = status;
  }
}

// A host can transparently decode Content-Encoding: gzip. Check the resulting
// document, not the compressed transfer hash, in that case.
export async function verifyDownload(blob: Blob, metadata?: ArtifactMetadata, decoded = false): Promise<void> {
  const bytes = decoded ? metadata?.decodedBytes : metadata?.bytes;
  const hash = decoded ? metadata?.decodedSha256 : metadata?.sha256;
  if (bytes !== undefined && bytes !== blob.size) throw new DownloadError('integrity');
  if (hash && globalThis.crypto?.subtle) {
    const digest = await crypto.subtle.digest('SHA-256', await blob.arrayBuffer());
    const actual = Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
    if (actual !== hash) throw new DownloadError('integrity');
  }
}

export async function downloadResource(options: {
  url: string;
  type: string;
  compressedStep?: boolean;
  metadata?: ArtifactMetadata;
  signal?: AbortSignal;
  timeoutMs?: number;
  onProgress?: (progress: DownloadProgress) => void;
  onProcessing?: () => void;
  fetcher?: typeof fetch;
}): Promise<Blob> {
  const controller = new AbortController();
  let timedOut = false;
  const cancel = () => controller.abort(options.signal?.reason);
  if (options.signal?.aborted) cancel();
  else options.signal?.addEventListener('abort', cancel, { once: true });
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, options.timeoutMs ?? 120_000);
  const throwIfCancelled = () => {
    if (controller.signal.aborted) throw controller.signal.reason ?? new DOMException('Aborted', 'AbortError');
  };
  try {
    throwIfCancelled();
    const response = await (options.fetcher ?? fetch)(options.url, { signal: controller.signal });
    throwIfCancelled();
    if (!response.ok) throw new DownloadError('http', response.status);
    const encoded = /\bgzip\b/i.test(response.headers.get('content-encoding') ?? '');
    const expected = encoded && options.compressedStep ? options.metadata?.decodedBytes : options.metadata?.bytes;
    const header = Number(response.headers.get('content-length'));
    const total = expected ?? (header > 0 ? header : null);
    let blob: Blob;
    if (response.body) {
      const reader = response.body.getReader();
      const cancelReader = () => { void reader.cancel().catch(() => {}); };
      controller.signal.addEventListener('abort', cancelReader, { once: true });
      const chunks: Uint8Array<ArrayBuffer>[] = [];
      let loaded = 0;
      try {
        while (true) {
          throwIfCancelled();
          const { value, done } = await reader.read();
          throwIfCancelled();
          if (done) break;
          // Own the buffer; some stream implementations reuse their read buffer.
          chunks.push(new Uint8Array(value));
          loaded += value.byteLength;
          options.onProgress?.({ loaded, total });
        }
      } catch (error) {
        await reader.cancel().catch(() => {});
        throw error;
      } finally {
        controller.signal.removeEventListener('abort', cancelReader);
        reader.releaseLock();
      }
      blob = new Blob(chunks, { type: response.headers.get('content-type') ?? 'application/octet-stream' });
      options.onProgress?.({ loaded, total: total ?? loaded });
    } else {
      blob = await response.blob();
      options.onProgress?.({ loaded: blob.size, total: total ?? blob.size });
    }
    throwIfCancelled();
    options.onProcessing?.();
    if (options.compressedStep) {
      const prefix = new Uint8Array(await blob.slice(0, 2).arrayBuffer());
      const compressed = prefix[0] === 0x1f && prefix[1] === 0x8b;
      // Only the raw gzip payload can be compared with its transfer hash.
      if (compressed) await verifyDownload(blob, options.metadata);
      try { blob = await decodeStepBlob(blob); }
      catch { throw new DownloadError('format'); }
      await verifyDownload(blob, options.metadata, true);
    } else {
      await verifyDownload(blob, options.metadata);
      const prefix = await blob.slice(0, 256).text();
      const valid = options.type === 'STEP' ? prefix.startsWith('ISO-10303-21;')
        : options.type === 'GLB' ? prefix.startsWith('glTF')
        : options.type === 'PDF' ? prefix.startsWith('%PDF-')
        : !/^\s*(?:<!doctype\s+html|<html\b)/i.test(prefix);
      if (!valid) throw new DownloadError('format');
      if (options.type === 'JSON') {
        try { JSON.parse(await blob.text()); } catch { throw new DownloadError('format'); }
      }
    }
    throwIfCancelled();
    return blob;
  } catch (error) {
    if (options.signal?.aborted) throw options.signal.reason ?? new DOMException('Aborted', 'AbortError');
    if (timedOut) throw new DownloadError('timeout');
    if (error instanceof DownloadError) throw error;
    throw new DownloadError('network');
  } finally {
    clearTimeout(timer);
    options.signal?.removeEventListener('abort', cancel);
  }
}

const manifests = new Map<string, Promise<ArtifactManifest | null>>();
export function loadDownloadManifest(url: string, fetcher: typeof fetch = fetch): Promise<ArtifactManifest | null> {
  const existing = manifests.get(url);
  if (existing) return existing;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15_000);
  const request = Promise.resolve().then(() => fetcher(url, { signal: controller.signal }))
    .then(async response => {
      if (!response.ok) throw new Error('Artifact manifest unavailable.');
      const manifest: unknown = await response.json();
      if (!manifest || typeof manifest !== 'object' || Array.isArray(manifest)) throw new Error('Invalid artifact manifest.');
      const result: ArtifactManifest = {};
      for (const [path, value] of Object.entries(manifest)) {
        if (!value || typeof value !== 'object') continue;
        const entry = value as Partial<ArtifactMetadata>;
        if (typeof entry.bytes === 'number' && entry.bytes > 0 && typeof entry.sha256 === 'string'
          && /^[0-9a-f]{64}$/.test(entry.sha256)) result[path] = entry as ArtifactMetadata;
      }
      return result;
    }).catch(() => { manifests.delete(url); return null; })
    .finally(() => clearTimeout(timer));
  manifests.set(url, request);
  return request;
}

export async function requireDownloadMetadata(url: string, path: string, known?: ArtifactMetadata,
  fetcher: typeof fetch = fetch): Promise<ArtifactMetadata> {
  const entry = known ?? (await loadDownloadManifest(url, fetcher))?.[path];
  if (!entry) throw new DownloadError('manifest');
  return entry;
}
