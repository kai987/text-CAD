import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtemp, mkdir, writeFile, readFile, rm } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { tmpdir } from 'node:os';
import { validateRiverArtifacts, riverArtifactPaths } from '../scripts/river-artifact-validation.mjs';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');

async function fixture(t) {
  const root = await mkdtemp(resolve(tmpdir(), 'river-publication-test-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const save = async (path, bytes) => {
    await mkdir(dirname(resolve(root, path)), { recursive: true });
    await writeFile(resolve(root, path), bytes);
  };
  const source = "raise RuntimeError('The publication gate must not execute geometry')\n";
  for (const path of ['src/lib/river_geometry.py', 'src/river_3d.py', 'src/generate_river_plans.py']) await save(path, source);
  // Deliberately minimal containers exercise only this publication hash gate.
  // Solid validity and decoded mesh bounds are checked by validate_river.py.
  await save('STEP/river_demo.step', 'ISO-10303-21;\nDATA;\nENDSEC;\nEND-ISO-10303-21;');
  const glb = Buffer.alloc(20); glb.write('glTF'); glb.writeUInt32LE(2, 4); glb.writeUInt32LE(glb.length, 8);
  await save('GLB/river_demo.glb', glb);
  const drawings = {
    schema_version: 1, status: 'concept_demo_only', revision: 'RIVER-R01', units: 'mm',
    source_geometry_revision: 'RIVER-R01',
    source_sha256: { 'src/lib/river_geometry.py': sha(source), 'src/generate_river_plans.py': sha(source) },
    drawings: [
      { id: 'plan', dxf: 'DXF/river_demo_plan.dxf', svg: 'output/svg/river_demo_plan.svg',
        dimensions_mm: [180000, 80000, 18000, 38000, 4000, 3000],
        required_labels: ['河川平面図', '歩道', '流下方向', 'デモ仮定'] },
      { id: 'section', dxf: 'DXF/river_demo_section.dxf', svg: 'output/svg/river_demo_section.svg',
        dimensions_mm: [80000, 18000, 38000, 3000, 900],
        required_labels: ['横断面', '河床', '水面', 'デモ仮定'] },
    ], artifacts: {},
  };
  for (const row of drawings.drawings) {
    await save(row.dxf, '0\nDIMENSION\n0\nTEXT\n');
    await save(row.svg, `<svg data-units="mm" data-revision="RIVER-R01">${row.dimensions_mm
      .map(value => `<text data-dimension-mm="${value}">${value}</text>`).join('')}${row.required_labels
      .map(label => `<text>${label}</text>`).join('')}</svg>`);
  }
  const manifest = {
    schema_version: 1, status: 'concept_demo_only', revision: 'RIVER-R01', units: 'mm',
    parameters: { length: 180000, width: 80000, water_width: 18000, bridge_width: 4000, path_width: 3000,
      crest_z: 3000, water_z: 0, bed_z: -900 },
    bridge: { span: 38000, structural_calculation: null },
    engineering: { hydraulic_capacity: null, bridge_strength: null, foundation_capacity: null, statutory_compliance: null },
    assumptions: ['Demonstration dimensions.', 'Invented terrain.', 'No flood calculation.', 'No bridge calculation.'],
    source_sha256: { 'src/lib/river_geometry.py': sha(source), 'src/river_3d.py': sha(source) }, artifacts: {},
  };
  async function bind(metadata, paths) {
    for (const path of paths) {
      const bytes = await readFile(resolve(root, path)); metadata.artifacts[path] = { bytes: bytes.length, sha256: sha(bytes) };
    }
  }
  await bind(manifest, riverArtifactPaths.slice(0, 2)); await bind(drawings, riverArtifactPaths.slice(2, 6));
  const saveMetadata = async () => {
    await save(riverArtifactPaths[6], JSON.stringify(manifest));
    await save(riverArtifactPaths[7], JSON.stringify(drawings));
  };
  await saveMetadata();
  return { root, save, manifest, drawings, bind, saveMetadata };
}

test('source-bound river publication can be verified in Node without CAD imports', async t => {
  const { root, manifest, drawings } = await fixture(t);
  const checked = await validateRiverArtifacts(root);
  assert.deepEqual(checked.manifest, manifest);
  assert.deepEqual(checked.drawings, drawings);
  assert.deepEqual(checked.paths, riverArtifactPaths);
});

test('changing any generation source rejects the published model or drawing bindings', async t => {
  const { root, save } = await fixture(t);
  for (const path of ['src/lib/river_geometry.py', 'src/river_3d.py', 'src/generate_river_plans.py']) {
    const previous = await readFile(resolve(root, path));
    await save(path, `${previous}# changed source\n`);
    await assert.rejects(validateRiverArtifacts(root), /Stale river source binding/);
    await save(path, previous);
  }
});

test('every changed CAD or SVG file rejects stale hashes and lengths', async t => {
  const { root, save } = await fixture(t);
  for (const path of riverArtifactPaths.slice(0, 6)) {
    const previous = await readFile(resolve(root, path));
    await save(path, Buffer.concat([previous, Buffer.from('changed')]));
    await assert.rejects(validateRiverArtifacts(root), /Stale river artifact/);
    await save(path, previous);
  }
});

test('missing drawing metadata, incomplete catalogs and unexpected source paths fail closed', async t => {
  const { root, drawings, manifest, saveMetadata } = await fixture(t);
  await rm(resolve(root, riverArtifactPaths[7]));
  await assert.rejects(validateRiverArtifacts(root), /Missing river asset or source/);
  await saveMetadata();
  delete drawings.artifacts['output/svg/river_demo_plan.svg']; await saveMetadata();
  await assert.rejects(validateRiverArtifacts(root), /Invalid river artifact set/);
  manifest.source_sha256['../outside.py'] = 'a'.repeat(64); await saveMetadata();
  await assert.rejects(validateRiverArtifacts(root), /Invalid river source set/);
});

test('rebinding an SVG cannot conceal dimension changes against shared model parameters', async t => {
  const { root, save, drawings, bind, saveMetadata } = await fixture(t);
  const row = drawings.drawings[0];
  const svg = await readFile(resolve(root, row.svg), 'utf8');
  await save(row.svg, svg.replace('data-dimension-mm="18000"', 'data-dimension-mm="19000"'));
  await bind(drawings, [row.svg]); await saveMetadata();
  await assert.rejects(validateRiverArtifacts(root), /SVG dimensions differ/);
  row.dimensions_mm[2] = 19000; await saveMetadata();
  await assert.rejects(validateRiverArtifacts(root), /Invalid river drawing dimensions/);
});

test('an SVG dimension attribute cannot conceal a different visible dimension number', async t => {
  const { root, save, drawings, bind, saveMetadata } = await fixture(t);
  const row = drawings.drawings[1];
  const svg = await readFile(resolve(root, row.svg), 'utf8');
  await save(row.svg, svg.replace('data-dimension-mm="900">900</text>', 'data-dimension-mm="900">100</text>'));
  await bind(drawings, [row.svg]); await saveMetadata();
  await assert.rejects(validateRiverArtifacts(root), /visible dimension text is inconsistent/);
});

test('mixed revisions, empty annotations and noneditable DXFs remain rejected after updated hashes', async t => {
  const { root, save, drawings, bind, saveMetadata } = await fixture(t);
  drawings.source_geometry_revision = 'RIVER-R02'; await saveMetadata();
  await assert.rejects(validateRiverArtifacts(root), /mixed revision/);
  drawings.source_geometry_revision = 'RIVER-R01';
  const row = drawings.drawings[0]; const labels = row.required_labels;
  row.required_labels = []; await saveMetadata();
  await assert.rejects(validateRiverArtifacts(root), /Invalid river drawing dimensions or labels/);
  row.required_labels = labels;
  await save(row.dxf, '0\nLINE\n'); await bind(drawings, [row.dxf]); await saveMetadata();
  await assert.rejects(validateRiverArtifacts(root), /no editable dimensions/);
});

test('demonstration publication never claims hydraulic, bridge, foundation or statutory approval', async t => {
  const { root, manifest, saveMetadata } = await fixture(t);
  for (const key of Object.keys(manifest.engineering)) {
    manifest.engineering[key] = { approved: true }; await saveMetadata();
    await assert.rejects(validateRiverArtifacts(root), /uncalculated engineering results/);
    manifest.engineering[key] = null;
  }
  manifest.bridge.structural_calculation = true; await saveMetadata();
  await assert.rejects(validateRiverArtifacts(root), /uncalculated engineering results/);
});
