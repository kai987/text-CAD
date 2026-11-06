import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { tmpdir } from 'node:os';
import { preparationInputPaths, preparationSnapshot, preparationCacheMatches, savePreparationCache } from '../scripts/artifact-preparation-cache.mjs';

async function fixture(t) {
  const root = await mkdtemp(join(tmpdir(), 'text-cad-prepare-cache-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const files = {
    'src/model.py': 'parameter = 1',
    'GLB/model.glb': 'native model',
    'web/scripts/copy-artifacts.mjs': 'prepare()',
    'web/scripts/nested/validation.mjs': 'validate()',
    'web/package-lock.json': '{}',
    'web/src/cad-outlines.ts': 'outlines',
    'web/src/static-outline-cache.ts': 'cache format',
    'web/public/artifacts/manifest.json': '{}',
    'web/public/artifacts/GLB/model.glb.gz': 'compressed model',
    'web/public/artifacts/output/review/seto_ohashi_summary.json': '{"revision":"BRIDGE-R05"}',
    'web/src/model-data.json': '{"revision":"1"}',
  };
  async function write(path, value) {
    await mkdir(dirname(join(root, path)), { recursive: true });
    await writeFile(join(root, path), value);
  }
  for (const [path, value] of Object.entries(files)) await write(path, value);
  const inputs = await preparationInputPaths(root, ['GLB/model.glb'], {
    sources: { 'src/model.py': 'verified hash' }, artifacts: { 'GLB/model.glb': 'verified hash' },
  });
  const metadata = ['web/src/model-data.json'];
  const snapshot = () => preparationSnapshot(root, inputs);
  const matches = async () => preparationCacheMatches(root, await snapshot(), metadata);
  const save = async () => savePreparationCache(root, await snapshot(), metadata);
  return { root, files, write, inputs, metadata, snapshot, matches, save };
}

test('prepared output is reused only after every input and generated output hash matches', async t => {
  const f = await fixture(t);
  assert.equal(await f.matches(), false);
  await f.save();
  assert.equal(await f.matches(), true);
  for (const path of ['src/model.py', 'GLB/model.glb', 'web/scripts/nested/validation.mjs',
    'web/package-lock.json', 'web/src/cad-outlines.ts', 'web/src/static-outline-cache.ts']) {
    await f.write(path, 'changed input');
    assert.equal(await f.matches(), false, path);
    await f.write(path, f.files[path]);
    assert.equal(await f.matches(), true, path);
  }
});

test('corrupt, missing, extra and modified generated metadata all invalidate reuse', async t => {
  const f = await fixture(t);
  await f.save();
  for (const path of ['web/public/artifacts/GLB/model.glb.gz', 'web/public/artifacts/manifest.json',
    'web/public/artifacts/output/review/seto_ohashi_summary.json',
    'web/src/model-data.json']) {
    await f.write(path, 'corrupt output');
    assert.equal(await f.matches(), false, path);
    await rm(join(f.root, path));
    assert.equal(await f.matches(), false, path);
    await f.write(path, f.files[path]);
    assert.equal(await f.matches(), true, path);
  }
  await f.write('web/public/artifacts/stale.bin', 'unregistered output');
  assert.equal(await f.matches(), false);
});

test('malformed, obsolete and incompatible runtime cache records cause a rebuild', async t => {
  const f = await fixture(t);
  await f.save();
  const path = 'web/.artifact-preparation-cache.json';
  const record = JSON.parse(await readFile(join(f.root, path), 'utf8'));
  for (const invalid of ['{broken', 'null', JSON.stringify({ ...record, schemaVersion: 0 }),
    JSON.stringify({ ...record, nodeVersion: 'different runtime' })]) {
    await f.write(path, invalid);
    assert.equal(await f.matches(), false);
  }
});

test('source changes during generation cannot bless outputs or replace a completed cache', async t => {
  const f = await fixture(t);
  await f.save();
  const path = join(f.root, 'web/.artifact-preparation-cache.json');
  const previous = await readFile(path);
  const before = await f.snapshot();
  await f.write('src/model.py', 'changed concurrently');
  await assert.rejects(savePreparationCache(f.root, before, f.metadata), /inputs changed/);
  assert.deepEqual(await readFile(path), previous);
});

test('new helper dependencies change the exact input catalog', async t => {
  const f = await fixture(t);
  await f.save();
  await f.write('web/scripts/new-validation.mjs', 'new dependency');
  const paths = await preparationInputPaths(f.root, ['GLB/model.glb'], {
    sources: { 'src/model.py': 'verified hash' }, artifacts: { 'GLB/model.glb': 'verified hash' },
  });
  assert.equal(await preparationCacheMatches(f.root, await preparationSnapshot(f.root, paths), f.metadata), false);
});
