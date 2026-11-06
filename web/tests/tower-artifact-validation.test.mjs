import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtemp, mkdir, readFile, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, resolve } from 'node:path';
import { towerCatalog, towerPaths, validateTowerArtifacts, hasStepContainerMarkers } from '../scripts/tower-artifact-validation.mjs';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
test('STEP container markers are checked as binary bytes without whole-file string conversion', () => {
  const step = Buffer.concat([Buffer.from('ISO-10303-21;\nDATA;'), Buffer.from([0, 255, 128]), Buffer.from('\nEND-ISO-10303-21;')]);
  step.toString = () => { throw new Error('Whole-file string conversion exceeds the native CAD size budget.'); };
  assert.equal(hasStepContainerMarkers(step), true);
  for (const invalid of [Buffer.alloc(0), Buffer.from('not a STEP END-ISO-10303-21;'), Buffer.from('ISO-10303-21;'), 'ISO-10303-21;END-ISO-10303-21;']) {
    assert.equal(hasStepContainerMarkers(invalid), false);
  }
});
async function fixture(t) {
  const root = await mkdtemp(resolve(tmpdir(), 'tower-publication-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const save = async (path, value) => {
    await mkdir(dirname(resolve(root, path)), { recursive: true });
    await writeFile(resolve(root, path), value);
  };
  const source = "raise RuntimeError('Publication must not execute CAD sources')\n";
  for (const path of ['src/lib/tower_geometry.py', 'src/lib/tower_parameters.py', 'src/lib/tokyo_tower_parameters.py', 'src/lib/skytree_parameters.py', 'src/towers_3d.py', 'src/generate_tower_plans.py', 'src/lib/tokyo_tower_detail.py', 'src/lib/tokyo_tower_steel.py', 'src/lib/tokyo_tower_equipment.py', 'src/lib/tokyo_tower_builtup.py', 'src/lib/tokyo_tower_integrated.py', 'src/lib/tokyo_tower_grid.py', 'src/lib/skytree_detail.py', 'src/lib/skytree_outline.py']) await save(path, source);
  const records = [];
  async function bind(metadata, paths) {
    metadata.artifacts = {};
    for (const path of paths) {
      const data = await readFile(resolve(root, path));
      metadata.artifacts[path] = { bytes: data.length, sha256: sha(data) };
    }
  }
  for (const tower of towerCatalog) {
    const paths = towerPaths(tower.stem);
    // The Node gate verifies publication containers and bindings; native solids
    // and real binary coordinates are independently read by validate_towers.py.
    await save(paths.models[0], 'ISO-10303-21;\nDATA;\nENDSEC;\nEND-ISO-10303-21;');
    const glb = Buffer.alloc(20); glb.write('glTF'); glb.writeUInt32LE(2, 4); glb.writeUInt32LE(20, 8);
    await save(paths.models[1], glb);
    await save(paths.drawings[4], '%PDF-1.7\nfixture');
    const dimensions = [[80000], [tower.height, ...tower.decks, ...(tower.roofLevels ?? [])]];
    const common = { schema_version: 1, revision: tower.revision, units: 'mm', status: 'reference_concept_only' };
    const manifest = { ...common, id: tower.id, height_mm: tower.height,
      parameters: { base_width_mm: 80000 }, assumptions: ['Schematic frame.', 'No structural design.'],
      source_references: [{ url: 'https://example.com/operator-reference' }],
      source_sha256: { 'src/lib/tower_geometry.py': sha(source), 'src/lib/tower_parameters.py': sha(source), 'src/towers_3d.py': sha(source) } };
    const drawings = { ...common, source_geometry_revision: tower.revision,
      ...(tower.roofLevels ? { roof_levels_mm: tower.roofLevels } : {}),
      source_sha256: { 'src/lib/tower_geometry.py': sha(source), 'src/lib/tower_parameters.py': sha(source), 'src/generate_tower_plans.py': sha(source) },
      drawings: ['plan', 'elevation'].map((id, index) => ({ id,
        dxf: paths.drawings[index], svg: paths.drawings[index + 2],
        dimensions_mm: dimensions[index], required_labels: ['参考モデル', '単位 mm'] })) };
    if(tower.id==='tokyo-tower'){
      manifest.steel_nodes=Array.from({length:20},(_,i)=>({id:`TT-N${String(i+1).padStart(2,'0')}`,
        names:{zh:'节点',ja:'接合部',en:'Node'},anchor_mm:[40000,40000,1200],
        part_names:['structure:plate_'+i,'structure:rib_a_'+i,'structure:rib_b_'+i]}));
      drawings.drawings.push({id:'steel-nodes',dxf:paths.drawings[5],svg:paths.drawings[6],
        dimensions_mm:[1200,151.2],required_labels:['参考モデル','単位 mm']});
    } else {
      drawings.drawings[1].roof_levels_mm = tower.roofLevels;
      drawings.drawings.push({id:'structure-zones',dxf:paths.drawings[5],svg:paths.drawings[6],
        dimensions_mm:[50000,12500,25000],required_labels:['参考モデル','単位 mm']});
    }
    for (const extra of tower.sources) {manifest.source_sha256[extra]=sha(source);drawings.source_sha256[extra]=sha(source);}
    for (const row of drawings.drawings) {
      await save(row.dxf, '0\nDIMENSION\n0\nTEXT\n');
      await save(row.svg, `<svg data-units="mm" data-revision="${tower.revision}">${row.dimensions_mm
        .map(value => `<text data-dimension-mm="${value}">${value}</text>`).join('')}<text>参考モデル</text><text>単位 mm</text></svg>`);
    }
    await bind(manifest, paths.models); await bind(drawings, paths.drawings);
    records.push({ manifest, drawings, paths });
  }
  const saveMetadata = async () => {
    for (const { manifest, drawings, paths } of records) {
      await save(paths.metadata[0], JSON.stringify(manifest));
      await save(paths.metadata[1], JSON.stringify(drawings));
    }
  };
  await saveMetadata();
  return { root, save, bind, saveMetadata, records };
}

test('both reference towers are source-bound without executing CAD generation', async t => {
  const fixtureData = await fixture(t);
  const result = await validateTowerArtifacts(fixtureData.root);
  assert.equal(result.models.length, 2); assert.equal(result.paths.length, 22);
});
test('changed tower source rejects publication', async t => {
  const { root, save } = await fixture(t);
  await save('src/lib/tower_geometry.py', '# changed dimensions');
  await assert.rejects(validateTowerArtifacts(root), /Stale tower source/);
});
test('modified exported bytes reject stale provenance', async t => {
  const { root, save, records } = await fixture(t);
  await save(records[1].paths.models[1], 'changed GLB bytes');
  await assert.rejects(validateTowerArtifacts(root), /Stale tower artifact/);
});
test('independent landmark reference heights reject altered model metadata', async t => {
  const { root, records, saveMetadata } = await fixture(t);
  records[0].manifest.height_mm = 334000; await saveMetadata();
  await assert.rejects(validateTowerArtifacts(root), /Invalid tower dimensions/);
});
test('rebound drawings still require readable and editable dimensions', async t => {
  const { root, save, bind, records, saveMetadata } = await fixture(t);
  const { paths, drawings } = records[0];
  await save(paths.drawings[0], '0\nLINE\n');
  await bind(drawings, paths.drawings); await saveMetadata();
  await assert.rejects(validateTowerArtifacts(root), /missing editable annotations/);
});
test('rebinding SVG bytes cannot disguise inconsistent visible dimension text', async t => {
  const { root, save, bind, records, saveMetadata } = await fixture(t);
  const { paths, drawings } = records[0];
  const svg = await readFile(resolve(root, paths.drawings[3]), 'utf8');
  await save(paths.drawings[3], svg.replace('>333000<', '>334000<'));
  await bind(drawings, paths.drawings); await saveMetadata();
  await assert.rejects(validateTowerArtifacts(root), /visible dimensions differ/);
});
test('all three independently referenced elevation levels are required', async t => {
  const { root, records, save, bind, saveMetadata } = await fixture(t);
  const { paths, drawings } = records[1];
  drawings.drawings[1].dimensions_mm=drawings.drawings[1].dimensions_mm.filter(value=>value!==450000);
  const svg = await readFile(resolve(root, paths.drawings[3]), 'utf8');
  await save(paths.drawings[3], svg.replace('<text data-dimension-mm="450000">450000</text>', ''));
  await bind(drawings, paths.drawings); await saveMetadata();
  await assert.rejects(validateTowerArtifacts(root), /Missing required tower model levels/);
});

// The two towers have independent release revisions and height conventions.
test('R11 Tokyo models and drawings reject old R10 through R02 independently', async t => {
  const { root, records, saveMetadata } = await fixture(t);
  assert.equal(records[1].manifest.revision,'LANDMARK-R05');
  for (const metadata of [records[0].manifest, records[0].drawings]) {
    for (const stale of ['LANDMARK-R10','LANDMARK-R09','LANDMARK-R08','LANDMARK-R07','LANDMARK-R06','LANDMARK-R05','LANDMARK-R04','LANDMARK-R03','LANDMARK-R02']) {
      metadata.revision=stale; await saveMetadata();
      await assert.rejects(validateTowerArtifacts(root), /Invalid landmark reference scope/);
    }
    metadata.revision='LANDMARK-R11'; await saveMetadata();
  }
  await validateTowerArtifacts(root);
});
test('changing the Tokyo detail module invalidates its own generation binding', async t => {
  const { root, save } = await fixture(t);
  await save('src/lib/tokyo_tower_detail.py','# changed stair or frame');
  await assert.rejects(validateTowerArtifacts(root), /Stale tower source/);
});

test('Tokyo equipment source is retained in R11 model and drawing bindings independently', async t => {
  const { root, records, saveMetadata } = await fixture(t);
  const path = 'src/lib/tokyo_tower_equipment.py';
  assert.deepEqual(towerCatalog.find(tower => tower.id === 'tokyo-tower').sources,
    ['src/lib/tokyo_tower_parameters.py', 'src/lib/tokyo_tower_detail.py', 'src/lib/tokyo_tower_steel.py', path, 'src/lib/tokyo_tower_builtup.py', 'src/lib/tokyo_tower_integrated.py', 'src/lib/tokyo_tower_grid.py']);
  for (const metadata of [records[0].manifest, records[0].drawings]) {
    const expected = metadata.source_sha256[path];
    assert.match(expected, /^[a-f0-9]{64}$/);
    delete metadata.source_sha256[path];
    await saveMetadata();
    await assert.rejects(validateTowerArtifacts(root), /Invalid tower source set/);
    metadata.source_sha256[path] = expected;
    await saveMetadata();
  }
  await validateTowerArtifacts(root);
});

test('changing the Tokyo equipment source invalidates R11 publication provenance', async t => {
  const { root, save } = await fixture(t);
  await save('src/lib/tokyo_tower_equipment.py', '# changed outboard brackets or covers');
  await assert.rejects(validateTowerArtifacts(root),
    /Stale tower source: src\/lib\/tokyo_tower_equipment\.py/);
});

test('R11 Tokyo built-up source is required in model and drawing bindings independently', async t => {
  const { root, records, saveMetadata } = await fixture(t);
  const path = 'src/lib/tokyo_tower_builtup.py';
  assert.ok(towerCatalog.find(tower => tower.id === 'tokyo-tower').sources.includes(path));
  for (const metadata of [records[0].manifest, records[0].drawings]) {
    const expected = metadata.source_sha256[path];
    assert.match(expected, /^[a-f0-9]{64}$/);
    delete metadata.source_sha256[path];
    await saveMetadata();
    await assert.rejects(validateTowerArtifacts(root), /Invalid tower source set/);
    metadata.source_sha256[path] = expected;
    await saveMetadata();
  }
  await validateTowerArtifacts(root);
});

test('changed or missing Tokyo built-up source invalidates R11 publication provenance', async t => {
  const { root, save } = await fixture(t);
  const path = 'src/lib/tokyo_tower_builtup.py';
  await save(path, '# changed cover plates or open built-up webs');
  await assert.rejects(validateTowerArtifacts(root),
    /Stale tower source: src\/lib\/tokyo_tower_builtup\.py/);
  await rm(resolve(root, path));
  await assert.rejects(validateTowerArtifacts(root),
    /Missing tower asset or source: src\/lib\/tokyo_tower_builtup\.py/);
});


test('R11 Tokyo integrated source is required in model and drawing bindings independently', async t => {
  const { root, records, saveMetadata } = await fixture(t);
  const path = 'src/lib/tokyo_tower_integrated.py';
  assert.ok(towerCatalog.find(tower => tower.id === 'tokyo-tower').sources.includes(path));
  for (const metadata of [records[0].manifest, records[0].drawings]) {
    const expected = metadata.source_sha256[path];
    assert.match(expected, /^[a-f0-9]{64}$/);
    delete metadata.source_sha256[path];
    await saveMetadata();
    await assert.rejects(validateTowerArtifacts(root), /Invalid tower source set/);
    metadata.source_sha256[path] = expected;
    await saveMetadata();
  }
  await validateTowerArtifacts(root);
});

test('changed or missing Tokyo integrated source invalidates R11 publication provenance', async t => {
  const { root, save } = await fixture(t);
  const path = 'src/lib/tokyo_tower_integrated.py';
  await save(path, '# changed gross leg or arch assembly');
  await assert.rejects(validateTowerArtifacts(root),
    /Stale tower source: src\/lib\/tokyo_tower_integrated\.py/);
  await rm(resolve(root, path));
  await assert.rejects(validateTowerArtifacts(root),
    /Missing tower asset or source: src\/lib\/tokyo_tower_integrated\.py/);
});


test('R11 Tokyo grid source is required in model and drawing bindings independently', async t => {
  const { root, records, saveMetadata } = await fixture(t);
  const path = 'src/lib/tokyo_tower_grid.py';
  assert.ok(towerCatalog.find(tower => tower.id === 'tokyo-tower').sources.includes(path));
  for (const metadata of [records[0].manifest, records[0].drawings]) {
    const expected = metadata.source_sha256[path];
    assert.match(expected, /^[a-f0-9]{64}$/);
    delete metadata.source_sha256[path];
    await saveMetadata();
    await assert.rejects(validateTowerArtifacts(root), /Invalid tower source set/);
    metadata.source_sha256[path] = expected;
    await saveMetadata();
  }
  await validateTowerArtifacts(root);
});

test('changed or missing Tokyo grid source invalidates R11 publication provenance', async t => {
  const { root, save } = await fixture(t);
  const path = 'src/lib/tokyo_tower_grid.py';
  await save(path, '# changed four-column grid or its 80m transition');
  await assert.rejects(validateTowerArtifacts(root),
    /Stale tower source: src\/lib\/tokyo_tower_grid\.py/);
  await rm(resolve(root, path));
  await assert.rejects(validateTowerArtifacts(root),
    /Missing tower asset or source: src\/lib\/tokyo_tower_grid\.py/);
});


test('R05 Skytree models and drawings reject old R04, R03, R02 and R01 independently of Tokyo', async t => {
  const {root,records,saveMetadata}=await fixture(t);
  assert.equal(records[0].manifest.revision,'LANDMARK-R11');
  for (const metadata of [records[1].manifest, records[1].drawings]) {
    for (const stale of ['LANDMARK-R04','LANDMARK-R03','LANDMARK-R02','LANDMARK-R01']) {
      metadata.revision=stale; await saveMetadata();
      await assert.rejects(validateTowerArtifacts(root), /Invalid landmark reference scope/);
    }
    metadata.revision='LANDMARK-R05'; await saveMetadata();
  }
  await validateTowerArtifacts(root);
});
test('changing the Skytree detail module invalidates its own generation binding', async t => {
  const {root,save}=await fixture(t);
  await save('src/lib/skytree_detail.py','# changed galleria ramp or tower frame');
  await assert.rejects(validateTowerArtifacts(root), /Stale tower source/);
});
test('changing or omitting the Skytree outline source invalidates R05 provenance', async t => {
  const {root,save,records,saveMetadata}=await fixture(t);
  assert.deepEqual(towerCatalog.find(tower=>tower.id==='tokyo-skytree').sources,
    ['src/lib/skytree_parameters.py','src/lib/skytree_detail.py','src/lib/skytree_outline.py']);
  delete records[1].manifest.source_sha256['src/lib/skytree_outline.py'];
  await saveMetadata();
  await assert.rejects(validateTowerArtifacts(root), /Invalid tower source set/);
  records[1].manifest.source_sha256['src/lib/skytree_outline.py']=records[1].manifest.source_sha256['src/lib/skytree_detail.py'];
  await saveMetadata();
  await save('src/lib/skytree_outline.py','# changed corner arcs or upper taper');
  await assert.rejects(validateTowerArtifacts(root), /Stale tower source/);
});


test('twenty assumed steel-node locations and current source bindings are required for Tokyo R06', async t => {
  const {root,records,saveMetadata}=await fixture(t);
  records[0].manifest.steel_nodes.pop();await saveMetadata();
  await assert.rejects(validateTowerArtifacts(root),/steel-node catalog/);
});
test('steel detail source changes invalidate the Tokyo release',async t=>{
  const {root,save}=await fixture(t);
  await save('src/lib/tokyo_tower_steel.py','# changed a node');
  await assert.rejects(validateTowerArtifacts(root),/Stale tower source/);
});
test('R06 requires the editable steel detail drawing in addition to the original sheets',async t=>{
  const {root,records,saveMetadata}=await fixture(t);
  records[0].drawings.drawings.pop();await saveMetadata();
  await assert.rejects(validateTowerArtifacts(root),/drawing catalog/);
});

test('R05 Skytree requires its source-bound structure zones page while keeping earlier sheet paths',async t=>{
  const {root,records,saveMetadata}=await fixture(t);
  const {drawings,paths}=records[1];
  assert.deepEqual(paths.drawings.slice(0,5),[
    'DXF/tokyo_skytree_plan.dxf','DXF/tokyo_skytree_elevation.dxf',
    'output/svg/tokyo_skytree_plan.svg','output/svg/tokyo_skytree_elevation.svg','output/pdf/tokyo_skytree_sheets.pdf',
  ]);
  assert.equal(drawings.drawings[2].id,'structure-zones');
  assert.equal(drawings.drawings[2].dxf,'DXF/tokyo_skytree_structure_zones.dxf');
  assert.equal(drawings.drawings[2].svg,'output/svg/tokyo_skytree_structure_zones.svg');
  drawings.drawings.pop(); await saveMetadata();
  await assert.rejects(validateTowerArtifacts(root),/drawing catalog/);
});

test('Skytree structure zones retain the model reference range and two ring intervals',async t=>{
  const {root,records,save,bind,saveMetadata}=await fixture(t);
  const {drawings,paths}=records[1], row=drawings.drawings[2];
  row.dimensions_mm=row.dimensions_mm.filter(value=>value!==12500);
  const svg=await readFile(resolve(root,row.svg),'utf8');
  await save(row.svg,svg.replace('<text data-dimension-mm="12500">12500</text>',''));
  await bind(drawings,paths.drawings);await saveMetadata();
  await assert.rejects(validateTowerArtifacts(root),/structure-zone dimensions/);
});

test('reference corrections accept different local part counts at the twenty assumed connections', async t => {
  const { root, records, saveMetadata } = await fixture(t);
  records[0].manifest.steel_nodes.forEach((node, index) => {
    node.part_names = Array.from({ length: [1, 2, 5, 13, 24][index % 5] }, (_, part) => `structure:${node.id}_part_${part}`);
  });
  await saveMetadata(); await validateTowerArtifacts(root);
  records[0].manifest.steel_nodes[0].part_names = [];
  await saveMetadata(); await assert.rejects(validateTowerArtifacts(root), /steel-node catalog/);
});

test('publication uses construction GL levels rather than the official deck-name heights', () => {
  assert.deepEqual(towerCatalog.find(tower => tower.id === 'tokyo-tower').decks, [125000, 223550]);
  assert.deepEqual(towerCatalog.find(tower => tower.id === 'tokyo-skytree').decks, [350000, 450000]);
  assert.deepEqual(towerCatalog.find(tower => tower.id === 'tokyo-skytree').roofLevels, [375000]);
});

test('Skytree R05 requires the equipment roof dimension and separate metadata without changing observation floors',async t=>{
  const {root,records,save,bind,saveMetadata}=await fixture(t);
  const {drawings,paths}=records[1],row=drawings.drawings[1];
  assert.deepEqual(row.roof_levels_mm,[375000]);
  delete row.roof_levels_mm;await saveMetadata();
  await assert.rejects(validateTowerArtifacts(root),/equipment-roof reference levels/);
  row.roof_levels_mm=[375000];
  row.dimensions_mm=row.dimensions_mm.filter(value=>value!==375000);
  const svg=await readFile(resolve(root,row.svg),'utf8');
  await save(row.svg,svg.replace('<text data-dimension-mm="375000">375000</text>',''));
  await bind(drawings,paths.drawings);await saveMetadata();
  await assert.rejects(validateTowerArtifacts(root),/equipment-roof reference levels/);
});


test('six-decimal SVG dimensions accept only rounding-scale differences from native DXF measurements',async t=>{
  const {root,records,saveMetadata}=await fixture(t);
  records[0].drawings.drawings[2].dimensions_mm[1]=151.20000000001684;
  await saveMetadata();await validateTowerArtifacts(root);
  records[0].drawings.drawings[2].dimensions_mm[1]=151.21;
  await saveMetadata();await assert.rejects(validateTowerArtifacts(root),/visible dimensions differ/);
});

test('each landmark binds its own parameters and the shared input schema', async t => {
  for (const tower of towerCatalog) {
    const own = tower.id === 'tokyo-tower' ? 'tokyo_tower_parameters' : 'skytree_parameters';
    const other = tower.id === 'tokyo-tower' ? 'skytree_parameters' : 'tokyo_tower_parameters';
    assert.ok(tower.sources.includes(`src/lib/${own}.py`));
    assert.ok(!tower.sources.includes(`src/lib/${other}.py`));
    for (const path of [`src/lib/${own}.py`, 'src/lib/tower_parameters.py']) {
      await t.test(`${tower.id}: ${path}`, async t => {
        const { root, save } = await fixture(t);
        await save(path, '# changed parameter values or shared validation');
        await assert.rejects(validateTowerArtifacts(root), /Stale tower source/);
      });
    }
  }
});
