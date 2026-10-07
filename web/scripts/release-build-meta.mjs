import { readFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

export function releaseBuildDefinitions(root = fileURLToPath(new URL('../../', import.meta.url)), commit) {
  const bytes = readFileSync(resolve(root, 'web/public/artifacts/manifest.json'));
  const manifest = JSON.parse(bytes.toString());
  const hashes = {};
  for (const [path, entry] of Object.entries(manifest)) {
    if (!/^[0-9a-f]{64}$/.test(entry.sha256)) throw new Error(`Invalid artifact hash: ${path}`);
    hashes[path] = entry.sha256;
  }
  // Sites has its own source history. Link to the GitHub commit it was copied from.
  const siteRecord = resolve(root, 'docs/sites-release.json');
  const sourceCommit = commit ?? (existsSync(siteRecord)
    ? JSON.parse(readFileSync(siteRecord, 'utf8')).github_commit
    : execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim());
  if (!/^[0-9a-f]{40}$/.test(sourceCommit)) throw new Error('Invalid release source commit.');
  return {
    __CAD_ASSET_HASHES__: JSON.stringify(hashes),
    __CAD_MANIFEST_HASH__: JSON.stringify(createHash('sha256').update(bytes).digest('hex')),
    __CAD_SOURCE_COMMIT__: JSON.stringify(sourceCommit),
  };
}
