import test from 'node:test';
import assert from 'node:assert/strict';
import { BoxGeometry, Color, Group, Mesh, MeshStandardMaterial } from 'three';
import { bindLandmarkMaterialLighting, landmarkLightRole, landmarkLocalLightLayout, landmarkLocalLightVisibility } from '../src/landmark-lighting.ts';

function fixture(t) {
  const root = new Group(), base = new Group(), decks = new Group(), antenna = new Group();
  root.add(base, decks, antenna);
  const shared = new MeshStandardMaterial({ color: '#b1532c' });
  const geometry = new BoxGeometry();
  const add = (parent, name) => { const mesh = new Mesh(geometry, shared); mesh.name = name; parent.add(mesh); return mesh; };
  const frame = add(root, 'structure:main_leg');
  const warm = add(base, 'base:entrance_light_lens');
  const red = add(antenna, 'antenna:obstruction_light_lens');
  let litName, darkName;
  for (let index = 0; index < 10; index++) {
    const name = `decks:main_glazing_${index}`;
    if (landmarkLightRole(name) === 'lit-window') litName ??= name;
    else darkName ??= name;
  }
  const lit = add(decks, litName), dark = add(decks, darkName);
  t.after(() => { geometry.dispose(); shared.dispose(); });
  return { root, base, decks, antenna, shared, frame, warm, red, lit, dark };
}

test('Tokyo lenses and selected windows glow without sharing emission with the steel frame', t => {
  const f = fixture(t), controller = bindLandmarkMaterialLighting(f.root, 'tokyo-tower');
  t.after(() => controller.dispose());
  const stats = controller.apply(true);
  assert.deepEqual(stats, { mode: 'local-fixtures', warmFixtures: 1, coolFixtures: 0, obstructionFixtures: 1, litWindows: 1 });
  assert.equal(f.frame.material, f.shared); assert.equal(f.dark.material, f.shared);
  assert.notEqual(f.warm.material, f.shared); assert.notEqual(f.lit.material, f.shared);
  assert.equal(f.shared.emissive.getHex(), 0);
  assert.equal(f.warm.material.emissive.getHexString(), new Color('#ffb064').getHexString());
  assert.equal(f.red.material.emissiveIntensity, 2.5);
});
test('hidden component groups cannot keep lens or window illumination active', t => {
  const f = fixture(t), controller = bindLandmarkMaterialLighting(f.root, 'tokyo-tower');
  t.after(() => controller.dispose());
  controller.apply(true); f.base.visible = false; f.antenna.visible = false;
  const stats = controller.apply(true);
  assert.equal(stats.warmFixtures, 0); assert.equal(stats.obstructionFixtures, 0); assert.equal(stats.litWindows, 1);
  assert.equal(f.warm.material.emissive.getHex(), 0); assert.equal(f.red.material.emissive.getHex(), 0);
  f.root.visible = false; assert.equal(controller.apply(true).litWindows, 0);
});
test('day mode restores original emission while preserving glass transparency and finish', t => {
  const f = fixture(t); f.shared.transparent = true; f.shared.opacity = .28; f.shared.roughness = .15;
  const controller = bindLandmarkMaterialLighting(f.root, 'tokyo-tower'); t.after(() => controller.dispose());
  controller.apply(true); controller.apply(false);
  assert.equal(f.lit.material.emissive.getHex(), 0); assert.equal(f.lit.material.emissiveIntensity, 1);
  assert.equal(f.lit.material.transparent, true); assert.equal(f.lit.material.opacity, .28); assert.equal(f.lit.material.roughness, .15);
});
test('Skytree uses blue-white local lenses and sparse windows without making its frame emissive', t => {
  const f = fixture(t), controller = bindLandmarkMaterialLighting(f.root, 'tokyo-skytree');
  t.after(() => controller.dispose());
  const stats = controller.apply(true);
  assert.deepEqual(stats, { mode: 'local-fixtures', warmFixtures: 0, coolFixtures: 1, obstructionFixtures: 1, litWindows: 1 });
  assert.equal(f.frame.material, f.shared); assert.equal(f.dark.material, f.shared);
  assert.notEqual(f.warm.material, f.shared); assert.notEqual(f.lit.material, f.shared);
  assert.equal(f.shared.emissive.getHex(), 0);
  assert.equal(f.warm.material.emissive.getHexString(), new Color('#b4e8ff').getHexString());
  assert.equal(f.lit.material.emissive.getHexString(), new Color('#c7edff').getHexString());
  f.decks.visible = false;
  assert.equal(controller.apply(true).litWindows, 0); assert.equal(f.lit.material.emissive.getHex(), 0);
  f.base.visible = false;
  assert.equal(controller.apply(true).coolFixtures, 0); assert.equal(f.warm.material.emissive.getHex(), 0);
  controller.apply(false);
  for (const mesh of [f.frame, f.warm, f.lit, f.red]) assert.equal(mesh.material.emissive.getHex(), 0);
});
for (const id of ['tokyo-tower', 'tokyo-skytree']) test(`${id}: owned finish clones are disposed once and original model materials are restored`, t => {
  const f = fixture(t), controller = bindLandmarkMaterialLighting(f.root, id);
  const clones = [f.warm.material, f.red.material, f.lit.material]; const events = new Map(clones.map(m => [m, 0]));
  for (const material of clones) material.addEventListener('dispose', () => events.set(material, events.get(material) + 1));
  let originalDisposals = 0; f.shared.addEventListener('dispose', () => originalDisposals++);
  controller.apply(true); controller.dispose(); controller.dispose();
  assert.ok([...events.values()].every(value => value === 1)); assert.equal(originalDisposals, 0);
  assert.equal(f.warm.material, f.shared); assert.equal(f.lit.material, f.shared);
});
test('local sources follow base/frame/deck visibility, readiness and scene time', () => {
  const visible = { base: true, structure: true, core: true, decks: true, antenna: true };
  assert.deepEqual(landmarkLocalLightVisibility('tokyo-tower', true, visible, true), { uplights: true, entry: true, decks: false });
  assert.deepEqual(landmarkLocalLightVisibility('tokyo-tower', true, { ...visible, structure: false }, true), { uplights: false, entry: true, decks: false });
  for (const state of [landmarkLocalLightVisibility('tokyo-tower', true, { ...visible, base: false }, true),
    landmarkLocalLightVisibility('tokyo-tower', false, visible, true), landmarkLocalLightVisibility('tokyo-tower', true, visible, false)]) {
    assert.deepEqual(state, { uplights: false, entry: false, decks: false });
  }
  assert.deepEqual(landmarkLocalLightVisibility('tokyo-skytree', true, visible, true), { uplights: true, entry: true, decks: true });
  assert.deepEqual(landmarkLocalLightVisibility('tokyo-skytree', true, { ...visible, base: false }, true), { uplights: false, entry: false, decks: true });
  assert.deepEqual(landmarkLocalLightVisibility('tokyo-skytree', true, { ...visible, decks: false }, true), { uplights: true, entry: true, decks: false });
  assert.deepEqual(landmarkLocalLightVisibility('tokyo-skytree', false, visible, true), { uplights: false, entry: false, decks: false });
  assert.deepEqual(landmarkLocalLightVisibility('tokyo-skytree', true, visible, false), { uplights: false, entry: false, decks: false });
});

test('each display light rig stays bounded and category masks disable every source at daytime', () => {
  const visible = { base: true, structure: true, core: true, decks: true, antenna: true };
  for (const id of ['tokyo-tower', 'tokyo-skytree']) {
    const specs = landmarkLocalLightLayout(id);
    assert.equal(specs.length, id === 'tokyo-tower' ? 5 : 6);
    const active = landmarkLocalLightVisibility(id, true, visible, true);
    assert.ok(specs.every(spec => active[spec.channel]));
    for (const spec of specs) {
      assert.ok(spec.position.every(Number.isFinite));
      assert.ok(spec.intensity > 0 && spec.distance > 0);
      if (spec.kind === 'spot') assert.ok(spec.target?.every(Number.isFinite));
    }
    for (const mask of [landmarkLocalLightVisibility(id, false, visible, true),
      landmarkLocalLightVisibility(id, true, Object.fromEntries(Object.keys(visible).map(key => [key, false])), true),
      landmarkLocalLightVisibility(id, true, visible, false)]) {
      assert.ok(specs.every(spec => !mask[spec.channel]));
    }
  }
});

test('explicit CAD mesh role supports materials whose display name lacks a lighting token', () => {
  assert.equal(landmarkLightRole('base:entrance_lens_01', 'light_lens'), 'warm-lens');
  assert.equal(landmarkLightRole('antenna:beacon_01', 'obstruction_light_lens'), 'obstruction-lens');
  assert.equal(landmarkLightRole('structure:painted_joint'), 'unlit');
});
