"""Original demonstration foundation, compact parking yard and open fencing.

Dimensions are millimetres. These editable solid bodies are a spatial proposal,
not a ground investigation, a concrete reinforcement design or a surveyed lot.
The approved building, porch and upper entrance step remain unchanged.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import ceil

from cadgen import build123d as bd
from shapely.geometry import box
from shapely.ops import unary_union

from .exterior_geometry import E


@dataclass(frozen=True)
class SiteParameters:
    lot_west: float = -1000
    lot_east: float = 9190
    lot_south: float = -5500
    lot_north: float = 8280
    ground_z: float = -500
    soil_thickness: float = 100
    finish_thickness: float = 50
    raft_bottom_z: float = -800
    raft_thickness: float = 150
    entrance_lower_step_depth: float = 300
    entrance_lower_step_top_z: float = -330
    parking_west: float = -750
    parking_east: float = 4850
    parking_south: float = -5500
    parking_north: float = -200
    parking_mark_south: float = -5200
    parking_line_width: float = 50
    parking_line_thickness: float = 2
    wheel_stop_width: float = 500
    wheel_stop_depth: float = 100
    wheel_stop_height: float = 100
    fence_west: float = -800
    fence_east: float = 8990
    fence_south: float = -5300
    fence_north: float = 8080
    fence_height: float = 1200
    fence_post_width: float = 50
    fence_post_embedment: float = 250
    fence_max_span: float = 1800
    fence_panel_thickness: float = 20
    fence_panel_frame_width: float = 20
    fence_panel_bottom_above_grade: float = 80
    fence_slats: int = 9
    fence_slat_height: float = 80
    fence_slat_gap: float = 40
    fence_footing_width: float = 300
    fence_footing_bottom_z: float = -950
    fence_footing_top_z: float = -550
    car_opening_west: float = -775
    car_opening_east: float = 4900
    pedestrian_opening_west: float = 5860
    pedestrian_opening_east: float = 7660
    parking_count: int = 2
    shrubs_enabled: bool = False
    shrub_center_z: float = -100


S = SiteParameters()


def _helpers():
    from .house_geometry import cuboid, extruded_polygon, named, polygons
    return cuboid, extruded_polygon, named, polygons


def site_dimensions(p, g, s=S):
    """Coordinates shared by the editable model, proposal drawing and manifest."""
    from .house_plan import floor_plan
    door = next(d for d in floor_plan(1, p).doors if d.a == "outside")
    margin = E.entrance_canopy_margin
    entrance_x1, entrance_x2 = door.start - margin, door.start + door.width + margin
    upper_step_south = -E.porch_depth - E.porch_step_depth
    lower_step_south = upper_step_south - s.entrance_lower_step_depth
    raft_top = s.raft_bottom_z + s.raft_thickness
    finish_bottom = s.ground_z - s.finish_thickness
    return {
        "lot": (s.lot_west, s.lot_south, s.lot_east, s.lot_north),
        "building": (0, 0, p.width, p.depth),
        "entrance": (entrance_x1, lower_step_south, entrance_x2, 0),
        "porch": (entrance_x1, -E.porch_depth, entrance_x2, 0),
        "upper_step": (entrance_x1, upper_step_south, entrance_x2, -E.porch_depth),
        "lower_step": (entrance_x1, lower_step_south, entrance_x2, upper_step_south),
        "path": (entrance_x1, s.lot_south, entrance_x2, lower_step_south),
        "parking": (s.parking_west, s.parking_south, s.parking_east, s.parking_north),
        "parking_bay": (s.parking_west, s.parking_mark_south, s.parking_east, s.parking_north),
        "parking_bays": [(s.parking_west+i*(s.parking_east-s.parking_west)/s.parking_count,
                          s.parking_mark_south,
                          s.parking_west+(i+1)*(s.parking_east-s.parking_west)/s.parking_count,
                          s.parking_north) for i in range(s.parking_count)],
        "raft_top_z": raft_top,
        "finish_bottom_z": finish_bottom,
        "soil_bottom_z": finish_bottom - s.soil_thickness,
        "old_plinth_bottom_z": -g.slab_thickness - E.foundation_depth,
        "lawns": {
            "north": (400, p.depth+250, p.width-400, s.lot_north-350),
            "east": (p.width+250, 500, s.lot_east-350, p.depth-500),
            "west": (s.lot_west+350, 700, -250, p.depth-700),
        },
        "shrubs": [(2850, -3800, 400), (3950, -3650, 450), (3450, -2250, 500)] if s.shrubs_enabled else [],
    }


def fence_layout(s=S):
    """Deduplicated corner posts and spans retaining the exact clear openings."""
    half = s.fence_post_width / 2
    segments = [
        ("north", "h", s.fence_north, s.fence_west, s.fence_east),
        ("west", "v", s.fence_west, s.fence_south, s.fence_north),
        ("east", "v", s.fence_east, s.fence_south, s.fence_north),
        ("south_west", "h", s.fence_south, s.fence_west, s.car_opening_west - half),
        ("south_middle", "h", s.fence_south, s.car_opening_east + half,
         s.pedestrian_opening_west - half),
        ("south_east", "h", s.fence_south, s.pedestrian_opening_east + half, s.fence_east),
    ]
    posts, panels, seen = [], [], {}
    for side, axis, at, start, end in segments:
        if end <= start:
            continue
        count = ceil((end - start) / s.fence_max_span)
        coordinates = [start + (end - start) * i / count for i in range(count + 1)]
        for i, coordinate in enumerate(coordinates, 1):
            x, y = (coordinate, at) if axis == "h" else (at, coordinate)
            key = (round(x, 8), round(y, 8))
            if key not in seen:
                identifier = f"{side}_{i:02d}"
                seen[key] = identifier
                posts.append({"id": identifier, "x": x, "y": y})
        for i, (a, b) in enumerate(zip(coordinates, coordinates[1:]), 1):
            panels.append({"id": f"{side}_{i:02d}", "axis": axis, "at": at,
                           "start": a + half, "end": b - half,
                           "post_center_span": b - a})
    return {"posts": posts, "panels": panels}


def _box_profile(bounds):
    return box(*bounds)


def _extrude_profile(profile, bottom, top, label, color):
    _, extruded_polygon, named, polygons = _helpers()
    shapes = [extruded_polygon(polygon, bottom, top - bottom) for polygon in polygons(profile)]
    shape = shapes[0] if len(shapes) == 1 else bd.Compound(shapes)
    return named(shape, label, color)


def foundation_group(p, g, s=S):
    from .exterior_geometry import plinth_parts
    cuboid, _, _, _ = _helpers()
    d = site_dimensions(p, g, s)
    x1, y1, x2, y2 = d["entrance"]
    raft = bd.Compound(children=[
        cuboid((0, 0, s.raft_bottom_z, p.width, p.depth, d["raft_top_z"]),
               "foundation:raft:slab", "site_concrete"),
        cuboid((x1, y1, s.raft_bottom_z, x2, y2, d["raft_top_z"]),
               "foundation:raft:entrance_footing", "site_concrete"),
    ], label="foundation:raft")
    t, bottom, top = E.foundation_wall_thickness, d["raft_top_z"], d["old_plinth_bottom_z"]
    wall_bounds = {
        "south": (0, 0, bottom, p.width, t, top),
        "north": (0, p.depth - t, bottom, p.width, p.depth, top),
        "west": (0, t, bottom, t, p.depth - t, top),
        "east": (p.width - t, t, bottom, p.width, p.depth - t, top),
    }
    stems = bd.Compound(children=[cuboid(bounds, f"foundation:stem_walls:{side}", "site_concrete")
                                  for side, bounds in wall_bounds.items()], label="foundation:stem_walls")
    supports = []
    for name, footprint, top in [
        ("porch", d["porch"], -g.slab_thickness),
        ("upper_step", d["upper_step"], -g.slab_thickness - 100),
    ]:
        x1, y1, x2, y2 = footprint
        supports.append(cuboid((x1, y1, bottom, x2, y2, top),
                               f"foundation:entrance_supports:{name}", "site_concrete"))
    plinth = bd.Compound(children=plinth_parts(p, g), label="foundation:existing_plinth")
    return bd.Compound(children=[raft, stems, plinth, internal_support_group(p, g, s),
                                 bd.Compound(children=supports, label="foundation:entrance_supports")],
                       label="foundation")


def internal_support_profiles(p):
    """Non-overlapping proposal ribs following candidate structural support lines.

    Concrete section dimensions remain unverified demonstration parameters.
    Existing perimeter stems/plinths occupy the perimeter; ribs meet that band
    without duplicating it or duplicating one another at crossings.
    """
    from .structure_geometry import foundation_support_segments
    t = E.foundation_wall_thickness
    outer = box(0, 0, p.width, p.depth)
    perimeter = outer.difference(box(t, t, p.width-t, p.depth-t))
    occupied, profiles = perimeter, []
    for index, segment in enumerate(foundation_support_segments(p), 1):
        axis, at, start, end = (segment[k] for k in ("axis", "at", "start", "end"))
        footprint = box(start, at-t/2, end, at+t/2) if axis == "h" else box(at-t/2, start, at+t/2, end)
        clipped = footprint.intersection(outer).difference(occupied)
        occupied = occupied.union(footprint)
        if not clipped.is_empty and clipped.area > .01:
            profiles.append((segment.get("id", f"rib_{index:02d}"), clipped))
    return profiles


def internal_support_group(p, g, s=S):
    d = site_dimensions(p, g, s)
    top = -g.slab_thickness
    children = [_extrude_profile(profile, d["raft_top_z"], top,
                 f"foundation:internal_supports:{name}", "site_concrete")
                for name, profile in internal_support_profiles(p)]
    return bd.Compound(children=children, label="foundation:internal_supports")


def _terrain_profiles(p, g, s=S):
    d, fence = site_dimensions(p, g, s), fence_layout(s)
    occupied = unary_union([_box_profile(d["building"]), _box_profile(d["entrance"])])
    half_foot, half_post = s.fence_footing_width / 2, s.fence_post_width / 2
    footing_profiles = [box(post["x"] - half_foot, post["y"] - half_foot,
                            post["x"] + half_foot, post["y"] + half_foot) for post in fence["posts"]]
    post_profiles = [box(post["x"] - half_post, post["y"] - half_post,
                         post["x"] + half_post, post["y"] + half_post) for post in fence["posts"]]
    # The separate balcony support foundations displace terrain as real solids.
    from .balcony_geometry import B, support_positions
    from .house_plan import dimensions
    bx=dimensions(p)['bx']; h=B.footing_width/2
    balcony_feet=[box(x-h,-p.balcony_depth+p.balcony_rail_thickness/2-h,x+h,
                      -p.balcony_depth+p.balcony_rail_thickness/2+h)
                  for x in support_positions(p)]
    occupied=unary_union([occupied,*balcony_feet])
    soil = _box_profile(d["lot"]).difference(unary_union([occupied, *footing_profiles]))
    finish = _box_profile(d["lot"]).difference(unary_union([occupied, *post_profiles]))
    parking = _box_profile(d["parking"]).intersection(finish)
    path = _box_profile(d["path"]).intersection(finish)
    lawns = {name: _box_profile(bounds).intersection(finish).difference(unary_union([parking, path]))
             for name, bounds in d["lawns"].items()}
    gravel = finish.difference(unary_union([parking, path, *lawns.values()]))
    return {"soil": soil, "finish": finish, "parking": parking, "path": path,
            "lawns": lawns, "gravel": gravel}


def yard_group(p, g, s=S):
    cuboid, _, named, _ = _helpers()
    d, profiles = site_dimensions(p, g, s), _terrain_profiles(p, g, s)
    soil = _extrude_profile(profiles["soil"], d["soil_bottom_z"], d["finish_bottom_z"],
                            "yard:soil:base", "site_soil")
    gravel = _extrude_profile(profiles["gravel"], d["finish_bottom_z"], s.ground_z,
                              "yard:ground_surfaces:gravel", "site_gravel")
    path = _extrude_profile(profiles["path"], d["finish_bottom_z"], s.ground_z,
                            "yard:entrance_path:paving", "site_paving")
    x1, y1, x2, y2 = d["lower_step"]
    lower_step = cuboid((x1, y1, d["raft_top_z"], x2, y2, s.entrance_lower_step_top_z),
                         "yard:entrance_path:lower_step", "site_concrete")
    parking = [_extrude_profile(profiles["parking"], d["finish_bottom_z"], s.ground_z,
                                "yard:parking:paving", "site_paving")]
    x1, y1, x2, y2 = d["parking_bay"]
    w = s.parking_line_width
    lines = [
        ("line_left", (x1,y1,x1+w,y2)),
        ("line_right", (x2-w,y1,x2,y2)),
        ("line_back", (x1+w,y2-w,x2-w,y2)),
    ]
    for i in range(1,s.parking_count):
        divider=x1+(x2-x1)*i/s.parking_count
        lines.append((f"line_divider_{i}",(divider-w/2,y1,divider+w/2,y2-w)))
    for name,bounds in lines:
        # The existing balcony footing straddles the shared boundary. Keep the
        # marking open over its real 450 mm exclusion, rather than drawing into it.
        profile=box(*bounds).intersection(profiles["parking"])
        if not profile.is_empty:
            parking.append(_extrude_profile(profile,s.ground_z,s.ground_z+s.parking_line_thickness,
                                            f"yard:parking:{name}","site_paint"))
    for i,(left,bottom,right,top) in enumerate(d["parking_bays"],1):
        for side,x in [("left",left+300),("right",right-300-s.wheel_stop_width)]:
            y=top-350
            parking.append(cuboid((x,y,s.ground_z,x+s.wheel_stop_width,y+s.wheel_stop_depth,
                                   s.ground_z+s.wheel_stop_height),
                                   f"yard:parking:bay_{i}_wheel_stop_{side}","site_concrete"))
    planting = [_extrude_profile(profile, d["finish_bottom_z"], s.ground_z,
                                 f"yard:planting:lawn_{name}", "site_lawn")
                for name, profile in profiles["lawns"].items()]
    for i, (x, y, radius) in enumerate(d["shrubs"], 1):
        shrub = bd.Sphere(radius).moved(bd.Location((x, y, s.shrub_center_z)))
        # Crop below grade; each compact crown touches the lawn without entering it.
        below = cuboid((x - radius - 1, y - radius - 1, s.shrub_center_z - radius - 1,
                         x + radius + 1, y + radius + 1, s.ground_z))
        shrub = shrub.cut(below)
        planting.append(named(shrub, f"yard:planting:shrub_{i:02d}", "site_shrub"))
    return bd.Compound(children=[
        bd.Compound(children=[soil], label="yard:soil"),
        bd.Compound(children=[gravel], label="yard:ground_surfaces"),
        bd.Compound(children=[path, lower_step], label="yard:entrance_path"),
        bd.Compound(children=parking, label="yard:parking"),
        bd.Compound(children=planting, label="yard:planting"),
    ], label="yard")


def _fence_panel(panel, s=S):
    cuboid, _, named, _ = _helpers()
    axis, start, end, at = (panel[key] for key in ("axis", "start", "end", "at"))
    frame, half = s.fence_panel_frame_width, s.fence_panel_thickness / 2
    bottom = s.ground_z + s.fence_panel_bottom_above_grade
    top = bottom + s.fence_slats * s.fence_slat_height + (s.fence_slats - 1) * s.fence_slat_gap

    def body(a, b, z1, z2):
        bounds = ((a, at - half, z1, b, at + half, z2) if axis == "h" else
                  (at - half, a, z1, at + half, b, z2))
        return cuboid(bounds)

    parts = [body(start, start + frame, bottom, top), body(end - frame, end, bottom, top)]
    for i in range(s.fence_slats):
        z1 = bottom + i * (s.fence_slat_height + s.fence_slat_gap)
        parts.append(body(start + frame, end - frame, z1, z1 + s.fence_slat_height))
    # Face joints make one valid connected solid, retaining all eight open gaps.
    fused = parts[0].fuse(*parts[1:])
    return named(fused, f"fence:panels:{panel['id']}", "site_metal")


def fence_group(s=S):
    cuboid, _, named, _ = _helpers()
    layout = fence_layout(s)
    half_post, half_foot = s.fence_post_width / 2, s.fence_footing_width / 2
    bottom, top = s.ground_z - s.fence_post_embedment, s.ground_z + s.fence_height
    posts, footings = [], []
    for post in layout["posts"]:
        x, y, identifier = (post[key] for key in ("x", "y", "id"))
        post_bounds = (x - half_post, y - half_post, bottom, x + half_post, y + half_post, top)
        posts.append(cuboid(post_bounds, f"fence:posts:{identifier}", "site_metal"))
        footing = cuboid((x - half_foot, y - half_foot, s.fence_footing_bottom_z,
                           x + half_foot, y + half_foot, s.fence_footing_top_z))
        # The embedded post occupies this pocket; no doubled concrete/steel volume.
        pocket = cuboid((x - half_post, y - half_post, bottom,
                         x + half_post, y + half_post, s.fence_footing_top_z + 1))
        footings.append(named(footing.cut(pocket), f"fence:footings:{identifier}", "site_concrete"))
    panels = [_fence_panel(panel, s) for panel in layout["panels"]]
    return bd.Compound(children=[bd.Compound(children=posts, label="fence:posts"),
                                 bd.Compound(children=panels, label="fence:panels"),
                                 bd.Compound(children=footings, label="fence:footings")], label="fence")


def site_manifest(p, g, s=S):
    d, layout, profiles = site_dimensions(p, g, s), fence_layout(s), _terrain_profiles(p, g, s)
    return {
        "revision": "R12-SITE",
        "parameters": asdict(s),
        "lot_bounds_mm": list(d["lot"]),
        "lot_dimensions_mm": [s.lot_east - s.lot_west, s.lot_north - s.lot_south],
        "lot_area_mm2": _box_profile(d["lot"]).area,
        "grade_z_mm": s.ground_z,
        "foundation": {
            "type": "demonstration raft, perimeter stems and candidate internal support ribs; no reinforcement design",
            "raft_bounds_mm": [0, 0, s.raft_bottom_z, p.width, p.depth, d["raft_top_z"]],
            "raft_thickness_mm": s.raft_thickness,
            "stem_width_mm": E.foundation_wall_thickness,
            "stem_bottom_top_mm": [d["raft_top_z"], d["old_plinth_bottom_z"]],
            "existing_plinth_preserved": True,
            "existing_plinth_group": "foundation:existing_plinth",
            "internal_support_width_mm": E.foundation_wall_thickness,
            "internal_support_bottom_top_mm": [d["raft_top_z"], -g.slab_thickness],
            "internal_supports": [{"id": name, "plan_bounds_mm": list(profile.bounds),
                                   "plan_area_mm2": profile.area}
                                  for name, profile in internal_support_profiles(p)],
            "design_status": "sizes are assumptions; reactions, ground bearing and reinforcement pending",
        },
        "entrance": {
            "footprint_mm": list(d["entrance"]),
            "path_bounds_mm": list(d["path"]),
            "path_width_mm": d["path"][2] - d["path"][0],
            "levels_mm": [s.ground_z, s.entrance_lower_step_top_z, E.porch_step_top, E.porch_top, 0],
            "rises_mm": [s.entrance_lower_step_top_z - s.ground_z,
                         E.porch_step_top - s.entrance_lower_step_top_z,
                         E.porch_top - E.porch_step_top, -E.porch_top],
            "old_porch_and_step_preserved": True,
        },
        "parking": {"surface_bounds_mm": list(d["parking"]), "bay_bounds_mm": list(d["parking_bay"]),
                    "count": s.parking_count,
                    "bay_dimensions_mm": [(s.parking_east-s.parking_west)/s.parking_count,
                                          s.parking_north-s.parking_mark_south],
                    "bays_bounds_mm": [list(b) for b in d["parking_bays"]],
                    "vehicle_envelopes_mm": [[(b[0]+b[2])/2-900,b[1]+100,
                                               (b[0]+b[2])/2+900,b[1]+4600] for b in d["parking_bays"]],
                    "vehicle_dimensions_mm": [1800,4500],
                    "maneuvering_verified": False},
        "fence": {
            "post_count": len(layout["posts"]), "panel_count": len(layout["panels"]),
            "height_above_grade_mm": s.fence_height,
            "panel_bottom_top_mm": [s.ground_z + s.fence_panel_bottom_above_grade,
                                    s.ground_z + s.fence_panel_bottom_above_grade +
                                    s.fence_slats * s.fence_slat_height + (s.fence_slats - 1) * s.fence_slat_gap],
            "slat_gap_mm": s.fence_slat_gap,
            "car_clear_opening_mm": [s.car_opening_west, s.car_opening_east],
            "pedestrian_clear_opening_mm": [s.pedestrian_opening_west, s.pedestrian_opening_east],
            "posts": layout["posts"], "panels": layout["panels"],
        },
        "surfaces": {
            "soil_area_mm2": profiles["soil"].area,
            "finish_total_area_mm2": profiles["finish"].area,
            "gravel_area_mm2": profiles["gravel"].area,
            "entrance_paving_area_mm2": profiles["path"].area,
            "parking_paving_area_mm2": profiles["parking"].area,
            "lawns_area_mm2": {name: profile.area for name, profile in profiles["lawns"].items()},
            "lawn_bounds_mm": {name: list(bounds) for name, bounds in d["lawns"].items()},
            "shrubs": [{"center_mm": [x, y, s.shrub_center_z], "radius_mm": radius}
                       for x, y, radius in d["shrubs"]],
        },
        "assumptions": [
            "R12用地沿用R11，暂定10190 × 13780 mm（约140.42㎡），东、西、北侧余量各1000 mm、南侧5500 mm，房屋在用地内的位置和南侧出入口均为演示假设，未依据实际测量或道路资料。",
            "院子完成面暂定Z=-500 mm；下设50 mm展示面层及100 mm概念土层，砂石、铺装和草坪的材质与厚度均可调整。",
            "新增贝塔基础仍以150 mm底板和140 mm周圈立上り表达；R10重排与结构草案柱线对应的内部支承肋，全部截面仍为演示假设，配筋、地盘、承载、抗震及排水待设计。",
            "保留原门廊与上阶并增设支承和下阶；入口标高依次为-500、-330、-160、-25、0 mm，高差170、170、135、25 mm为演示值，未验证无障碍或通行法规。",
            "南侧并列2个停车位，每位暂定2800 × 5000 mm，车辆开口5675 mm、行人开口1800 mm；1800 × 4500 mm车辆包络仅作静态空间检查；未验证具体车辆转弯、道路接入或停车许可。",
            "金属围栏暂定地上高1200 mm、柱宽50 mm；24片面板各含9道80 mm横栅和40 mm空隙，26个柱脚为概念展示，未完成连接或结构设计。",
            "围栏柱脚暂定300 × 300 mm、Z=-950至-550 mm，并为柱嵌入留孔；土层和面层对应挖孔，各实体仅在边界接触，未配置实际施工构造。",
            "三侧窄草坪保留，前院草坪改为第二车位，所有灌木移除；基础、院子、入口与围栏分组可独立查看，已确认两层平面保持不变。",
        ],
    }
