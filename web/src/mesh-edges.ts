import { BufferAttribute, BufferGeometry, EdgesGeometry } from 'three';
import type { WorkerGeometry } from './geometry-worker-protocol.ts';

/** Use the installed Three implementation: CAD outlines have different weld semantics. */
export function createMeshEdgePositions(input: WorkerGeometry, thresholdAngle: number): Float32Array {
  const source = new BufferGeometry();
  source.setAttribute('position', new BufferAttribute(input.positions, 3));
  if (input.indexed) source.setIndex(new BufferAttribute(input.indices, 1));
  const edges = new EdgesGeometry(source, thresholdAngle);
  const positions = edges.getAttribute('position').array as Float32Array;
  edges.dispose();
  source.dispose();
  return positions;
}
