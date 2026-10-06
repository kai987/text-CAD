import test from 'node:test';
import assert from 'node:assert/strict';
import { Box3, Scene, Vector3 } from 'three';
import { loadGlbGeometry } from './helpers/load-glb-geometry.mjs';
import { bindCadNodes, centerModelAtFloorDatum } from '../src/model-scene.ts';
import { settingsForPreset } from '../src/model-state.ts';
import { createOutdoorLighting, outdoorLightSpec } from '../src/scene-lighting.ts';

test('actual exported fixture sources follow CAD datum, power, category visibility and cutting without altering geometry', async () => {
  const gltf = await loadGlbGeometry(new URL('../../GLB/house_3d.glb', import.meta.url));
  const objects = bindCadNodes(gltf);
  assert.equal(centerModelAtFloorDatum(gltf.scene, objects), true);
  const scene = new Scene(); scene.add(gltf.scene);
  const originalBounds = new Box3().setFromObject(gltf.scene);
  const emitters = [...objects.values()].filter(object => object.isMesh && object.userData.outdoorLight);
  assert.equal(emitters.length, 7);
  const originalMaterials = emitters.map(object => object.material);
  const runtime = createOutdoorLighting(scene); runtime.register(gltf.scene); runtime.register(gltf.scene);
  const lights = [];
  scene.traverse(object => { if (object.isSpotLight) lights.push(object); });
  assert.equal(lights.length, 7, 'registration cannot allocate duplicate lights');
  assert.equal(lights.filter(light => light.castShadow).length, 1, 'only one CAD shadow pass is allocated');
  const day = settingsForPreset('exterior');
  assert.equal(runtime.update(day).active, 0);
  const night = { ...day, environment: 'night' };
  assert.equal(runtime.update(night).active, 7);
  assert.ok(emitters.every(object => object.material.emissiveIntensity > 0));
  for (const emitter of emitters) {
    const spec = outdoorLightSpec(emitter.userData.outdoorLight);
    assert.ok(spec);
    const light = lights.find(object => object.name === `illumination:${spec.id}`);
    const position = gltf.scene.localToWorld(new Vector3(...spec.light_position_glb_m));
    assert.ok(light.position.distanceTo(position) < 1e-8, 'source stays aligned to translated CAD origin');
    assert.ok(light.target.position.distanceTo(gltf.scene.localToWorld(new Vector3(...spec.target_glb_m))) < 1e-8);
  }
  assert.equal(runtime.update({ ...night, outdoorLights: false }).active, 0);
  assert.ok(emitters.every(object => object.material.emissiveIntensity === 0));
  runtime.update(night);
  objects.get('lighting:path').visible = false;
  assert.equal(runtime.update(night).active, 5, 'hidden path fixtures cannot continue lighting');
  objects.get('lighting:path').visible = true;
  objects.get('lighting').visible = false;
  assert.equal(runtime.update(night).active, 0, 'hidden ancestor disables every emitter');
  objects.get('lighting').visible = true;
  const cut = runtime.update({ ...night, cutaway: true, heightMm: 0 });
  assert.equal(cut.active, 2, 'only below-datum garden emitters remain below this real cut plane');
  assert.ok(cut.activeIds.every(id => id.startsWith('garden_')));
  assert.equal(cut.shadowLights, 0);
  assert.equal(runtime.update(day).active, 0);
  const newBounds = new Box3().setFromObject(gltf.scene);
  assert.deepEqual(newBounds.min.toArray(), originalBounds.min.toArray());
  assert.deepEqual(newBounds.max.toArray(), originalBounds.max.toArray());
  runtime.dispose(); runtime.dispose();
  assert.ok(!scene.getObjectByName('outdoor-lighting-effects'));
  assert.ok(emitters.every((emitter, index) => emitter.material === originalMaterials[index]), 'dispose restores CAD material ownership');
});

test('malformed or unsupported GLB lighting metadata cannot create an invalid source', () => {
  assert.equal(outdoorLightSpec(null), null);
  assert.equal(outdoorLightSpec({ light_position_glb_m: [0, NaN, 0] }), null);
  assert.equal(outdoorLightSpec({ category: 'unknown', diffuser_label: 'body' }), null);
});
