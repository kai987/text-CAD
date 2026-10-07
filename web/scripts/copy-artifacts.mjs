import { copyFile, mkdir, readFile, writeFile, rm } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { gzipSync, gunzipSync } from 'node:zlib';
import { validateCadRelease } from './cad-release-validation.mjs';
import { validatePlanPreviews, validateApartmentPreviews } from './plan-preview-validation.mjs';

const root = fileURLToPath(new URL('../../', import.meta.url));
const dest = resolve(root, 'web/public/artifacts');
await validateCadRelease(root);
// Fail before publishing if the approved PDF was changed without regenerating SVG.
const vectorPlans = await validatePlanPreviews(root);
const apartmentPlans = await validateApartmentPreviews(root);
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
  ...apartmentPlans.floors.map(floor => floor.path),
];

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const manifest = {};
for (const source of artifacts) {
  const bytes = await readFile(resolve(root, source));
  if (!bytes.length) throw new Error(`Empty artifact: ${source}`);
  const out = resolve(dest, source);
  await mkdir(dirname(out), { recursive: true });
  if (source==='STEP/house_3d.step') {
    const compressed=gzipSync(bytes,{level:9});
    if (!gunzipSync(compressed).equals(bytes)) throw new Error('STEP transport round-trip failed');
    await writeFile(`${out}.gz`,compressed);
    manifest[`${source}.gz`]={bytes:compressed.length,sha256:sha(compressed),decodedBytes:bytes.length,decodedSha256:sha(bytes)};
    await rm(out,{force:true});
    continue;
  }
  await copyFile(resolve(root, source), out);
  manifest[source] = { bytes: bytes.length, sha256: sha(bytes) };
  if (source.endsWith('.glb')) {
    const compressed = gzipSync(bytes, { level: 9 });
    if (!gunzipSync(compressed).equals(bytes)) throw new Error(`Model transport round-trip failed: ${source}`);
    await writeFile(`${out}.gz`, compressed);
    manifest[`${source}.gz`] = { bytes: compressed.length, sha256: sha(compressed) };
    console.log(`${source}: ${bytes.length} -> ${compressed.length} transport bytes (${Math.round(100 * compressed.length / bytes.length)}%).`);
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
await writeFile(resolve(root, 'web/src/house-data.json'), JSON.stringify(data, null, 2) + '\n');
await copyFile(resolve(root, 'output/review/apartment_2ldk_manifest.json'), resolve(root, 'web/src/apartment-data.json'));
await copyFile(resolve(root, 'output/review/apartment_2ldk_preview.json'), resolve(root, 'web/src/apartment-preview-metadata.json'));
console.log(`Prepared ${Object.keys(manifest).length} CAD/drawing and lossless transport assets, including verified vector PDF previews.`);
