import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtemp, mkdir, writeFile, readFile, rm } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { validateBridgeArtifacts, bridgeGeometrySources, bridgeDrawingSources,
  bridgeArtifactPaths, validateBridgeActivity } from '../scripts/bridge-artifact-validation.mjs';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
function activityFixture() {
  const parameters = { road_deck_z_mm: 93000, rail_deck_z_mm: 80000, shared_anchor_half_length_mm: 24500,
    north_outer_end_mm: -1610700, south_outer_end_mm: 1723100, context_width_mm: 760000, sea_z_mm: 0 };
  const actors = [], components = [];
  const add = actor => {
    actor.part_names = ['body', 'cabin', 'detail_1', 'detail_2', 'detail_3', 'detail_4'].map(piece => `${actor.group}:${actor.id}:${piece}`);
    components.push(...actor.part_names.map(name => ({ name, group: actor.group, actor_id: actor.id })));
    actors.push(actor);
  };
  for (let index = 0; index < 28; index++) {
    const car = index < 24, local = car ? index : index - 24, group = car ? 'traffic' : 'vessels';
    const id = `${car ? 'car' : 'boat'}_${String(local + 1).padStart(2, '0')}`;
    const fixed = car ? [3500, 8500, -3500, -8500][local % 4] : [-825000, -765000, 820000, 880000][local];
    const direction = car ? Math.sign(fixed) : local % 2 ? -1 : 1, phase = car ? (Math.floor(local / 4) + .5) / 6 : .1 + .2 * local;
    const route = { axis: car ? 'x' : 'y', min_mm: car ? -1590000 : -300000, max_mm: car ? 1700000 : 300000, fixed_mm: fixed };
    const along = route.min_mm + phase * (route.max_mm - route.min_mm);
    const origin_mm = car ? [along, fixed, 93000 - .01 * Math.max(Math.abs(along), 24500)] : [fixed, along, 0];
    add({ id, group, kind: car ? 'sedan' : 'cruise', direction, phase, route,
      length_mm: car ? 4500 : 24000, width_mm: car ? 1820 : 6400, height_mm: car ? 1560 : 6400,
      speed_mps: car ? 22 : 7, heading_rad: car ? direction === 1 ? 0 : Math.PI : direction * Math.PI / 2, origin_mm });
  }
  for (let train = 1; train <= 2; train++) {
    const direction = train === 1 ? 1 : -1, phase = train === 1 ? .4 : .62;
    const route = { axis: 'x', min_mm: -1510700, max_mm: 1623100, fixed_mm: direction === 1 ? -5500 : -10500 };
    const lead_position_mm = route.min_mm + phase * (route.max_mm - route.min_mm);
    for (let carriage_index = 0; carriage_index < 4; carriage_index++) {
      const consist_offset_mm = -20500 * carriage_index;
      const x = lead_position_mm + direction * consist_offset_mm;
      const rail = at => 80420 - .01 * Math.max(Math.abs(at), 24500);
      add({ id: `emu_${train}_car_${carriage_index + 1}`, train_id: `emu_${train}`, group: 'trains',
        kind: 'electric_carriage', direction, phase, route: { ...route }, speed_mps: 25, carriage_index,
        consist_offset_mm, lead_position_mm, bogie_spacing_mm: 13800,
        length_mm: 20000, width_mm: 2850, height_mm: 5300,
        heading_rad: direction === 1 ? 0 : Math.PI,
        pitch_rad: -Math.atan(direction * (rail(x + 6900) - rail(x - 6900)) / 13800),
        origin_mm: [x, route.fixed_mm, (rail(x - 6900) + rail(x + 6900)) / 2] });
    }
  }
  return { parameters, components, activity: { schema_version: 2, snapshot_time_s: 0,
    road_crest_z_mm: 93000, rail_crest_z_mm: 80420, road_grade: .01, shared_anchor_half_length_mm: 24500, actors } };
}
async function fixture(t) {
  const root = await mkdtemp(resolve(tmpdir(), 'seto-publication-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const save = async (path, bytes) => {
    await mkdir(dirname(resolve(root, path)), { recursive: true });
    await writeFile(resolve(root, path), bytes);
  };
  // Minimal containers test publication integrity, not CAD solid validity.
  // Saved solids, mesh positions and editable dimensions have Python checks.
  const source = '# independent source binding fixture\n';
  for (const path of new Set([...bridgeGeometrySources, ...bridgeDrawingSources])) await save(path, source);
  await save('STEP/seto_ohashi.step', 'ISO-10303-21;\nEND-ISO-10303-21;');
  const glb = Buffer.alloc(20); glb.write('glTF'); glb.writeUInt32LE(2, 4); glb.writeUInt32LE(20, 8);
  await save('GLB/seto_ohashi.glb', glb);
  const base = { schema_version: 1, id: 'seto-ohashi', revision: 'BRIDGE-R05', units: 'mm', status: 'reference_concept_only' };
  const manifest = { ...base, ...activityFixture(), assumptions: ['Photo-fitted members.', 'Schematic terrain.', 'No structural analysis.'],
    source_sha256: Object.fromEntries(bridgeGeometrySources.map(path => [path, sha(source)])), artifacts: {} };
  const drawings = { ...base, source_geometry_revision: 'BRIDGE-R05',
    source_sha256: Object.fromEntries(bridgeDrawingSources.map(path => [path, sha(source)])),
    artifacts: {}, drawings: ['plan', 'elevation', 'section'].map(id => ({ id,
      dxf: `DXF/seto_ohashi_${id}.dxf`, svg: `output/svg/seto_ohashi_${id}.svg`,
      dimensions_mm: id === 'elevation' ? [1538000, 1648000, 990000, 1100000, 3333800, 184000, 194000, 35000, 35000] : id === 'section' ? [30000, 13000, 79000, 53000, 86000] : [30000, 13000],
      required_labels: id === 'elevation' ? ['瀬戸大橋', '参考モデル', '主塔正面図'] : id === 'section' ? ['瀬戸大橋', '参考モデル', 'BB4A外形'] : ['瀬戸大橋', '参考モデル'] })) };
  for (const row of drawings.drawings) {
    await save(row.dxf, '0\nTEXT\n0\nDIMENSION\n');
    await save(row.svg, `<svg data-units="mm" data-revision="BRIDGE-R05">${row.dimensions_mm.map(value =>
      `<text data-dimension-mm="${value}">${value}</text>`).join('')}${row.required_labels.join(' ')}</svg>`);
  }
  await save('output/pdf/seto_ohashi_sheets.pdf', '%PDF-1.4\nfixture');
  const bind = async (record, paths) => {
    for (const path of paths) {
      const bytes = await readFile(resolve(root, path)); record.artifacts[path] = { bytes: bytes.length, sha256: sha(bytes) };
    }
  };
  await bind(manifest, bridgeArtifactPaths.slice(0, 2));
  await bind(drawings, bridgeArtifactPaths.slice(2, -2));
  const saveMetadata = async () => {
    await save(bridgeArtifactPaths.at(-2), JSON.stringify(manifest));
    await save(bridgeArtifactPaths.at(-1), JSON.stringify(drawings));
  };
  await saveMetadata();
  return { root, save, bind, manifest, drawings, saveMetadata };
}

test('Seto Ohashi native and editable drawing publication verifies without executing Python', async t => {
  const f = await fixture(t);
  assert.deepEqual((await validateBridgeArtifacts(f.root)).paths, bridgeArtifactPaths);
});

test('changed exporter or geometry source is rejected rather than silently rebound', async t => {
  const f = await fixture(t);
  for (const path of bridgeGeometrySources) {
    const previous = await readFile(resolve(f.root, path));
    await f.save(path, '# changed\n');
    await assert.rejects(validateBridgeArtifacts(f.root), /Stale Seto Ohashi source/);
    await f.save(path, previous);
  }
});

test('changed saved CAD and incomplete artifact catalogs are rejected', async t => {
  const f = await fixture(t);
  await f.save('GLB/seto_ohashi.glb', 'stale');
  await assert.rejects(validateBridgeArtifacts(f.root), /Stale Seto Ohashi artifact/);
  delete f.manifest.artifacts['GLB/seto_ohashi.glb']; await f.saveMetadata();
  await assert.rejects(validateBridgeArtifacts(f.root), /Invalid Seto Ohashi artifact catalog/);
});

test('rebinding SVG hashes does not hide incorrect visible dimensions or lost official spans', async t => {
  const f = await fixture(t), row = f.drawings.drawings[1];
  const previous = await readFile(resolve(f.root, row.svg), 'utf8');
  await f.save(row.svg, previous.replace('>990000</text>', '>900000</text>'));
  await f.bind(f.drawings, [row.svg]); await f.saveMetadata();
  await assert.rejects(validateBridgeArtifacts(f.root), /SVG visible dimensions differ/);
  row.dimensions_mm = row.dimensions_mm.filter(value => value !== 990000);
  await f.save(row.svg, previous.replace('<text data-dimension-mm="990000">990000</text>', ''));
  await f.bind(f.drawings, [row.svg]); await f.saveMetadata();
  await assert.rejects(validateBridgeArtifacts(f.root), /official bridge and central span lengths/);
});

test('a mixed drawing revision and raster or executable drawing payloads cannot publish', async t => {
  const f = await fixture(t);
  f.drawings.source_geometry_revision = 'BRIDGE-R00'; await f.saveMetadata();
  await assert.rejects(validateBridgeArtifacts(f.root), /mixed revision/);
  f.drawings.source_geometry_revision = 'BRIDGE-R05';
  const row = f.drawings.drawings[0], previous = await readFile(resolve(f.root, row.svg), 'utf8');
  await f.save(row.svg, previous.replace('</svg>', '<image href="foreign"/></svg>'));
  await f.bind(f.drawings, [row.svg]); await f.saveMetadata();
  await assert.rejects(validateBridgeArtifacts(f.root), /Invalid Seto Ohashi SVG/);
});

test('rebinding SVG hashes cannot omit the dimensioned tower front details', async t => {
  const f=await fixture(t), row=f.drawings.drawings.find(row=>row.id==='elevation');
  const svg=await readFile(resolve(f.root,row.svg),'utf8');
  row.dimensions_mm=row.dimensions_mm.filter(value=>value!==194000);
  await f.save(row.svg,svg.replace('<text data-dimension-mm="194000">194000</text>',''));
  await f.bind(f.drawings,[row.svg]);await f.saveMetadata();
  await assert.rejects(validateBridgeArtifacts(f.root),/annotated tower front projections/);
});

test('rebinding SVG hashes cannot omit the BB4A profile label or its three dimensions', async t => {
  for (const omitted of ['BB4A外形', 79000, 53000, 86000]) {
    const f = await fixture(t), row = f.drawings.drawings.find(row => row.id === 'section');
    const svg = await readFile(resolve(f.root, row.svg), 'utf8');
    if (typeof omitted === 'string') {
      row.required_labels = row.required_labels.filter(value => value !== omitted);
      await f.save(row.svg, svg.replace(omitted, ''));
    } else {
      row.dimensions_mm = row.dimensions_mm.filter(value => value !== omitted);
      await f.save(row.svg, svg.replace(`<text data-dimension-mm="${omitted}">${omitted}</text>`, ''));
    }
    await f.bind(f.drawings, [row.svg]); await f.saveMetadata();
    await assert.rejects(validateBridgeArtifacts(f.root), /annotated BB4A external profile/);
  }
});

test('traffic metadata rejects wrong-side driving, floating vehicles and routes beyond the deck', () => {
  const original = activityFixture(); validateBridgeActivity(original);
  for (const mutate of [
    actor => { actor.route.fixed_mm *= -1; actor.origin_mm[1] *= -1; },
    actor => { actor.origin_mm[2] += 300; },
    actor => { actor.route.min_mm = -2000000; },
    actor => { actor.speed_mps = Infinity; },
  ]) {
    const changed = structuredClone(original); mutate(changed.activity.actors[0]);
    assert.throws(() => validateBridgeActivity(changed), /Seto Ohashi/);
  }
});

test('vessel metadata rejects island corridors and mismatched or duplicate native actor parts', () => {
  const original = activityFixture();
  for (const mutate of [
    data => { data.activity.actors[24].route.fixed_mm = 10000; data.activity.actors[24].origin_mm[0] = 10000; },
    data => { data.activity.actors[24].route.max_mm = 390000; },
    data => { data.activity.actors[24].part_names[0] = data.activity.actors[0].part_names[0]; },
    data => { data.activity.actors[24].id = data.activity.actors[0].id; },
    data => { data.components[0].actor_id = 'other'; },
    data => { data.activity.actors.pop(); },
  ]) {
    const changed = structuredClone(original); mutate(changed);
    assert.throws(() => validateBridgeActivity(changed), /Seto Ohashi/);
  }
});


test('crossing boats cannot silently revert to sailing along the bridge', () => {
  const original = activityFixture();
  for (const mutate of [
    actor => { actor.route.axis = 'x'; },
    actor => { actor.heading_rad = 0; },
    actor => { actor.route.min_mm = 20000; },
    actor => { actor.origin_mm[2] = 100; },
  ]) {
    const changed = structuredClone(original); mutate(changed.activity.actors[24]);
    assert.throws(() => validateBridgeActivity(changed), /Seto Ohashi/);
  }
});

test('train publication rejects broken consists, wrong tracks, floating wheels and missing native parts', () => {
  const original = activityFixture(); validateBridgeActivity(original);
  for (const mutate of [
    data => { data.activity.actors[29].carriage_index = 0; },
    data => { data.activity.actors[29].consist_offset_mm = -21500; },
    data => { data.activity.actors[29].speed_mps += 1; },
    data => { data.activity.actors[29].route.fixed_mm = -10500; data.activity.actors[29].origin_mm[1] = -10500; },
    data => { data.activity.actors[29].origin_mm[2] += 300; },
    data => { data.activity.actors[29].pitch_rad *= -1; },
    data => { data.activity.actors[29].route.min_mm = -1610000; },
    data => { data.activity.actors[29].part_names[0] = data.activity.actors[28].part_names[0]; },
    data => { data.activity.rail_crest_z_mm -= 420; },
    data => { data.components.push({ name: 'trains:orphan:body', group: 'trains', actor_id: 'orphan' }); },
    data => { data.components.push(data.components[0]); },
    data => { data.activity.schema_version = 1; },
  ]) {
    const changed = structuredClone(original); mutate(changed);
    assert.throws(() => validateBridgeActivity(changed), /Seto Ohashi/);
  }
});
