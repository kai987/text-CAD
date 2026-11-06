import { Quaternion, Vector3 } from 'three';

export type BridgeActivityGroup = 'traffic' | 'vessels' | 'trains';
export interface BridgeActor {
  id: string; group: BridgeActivityGroup; kind: string;
  origin_mm: [number, number, number]; heading_rad: number; direction: 1 | -1;
  speed_mps: number; phase: number; length_mm: number; width_mm: number; height_mm: number;
  route: { axis: 'x' | 'y'; min_mm: number; max_mm: number; fixed_mm: number }; part_names: string[];
  train_id?: string; carriage_index?: number; lead_position_mm?: number; consist_offset_mm?: number; bogie_spacing_mm?: number;
}
export interface BridgeActivity {
  schema_version: 2; snapshot_time_s: number; road_crest_z_mm: number; rail_crest_z_mm: number; road_grade: number;
  shared_anchor_half_length_mm: number; actors: BridgeActor[];
}
const finite = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value);
const validRecord = (value: unknown): value is Record<string, unknown> => !!value && typeof value === 'object' && !Array.isArray(value);
const headingFor = (axis: 'x' | 'y', direction: number) => axis === 'y' ? direction * Math.PI / 2 : direction === 1 ? 0 : Math.PI;

/** Only the versioned activity bundled with the exact downloadable GLB is used. */
export function parseBridgeActivity(value: unknown): BridgeActivity {
  if (!validRecord(value) || value.schema_version !== 2 || value.snapshot_time_s !== 0
      || !finite(value.road_crest_z_mm) || !finite(value.rail_crest_z_mm)
      || !finite(value.road_grade) || value.road_grade <= 0 || value.road_grade > .1
      || !finite(value.shared_anchor_half_length_mm) || value.shared_anchor_half_length_mm <= 0
      || !Array.isArray(value.actors) || value.actors.length < 3 || value.actors.length > 100) throw new Error('Invalid bridge activity profile.');
  const records = value.actors, ids = new Set<string>(), parts = new Set<string>();
  for (const item of records) {
    if (!validRecord(item) || typeof item.id !== 'string' || !/^[a-zA-Z0-9_-]{1,64}$/.test(item.id) || ids.has(item.id)
        || !['traffic', 'vessels', 'trains'].includes(String(item.group)) || typeof item.kind !== 'string'
        || !Array.isArray(item.origin_mm) || item.origin_mm.length !== 3 || !item.origin_mm.every(finite)
        || !finite(item.heading_rad) || (item.direction !== 1 && item.direction !== -1)
        || !finite(item.speed_mps) || item.speed_mps <= 0 || item.speed_mps > 70 || !finite(item.phase) || item.phase < 0 || item.phase >= 1
        || !['length_mm', 'width_mm', 'height_mm'].every(key => finite(item[key]) && Number(item[key]) > 0)
        || !validRecord(item.route) || !['x', 'y'].includes(String(item.route.axis))
        || !finite(item.route.min_mm) || !finite(item.route.max_mm) || !finite(item.route.fixed_mm)
        || item.route.max_mm - item.route.min_mm < 100000
        || Math.abs(item.origin_mm[item.route.axis === 'x' ? 1 : 0] - item.route.fixed_mm) > .01
        || Math.abs(item.heading_rad - headingFor(item.route.axis as 'x' | 'y', item.direction)) > 1e-8
        || !Array.isArray(item.part_names) || !item.part_names.length || new Set(item.part_names).size !== item.part_names.length
        || item.part_names.some(name => typeof name !== 'string' || !name.startsWith(item.group + ':' + item.id + ':') || parts.has(name))) {
      throw new Error('Invalid bridge actor.');
    }
    if (item.group === 'vessels' && item.route.axis !== 'y') throw new Error('Boats must cross the bridge axis.');
    if (item.group !== 'vessels' && item.route.axis !== 'x') throw new Error('Road and rail actors must follow the bridge.');
    if (item.group === 'traffic' && Math.sign(item.route.fixed_mm) !== item.direction) throw new Error('Bridge traffic must use left-hand carriageways.');
    if (item.group === 'trains') {
      if (typeof item.train_id !== 'string' || !/^[a-zA-Z0-9_-]{1,64}$/.test(item.train_id)
          || !Number.isInteger(item.carriage_index) || Number(item.carriage_index) < 0 || Number(item.carriage_index) > 15
          || !finite(item.lead_position_mm) || item.lead_position_mm < item.route.min_mm || item.lead_position_mm >= item.route.max_mm
          || !finite(item.bogie_spacing_mm) || item.bogie_spacing_mm <= 0 || item.bogie_spacing_mm >= Number(item.length_mm)
          || !finite(item.consist_offset_mm) || item.consist_offset_mm > 0
          || Math.abs(item.origin_mm[0] - (item.lead_position_mm + item.direction * item.consist_offset_mm)) > .01) throw new Error('Invalid train carriage.');
    } else {
      const coordinate = item.origin_mm[item.route.axis === 'x' ? 0 : 1];
      if (coordinate < item.route.min_mm || coordinate >= item.route.max_mm) throw new Error('Actor lies outside its route.');
    }
    ids.add(item.id); for (const name of item.part_names) parts.add(name);
  }
  if (!['traffic', 'vessels', 'trains'].every(group => records.some(actor => actor.group === group))) throw new Error('Missing bridge activity group.');
  const consists = new Map<string, BridgeActor[]>();
  for (const actor of records as unknown as BridgeActor[]) if (actor.group === 'trains') {
    const cars = consists.get(actor.train_id!) ?? []; cars.push(actor); consists.set(actor.train_id!, cars);
  }
  for (const cars of consists.values()) {
    cars.sort((a, b) => a.carriage_index! - b.carriage_index!);
    if (cars.length < 2 || cars.some((car, index) => car.carriage_index !== index
        || car.direction !== cars[0].direction || car.speed_mps !== cars[0].speed_mps || car.phase !== cars[0].phase
        || car.lead_position_mm !== cars[0].lead_position_mm || JSON.stringify(car.route) !== JSON.stringify(cars[0].route)
        || (index === 0 ? car.consist_offset_mm !== 0
          : cars[index - 1].consist_offset_mm! - car.consist_offset_mm! < (cars[index - 1].length_mm + car.length_mm) / 2 + 100))) {
      throw new Error('Train consists must share a lead route and keep carriage spacing.');
    }
  }
  return value as unknown as BridgeActivity;
}

export function bridgeRoadHeight(x: number, activity: BridgeActivity): number {
  return activity.road_crest_z_mm - activity.road_grade * Math.max(Math.abs(x), activity.shared_anchor_half_length_mm);
}
export function bridgeRailHeight(x: number, activity: BridgeActivity): number {
  return activity.rail_crest_z_mm - activity.road_grade * Math.max(Math.abs(x), activity.shared_anchor_half_length_mm);
}
export function bridgeRoadDerivative(x: number, activity: BridgeActivity): number {
  return Math.abs(x) <= activity.shared_anchor_half_length_mm ? 0 : -activity.road_grade * Math.sign(x);
}

/** The entire consist wraps its leader once; individual carriages never wrap. */
export function bridgeActorCoordinate(actor: BridgeActor, elapsedSeconds: number): number {
  const { min_mm: minimum, max_mm: maximum } = actor.route, length = maximum - minimum;
  const start = actor.group === 'trains' ? actor.lead_position_mm! : actor.origin_mm[actor.route.axis === 'x' ? 0 : 1];
  const distance = Math.max(0, elapsedSeconds) * actor.speed_mps * 1000 * actor.direction;
  const head = minimum + ((start - minimum + distance) % length + length) % length;
  return head + (actor.group === 'trains' ? actor.direction * actor.consist_offset_mm! : 0);
}
export function bridgeActorX(actor: BridgeActor, elapsedSeconds: number): number {
  return actor.route.axis === 'x' ? bridgeActorCoordinate(actor, elapsedSeconds) : actor.route.fixed_mm;
}

/** Native coordinates are mm/Z-up; the viewer uses m/Y-up. */
export function bridgeActorPose(actor: BridgeActor, activity: BridgeActivity, elapsedSeconds: number, gentleWaves = true) {
  const coordinate = bridgeActorCoordinate(actor, elapsedSeconds), x = actor.route.axis === 'x' ? coordinate : actor.route.fixed_mm;
  const y = actor.route.axis === 'y' ? coordinate : actor.route.fixed_mm, vessel = actor.group === 'vessels';
  const trainHeight = (station: number) => (bridgeRailHeight(station - actor.bogie_spacing_mm! / 2, activity) + bridgeRailHeight(station + actor.bogie_spacing_mm! / 2, activity)) / 2;
  const baseHeight = (station: number) => actor.group === 'trains' ? trainHeight(station) : bridgeRoadHeight(station, activity);
  const groundOffset = actor.origin_mm[2] - baseHeight(actor.origin_mm[0]);
  const phase = actor.phase * 2 * Math.PI, seconds = Math.max(0, elapsedSeconds);
  const heave = vessel && gentleWaves ? 70 * (Math.sin(seconds * .75 + phase) - Math.sin(phase)) : 0;
  const z = vessel ? actor.origin_mm[2] + heave : baseHeight(x) + groundOffset;
  const position = new Vector3(x / 1000, z / 1000, -y / 1000);
  const pitch = vessel ? (gentleWaves ? .003 * Math.sin(seconds * .65) : 0)
    : Math.atan(actor.direction * (actor.group === 'trains'
      ? (bridgeRailHeight(x + actor.bogie_spacing_mm! / 2, activity) - bridgeRailHeight(x - actor.bogie_spacing_mm! / 2, activity)) / actor.bogie_spacing_mm!
      : bridgeRoadDerivative(x, activity)));
  const roll = vessel && gentleWaves ? .004 * (Math.sin(seconds * .6 + phase) - Math.sin(phase)) : 0;
  const rotation = new Quaternion().setFromAxisAngle(new Vector3(0, 1, 0), actor.heading_rad)
    .multiply(new Quaternion().setFromAxisAngle(new Vector3(0, 0, 1), pitch))
    .multiply(new Quaternion().setFromAxisAngle(new Vector3(1, 0, 0), roll));
  return { position, rotation };
}

/** Reset wall time on every pause; inactive tabs never accumulate catch-up. */
export function createBridgeMotionClock() {
  let previous: number | null = null, elapsed = 0;
  return {
    step(nowMs: number, active: boolean) {
      if (!active || !Number.isFinite(nowMs)) { previous = null; return elapsed; }
      if (previous !== null) elapsed += Math.min(.1, Math.max(0, (nowMs - previous) / 1000));
      previous = nowMs;
      return elapsed;
    },
    pause() { previous = null; },
    get elapsed() { return elapsed; },
  };
}

export function bridgeActivityRunning(playing: boolean, visible: boolean,
  groups: Readonly<Record<BridgeActivityGroup, boolean>>, waterVisible = false, waterWaves = false) {
  return playing && visible && (groups.traffic || groups.vessels || groups.trains || (waterVisible && waterWaves));
}
