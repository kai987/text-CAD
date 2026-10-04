import { copyFile, mkdir, readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { validatePlanPreviews } from './plan-preview-validation.mjs';

const root = fileURLToPath(new URL('../../', import.meta.url));
const dest = resolve(root, 'web/public/artifacts');
// Fail before publishing if the approved PDF was changed without regenerating SVG.
const vectorPlans = await validatePlanPreviews(root);
export const artifacts = [
  'GLB/house_3d.glb', 'STEP/house_3d.step', 'STEP/house_3d.step.json',
  'DXF/001D0PL2-1FPLAN.DXF', 'DXF/002D0PL2-2FPLAN.DXF',
  'output/pdf/house_floor_plans_R02_JP.pdf',
  'output/review/jp_floor_plan-1.png', 'output/review/jp_floor_plan-2.png',
  'output/review/house_3d_iso.png',
  'output/review/house_3d_1f_interior.png', 'output/review/house_3d_2f_interior.png',
  'output/review/design_manifest.json', 'output/review/house_3d_assumptions_R01.json',
  ...vectorPlans.floors.map(floor => floor.path),
];

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const manifest = {};
for (const source of artifacts) {
  const bytes = await readFile(resolve(root, source));
  if (!bytes.length) throw new Error(`Empty artifact: ${source}`);
  const out = resolve(dest, source);
  await mkdir(dirname(out), { recursive: true });
  await copyFile(resolve(root, source), out);
  manifest[source] = { bytes: bytes.length, sha256: sha(bytes) };
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
console.log(`Prepared ${artifacts.length} CAD/drawing assets, including verified vector PDF previews.`);
