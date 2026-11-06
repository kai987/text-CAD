import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';

export const towerCatalog = [
  { id: 'tokyo-tower', stem: 'tokyo_tower', revision: 'LANDMARK-R11', height: 333000, decks: [125000, 223550], sources: ['src/lib/tokyo_tower_parameters.py', 'src/lib/tokyo_tower_detail.py', 'src/lib/tokyo_tower_steel.py', 'src/lib/tokyo_tower_equipment.py', 'src/lib/tokyo_tower_builtup.py', 'src/lib/tokyo_tower_integrated.py', 'src/lib/tokyo_tower_grid.py'] },
  { id: 'tokyo-skytree', stem: 'tokyo_skytree', revision: 'LANDMARK-R05', height: 634000, decks: [350000, 450000], roofLevels: [375000], sources: ['src/lib/skytree_parameters.py', 'src/lib/skytree_detail.py', 'src/lib/skytree_outline.py'] },
];
const modelSources = ['src/lib/tower_geometry.py', 'src/lib/tower_parameters.py', 'src/towers_3d.py'];
const drawingSources = ['src/lib/tower_geometry.py', 'src/lib/tower_parameters.py', 'src/generate_tower_plans.py'];
const sha = value => createHash('sha256').update(value).digest('hex');
const sameKeys = (record, paths) => record && typeof record === 'object' && !Array.isArray(record)
  && JSON.stringify(Object.keys(record).sort()) === JSON.stringify([...paths].sort());
const stepHeader = Buffer.from('ISO-10303-21;');
const stepFooter = Buffer.from('END-ISO-10303-21;');
export function hasStepContainerMarkers(bytes) {
  // A detailed STEP can exceed V8's maximum string length. Integrity and
  // native validity are checked separately; container markers stay binary.
  return Buffer.isBuffer(bytes) && bytes.subarray(0, stepHeader.length).equals(stepHeader)
    && bytes.includes(stepFooter);
}

export function towerPaths(stem) {
  return {
    models: [`STEP/${stem}.step`, `GLB/${stem}.glb`],
    drawings: [`DXF/${stem}_plan.dxf`, `DXF/${stem}_elevation.dxf`,
      `output/svg/${stem}_plan.svg`, `output/svg/${stem}_elevation.svg`, `output/pdf/${stem}_sheets.pdf`,
      ...(stem === 'tokyo_tower' ? [`DXF/${stem}_steel_nodes.dxf`, `output/svg/${stem}_steel_nodes.svg`]
        : stem === 'tokyo_skytree' ? [`DXF/${stem}_structure_zones.dxf`, `output/svg/${stem}_structure_zones.svg`] : [])],
    metadata: [`output/review/${stem}_manifest.json`, `output/review/${stem}_drawings.json`],
  };
}
export const towerArtifactPaths = towerCatalog.flatMap(({ stem }) => {
  const paths = towerPaths(stem);
  return [...paths.models, ...paths.drawings, ...paths.metadata];
});

async function bytes(root, path) {
  try { return await readFile(resolve(root, path)); }
  catch (error) { throw new Error(`Missing tower asset or source: ${path}`, { cause: error }); }
}
async function sourcesMatch(root, bindings, expected) {
  if (!sameKeys(bindings, expected)) throw new Error('Invalid tower source set.');
  for (const path of expected) {
    if (!/^[a-f0-9]{64}$/.test(bindings[path] ?? '') || sha(await bytes(root, path)) !== bindings[path]) {
      throw new Error(`Stale tower source: ${path}; regenerate the landmark catalog.`);
    }
  }
}
async function artifactsMatch(root, bindings, expected) {
  if (!sameKeys(bindings, expected)) throw new Error('Invalid tower artifact set.');
  const result = new Map();
  for (const path of expected) {
    const record = bindings[path];
    if (!sameKeys(record, ['bytes', 'sha256']) || !Number.isSafeInteger(record.bytes) || record.bytes < 1) {
      throw new Error(`Invalid tower artifact metadata: ${path}`);
    }
    const saved = await bytes(root, path);
    if (saved.length !== record.bytes || sha(saved) !== record.sha256) throw new Error(`Stale tower artifact: ${path}`);
    result.set(path, saved);
  }
  return result;
}
function checkDrawing(row, assets, revision) {
  if (!Array.isArray(row.dimensions_mm) || row.dimensions_mm.length < 1
      || row.dimensions_mm.some(value => !Number.isFinite(value) || value <= 0)
      || !Array.isArray(row.required_labels) || row.required_labels.length < 2
      || row.required_labels.some(value => typeof value !== 'string' || !value.trim())) {
    throw new Error(`Invalid tower drawing metadata: ${row.id}`);
  }
  const svg = assets.get(row.svg).toString('utf8');
  if (!svg.includes('<svg') || !/data-units=["']mm["']/.test(svg)
      || !svg.includes(`data-revision="${revision}"`) || /<(script|image|foreignObject)\b/i.test(svg)) {
    throw new Error(`Invalid tower SVG: ${row.svg}`);
  }
  const values = [...svg.matchAll(/<text\b[^>]*data-dimension-mm=["']([^"']+)["'][^>]*>([\s\S]*?)<\/text>/g)];
  const dimensions = values.map(match => Number(match[1])).sort((a, b) => a - b);
  const declared=[...row.dimensions_mm].sort((a,b)=>a-b);
  // DXF measurements keep floating precision; SVG serializes six decimals.
  const sameDimension=(a,b)=>Number.isFinite(a)&&Number.isFinite(b)&&Math.abs(a-b)<=1e-6;
  if (dimensions.length !== declared.length || dimensions.some((value,index)=>!sameDimension(value,declared[index]))
      || values.some(match => !sameDimension(Number(match[2].replace(/<[^>]+>/g, '').replace(/\s*mm\s*$/i, '').replaceAll(',', '').trim()), Number(match[1])))) {
    throw new Error(`Tower SVG visible dimensions differ: ${row.svg}`);
  }
  if (row.required_labels.some(label => !svg.includes(label))) throw new Error(`Missing tower drawing label: ${row.svg}`);
  const dxf = assets.get(row.dxf).toString('utf8');
  if (!dxf.includes('DIMENSION') || !dxf.includes('TEXT')) throw new Error(`Tower DXF is missing editable annotations: ${row.dxf}`);
}

export async function validateTowerArtifacts(root) {
  const models = [];
  for (const tower of towerCatalog) {
    const revision = tower.revision;
    const paths = towerPaths(tower.stem);
    const manifest = JSON.parse((await bytes(root, paths.metadata[0])).toString('utf8'));
    const drawings = JSON.parse((await bytes(root, paths.metadata[1])).toString('utf8'));
    for (const item of [manifest, drawings]) {
      if (item.schema_version !== 1 || item.revision !== revision || item.units !== 'mm'
          || item.status !== 'reference_concept_only') throw new Error(`Invalid landmark reference scope: ${tower.id}`);
    }
    if (manifest.id !== tower.id || manifest.height_mm !== tower.height
        || !Array.isArray(manifest.assumptions) || manifest.assumptions.length < 2
        || !Array.isArray(manifest.source_references) || !manifest.source_references.length) {
      throw new Error(`Invalid tower dimensions or reference provenance: ${tower.id}`);
    }
    await sourcesMatch(root, manifest.source_sha256, [...modelSources, ...tower.sources]);
    await sourcesMatch(root, drawings.source_sha256, [...drawingSources, ...tower.sources]);
    const savedModels = await artifactsMatch(root, manifest.artifacts, paths.models);
    const savedDrawings = await artifactsMatch(root, drawings.artifacts, paths.drawings);
    const views = tower.id === 'tokyo-tower' ? ['plan', 'elevation', 'steel-nodes'] : ['plan', 'elevation', 'structure-zones'];
    if (!Array.isArray(drawings.drawings) || drawings.drawings.length !== views.length
        || drawings.source_geometry_revision !== revision) throw new Error('Invalid tower drawing catalog.');
    if (tower.id === 'tokyo-tower') {
      const nodes=manifest.steel_nodes;
      if (!Array.isArray(nodes) || nodes.length !== 20 || new Set(nodes.map(n=>n.id)).size !== 20
          || nodes.some((node,index)=>node.id !== `TT-N${String(index+1).padStart(2,'0')}`
            || !['zh','ja','en'].every(locale=>typeof node.names?.[locale] === 'string' && node.names[locale].trim())
            || !Array.isArray(node.anchor_mm) || node.anchor_mm.length !== 3 || !node.anchor_mm.every(Number.isFinite)
            || !Array.isArray(node.part_names) || node.part_names.length < 1
            || new Set(node.part_names).size !== node.part_names.length
            || node.part_names.some(name=>typeof name !== 'string' || !name.startsWith('structure:')))) {
        throw new Error('Invalid Tokyo steel-node catalog.');
      }
    }
    for (const [index, id] of views.entries()) {
      const row = drawings.drawings.find(value => value.id === id);
      const detail = id === 'steel-nodes' || id === 'structure-zones';
      const dxf = detail ? paths.drawings[5] : paths.drawings[index];
      const svg = detail ? paths.drawings[6] : paths.drawings[index + 2];
      if (!row || row.dxf !== dxf || row.svg !== svg) throw new Error('Unexpected tower drawing path.');
      checkDrawing(row, savedDrawings, revision);
      if (id === 'plan' && (!Number.isFinite(manifest.parameters?.base_width_mm)
          || !row.dimensions_mm.includes(manifest.parameters.base_width_mm))) {
        throw new Error(`Plan dimensions differ from tower parameters: ${tower.id}`);
      }
      if (id === 'elevation' && [tower.height, ...tower.decks].some(level => !row.dimensions_mm.includes(level))) {
        throw new Error(`Missing required tower model levels: ${tower.id}`);
      }
      if (id === 'elevation' && tower.roofLevels && (
        JSON.stringify(drawings.roof_levels_mm) !== JSON.stringify(tower.roofLevels)
        || JSON.stringify(row.roof_levels_mm) !== JSON.stringify(tower.roofLevels)
        || tower.roofLevels.some(level => !row.dimensions_mm.includes(level)))) {
        throw new Error('Missing Skytree equipment-roof reference levels; roof heights must remain separate from observation floors.');
      }
      if (id === 'structure-zones' && [50000, 12500, 25000].some(value => !row.dimensions_mm.includes(value))) {
        throw new Error('Missing Skytree model structure-zone dimensions.');
      }
    }
    const step = savedModels.get(paths.models[0]);
    const glb = savedModels.get(paths.models[1]);
    if (!hasStepContainerMarkers(step)) throw new Error('Invalid tower STEP container.');
    if (glb.length < 20 || glb.toString('ascii', 0, 4) !== 'glTF'
        || glb.readUInt32LE(4) !== 2 || glb.readUInt32LE(8) !== glb.length) throw new Error('Invalid tower GLB container.');
    if (!savedDrawings.get(paths.drawings[4]).subarray(0, 5).equals(Buffer.from('%PDF-'))) throw new Error('Invalid tower PDF.');
    models.push({ manifest, drawings });
  }
  return { models, paths: towerArtifactPaths };
}
