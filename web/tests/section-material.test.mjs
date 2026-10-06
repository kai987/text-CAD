import test from 'node:test';
import assert from 'node:assert/strict';
import { BoxGeometry, FrontSide, Mesh, MeshPhysicalMaterial, MeshStandardMaterial, Plane, Texture, Vector3 } from 'three';
import { createHorizontalCap, createSectionMaterial } from '../src/section-caps.ts';

test('untextured section materials preserve PBR and clipping without mutating or disposing shared texture maps', () => {
  const texture = new Texture();
  let textureDisposals = 0;
  texture.addEventListener('dispose', () => textureDisposals++);
  const source = new MeshPhysicalMaterial({ color: '#d4ccbf', roughness: .88, metalness: .12,
    emissive: '#80520d', emissiveIntensity: .25, clearcoat: .35, clearcoatRoughness: .7,
    side: FrontSide, polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1,
    clippingPlanes: [new Plane(new Vector3(0, -1, 0), 1.8)], clipIntersection: true, clipShadows: true });
  // Include every exposed standard/physical map slot, not only base colour.
  const slots = Object.keys(source).filter(key => key === 'map' || key.endsWith('Map'));
  assert.ok(slots.includes('map') && slots.includes('normalMap') && slots.includes('roughnessMap'));
  assert.ok(slots.includes('clearcoatMap'), 'physical material extensions are covered');
  slots.forEach(key => { source[key] = texture; });
  const cap = createSectionMaterial(source);
  assert.notEqual(cap, source, 'cap owns a separate material');
  assert.ok(cap instanceof MeshPhysicalMaterial, 'PBR material type is preserved');
  for (const key of slots) {
    assert.equal(cap[key], null, `${key}: cap does not depend on UVs`);
    assert.equal(source[key], texture, `${key}: exterior keeps its texture`);
  }
  for (const key of ['roughness', 'metalness', 'emissiveIntensity', 'clearcoat', 'clearcoatRoughness',
    'side', 'polygonOffset', 'polygonOffsetFactor', 'polygonOffsetUnits', 'clipIntersection', 'clipShadows']) {
    assert.equal(cap[key], source[key], `preserved ${key}`);
  }
  assert.ok(cap.color.equals(source.color));
  assert.ok(cap.emissive.equals(source.emissive));
  assert.deepEqual(cap.clippingPlanes, source.clippingPlanes, 'clipping plane values are retained');
  cap.color.set('#000000');
  assert.notEqual(cap.color.getHex(), source.color.getHex(), 'cap edits do not mutate source colour');
  cap.clippingPlanes[0].constant = 2.1;
  assert.equal(source.clippingPlanes[0].constant, 1.8, 'cap edits do not mutate source clipping');
  cap.dispose(); source.dispose();
  assert.equal(textureDisposals, 0, 'creating/replacing caps never disposes shared textures');
  texture.dispose();
});

test('actual UV-free cap geometry can retain selection colour without an inherited exterior texture', () => {
  const texture = new Texture(), source = new MeshStandardMaterial({ color: '#eeeadf', map: texture, roughness: .88 });
  const mesh = new Mesh(new BoxGeometry(1, 2, .02), source);
  const geometry = createHorizontalCap(mesh, 0);
  assert.ok(geometry && !geometry.getAttribute('uv'), 'actual generated section has no surface UV');
  const highlighted = source.clone();
  highlighted.color.set('#e7aa37'); highlighted.emissive.set('#80520d'); highlighted.emissiveIntensity = .25;
  const cap = createSectionMaterial(highlighted);
  assert.equal(cap.map, null);
  assert.equal(cap.color.getHexString(), 'e7aa37');
  assert.equal(cap.emissive.getHexString(), '80520d');
  assert.equal(cap.emissiveIntensity, .25);
  assert.equal(cap.roughness, .88);
  assert.equal(highlighted.map, texture, 'selection keeps the original facade texture');
  assert.equal(source.map, texture, 'original facade is unchanged');
  cap.dispose(); highlighted.dispose(); source.dispose(); geometry.dispose(); mesh.geometry.dispose(); texture.dispose();
});
