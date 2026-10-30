import { Box3, Mesh } from 'three';
import type { Object3D } from 'three';
import type { LandmarkCamera, LandmarkId } from './landmark-copy';

function namedMeshBounds(nodes: ReadonlyMap<string, Object3D>, prefix: string): Box3 | null {
  const bounds = new Box3();
  for (const [name, node] of nodes) {
    if (!(node instanceof Mesh) || !name.startsWith(prefix)) continue;
    node.updateWorldMatrix(true, false);
    bounds.expandByObject(node);
  }
  return bounds.isEmpty() ? null : bounds.expandByScalar(2);
}

/** Only the named 150m deck belongs to this close-up; top_maintenance does not. */
export function landmarkMainDeckBounds(nodes: ReadonlyMap<string, Object3D>): Box3 | null {
  return namedMeshBounds(nodes, 'decks:main_');
}

/** CAD node prefixes keep the 350m deck, upper gallery and spire separate. */
export function landmarkCloseupBounds(id: LandmarkId, nodes: ReadonlyMap<string, Object3D>, modelBounds: Box3): ReadonlyMap<LandmarkCamera, Box3> {
  const result = new Map<LandmarkCamera, Box3>();
  if (!modelBounds.isEmpty()) {
    const base = modelBounds.clone();
    base.max.y = Math.min(id === 'tokyo-tower' ? 80 : 100, modelBounds.max.y);
    result.set('base', base);
  }
  const regions: readonly [LandmarkCamera, string][] = id === 'tokyo-tower'
    ? [['main-deck', 'decks:main_']]
    : [['tembo-deck', 'decks:tembo_deck_'], ['tembo-galleria', 'decks:tembo_galleria_'], ['spire', 'antenna:']];
  for (const [camera, prefix] of regions) {
    const region = namedMeshBounds(nodes, prefix);
    if (region) result.set(camera, region);
  }
  return result;
}
