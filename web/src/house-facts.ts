interface FactSource {
  plan_parameters: Record<string, number | boolean>;
  geometry_parameters: Record<string, number>;
}
export type HouseFacts = Record<string, number | string>;

export function createHouseFacts(source: FactSource): HouseFacts {
  const p = source.plan_parameters, g = source.geometry_parameters;
  const number = (values: Record<string, unknown>, key: string): number => {
    const value = values[key];
    if (typeof value !== 'number' || !Number.isFinite(value)) throw new Error(`Missing CAD fact: ${key}`);
    return value;
  };
  const width = number(p, 'width'), depth = number(p, 'depth');
  const storeyHeight = number(p, 'storey_height'), risers = number(p, 'risers');
  const balconyDepth = number(p, 'balcony_depth'), rail = number(p, 'balcony_rail_thickness');
  const balconyClearWidth = number(p, 'balcony_width') - 2 * rail;
  const balconyClearDepth = balconyDepth - rail;
  return {
    width, depth, storeyHeight, balconyWidth: number(p, 'balcony_width'), balconyDepth, balconyClearWidth, balconyClearDepth,
    balconyClearArea: balconyClearWidth * balconyClearDepth / 1e6,
    externalWall: number(p, 'external_wall'), internalWall: number(p, 'internal_wall'),
    southWindowSill: number(p, 'south_window_sill'), southWindowHeight: number(p, 'south_window_height'), southWindowWidths: ['south_living_window_width', 'south_master_window_width', 'south_bedroom_window_width'].map(key => number(p, key)).join('/'),
    toiletWidth: number(p, 'toilet_width'), toiletDepth: number(p, 'toilet_depth'),
    risers, rise: storeyHeight / risers, tread: number(p, 'tread'), stairWidth: number(p, 'stair_width'),
    slabThickness: number(g, 'slab_thickness'), clearHeight: storeyHeight - number(g, 'slab_thickness'),
    doorHeight: number(g, 'door_height'), doorLeafThickness: number(g, 'door_leaf_thickness'),
    largeWindowSill: number(g, 'large_window_sill'), largeWindowHeight: number(g, 'large_window_height'),
    smallWindowSill: number(g, 'small_window_sill'), smallWindowHeight: number(g, 'small_window_height'),
    windowFrameWidth: number(g, 'window_frame_width'), windowFrameDepth: number(g, 'window_frame_depth'),
    glassThickness: number(g, 'glass_thickness'), roofPitch: number(g, 'roof_pitch_degrees'),
    roofOverhang: number(g, 'roof_overhang'), roofThickness: number(g, 'roof_vertical_thickness'),
    landingThickness: number(g, 'landing_thickness'), shoeCabinetHeight: number(g, 'shoe_cabinet_height'),
    storageCabinetHeight: number(g, 'storage_cabinet_height'),
  };
}
export function renderFacts(template: string, facts: HouseFacts): string {
  return template.replace(/\{(\w+)\}/g, (_, key: string) => {
    if (!Object.hasOwn(facts, key)) throw new Error(`Unknown CAD fact: ${key}`);
    const value = facts[key];
    return typeof value === 'number' ? String(Number(value.toFixed(4))) : value;
  });
}
