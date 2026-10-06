#!/usr/bin/env node
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { isAbsolute } from 'node:path';
import { performance } from 'node:perf_hooks';
import { Box3, EdgesGeometry, Vector3 } from 'three';
import { loadGlbGeometry } from '../tests/helpers/load-glb-geometry.mjs';
import { bindCadNodes, centerModelAtFloorDatum } from '../src/model-scene.ts';
import { createCadOutlineGeometry } from '../src/cad-outlines.ts';
import { createHorizontalCap } from '../src/section-caps.ts';
import { createWasmHorizontalCap, createWasmCadOutlineGeometry, initializeSectionCapsWasm } from '../src/section-caps-wasm.ts';

const args = process.argv.slice(2);
let output, includeEdges = false, trials = 150;
for (let i = 0; i < args.length; i++) {
  if (args[i] === '--edges') includeEdges = true;
  else if (args[i] === '--output') {
    output = args[++i];
    assert.ok(output !== undefined, '--output requires an absolute path');
  }
  else if (args[i] === '--trials') trials = Number(args[++i]);
  else throw new Error(`Unknown option ${args[i]}; supported: --edges --trials 150 --output /absolute/path.json`);
}
assert.ok(Number.isInteger(trials) && trials >= 100 && trials <= 2000, '--trials must be an integer from 100 to 2000');
assert.ok(output === undefined || (typeof output === 'string' && isAbsolute(output)), '--output must use an absolute path');

const wasmBytes = await readFile(new URL('../src/wasm/section_caps_bg.wasm', import.meta.url));
const initStart = performance.now();
await initializeSectionCapsWasm(wasmBytes);
const coldInitMs = performance.now() - initStart;
const modelBytes = await readFile(new URL('../../GLB/house_3d.glb', import.meta.url));
const gltf = await loadGlbGeometry(new URL('../../GLB/house_3d.glb', import.meta.url));
const nodes = bindCadNodes(gltf);
assert.ok(centerModelAtFloorDatum(gltf.scene, nodes), 'use the viewer first-floor datum');
const offset = gltf.scene.position.y;
const meshes = [];
gltf.scene.traverse(object => {
  if (!object.isMesh) return;
  const material = Array.isArray(object.material) ? object.material[0] : object.material;
  // Exactly the opaque mesh predicate used by the viewer's section-cap pass.
  if (!material.transparent && material.opacity >= 1) meshes.push(object);
});
assert.ok(meshes.length > 0, 'benchmark must load opaque house meshes');
const drawingHeightsMm = [1200, 2700, 4200, 5600];
const heights = drawingHeightsMm.map(height => height / 1000 - 0.00005);

function describe(mesh, geometry) {
  if (!geometry) return null;
  const positions = geometry.getAttribute('position'), bounds = new Box3();
  let area = 0;
  for (let i = 0; i < positions.count; i += 3) {
    const [a, b, c] = [0, 1, 2].map(offset => new Vector3()
      .fromBufferAttribute(positions, i + offset).applyMatrix4(mesh.matrixWorld));
    bounds.expandByPoint(a); bounds.expandByPoint(b); bounds.expandByPoint(c);
    const cross = new Vector3().subVectors(b, a).cross(new Vector3().subVectors(c, a));
    assert.ok(cross.y > 0, 'cap winding must point up'); area += cross.y / 2;
  }
  return { area, bounds };
}

let comparisons = 0, nonempty = 0;
for (const height of heights) for (const mesh of meshes) {
  const reference = createHorizontalCap(mesh, height), actual = createWasmHorizontalCap(mesh, height);
  try {
    assert.equal(actual === null, reference === null, 'benchmark cap/null correctness gate');
    if (reference) {
      const a = describe(mesh, reference), b = describe(mesh, actual);
      assert.ok(Math.abs(a.area - b.area) <= Math.max(2e-5, a.area * 1e-5), 'benchmark cap area correctness gate');
      for (const side of ['min', 'max']) for (const axis of ['x', 'y', 'z']) {
        assert.ok(Math.abs(a.bounds[side][axis] - b.bounds[side][axis]) <= 2e-5, 'benchmark cap bounds correctness gate');
      }
      nonempty++;
    }
    comparisons++;
  } finally { reference?.dispose(); actual?.dispose(); }
}

function runBatch(createCap, edges) {
  let capCount = 0, triangleCount = 0;
  for (const height of heights) for (const mesh of meshes) {
    const geometry = createCap(mesh, height);
    if (!geometry) continue;
    capCount++; triangleCount += geometry.getAttribute('position').count / 3;
    if (edges) new EdgesGeometry(geometry, 28).dispose();
    geometry.dispose();
  }
  return { capCount, triangleCount };
}

const engines = { typescript: createHorizontalCap, rustWasm: createWasmHorizontalCap };
const phases = includeEdges ? [['geometry', false], ['geometryAndEdges', true]] : [['geometry', false]];
const results = {};
for (const [phase, edges] of phases) {
  // Warm JIT, allocator and WASM paths equally; do not include warmup in timings.
  for (let i = 0; i < 30; i++) for (const engine of Object.values(engines)) runBatch(engine, edges);
  const samples = { typescript: [], rustWasm: [] }, outputCounts = {};
  for (let i = 0; i < trials; i++) {
    // Alternate timing order to reduce a consistent first/last-engine bias.
    const order = i % 2 ? ['rustWasm', 'typescript'] : ['typescript', 'rustWasm'];
    for (const name of order) {
      const start = performance.now();
      outputCounts[name] = runBatch(engines[name], edges);
      samples[name].push(performance.now() - start);
    }
  }
  for (const name of Object.keys(samples)) samples[name].sort((a, b) => a - b);
  const summarize = values => ({
    medianBatchMs: (values[Math.floor((values.length - 1) / 2)] + values[Math.floor(values.length / 2)]) / 2,
    p95BatchMs: values[Math.ceil(values.length * 0.95) - 1],
    minBatchMs: values[0],
  });
  results[phase] = {
    typescript: { ...summarize(samples.typescript), ...outputCounts.typescript },
    rustWasm: { ...summarize(samples.rustWasm), ...outputCounts.rustWasm },
  };
  assert.equal(outputCounts.typescript.capCount, outputCounts.rustWasm.capCount, 'identical number of caps');
}

const walls = [...nodes].filter(([name, mesh]) => mesh.isMesh &&
  /:wall_(?:external|partition)_|^roof:.*gable_wall$|:cladding:/.test(name)).map(([, mesh]) => mesh);
for (const mesh of walls) {
  const expected = createCadOutlineGeometry(mesh.geometry, 28);
  const actual = createWasmCadOutlineGeometry(mesh.geometry, 28);
  try {
    const a = expected.getAttribute('position').array, b = actual.getAttribute('position').array;
    assert.equal(a.length, b.length, 'outline endpoint count parity');
    for (let i = 0; i < a.length; i++) assert.ok(Math.abs(a[i] - b[i]) <= 2e-6, 'outline endpoint parity');
  } finally { expected.dispose(); actual.dispose(); }
}
const outlineEngines = { typescript: createCadOutlineGeometry, rustWasm: createWasmCadOutlineGeometry };
function outlineBatch(engine) {
  let segments = 0;
  for (const mesh of walls) {
    const geometry = engine(mesh.geometry, 28);
    segments += geometry.getAttribute('position').count / 2; geometry.dispose();
  }
  return segments;
}
for (let i = 0; i < 30; i++) for (const engine of Object.values(outlineEngines)) outlineBatch(engine);
const outlineSamples = { typescript: [], rustWasm: [] };
for (let i = 0; i < trials; i++) for (const name of i % 2 ? ['rustWasm', 'typescript'] : ['typescript', 'rustWasm']) {
  const start = performance.now(); outlineBatch(outlineEngines[name]); outlineSamples[name].push(performance.now() - start);
}
results.cadOutlines = Object.fromEntries(Object.entries(outlineSamples).map(([name, values]) => {
  values.sort((a, b) => a - b);
  return [name, { medianBatchMs: (values[Math.floor((values.length - 1) / 2)] + values[Math.floor(values.length / 2)]) / 2,
    p95BatchMs: values[Math.ceil(values.length * 0.95) - 1], minBatchMs: values[0] }];
}));

const report = {
  runtime: { node: process.version, platform: process.platform, arch: process.arch },
  workload: {
    model: 'GLB/house_3d.glb', modelSha256: createHash('sha256').update(modelBytes).digest('hex'),
    opaqueMeshes: meshes.length,
    cadOutlineMeshes: walls.length,
    inputTriangles: meshes.reduce((sum, mesh) => sum + (mesh.geometry.index?.count ?? mesh.geometry.getAttribute('position').count) / 3, 0),
    drawingHeightsMm, worldYZeroOffsetMetres: offset, displayCapOffsetMm: -0.05,
    meshHeightCallsPerBatch: meshes.length * heights.length,
    warmupBatchesPerEngine: 30, trialsPerEngine: trials, wasmBytes: wasmBytes.byteLength,
  },
  correctness: { passed: true, comparisons, nonempty, outlineComparisons: walls.length },
  coldWasmCompileAndInstantiateMs: coldInitMs,
  results,
  scope: [
    'Each batch covers every opaque source mesh at all four heights, including null sections.',
    'Timings include coordinate marshalling, mesh world-transform updates, cap triangulation, BufferGeometry creation, bounds, and disposal.',
    'With --edges, a separate phase also includes the same EdgesGeometry(geometry, 28) creation and disposal used by the viewer.',
    'Cold initialization excludes file reading and JavaScript module imports; measurements use Node, not browser frames or GPU rendering.',
    'CAD outline timings cover all viewer wall/cladding/gable meshes; embedded image decoding is excluded from this geometry benchmark.',
    'Direct WASM timings exclude Worker registration, transfers, queueing and main-thread result application.',
    'These measurements describe this small house mesh only; they do not establish a speedup for larger CAD models.',
  ],
};
const json = `${JSON.stringify(report, null, 2)}\n`;
if (output) await writeFile(output, json, 'utf8');
process.stdout.write(json);
