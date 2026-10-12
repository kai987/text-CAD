import { startModelLoad } from './model-resource.ts';
import { decodeStaticOutlineCache } from './static-outline-cache.ts';
import type { StaticOutlineEntry } from './static-outline-cache.ts';

/** Optional display data. Missing/stale cache falls back to the geometry worker. */
export function loadStaticOutlines(options: {
  url: string; compressedUrl: string; expectedSha256?: string; sourceSha256?: string;
}) {
  let resolve!: (entries: ReadonlyMap<number, StaticOutlineEntry> | null) => void;
  const ready = new Promise<ReadonlyMap<number, StaticOutlineEntry> | null>(done => { resolve = done; });
  if (!options.sourceSha256 || !options.expectedSha256 || !globalThis.crypto?.subtle) {
    resolve(null);
    return { ready, cancel() {} };
  }
  const request = startModelLoad({
    ...options, compressed: true, timeoutMs: 3000,
    parse: async bytes => decodeStaticOutlineCache(bytes, options.sourceSha256!),
    onLoad: resolve, onError: () => resolve(null), disposeLate: () => {},
  });
  return { ready, cancel() { request.cancel(); resolve(null); } };
}
