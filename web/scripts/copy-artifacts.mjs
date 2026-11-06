import { copyFile, mkdir, readFile, writeFile, rm, readdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { basename, dirname, resolve } from 'node:path';
import { gzipSync } from 'node:zlib';
import { validateCadRelease } from './cad-release-validation.mjs';
import { validatePlanPreviews, validateApartmentPreviews } from './plan-preview-validation.mjs';
import { validateAnalysisReport } from './analysis-report-validation.mjs';
import { validateRiverArtifacts } from './river-artifact-validation.mjs';
import { validateTowerArtifacts } from './tower-artifact-validation.mjs';
import { buildStaticOutlines } from './static-outlines.mjs';
import { artifactTransport } from './artifact-transport.mjs';
import { buildLandmarkCatalog, catalogText } from './landmark-catalog.mjs';
import { preparationInputPaths, preparationSnapshot, preparationCacheMatches, savePreparationCache } from './artifact-preparation-cache.mjs';

const root = fileURLToPath(new URL('../../', import.meta.url));
const dest = resolve(root, 'web/public/artifacts');
const release = await validateCadRelease(root);
// Fail before publishing if the approved PDF was changed without regenerating SVG.
const vectorPlans = await validatePlanPreviews(root);
const apartmentPlans = await validateApartmentPreviews(root);
const analysisReport = await validateAnalysisReport(root);
const riverArtifacts = await validateRiverArtifacts(root);
const towerArtifacts = await validateTowerArtifacts(root);
// Display metadata comes from the same verified, downloadable CAD manifests.
const landmarkCatalog = buildLandmarkCatalog(towerArtifacts.models.map(({ manifest }) => manifest));
export const artifacts = [
  'output/review/cad_release.json',
  'GLB/house_3d.glb', 'STEP/house_3d.step', 'STEP/house_3d.step.json',
  'DXF/001D0PL2-1FPLAN.DXF', 'DXF/002D0PL2-2FPLAN.DXF',
  'DXF/house_attic_plan.dxf', 'output/pdf/house_attic_plan_R06_JP.pdf',
  'DXF/house_structural_scheme.dxf', 'output/pdf/house_structural_scheme_R06_JP.pdf',
  'DXF/house_site_plan.dxf', 'output/pdf/house_site_plan_R05_JP.pdf',
  'output/pdf/house_floor_plans_R10_JP.pdf',
  'output/review/jp_floor_plan-1.png', 'output/review/jp_floor_plan-2.png',
  'output/review/house_3d_iso.png',
  'output/review/house_3d_1f_interior.png', 'output/review/house_3d_2f_interior.png',
  'output/review/house_3d_attic_interior.png', 'output/review/house_3d_structure.png',
  'output/review/engineering_inputs_R06.json', 'src/lib/engineering_inputs.py',
  ...['W', 'S', 'RC'].flatMap(system => [`GLB/structure_${system}.glb`, `STEP/structure_${system}.step`]),
  'output/review/regulatory_profiles_R07.json', 'output/review/structural_variants_R07.json',
  'output/review/structural_cases_R07.json',
  ...['tokyo', 'osaka', 'kyoto', 'nagoya'].flatMap(city =>
    ['W', 'S', 'RC'].map(system => `output/review/cases/${city}_${system}_R07.json`)),
  'output/review/design_manifest.json', 'output/review/house_3d_assumptions_R01.json',
  ...vectorPlans.floors.map(floor => floor.path),
  'GLB/apartment_2ldk.glb', 'STEP/apartment_2ldk.step',
  'DXF/apartment_2ldk_plan.dxf', 'output/pdf/apartment_2ldk_plan.pdf',
  'output/review/apartment_2ldk_manifest.json', 'output/review/apartment_2ldk_preview.json',
  'output/review/apartment_2ldk_iso.png',
  ...analysisReport.paths,
  ...apartmentPlans.floors.map(floor => floor.path),
  ...riverArtifacts.paths,
  ...towerArtifacts.paths,
  'src/towers_3d.py', 'src/generate_tower_plans.py', 'src/lib/tower_geometry.py', 'src/lib/tower_parameters.py', 'src/lib/tokyo_tower_parameters.py', 'src/lib/skytree_parameters.py', 'src/lib/tokyo_tower_detail.py', 'src/lib/tokyo_tower_steel.py', 'src/lib/tokyo_tower_equipment.py', 'src/lib/tokyo_tower_builtup.py', 'src/lib/tokyo_tower_integrated.py', 'src/lib/tokyo_tower_grid.py', 'src/lib/skytree_detail.py', 'src/lib/skytree_outline.py',
  'src/river_3d.py', 'src/generate_river_plans.py', 'src/lib/river_geometry.py',
];

const generatedMetadata = ['web/src/landmark-catalog.json', 'web/src/house-data.json',
  'web/src/apartment-data.json', 'web/src/apartment-preview-metadata.json', 'web/src/river-data.json'];
const inputs = await preparationSnapshot(root, await preparationInputPaths(root, artifacts, release));
if (await preparationCacheMatches(root, inputs, generatedMetadata)) {
  await validateCadRelease(root);
  console.log('Reused prepared artifacts after checking every input and generated output hash.');
} else {
  const sha = bytes => createHash('sha256').update(bytes).digest('hex');
  const manifest = {};
  for (const source of artifacts) {
    const bytes = await readFile(resolve(root, source));
    if (!bytes.length) throw new Error(`Empty artifact: ${source}`);
    const out = resolve(dest, source);
    await mkdir(dirname(out), { recursive: true });
    const transport = artifactTransport(source, bytes);
    Object.assign(manifest, transport.records);
    if (transport.records[source].transport === 'gzip') await rm(out, { force: true });
    if (!transport.records[`${source}.gz`] || transport.records[`${source}.gz`].transport === 'chunks') await rm(`${out}.gz`, { force: true });
    const chunkPrefix = `${basename(out)}.gz.part-`;
    for (const oldPart of await readdir(dirname(out))) {
      if (oldPart.startsWith(chunkPrefix) && /^\d{3}$/.test(oldPart.slice(chunkPrefix.length))) {
        await rm(resolve(dirname(out), oldPart), { force: true });
      }
    }
    for (const [path, payload] of transport.files) await writeFile(resolve(dest, path), payload);
    if (source.endsWith('.glb')) {
      const encoded = transport.records[`${source}.gz`];
      if (encoded) console.log(`${source}: ${bytes.length} -> ${encoded.bytes} transport bytes (${Math.round(100 * encoded.bytes / bytes.length)}%).`);
      else console.log(`${source}: ${bytes.length} raw bytes retained; gzip would not reduce transfer size.`);
      if (!source.endsWith('river_demo.glb') && !/\/tokyo_(tower|skytree)\.glb$/.test(source)) {
        // Display-only edges are pinned to the exact downloadable model bytes.
        const outlines = await buildStaticOutlines(bytes);
        const cachePath = `${source}.edges.bin`;
        const packed = gzipSync(outlines.bytes, { level: 9 });
        await writeFile(`${out}.edges.bin`, outlines.bytes);
        await writeFile(`${out}.edges.bin.gz`, packed);
        manifest[cachePath] = { bytes: outlines.bytes.length, sha256: sha(outlines.bytes) };
        manifest[`${cachePath}.gz`] = { bytes: packed.length, sha256: sha(packed), decodedBytes: outlines.bytes.length, decodedSha256: sha(outlines.bytes) };
        console.log(`${source}: precomputed ${outlines.entries} outlines (${packed.length} transport bytes).`);
      }
    }
  }
  await writeFile(resolve(dest, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
  const plan = JSON.parse(await readFile(resolve(root, 'output/review/design_manifest.json'), 'utf8'));
  const model = JSON.parse(await readFile(resolve(root, 'output/review/house_3d_assumptions_R01.json'), 'utf8'));
  const data = {
    parameters: plan.parameters,
    drawingRevision: plan.drawing_revision,
    modelRevision: model.revision,
    assumptions: [...plan.assumptions, ...model.assumptions],
    floors: plan.floors.map(f => ({ floor: f.floor, rooms: f.rooms.map(r => ({
      id: r.id, name: r.name, area: r.area_m2, size: r.size_note,
    })) })),
  };
  await mkdir(resolve(root, 'web/src'), { recursive: true });
  await writeFile(resolve(root, 'web/src/landmark-catalog.json'), catalogText(landmarkCatalog));
  await writeFile(resolve(root, 'web/src/house-data.json'), JSON.stringify(data, null, 2) + '\n');
  await copyFile(resolve(root, 'output/review/apartment_2ldk_manifest.json'), resolve(root, 'web/src/apartment-data.json'));
  await copyFile(resolve(root, 'output/review/apartment_2ldk_preview.json'), resolve(root, 'web/src/apartment-preview-metadata.json'));
  await copyFile(resolve(root, 'output/review/river_demo_manifest.json'), resolve(root, 'web/src/river-data.json'));
  console.log(`Prepared ${Object.keys(manifest).length} CAD/drawing and lossless transport assets, including verified vector PDF previews.`);
  await validateCadRelease(root);
  await savePreparationCache(root, inputs, generatedMetadata);
}
