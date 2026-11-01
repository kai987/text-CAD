import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const ids = ['tokyo-tower', 'tokyo-skytree'];
const locales = ['zh', 'ja', 'en'];
const fileTypes = [
  ['glb', 'glb', 'GLB'], ['step', 'step', 'STEP'], ['plan', 'plan_dxf', 'DXF'],
  ['elevation', 'elevation_dxf', 'DXF'], ['steelNodes', 'steel_nodes_dxf', 'DXF'],
  ['structureZones', 'structure_zones_dxf', 'DXF'], ['pdf', 'pdf', 'PDF'],
];
const references = {
  'tokyo-tower': {
    official: 'https://www.tokyotower.co.jp/guidance/',
    construction: 'https://www.miyaji-eng.co.jp/technology/newsletter/media/18/no18-p085-091.pdf',
  },
  'tokyo-skytree': { official: 'https://www.tokyo-skytree.jp/about/outline/' },
};
const positive = value => Number.isFinite(value) && value > 0;
function fail(id, message) { throw new Error(`Invalid landmark catalog ${id}: ${message}`); }
function levels(id, values, height, label) {
  if (!Array.isArray(values) || !values.length || values.some((value, index) =>
    !positive(value) || value >= height || index > 0 && value <= values[index - 1])) fail(id, label);
  return [...values];
}
function reference(manifest, url) {
  const value = manifest.source_references?.find(entry => entry.url === url)?.url;
  if (!value) fail(manifest.id, 'missing cited reference');
  return value;
}
function safeFile(id, path, expected) {
  // A generated download must address a local artifact, never an arbitrary URL.
  if (path !== expected) fail(id, `unexpected download path: ${path}`);
  return path;
}

/** Tiny, deliberately schematic loading shape; not a replacement elevation.
 * Coordinates come only from the manifest's retained profile/deck controls.
 * The active Tokyo upper-shaft fit is sampled from its declared parameters.
 */
export function landmarkLoadingPreview(manifest) {
  const p = manifest.parameters, id = manifest.id, height = manifest.height_mm;
  if (!ids.includes(id) || !/^LANDMARK-R\d{2,}$/.test(manifest.revision) || !positive(height)) {
    fail(id, 'loading preview identity');
  }
  const profile = p.profile;
  if (!Array.isArray(profile) || profile.length < 2 || profile.some((point, index) =>
    !Array.isArray(point) || point.length !== 2 || !Number.isFinite(point[0]) || point[0] < 0
    || point[0] > height || !positive(point[1]) || index > 0 && point[0] <= profile[index - 1][0])) {
    fail(id, 'loading preview profile controls');
  }
  const decks = p.deck_specs;
  if (!Array.isArray(decks) || decks.some(deck => !positive(deck.half_width_mm ?? deck.radius_mm)
    || !Number.isFinite(deck.bottom_mm) || !Number.isFinite(deck.top_mm)
    || deck.bottom_mm < 0 || deck.top_mm <= deck.bottom_mm || deck.top_mm > height)) {
    fail(id, 'loading preview deck controls');
  }
  if (!positive(p.antenna_start_mm) || p.antenna_start_mm > height) fail(id, 'loading preview antenna controls');
  const fit = p.detail?.upper_shaft_outline;
  const rows = profile.map(point => [...point]);
  if (fit?.enabled) {
    const { start_mm: start, end_mm: end, start_half_width_mm: r0, end_half_width_mm: r1,
      start_slope_mm_per_mm: m0, end_slope_mm_per_mm: m1 } = fit;
    const secant = (r1 - r0) / (end - start), power = (m1 - m0) / (secant - m0) - 1;
    if (![start, end, r0, r1, m0, m1, power].every(Number.isFinite)
      || !(0 <= start && start < end && end <= height && 0 < r1 && r1 < r0
        && m0 < secant && secant < m1 && m1 < 0 && power >= 1)
      || fit.method !== 'convex integrated power tangent blend') fail(id, 'loading preview upper-shaft controls');
    for (let i = 0; i <= 12; i++) rows.push([start + (end - start) * i / 12, 0]);
    for (const row of rows) if (row[0] >= start && row[0] <= end) {
      const t = (row[0] - start) / (end - start);
      row[1] = r0 + (end - start) * (m0 * t + (m1 - m0) * t ** (power + 1) / (power + 1));
    }
  }
  const points = [...new Map(rows.map(point => [point[0], point])).values()].sort((a, b) => a[0] - b[0]);
  const halfWidth = Math.max(...points.map(point => point[1]), ...decks.map(deck => deck.half_width_mm ?? deck.radius_mm));
  const controls = { id, revision: manifest.revision, height_mm: height, profile_kind: p.profile_kind,
    profile, deck_specs: decks, antenna_start_mm: p.antenna_start_mm, upper_shaft_outline: fit ?? null };
  const sourceSha256 = createHash('sha256').update(JSON.stringify(controls)).digest('hex');
  const number = value => String(Math.round(value * 1000) / 1000);
  const padding = height * .025, width = halfWidth * 2 + padding * 2;
  const polygon = [...points.map(([z, r]) => [-r, -z]), ...[...points].reverse().map(([z, r]) => [r, -z])]
    .map(point => point.map(number).join(',')).join(' ');
  const rectangles = decks.map(deck => {
    const radius = deck.half_width_mm ?? deck.radius_mm;
    return `<rect data-kind="deck-control" x="${number(-radius)}" y="${number(-deck.top_mm)}" width="${number(radius * 2)}" height="${number(deck.top_mm - deck.bottom_mm)}"/>`;
  }).join('');
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${number(-halfWidth - padding)} ${number(-height - padding)} ${number(width)} ${number(height + padding * 2)}" data-model-id="${id}" data-revision="${manifest.revision}" data-source-sha256="${sourceSha256}" data-units="mm" data-preview-scope="manifest-control-schematic"><g fill="#91a4b4" fill-opacity=".18" stroke="#68849a" stroke-width="${number(height * .0018)}" stroke-linejoin="round"><polygon points="${polygon}"/>${rectangles}<path fill="none" d="M0 ${number(-p.antenna_start_mm)} V${number(-height)}"/></g></svg>`;
  if (Buffer.byteLength(svg) >= 10_000) fail(id, 'loading preview exceeds 10 KB budget');
  return { svg, revision: manifest.revision, sourceSha256,
    sourceDigestScope: 'selected-manifest-controls-json-v1', scope: 'manifest-control-schematic',
    boundsMm: { minX: -halfWidth, minZ: 0, maxX: halfWidth, maxZ: height } };
}

/** Manifest-owned facts only. Editorial translations remain in stable keyed notes.
 * Callers publishing artifacts must still run validateTowerArtifacts: generating
 * this display catalog does not attest source, geometry or artifact integrity.
 */
export function buildLandmarkCatalog(manifests) {
  if (!Array.isArray(manifests) || manifests.length !== ids.length
      || new Set(manifests.map(item => item.id)).size !== ids.length
      || manifests.some(item => !ids.includes(item.id))) throw new Error('Invalid landmark catalog model set.');
  const models = {};
  for (const id of ids) {
    const manifest = manifests.find(item => item.id === id), p = manifest.parameters;
    const stem = id.replaceAll('-', '_');
    if (manifest.schema_version !== 1 || manifest.units !== 'mm' || manifest.status !== 'reference_concept_only'
        || p?.file_stem !== stem || manifest.revision !== p.revision
        || !/^LANDMARK-R\d{2,}$/.test(manifest.revision) || !positive(manifest.height_mm)
        || manifest.height_mm !== p.height_mm) fail(id, 'identity, revision or units');
    if (!locales.every(locale => typeof manifest.names?.[locale] === 'string' && manifest.names[locale].trim()
        && manifest.names[locale] === p.names?.[locale])) fail(id, 'missing or mismatched model name translation');
    const model = {
      stem, revision: manifest.revision, height: manifest.height_mm,
      levels: levels(id, p.deck_levels_mm, manifest.height_mm, 'model GL levels'),
      ...(p.nominal_deck_levels_mm ? {
        nominalLevels: levels(id, p.nominal_deck_levels_mm, manifest.height_mm, 'nominal visitor levels'),
      } : {}),
      names: Object.fromEntries(locales.map(locale => [locale, manifest.names[locale]])),
      reference: reference(manifest, references[id].official),
      ...(references[id].construction ? { constructionReference: reference(manifest, references[id].construction) } : {}),
      loadingPreview: landmarkLoadingPreview(manifest),
      downloads: [],
    };
    const expected = {
      glb: `GLB/${stem}.glb`, step: `STEP/${stem}.step`, plan_dxf: `DXF/${stem}_plan.dxf`,
      elevation_dxf: `DXF/${stem}_elevation.dxf`, pdf: `output/pdf/${stem}_sheets.pdf`,
      ...(id === 'tokyo-tower' ? { steel_nodes_dxf: `DXF/${stem}_steel_nodes.dxf` }
        : { structure_zones_dxf: `DXF/${stem}_structure_zones.dxf` }),
    };
    for (const [fileId, key, type] of fileTypes) {
      if (!Object.hasOwn(expected, key)) continue;
      model.downloads.push({ id: fileId, path: safeFile(id, manifest.files?.[key], expected[key]), type });
    }
    model.downloads.push({ id: 'manifest', path: `output/review/${stem}_manifest.json`, type: 'JSON' });
    models[id] = model;
  }
  // Distinct meanings must survive generation, including after a future edit.
  if (!models['tokyo-tower'].nominalLevels) fail('tokyo-tower', 'missing separate nominal visitor levels');
  return { schema_version: 1, units: 'mm', models };
}

export const catalogText = value => JSON.stringify(value, null, 2) + '\n';
export async function readLandmarkCatalog(root) {
  const manifests = await Promise.all(ids.map(id => readFile(resolve(root,
    `output/review/${id.replaceAll('-', '_')}_manifest.json`), 'utf8').then(JSON.parse)));
  return buildLandmarkCatalog(manifests);
}
export async function writeLandmarkCatalog(root, { check = false } = {}) {
  const path = resolve(root, 'web/src/landmark-catalog.json');
  const expected = catalogText(await readLandmarkCatalog(root));
  if (check) {
    if (await readFile(path, 'utf8') !== expected) throw new Error('Stale landmark display catalog. Run node web/scripts/landmark-catalog.mjs.');
  } else await writeFile(path, expected);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  if (args.some(value => value !== '--check')) throw new Error('Usage: node web/scripts/landmark-catalog.mjs [--check]');
  await writeLandmarkCatalog(fileURLToPath(new URL('../../', import.meta.url)), { check: args.includes('--check') });
  console.log(args.includes('--check') ? 'Landmark display catalog matches the source manifests.' : 'Generated landmark display catalog from source manifests.');
}
