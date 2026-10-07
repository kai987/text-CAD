import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { Box3, Vector3 } from 'three';
import {
  cityNames, designCities, initialStructuralDesign, structuralCopy, structuralDesignUrl,
  structuralObjectVisible, structuralPaths, structuralSystems, systemNames,
} from '../src/structural-design.ts';
import { modelUrl, settingsForPreset, isolatePart } from '../src/model-state.ts';
import { cadComponentLabel } from '../src/cad-component-labels.ts';
import { bindCadNodes, centerModelAtFloorDatum, selectionFor } from '../src/model-scene.ts';
import { loadGlbGeometry } from './helpers/load-glb-geometry.mjs';
import { createHorizontalCap } from '../src/section-caps.ts';
import { createWasmHorizontalCap, initializeSectionCapsWasm } from '../src/section-caps-wasm.ts';

test('all twelve combinations round-trip with other view, section and theme URL inputs retained', () => {
  const current = 'https://example.com/text-CAD/?model=house&view=3d&mode=structure&section=wasm&theme=dark';
  for (const city of designCities) for (const system of structuralSystems) {
    const next = structuralDesignUrl(current, { city, system });
    assert.deepEqual(initialStructuralDesign(new URL(next).search), { city, system });
    for (const [key, value] of new URL(current).searchParams) assert.equal(new URL(next).searchParams.get(key), value);
    const plans = new URL(modelUrl(next, '1f', 'house'));
    assert.equal(plans.searchParams.get('city'), city);
    assert.equal(plans.searchParams.get('system'), system);
    assert.equal(plans.searchParams.get('mode'), 'structure');
    const paths = structuralPaths({ city, system });
    assert.equal(paths.glb, `GLB/structure_${system}.glb`);
    assert.equal(paths.case, `output/review/cases/${city}_${system}_R07.json`);
    const apartment = new URL(modelUrl(next, '3d', 'apartment'));
    assert.equal(apartment.searchParams.has('city'), false, 'house jurisdiction controls must not describe the apartment');
    assert.equal(apartment.searchParams.has('system'), false);
  }
  assert.deepEqual(initialStructuralDesign('?city=invalid&system=SRC'), { city: 'tokyo', system: 'W' });
});

test('localized concept copy and all added member kinds are available in Chinese, Japanese and English', () => {
  for (const locale of ['zh', 'ja', 'en']) {
    for (const value of [...Object.values(structuralCopy), ...Object.values(cityNames), ...Object.values(systemNames)]) {
      assert.ok(value[locale]?.trim(), locale);
    }
    for (const name of ['structure:F1:strap_brace_BW01_A', 'structure:F1:gusset_BW01_SW', 'structure:F1:base_plate_C01', 'structure:F1:shear_wall_SW01', 'structure:F1:slab_ground']) {
      const label = cadComponentLabel(locale, name);
      assert.ok(label?.trim());
      assert.ok(!label.includes('structure:'), 'stable native CAD IDs are not visible UI copy');
      if (locale !== 'en') assert.ok(!label.includes('ground'));
    }
  }
});

test('cut heights and isolation control the chosen overlay categories without restoring the original foundation', () => {
  const settings = settingsForPreset('structure');
  assert.equal(structuralObjectVisible('structure:columns', settings), true);
  assert.equal(structuralObjectVisible('foundation:raft', settings), true);
  assert.equal(structuralObjectVisible('F1:floor_slab', settings), false);
  const cut = { ...settings, cutaway: true, heightMm: 3700 };
  assert.equal(structuralObjectVisible('structure:columns', cut), true);
  const isolated = isolatePart(cut, 'foundation:raft');
  assert.equal(structuralObjectVisible('foundation:raft', isolated), true);
  assert.equal(structuralObjectVisible('structure:columns', isolated), false);
  assert.equal(structuralObjectVisible('foundation:stem_walls', isolated), false);
});

test('all variant solids remain selectable and use the architectural CAD datum without per-model recentering', async () => {
  const house = await loadGlbGeometry(new URL('../../GLB/house_3d.glb', import.meta.url));
  const houseNodes = bindCadNodes(house);
  assert.equal(centerModelAtFloorDatum(house.scene, houseNodes), true);
  const shift = house.scene.position.clone();
  const signatures = new Set();
  for (const system of structuralSystems) {
    const gltf = await loadGlbGeometry(new URL(`../../GLB/structure_${system}.glb`, import.meta.url));
    const nodes = bindCadNodes(gltf);
    assert.ok(nodes.get('structure') && nodes.get('foundation'), system);
    const originalBounds = new Box3().setFromObject(gltf.scene);
    house.scene.add(gltf.scene);
    const placedBounds = new Box3().setFromObject(gltf.scene);
    assert.ok(placedBounds.min.distanceTo(originalBounds.min.clone().add(shift)) < 1e-6, system);
    assert.ok(placedBounds.max.distanceTo(originalBounds.max.clone().add(shift)) < 1e-6, system);
    const memberNames = [];
    for (const [name, object] of nodes) {
      if (!object.isMesh) continue;
      const selection = selectionFor(object);
      assert.ok(selection, `${system}: ${name} is selectable`);
      assert.ok(selection.id.startsWith('structure:') || selection.id.startsWith('foundation:'), name);
      for (const locale of ['zh', 'ja', 'en']) {
        const label = cadComponentLabel(locale, name);
        assert.ok(label?.trim(), `${system} ${locale}: ${name} has a visible component label`);
        assert.ok(!label.includes('structure:') && !label.includes('foundation:'), name);
        if (locale !== 'en') assert.ok(!/\bground\b|\bstorage\b|\bperimeter\b|gable_shear/.test(label), `${locale}: internal English suffixes must be translated`);
      }
      memberNames.push(name);
    }
    assert.ok(memberNames.length > 20, system);
    signatures.add(memberNames.sort().join('|'));
    house.scene.remove(gltf.scene);
  }
  assert.equal(signatures.size, 3, 'W, S and RC must be distinct named structural schemes');
});

test('real S and RC sections preserve the steel core, stairwell and attic hatch in both section engines', async () => {
  await initializeSectionCapsWasm(await readFile(new URL('../src/wasm/section_caps_bg.wasm', import.meta.url)));
  const steel = await loadGlbGeometry(new URL('../../GLB/structure_S.glb', import.meta.url));
  const concrete = await loadGlbGeometry(new URL('../../GLB/structure_RC.glb', import.meta.url));
  const steelNodes = bindCadNodes(steel), rcNodes = bindCadNodes(concrete);
  const examples = [
    { name: 'structure:F1:column_C01', mesh: steelNodes.get('structure:F1:column_C01'), height: 1.4, empty: { x: 8.19-.09, z: -.09 }, area: .12 ** 2 - (.12 - 2 * .0023) ** 2 },
    { name: 'structure:F2:slab_floor', mesh: rcNodes.get('structure:F2:slab_floor'), height: 2.7, empty: { x: 8.19-7.06, z: -5.74 } },
    { name: 'structure:attic:slab_storage', mesh: rcNodes.get('structure:attic:slab_storage'), height: 5.5, empty: { x: 8.19-4.7, z: -3.83 } },
  ];
  function inspect(mesh, geometry, point) {
    const positions = geometry.getAttribute('position');
    let area = 0;
    for (let i = 0; i < positions.count; i += 3) {
      const triangle = [0, 1, 2].map(offset => new Vector3().fromBufferAttribute(positions, i + offset).applyMatrix4(mesh.matrixWorld));
      const signs = triangle.map((a, j) => {
        const b = triangle[(j + 1) % 3];
        return (b.x - a.x) * (point.z - a.z) - (b.z - a.z) * (point.x - a.x);
      });
      assert.ok(!signs.every(value => value <= 1e-10) && !signs.every(value => value >= -1e-10), 'section triangles must retain the actual hollow/opening centre');
      const cross = new Vector3().subVectors(triangle[1], triangle[0]).cross(new Vector3().subVectors(triangle[2], triangle[0]));
      assert.ok(cross.y > 0, 'sections face upward'); area += cross.y / 2;
    }
    return area;
  }
  for (const example of examples) {
    assert.ok(example.mesh?.isMesh, example.name);
    let previousArea;
    for (const create of [createHorizontalCap, createWasmHorizontalCap]) {
      const cap = create(example.mesh, example.height);
      assert.ok(cap, example.name);
      try {
        const area = inspect(example.mesh, cap, example.empty);
        assert.ok(area > 0, example.name);
        if (example.area) assert.ok(Math.abs(area - example.area) < 2e-6, 'steel cross-section area excludes its inner core');
        if (previousArea !== undefined) assert.ok(Math.abs(area - previousArea) < 2e-5, 'TS/WASM cap parity');
        previousArea = area;
      } finally { cap.dispose(); }
    }
  }
});
