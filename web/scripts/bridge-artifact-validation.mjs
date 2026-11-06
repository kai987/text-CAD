import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
import { hasStepContainerMarkers } from './tower-artifact-validation.mjs';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const revision = 'BRIDGE-R05';
export const bridgeGeometrySources = ['src/lib/seto_bridge_geometry.py', 'src/lib/seto_bridge_activity.py', 'src/seto_bridge_3d.py', 'src/lib/step_transport.py'];
export const bridgeDrawingSources = ['src/lib/seto_bridge_geometry.py', 'src/lib/seto_bridge_activity.py', 'src/generate_seto_bridge_plans.py'];
const models = ['STEP/seto_ohashi.step', 'GLB/seto_ohashi.glb'];
const views = ['plan', 'elevation', 'section'];
const drawingPaths = [...views.map(id => `DXF/seto_ohashi_${id}.dxf`),
  ...views.map(id => `output/svg/seto_ohashi_${id}.svg`), 'output/pdf/seto_ohashi_sheets.pdf'];
const metadata = ['output/review/seto_ohashi_manifest.json', 'output/review/seto_ohashi_drawings.json'];
export const bridgeArtifactPaths = [...models, ...drawingPaths, ...metadata];
const exactKeys = (value, keys) => value && typeof value === 'object' && !Array.isArray(value)
  && JSON.stringify(Object.keys(value).sort()) === JSON.stringify([...keys].sort());
const nonempty = value => typeof value === 'string' && value.trim().length > 0;
const assumption = value => nonempty(value)
  || (exactKeys(value, ['zh', 'ja', 'en']) && Object.values(value).every(nonempty));

async function read(root, path) {
  try { return await readFile(resolve(root, path)); }
  catch (cause) { throw new Error(`Missing Seto Ohashi asset or source: ${path}`, { cause }); }
}

async function sourcesMatch(root, bindings, expected) {
  if (!exactKeys(bindings, expected)) throw new Error('Invalid Seto Ohashi source catalog.');
  for (const path of expected) {
    if (sha(await read(root, path)) !== bindings[path]) throw new Error(`Stale Seto Ohashi source: ${path}`);
  }
}

async function artifactsMatch(root, bindings, expected) {
  if (!exactKeys(bindings, expected)) throw new Error('Invalid Seto Ohashi artifact catalog.');
  const result = new Map();
  for (const path of expected) {
    const entry = bindings[path], bytes = await read(root, path);
    if (!exactKeys(entry, ['bytes', 'sha256']) || !Number.isSafeInteger(entry.bytes)
        || entry.bytes < 1 || entry.bytes !== bytes.length || entry.sha256 !== sha(bytes)) {
      throw new Error(`Stale Seto Ohashi artifact: ${path}`);
    }
    result.set(path, bytes);
  }
  return result;
}

/** Guard the demonstrative scene animation contract without executing CAD. */
export function validateBridgeActivity(manifest) {
  const activity = manifest.activity, p = manifest.parameters;
  if (!p || !['road_deck_z_mm', 'rail_deck_z_mm', 'shared_anchor_half_length_mm',
    'north_outer_end_mm', 'south_outer_end_mm', 'context_width_mm', 'sea_z_mm'].every(key => Number.isFinite(p[key]))
      || activity?.schema_version !== 2 || activity.snapshot_time_s !== 0
      || activity.road_crest_z_mm !== p.road_deck_z_mm || activity.road_grade !== .01
      || activity.rail_crest_z_mm !== p.rail_deck_z_mm + 420
      || activity.shared_anchor_half_length_mm !== p.shared_anchor_half_length_mm
      || !Array.isArray(activity.actors) || activity.actors.length !== 36
      || !Array.isArray(manifest.components)) throw new Error('Invalid Seto Ohashi activity contract.');
  const components = new Map(manifest.components.map(part => [part.name, part]));
  if (components.size !== manifest.components.length) throw new Error('Duplicate Seto Ohashi components.');
  const ids = new Set(), assigned = new Set(), consists = new Map(), boatRoutes = new Set();
  const rail = x => p.rail_deck_z_mm + 420 - .01 * Math.max(Math.abs(x), p.shared_anchor_half_length_mm);
  const close = (a, b, tolerance = .01) => Math.abs(a - b) <= tolerance;
  for (const actor of activity.actors) {
    const route = actor.route, car = actor.group === 'traffic', boat = actor.group === 'vessels';
    const heading = boat ? actor.direction * Math.PI / 2 : actor.direction === 1 ? 0 : Math.PI;
    if (!['traffic', 'vessels', 'trains'].includes(actor.group) || typeof actor.id !== 'string'
        || !/^[A-Za-z0-9_]{1,64}$/.test(actor.id) || ids.has(actor.id)
        || ![1, -1].includes(actor.direction) || !Number.isFinite(actor.speed_mps)
        || actor.speed_mps <= 0 || actor.speed_mps > (car ? 35 : boat ? 15 : 60)
        || !Number.isFinite(actor.phase) || actor.phase < 0 || actor.phase >= 1
        || !Array.isArray(actor.origin_mm) || actor.origin_mm.length !== 3 || !actor.origin_mm.every(Number.isFinite)
        || !['length_mm', 'width_mm', 'height_mm'].every(key => Number.isFinite(actor[key]) && actor[key] > 0)
        || !Number.isFinite(actor.heading_rad) || !close(actor.heading_rad, heading, 1e-9)
        || !exactKeys(route, ['axis', 'min_mm', 'max_mm', 'fixed_mm']) || route.axis !== (boat ? 'y' : 'x')
        || ![route.min_mm, route.max_mm, route.fixed_mm].every(Number.isFinite)
        || route.min_mm >= route.max_mm
        || actor.origin_mm[boat ? 0 : 1] !== route.fixed_mm
        || !Array.isArray(actor.part_names) || actor.part_names.length < 5
        || new Set(actor.part_names).size !== actor.part_names.length) {
      throw new Error('Invalid Seto Ohashi actor or route.');
    }
    ids.add(actor.id);
    if (car || boat) {
      const along = actor.origin_mm[boat ? 1 : 0];
      if (along < route.min_mm || along >= route.max_mm
          || !close(along, route.min_mm + actor.phase * (route.max_mm - route.min_mm))) {
        throw new Error('Invalid Seto Ohashi actor initial route phase.');
      }
    }
    if (car) {
      const z = p.road_deck_z_mm - .01 * Math.max(Math.abs(actor.origin_mm[0]), p.shared_anchor_half_length_mm);
      if (![3500, 8500].includes(Math.abs(route.fixed_mm)) || Math.sign(route.fixed_mm) !== actor.direction
          || route.min_mm - actor.length_mm / 2 < p.north_outer_end_mm
          || route.max_mm + actor.length_mm / 2 > p.south_outer_end_mm
          || !close(actor.origin_mm[2], z)) throw new Error('Seto Ohashi traffic must follow left-hand lanes and the deck profile.');
    } else if (boat) {
      if (![-825000, -765000, 820000, 880000].includes(route.fixed_mm) || boatRoutes.has(route.fixed_mm)
          || route.min_mm >= -15000 || route.max_mm <= 15000
          || route.min_mm - actor.length_mm / 2 < -p.context_width_mm / 2
          || route.max_mm + actor.length_mm / 2 > p.context_width_mm / 2
          || !close(actor.origin_mm[2], p.sea_z_mm)) {
        throw new Error('Seto Ohashi vessels must cross beneath the main spans in the illustrative open-water corridors.');
      }
      boatRoutes.add(route.fixed_mm);
    } else {
      const index = actor.carriage_index, offset = actor.consist_offset_mm;
      const half = actor.bogie_spacing_mm / 2, x = actor.origin_mm[0];
      if (typeof actor.train_id !== 'string' || !/^emu_[12]$/.test(actor.train_id)
          || !Number.isInteger(index) || index < 0 || index > 3 || offset !== -20500 * index
          || actor.bogie_spacing_mm !== 13800 || actor.length_mm !== 20000
          || actor.width_mm !== 2850 || actor.height_mm !== 5300
          || route.fixed_mm !== (actor.direction === 1 ? -5500 : -10500)
          || !Number.isFinite(actor.lead_position_mm)
          || actor.lead_position_mm < route.min_mm || actor.lead_position_mm >= route.max_mm
          || !close(actor.lead_position_mm, route.min_mm + actor.phase * (route.max_mm - route.min_mm))
          || !close(x, actor.lead_position_mm + actor.direction * offset)
          || route.min_mm - (actor.direction === 1 ? 61500 : 0) - actor.length_mm / 2 < p.north_outer_end_mm
          || route.max_mm + (actor.direction === -1 ? 61500 : 0) + actor.length_mm / 2 > p.south_outer_end_mm
          || !close(actor.origin_mm[2], (rail(x - half) + rail(x + half)) / 2)
          || !Number.isFinite(actor.pitch_rad)
          || !close(actor.pitch_rad, -Math.atan(actor.direction * (rail(x + half) - rail(x - half)) / actor.bogie_spacing_mm), 1e-9)) {
        throw new Error('Seto Ohashi electric trains must form complete consists on the railway profile.');
      }
      const consist = consists.get(actor.train_id) ?? [];
      consist.push(actor); consists.set(actor.train_id, consist);
    }
    for (const name of actor.part_names) {
      const part = components.get(name);
      if (typeof name !== 'string' || !name.startsWith(`${actor.group}:${actor.id}:`) || assigned.has(name)
          || !part || part.group !== actor.group || part.actor_id !== actor.id) throw new Error('Invalid Seto Ohashi actor component binding.');
      assigned.add(name);
    }
  }
  if (consists.size !== 2) throw new Error('Incomplete Seto Ohashi train catalog.');
  const directions = new Set();
  for (const consist of consists.values()) {
    const first = consist[0]; directions.add(first.direction);
    if (consist.length !== 4 || new Set(consist.map(actor => actor.carriage_index)).size !== 4
        || consist.some(actor => ['direction', 'speed_mps', 'phase', 'lead_position_mm'].some(key => actor[key] !== first[key])
          || ['axis', 'min_mm', 'max_mm', 'fixed_mm'].some(key => actor.route[key] !== first.route[key]))) {
      throw new Error('Seto Ohashi electric train consist clocks and routes must agree.');
    }
  }
  if (activity.actors.filter(actor => actor.group === 'traffic').length !== 24
      || activity.actors.filter(actor => actor.group === 'vessels').length !== 4
      || activity.actors.filter(actor => actor.group === 'trains').length !== 8 || directions.size !== 2
      || manifest.components.some(part => ['traffic', 'vessels', 'trains'].includes(part.group) && !assigned.has(part.name))) {
    throw new Error('Incomplete Seto Ohashi traffic, vessel and train catalog.');
  }
}

export async function validateBridgeArtifacts(root) {
  const manifest = JSON.parse(await read(root, metadata[0]));
  const drawings = JSON.parse(await read(root, metadata[1]));
  for (const record of [manifest, drawings]) {
    if (record.schema_version !== 1 || record.revision !== revision || record.units !== 'mm'
        || record.status !== 'reference_concept_only') throw new Error('Invalid Seto Ohashi reference scope.');
  }
  if (manifest.id !== 'seto-ohashi' || !Array.isArray(manifest.assumptions) || manifest.assumptions.length < 3
      || manifest.assumptions.some(value => !assumption(value))) {
    throw new Error('Seto Ohashi must identify the model and its assumptions.');
  }
  validateBridgeActivity(manifest);
  await sourcesMatch(root, manifest.source_sha256, bridgeGeometrySources);
  await sourcesMatch(root, drawings.source_sha256, bridgeDrawingSources);
  const savedModels = await artifactsMatch(root, manifest.artifacts, models);
  const savedDrawings = await artifactsMatch(root, drawings.artifacts, drawingPaths);
  if (drawings.source_geometry_revision !== revision || !Array.isArray(drawings.drawings)
      || drawings.drawings.length !== views.length || new Set(drawings.drawings.map(row => row.id)).size !== views.length) {
    throw new Error('Invalid Seto Ohashi drawing list or mixed revision.');
  }
  for (const id of views) {
    const row = drawings.drawings.find(value => value.id === id);
    if (!row || row.dxf !== `DXF/seto_ohashi_${id}.dxf` || row.svg !== `output/svg/seto_ohashi_${id}.svg`
        || !Array.isArray(row.dimensions_mm) || !row.dimensions_mm.length
        || row.dimensions_mm.some(value => !Number.isFinite(value) || value <= 0)
        || !Array.isArray(row.required_labels) || row.required_labels.length < 2
        || row.required_labels.some(value => typeof value !== 'string' || !value.trim())) {
      throw new Error(`Invalid Seto Ohashi drawing metadata: ${id}`);
    }
    const svg = savedDrawings.get(row.svg).toString('utf8');
    if (!svg.includes('<svg') || !svg.includes('data-units="mm"') || !svg.includes(`data-revision="${revision}"`)
        || /<(?:script|image|foreignObject)\b/i.test(svg)) throw new Error(`Invalid Seto Ohashi SVG: ${id}`);
    const texts = [...svg.matchAll(/<text\b[^>]*data-dimension-mm=["']([^"']+)["'][^>]*>([\s\S]*?)<\/text>/g)];
    const values = texts.map(match => Number(match[1])).sort((a, b) => a - b);
    const expected = [...row.dimensions_mm].sort((a, b) => a - b);
    if (JSON.stringify(values) !== JSON.stringify(expected) || texts.some(match =>
      Number(match[2].replace(/<[^>]+>/g, '').replace(/\s*mm\s*$/i, '').replaceAll(',', '').trim()) !== Number(match[1]))) {
      throw new Error(`Seto Ohashi SVG visible dimensions differ: ${id}`);
    }
    if (row.required_labels.some(label => !svg.includes(label))) throw new Error(`Missing Seto Ohashi SVG label: ${id}`);
    const dxf = savedDrawings.get(row.dxf).toString('utf8');
    if (!dxf.includes('DIMENSION') || !dxf.includes('TEXT')) throw new Error(`Seto Ohashi DXF annotations are not editable: ${id}`);
  }
  const elevation = drawings.drawings.find(row => row.id === 'elevation');
  if ([1538000, 1648000, 990000, 1100000].some(value => !elevation.dimensions_mm.includes(value))) {
    throw new Error('Seto Ohashi elevation must retain official bridge and central span lengths.');
  }
  if ([184000,194000,35000].some(value=>!elevation.dimensions_mm.includes(value))
      || !elevation.required_labels.includes('主塔正面図')) {
    throw new Error('Seto Ohashi elevation must retain the annotated tower front projections.');
  }
  const section = drawings.drawings.find(row => row.id === 'section');
  if ([79000, 53000, 86000].some(value => !section.dimensions_mm.includes(value))
      || !section.required_labels.includes('BB4A外形')) {
    throw new Error('Seto Ohashi cross-section must retain the annotated BB4A external profile.');
  }
  if (!hasStepContainerMarkers(savedModels.get(models[0]))) throw new Error('Invalid Seto Ohashi STEP container.');
  const glb = savedModels.get(models[1]);
  if (glb.length < 20 || glb.toString('ascii', 0, 4) !== 'glTF' || glb.readUInt32LE(4) !== 2
      || glb.readUInt32LE(8) !== glb.length) throw new Error('Invalid Seto Ohashi GLB container.');
  if (!savedDrawings.get(drawingPaths.at(-1)).subarray(0, 5).equals(Buffer.from('%PDF-'))) {
    throw new Error('Invalid Seto Ohashi PDF.');
  }
  return { manifest, drawings, paths: bridgeArtifactPaths };
}
