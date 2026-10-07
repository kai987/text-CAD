"""Parametric concept assembly derived from the user-confirmed floor plans.

All source dimensions are millimetres; Z=0 and Z=2800 are finished-floor
datums. This is a concept model, not a structural or statutory design.
"""
from __future__ import annotations

from .orientation import orient_shape, orient_record

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
    stair_tread_thickness: float = 60
    stair_stringer_width: float = 40
    stair_stringer_depth: float = 200
    shoe_cabinet_height: float = 1800
    storage_cabinet_height: float = 2000


G = GeometryParameters()
COLORS = {
    "external": "#EEEAE2", "internal": "#ECE6DC", "slab": "#BFA47F",
    "roof": "#353B40", "door": "#9A7959", "frame": "#272D31",
    "glass": "#A0D6E0", "stairs": "#BA9265", "storage": "#B7A38C",
    "exterior": "#F3F0E8", "entrywood": "#B58B5A", "charcoal": "#30363B",
    "concrete": "#A7A8A3", "soffit": "#E7E5DE",
    "attic_wood": "#C5AD8C", "attic_lining": "#EEE9DF",
    "site_concrete": "#A7A8A3", "site_soil": "#806951", "site_gravel": "#C2BDB2",
    "site_paving": "#B8B9B5", "site_lawn": "#79925C", "site_shrub": "#607F48",
    "site_metal": "#30363B", "site_paint": "#F4F3EB",
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
                                  p.external_wall if {'outside','balcony'} & {d.a,d.b} else p.internal_wall)
               for d in floor.doors]
    filled += [aperture_footprint(*window, p.external_wall) for window in floor.windows]
    return unary_union(filled).intersection(box(0,0,p.width,p.depth))


def window_vertical_range(window, g=G, p=P):
    from .house_redesign_plan import south_floor_window
    if south_floor_window(window,p):
        return p.south_window_sill,p.south_window_height
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
    if floor.number==1:
        d=dimensions(p)
        # Stair-under partitions are modelled below the stepped soffit, rather
        # than extruded through the upper flight at ordinary storey height.
        partitions=partitions.difference(box(d['xmax']-p.stair_width,d['sy'],d['xmax'],
                                             d['sy']+(p.risers//2-1)*p.tread))
    wall_profiles = [
        ("south", box(setback, setback, p.width-setback, e)),
        ("north", box(setback, p.depth-e, p.width-setback, p.depth-setback)),
        ("west", box(setback, e, e, p.depth-e)),
        ("east", box(p.width-e, e, p.width-setback, p.depth-e)),
    ]
    cuts = [opening_box(d.axis, d.at, d.start, d.width,
                         p.external_wall if {'outside','balcony'} & {d.a,d.b} else p.internal_wall,
                         z, z+g.door_height) for d in floor.doors]
    for window in floor.windows:
        sill, wh = window_vertical_range(window, g, p)
        cuts.append(opening_box(*window, p.external_wall, z+sill, z+sill+wh))
    exterior = []
    for direction, profile in wall_profiles:
        wall = extruded_polygon(profile, z, h)
        wall = wall.cut(*cuts)
        exterior.append(named(wall, f"{prefix}:wall_external_{direction}", "external"))
    exterior.extend(facade_parts(floor, p, g, include_plinth=False))
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
        if door.kind == 'open':
            continue
        if door.kind=='bypass':
            for i in range(2):
                start=door.start+10+i*(door.width-30)/2
                width=(door.width-30)/2+10
                at=door.at+(-20 if i==0 else 20)
                frame=opening_box('h',at,start,width,32,z+10,z+g.door_height-10)
                glass=opening_box('h',at,start+45,width-90,8,z+75,z+g.door_height-55)
                tool=opening_box('h',at,start+45,width-90,36,z+75,z+g.door_height-55)
                leaves.extend([named(frame.cut(tool),f'F{floor.number}:{door.id}_slider_frame_{i+1}','frame'),
                               named(glass,f'F{floor.number}:{door.id}_slider_glass_{i+1}','glass',.45)])
            continue
        leaf = opening_box(door.axis, door.at, door.start+10, door.width-20,
                           g.door_leaf_thickness-2, z+10, z+g.door_height-10)
        if 'balcony' in (door.a,door.b):
            glazing=opening_box(door.axis,door.at,door.start+55,door.width-110,
                                g.door_leaf_thickness,z+450,z+g.door_height-55)
            leaf=leaf.cut(glazing)
            glass=opening_box(door.axis,door.at,door.start+55,door.width-110,
                              g.glass_thickness-2,z+450,z+g.door_height-55)
            leaves.append(named(glass,f'F{floor.number}:{door.id}_door_glass','glass',.45))
        if door.a == "outside":
            # The original opening stays fixed; the closed leaf is flush with its outer face.
            offset = g.door_leaf_thickness/2-door.at
            leaf = leaf.moved(bd.Location((0, offset, 0) if door.axis == "h" else (offset, 0, 0)))
        leaves.append(named(leaf, f"F{floor.number}:{door.id}_door_{door.kind}",
                            "entrywood" if door.a == "outside" else 'frame' if 'balcony' in (door.a,door.b) else "door"))
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
        sill, height = window_vertical_range(window, g, p)
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
        glass_shape=cuboid(glass_bounds)
        from .house_redesign_plan import south_floor_window
        sash=[]
        if south_floor_window(window,p):
            mid=start+width/2
            divider=cuboid((mid-fw/2,at-g.window_frame_depth/2,bottom+fw,
                            mid+fw/2,at+g.window_frame_depth/2,bottom+height-fw))
            glass_shape=glass_shape.cut(divider)
            sash=[named(divider,f"{label}:frame_5","frame")]
        glass = named(glass_shape, f"{label}:glass", "glass", 0.45)
        windows.append(bd.Compound(children=[frame, glass, *sash,
                                             *exterior_window_parts(window, floor.number, i, p, g)], label=label))
    return bd.Compound(children=windows, label=f"F{floor.number}:windows")


@orient_shape
def stair_group(p=P, g=G):
    d = dimensions(p)
    sx, sy, xm, ym = (d[k] for k in ("sx", "sy", "xmax", "ymax"))
    rise = p.storey_height/p.risers
    per_flight = p.risers//2
    landing_y = sy+(per_flight-1)*p.tread
    half_z = per_flight*rise
    lower, upper = [], []
    for i in range(per_flight-1):
        lower.append(cuboid((sx, sy+i*p.tread, (i+1)*rise-g.stair_tread_thickness,
                              sx+p.stair_width, sy+(i+1)*p.tread, (i+1)*rise),
                             f"stairs:lower_tread_{i+1:02d}", "stairs"))
        upper.append(cuboid((xm-p.stair_width, landing_y-(i+1)*p.tread, half_z+(i+1)*rise-g.stair_tread_thickness,
                              xm, landing_y-i*p.tread, half_z+(i+1)*rise),
                             f"stairs:upper_tread_{i+1:02d}", "stairs"))
    # The F2 slab's own south opening edge forms the eighth return-flight
    # riser. No extra panel consumes any of the final 260 mm tread.
    landing = cuboid((sx, landing_y, half_z-g.landing_thickness,
                       xm, ym, half_z), "stairs:mid_landing", "stairs")
    # Two side stringers per flight leave the middle open. Their illustrative
    # intersections express support continuity only, not verified connections.
    stringers=[]
    def rail(label,x,y0,y1,z0,z1):
        from shapely.geometry import Polygon
        profile=Polygon([(y0,z0),(y1,z1),(y1,z1-g.stair_stringer_depth),
                         (y0,z0-g.stair_stringer_depth)]).intersection(box(y0,0,y1,p.storey_height))
        wire=bd.Wire.make_polygon([(x,y,z) for y,z in profile.exterior.coords])
        stringers.append(named(bd.extrude(bd.Face(wire),amount=g.stair_stringer_width,dir=(1,0,0)),label,'stairs'))
    for side,x in enumerate((sx,sx+p.stair_width-g.stair_stringer_width),1):
        rail(f'stairs:lower_stringer_{side}',x,sy,landing_y+p.tread,
             -g.stair_tread_thickness+20,half_z-g.stair_tread_thickness+20)
    for side,x in enumerate((xm-p.stair_width,xm-g.stair_stringer_width),1):
        rail(f'stairs:upper_stringer_{side}',x,sy-p.tread,landing_y,
             p.storey_height-g.stair_tread_thickness+20,half_z-g.stair_tread_thickness+20)
    return bd.Compound(children=[
        bd.Compound(children=lower,label='stairs:lower_flight'),landing,
        bd.Compound(children=upper,label='stairs:upper_flight'),*stringers],label='stairs')



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
    from .attic_geometry import north_vent_tool
    north = section_extrusion(gable_section, p.depth-p.external_wall, p.external_wall-setback).cut(north_vent_tool(p,g))
    return bd.Compound(children=[named(west, "roof:west_plane", "roof"),
                                  named(east, "roof:east_plane", "roof"),
                                  named(south, "roof:south_gable_wall", "external"),
                                  named(north, "roof:north_gable_wall", "external"),
                                  *roof_detail_parts(p, g)],
                       label="roof")


def storage_group(floor, p=P, g=G):
    z = (floor.number-1)*p.storey_height
    storage = []
    for i, (name, bounds) in enumerate(floor.fixtures, 1):
        if name not in ("靴収納", "収納", "食品棚", "収納棚", "食品収納", "衣類棚", "CL", "リネン"):
            continue
        x1, y1, x2, y2 = bounds
        height = G.shoe_cabinet_height if name == "靴収納" else G.storage_cabinet_height
        storage.append(cuboid((x1, y1, z, x2, y2, z+height),
                                f"F{floor.number}:storage_{i:02d}", "storage"))
    if floor.number==1:
        d=dimensions(p);x1=d['xmax']-p.stair_width;x2=d['xmax'];sy=d['sy']
        landing_y=sy+(p.risers//2-1)*p.tread;rise=p.storey_height/p.risers
        def yz_panel(points,x,width,label):
            wire=bd.Wire.make_polygon([(x,y,z) for y,z in points])
            return named(bd.extrude(bd.Face(wire),amount=width,dir=(1,0,0)),label,'internal')
        for i in range(p.risers//2-1):
            ya=landing_y-(i+1)*p.tread;yb=landing_y-i*p.tread
            underside=p.storey_height/2+(i+1)*rise-g.stair_tread_thickness
            za=underside+20-g.stair_stringer_depth-10;zb=za-rise
            prefix=f'F1:under_stairs:section_{i+1}'
            storage.extend([yz_panel([(ya,0),(yb,0),(yb,zb-35),(ya,za-35)],x1,50,prefix+':side'),
                            yz_panel([(ya,za-35),(yb,zb-35),(yb,zb),(ya,za)],x1+50,p.stair_width-100,prefix+':ceiling')])
        rear_height=p.storey_height/2-g.stair_tread_thickness+20-g.stair_stringer_depth-10-35
        storage.append(yz_panel([(landing_y-60,0),(landing_y,0),(landing_y,rear_height),
                                 (landing_y-60,rear_height+60/p.tread*rise)],x1+50,p.stair_width-100,'F1:under_stairs:back'))
        for i,zs in enumerate((400,800),1):
            storage.append(cuboid((x1+65,landing_y-400,zs,x2-65,landing_y-70,zs+25),
                                  f'F1:under_stairs:shelf_{i}','storage'))
    return bd.Compound(children=storage, label=f"F{floor.number}:storage_fixtures")


@orient_shape
def house_assembly(p=P, g=G, include_roof=True):
    from .furniture_geometry import furniture_group
    from .indoor_lighting import indoor_lighting_group
    from .fixture_geometry import fixture_group
    from .attic_geometry import attic_access_group, attic_group
    from .site_geometry import foundation_group, yard_group, fence_group
    from .structure_geometry import structure_group
    from .outdoor_lighting import outdoor_lighting_group
    from .balcony_geometry import balcony_group
    floors = []
    for number in (1, 2):
        plan = floor_plan(number, p)
        external, internal = wall_groups(plan, p, g)
        floors.append(bd.Compound(children=[slab_for_floor(number, p, g), external, internal,
                                            door_group(plan, p, g), window_group(plan, p, g),
                                            storage_group(plan, p, g), fixture_group(plan, p, "house"),
                                            furniture_group(plan, "house", p),indoor_lighting_group(number,p,g)], label=f"F{number}"))
    children = floors+[stair_group(p, g),balcony_group(p,g)]
    if include_roof:
        children.append(roof_group(p, g))
    attic=attic_group(p,g)
    from .indoor_lighting import indoor_lighting_group
    lamp=indoor_lighting_group(3,p,g)
    # Keep the attic light under its equipment category and floor visibility.
    attic.children=tuple(attic.children)+(lamp,)
    children += [attic, attic_access_group(p, g)]
    children += [foundation_group(p, g), yard_group(p, g), fence_group(p=p)]
    children.append(structure_group(p, g))
    children.append(outdoor_lighting_group(p, g))
    return bd.Compound(children=children, label="house_3d")


def geometry_manifest(p=P, g=G):
    from .furniture_geometry import furniture_manifest
    from .exterior_geometry import exterior_manifest
    from .attic_geometry import attic_manifest
    from .site_geometry import site_manifest
    from .structure_geometry import structure_manifest
    from .outdoor_lighting import outdoor_lighting_manifest
    exterior = exterior_manifest(p=p)
    attic = attic_manifest(p, g)
    site = site_manifest(p, g)
    structure = structure_manifest(p, g)
    lighting = outdoor_lighting_manifest(p, g)
    from .indoor_lighting import indoor_lighting_manifest
    indoor=indoor_lighting_manifest(p,g)
    return {
        "revision": "R19-3D", "stage": "demonstration_structural_layout_pending_engineering",
        "source_plan": "src/lib/house_plan.py", "units": "mm",
        "plan_parameters": asdict(p), "geometry_parameters": asdict(g),
        "floor_datums_mm": [0, p.storey_height], "roof_base_mm": 2*p.storey_height,
        "axis_convention": "X east, Y north, Z up; GLB is metre-scaled Y-up",
        "exterior": exterior,
        "attic": attic,
        "site": site,
        "structure": structure,
        "outdoor_lighting": lighting,
        "indoor_lighting": indoor,
        "engineering_status": {
            "site": "demonstration; municipality and actual parcel unspecified",
            "structural_calculation": "not performed",
            "statutory_classification": "pending local authority review",
            "construction_use": "not approved for construction",
            "input_sheet": "output/review/engineering_inputs_R06.json",
        },
        "assumptions": [
            "R19玄关把手移到室外正视左侧；一层取消独立厕所前厅并入LDK，增加800×1760 mm斜顶楼梯下储物间、700 mm门和搁板；净高随上跑踏步变化，结构与防火尚未计算。",
            "R19四人转角沙发2600×1550 mm与南墙电视相对，茶几950×550 mm，餐桌1600×850 mm配四椅；双开门冰箱900×750 mm。家具尺寸与动线均为演示方案。",
            "R19按用户要求镜像一二层：西南玄关、西北楼梯，东侧客厅及两个临东卧室设窗，西侧仅楼梯窗。",
            "対面式厨房2550×650 mm，主要后方通道900 mm，新增冰箱、微波炉、电器柜和吸油烟机；阁楼北侧换气窗600×300 mm、窗台FL+850 mm，均为演示假设，排烟、通风和承载未设计。",
            "8190 × 7280 mm 外轮廓、2800 mm 层高及北向/南入口是演示假设。",
            "R19左右镜像原房间净边界并调整厨房和侧窗；入口及楼梯转到西侧，南侧全宽阳台和取消独立玄关雨棚的设置保留。",
            "R13南侧阳台外形8190 × 1000 mm，净空间7990 × 900 mm、净几何面积7.191㎡；由两间南侧卧室进入，两端与东西外墙齐平；南侧客厅落地窗高2200，卧室阳台推拉门高2100（宽2100/1600/1800），三根支柱及独立基础已移除；1300 mm玄关平台外沿300 mm露出，独立雨棚保持取消；悬挑承载、连接、栏杆、防水和排水未计算。",
            "楼层完成面基准 Z=0、2800 mm；楼板暂定厚200 mm并位于完成面以下，墙净高2600 mm。",
            "二层楼板保留整个1900 × 2720 mm梯间净边界开洞；阁楼改为24 mm示意底板、18 mm饰面及独立梁/搁栅结构草案。",
            "门洞高2100 mm；门扇厚36 mm，以关闭位置表达，侧边及上下留10 mm示意间隙。",
            "南侧客厅落地窗窗台0/高2200 mm，二层两扇阳台双扇推拉门高2100 mm、宽1600/1800 mm；其他大窗窗台900/高1300 mm，小窗窗台1500/高600 mm。",
            "窗框面宽45 mm、进深70 mm，玻璃厚10 mm；窗框位于外侧墙带；门窗尚未选型，洞口为毛洞尺寸。",
            "切妻屋根屋脊沿南北方向，坡度30度、四周屋檐450 mm、竖向厚度150 mm均可改参数。",
            "U型楼梯16踢面×175 mm，踏面260 mm，梯宽900 mm，中间平台900 mm深；各半梯7踏步加平台/二层地坪为第8级。开放踢面栏护及防跌落构造尚未深化。",
            "两跑踏步采用60 mm概念厚度、115 mm开口及40×200 mm侧梁，储物间斜顶低于侧梁；侧梁与踏步、平台及楼板接触，二层楼板洞口南缘为末级踢面。连接和承载未计算。",
            "鞋柜高1800 mm、其余收纳柜2000 mm，位置沿用确认平面；家具与卫浴根据公开尺寸参考进行原创参数化建模，未选实际产品。",
            "移门门袋、楼梯扶手、结构连接、实际屋面/墙体层次及设备系统留待深化。",
            "未验证结构、消防、建筑法规、实际楼梯头部净空或建筑确认申报要求。",
        ] + exterior["assumptions"] + attic["assumptions"] + site["assumptions"] + structure["assumptions"] + lighting["assumptions"] + indoor["assumptions"],
        "interior_reference": "references/interior-furnishings.md",
        "interior_model": "Original parametric furniture and fixtures; visual dimensions are assumptions, not manufacturer CAD.",
        "furnishings": [furniture_manifest(floor_plan(n, p), "house", p) for n in (1, 2)],
        "outputs": ["STEP/house_3d.step", "GLB/house_3d.glb"],
    }
