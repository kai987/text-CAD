import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { buildLandmarkCatalog, catalogText, landmarkLoadingPreview, readLandmarkCatalog, writeLandmarkCatalog } from '../scripts/landmark-catalog.mjs';
import { landmarkModels, landmarkDownloadFiles, landmarkCopy } from '../src/landmark-copy.ts';

const root = fileURLToPath(new URL('../../', import.meta.url));
const manifests = await Promise.all(['tokyo_tower', 'tokyo_skytree'].map(stem =>
  readFile(resolve(root, `output/review/${stem}_manifest.json`), 'utf8').then(JSON.parse)));
const edited = action => { const rows = structuredClone(manifests); action(rows); return rows; };

test('generated landmark display catalog exactly follows the saved CAD manifests', async () => {
  const catalog = await readLandmarkCatalog(root);
  assert.equal(await readFile(resolve(root, 'web/src/landmark-catalog.json'), 'utf8'), catalogText(catalog));
  for (const manifest of manifests) {
    const model = landmarkModels[manifest.id];
    assert.equal(model.revision, manifest.revision);
    assert.equal(model.height, manifest.height_mm);
    assert.equal(model.stem, manifest.parameters.file_stem);
    assert.deepEqual(model.names, manifest.names);
    assert.deepEqual(model.levels, manifest.parameters.deck_levels_mm);
    for (const locale of ['zh', 'ja', 'en']) {
      assert.ok(model.assumptionNotes[locale]?.trim(), 'editorial notes retain all three languages');
      for (const file of landmarkDownloadFiles(manifest.id)) {
        assert.ok(landmarkCopy[locale].fileNames[file.id]?.trim());
        assert.ok(landmarkCopy[locale].fileDetails[file.id]?.trim());
      }
    }
  }
});

test('Tokyo R11 catalog follows the integrated lower-frame manifest independently of Skytree', () => {
  const tokyo = manifests.find(manifest => manifest.id === 'tokyo-tower');
  const skytree = manifests.find(manifest => manifest.id === 'tokyo-skytree');
  assert.equal(tokyo.revision, 'LANDMARK-R11');
  assert.equal(tokyo.parameters.detail.integrated_lower.enabled, true);
  assert.equal(tokyo.parameters.detail.lower_grid_continuity.enabled, true);
  assert.match(tokyo.source_sha256['src/lib/tokyo_tower_grid.py'], /^[a-f0-9]{64}$/);
  const model = buildLandmarkCatalog(manifests).models['tokyo-tower'];
  assert.equal(model.revision, tokyo.revision);
  assert.equal(model.loadingPreview.revision, tokyo.revision);
  assert.ok(model.loadingPreview.svg.includes('data-revision="LANDMARK-R11"'));
  assert.equal(skytree.revision, 'LANDMARK-R05');
});

test('model GL controls and official visitor levels remain separate when manifests change', () => {
  const rows = edited(rows => {
    rows[0].parameters.deck_levels_mm = [124000, 224000];
    rows[0].revision = rows[0].parameters.revision = 'LANDMARK-R99';
    rows[0].names.ja = rows[0].parameters.names.ja = '東京タワー（参照）';
  });
  const model = buildLandmarkCatalog(rows).models['tokyo-tower'];
  assert.equal(model.revision, 'LANDMARK-R99');
  assert.equal(model.names.ja, '東京タワー（参照）');
  assert.deepEqual(model.levels, [124000, 224000]);
  assert.deepEqual(model.nominalLevels, [150000, 250000]);
});

test('unknown, duplicate or incomplete model and language identities fail catalog generation', () => {
  assert.throws(() => buildLandmarkCatalog(manifests.slice(0, 1)), /model set/);
  assert.throws(() => buildLandmarkCatalog([manifests[0], manifests[0]]), /model set/);
  assert.throws(() => buildLandmarkCatalog(edited(rows => { rows[1].id = '__proto__'; })), /model set/);
  assert.throws(() => buildLandmarkCatalog(edited(rows => { delete rows[0].names.ja; })), /name translation/);
  assert.throws(() => buildLandmarkCatalog(edited(rows => { rows[0].parameters.names = { ...rows[0].parameters.names, ja: 'mismatch' }; })), /name translation/);
  assert.throws(() => buildLandmarkCatalog(edited(rows => { rows[1].parameters.revision = 'LANDMARK-R99'; })), /revision or units/);
  assert.throws(() => buildLandmarkCatalog(edited(rows => { rows[0].units = 'm'; })), /revision or units/);
});

test('download catalogs reject traversal, external URLs and missing model-specific drawings', () => {
  for (const path of ['../../secret.step', 'https://example.com/asset.step', 'STEP/tokyo_skytree.step']) {
    assert.throws(() => buildLandmarkCatalog(edited(rows => { rows[0].files.step = path; })), /download path/);
  }
  assert.throws(() => buildLandmarkCatalog(edited(rows => { delete rows[0].files.steel_nodes_dxf; })), /download path/);
  assert.throws(() => buildLandmarkCatalog(edited(rows => { delete rows[1].files.structure_zones_dxf; })), /download path/);
  const catalog = buildLandmarkCatalog(manifests);
  assert.equal(catalog.models['tokyo-tower'].downloads.find(file => file.id === 'steelNodes').path, manifests[0].files.steel_nodes_dxf);
  assert.equal(catalog.models['tokyo-skytree'].downloads.find(file => file.id === 'structureZones').path, manifests[1].files.structure_zones_dxf);
});

test('invalid height semantics and uncited display references are rejected', () => {
  for (const values of [[0, 223550], [223550, 125000], [125000, Infinity], [125000, 400000]]) {
    assert.throws(() => buildLandmarkCatalog(edited(rows => { rows[0].parameters.deck_levels_mm = values; })), /model GL levels/);
  }
  assert.throws(() => buildLandmarkCatalog(edited(rows => { delete rows[0].parameters.nominal_deck_levels_mm; })), /nominal visitor levels/);
  assert.throws(() => buildLandmarkCatalog(edited(rows => { rows[0].height_mm += 1; })), /identity, revision or units/);
  assert.throws(() => buildLandmarkCatalog(edited(rows => { rows[0].source_references = []; })), /missing cited reference/);
});

test('check mode detects stale metadata without rewriting it', async t => {
  const fixture = await mkdtemp(resolve(tmpdir(), 'landmark-catalog-'));
  t.after(() => rm(fixture, { recursive: true, force: true }));
  await mkdir(resolve(fixture, 'output/review'), { recursive: true });
  await mkdir(resolve(fixture, 'web/src'), { recursive: true });
  for (const manifest of manifests) await writeFile(resolve(fixture,
    `output/review/${manifest.parameters.file_stem}_manifest.json`), JSON.stringify(manifest));
  await writeLandmarkCatalog(fixture);
  await writeLandmarkCatalog(fixture, { check: true });
  const path = resolve(fixture, 'web/src/landmark-catalog.json');
  const stale = (await readFile(path, 'utf8')).replace('333000', '333001');
  await writeFile(path, stale);
  await assert.rejects(writeLandmarkCatalog(fixture, { check: true }), /Stale landmark display catalog/);
  assert.equal(await readFile(path, 'utf8'), stale);
  await writeLandmarkCatalog(fixture);
  await writeLandmarkCatalog(fixture, { check: true });
});

test('inline loading silhouettes stay under 10 KB with only bounded source geometry and safe SVG', () => {
  for (const manifest of manifests) {
    const preview = landmarkLoadingPreview(manifest), p = manifest.parameters;
    assert.ok(Buffer.byteLength(preview.svg) < 10_000);
    assert.equal(preview.scope, 'manifest-control-schematic');
    assert.equal(preview.revision, manifest.revision);
    assert.ok(preview.svg.includes(`data-model-id="${manifest.id}"`));
    assert.ok(preview.svg.includes(`data-revision="${manifest.revision}"`));
    assert.doesNotMatch(preview.svg, /<(script|image|foreignObject|text)\b|(?:href|style|onload)=/i);
    const maxRadius = Math.max(...p.profile.map(row => row[1]), ...p.deck_specs.map(row => row.radius_mm ?? row.half_width_mm));
    assert.deepEqual(preview.boundsMm, { minX: -maxRadius, minZ: 0, maxX: maxRadius, maxZ: manifest.height_mm });
    const [x, y, width, height] = preview.svg.match(/viewBox="([^"]+)"/)[1].split(' ').map(Number);
    assert.ok([x, y, width, height].every(Number.isFinite));
    assert.ok(x < preview.boundsMm.minX && x + width > preview.boundsMm.maxX);
    assert.ok(y < -preview.boundsMm.maxZ && y + height > 0);
    const points = preview.svg.match(/<polygon points="([^"]+)"/)[1].split(' ').map(point => point.split(',').map(Number));
    assert.ok(points.every(([px, py]) => px >= x && px <= x + width && py >= y && py <= y + height));
    assert.equal((preview.svg.match(/data-kind="deck-control"/g) ?? []).length, p.deck_specs.length);
    assert.ok(preview.svg.includes(`V${-manifest.height_mm}`), 'antenna centerline ends at the saved tip control');
  }
});

test('preview source digest binds its exact manifest controls and revision', () => {
  for (const manifest of manifests) {
    const p = manifest.parameters;
    const controls = { id: manifest.id, revision: manifest.revision, height_mm: manifest.height_mm,
      profile_kind: p.profile_kind, profile: p.profile, deck_specs: p.deck_specs,
      antenna_start_mm: p.antenna_start_mm, upper_shaft_outline: p.detail?.upper_shaft_outline ?? null };
    const preview = landmarkLoadingPreview(manifest);
    const expected = createHash('sha256').update(JSON.stringify(controls)).digest('hex');
    assert.equal(preview.sourceDigestScope, 'selected-manifest-controls-json-v1');
    assert.equal(preview.sourceSha256, expected);
    assert.ok(preview.svg.includes(`data-source-sha256="${expected}"`));
    const next = structuredClone(manifest);
    next.parameters.profile[1][1] += 100;
    assert.notEqual(landmarkLoadingPreview(next).sourceSha256, expected);
    assert.notEqual(landmarkLoadingPreview(next).svg, preview.svg);
    const revision = structuredClone(manifest); revision.revision = 'LANDMARK-R99';
    assert.notEqual(landmarkLoadingPreview(revision).sourceSha256, expected);
    assert.equal(landmarkLoadingPreview(revision).revision, 'LANDMARK-R99');
  }
});

test('Tokyo loading silhouette follows the active R07 shaft fit rather than its retained legacy guide', () => {
  const preview = landmarkLoadingPreview(manifests[0]);
  const points = preview.svg.match(/<polygon points="([^"]+)"/)[1].split(' ').map(point => point.split(',').map(Number));
  // Cross-checked against Python body_radius for the saved R07 controls.
  for (const [z, r] of [[150000, 8534.551769806661], [170000, 7172.489329513928],
    [190000, 5838.6191592082905], [210000, 4617.86205229427]]) {
    const point = points.find(([x, y]) => x < 0 && y === -z);
    assert.ok(point && Math.abs(point[0] + r) < .001);
  }
});

test('malformed preview coordinates, unsupported fits and unsafe identities fail instead of producing SVG', () => {
  const cases = [
    row => { row.parameters.profile[1][0] = row.parameters.profile[0][0]; },
    row => { row.parameters.profile[1][1] = NaN; },
    row => { row.parameters.deck_specs[0].top_mm = row.height_mm + 1; },
    row => { row.parameters.antenna_start_mm = row.height_mm + 1; },
    row => { row.parameters.detail.upper_shaft_outline.method = 'invented'; },
    row => { row.id = '" onload="alert(1)'; },
    row => { row.revision = '" onload="alert(1)'; },
  ];
  for (const edit of cases) {
    const manifest = structuredClone(manifests[0]); edit(manifest);
    assert.throws(() => landmarkLoadingPreview(manifest), /loading preview/);
  }
});
