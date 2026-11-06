import test from 'node:test';
import assert from 'node:assert/strict';
import { Box3, BoxGeometry, Group, Mesh, MeshStandardMaterial, Vector3 } from 'three';
import { bridgeActivityRunning, bridgeActorCoordinate, bridgeActorPose, bridgeActorX, bridgeRailHeight, bridgeRoadDerivative, bridgeRoadHeight, createBridgeMotionClock, parseBridgeActivity } from '../src/bridge-motion.ts';
import { bridgeDisplay } from '../src/bridge-batches.ts';
import { bridgeGroups } from '../src/bridge-copy.ts';
import { bridgeWaterShaderProfile, createBridgeWater } from '../src/bridge-water.ts';

function fixture() {
  return { schema_version: 2, snapshot_time_s: 0, road_crest_z_mm: 93000, rail_crest_z_mm: 80420, road_grade: .01, shared_anchor_half_length_mm: 24500, actors: [
    { id: 'car_01', group: 'traffic', kind: 'sedan', origin_mm: [100000, 3500, 92000], heading_rad: 0, direction: 1, speed_mps: 22.5, phase: .2, length_mm: 4400, width_mm: 1800, height_mm: 1500, route: { axis: 'x', min_mm: -1500000, max_mm: 1600000, fixed_mm: 3500 }, part_names: ['traffic:car_01:body', 'traffic:car_01:roof'] },
    { id: 'boat_01', group: 'vessels', kind: 'cruise', origin_mm: [-825000, -42000, 0], heading_rad: Math.PI / 2, direction: 1, speed_mps: 6, phase: .4, length_mm: 20000, width_mm: 6000, height_mm: 6500, route: { axis: 'y', min_mm: -300000, max_mm: 300000, fixed_mm: -825000 }, part_names: ['vessels:boat_01:hull'] },
    ...Array.from({ length: 4 }, (_, i) => ({ id: 'train_01_' + i, group: 'trains', kind: 'emu', origin_mm: [100000-i*20500, -5500, 79420+i*205], heading_rad: 0, direction: 1, speed_mps: 25, phase: .4, length_mm: 20000, width_mm: 2900, height_mm: 4000, route: { axis: 'x', min_mm: -1400000, max_mm: 1500000, fixed_mm: -5500 }, part_names: ['trains:train_01_'+i+':body'], train_id: 'emu_1', carriage_index: i, lead_position_mm: 100000, consist_offset_mm: -i*20500, bogie_spacing_mm: 13800 })),
  ] };
}
const near = (a,b,e=1e-8) => assert.ok(Math.abs(a-b)<e, `${a} != ${b}`);

test('schema2 rejects old routes, wrong directions, duplicate parts and broken train consists', () => {
  assert.equal(parseBridgeActivity(fixture()).actors.length, 6);
  for (const mutate of [
    a => { a.schema_version=1; }, a => { a.actors[0].route.fixed_mm=-3500; a.actors[0].origin_mm[1]=-3500; }, a => { a.actors[1].route.axis='x'; },
    a => { a.actors[1].direction='1'; }, a => { a.actors[0].part_names.push(a.actors[0].part_names[0]); }, a => { a.actors[1].origin_mm[1]=a.actors[1].route.max_mm; },
    a => { a.actors[0].speed_mps=Infinity; }, a => { a.actors.splice(2); }, a => { a.actors[0].heading_rad=Math.PI; }, a => { a.actors[3].speed_mps=26; },
    a => { a.actors[3].carriage_index=3; }, a => { a.actors[3].consist_offset_mm=-10000; }, a => { a.actors[3].bogie_spacing_mm=0; },
  ]) { const a=fixture(); mutate(a); assert.throws(() => parseBridgeActivity(a)); }
});

test('cars keep left and follow the 1% grade and actual flat 49m shared connection', () => {
  const a=parseBridgeActivity(fixture()), car=a.actors[0];
  for (const x of [-100000,-24501,-24500,0,24500,24501,100000]) {
    const pose=bridgeActorPose({...car,origin_mm:[x,3500,bridgeRoadHeight(x,a)]},a,0);
    near(pose.position.y*1000,bridgeRoadHeight(x,a)); near(pose.position.z,-3.5);
    const dir=new Vector3(1,0,0).applyQuaternion(pose.rotation); near(dir.y/dir.x,bridgeRoadDerivative(x,a));
  }
  near(bridgeRoadHeight(0,a),92755); near(bridgeRoadHeight(24500,a),92755); assert.equal(bridgeRoadDerivative(0,a),0);
  near(bridgeRoadHeight(-24500.001,a),bridgeRoadHeight(-24500,a),.001);
  const reverse={...car,direction:-1,heading_rad:Math.PI,origin_mm:[100000,-3500,92000],route:{...car.route,fixed_mm:-3500}};
  const pose=bridgeActorPose(reverse,a,0), dir=new Vector3(1,0,0).applyQuaternion(pose.rotation);
  assert.ok(dir.x<0); near(dir.y/dir.x,-.01); near(pose.position.z,3.5);
});

test('boats cross the bridge X axis along Y while road vehicles retain their lanes', () => {
  const a=fixture(), car=a.actors[0], boat=a.actors[1];
  for (const actor of [car,boat]) for (const t of [0,.016,100,1000,100000]) {
    const coord=bridgeActorCoordinate(actor,t); assert.ok(coord>=actor.route.min_mm&&coord<actor.route.max_mm);
    const pose=bridgeActorPose(actor,a,t,false); if(actor.group==='traffic') near(pose.position.z,-actor.route.fixed_mm/1000); else near(pose.position.x,actor.route.fixed_mm/1000);
  }
  near(bridgeActorX(boat,0),-825000); near(bridgeActorX(boat,100),-825000); near(bridgeActorPose(boat,a,7,false).position.z,0);
  assert.ok(bridgeActorPose(boat,a,6,false).position.z>0); assert.ok(bridgeActorPose(boat,a,8,false).position.z<0);
  const dir=new Vector3(1,0,0).applyQuaternion(bridgeActorPose(boat,a,0,false).rotation); near(dir.x,0); near(dir.z,-1);
  near(new Vector3(1,0,0).applyQuaternion(bridgeActorPose({...boat,direction:-1,heading_rad:-Math.PI/2},a,0,false).rotation).z,1);
});

test('whole trains keep 20.5m spacing across leader wrapping in either direction', () => {
  const a=fixture(), cars=a.actors.filter(actor=>actor.group==='trains');
  for(const direction of [1,-1]) for(const t of [0,55.999,56,56.001,120,100000]) {
    const consist=cars.map(car=>{ const x=100000+direction*car.consist_offset_mm; return {...car,direction,heading_rad:direction===1?0:Math.PI,origin_mm:[x,-5500,(bridgeRailHeight(x-6900,a)+bridgeRailHeight(x+6900,a))/2]}; });
    const xs=consist.map(car=>bridgeActorCoordinate(car,t)); for(let i=1;i<xs.length;i++) near((xs[i-1]-xs[i])*direction,20500);
    for(const car of consist) { const pose=bridgeActorPose(car,a,t,false); near(pose.position.x*1000,bridgeActorCoordinate(car,t)); near(pose.position.z,5.5); near(pose.position.y*1000,(bridgeRailHeight(pose.position.x*1000-6900,a)+bridgeRailHeight(pose.position.x*1000+6900,a))/2); }
  }
});

test('carriages bridge both bogies smoothly at each flat shared-anchor transition', () => {
  const a=fixture(), train=a.actors[2];
  for(const direction of [1,-1]) for(const x of [-30000,-24500,-20000,0,20000,24500,30000]) {
    const lo=bridgeRailHeight(x-6900,a),hi=bridgeRailHeight(x+6900,a), actor={...train,direction,heading_rad:direction===1?0:Math.PI,lead_position_mm:x,origin_mm:[x,-5500,(lo+hi)/2]};
    const pose=bridgeActorPose(actor,a,0,false),dir=new Vector3(1,0,0).applyQuaternion(pose.rotation);
    near(pose.position.y*1000,(lo+hi)/2); near(dir.y/dir.x,(hi-lo)/13800);
    near(pose.position.y*1000-6900*dir.y/dir.x,lo); near(pose.position.y*1000+6900*dir.y/dir.x,hi);
  }
});

test('bounded active clock excludes paused wall time and water can animate without visible actors', () => {
  const clock=createBridgeMotionClock(); near(clock.step(1000,true),0); near(clock.step(1050,true),.05); near(clock.step(300000,false),.05);
  near(clock.step(900000,true),.05); near(clock.step(900050,true),.1); near(clock.step(999999,true),.2); clock.pause(); near(clock.step(2000000,true),.2);
  const hidden={traffic:false,vessels:false,trains:false},shown={...hidden,trains:true};
  assert.equal(bridgeActivityRunning(true,false,shown,true,true),false); assert.equal(bridgeActivityRunning(false,true,shown,true,true),false);
  assert.equal(bridgeActivityRunning(true,true,hidden,true,false),false); assert.equal(bridgeActivityRunning(true,true,hidden,false,true),false);
  assert.equal(bridgeActivityRunning(true,true,hidden,true,true),true); assert.equal(bridgeActivityRunning(true,true,shown),true);
});

test('boats have bounded gentle motion and retain their exact native zero-time pose', () => {
  const a=fixture(),boat=a.actors[1],initial=bridgeActorPose(boat,a,0),plain=bridgeActorPose(boat,a,0,false);
  near(initial.position.distanceTo(plain.position),0); near(initial.rotation.angleTo(plain.rotation),0);
  for(const t of [.2,2,10,100]) { const pose=bridgeActorPose(boat,a,t); assert.ok(Math.abs(pose.position.y)<=.141); assert.ok(pose.rotation.angleTo(bridgeActorPose(boat,a,t,false).rotation)<.02); }
});

test('procedural sea retains mean-water extent and has distance-filtered animated normals', () => {
  const water=createBridgeWater(new Box3(new Vector3(-1500,-5,-300),new Vector3(1700,0,300)));
  try {
    near(water.mesh.position.y,.025); near(new Box3().setFromObject(water.mesh).getSize(new Vector3()).x,3200);
    water.time(1.25); assert.equal(water.mesh.material.uniforms.uTime.value,1.25); water.night(true); assert.equal(water.mesh.material.uniforms.uNight.value,1);
    assert.equal(bridgeWaterShaderProfile.externalTextures,false); assert.equal(bridgeWaterShaderProfile.distanceFiltered,true);
    assert.ok(bridgeWaterShaderProfile.wavelengthsM.every(n=>n>=1&&n<21)); assert.match(water.mesh.material.fragmentShader,/fwidth/); assert.throws(()=>createBridgeWater(new Box3()));
  } finally {water.dispose();}
});

test('actor-local colour batches preserve source geometry and isolate actor motion', () => {
  const a=fixture(),root=new Group(),materials=[],source=[];
  const add=(name,colour,pose,offset=0)=>{const mat=new MeshStandardMaterial({color:colour,roughness:.7,metalness:.12});materials.push(mat);const mesh=new Mesh(new BoxGeometry(1,1,1).translate(offset,.5,0),mat);mesh.name=name;if(pose){mesh.position.copy(pose.position);mesh.quaternion.copy(pose.rotation);}root.add(mesh);source.push(mesh);};
  for(const g of bridgeGroups.filter(id=>!['traffic','vessels','trains'].includes(id))) add(g+':static','#f0e8dd');
  add('environment:sea:mean','#f0e8dd',undefined,20);
  for(const actor of a.actors) actor.part_names.forEach((name,i)=>add(name,i?'#e22333':'#2266bb',bridgeActorPose(actor,a,0,false),i*2));
  const original=new Box3().setFromObject(root),batch=bridgeDisplay(root,a);
  try {
    const actual=new Box3().setFromObject(batch.display);near(original.min.distanceTo(actual.min),0,1e-5);near(original.max.distanceTo(actual.max),0,1e-5);assert.equal(batch.actors.size,6);
    const waterSources=batch.groups.get('environment').filter(node=>node.userData.bridgeWaterSource); assert.equal(waterSources.length,1);
    near(new Box3().setFromObject(waterSources[0]).getCenter(new Vector3()).x,20); // Equal-colour land is never hidden with the sea.
    const car=batch.actors.get('car_01');assert.equal(car.object.children.length,1);const colours=car.object.children[0].geometry.getAttribute('color'),unique=new Set();assert.ok(colours);for(let i=0;i<colours.count;i++)unique.add([colours.getX(i),colours.getY(i),colours.getZ(i)].join(','));assert.equal(unique.size,2);
    const staticBounds=new Box3().setFromObject(batch.groups.get('towers')[0]),pose=bridgeActorPose(car.spec,a,10);car.object.position.copy(pose.position);car.object.quaternion.copy(pose.rotation);
    near(new Box3().setFromObject(batch.groups.get('towers')[0]).min.distanceTo(staticBounds.min),0);assert.ok(new Box3().setFromObject(car.object).getCenter(new Vector3()).x>300);
  }finally{batch.display.traverse(n=>{if(n.isMesh)n.geometry.dispose();});batch.ownedMaterials.forEach(m=>m.dispose());source.forEach(m=>m.geometry.dispose());materials.forEach(m=>m.dispose());}
});
