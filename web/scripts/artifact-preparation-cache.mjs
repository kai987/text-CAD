import { createHash, randomUUID } from 'node:crypto';
import { createReadStream } from 'node:fs';
import { lstat, mkdir, readFile, readdir, rename, rm, writeFile } from 'node:fs/promises';
import { dirname, resolve, sep } from 'node:path';

const cachePath = 'web/.artifact-preparation-cache.json';
const schemaVersion = 1;

async function filesUnder(root, directory) {
  const full = resolve(root, directory);
  const entries = await readdir(full, { withFileTypes: true });
  const paths = [];
  for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name))) {
    const path = `${directory}/${entry.name}`;
    if (entry.isDirectory()) paths.push(...await filesUnder(root, path));
    else if (entry.isFile()) paths.push(path);
    else throw new Error(`Preparation input/output must be a regular file: ${path}`);
  }
  return paths;
}

export async function preparationInputPaths(root, artifacts, release) {
  const scripts = (await filesUnder(root, 'web/scripts')).filter(path => path.endsWith('.mjs'));
  return [...new Set([...artifacts, ...Object.keys(release.sources), ...Object.keys(release.artifacts),
    ...scripts, 'web/package-lock.json',
    'web/src/cad-outlines.ts', 'web/src/static-outline-cache.ts'])].sort();
}

export async function preparationSnapshot(root, paths) {
  const snapshot = {};
  for (const path of [...new Set(paths)].sort()) {
    const full = resolve(root, path);
    if (!full.startsWith(resolve(root) + sep) || !(await lstat(full)).isFile()) {
      throw new Error(`Preparation input/output must be inside the repository: ${path}`);
    }
    const hash = createHash('sha256');
    for await (const bytes of createReadStream(full)) hash.update(bytes);
    snapshot[path] = hash.digest('hex');
  }
  return snapshot;
}

async function outputSnapshot(root, metadata) {
  return preparationSnapshot(root, [...await filesUnder(root, 'web/public/artifacts'), ...metadata]);
}

function same(a, b) {
  return JSON.stringify(a) === JSON.stringify(b);
}

export async function preparationCacheMatches(root, inputs, metadata) {
  try {
    const record = JSON.parse(await readFile(resolve(root, cachePath), 'utf8'));
    if (!record || record.schemaVersion !== schemaVersion || record.nodeVersion !== process.versions.node
        || !same(record.inputs, inputs)) return false;
    return same(record.outputs, await outputSnapshot(root, metadata))
      && same(inputs, await preparationSnapshot(root, Object.keys(inputs)));
  } catch (error) {
    if (error.code === 'ENOENT' || error instanceof SyntaxError) return false;
    throw error;
  }
}

export async function savePreparationCache(root, inputs, metadata) {
  if (!same(inputs, await preparationSnapshot(root, Object.keys(inputs)))) {
    throw new Error('Artifact preparation inputs changed while generating outputs.');
  }
  const record = { schemaVersion, nodeVersion: process.versions.node, inputs,
    outputs: await outputSnapshot(root, metadata) };
  const target = resolve(root, cachePath), temporary = `${target}.${randomUUID()}.tmp`;
  await mkdir(dirname(target), { recursive: true });
  try {
    await writeFile(temporary, JSON.stringify(record) + '\n', { flag: 'wx' });
    await rename(temporary, target);
  } finally {
    await rm(temporary, { force: true });
  }
}
