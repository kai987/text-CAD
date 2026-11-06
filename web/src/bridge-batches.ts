import { Float32BufferAttribute, Group, Matrix4, Mesh, MeshStandardMaterial, Vector3 } from 'three';
import type { BufferGeometry, Material, Object3D } from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { bridgeGroupForName, bridgeGroups } from './bridge-copy.ts';
import type { BridgeGroupId } from './bridge-copy';
import { bridgeActorPose } from './bridge-motion.ts';
import type { BridgeActivity, BridgeActor } from './bridge-motion';
import { isObjectVisible } from './model-scene.ts';

export interface BridgeActorDisplay { spec: BridgeActor; object: Group }

/** Static finishes batch together; moving actors each retain an independent origin. */
export function bridgeDisplay(root: Object3D, activity: BridgeActivity) {
  root.updateWorldMatrix(true, true);
  const display = new Group(), groups = new Map<BridgeGroupId, Object3D[]>();
  const buckets = new Map<string, { group: BridgeGroupId; actor?: BridgeActor; material: Material; geometry: BufferGeometry[]; water?: boolean }>();
  const actors = new Map<string, BridgeActorDisplay>(), byPart = new Map<string, BridgeActor>(), seen = new Set<string>();
  const actorInverse = new Map<string, Matrix4>(), pendingGeometry = new Set<BufferGeometry>(), ownedMaterials = new Set<Material>();
  for (const actor of activity.actors) {
    const pose = bridgeActorPose(actor, activity, 0, false);
    actorInverse.set(actor.id, new Matrix4().compose(pose.position, pose.rotation, new Vector3(1, 1, 1)).invert());
    for (const name of actor.part_names) byPart.set(name, actor);
  }
  const inverse = new Matrix4().copy(root.matrixWorld).invert();
  let batchCount = 0;
  try {
    root.traverse(node => {
      if (!(node instanceof Mesh) || !isObjectVisible(node)) return;
      const name = String(node.userData.cadName ?? node.name);
      let group: BridgeGroupId | null = null;
      for (let current: Object3D | null = node; current && !group; current = current.parent) group = bridgeGroupForName(String(current.userData.cadName ?? current.name));
      if (!group) throw new Error('Unclassified bridge mesh: ' + name);
      const actor = byPart.get(name);
      if ((group === 'traffic' || group === 'vessels' || group === 'trains') && (!actor || actor.group !== group)) throw new Error('Unbound bridge actor mesh: ' + name);
      if (actor) seen.add(name);
      if (Array.isArray(node.material) || Object.keys(node.geometry.morphAttributes).length) throw new Error('Unsupported bridge presentation geometry.');
      const geometry = node.geometry.index ? node.geometry.toNonIndexed() : node.geometry.clone();
      pendingGeometry.add(geometry);
      for (const attribute of Object.keys(geometry.attributes)) if (attribute !== 'position' && attribute !== 'normal') geometry.deleteAttribute(attribute);
      if (!geometry.getAttribute('normal')) geometry.computeVertexNormals();
      const transform = new Matrix4().multiplyMatrices(inverse, node.matrixWorld);
      if (actor) transform.premultiply(actorInverse.get(actor.id)!);
      geometry.applyMatrix4(transform);
      const material = node.material;
      const plainFinish = material.constructor === MeshStandardMaterial && material instanceof MeshStandardMaterial && !material.map && !material.normalMap && !material.roughnessMap && !material.metalnessMap && !material.emissiveMap && !material.alphaMap && !material.aoMap && !material.lightMap && !material.vertexColors
        && material.onBeforeCompile === MeshStandardMaterial.prototype.onBeforeCompile && material.customProgramCacheKey === MeshStandardMaterial.prototype.customProgramCacheKey;
      // CAD actors use the same untextured PBR finish. Bake only its base colour
      // into vertex colours, preserving the finish while drawing each actor once.
      const bakeColour = !!actor && plainFinish;
      if (bakeColour) {
        const colours = new Float32Array(geometry.getAttribute('position').count * 3), rgb = material.color.toArray();
        for (let index = 0; index < colours.length; index += 3) colours.set(rgb, index);
        geometry.setAttribute('color', new Float32BufferAttribute(colours, 3));
      }
      const finish = plainFinish
        ? [...(bakeColour ? [] : material.color.toArray()), material.roughness, material.metalness, ...material.emissive.toArray(), material.emissiveIntensity, material.opacity, material.transparent, material.side, material.flatShading, material.depthWrite, material.alphaTest].join('/')
        : material.uuid;
      const waterSource = name.startsWith('environment:sea:');
      const key = group + ':' + (actor?.id ?? 'static') + ':' + finish + (waterSource ? ':mean-water' : '');
      if (!buckets.has(key)) {
        const batchMaterial = bakeColour ? material.clone() : material;
        if (bakeColour && batchMaterial instanceof MeshStandardMaterial) {
          batchMaterial.color.setRGB(1, 1, 1); batchMaterial.vertexColors = true; ownedMaterials.add(batchMaterial);
        }
        buckets.set(key, { group, actor, material: batchMaterial, geometry: [], water: waterSource });
      }
      buckets.get(key)!.geometry.push(geometry);
    });
    if (!buckets.size || seen.size !== byPart.size) throw new Error('Incomplete bridge release or activity assembly.');
    for (const { group, actor, material, geometry, water } of buckets.values()) {
      const merged = mergeGeometries(geometry, false);
      geometry.forEach(item => { item.dispose(); pendingGeometry.delete(item); });
      if (!merged) throw new Error('Bridge display batch could not be built.');
      merged.computeBoundingSphere();
      const mesh = new Mesh(merged, material); mesh.userData.bridgeGroup = group; if (water) mesh.userData.bridgeWaterSource = true;
      if (actor) {
        if (!actors.has(actor.id)) {
          const object = new Group(), pose = bridgeActorPose(actor, activity, 0, false);
          object.name = group + ':' + actor.id; object.position.copy(pose.position); object.quaternion.copy(pose.rotation);
          object.userData.bridgeGroup = group; object.userData.actorId = actor.id;
          actors.set(actor.id, { spec: actor, object }); display.add(object);
          const nodes = groups.get(group) ?? []; nodes.push(object); groups.set(group, nodes);
        }
        actors.get(actor.id)!.object.add(mesh);
      } else {
        display.add(mesh);
        const nodes = groups.get(group) ?? []; nodes.push(mesh); groups.set(group, nodes);
      }
      batchCount++;
    }
    for (const group of bridgeGroups) if (!groups.has(group)) throw new Error('Missing bridge release group: ' + group);
    return { display, groups, actors, batchCount, ownedMaterials };
  } catch (error) {
    pendingGeometry.forEach(geometry => geometry.dispose()); ownedMaterials.forEach(material => material.dispose());
    display.traverse(node => { if (node instanceof Mesh) node.geometry.dispose(); });
    throw error;
  }
}
