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

/** Only named main-deck meshes belong to this close-up; top_maintenance does not. */
export function landmarkMainDeckBounds(nodes: ReadonlyMap<string, Object3D>): Box3 | null {
  return namedMeshBounds(nodes, 'decks:main_');
}

/** Two complete native grid bands on each side of the model GL80m junction. */
export function landmarkGridTransitionBounds(nodes: ReadonlyMap<string, Object3D>): Box3 | null {
  const bounds = new Box3();
  let upper = false, lower = false;
  for (const [name, node] of nodes) {
    if (!(node instanceof Mesh)) continue;
    const grid = /^structure:grid_(?:panel_[ab]|vertical|belt)_[0-3]_[01](?:_[0-3])?$/.test(name);
    const retained = /^structure:lower_panel_(?:a|b|vertical)_[0-3]_[12]_[0-3]$/.test(name)
      || /^structure:lower_belt_[0-3]_[12]$/.test(name);
    if (!grid && !retained) continue;
    node.updateWorldMatrix(true, false);
    bounds.expandByObject(node);
    upper ||= grid; lower ||= retained;
  }
  return !upper || !lower || bounds.isEmpty() ? null : bounds.expandByScalar(2);
}

/** CAD prefixes include each deck's equipment crown and the complete antenna envelope. */
export function landmarkCloseupBounds(id: LandmarkId, nodes: ReadonlyMap<string, Object3D>, modelBounds: Box3): ReadonlyMap<LandmarkCamera, Box3> {
  const result = new Map<LandmarkCamera, Box3>();
  if (!modelBounds.isEmpty()) {
    const base = modelBounds.clone();
    base.max.y = Math.min(id === 'tokyo-tower' ? 80 : 100, modelBounds.max.y);
    result.set('base', base);
  }
  if (id === 'tokyo-tower') {
    const transition = landmarkGridTransitionBounds(nodes);
    if (transition) result.set('grid-transition', transition);
  }
  const regions: readonly [LandmarkCamera, string][] = id === 'tokyo-tower'
    ? [['main-deck', 'decks:main_'], ['top-deck', 'decks:top_'], ['spire', 'antenna:']]
    : [['tembo-deck', 'decks:tembo_deck_'], ['tembo-galleria', 'decks:tembo_galleria_'], ['spire', 'antenna:']];
  for (const [camera, prefix] of regions) {
    const region = namedMeshBounds(nodes, prefix);
    if (region) result.set(camera, region);
  }
  return result;
}
