import { readFile, readdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { validatePlanMetadata } from './plan-preview-validation.mjs';

const dist = fileURLToPath(new URL('../dist/', import.meta.url));
const vectorMetadata = JSON.parse(await readFile(new URL('../src/plan-preview-metadata.json', import.meta.url), 'utf8'));
validatePlanMetadata(vectorMetadata,
  await readFile(resolve(dist, 'artifacts', vectorMetadata.source.path)),
  new Map(await Promise.all(vectorMetadata.floors.map(async floor => [
    floor.floor, await readFile(resolve(dist, 'artifacts', floor.path)),
  ]))));
const manifest = JSON.parse(await readFile(resolve(dist, 'artifacts/manifest.json'), 'utf8'));
for (const [name, expected] of Object.entries(manifest)) {
  const bytes = await readFile(resolve(dist, 'artifacts', name));
  const hash = createHash('sha256').update(bytes).digest('hex');
  if (hash !== expected.sha256) throw new Error(`Published asset differs: ${name}`);
}
const html = await readFile(resolve(dist, 'index.html'), 'utf8');
if (!html.includes('/text-CAD/assets/')) throw new Error('Incorrect GitHub Pages project base.');
const scripts = (await readdir(resolve(dist, 'assets'))).filter(x => x.endsWith('.js'));
for (const name of scripts) {
  const js = await readFile(resolve(dist, 'assets', name), 'utf8');
  if (/127\.0\.0\.1:3245|localhost:3245/.test(js)) throw new Error('Local CAD server dependency in build.');
}
console.log(`Verified ${Object.keys(manifest).length} asset hashes and static Pages URLs.`);
