import test from 'node:test';
import assert from 'node:assert/strict';
import {Scene,Box3,Raycaster,Vector3} from 'three';
import {loadGlbGeometry} from './helpers/load-glb-geometry.mjs';
import {bindCadNodes,centerModelAtFloorDatum} from '../src/model-scene.ts';
import {createIndoorLighting} from '../src/scene-lighting.ts';
import {settingsForPreset} from '../src/model-state.ts';
import {initialSceneLighting,sceneLightingUrl} from '../src/scene-lighting-settings.ts';

test('exported room lights follow power, floor visibility and actual cut height; furniture is independent',async()=>{
 const gltf=await loadGlbGeometry(new URL('../../GLB/house_3d.glb',import.meta.url));
 const objects=bindCadNodes(gltf);centerModelAtFloorDatum(gltf.scene,objects);
 const scene=new Scene();scene.add(gltf.scene);const bounds=new Box3().setFromObject(gltf.scene);
 const emitters=[...objects.values()].filter(o=>o.isMesh && o.userData.indoorLight);
 assert.equal(emitters.length,14);assert.equal(new Set(emitters.map(o=>o.userData.indoorLight.id)).size,14);
 const runtime=createIndoorLighting(scene);runtime.register(gltf.scene);runtime.register(gltf.scene);
 const settings=settingsForPreset('exterior');assert.equal(runtime.update(settings).active,14);
 objects.get('F1').visible=false;assert.equal(runtime.update(settings).active,7);
 objects.get('F2').visible=false;assert.equal(runtime.update(settings).active,1);
 objects.get('attic').visible=false;assert.equal(runtime.update(settings).active,0);
 objects.get('F2').visible=true;objects.get('F2:furniture').visible=false;
 assert.equal(runtime.update(settings).active,6);
 assert.equal(runtime.update({...settings,indoorLights:false}).active,0);
 assert.ok(emitters.every(o=>o.material.emissiveIntensity===0));
 assert.equal(runtime.update({...settings,cutaway:true,heightMm:4000}).active,0);
 assert.equal(runtime.update({...settings,cutaway:true,heightMm:5400}).active,6);
 assert.deepEqual(new Box3().setFromObject(gltf.scene).min.toArray(),bounds.min.toArray());
 runtime.dispose();assert.ok(!scene.getObjectByName('indoor-lighting-effects'));
});

test('indoor switch survives model links and presets; legacy preferences migrate to enabled',()=>{
 const saved={getItem:()=>'{"version":1,"environment":"night","outdoorLights":false}'};
 assert.equal(initialSceneLighting('',saved).indoorLights,true);
 const state=initialSceneLighting('?indoorLights=off',saved);assert.equal(state.indoorLights,false);
 assert.equal(state.outdoorLights,false);assert.equal(state.environment,'night');
 assert.equal(new URL(sceneLightingUrl('https://example.com/?mode=second',state)).searchParams.get('indoorLights'),'off');
 assert.equal(settingsForPreset('first',undefined,{...settingsForPreset('second'),indoorLights:false}).indoorLights,false);
});

// Intersect the exported solids, not a synthetic cylinder: a visible emitter is
// required from the elevated camera used by the interior presets.
test('every pendant and attic diffuser is visible through its shade from above',async()=>{
 const gltf=await loadGlbGeometry(new URL('../../GLB/house_3d.glb',import.meta.url));
 const objects=bindCadNodes(gltf);centerModelAtFloorDatum(gltf.scene,objects);
 const scene=new Scene();scene.add(gltf.scene);scene.updateMatrixWorld(true);
 const runtime=createIndoorLighting(scene);runtime.register(gltf.scene);
 const emitters=[...objects.values()].filter(o=>o.isMesh && o.userData.indoorLight);
 let examined=0;
 for(const emitter of emitters){
  const fixture=emitter.userData.indoorLight;
  if(fixture.style==='wall')continue;
  const center=new Box3().setFromObject(emitter).getCenter(new Vector3());
  const ray=new Raycaster(new Vector3(center.x+.06,center.y+.5,center.z),new Vector3(0,-1,0));
  const group=objects.get(fixture.group);assert.ok(group,fixture.id);
  const hit=ray.intersectObject(group,true)[0];
  assert.equal(hit?.object,emitter,fixture.id+' is occluded by its exported shade');examined++;
 }
 assert.equal(examined,12);
 runtime.update(settingsForPreset('exterior'));
 assert.ok(emitters.every(o=>o.material.emissiveIntensity>0));
 runtime.update({...settingsForPreset('exterior'),indoorLights:false});
 assert.ok(emitters.every(o=>o.material.emissiveIntensity===0));runtime.dispose();
});
