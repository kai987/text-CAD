"""Physical R03 preflight shared by source tests and saved-STEP validation.

Swept corridors enclose the actual vehicles, wheels, decks and transverse
beams over the complete demonstration paths, including the flat 49m joint.
This is geometric interference checking, not a railway clearance certificate.
"""
from math import cos, sin

from checks.seto_r02_baseline import ALLOWED_ORIGINAL, ANCHOR_NAMES, FLOORBEAM_NAMES


def intersection_volume(first, second):
    common = first.intersect(second)
    return sum(abs(part.volume) for part in common) if common else 0.


def prism_vertices(spec):
    return [point for base in spec['outline'] for point in
            (base, [base[i]+spec['extrusion'][i] for i in range(3)])]


def _graded_corridors(bd, low, high, y0, y1, bottom, top, p):
    """Piecewise-linear native solid sweep, with both grade breaks explicit."""
    half = p['shared_anchor_half_length_mm']
    stations = [low, *[x for x in (-half, half) if low < x < high], high]
    pieces = []
    for a, b in zip(stations, stations[1:]):
        rings = []
        for x in (a, b):
            fall = .01*max(abs(x), half)
            rings.append(bd.Wire.make_polygon([(x,y0,bottom-fall), (x,y1,bottom-fall),
                (x,y1,top-fall), (x,y0,top-fall)], close=True))
        pieces.append(bd.Solid.make_loft(rings, ruled=True))
    return pieces


def train_local_extents(specs, actors):
    """Undo the saved rigid pose, measuring every actual carriage vertex."""
    by_name = {part['name']: part for part in specs}
    local = []
    for actor in actors:
        if actor['group'] != 'trains':
            continue
        yaw, pitch = actor['heading_rad'], actor['pitch_rad']
        cy, sy, cp, sp = cos(yaw), sin(yaw), cos(pitch), sin(pitch)
        for name in actor['part_names']:
            for point in prism_vertices(by_name[name]):
                dx,dy,dz = [point[i]-actor['origin_mm'][i] for i in range(3)]
                u,v = cy*dx+sy*dy, -sy*dx+cy*dy
                local.append((cp*u-sp*dz, v, sp*u+cp*dz))
    return {key: [operation(v[i] for v in local) for i in range(3)]
            for key, operation in [('min',min), ('max',max)]}


def physical_clearance_checks(specs, p, activity, shapes=None):
    """Return inspectable native-volume results; optionally use saved shapes."""
    import build123d as bd
    from lib.seto_bridge_geometry import cad_shape
    by_name = {part['name']:part for part in specs}
    shape_cache = dict(shapes or {})
    rows = []
    def record(name, condition, actual):
        rows.append({'check':name, 'pass':bool(condition), 'actual':actual})
    def shape(name):
        if name not in shape_cache:
            shape_cache[name]=cad_shape(by_name[name],bd)
        return shape_cache[name]

    extents = train_local_extents(specs, activity['actors'])
    # 100mm includes the rigid body's chord over the two 1% grade breaks;
    # wheel/pantograph geometry is measured above, not inferred from a label.
    train_half_width = max(abs(extents['min'][1]),abs(extents['max'][1]))+100
    train_bottom, train_top = extents['min'][2]-100, extents['max'][2]+100
    record('actual_train_envelope', train_half_width < 1700 and train_top < 5500,
           {'local_bounds_mm':extents, 'swept_half_width_mm':train_half_width,
            'swept_height_mm':train_top, 'grade_break_margin_mm':100})
    trains = [a for a in activity['actors'] if a['group']=='trains']
    for name in ANCHOR_NAMES:
        original = ALLOWED_ORIGINAL[name]
        if original['kind']=='box':
            low, high = original['bounds'][0], original['bounds'][3]
        else:
            low, high = min(x for x,z in original['outline_xz']), max(x for x,z in original['outline_xz'])
        # Full-width deck/chord/floorbeam/barrier passage, not merely one
        # nominal rail line. This also protects the road and future corridor.
        transport = _graded_corridors(bd,low-100,high+100,-16300,16300,
            p['rail_deck_z_mm']-1750,p['road_deck_z_mm']+1700,p)
        old_body = cad_shape(original,bd)
        old_overlap = sum(intersection_volume(old_body,sweep) for sweep in transport)
        new_overlap = sum(intersection_volume(shape(name),sweep) for sweep in transport)
        record('anchor:old_obstruction:'+name,old_overlap>1,round(old_overlap,3))
        record('anchor:transport_sweep:'+name,new_overlap<.01,round(new_overlap,6))
        # Each track's complete four-car consist stays in this continuous
        # sweep. Every carriage shares a leader loop, with no detached wrap.
        for lead in (a for a in trains if a['carriage_index']==0):
            y = lead['route']['fixed_mm']
            sweep = _graded_corridors(bd,low-11000,high+11000,y-train_half_width,y+train_half_width,
                p['rail_deck_z_mm']+420+train_bottom,p['rail_deck_z_mm']+420+train_top,p)
            overlap = sum(intersection_volume(shape(name),piece) for piece in sweep)
            record('anchor:actual_consist_sweep:'+name+':'+lead['train_id'],overlap<.01,round(overlap,6))

    # The old 1000mm beams project 80mm above the actual rail crest. Require
    # a measured positive collision before proving the 1200mm relocation.
    for name in FLOORBEAM_NAMES:
        original = ALLOWED_ORIGINAL[name]
        x = original['start'][0]
        fall = .01*abs(x)
        wheel_path = bd.Solid.make_box(1600,1600,900,
            plane=bd.Plane(origin=(x-800,-11300,p['rail_deck_z_mm']+420-fall)))
        old_overlap = intersection_volume(cad_shape(original,bd),wheel_path)
        new_overlap = intersection_volume(shape(name),wheel_path)
        record('floorbeam:old_wheel_obstruction:'+name,old_overlap>1,round(old_overlap,3))
        record('floorbeam:wheel_sweep:'+name,new_overlap<.01,round(new_overlap,6))

    # Entire four-car paths at their outer extrema, including couplers and
    # pitch, must remain on the modeled bridge after simultaneous wrapping.
    overhang = max(abs(extents['min'][0]),abs(extents['max'][0]))+100
    for lead in (a for a in trains if a['carriage_index']==0):
        consist = [a for a in trains if a['train_id']==lead['train_id']]
        xvalues = [endpoint+a['direction']*a['consist_offset_mm']
                   for endpoint in (lead['route']['min_mm'],lead['route']['max_mm']) for a in consist]
        low,high = min(xvalues)-overhang,max(xvalues)+overhang
        record('consist:whole_loop_on_bridge:'+lead['train_id'],
            low>=p['north_outer_end_mm'] and high<=p['south_outer_end_mm'],
            {'min_mm':low,'max_mm':high,'carriages':len(consist)})

    # Persist the full-route interference preflight as well: all foundations,
    # portals, truss members, road slabs, catenaries and rail infrastructure.
    # Rail-top contact is intentional, so the swept occupied space starts
    # 1mm above it. A 40mm roof margin covers the rigid-body grade break;
    # the contact wire itself remains outside the pantograph envelope.
    corridors=[]
    for lead in (a for a in trains if a['carriage_index']==0):
        y=lead['route']['fixed_mm']
        corridors.extend(_graded_corridors(bd,p['north_outer_end_mm'],p['south_outer_end_mm'],
            y-train_half_width,y+train_half_width,p['rail_deck_z_mm']+421,
            p['rail_deck_z_mm']+420+extents['max'][2]+40,p))
    corridor_bounds=[s.bounding_box() for s in corridors]
    candidates=0;collisions=[]
    for part in specs:
        if part['group'] not in ('foundations','towers','truss','road','railway'):
            continue
        solid=shape(part['name']);bounds=solid.bounding_box()
        for sweep,other in zip(corridors,corridor_bounds):
            if not all(getattr(bounds.max,axis)>getattr(other.min,axis)+.01 and
                       getattr(other.max,axis)>getattr(bounds.min,axis)+.01 for axis in ('X','Y','Z')):
                continue
            candidates+=1
            overlap=intersection_volume(solid,sweep)
            if overlap>.01:collisions.append({'name':part['name'],'volume_mm3':round(overlap,6)})
    record('consist:all_infrastructure_full_route_sweeps',not collisions,
           {'native_candidates':candidates,'pieces':len(corridors),'collisions':collisions})
    return rows
