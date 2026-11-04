import { readFile, readdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { validatePlanMetadata, apartmentPlanRequirements } from './plan-preview-validation.mjs';
import { verifySectionWasmArtifacts } from './section-wasm-artifacts.mjs';
import { verifyArtifactTransports, verifyStaticBuildBudget } from './artifact-transport.mjs';

const dist = fileURLToPath(new URL('../dist/', import.meta.url));
const budget = await verifyStaticBuildBudget(dist);
await verifySectionWasmArtifacts(dist);
const vectorMetadata = JSON.parse(await readFile(new URL('../src/plan-preview-metadata.json', import.meta.url), 'utf8'));
validatePlanMetadata(vectorMetadata,
  await readFile(resolve(dist, 'artifacts', vectorMetadata.source.path)),
  new Map(await Promise.all(vectorMetadata.floors.map(async floor => [
    floor.floor, await readFile(resolve(dist, 'artifacts', floor.path)),
  ]))));
const apartmentMetadata = JSON.parse(await readFile(resolve(dist, 'artifacts/output/review/apartment_2ldk_preview.json'), 'utf8'));
validatePlanMetadata(apartmentMetadata,
  await readFile(resolve(dist, 'artifacts', apartmentMetadata.source.path)),
  new Map(await Promise.all(apartmentMetadata.floors.map(async floor => [
    floor.floor, await readFile(resolve(dist, 'artifacts', floor.path)),
  ]))), apartmentPlanRequirements);
const manifest = JSON.parse(await readFile(resolve(dist, 'artifacts/manifest.json'), 'utf8'));
await verifyArtifactTransports(resolve(dist, 'artifacts'), manifest);
const html = await readFile(resolve(dist, 'index.html'), 'utf8');
if (!html.includes('/text-CAD/assets/')) throw new Error('Incorrect GitHub Pages project base.');
const scripts = (await readdir(resolve(dist, 'assets'))).filter(x => x.endsWith('.js'));
for (const name of scripts) {
  const js = await readFile(resolve(dist, 'assets', name), 'utf8');
  if (/127\.0\.0\.1:3245|localhost:3245/.test(js)) throw new Error('Local CAD server dependency in build.');
}
console.log(`Verified ${Object.keys(manifest).length} asset hashes and static Pages URLs.`);
console.log(`Expanded static build: ${budget.bytes} / ${budget.limitBytes} bytes across ${budget.files} files.`);
