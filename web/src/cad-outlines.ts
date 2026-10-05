import { BufferGeometry, Float32BufferAttribute, Triangle, Vector3 } from 'three';

interface EdgeInterval {
  start: number;
  end: number;
  forward: boolean;
  normal: Vector3;
}

interface EdgeLine {
  origin: Vector3;
  direction: Vector3;
  intervals: EdgeInterval[];
}

// CAD face tessellation can put one long edge opposite several shorter edges.
// EdgesGeometry only pairs identical endpoints, leaving those planar seams visible.
// Split collinear edges into shared intervals before deciding whether each is a
// boundary or a crease. Use only for the small architectural wall meshes.
export function createCadOutlineGeometry(geometry: BufferGeometry, thresholdAngle = 28): BufferGeometry {
  const positions = geometry.getAttribute('position');
  const result = new BufferGeometry();
  if (!positions) return result.setAttribute('position', new Float32BufferAttribute([], 3));

  let coordinateScale = 1;
  for (let i = 0; i < positions.count; i++) {
    for (const coordinate of [positions.getX(i), positions.getY(i), positions.getZ(i)]) {
      if (Number.isFinite(coordinate)) coordinateScale = Math.max(coordinateScale, Math.abs(coordinate));
    }
  }
  // One Float32 rounding step at the model scale; nearby distinct edges outside
  // that tolerance must stay separate, even when their directions are parallel.
  const tolerance = coordinateScale * 1e-7;
  const toleranceSquared = tolerance * tolerance;
  const thresholdDot = Math.cos(thresholdAngle * Math.PI / 180);
  const index = geometry.getIndex();
  const count = index?.count ?? positions.count;
  const lines: EdgeLine[] = [];
  const vertices: [Vector3, Vector3, Vector3] = [new Vector3(), new Vector3(), new Vector3()];
  const triangle = new Triangle(...vertices);
  const normal = new Vector3();
  const direction = new Vector3();
  const offset = new Vector3();
  const cross = new Vector3();

  function onLine(point: Vector3, line: EdgeLine): boolean {
    offset.subVectors(point, line.origin);
    return cross.crossVectors(offset, line.direction).lengthSq() <= toleranceSquared;
  }

  for (let i = 0; i + 2 < count; i += 3) {
    for (let j = 0; j < 3; j++) vertices[j].fromBufferAttribute(positions, index ? index.getX(i + j) : i + j);
    if (vertices.some(vertex => !Number.isFinite(vertex.x + vertex.y + vertex.z))) continue;
    triangle.getNormal(normal);
    if (normal.lengthSq() === 0) continue;

    for (let j = 0; j < 3; j++) {
      const start = vertices[j];
      const end = vertices[(j + 1) % 3];
      direction.subVectors(end, start);
      if (direction.lengthSq() <= toleranceSquared) continue;
      direction.normalize();
      let line = lines.find(candidate =>
        cross.crossVectors(direction, candidate.direction).lengthSq() <= 1e-12 &&
        onLine(start, candidate) && onLine(end, candidate));
      if (!line) {
        line = { origin: start.clone(), direction: direction.clone(), intervals: [] };
        lines.push(line);
      }
      const t0 = offset.subVectors(start, line.origin).dot(line.direction);
      const t1 = offset.subVectors(end, line.origin).dot(line.direction);
      line.intervals.push({ start: Math.min(t0, t1), end: Math.max(t0, t1), forward: t1 > t0, normal: normal.clone() });
    }
  }

  const output: number[] = [];
  const point = new Vector3();
  function emit(line: EdgeLine, start: number, end: number) {
    point.copy(line.direction).multiplyScalar(start).add(line.origin);
    output.push(point.x, point.y, point.z);
    point.copy(line.direction).multiplyScalar(end).add(line.origin);
    output.push(point.x, point.y, point.z);
  }

  for (const line of lines) {
    const endpoints = line.intervals.flatMap(interval => [interval.start, interval.end]).sort((a, b) => a - b);
    const breaks: number[] = [];
    for (const endpoint of endpoints) {
      if (!breaks.length || endpoint - breaks[breaks.length - 1] > tolerance) breaks.push(endpoint);
    }
    let visibleStart: number | undefined;
    for (let i = 0; i + 1 < breaks.length; i++) {
      const start = breaks[i];
      const end = breaks[i + 1];
      const midpoint = (start + end) / 2;
      const active = line.intervals.filter(interval => interval.start < midpoint && interval.end > midpoint);
      const shared = active.some(interval => interval.forward) && active.some(interval => !interval.forward);
      // Same-directed duplicates are still an open border. Opposite directions
      // cancel only when every incident face is below the crease threshold.
      const visible = active.length > 0 && (!shared || active.some((a, j) =>
        active.slice(j + 1).some(b => a.normal.dot(b.normal) <= thresholdDot)));
      if (visible && visibleStart === undefined) visibleStart = start;
      if (!visible && visibleStart !== undefined) {
        emit(line, visibleStart, start);
        visibleStart = undefined;
      }
    }
    if (visibleStart !== undefined) emit(line, visibleStart, breaks[breaks.length - 1]);
  }
  return result.setAttribute('position', new Float32BufferAttribute(output, 3));
}
