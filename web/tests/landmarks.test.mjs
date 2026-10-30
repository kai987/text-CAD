import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { Box3, OrthographicCamera, Vector3 } from 'three';
import { bindCadNodes, isObjectVisible } from '../src/model-scene.ts';
import { bindLandmarkMaterialLighting, landmarkLightRole, landmarkLocalLightLayout } from '../src/landmark-lighting.ts';
import { batchLandmarkStairs } from '../src/landmark-stair-batches.ts';
import { landmarkCloseupBounds, landmarkMainDeckBounds } from '../src/landmark-camera-bounds.ts';
import { bindLandmarkSteelDetails, readLandmarkSteelNodes } from '../src/landmark-steel-nodes.ts';
import { initialLandmarkView, isLandmarkId, landmarkCameraOptions, landmarkCameras, landmarkCopy, landmarkDetailCameras, landmarkDownloadFiles, landmarkGroupForName, landmarkGroupIds, landmarkIds, landmarkModels, landmarkUrl, landmarkViews } from '../src/landmark-copy.ts';

test('landmark navigation accepts only catalog IDs and keeps the hosting base and day/night choice', () => {
  for (const base of ['http://127.0.0.1:4199/text-CAD/', 'https://kai987.github.io/text-CAD/', 'https://example.chatgpt.site/']) {
    for (const model of landmarkIds) for (const view of landmarkViews) {
      const next = new URL(landmarkUrl(`${base}?model=house&view=2f&mode=attic&city=kyoto&system=RC&environment=night`, model, view));
      assert.equal(next.pathname, new URL(base).pathname);
      assert.equal(next.searchParams.get('model'), model); assert.equal(next.searchParams.get('view'), view);
      assert.equal(next.searchParams.get('environment'), 'night');
      for (const residential of ['mode', 'city', 'system']) assert.equal(next.searchParams.has(residential), false);
      assert.equal(initialLandmarkView(next.search), view);
    }
  }
  for (const invalid of [null, undefined, '', '__proto__', 'house', 'TokyoTower', 1, {}]) assert.equal(isLandmarkId(invalid), false);
  for (const model of landmarkIds) assert.equal(isLandmarkId(model), true);
  assert.equal(initialLandmarkView('?view=1f'), 'plan');
  assert.equal(initialLandmarkView('?view=2f'), 'plan');
  assert.equal(initialLandmarkView('?view=unknown'), '3d');
});

test('landmark controls and downloads have complete Chinese, Japanese and English copy', () => {
  for (const locale of ['zh', 'ja', 'en']) {
    const copy = landmarkCopy[locale];
    for (const view of landmarkViews) assert.ok(copy.tabs[view]?.trim());
    for (const camera of landmarkCameras) assert.ok(copy.views[camera]?.trim());
    for (const camera of landmarkDetailCameras) assert.ok(copy.views[camera]?.trim());
    for (const group of landmarkGroupIds) assert.ok(copy.groups[group]?.trim());
    for (const mode of ['auto', 'on', 'off']) assert.ok(copy.steel.modes[mode]?.trim());
    assert.ok(copy.steel.note.length > 40); assert.ok(copy.steel.focus.trim()); assert.ok(copy.views['steel-node'].trim());
    for (const key of ['modelGlLevels', 'nominalLevels', 'constructionSource', 'glReferenceNote']) assert.ok(copy[key]?.trim());
    for (const model of landmarkIds) {
      assert.ok(landmarkModels[model].names[locale]?.trim());
      assert.ok(landmarkModels[model].assumptionNotes[locale].length > 100);
      for (const file of landmarkDownloadFiles(model)) {
        assert.ok(copy.fileNames[file.id]?.trim()); assert.ok(copy.fileDetails[file.id]?.trim());
      }
    }
    assert.ok(copy.note.length > 40); assert.ok(copy.drawingNote.length > 30);
  }
  assert.equal(landmarkGroupForName('structure:leg_01_01'), 'structure');
  assert.equal(landmarkGroupForName('decks:main_deck_glass'), 'decks');
  assert.equal(landmarkGroupForName('TokyoTower'), null);
  assert.equal(landmarkGroupForName('substructure'), null);
  assert.deepEqual(landmarkCameraOptions('tokyo-skytree'), [...landmarkCameras, 'base', 'tembo-deck', 'tembo-galleria', 'spire']);
  assert.deepEqual(landmarkCameraOptions('tokyo-tower'), [...landmarkCameras, 'base', 'main-deck', 'top-deck', 'spire']);
  assert.equal(landmarkDownloadFiles('tokyo-tower').length, 7);
  assert.equal(landmarkDownloadFiles('tokyo-skytree').length, 7);
  assert.equal(landmarkDownloadFiles('tokyo-skytree').some(file => file.id === 'steelNodes'), false);
  assert.equal(landmarkDownloadFiles('tokyo-skytree').find(file => file.id === 'structureZones').path,'DXF/tokyo_skytree_structure_zones.dxf');
  assert.equal(landmarkModels['tokyo-skytree'].revision, 'LANDMARK-R04');
  assert.equal(landmarkModels['tokyo-tower'].revision, 'LANDMARK-R06');
  assert.match(landmarkModels['tokyo-tower'].assumptionNotes.en, /JAEE 1962.*H11.*27 m square.*H12.*28 m square.*H23.*13 m diameter circle/);
  assert.match(landmarkModels['tokyo-tower'].assumptionNotes.en, /historical 29 × 24 m H13 plan.*separately.*use and mapping.*current envelope.*unverified/);
  assert.match(landmarkModels['tokyo-tower'].assumptionNotes.en, /retrofit appearance.*shell thickness.*glazing divisions.*display approximations/);
  const tokyoNotes = landmarkModels['tokyo-tower'].assumptionNotes;
  assert.match(tokyoNotes.zh, /48面.*H24圆形设备平台.*两组红白圆形天线阵列.*2012年Fig\.5.*300片.*当前用途尚未核定/);
  assert.match(tokyoNotes.ja, /48面.*H24.*円形設備床.*2012年Fig\.5.*円形アンテナ2組.*300枚.*現在の用途は未確認/);
  assert.match(tokyoNotes.en, /48 facets.*circular H24 equipment platform.*Two red-and-white circular antenna banks.*2012 Fig\.5.*300 panels.*current uses remain unverified/);
  assert.match(tokyoNotes.en, /H23 at GL223\.55 m.*structural-band\/roof reference.*visitor finished floor has not been surveyed/);
  assert.match(landmarkModels['tokyo-skytree'].assumptionNotes.en, /Three four-column clusters.*model GL 0–50 m base-connection zone.*12\.5\/25 m ring/);
  assert.match(landmarkModels['tokyo-skytree'].assumptionNotes.en, /display approximations.*not a member-for-member reconstruction/);
  const skytreeNotes = landmarkModels['tokyo-skytree'].assumptionNotes;
  assert.match(skytreeNotes.zh, /公开资料.*340\/345\/350.*375 m设备屋顶高度.*71°/);
  assert.match(skytreeNotes.zh, /24点.*设备冠半径与分段截面.*模型拟合近似.*非竣工实测.*375 m不是展望楼层/);
  assert.match(skytreeNotes.ja, /公開資料.*340\/345\/350.*375 mの設備屋上高さ.*71°/);
  assert.match(skytreeNotes.ja, /24点.*設備冠の半径と分節断面.*形状合わせ.*竣工実測ではありません.*375 mは展望フロアではありません/);
  assert.match(skytreeNotes.en, /Published controls.*340\/345\/350.*375 m equipment-roof height.*71°/);
  assert.match(skytreeNotes.en, /24 contour samples.*unpublished equipment stations.*model-fit approximations, not surveyed as-built geometry; 375 m is not an observation floor/);
  assert.deepEqual(landmarkModels['tokyo-skytree'].levels, [350000, 450000]);
  assert.deepEqual(landmarkModels['tokyo-tower'].levels, [125000, 223550]);
  assert.deepEqual(landmarkModels['tokyo-tower'].nominalLevels, [150000, 250000]);
  assert.match(landmarkCopy.en.glReferenceNote, /JAEE 1962.*Miyaji.*retains.*120\/125/);
  assert.match(landmarkCopy.en.glReferenceNote, /150 m\/250 m.*no verified conversion/);
  assert.match(landmarkCopy.en.steel.note, /approximation.*published elevations.*construction photographs/);
});

for (const id of landmarkIds) {
  test(`${id}: real exported model supports the named visibility categories at tower scale`, async t => {
    const model = landmarkModels[id];
    const bytes = await readFile(new URL(`../../GLB/${model.stem}.glb`, import.meta.url));
    const gltf = await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '');
    t.after(() => {
      const materials = new Set(), geometries = new Set();
      gltf.scene.traverse(node => { if (node.isMesh) { geometries.add(node.geometry); for (const material of Array.isArray(node.material) ? node.material : [node.material]) materials.add(material); } });
      geometries.forEach(geometry => geometry.dispose()); materials.forEach(material => material.dispose());
    });
    const nodes = bindCadNodes(gltf);
    for (const category of landmarkGroupIds) {
      const node = nodes.get(category); assert.ok(node, `Missing named group: ${category}`);
      let mesh; node.traverse(child => { if (child.isMesh) mesh ??= child; });
      assert.ok(mesh, `No rendered geometry in ${category}`); assert.equal(isObjectVisible(mesh), true);
      node.visible = false; assert.equal(isObjectVisible(mesh), false); node.visible = true; assert.equal(isObjectVisible(mesh), true);
    }
    const bounds = new Box3().setFromObject(gltf.scene);
    assert.ok(bounds.max.y > model.height / 1000 * .98 && bounds.max.y < model.height / 1000 * 1.02, 'GLB is metres, Y-up and has the expected tower height');
    const manifest = JSON.parse(await readFile(new URL(`../../output/review/${model.stem}_manifest.json`, import.meta.url), 'utf8'));
    assert.equal(manifest.id, id); assert.equal(manifest.height_mm, model.height);
    assert.equal(manifest.revision, model.revision);
    assert.equal(gltf.parser.json.asset.extras.revision, model.revision);
    if (id === 'tokyo-tower') {
      const catalog = readLandmarkSteelNodes(gltf.parser.json.asset.extras.steelNodes);
      assert.equal(catalog.length, 20);
      assert.deepEqual(gltf.parser.json.asset.extras.steelNodes, manifest.steel_nodes, 'viewer catalog must match the downloadable CAD manifest');
      const microForEntry = entry => entry.part_names.map(name => nodes.get(name)).filter(node => node?.isMesh
        && node.userData.steelMicro === true && node.userData.steelDetailKind === 'rivet' && node.userData.landmarkRole === 'rivet_head');
      const expectedMicroCount = catalog.reduce((count, entry) => count + microForEntry(entry).length, 0);
      assert.equal(expectedMicroCount, 248, 'all existing named rivet heads remain in the actual exported catalog');
      const details = bindLandmarkSteelDetails(nodes, catalog, gltf.scene);
      try {
        const camera = new OrthographicCamera(-300, 300, 300, -300, .1, 3000);
        camera.position.set(500, 300, 500); camera.lookAt(0, 150, 0); camera.updateProjectionMatrix();
        assert.deepEqual(details.apply(camera, 'auto'), { microMeshes: expectedMicroCount, visibleMicroMeshes: 0 });
        for (const entry of catalog) {
          const rawEntry = manifest.steel_nodes.find(node => node.id === entry.id), b = rawEntry.bounds_mm;
          const location = rawEntry.local_frame?.origin_mm ?? entry.anchor_mm;
          const region = details.bounds(entry.id), origin = new Vector3(location[0], location[2], -location[1]).divideScalar(1000);
          assert.ok(region && Array.isArray(b) && b.length === 6 && b.every(Number.isFinite));
          const declared = new Box3(new Vector3(b[0], b[2], -b[4]).divideScalar(1000), new Vector3(b[3], b[5], -b[1]).divideScalar(1000)).expandByScalar(1);
          assert.ok(region.min.distanceTo(declared.min) < .01 && region.max.distanceTo(declared.max) < .01,
            `${entry.id}: close-up uses the declared local CAD parts rather than full-length referenced members`);
          assert.ok(region.containsPoint(origin), `${entry.id}: close-up contains its local CAD connection origin after Y-up conversion`);
          for (const name of entry.part_names) assert.equal(nodes.get(name).userData.steelNodeId, entry.id);
          const center = region.getCenter(new Vector3());
          camera.left = -4; camera.right = 4; camera.top = 4; camera.bottom = -4; camera.zoom = 1;
          camera.position.copy(center).addScaledVector(details.direction(entry.id), 30); camera.lookAt(center); camera.updateProjectionMatrix();
          details.apply(camera, 'auto');
          assert.ok(microForEntry(entry).every(node => isObjectVisible(node)), `${entry.id}: every original rivet in this connection appears in close-up`);
        }
        nodes.get('structure').visible = false;
        assert.equal(details.apply(camera, 'on').visibleMicroMeshes, 0, 'manual rivets cannot override the hidden lattice category');
        nodes.get('structure').visible = true;
        assert.equal(details.apply(camera, 'on').visibleMicroMeshes, expectedMicroCount);
        assert.equal(details.apply(camera, 'off').visibleMicroMeshes, 0);
      } finally { details.dispose(); }
      const mainDeck = landmarkMainDeckBounds(nodes);
      assert.ok(mainDeck && mainDeck.min.y > 110 && mainDeck.max.y < 145,
        'the interpreted GL120/125m main-deck close-up must not include GL223.55m top-deck parts');
      const regions = landmarkCloseupBounds(id, nodes, bounds);
      const topDeck = regions.get('top-deck'), spire = regions.get('spire');
      const namedBounds = prefix => {
        const region = new Box3();
        for (const [name, node] of nodes) if (node.isMesh && name.startsWith(prefix)) region.expandByObject(node);
        return region.expandByScalar(2);
      };
      for (const [region, prefix] of [[topDeck, 'decks:top_'], [spire, 'antenna:']]) {
        const actual = namedBounds(prefix);
        assert.ok(region && region.min.distanceTo(actual.min) < 1e-6 && region.max.distanceTo(actual.max) < 1e-6,
          `${prefix}: close-up must retain the complete physical CAD range`);
      }
      assert.ok(topDeck.getCenter(new Vector3()).y > 215 && topDeck.getCenter(new Vector3()).y < 235,
        'the top-deck camera remains near its model GL223.55m geometry');
      assert.ok(spire.min.y > 225 && spire.min.y < 242 && spire.max.y > 332,
        'the spire region includes the side-mounted digital equipment near 238m and the full 333m tip');
      const stairs = batchLandmarkStairs(gltf.scene, id);
      const lights = bindLandmarkMaterialLighting(gltf.scene, id);
      try {
        assert.equal(stairs.sourceMeshes, 600, 'every named external stair tread is retained by the display batch');
        assert.ok(stairs.drawBatches > 0 && stairs.drawBatches < 10, '600 treads use a bounded number of display draws');
        const after = new Box3().setFromObject(gltf.scene);
        assert.ok(after.min.distanceTo(bounds.min) < 1e-4 && after.max.distanceTo(bounds.max) < 1e-4);
        const lit = lights.apply(true);
        const meshes = [...nodes.values()].filter(node => node.isMesh);
        const countRole = role => meshes.filter(node => node.userData.landmarkRole === role).length;
        assert.ok(countRole('light_lens') > 0 && countRole('obstruction_light_lens') > 0);
        assert.equal(lit.warmFixtures, countRole('light_lens')); assert.equal(lit.obstructionFixtures, countRole('obstruction_light_lens'));
        const visibleLitWindows = () => meshes.filter(node => isObjectVisible(node)
          && landmarkLightRole(String(node.userData.cadName ?? node.name), node.userData.landmarkRole) === 'lit-window').length;
        assert.ok(lit.litWindows > 0 && lit.litWindows < countRole('glazing'), 'a sparse subset of windows receives local warm light');
        assert.equal(lit.litWindows, visibleLitWindows(), 'night glass count comes from actual named CAD metadata');
        nodes.get('decks').visible = false;
        assert.equal(lights.apply(true).litWindows, visibleLitWindows(), 'hidden main and top glazing cannot remain lit');
        nodes.get('decks').visible = true;
        assert.equal(lights.apply(true).litWindows, visibleLitWindows(), 'restored deck glazing returns to its named local-light selection');
        nodes.get('base').visible = false;
        assert.equal(lights.apply(true).warmFixtures, 0, 'hidden base fixtures cannot stay lit');
        nodes.get('base').visible = true;
        const day = lights.apply(false);
        assert.equal(day.warmFixtures + day.obstructionFixtures + day.litWindows, 0);
      } finally { lights.dispose(); stairs.dispose(); }
    } else {
      const regions = landmarkCloseupBounds(id, nodes, bounds);
      const deck = regions.get('tembo-deck'), gallery = regions.get('tembo-galleria'), spire = regions.get('spire');
      assert.equal(regions.get('base').max.y, 100);
      const namedBounds = prefix => {
        const region = new Box3();
        for (const [name, node] of nodes) if (node.isMesh && name.startsWith(prefix)) region.expandByObject(node);
        return region.expandByScalar(2);
      };
      for (const [region, prefix] of [[deck, 'decks:tembo_deck_'], [gallery, 'decks:tembo_galleria_'], [spire, 'antenna:']]) {
        const actual = namedBounds(prefix);
        assert.ok(region && region.min.distanceTo(actual.min) < 1e-6 && region.max.distanceTo(actual.max) < 1e-6,
          `${prefix}: close-up must retain every actual CAD part, including equipment outside the main facade`);
      }
      assert.ok(deck && deck.min.y > 310 && deck.max.y > 374 && deck.max.y < 382 && deck.getCenter(new Vector3()).y > 340 && deck.getCenter(new Vector3()).y < 375,
        'the 350m deck target includes its approximately 375m equipment crown while excluding the upper gallery and continuous lift core');
      assert.ok(gallery && gallery.min.y > 430 && gallery.max.y < 470 && gallery.getCenter(new Vector3()).y > 445 && gallery.getCenter(new Vector3()).y < 455,
        'the upper gallery target must stay at the 445-450m route');
      assert.ok(spire && spire.min.y > 490 && spire.min.y < 500 && spire.max.y < 640,
        'the spire close-up includes the approximately 497m transition, segmented antenna equipment and terminal cap');
      let fixtureCount = 0, beaconCount = 0, glazingCount = 0, frame;
      const fixturePositions = [];
      const originalGlazingEmission = new Map();
      for (const [name, node] of nodes) {
        if (!node.isMesh) continue;
        const role = node.userData.landmarkRole;
        if (role === 'light_lens') { fixtureCount++; fixturePositions.push(new Box3().setFromObject(node).getCenter(new Vector3())); }
        if (role === 'obstruction_light_lens') beaconCount++;
        if (role === 'glazing') {
          glazingCount++;
          const materials = Array.isArray(node.material) ? node.material : [node.material];
          originalGlazingEmission.set(node, materials.map(material => ({ color: material.emissive.getHex(), intensity: material.emissiveIntensity })));
        }
        if (name.startsWith('structure:')) frame ??= node;
        if (role === 'light_lens' || role === 'obstruction_light_lens') {
          const materials = Array.isArray(node.material) ? node.material : [node.material];
          assert.ok(materials.every(material => material.emissiveIntensity === 0 || material.emissive.getHex() === 0),
            'downloaded daylight CAD must not bake night emission into a lens');
        }
      }
      assert.ok(fixtureCount > 0 && beaconCount > 0 && glazingCount > 0 && frame);
      for (const spec of landmarkLocalLightLayout(id).filter(light => light.channel === 'uplights')) {
        assert.ok(fixturePositions.some(center => center.distanceTo(new Vector3().fromArray(spec.position)) < .1),
          'display uplights must sit at exported plaza lenses rather than an unrelated proxy position');
      }
      const originalFrameMaterial = frame.material;
      const originalFrameEmission = (Array.isArray(frame.material) ? frame.material : [frame.material])
        .map(material => ({ color: material.emissive.getHex(), intensity: material.emissiveIntensity }));
      const visibleLightCount = role => [...nodes.values()].filter(node => node.isMesh && isObjectVisible(node)
        && landmarkLightRole(String(node.userData.cadName ?? node.name), node.userData.landmarkRole) === role)
        .reduce((count, node) => count + (Array.isArray(node.material) ? node.material : [node.material])
          .filter(material => material.isMeshStandardMaterial).length, 0);
      const lights = bindLandmarkMaterialLighting(gltf.scene, id);
      try {
        const lit = lights.apply(true);
        assert.equal(lit.mode, 'local-fixtures'); assert.equal(lit.coolFixtures, fixtureCount); assert.equal(lit.warmFixtures, 0);
        assert.equal(lit.obstructionFixtures, beaconCount);
        assert.ok(lit.litWindows > 0 && lit.litWindows < glazingCount, 'only a sparse subset of glass receives local night light');
        assert.equal(lit.litWindows, visibleLightCount('lit-window'), 'window lighting follows the current exported pane metadata');
        assert.equal(frame.material, originalFrameMaterial, 'night light cannot replace shared tower frame materials');
        const materials = Array.isArray(frame.material) ? frame.material : [frame.material];
        assert.deepEqual(materials.map(material => ({ color: material.emissive.getHex(), intensity: material.emissiveIntensity })),
          originalFrameEmission, 'night light must preserve the downloaded steel material emission');
        for (const group of ['structure', 'decks', 'antenna']) {
          nodes.get(group).visible = false;
          const remaining = lights.apply(true);
          assert.equal(remaining.obstructionFixtures, visibleLightCount('obstruction-lens'), `${group}: hidden obstruction lenses cannot stay lit`);
          assert.equal(remaining.litWindows, visibleLightCount('lit-window'), `${group}: hidden glazing cannot stay lit`);
          nodes.get(group).visible = true;
        }
        nodes.get('base').visible = false;
        assert.equal(lights.apply(true).coolFixtures, 0, 'hidden base fixtures cannot stay lit');
        nodes.get('base').visible = true; nodes.get('decks').visible = false;
        const remainingWindows = [...nodes.values()].filter(node => node.isMesh && isObjectVisible(node)
          && landmarkLightRole(String(node.userData.cadName ?? node.name), node.userData.landmarkRole) === 'lit-window').length;
        assert.ok(remainingWindows > 0, 'visible entrance glazing keeps its independent night illumination');
        assert.equal(lights.apply(true).litWindows, remainingWindows, 'only still-visible windows may remain lit');
        nodes.get('decks').traverse(node => {
          if (!node.isMesh || node.userData.landmarkRole !== 'glazing') return;
          const materials = Array.isArray(node.material) ? node.material : [node.material];
          assert.deepEqual(materials.map(material => ({ color: material.emissive.getHex(), intensity: material.emissiveIntensity })),
            originalGlazingEmission.get(node), 'every hidden deck pane returns to its original daylight emission');
        });
        nodes.get('decks').visible = true;
        const day = lights.apply(false);
        assert.equal(day.coolFixtures + day.warmFixtures + day.obstructionFixtures + day.litWindows, 0);
      } finally { lights.dispose(); }
    }
    for (const file of landmarkDownloadFiles(id)) assert.ok((await readFile(new URL(`../../${file.path}`, import.meta.url))).length > 0, file.path);
  });
}
