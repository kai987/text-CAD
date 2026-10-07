import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { resolve } from 'node:path';
import { artifactUrl, gzipUrl, pinnedSourceUrl } from '../src/asset-url.ts';
import { releaseBuildDefinitions } from '../scripts/release-build-meta.mjs';

test('artifact URLs use the right release hash for native, gzip and manifest on both hosts', () => {
  const hashes = { 'GLB/house.glb': 'native', 'GLB/house.glb.gz': 'gzip' };
  for (const base of ['/', '/text-CAD/']) {
    assert.equal(artifactUrl(base, 'GLB/house.glb', hashes, 'catalog'), `${base}artifacts/GLB/house.glb?v=native`);
    assert.equal(artifactUrl(base, 'GLB/house.glb.gz', hashes, 'catalog'), `${base}artifacts/GLB/house.glb.gz?v=gzip`);
    assert.equal(artifactUrl(base, 'manifest.json', hashes, 'catalog'), `${base}artifacts/manifest.json?v=catalog`);
  }
  assert.equal(gzipUrl('/model.glb?v=abc#mesh'), '/model.glb.gz?v=abc#mesh');
  assert.equal(gzipUrl('https://host/model.glb#mesh'), 'https://host/model.glb.gz#mesh');
});
test('source links resolve the exact GitHub revision and refuse an unknown revision', () => {
  const sha = 'a'.repeat(40);
  assert.equal(pinnedSourceUrl('https://github.com/kai987/text-CAD', sha, 'src/lib', 'tree'),
    `https://github.com/kai987/text-CAD/tree/${sha}/src/lib`);
  assert.throws(() => pinnedSourceUrl('repo', 'main', 'src.py'), /Missing release/);
});
test('build metadata binds artifact hashes and uses GitHub source identity for a Sites checkout', async t => {
  const root = await mkdtemp(resolve(tmpdir(), 'cad-build-meta-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  await mkdir(resolve(root, 'web/public/artifacts'), { recursive: true });
  await mkdir(resolve(root, 'docs'));
  const hash = 'b'.repeat(64), sha = 'c'.repeat(40);
  await writeFile(resolve(root, 'web/public/artifacts/manifest.json'), JSON.stringify({ 'GLB/a.glb': { sha256: hash } }));
  await writeFile(resolve(root, 'docs/sites-release.json'), JSON.stringify({ github_commit: sha }));
  const defs = releaseBuildDefinitions(root);
  assert.equal(JSON.parse(defs.__CAD_ASSET_HASHES__)['GLB/a.glb'], hash);
  assert.equal(JSON.parse(defs.__CAD_SOURCE_COMMIT__), sha);
  assert.match(JSON.parse(defs.__CAD_MANIFEST_HASH__), /^[a-f0-9]{64}$/);
  assert.throws(() => releaseBuildDefinitions(root, 'main'), /Invalid release/);
});
