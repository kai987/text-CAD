"""Parametric concept assembly derived from the approved R01 floor plans.

All source dimensions are millimetres; Z=0 and Z=2800 are finished-floor
datums. This is a concept model, not a structural or statutory design.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import radians, tan

from cadgen import build123d as bd, srgb
from shapely.geometry import box
from shapely.ops import unary_union

from .house_plan import P, Parameters, dimensions, floor_plan
from .exterior_geometry import E, exterior_window_center, wall_setback


@dataclass(frozen=True)
class GeometryParameters:
    slab_thickness: float = 200
    door_height: float = 2100
    door_leaf_thickness: float = 36
    large_window_sill: float = 900
    large_window_height: float = 1300
    small_window_sill: float = 1500
    small_window_height: float = 600
    window_frame_width: float = 45
    window_frame_depth: float = 70
    glass_thickness: float = 10
    roof_overhang: float = 450
    roof_pitch_degrees: float = 30
    roof_vertical_thickness: float = 150
    landing_thickness: float = 200


G = GeometryParameters()
COLORS = {
    "external": "#EEEAE2", "internal": "#ECE6DC", "slab": "#BFA47F",
    "roof": "#353B40", "door": "#9A7959", "frame": "#272D31",
    "glass": "#A0D6E0", "stairs": "#BA9265", "storage": "#B7A38C",
    "exterior": "#F3F0E8", "entrywood": "#B58B5A", "charcoal": "#30363B",
    "concrete": "#A7A8A3", "soffit": "#E7E5DE",
}


def named(shape, label, color, opacity=1.0):
    shape.label = label
    shape.color = srgb(COLORS[color], opacity)
    return shape


def cuboid(bounds, label=None, color=None):
    x1, y1, z1, x2, y2, z2 = bounds
    shape = bd.Box(x2-x1, y2-y1, z2-z1,
                   align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN))
    shape = shape.moved(bd.Location((x1, y1, z1)))
    return named(shape, label, color) if label else shape


def extruded_polygon(polygon, z, height):
    wire = bd.Wire.make_polygon([(x, y, z) for x, y in polygon.exterior.coords])
    holes = [bd.Wire.make_polygon([(x, y, z) for x, y in ring.coords])
             for ring in polygon.interiors]
    return bd.extrude(bd.Face(wire, holes), amount=height, dir=(0, 0, 1))


def polygons(geometry):
    if geometry.geom_type == "Polygon":
        return [geometry]
    return sorted(geometry.geoms, key=lambda p: (p.bounds, p.area))


def aperture_footprint(axis, at, start, width, thickness):
    """Exact wall footprint occupied by a shared two-dimensional aperture."""
    if axis == "h":
        return box(start, at-thickness/2, start+width, at+thickness/2)
    return box(at-thickness/2, start, at+thickness/2, start+width)


def raw_wall_footprint(floor, p=P):
    # The plan geometry deliberately cuts apertures through its entire height.
    # Refill precisely their wall footprints before cutting the 3D height range.
    filled = [floor.walls]
    filled += [aperture_footprint(d.axis, d.at, d.start, d.width,
                                  p.external_wall if d.a == "outside" else p.internal_wall)
               for d in floor.doors]
    filled += [aperture_footprint(*window, p.external_wall) for window in floor.windows]
    return unary_union(filled)


def window_vertical_range(window, g=G):
    if window[3] > 1000:
        return g.large_window_sill, g.large_window_height
    return g.small_window_sill, g.small_window_height


def opening_box(axis, at, start, width, thickness, z1, z2):
    if axis == "h":
        bounds = (start, at-thickness/2-1, z1,
                  start+width, at+thickness/2+1, z2)
    else:
        bounds = (at-thickness/2-1, start, z1,
                  at+thickness/2+1, start+width, z2)
    return cuboid(bounds)


def wall_groups(floor, p=P, g=G):
    from .exterior_geometry import facade_parts
    prefix, z = f"F{floor.number}", (floor.number-1)*p.storey_height
    h = p.storey_height-g.slab_thickness
    e = p.external_wall
    setback = wall_setback()
    outer = box(0, 0, p.width, p.depth).difference(box(e, e, p.width-e, p.depth-e))
    partitions = raw_wall_footprint(floor, p).difference(outer)
    wall_profiles = [
        ("south", box(setback, setback, p.width-setback, e)),
        ("north", box(setback, p.depth-e, p.width-setback, p.depth-setback)),
        ("west", box(setback, e, e, p.depth-e)),
        ("east", box(p.width-e, e, p.width-setback, p.depth-e)),
    ]
    cuts = [opening_box(d.axis, d.at, d.start, d.width,
                         p.external_wall if d.a == "outside" else p.internal_wall,
                         z, z+g.door_height) for d in floor.doors]
    for window in floor.windows:
        sill, wh = window_vertical_range(window, g)
        cuts.append(opening_box(*window, p.external_wall, z+sill, z+sill+wh))
    exterior = []
    for direction, profile in wall_profiles:
        wall = extruded_polygon(profile, z, h)
        wall = wall.cut(*cuts)
        exterior.append(named(wall, f"{prefix}:wall_external_{direction}", "external"))
    exterior.extend(facade_parts(floor, p, g))
    interior = []
    for i, profile in enumerate(polygons(partitions), 1):
        wall = extruded_polygon(profile, z, h).cut(*cuts)
        interior.append(named(wall, f"{prefix}:wall_partition_{i:02d}", "internal"))
    return bd.Compound(children=exterior, label=f"{prefix}:external_walls"), \
        bd.Compound(children=interior, label=f"{prefix}:partition_walls")


def door_group(floor, p=P, g=G):
    from .exterior_geometry import entrance_parts
    z = (floor.number-1)*p.storey_height
    leaves = []
    for door in floor.doors:
        leaf = opening_box(door.axis, door.at, door.start+10, door.width-20,
                           g.door_leaf_thickness-2, z+10, z+g.door_height-10)
        if door.a == "outside":
            # The original opening stays fixed; the closed leaf is flush with its outer face.
            offset = g.door_leaf_thickness/2-door.at
            leaf = leaf.moved(bd.Location((0, offset, 0) if door.axis == "h" else (offset, 0, 0)))
        leaves.append(named(leaf, f"F{floor.number}:{door.id}_door_{door.kind}",
                            "entrywood" if door.a == "outside" else "door"))
    leaves.extend(entrance_parts(floor, p, g))
    return bd.Compound(children=leaves, label=f"F{floor.number}:doors")


def window_group(floor, p=P, g=G):
    from .exterior_geometry import exterior_window_parts
    z = (floor.number-1)*p.storey_height
    windows = []
    fw = g.window_frame_width
    for i, window in enumerate(floor.windows, 1):
        axis, at, start, width = window
        at = exterior_window_center(axis, at, p, g)
        sill, height = window_vertical_range(window, g)
        bottom = z+sill
        label = f"F{floor.number}:W{i:02d}"
        if axis == "h":
            frame_bounds = [
                (start, at-g.window_frame_depth/2, bottom, start+width, at+g.window_frame_depth/2, bottom+fw),
                (start, at-g.window_frame_depth/2, bottom+height-fw, start+width, at+g.window_frame_depth/2, bottom+height),
                (start, at-g.window_frame_depth/2, bottom+fw, start+fw, at+g.window_frame_depth/2, bottom+height-fw),
                (start+width-fw, at-g.window_frame_depth/2, bottom+fw, start+width, at+g.window_frame_depth/2, bottom+height-fw),
            ]
            glass_bounds = (start+fw, at-g.glass_thickness/2, bottom+fw,
                            start+width-fw, at+g.glass_thickness/2, bottom+height-fw)
        else:
            frame_bounds = [
                (at-g.window_frame_depth/2, start, bottom, at+g.window_frame_depth/2, start+width, bottom+fw),
                (at-g.window_frame_depth/2, start, bottom+height-fw, at+g.window_frame_depth/2, start+width, bottom+height),
                (at-g.window_frame_depth/2, start, bottom+fw, at+g.window_frame_depth/2, start+fw, bottom+height-fw),
                (at-g.window_frame_depth/2, start+width-fw, bottom+fw, at+g.window_frame_depth/2, start+width, bottom+height-fw),
            ]
            glass_bounds = (at-g.glass_thickness/2, start+fw, bottom+fw,
                            at+g.glass_thickness/2, start+width-fw, bottom+height-fw)
        frame = bd.Compound(children=[cuboid(b, f"{label}:frame_{j}", "frame")
                                      for j, b in enumerate(frame_bounds, 1)],
                            label=f"{label}:frame")
        glass = named(cuboid(glass_bounds), f"{label}:glass", "glass", 0.45)
        windows.append(bd.Compound(children=[frame, glass,
                                             *exterior_window_parts(window, floor.number, i, p, g)], label=label))
    return bd.Compound(children=windows, label=f"F{floor.number}:windows")


def stair_group(p=P, g=G):
    d = dimensions(p)
    sx, sy, xm, ym = (d[k] for k in ("sx", "sy", "xmax", "ymax"))
    rise = p.storey_height/p.risers
    per_flight = p.risers//2
    landing_y = sy+(per_flight-1)*p.tread
    half_z = per_flight*rise
    lower, upper = [], []
    for i in range(per_flight-1):
        lower.append(cuboid((sx, sy+i*p.tread, 0,
                              sx+p.stair_width, sy+(i+1)*p.tread, (i+1)*rise),
                             f"stairs:lower_tread_{i+1:02d}", "stairs"))
        upper.append(cuboid((xm-p.stair_width, landing_y-(i+1)*p.tread, half_z-g.landing_thickness,
                              xm, landing_y-i*p.tread, half_z+(i+1)*rise),
                             f"stairs:upper_tread_{i+1:02d}", "stairs"))
    # The F2 slab's own south opening edge forms the eighth return-flight
    # riser. No extra panel consumes any of the final 260 mm tread.
    landing = cuboid((sx, landing_y, half_z-g.landing_thickness,
                       xm, ym, half_z), "stairs:mid_landing", "stairs")
    return bd.Compound(children=[
        bd.Compound(children=lower, label="stairs:lower_flight"), landing,
        bd.Compound(children=upper, label="stairs:upper_flight")], label="stairs")


def slab_for_floor(number, p=P, g=G):
    z = (number-1)*p.storey_height
    setback = wall_setback()
    slab = cuboid((setback, setback, z-g.slab_thickness,
                    p.width-setback, p.depth-setback, z))
    if number == 2:
        stair_room = next(r for r in floor_plan(2, p).rooms if r.id == "stairs")
        x1, y1, x2, y2 = stair_room.shape.bounds
        slab = slab.cut(cuboid((x1, y1, z-g.slab_thickness-1, x2, y2, z+1)))
    return named(slab, f"F{number}:floor_slab", "slab")


def section_extrusion(points_xz, y, depth):
    face = bd.Face(bd.Wire.make_polygon([(x, y, z) for x, z in points_xz]))
    return bd.extrude(face, amount=depth, dir=(0, 1, 0))


def roof_group(p=P, g=G):
    from .exterior_geometry import roof_detail_parts
    slope = tan(radians(g.roof_pitch_degrees))
    zbase, ridge_x = 2*p.storey_height, p.width/2
    peak = zbase+ridge_x*slope
    overhang, thick = g.roof_overhang, g.roof_vertical_thickness
    eave_z = zbase-overhang*slope
    west = section_extrusion([(-overhang, eave_z), (ridge_x, peak),
                              (ridge_x, peak+thick), (-overhang, eave_z+thick)],
                             -overhang, p.depth+2*overhang)
    east = section_extrusion([(ridge_x, peak), (p.width+overhang, eave_z),
                              (p.width+overhang, eave_z+thick), (ridge_x, peak+thick)],
                             -overhang, p.depth+2*overhang)
    gable_section = [(0, zbase), (p.width, zbase), (ridge_x, peak)]
    setback = wall_setback()
    south = section_extrusion(gable_section, setback, p.external_wall-setback)
    north = section_extrusion(gable_section, p.depth-p.external_wall, p.external_wall-setback)
    ceiling = cuboid((setback, setback, zbase-g.slab_thickness,
                       p.width-setback, p.depth-setback, zbase),
                     "roof:attic_ceiling_slab", "slab")
    return bd.Compound(children=[named(west, "roof:west_plane", "roof"),
                                  named(east, "roof:east_plane", "roof"),
                                  named(south, "roof:south_gable_wall", "external"),
                                  named(north, "roof:north_gable_wall", "external"), ceiling,
                                  *roof_detail_parts(p, g)],
                       label="roof")


def storage_group(floor, p=P):
    z = (floor.number-1)*p.storey_height
    storage = []
    for i, (name, bounds) in enumerate(floor.fixtures, 1):
        if name not in ("靴収納", "収納", "食品棚", "収納棚"):
            continue
        x1, y1, x2, y2 = bounds
        height = 1800 if name == "靴収納" else 2100
        storage.append(cuboid((x1, y1, z, x2, y2, z+height),
                                f"F{floor.number}:storage_{i:02d}", "storage"))
    return bd.Compound(children=storage, label=f"F{floor.number}:storage_fixtures")


def house_assembly(p=P, g=G, include_roof=True):
    from .furniture_geometry import furniture_group
    from .fixture_geometry import fixture_group
    floors = []
    for number in (1, 2):
        plan = floor_plan(number, p)
        external, internal = wall_groups(plan, p, g)
        floors.append(bd.Compound(children=[slab_for_floor(number, p, g), external, internal,
                                            door_group(plan, p, g), window_group(plan, p, g),
                                            storage_group(plan, p), fixture_group(plan, p, "house"),
                                            furniture_group(plan, "house", p)], label=f"F{number}"))
    children = floors+[stair_group(p, g)]
    if include_roof:
        children.append(roof_group(p, g))
    return bd.Compound(children=children, label="house_3d")


def geometry_manifest(p=P, g=G):
    from .furniture_geometry import furniture_manifest
    from .exterior_geometry import exterior_manifest
    exterior = exterior_manifest()
    return {
        "revision": "R03-3D", "stage": "approved_floor_plan_concept_model",
        "source_plan": "src/lib/house_plan.py", "units": "mm",
        "plan_parameters": asdict(p), "geometry_parameters": asdict(g),
        "floor_datums_mm": [0, p.storey_height], "roof_base_mm": 2*p.storey_height,
        "axis_convention": "X east, Y north, Z up; GLB is metre-scaled Y-up",
        "exterior": exterior,
        "assumptions": [
            "7280 × 7280 mm 外轮廓、2800 mm 层高及北向/南入口是演示假设。",
            "已确认 R01 房间净边界和门窗平面位置直接复用；一、二层厕所上下对齐。",
            "楼层完成面基准 Z=0、2800 mm；楼板暂定厚200 mm并位于完成面以下，墙净高2600 mm。",
            "二层楼板为整个1900 × 2720 mm 梯间净边界开洞，未覆盖楼梯；屋顶下另设200 mm概念顶板。",
            "门洞高2100 mm；门扇厚36 mm，以关闭位置表达，侧边及上下留10 mm示意间隙。",
            "大窗宽大于1000 mm：窗台900/窗高1300 mm；其他窗：窗台1500/窗高600 mm。",
            "窗框面宽45 mm、进深70 mm，玻璃厚10 mm；窗框位于外侧墙带；门窗尚未选型，洞口为毛洞尺寸。",
            "切妻屋根屋脊沿南北方向，坡度30度、四周屋檐450 mm、竖向厚度150 mm均可改参数。",
            "U型楼梯16踢面×175 mm，踏面260 mm，梯宽900 mm，中间平台900 mm深；各半梯7踏步加平台/二层地坪为第8级。",
            "梯段采用概念阶梯体，平台厚200 mm、上跑实体底与平台底同高以形成接触；二层楼板洞口南缘为末级踢面，未另设侵占踏面的面板。",
            "鞋柜高1800 mm、其余收纳柜2100 mm，位置沿用确认平面；家具与卫浴根据公开尺寸参考进行原创参数化建模，未选实际产品。",
            "移门门袋、楼梯扶手、结构连接、实际屋面/墙体层次及设备系统留待深化。",
            "未验证结构、消防、建筑法规、实际楼梯头部净空或建筑确认申报要求。",
        ] + exterior["assumptions"],
        "interior_reference": "references/interior-furnishings.md",
        "interior_model": "Original parametric furniture and fixtures; visual dimensions are assumptions, not manufacturer CAD.",
        "furnishings": [furniture_manifest(floor_plan(n, p), "house", p) for n in (1, 2)],
        "outputs": ["STEP/house_3d.step", "GLB/house_3d.glb"],
    }
