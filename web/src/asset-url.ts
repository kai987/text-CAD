export function artifactUrl(base: string, path: string, hashes: Record<string, string>, manifestHash: string): string {
  const digest = path === 'manifest.json' ? manifestHash : hashes[path];
  return `${base}artifacts/${path}${digest ? `?v=${digest}` : ''}`;
}

// Insert the suffix before the query/hash, even when the caller uses a relative URL.
export function gzipUrl(url: string): string {
  const at = url.search(/[?#]/);
  return at < 0 ? `${url}.gz` : `${url.slice(0, at)}.gz${url.slice(at)}`;
}

export function pinnedSourceUrl(repository: string, commit: string, path: string, kind: 'blob' | 'tree' = 'blob'): string {
  if (!/^[0-9a-f]{40}$/.test(commit)) throw new Error('Missing release source commit.');
  return `${repository}/${kind}/${commit}/${path}`;
}
