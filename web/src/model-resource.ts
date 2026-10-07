import { gzipUrl } from './asset-url.ts';

export interface ModelProgress { loaded: number; total: number | null }
export interface ModelLoadOptions<T> {
  url: string;
  parse: (bytes: ArrayBuffer) => Promise<T>;
  onLoad: (value: T) => void;
  onError: (error: unknown) => void;
  onProgress?: (progress: ModelProgress) => void;
  disposeLate: (value: T) => void;
  timeoutMs?: number;
  fetcher?: typeof fetch;
  compressed?: boolean;
  compressedUrl?: string;
  expectedSha256?: string;
}

// One deadline covers download and parsing. Cancellation also isolates late decode results.
export function startModelLoad<T>(options: ModelLoadOptions<T>) {
  const abort = new AbortController();
  let active = true;
  function finish() { active = false; clearTimeout(deadline); }
  function fail(error: unknown) {
    if (!active) return;
    finish(); abort.abort(); options.onError(error);
  }
  const deadline = setTimeout(() => fail(new Error('Model load timed out.')), options.timeoutMs ?? 60_000);
  async function download(url: string) {
    const response = await (options.fetcher ?? fetch)(url, { signal: abort.signal });
    if (!response.ok) throw new Error(`Model request failed: ${response.status}`);
    const length = Number(response.headers.get('content-length'));
    const total = !response.headers.get('content-encoding') && Number.isFinite(length) && length > 0 ? length : null;
    let bytes: ArrayBuffer;
    if (response.body) {
      const reader = response.body.getReader();
      const chunks: Uint8Array[] = [];
      let loaded = 0;
      try {
        while (active) {
          const { done, value } = await reader.read();
          if (done) break;
          chunks.push(value); loaded += value.byteLength;
          if (active) options.onProgress?.({ loaded, total });
        }
      } finally { reader.releaseLock(); }
      if (!active) throw new Error('Cancelled model request.');
      const joined = new Uint8Array(loaded);
      let offset = 0;
      for (const chunk of chunks) { joined.set(chunk, offset); offset += chunk.byteLength; }
      bytes = joined.buffer;
    } else {
      bytes = await response.arrayBuffer();
      if (active) options.onProgress?.({ loaded: bytes.byteLength, total });
    }
    return bytes;
  }
  async function verify(bytes: ArrayBuffer) {
    if (!options.expectedSha256 || !globalThis.crypto?.subtle) return;
    const digest = await crypto.subtle.digest('SHA-256', bytes);
    const actual = Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
    if (actual !== options.expectedSha256) throw new Error('Model checksum does not match this release.');
  }
  void (async () => {
    let bytes: ArrayBuffer;
    if (options.compressed && typeof DecompressionStream !== 'undefined') {
      try {
        bytes = await download(options.compressedUrl ?? gzipUrl(options.url));
        const magic = new Uint8Array(bytes, 0, Math.min(bytes.byteLength, 2));
        // Hosts may already decompress a response with Content-Encoding: gzip.
        if (magic[0] === 0x1f && magic[1] === 0x8b) {
          bytes = await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
        }
        await verify(bytes);
      } catch (error) {
        if (!active || abort.signal.aborted) return;
        bytes = await download(options.url);
        await verify(bytes);
      }
    } else { bytes = await download(options.url); await verify(bytes); }
    if (!active) return;
    const value = await options.parse(bytes);
    if (!active) { options.disposeLate(value); return; }
    finish();
    try { options.onLoad(value); } catch (error) { options.onError(error); }
  })().catch(fail);
  return { cancel() { if (active) { finish(); abort.abort(); } } };
}
