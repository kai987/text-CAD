import { decodeGzipBlob, hasDecodedIntegrity, isArtifactMetadata, selectDownloadTransport } from './download-transport.ts';
import type { ArtifactMetadata, ArtifactManifest, DownloadTransport } from './download-transport.ts';
export type { ArtifactMetadata, ArtifactManifest } from './download-transport.ts';
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
  compression?: 'gzip';
  decompress?: boolean;
  parts?: { url: string; metadata: ArtifactMetadata }[];
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
    const gzip = options.compression === 'gzip' || options.compressedStep;
    if (options.compression === 'gzip' && !hasDecodedIntegrity(options.metadata)) throw new DownloadError('manifest');
    const chunked = options.metadata?.transport === 'chunks';
    if (chunked) {
      const descriptor = options.metadata!.parts;
      if (!isArtifactMetadata(options.metadata) || options.parts?.length !== 2 || !descriptor
        || new Set(options.parts.map(part => part.url)).size !== 2 || !options.parts.every((part, index) =>
          isArtifactMetadata(part.metadata) && part.metadata.transport === undefined
          && part.metadata.bytes === descriptor[index].bytes && part.metadata.sha256 === descriptor[index].sha256
          && new URL(part.url, 'https://artifact.local').pathname.endsWith(`/${descriptor[index].path}`))) {
        throw new DownloadError('manifest');
      }
    } else if (options.parts) throw new DownloadError('manifest');
    async function receive(url: string, metadata: ArtifactMetadata | undefined, offset = 0): Promise<Blob> {
      throwIfCancelled();
      const response = await (options.fetcher ?? fetch)(url, { signal: controller.signal });
      throwIfCancelled();
      if (!response.ok) throw new DownloadError('http', response.status);
      const encoded = /\bgzip\b/i.test(response.headers.get('content-encoding') ?? '');
      const expected = chunked ? options.metadata!.bytes : encoded && gzip ? metadata?.decodedBytes : metadata?.bytes;
      const header = Number(response.headers.get('content-length'));
      const total = expected ?? (header > 0 ? header : null);
      if (!response.body) {
        const result = await response.blob();
        options.onProgress?.({ loaded: offset + result.size, total: total ?? result.size });
        return result;
      }
      const reader = response.body.getReader();
      const cancelReader = () => { void reader.cancel().catch(() => {}); };
      controller.signal.addEventListener('abort', cancelReader, { once: true });
      const chunks: Uint8Array<ArrayBuffer>[] = []; let loaded = 0;
      try {
        while (true) {
          throwIfCancelled();
          const { value, done } = await reader.read();
          throwIfCancelled();
          if (done) break;
          chunks.push(new Uint8Array(value)); loaded += value.byteLength;
          options.onProgress?.({ loaded: offset + loaded, total });
        }
      } catch (error) { await reader.cancel().catch(() => {}); throw error; }
      finally { controller.signal.removeEventListener('abort', cancelReader); reader.releaseLock(); }
      options.onProgress?.({ loaded: offset + loaded, total: total ?? loaded });
      return new Blob(chunks, { type: response.headers.get('content-type') ?? 'application/octet-stream' });
    }
    let blob: Blob;
    if (chunked) {
      const received: Blob[] = []; let loaded = 0;
      for (const part of options.parts!) {
        const result = await receive(part.url, part.metadata, loaded);
        throwIfCancelled(); await verifyDownload(result, part.metadata); throwIfCancelled();
        received.push(result); loaded += result.size;
      }
      blob = new Blob(received);
    } else blob = await receive(options.url, options.metadata);
    throwIfCancelled();
    options.onProcessing?.();
    let retainedGzip = false;
    if (gzip) {
      const prefix = new Uint8Array(await blob.slice(0, 2).arrayBuffer());
      const compressed = prefix[0] === 0x1f && prefix[1] === 0x8b;
      // Only the raw gzip payload can be compared with its transfer hash.
      if (compressed) await verifyDownload(blob, options.metadata);
      if (compressed && options.decompress === false) retainedGzip = true;
      else {
        try { blob = await decodeGzipBlob(blob); }
        catch { throw new DownloadError('format'); }
        await verifyDownload(blob, options.metadata, true);
      }
    } else await verifyDownload(blob, options.metadata);
    const prefix = await blob.slice(0, 256).text();
    let valid = retainedGzip || (options.type === 'STEP' ? prefix.startsWith('ISO-10303-21;')
      : options.type === 'PDF' ? prefix.startsWith('%PDF-')
      : options.type === 'DXF' ? /^(?:\uFEFF)?\s*0\s*[\r\n]+\s*SECTION\s*[\r\n]+/i.test(prefix)
        || prefix.startsWith('AutoCAD Binary DXF')
      : !/^\s*(?:<!doctype\s+html|<html\b)/i.test(prefix));
    if (!retainedGzip && options.type === 'GLB') {
      const header = await blob.slice(0, 12).arrayBuffer();
      valid = header.byteLength === 12 && new DataView(header).getUint32(0, true) === 0x46546c67
        && new DataView(header).getUint32(4, true) === 2 && new DataView(header).getUint32(8, true) === blob.size;
    }
    if (!valid) throw new DownloadError('format');
    if (!retainedGzip && options.type === 'JSON') {
      try { JSON.parse(await blob.text()); } catch { throw new DownloadError('format'); }
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
        if (isArtifactMetadata(value)) result[path] = value;
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

export async function requireDownloadTransport(url: string, path: string, options: {
  manifest?: ArtifactManifest | null; known?: ArtifactMetadata; compressedStep?: boolean; fetcher?: typeof fetch;
} = {}): Promise<DownloadTransport> {
  const manifest = options.manifest ?? await loadDownloadManifest(url, options.fetcher);
  const fallback = options.known ? (hasDecodedIntegrity(options.known)
    ? { [`${path}.gz`]: options.known } : { [path]: options.known }) : {};
  const selected = selectDownloadTransport(path, manifest ?? fallback, options.compressedStep);
  if (!selected) throw new DownloadError('manifest');
  return selected;
}
