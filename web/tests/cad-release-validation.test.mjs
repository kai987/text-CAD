import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { resolve, dirname } from 'node:path';
import { createHash } from 'node:crypto';
import { validateCadRelease } from '../scripts/cad-release-validation.mjs';
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
test('the web publication gate rejects source drift, broken CAD and unknown paths', async t => {
  const root = await mkdtemp(resolve(tmpdir(), 'cad-release-test-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const sources = ['src/model.py', 'checks/validate.py', 'requirements.txt', 'web/scripts/generate-plan-svg.py'];
  for (const path of [...sources, 'GLB/house.glb']) {
    await mkdir(dirname(resolve(root, path)), { recursive: true });
    await writeFile(resolve(root, path), 'original');
  }
  const release = { schema_version: 1, validation_commands: ['check.py'],
    sources: Object.fromEntries(sources.map(path => [path, sha('original')])),
    artifacts: { 'GLB/house.glb': sha('original') } };
  await mkdir(resolve(root, 'output/review'), { recursive: true });
  const save = () => writeFile(resolve(root, 'output/review/cad_release.json'), JSON.stringify(release));
  await save(); await validateCadRelease(root);
  await writeFile(resolve(root, 'src/model.py'), 'new parameters');
  await assert.rejects(validateCadRelease(root), /Stale CAD sources/);
  await writeFile(resolve(root, 'src/model.py'), 'original');
  await writeFile(resolve(root, 'GLB/house.glb'), 'corrupt');
  await assert.rejects(validateCadRelease(root), /Stale CAD artifacts/);
  await writeFile(resolve(root, 'GLB/house.glb'), 'original');
  await writeFile(resolve(root, 'src/new.py'), 'new');
  await assert.rejects(validateCadRelease(root), /source set changed/);
  await rm(resolve(root, 'src/new.py'));
  release.artifacts = { '../outside': 'bad' }; await save();
  await assert.rejects(validateCadRelease(root), /Invalid CAD release path/);
});
