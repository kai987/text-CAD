import test from 'node:test';
import assert from 'node:assert/strict';
import { Box3, BoxGeometry, Group, Mesh, MeshBasicMaterial, Vector3 } from 'three';
import { landmarkCloseupBounds, landmarkMainDeckBounds } from '../src/landmark-camera-bounds.ts';

test('main deck close-up excludes top_maintenance parts and unrelated main substrings', t => {
  const material = new MeshBasicMaterial(), geometries = [];
  t.after(() => { material.dispose(); geometries.forEach(geometry => geometry.dispose()); });
  const box = (name, y, width = 30, height = 1) => {
    const geometry = new BoxGeometry(width, height, width); geometries.push(geometry);
    const mesh = new Mesh(geometry, material); mesh.name = name; mesh.position.y = y; return mesh;
  };
  const nodes = new Map([
    ['decks:main_reference_floor', box('main floor', 149.5)],
    ['decks:main_roof', box('main roof', 156)],
    ['decks:top_maintenance_guard_0', box('top rail', 255)],
    ['decks:top_maintenance_post_0', box('top post', 254)],
    ['core:main_elevator_shaft', box('shaft', 180, 4, 200)],
  ]);
  const bounds = landmarkMainDeckBounds(nodes);
  assert.ok(bounds);
  assert.deepEqual(bounds.min.toArray(), [-17, 147, -17]);
  assert.deepEqual(bounds.max.toArray(), [17, 158.5, 17]);
});

test('Tokyo top-deck and spire close-ups retain their own named CAD range including side-mounted equipment', t => {
  const material = new MeshBasicMaterial(), geometry = new BoxGeometry(12, 2, 12);
  t.after(() => { material.dispose(); geometry.dispose(); });
  const box = y => { const mesh = new Mesh(geometry, material); mesh.position.y = y; return mesh; };
  const nodes = new Map([
    ['decks:main_reference_floor', box(125)],
    ['decks:top_reference_floor', box(223.55)],
    ['decks:top_maintenance_guard_0', box(228)],
    ['decks:machine_h13_floor', box(140)],
    ['antenna:digital_side_equipment', box(238)],
    ['antenna:mast_upper', box(333)],
    ['core:top_elevator_shaft', box(160)],
  ]);
  const full = new Box3(new Vector3(-45, -2, -45), new Vector3(45, 334, 45));
  const regions = landmarkCloseupBounds('tokyo-tower', nodes, full);
  assert.equal(regions.get('base').max.y, 80);
  assert.equal(regions.get('main-deck').getCenter(new Vector3()).y, 125);
  assert.equal(regions.get('top-deck').min.y, 220.55);
  assert.equal(regions.get('top-deck').max.y, 231);
  assert.equal(regions.get('spire').min.y, 235);
  assert.equal(regions.get('spire').max.y, 336);
  assert.equal(regions.has('tembo-deck'), false);
  assert.equal(full.max.y, 334, 'local camera fitting must not shift physical overall bounds');
});

test('Skytree close-ups retain the 375m deck equipment crown, upper gallery and complete gain envelope', t => {
  const material = new MeshBasicMaterial(), geometry = new BoxGeometry(30, 2, 30);
  t.after(() => { material.dispose(); geometry.dispose(); });
  const box = (y) => { const mesh = new Mesh(geometry, material); mesh.position.y = y; return mesh; };
  const nodes = new Map([
    ['decks:tembo_deck_floor', box(350)],
    ['decks:tembo_deck_equipment_crown', box(375)],
    ['decks:tembo_galleria_ramp_01', box(445)],
    ['decks:tembo_galleria_roof', box(450)],
    ['antenna:mast_upper', box(634)],
    ['antenna:gain_transition', box(497)],
    ['antenna:gain_tmd_cap', box(631)],
    ['decks:maintenance_above_tembo_deck', box(550)],
    ['core:tembo_deck_lift', box(200)],
  ]);
  const full = new Box3(new Vector3(-50, -3, -50), new Vector3(50, 635, 50));
  const regions = landmarkCloseupBounds('tokyo-skytree', nodes, full);
  assert.equal(regions.get('base').max.y, 100);
  assert.equal(regions.get('tembo-deck').getCenter(new Vector3()).y, 362.5);
  assert.equal(regions.get('tembo-deck').min.y, 347);
  assert.equal(regions.get('tembo-deck').max.y, 378);
  assert.equal(regions.get('tembo-galleria').getCenter(new Vector3()).y, 447.5);
  assert.equal(regions.get('tembo-galleria').min.y, 442);
  assert.equal(regions.get('tembo-galleria').max.y, 453);
  assert.equal(regions.get('spire').min.y, 494);
  assert.equal(regions.get('spire').max.y, 637);
  assert.equal(regions.has('main-deck'), false);
  assert.equal(full.max.y, 635, 'camera fitting must not mutate overall CAD bounds');
});

test('Skytree close-ups include parent transforms while ignoring named container groups', t => {
  const material = new MeshBasicMaterial(), geometry = new BoxGeometry(20, 2, 20);
  t.after(() => { material.dispose(); geometry.dispose(); });
  const root = new Group(); root.position.set(4, 300, -5); root.scale.set(2, 2, 2);
  const deck = new Mesh(geometry, material); deck.position.y = 25; root.add(deck);
  const gallery = new Mesh(geometry, material); gallery.position.y = 73.75; root.add(gallery);
  const antenna = new Mesh(geometry, material); antenna.position.y = 130; root.add(antenna);
  const nodes = new Map([
    ['decks:tembo_deck_container', root], ['decks:tembo_deck_glazing_01', deck],
    ['decks:tembo_galleria_glazing_01', gallery], ['antenna:mast', antenna],
  ]);
  const regions = landmarkCloseupBounds('tokyo-skytree', nodes, new Box3().setFromObject(root));
  assert.deepEqual(regions.get('tembo-deck').getCenter(new Vector3()).toArray(), [4, 350, -5]);
  assert.equal(regions.get('tembo-galleria').getCenter(new Vector3()).y, 447.5);
  assert.equal(regions.get('spire').getCenter(new Vector3()).y, 560);
  const missing = landmarkCloseupBounds('tokyo-skytree', new Map([['decks:tembo_deck_container', root]]), new Box3());
  assert.equal(missing.size, 0, 'a category name alone must not frame an unrelated model envelope');
});
test('close-up bounds account for parent transforms and do not use a main-named group envelope', t => {
  const geometry = new BoxGeometry(20, 2, 20), material = new MeshBasicMaterial();
  t.after(() => { geometry.dispose(); material.dispose(); });
  const parent = new Group(); parent.position.y = 150;
  const panel = new Mesh(geometry, material); parent.add(panel);
  const upper = new Mesh(geometry, material); upper.position.y = 100; parent.add(upper);
  const bounds = landmarkMainDeckBounds(new Map([['decks:main_group', parent], ['decks:main_glazing_01', panel], ['decks:top_maintenance_guard_1', upper]]));
  assert.ok(bounds); assert.equal(bounds.min.y, 147); assert.equal(bounds.max.y, 153);
  assert.equal(landmarkMainDeckBounds(new Map([['decks:top_maintenance_guard_1', upper]])), null);
});
