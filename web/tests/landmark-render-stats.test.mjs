import test from 'node:test';
import assert from 'node:assert/strict';
import { BoxGeometry, Group, Mesh, MeshStandardMaterial } from 'three';
import { landmarkPickableMeshes, landmarkVisibleGeometry } from '../src/landmark-render-stats.ts';

test('geometry statistics and picking skip hidden original meshes and hidden parents', () => {
  const root = new Group(), parent = new Group(), geometry = new BoxGeometry(), material = new MeshStandardMaterial();
  const shown = new Mesh(geometry, material), hidden = new Mesh(geometry, material), child = new Mesh(geometry, material);
  hidden.visible = false; parent.visible = false; parent.add(child); root.add(shown, hidden, parent);
  try {
    assert.deepEqual(landmarkPickableMeshes(root), [shown]);
    assert.deepEqual(landmarkVisibleGeometry(root), { meshes: 1, triangles: 12 });
    material.visible = false;
    assert.deepEqual(landmarkPickableMeshes(root), []);
    assert.deepEqual(landmarkVisibleGeometry(root), { meshes: 0, triangles: 0 });
  } finally { geometry.dispose(); material.dispose(); }
});
