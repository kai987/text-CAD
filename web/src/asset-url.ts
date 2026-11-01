import type { ArtifactMetadata, DownloadTransport } from './download-transport';

export function artifactUrl(base: string, path: string, hashes: Record<string, string>, manifestHash: string,
  selectedSha256?: string): string {
  if (selectedSha256 !== undefined && !/^[0-9a-f]{64}$/.test(selectedSha256)) {
    throw new Error('Invalid selected artifact hash.');
  }
  const digest = selectedSha256 ?? (path === 'manifest.json' ? manifestHash : hashes[path]);
  return `${base}artifacts/${path}${digest ? `?v=${digest}` : ''}`;
}

/** Runtime manifest selections own the transfer versions, including each chunk. */
export function artifactDownloadRequests(transfer: DownloadTransport,
  resolve: (path: string, selectedSha256?: string) => string): {
    url: string; parts?: { url: string; metadata: ArtifactMetadata }[];
  } {
  return {
    url: resolve(transfer.path, transfer.metadata.sha256),
    parts: transfer.metadata.transport === 'chunks'
      ? transfer.metadata.parts!.map(part => ({ url: resolve(part.path, part.sha256), metadata: part }))
      : undefined,
  };
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
