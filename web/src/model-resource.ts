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
  void (async () => {
    const response = await (options.fetcher ?? fetch)(options.url, { signal: abort.signal });
    if (!response.ok) throw new Error(`Model request failed: ${response.status}`);
    const length = Number(response.headers.get('content-length'));
    const total = Number.isFinite(length) && length > 0 ? length : null;
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
      if (!active) return;
      const joined = new Uint8Array(loaded);
      let offset = 0;
      for (const chunk of chunks) { joined.set(chunk, offset); offset += chunk.byteLength; }
      bytes = joined.buffer;
    } else {
      bytes = await response.arrayBuffer();
      if (active) options.onProgress?.({ loaded: bytes.byteLength, total });
    }
    if (!active) return;
    const value = await options.parse(bytes);
    if (!active) { options.disposeLate(value); return; }
    finish();
    try { options.onLoad(value); } catch (error) { options.onError(error); }
  })().catch(fail);
  return { cancel() { if (active) { finish(); abort.abort(); } } };
}
