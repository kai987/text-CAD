import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const revision = 'RIVER-R01';
const geometrySources = ['src/lib/river_geometry.py', 'src/river_3d.py'];
const drawingSources = ['src/lib/river_geometry.py', 'src/generate_river_plans.py'];
const modelPaths = ['STEP/river_demo.step', 'GLB/river_demo.glb'];
const drawingPaths = ['DXF/river_demo_plan.dxf', 'DXF/river_demo_section.dxf',
  'output/svg/river_demo_plan.svg', 'output/svg/river_demo_section.svg'];
export const riverArtifactPaths = [...modelPaths, ...drawingPaths,
  'output/review/river_demo_manifest.json', 'output/review/river_demo_drawings.json'];

const sameKeys = (value, keys) => value && typeof value === 'object' && !Array.isArray(value)
  && JSON.stringify(Object.keys(value).sort()) === JSON.stringify([...keys].sort());
const numbers = values => Array.isArray(values) && values.length > 0
  && values.every(value => typeof value === 'number' && Number.isFinite(value) && value > 0);

async function read(root, path) {
  try { return await readFile(resolve(root, path)); }
  catch (error) { throw new Error(`Missing river asset or source: ${path}`, { cause: error }); }
}

async function checkSources(root, bindings, paths) {
  if (!sameKeys(bindings, paths)) throw new Error('Invalid river source set.');
  for (const path of paths) {
    if (!/^[a-f0-9]{64}$/.test(bindings[path] ?? '') || sha(await read(root, path)) !== bindings[path]) {
      throw new Error(`Stale river source binding: ${path}; regenerate river CAD.`);
    }
  }
}

async function checkArtifacts(root, bindings, paths) {
  if (!sameKeys(bindings, paths)) throw new Error('Invalid river artifact set.');
  const assets = new Map();
  for (const path of paths) {
    const entry = bindings[path];
    if (!sameKeys(entry, ['sha256', 'bytes']) || !Number.isSafeInteger(entry.bytes) || entry.bytes < 1
        || !/^[a-f0-9]{64}$/.test(entry.sha256 ?? '')) {
      throw new Error(`Invalid river artifact metadata: ${path}`);
    }
    const bytes = await read(root, path);
    if (entry.bytes !== bytes.length || entry.sha256 !== sha(bytes)) throw new Error(`Stale river artifact: ${path}; regenerate river CAD.`);
    assets.set(path, bytes);
  }
  return assets;
}

function checkSvg(bytes, row) {
  const svg = bytes.toString('utf8');
  if (!svg.includes('<svg') || /<(?:script|image|foreignObject)\b/i.test(svg)
      || !/data-units=["']mm["']/.test(svg) || !/data-revision=["']RIVER-R01["']/.test(svg)) {
    throw new Error(`Invalid river SVG profile: ${row.svg}`);
  }
  const dimensions = [...svg.matchAll(/data-dimension-mm=["']([^"']+)["']/g)].map(match => Number(match[1]));
  if (!numbers(dimensions) || JSON.stringify(dimensions.sort((a, b) => a - b))
      !== JSON.stringify([...row.dimensions_mm].sort((a, b) => a - b))) {
    throw new Error(`River SVG dimensions differ from drawing metadata: ${row.svg}`);
  }
  const visibleDimensions = [...svg.matchAll(/<text\b[^>]*data-dimension-mm=["']([^"']+)["'][^>]*>([\s\S]*?)<\/text>/g)];
  if (visibleDimensions.length !== dimensions.length || visibleDimensions.some(match => {
    const visible = match[2].replace(/<[^>]+>/g, '').trim().replace(/\s*mm\s*$/i, '').replaceAll(',', '');
    return visible.length === 0 || Number(visible) !== Number(match[1]);
  })) throw new Error(`River SVG visible dimension text is inconsistent: ${row.svg}`);
  if (row.required_labels.some(label => !svg.includes(label))) throw new Error(`Missing river SVG label: ${row.svg}`);
}

export async function validateRiverArtifacts(root) {
  const manifest = JSON.parse((await read(root, riverArtifactPaths[6])).toString('utf8'));
  const drawings = JSON.parse((await read(root, riverArtifactPaths[7])).toString('utf8'));
  if (manifest.schema_version !== 1 || manifest.revision !== revision || manifest.units !== 'mm'
      || manifest.status !== 'concept_demo_only') throw new Error('Invalid river concept manifest.');
  if (!sameKeys(manifest.engineering, ['hydraulic_capacity', 'bridge_strength', 'foundation_capacity', 'statutory_compliance'])
      || Object.values(manifest.engineering).some(value => value !== null)
      || !Array.isArray(manifest.assumptions) || manifest.assumptions.length < 4
      || manifest.assumptions.some(value => typeof value !== 'string' || value.trim().length === 0)
      || manifest.bridge?.structural_calculation !== null) {
    throw new Error('River demonstration must retain assumptions and uncalculated engineering results.');
  }
  if (drawings.schema_version !== 1 || drawings.revision !== revision || drawings.units !== 'mm'
      || drawings.status !== 'concept_demo_only' || drawings.source_geometry_revision !== revision) {
    throw new Error('Invalid river drawing metadata or mixed revision.');
  }
  await checkSources(root, manifest.source_sha256, geometrySources);
  await checkSources(root, drawings.source_sha256, drawingSources);
  const models = await checkArtifacts(root, manifest.artifacts, modelPaths);
  const savedDrawings = await checkArtifacts(root, drawings.artifacts, drawingPaths);
  const p = manifest.parameters;
  const expected = [
    { id: 'plan', dxf: drawingPaths[0], svg: drawingPaths[2], dimensions_mm:
      [p?.length, p?.width, p?.water_width, manifest.bridge?.span, p?.bridge_width, p?.path_width] },
    { id: 'section', dxf: drawingPaths[1], svg: drawingPaths[3], dimensions_mm:
      [p?.width, p?.water_width, manifest.bridge?.span, p?.crest_z - p?.water_z, p?.water_z - p?.bed_z] },
  ];
  if (!Array.isArray(drawings.drawings) || drawings.drawings.length !== 2
      || new Set(drawings.drawings.map(row => row.id)).size !== 2) throw new Error('Invalid river drawing list.');
  for (const expectedRow of expected) {
    const row = drawings.drawings.find(row => row.id === expectedRow.id);
    if (!row || row.dxf !== expectedRow.dxf || row.svg !== expectedRow.svg
        || !numbers(expectedRow.dimensions_mm) || !numbers(row.dimensions_mm)
        || JSON.stringify(row.dimensions_mm) !== JSON.stringify(expectedRow.dimensions_mm)
        || !Array.isArray(row.required_labels) || row.required_labels.length < 4
        || row.required_labels.some(label => typeof label !== 'string' || label.trim().length === 0)) {
      throw new Error(`Invalid river drawing dimensions or labels: ${expectedRow.id}`);
    }
    checkSvg(savedDrawings.get(row.svg), row);
    if (!savedDrawings.get(row.dxf).toString('utf8').includes('DIMENSION')) {
      throw new Error(`River DXF has no editable dimensions: ${row.dxf}`);
    }
  }
  const step = models.get(modelPaths[0]).toString('utf8');
  if (!step.startsWith('ISO-10303-21;') || !step.includes('END-ISO-10303-21;')) throw new Error('Invalid river STEP container.');
  const glb = models.get(modelPaths[1]);
  if (glb.length < 20 || glb.toString('ascii', 0, 4) !== 'glTF'
      || glb.readUInt32LE(4) !== 2 || glb.readUInt32LE(8) !== glb.length) throw new Error('Invalid river GLB container.');
  return { manifest, drawings, paths: riverArtifactPaths };
}
