"""Editable Japanese suburban river demonstration in millimetres, Z up.

This is an invented landscape section, not surveyed terrain, flood analysis or
an engineered bridge. Bank offsets are measured in X rather than normal to the
curved centreline; the gentle curve and exact convention are stated explicitly.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from math import ceil, cos, hypot, pi, sin, sqrt

from cadgen import build123d as bd, srgb


@dataclass(frozen=True)
class RiverParameters:
    length: float = 180000
    width: float = 80000
    water_width: float = 18000
    curve_amplitude: float = 3500
    bed_z: float = -900
    water_z: float = 0
    platform_z: float = 1000
    crest_z: float = 3000
    base_bottom_z: float = -2200
    terrain_bottom_z: float = -1800
    submerged_bank_run: float = 2000
    revetment_run: float = 3000
    platform_width: float = 2000
    grass_slope_run: float = 3500
    path_width: float = 3000
    path_thickness: float = 160
    armor_thickness: float = 150
    bridge_y: float = 15000
    bridge_width: float = 4000
    bridge_top_z: float = 3100
    bridge_thickness: float = 260
    bridge_beam_depth: float = 750
    bridge_rail_height: float = 1200
    approach_length: float = 800
    stair_width: float = 1800
    stair_count: int = 14
    sample_count: int = 36


R = RiverParameters()
REVISION = "RIVER-R01"
GROUPS = (
    "Terrain:base", "River:bed", "River:water", "Banks:left", "Banks:right",
    "Paths:left", "Paths:right", "Bridge:deck", "Bridge:beams", "Bridge:rails",
    "Bridge:abutments", "Bridge:approaches", "Access:stairs", "Landscape:trees",
    "Landscape:benches", "Lighting:fixtures",
)
COLORS = {
    "earth": "#8E7965", "bed": "#958B72", "water": "#53B4C5",
    "stone": "#ACAFAD", "stone_dark": "#8C9694", "gravel": "#C9C1A8",
    "grass": "#7CA168", "paving": "#CECAC0", "concrete": "#B4B5B1",
    "metal": "#3A535A", "wood": "#A97D51", "trunk": "#795B43",
    "leaves": "#779860", "leaves_dark": "#618051", "sakura": "#EEC7D4",
    "lamp": "#FFF0C8",
}


def validate_parameters(p=R):
    if p.length <= 0 or p.width <= 0 or p.water_width <= 0:
        raise ValueError("River length, envelope width and water width must be positive")
    if not p.terrain_bottom_z < p.bed_z < p.water_z < p.platform_z < p.crest_z <= p.bridge_top_z:
        raise ValueError("River elevations must follow the documented cross-section order")
    if p.sample_count < 4 or p.stair_count < 2:
        raise ValueError("The river needs at least four longitudinal samples and two stair risers")
    if any(value <= 0 for value in (p.revetment_run, p.platform_width, p.grass_slope_run,
                                    p.path_width, p.path_thickness, p.approach_length,
                                    p.bridge_width, p.bridge_thickness, p.stair_width)):
        raise ValueError("Bank, path, bridge and stair dimensions must be positive")
    if p.curve_amplitude < 0 or section_offsets(p)["path_outer"] + p.curve_amplitude >= p.width / 2:
        raise ValueError("Bank and path offsets must fit inside the fixed terrain envelope")
    if not 0 < p.submerged_bank_run < p.water_width / 2:
        raise ValueError("Submerged bank slopes must leave a positive flat-bed width")
    if abs(p.bridge_y) + p.bridge_width / 2 >= p.length / 2:
        raise ValueError("Bridge must be inside the modelled river reach")
    if p.approach_length >= p.path_width / 2:
        raise ValueError("Bridge approach must fit within the outer half of each crest path")


def center_x(y, p=R):
    return p.curve_amplitude * sin(2 * pi * y / p.length)


def sample_ys(p=R):
    return [-p.length / 2 + p.length * i / p.sample_count for i in range(p.sample_count + 1)]


def section_offsets(p=R):
    water = p.water_width / 2
    platform_inner = water + p.revetment_run
    platform_outer = platform_inner + p.platform_width
    path_inner = platform_outer + p.grass_slope_run
    return {"bed_inner": water-p.submerged_bank_run, "water_edge": water, "platform_inner": platform_inner,
            "platform_outer": platform_outer, "path_inner": path_inner,
            "path_outer": path_inner + p.path_width,
            "path_center": path_inner + p.path_width / 2}


def channel_edges(y, p=R):
    x = center_x(y, p)
    return x - p.water_width / 2, x + p.water_width / 2


def walkway_centres(y, p=R):
    x, offset = center_x(y, p), section_offsets(p)["path_center"]
    return x - offset, x + offset


def cross_section(y=0, p=R):
    o, x = section_offsets(p), center_x(y, p)
    right = [(o["bed_inner"], p.bed_z), (o["water_edge"], p.water_z), (o["platform_inner"], p.platform_z),
             (o["platform_outer"], p.platform_z), (o["path_inner"], p.crest_z),
             (o["path_outer"], p.crest_z)]
    return [(x - offset, z) for offset, z in reversed(right)] + [(x + offset, z) for offset, z in right]


def bridge_dimensions(p=R):
    left, right = walkway_centres(p.bridge_y, p)
    return {"y": p.bridge_y, "start_x": left, "end_x": right,
            "span": right - left, "clear_water_width": p.water_width,
            "width": p.bridge_width, "top_z": p.bridge_top_z,
            "underside_z": p.bridge_top_z - p.bridge_thickness,
            "beam_bottom_z": p.bridge_top_z - p.bridge_thickness - p.bridge_beam_depth,
            "approach_length": p.approach_length,
            "approach_rise": p.bridge_top_z - p.crest_z,
            "structural_calculation": None}


def stairs_positions(p=R):
    # Locations scale with the reach so edited lengths retain both access points.
    o = section_offsets(p)
    return [{"id": f"{side}_access", "side": side, "y": y,
             "width": p.stair_width, "lower_x": center_x(y, p) + sign * o["platform_outer"],
             "upper_x": center_x(y, p) + sign * o["path_inner"],
             "bottom_z": p.platform_z, "top_z": p.crest_z,
             "risers": p.stair_count, "riser": (p.crest_z - p.platform_z) / p.stair_count,
             "tread": p.grass_slope_run / p.stair_count}
            for side, sign, y in (("left", -1, -p.length * 4 / 15),
                                  ("right", 1, p.length * 4 / 15))]


def tree_positions(p=R):
    result = []
    for side, sign in (("left", -1), ("right", 1)):
        for i, fraction in enumerate((-.41, -.31, -.18, -.03, .23, .36, .44), 1):
            y = p.length * fraction
            result.append({"id": f"{side}_{i:02d}", "side": side,
                           "x": center_x(y, p) + sign * (section_offsets(p)["path_outer"] + 6000 + (i % 2) * 2300),
                           "y": y, "z": p.crest_z, "radius": 2100 + (i % 3) * 180,
                           "kind": "sakura" if i % 3 != 0 else "green"})
    return result


def _tree_variation(tree):
    """Stable variation avoids changing the planting every time it is exported."""
    digest = sha256(str(tree["id"]).encode("utf-8")).digest()
    return {
        "phase": 2*pi*digest[0]/255,
        "height": 180*(digest[1]/255-.5),
        "lean_x": 230*(digest[2]/255-.5),
        "lean_y": 230*(digest[3]/255-.5),
        "samples": [value/255 for value in digest[4:]],
    }


def tree_crown_lobes(tree):
    """Return the fixed planting envelope as absolute CAD-mm ellipsoids.

    Each item has ``centre: [X, Y, Z]`` and ``radii: [rx, ry, rz]``. Nine
    overlapping solids describe the crown without requiring an expensive union.
    Their horizontal projection remains inside the recorded circular footprint.
    STEP uses these envelopes; the GLB exporter places leaf/blossom geometry
    inside their recorded bounding boxes and planting radius while retaining
    the named crown occurrence.
    """
    x, y, z, r = (tree[key] for key in ("x", "y", "z", "radius"))
    variation = _tree_variation(tree)
    samples = variation["samples"]
    lobes = [{"centre": [x+variation["lean_x"], y+variation["lean_y"],
                          z+4300+variation["height"]],
              "radii": [r*.55, r*.52, r*.49]}]
    for i in range(8):
        angle = variation["phase"]+i*pi/4+(.11*(samples[i]-.5))
        distance = r*(.41+.06*samples[i+8])
        # An asymmetric crown has open spaces between smaller peripheral lobes.
        rx = r*(.37+.09*samples[i+16])
        ry = r*(.36+.09*samples[(i+20) % len(samples)])
        rz = r*(.34+.13*samples[(i+24) % len(samples)])
        # The foliage exporter uses lobe AABBs, so even their corners must fit.
        horizontal_scale = min(1, (.975*r-distance)/hypot(rx, ry))
        rx, ry = rx*horizontal_scale, ry*horizontal_scale
        lobes.append({"centre": [x+distance*cos(angle), y+distance*sin(angle),
                                  z+4080+variation["height"]+640*(samples[i+4]-.5)],
                      "radii": [rx, ry, rz]})
    return lobes


def _tree_stem_points(tree):
    x, y, z = (tree[key] for key in ("x", "y", "z"))
    variation = _tree_variation(tree)
    lean_x, lean_y = variation["lean_x"], variation["lean_y"]
    return [((x, y, z), 185),
            ((x+lean_x*.22, y+lean_y*.17, z+1150), 133),
            ((x+lean_x*.63, y+lean_y*.58, z+2450), 83),
            ((x+lean_x, y+lean_y, z+3550+variation["height"]*.4), 43)]


def tree_branch_segments(tree):
    """Deterministic tapered branch axes and radii in absolute CAD millimetres."""
    x, y, z, r = (tree[key] for key in ("x", "y", "z", "radius"))
    variation = _tree_variation(tree)
    segments = []
    for i, lobe in enumerate(tree_crown_lobes(tree)[1:]):
        sample = variation["samples"][i]
        angle = variation["phase"]+i*pi/4
        stem_fraction = .55+.35*sample
        start = [x+variation["lean_x"]*stem_fraction,
                 y+variation["lean_y"]*stem_fraction, z+2100+760*sample]
        end = [x+(lobe["centre"][0]-x)*.78,
               y+(lobe["centre"][1]-y)*.78,
               lobe["centre"][2]-r*.19]
        segments.append({"start": start, "end": end,
                         "base_radius": 85-16*sample, "top_radius": 38-9*sample})
        for sign in (-1, 1):
            fork_angle = angle+sign*(.34+.15*sample)
            distance = r*(.55+.07*sample)
            tip = [x+distance*cos(fork_angle), y+distance*sin(fork_angle),
                   lobe["centre"][2]+r*(.05+.13*sample)]
            segments.append({"start": end, "end": tip,
                             "base_radius": 37-8*sample, "top_radius": 12+5*sample})
    return segments


def _tree_trunk(tree):
    stem = _tree_stem_points(tree)
    segments = []
    for (start, bottom_radius), (end, top_radius) in zip(stem, stem[1:]):
        # Horizontal cross-sections keep the root exactly on the terrain datum.
        rings = [bd.Wire.make_circle(radius, bd.Plane(origin=point))
                 for point, radius in ((start, bottom_radius), (end, top_radius))]
        segments.append(bd.Solid.make_loft(rings, ruled=True))
    return _named(bd.Compound(segments), f"Landscape:trees:{tree['id']}:trunk", "trunk")


def _tree_branches(tree):
    solids = []
    for branch in tree_branch_segments(tree):
        direction = tuple(b-a for a, b in zip(branch["start"], branch["end"]))
        length = sqrt(sum(value*value for value in direction))
        solids.append(bd.Solid.make_cone(branch["base_radius"], branch["top_radius"], length,
                                        bd.Plane(origin=branch["start"], z_dir=direction)))
    # Positional solids deliberately remain one assembly leaf and one GLB mesh.
    return _named(bd.Compound(solids), f"Landscape:trees:{tree['id']}:branches", "trunk")


def _tree_crown(tree):
    solids = [bd.Sphere(1).scale(tuple(lobe["radii"]))
              .moved(bd.Location(tuple(lobe["centre"]))) for lobe in tree_crown_lobes(tree)]
    return _named(bd.Compound(solids), f"Landscape:trees:{tree['id']}:crown",
                  "sakura" if tree["kind"] == "sakura" else "leaves_dark")


def bench_positions(p=R):
    return [{"id": f"{side}_{i:02d}", "side": side,
             "x": center_x(y, p) + sign * (section_offsets(p)["path_outer"] + 1100),
             "y": y, "z": p.crest_z}
            for side, sign in (("left", -1), ("right", 1))
            for i, y in enumerate((-p.length * .36, -p.length * .09, p.length * .29), 1)]


def lamp_positions(p=R):
    return [{"id": f"{side}_{i:02d}", "side": side,
             "x": center_x(y, p) + sign * (section_offsets(p)["path_outer"] + 550),
             "y": y, "z": p.crest_z, "height": 4000}
            for side, sign in (("left", -1), ("right", 1))
            for i, y in enumerate((-p.length * .4, -p.length * .2, 0, p.length * .2, p.length * .4), 1)]


def _named(shape, label, color, opacity=1):
    shape.label, shape.color = label, srgb(COLORS[color], opacity)
    return shape


def _group(label, shapes):
    return bd.Compound(children=shapes, label=label)


def _box(bounds, label, color):
    x1, y1, z1, x2, y2, z2 = bounds
    return _named(bd.Box(x2-x1, y2-y1, z2-z1, align=(bd.Align.MIN,)*3)
                  .moved(bd.Location((x1, y1, z1))), label, color)


def _strip(p, start_offset, end_offset, start_z, end_z, bottom_z, label, color,
           *, fixed_outer=False, opacity=1):
    """One watertight, ruled longitudinal solid, avoiding duplicate seam faces."""
    wires = []
    for y in sample_ys(p):
        x = center_x(y, p)
        x1, x2 = x + start_offset, x + end_offset
        if fixed_outer:
            x2 = end_offset
        wires.append(bd.Wire.make_polygon([(x1, y, bottom_z), (x2, y, bottom_z),
                                           (x2, y, end_z), (x1, y, start_z)], close=True))
    return _named(bd.Solid.make_loft(wires, ruled=True), label, color, opacity)


def _shell_strip(p, start_offset, end_offset, start_z, end_z, thickness, label, color):
    """Thin armor follows the slope, with a vertical rather than normal thickness."""
    wires = []
    for y in sample_ys(p):
        x = center_x(y, p)
        wires.append(bd.Wire.make_polygon([(x+start_offset, y, start_z-thickness),
                                           (x+end_offset, y, end_z-thickness),
                                           (x+end_offset, y, end_z),
                                           (x+start_offset, y, start_z)], close=True))
    return _named(bd.Solid.make_loft(wires, ruled=True), label, color)


def _prism(vertices, direction, label, color):
    face = bd.Face(bd.Wire.make_polygon(vertices, close=True))
    return _named(bd.extrude(face, amount=direction[1], dir=(0, 1, 0)), label, color)


def _bank(side, sign, p):
    o = section_offsets(p)
    # Every band meets its neighbour at one interface, with no duplicated top.
    soil = _strip(p, sign*o["water_edge"], sign*o["platform_inner"],
                  p.water_z-p.armor_thickness, p.platform_z-p.armor_thickness,
                  p.terrain_bottom_z, f"Banks:{side}:inner_soil", "earth")
    armor = _shell_strip(p, sign*o["water_edge"], sign*o["platform_inner"],
                         p.water_z, p.platform_z, p.armor_thickness,
                         f"Banks:{side}:stone_revetment", "stone")
    platform = _strip(p, sign*o["platform_inner"], sign*o["platform_outer"],
                      p.platform_z, p.platform_z, p.terrain_bottom_z,
                      f"Banks:{side}:waterside_platform", "gravel")
    slope = _strip(p, sign*o["platform_outer"], sign*o["path_inner"],
                   p.platform_z, p.crest_z, p.terrain_bottom_z,
                   f"Banks:{side}:grass_slope", "grass")
    for stair in stairs_positions(p):
        if stair["side"] == side:
            x1, x2 = sorted((stair["lower_x"], stair["upper_x"]))
            slope = slope.cut(_box((x1, stair["y"]-p.stair_width/2,
                                    p.platform_z-20, x2,
                                    stair["y"]+p.stair_width/2, p.crest_z+20),
                                   "temporary_stair_recess", "earth"))
            _named(slope, f"Banks:{side}:grass_slope", "grass")
    under_path = _strip(p, sign*o["path_inner"], sign*o["path_outer"],
                        p.crest_z-p.path_thickness, p.crest_z-p.path_thickness,
                        p.terrain_bottom_z, f"Banks:{side}:path_subgrade", "earth")
    outer = _strip(p, sign*o["path_outer"], sign*p.width/2, p.crest_z, p.crest_z,
                   p.terrain_bottom_z, f"Banks:{side}:outer_green", "grass", fixed_outer=True)
    return _group(f"Banks:{side}", [soil, armor, platform, slope, under_path, outer])


def _bridge(p):
    d = bridge_dimensions(p)
    x1, x2, y1, y2, z = d["start_x"], d["end_x"], p.bridge_y-p.bridge_width/2, p.bridge_y+p.bridge_width/2, p.bridge_top_z
    deck = _box((x1, y1, z-p.bridge_thickness, x2, y2, z), "Bridge:deck:slab", "concrete")
    beams = [_box((x1, y-160, d["beam_bottom_z"], x2, y+160, d["underside_z"]),
                  f"Bridge:beams:girder_{i}", "metal")
             for i, y in enumerate((y1+450, y2-450), 1)]
    rails = []
    count = ceil(d["span"] / 1900)
    for side, y in (("south", y1+55), ("north", y2-55)):
        for i in range(count+1):
            x = x1+(x2-x1)*i/count
            rails.append(_box((x-40, y-40, z, x+40, y+40, z+p.bridge_rail_height),
                              f"Bridge:rails:{side}:post_{i:02d}", "metal"))
        for name, height in (("top", p.bridge_rail_height-40), ("middle", 620), ("toe", 120)):
            rails.append(_box((x1, y-30, z+height, x2, y+30, z+height+60),
                              f"Bridge:rails:{side}:{name}", "metal"))
        # Closely spaced infill is a visible proposal, without a code certification.
        for i in range(1, int(d["span"] / 240)):
            x = x1+d["span"]*i/int(d["span"] / 240)
            rails.append(_box((x-12, y-12, z+180, x+12, y+12, z+p.bridge_rail_height-40),
                              f"Bridge:rails:{side}:infill_{i:03d}", "metal"))
    abutments = [_box((x-650, y1-150, p.terrain_bottom_z, x+650, y2+150, d["beam_bottom_z"]),
                      f"Bridge:abutments:{side}", "concrete") for side, x in (("left",x1+700),("right",x2-700))]
    approaches = []
    for side, sign, x in (("left", -1, x1), ("right", 1, x2)):
        outer_x = x+sign*p.approach_length
        approaches.append(_prism([(x,y1,p.crest_z-p.path_thickness),
                                  (outer_x,y1,p.crest_z-p.path_thickness),
                                  (outer_x,y1,p.crest_z), (x,y1,z)], (0,p.bridge_width,0),
                                 f"Bridge:approaches:{side}_ramp", "concrete"))
    return [_group("Bridge:deck",[deck]), _group("Bridge:beams",beams),
            _group("Bridge:rails",rails), _group("Bridge:abutments",abutments),
            _group("Bridge:approaches",approaches)]


def _stairs(p):
    children = []
    for stair in stairs_positions(p):
        sign = -1 if stair["side"] == "left" else 1
        for i in range(p.stair_count):
            a = stair["lower_x"]+sign*i*stair["tread"]
            b = stair["lower_x"]+sign*(i+1)*stair["tread"]
            x1,x2 = sorted((a,b))
            children.append(_box((x1,stair["y"]-p.stair_width/2,p.platform_z-100,
                                  x2,stair["y"]+p.stair_width/2,p.platform_z+(i+1)*stair["riser"]),
                                 f"Access:stairs:{stair['id']}:tread_{i+1:02d}", "concrete"))
    return _group("Access:stairs",children)


def _landscape(p):
    trees, benches, lamps = [], [], []
    for tree in tree_positions(p):
        trees += [_tree_trunk(tree), _tree_branches(tree), _tree_crown(tree)]
    for bench in bench_positions(p):
        x,y,z = (bench[k] for k in ("x","y","z"))
        ident = bench["id"]
        for i, yoff in enumerate((-600,600),1):
            benches.append(_box((x-180,y+yoff-55,z,x+180,y+yoff+55,z+430),
                                f"Landscape:benches:{ident}:leg_{i}","metal"))
        benches.append(_box((x-300,y-1000,z+430,x+300,y+1000,z+510),
                            f"Landscape:benches:{ident}:seat","wood"))
        # The back sits on the outer side, so the seats face the river.
        back_x = x+(-1 if bench["side"]=="left" else 1)*250
        benches.append(_box((back_x-45,y-1000,z+510,back_x+45,y+1000,z+950),
                            f"Landscape:benches:{ident}:back","wood"))
    for lamp in lamp_positions(p):
        x,y,z = (lamp[k] for k in ("x","y","z"))
        ident = lamp["id"]
        lamps.append(_named(bd.Cylinder(65,lamp["height"],align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))
                            .moved(bd.Location((x,y,z))),f"Lighting:fixtures:{ident}:pole","metal"))
        lamps.append(_box((x-180,y-260,z+lamp["height"]-100,x+180,y+260,z+lamp["height"]+100),
                          f"Lighting:fixtures:{ident}:housing","metal"))
        lamps.append(_box((x-145,y-225,z+lamp["height"]-110,x+145,y+225,z+lamp["height"]-100),
                          f"Lighting:fixtures:{ident}:lens","lamp"))
    return [_group("Landscape:trees",trees), _group("Landscape:benches",benches), _group("Lighting:fixtures",lamps)]


def _water_volume(p):
    """Trapezoidal water meets both submerged slopes at the exact waterline."""
    offsets=section_offsets(p)
    wires=[]
    for y in sample_ys(p):
        x=center_x(y,p)
        wires.append(bd.Wire.make_polygon([
            (x-offsets["bed_inner"],y,p.bed_z),(x+offsets["bed_inner"],y,p.bed_z),
            (x+offsets["water_edge"],y,p.water_z),(x-offsets["water_edge"],y,p.water_z),
        ],close=True))
    return _named(bd.Solid.make_loft(wires,ruled=True),"River:water:surface_volume","water",opacity=.62)


def river_assembly(p=R):
    validate_parameters(p)
    o = section_offsets(p)
    children = [
        _group("Terrain:base",[_box((-p.width/2,-p.length/2,p.base_bottom_z,
                                    p.width/2,p.length/2,p.terrain_bottom_z),"Terrain:base:soil_block","earth")]),
        _group("River:bed",[
            _strip(p,-o["bed_inner"],o["bed_inner"],p.bed_z,p.bed_z,
                   p.terrain_bottom_z,"River:bed:channel","bed"),
            *[_strip(p,sign*o["bed_inner"],sign*o["water_edge"],p.bed_z,p.water_z,
                      p.terrain_bottom_z,f"River:bed:{side}_submerged_slope","bed")
              for side,sign in (("left",-1),("right",1))],
        ]),
        _group("River:water",[_water_volume(p)]),
    ]
    for side, sign in (("left",-1),("right",1)):
        children.append(_bank(side,sign,p))
        paving = _strip(p,sign*o["path_inner"],sign*o["path_outer"],p.crest_z,p.crest_z,
                        p.crest_z-p.path_thickness,f"Paths:{side}:paving","paving")
        # Real recesses prevent overlapping paving and bridge ramps/abutments.
        d = bridge_dimensions(p); x = d["start_x"] if side=="left" else d["end_x"]
        paving = paving.cut(_box((x-p.approach_length,p.bridge_y-p.bridge_width/2,
                                  p.crest_z-p.path_thickness-20,x+p.approach_length,
                                  p.bridge_y+p.bridge_width/2,p.bridge_top_z+20),"temporary_bridge_path_recess","earth"))
        _named(paving,f"Paths:{side}:paving","paving")
        children.append(_group(f"Paths:{side}",[paving]))
    children += _bridge(p)+[_stairs(p)]+_landscape(p)
    return _group("river_demo",children)


def geometry_manifest(p=R, assembly=None):
    validate_parameters(p)
    result = {
        "schema_version":1,"status":"concept_demo_only",
        "revision":REVISION,"units":"mm","type":"invented Japanese suburban river demonstration",
        "coordinate_system":{"X":"east","Y":"north","Z":"elevation","flow":"north (+Y) to south (-Y)"},
        "bank_name_convention":"left means west/-X on the plan and right east/+X; these are display labels, not formal downstream bank names",
        "parameters":asdict(p),"section_offsets":section_offsets(p),"bridge":bridge_dimensions(p),
        "stairs":stairs_positions(p),"trees":tree_positions(p),"benches":bench_positions(p),"lamps":lamp_positions(p),
        "tree_visual_style":{
            "revision":"natural_trees_v1",
            "native_crown":"deterministic ellipsoid cluster planting envelope",
            "glb_crown":"detailed leaf and blossom mesh within recorded crown boxes and planting radius",
            "seed":"tree id",
            "footprint":"all trunk, branch and crown geometry stays inside each recorded XY radius",
        },
        "groups":list(GROUPS),"centreline_formula":"x = curve_amplitude * sin(2*pi*y/length)",
        "centreline_samples":[[center_x(y,p),y] for y in sample_ys(p)],
        "assumptions":[
            "All dimensions, elevations, materials and locations are demonstration assumptions.",
            "No real river, parcel, flood level, road boundary or surveyed terrain is represented.",
            "Bank and walkway widths are X offsets, not surveyed normal-to-centreline widths.",
            "The smooth centreline is represented by ruled solid segments at saved longitudinal samples.",
            "The 38 m bridge is a visual span proposal without intermediate in-channel piers; section sizes and strength are not calculated.",
            f"Access stairs use {p.stair_count} demonstration risers of {(p.crest_z-p.platform_z)/p.stair_count:.3f} mm with {p.grass_slope_run/p.stair_count:.3f} mm treads; accessible routes and code compliance are not validated.",
            "Armor thickness is vertical, not the thickness normal to the sloped surface.",
            "No hydraulic capacity, design flood level, scouring depth, foundation capacity or statutory compliance has been calculated.",
        ],
        "engineering":{"hydraulic_capacity":None,"bridge_strength":None,"foundation_capacity":None,"statutory_compliance":None},
        "glb_coordinates":{"units":"m","up_axis":"Y","mapping_from_CAD":"(X, Y, Z) mm -> (X, Z, -Y) m / 1000"},
    }
    if assembly is not None:
        bbox=assembly.bounding_box()
        result["bbox"]={"min":[bbox.min.X,bbox.min.Y,bbox.min.Z],"max":[bbox.max.X,bbox.max.Y,bbox.max.Z]}
        result["parts"]=[{"name":child.label,"valid":child.is_valid,"solids":len(child.solids())}
                          for child in assembly.children]
    return result
