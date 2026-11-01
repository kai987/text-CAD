/** Offline display-geometry benchmark; never changes native GLB/CAD artifacts. */
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { performance } from 'node:perf_hooks';
import { loadGlbGeometry } from './glb-geometry.mjs';
import { batchLandmarkStairs } from '../src/landmark-stair-batches.ts';
import { batchLandmarkOpaque } from '../src/skytree-opaque-batches.ts';
import { landmarkVisibleGeometry } from '../src/landmark-render-stats.ts';

const root = fileURLToPath(new URL('../../', import.meta.url));
const args = process.argv.slice(2);
function option(name, fallback) {
  const index = args.indexOf(name);
  if (index === -1) return fallback;
  if (!args[index + 1] || args[index + 1].startsWith('--')) throw new Error(`Missing ${name} value`);
  return args[index + 1];
}
const samples = Number(option('--samples', '3'));
if (!Number.isInteger(samples) || samples < 1 || samples > 20) throw new Error('--samples must be 1–20');
const median = values => [...values].sort((a, b) => a - b)[Math.floor(values.length / 2)];
const models = [];
for (const id of ['tokyo-tower', 'tokyo-skytree']) {
  const path = `GLB/${id.replaceAll('-', '_')}.glb`, bytes = await readFile(resolve(root, path));
  const measurements = [];
  for (let i = 0; i < samples; i++) {
    const parseStarted = performance.now(), gltf = await loadGlbGeometry(bytes);
    const parseMs = performance.now() - parseStarted, scene = gltf.scene;
    const native = landmarkVisibleGeometry(scene);
    const stairs = batchLandmarkStairs(scene, id), withoutOpaque = landmarkVisibleGeometry(scene);
    const started = performance.now(), opaque = batchLandmarkOpaque(scene, id);
    const opaquePreparationMs = performance.now() - started, batched = landmarkVisibleGeometry(scene);
    if (native.triangles !== batched.triangles) throw new Error(`Triangle count changed: ${id}`);
    measurements.push({ parseMs, opaquePreparationMs, native, withoutOpaque, batched,
      sourceMeshes: opaque.sourceMeshes, drawBatches: opaque.drawBatches });
    opaque.dispose(); stairs.dispose();
    const geometries = new Set(), materials = new Set();
    scene.traverse(node => {
      if (!node.isMesh) return;
      geometries.add(node.geometry);
      for (const material of Array.isArray(node.material) ? node.material : [node.material]) materials.add(material);
    });
    geometries.forEach(geometry => geometry.dispose()); materials.forEach(material => material.dispose());
  }
  const first = measurements[0];
  const existing = id === 'tokyo-tower' ? first.withoutOpaque : first.batched;
  models.push({ id, path, sha256: createHash('sha256').update(bytes).digest('hex'), bytes: bytes.length,
    samples, nativeVisibleMeshes: first.native.meshes,
    existingVisibleSubmissions: existing.meshes, optimizedVisibleSubmissions: first.batched.meshes,
    savedSubmissions: existing.meshes - first.batched.meshes,
    opaqueSourceMeshes: first.sourceMeshes, opaqueDrawBatches: first.drawBatches,
    trianglesBefore: first.native.triangles, trianglesAfter: first.batched.triangles,
    medianOfflineParseMs: median(measurements.map(value => value.parseMs)),
    medianOpaquePreparationMs: median(measurements.map(value => value.opaquePreparationMs)),
  });
}
const report = { schemaVersion: 1, node: process.version, platform: `${process.platform}/${process.arch}`, models,
  scope: 'Offline CPU geometry preparation and visible mesh submissions before frustum culling. Texture decoding, network, GPU frame time and actual WebGL draw calls are excluded. Skytree already used opaque batches in R07.',
  browserMetrics: ['modelLoadMs', 'modelFirstFrameMs', 'modelTransferDecodeMs', 'modelParseMs', 'modelPreparationMs', 'opaquePreparationMs',
    'renderCalls', 'renderTriangles', 'renderCpuMs', 'renderGeometries', 'renderTextures', 'renderPrograms'],
  browserComparison: 'Use the same camera, viewport, micro mode, lighting and loaded revision. Compare ?renderBatching=off against the default. renderCpuMs is CPU submission time, not GPU time or FPS.',
};
const output = option('--output', null);
if (output) await writeFile(resolve(output), `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report, null, 2));
