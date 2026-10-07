"""Original, low-complexity concept details for a contemporary Japanese house.

All dimensions below are millimetre-based demonstration assumptions, not a
selected manufacturer's CAD or a construction specification. The 20 mm siding
replaces the outer portion of the original wall rather than enlarging its
7280 x 7280 mm finished footprint. Protruding trims, rainwater goods and entrance
attachments are separately named and remain editable.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import radians, sqrt, tan

from cadgen import build123d as bd


@dataclass(frozen=True)
class ExteriorParameters:
    cladding_thickness: float = 20
    backing_gap: float = 2
    foundation_depth: float = 300
    foundation_wall_thickness: float = 140
    window_trim_width: float = 32
    window_trim_projection: float = 12
    window_sill_drop: float = 48
    window_sill_projection: float = 35
    door_frame_width: float = 45
    door_frame_projection: float = 18
    entrance_canopy_margin: float = 300
    entrance_canopy_depth: float = 900
    entrance_canopy_height: float = 2250
    entrance_canopy_thickness: float = 65
    porch_depth: float = 1300
    porch_top: float = -25
    porch_step_depth: float = 300
    porch_step_top: float = -160
    standing_seam_spacing: float = 455  # Nominal; evenly distributed between roof edges.
    standing_seam_width: float = 12
    standing_seam_height: float = 12
    ridge_cap_half_width: float = 80
    ridge_cap_lift: float = 20
    ridge_cap_thickness: float = 12
    fascia_projection: float = 25
    soffit_thickness: float = 16
    gutter_width: float = 90
    gutter_depth: float = 85
    gutter_wall_thickness: float = 9
    gutter_top_below_eave: float = 15
    downpipe_radius: float = 32
    downpipe_wall_thickness: float = 3
    downpipe_wall_offset: float = 55
    downpipe_north_inset: float = 260
    downpipe_elbow_drop: float = 320
    downpipe_ground_clearance: float = 50


E = ExteriorParameters()


def wall_setback(e=E):
    return e.cladding_thickness + e.backing_gap


def exterior_window_center(axis, at, p, g):
    """Recess a 70 mm frame inside the outer face while retaining its opening."""
    size = p.depth if axis == "h" else p.width
    return g.window_frame_depth / 2 if at < size / 2 else size - g.window_frame_depth / 2


def _helpers():
    # Lazy imports allow the house assembly to reuse these detail builders.
    from .house_geometry import cuboid, named, opening_box, section_extrusion, window_vertical_range
    return cuboid, named, opening_box, section_extrusion, window_vertical_range


def plinth_parts(p, g, e=E):
    """Original plinth solids, retained by name under the foundation hierarchy."""
    cuboid, _, _, _, _ = _helpers()
    z0 = -g.slab_thickness - e.foundation_depth
    t = e.foundation_wall_thickness
    foundation = {
        "south": (0, 0, z0, p.width, t, -g.slab_thickness),
        "north": (0, p.depth-t, z0, p.width, p.depth, -g.slab_thickness),
        "west": (0, t, z0, t, p.depth-t, -g.slab_thickness),
        "east": (p.width-t, t, z0, p.width, p.depth-t, -g.slab_thickness),
    }
    return [cuboid(b, f"F1:exterior:foundation:{side}", "concrete") for side, b in foundation.items()]


def facade_parts(floor, p, g, e=E, include_plinth=True):
    cuboid, named, opening_box, _, window_vertical_range = _helpers()
    c = e.cladding_thickness
    z = (floor.number - 1) * p.storey_height
    bottom = z - g.slab_thickness
    top = z + p.storey_height - (g.slab_thickness if floor.number == 1 else 0)
    cuts = [opening_box(d.axis, d.at, d.start, d.width, p.external_wall, z, z + g.door_height)
            for d in floor.doors if {'outside','balcony'} & {d.a,d.b}]
    for window in floor.windows:
        sill, height = window_vertical_range(window, g, p)
        cuts.append(opening_box(*window, p.external_wall, z + sill, z + sill + height))
    bounds = {
        "south": (0, 0, bottom, p.width, c, top),
        "north": (0, p.depth - c, bottom, p.width, p.depth, top),
        "west": (0, c, bottom, c, p.depth - c, top),
        "east": (p.width - c, c, bottom, p.width, p.depth - c, top),
    }
    leaves = [named(cuboid(b).cut(*cuts), f"F{floor.number}:exterior:cladding:{side}", "exterior")
              for side, b in bounds.items()]
    if floor.number == 1:
        if include_plinth:
            leaves += plinth_parts(p, g, e)
    leaves += downpipe_parts(floor.number, p, g, e)
    return leaves


def entrance_parts(floor, p, g, e=E):
    cuboid, named, _, _, _ = _helpers()
    if floor.number != 1:
        return []
    door = next(d for d in floor.doors if d.a == "outside")
    x, w, f = door.start, door.width, e.door_frame_width
    label = f"F1:{door.id}"
    frame = cuboid((x-f, -e.door_frame_projection, -20,
                     x+w+f, 0, g.door_height+f))
    frame = frame.cut(cuboid((x, -e.door_frame_projection-1, 0,
                              x+w, 1, g.door_height)))
    handle_x = x + 90
    handle = cuboid((handle_x, -50, 860, handle_x+20, -30, 1400))
    handle = handle.fuse(cuboid((handle_x, -30, 900, handle_x+20, 0, 920)),
                         cuboid((handle_x, -30, 1340, handle_x+20, 0, 1360)))
    margin = e.entrance_canopy_margin
    canopy = [cuboid((x-margin, -e.entrance_canopy_depth, e.entrance_canopy_height,
                      x+w+margin, 0, e.entrance_canopy_height+e.entrance_canopy_thickness),
                     f"{label}:canopy", "charcoal")] if getattr(p,"entrance_canopy",True) else []
    return [
        named(frame, f"{label}:frame", "charcoal"),
        named(handle, f"{label}:handle", "charcoal"),
        cuboid((x, -70, -18, x+w, 0, 0), f"{label}:threshold", "charcoal"),
        *canopy,
        cuboid((x-margin, -e.porch_depth, -g.slab_thickness,
                 x+w+margin, 0, e.porch_top), f"{label}:porch", "concrete"),
        cuboid((x-margin, -e.porch_depth-e.porch_step_depth, -g.slab_thickness-100,
                 x+w+margin, -e.porch_depth, e.porch_step_top),
                f"{label}:porch_step", "concrete"),
    ]


def exterior_window_parts(window, number, index, p, g, e=E):
    cuboid, named, _, _, window_vertical_range = _helpers()
    axis, at, start, width = window
    sill, height = window_vertical_range(window, g, p)
    z = (number-1) * p.storey_height + sill
    t, projection = e.window_trim_width, e.window_trim_projection
    lower=z if sill==0 else z-t
    label = f"F{number}:W{index:02d}"
    size = p.depth if axis == "h" else p.width
    positive = at > size / 2
    outer = size if positive else 0
    a, b = (outer, outer+projection) if positive else (-projection, 0)
    sill_a, sill_b = ((outer, outer+e.window_sill_projection) if positive
                       else (-e.window_sill_projection, 0))
    if axis == "h":
        trim = cuboid((start-t, a, lower, start+width+t, b, z+height+t))
        trim = trim.cut(cuboid((start, a-1, z, start+width, b+1, z+height)))
        sill_bounds = (start-t, sill_a, z-e.window_sill_drop,
                       start+width+t, sill_b, z-t)
    else:
        trim = cuboid((a, start-t, lower, b, start+width+t, z+height+t))
        trim = trim.cut(cuboid((a-1, start, z, b+1, start+width, z+height)))
        sill_bounds = (sill_a, start-t, z-e.window_sill_drop,
                       sill_b, start+width+t, z-t)
    # The sill meets the bottom surround at an edge without overlapping its volume.
    parts=[named(trim,f"{label}:exterior_trim","frame")]
    if sill>0:
        parts.append(cuboid(sill_bounds,f"{label}:sill","charcoal"))
    return parts


def _rainpipe(points, e):
    """A fused, hollow rainwater pipe with a rounded offset bend."""
    outside, inside = [], []
    for a, b in zip(points, points[1:]):
        delta = tuple(b[i]-a[i] for i in range(3))
        length = sqrt(sum(v*v for v in delta))
        plane = bd.Plane(origin=a, z_dir=delta)
        outside.append(bd.Solid.make_cylinder(e.downpipe_radius, length, plane))
        inside.append(bd.Solid.make_cylinder(e.downpipe_radius-e.downpipe_wall_thickness,
                                             length, plane))
    for point in points[1:-1]:
        outside.append(bd.Sphere(e.downpipe_radius).moved(bd.Location(point)))
        inside.append(bd.Sphere(e.downpipe_radius-e.downpipe_wall_thickness).moved(bd.Location(point)))
    shell = outside[0].fuse(*outside[1:]) if len(outside) > 1 else outside[0]
    return shell.cut(*inside)


def downpipe_parts(number, p, g, e=E):
    _, named, _, _, _ = _helpers()
    eave_z = 2*p.storey_height-g.roof_overhang*tan(radians(g.roof_pitch_degrees))
    y = p.depth-e.downpipe_north_inset
    parts = []
    for side, x, outlet_x in [
        ("west", -e.downpipe_wall_offset, -g.roof_overhang-e.gutter_width/2),
        ("east", p.width+e.downpipe_wall_offset, p.width+g.roof_overhang+e.gutter_width/2),
    ]:
        bottom = -g.slab_thickness-e.foundation_depth+e.downpipe_ground_clearance
        points = [(x, y, bottom), (x, y, p.storey_height)] if number == 1 else [
            (x, y, p.storey_height), (x, y, eave_z-e.downpipe_elbow_drop),
            (outlet_x, y, eave_z-e.gutter_top_below_eave-e.gutter_depth),
        ]
        parts.append(named(_rainpipe(points, e), f"F{number}:exterior:downpipe:{side}", "charcoal"))
    return parts


def roof_detail_parts(p, g, e=E):
    cuboid, named, _, section_extrusion, _ = _helpers()
    slope = tan(radians(g.roof_pitch_degrees))
    h, xmid, overhang = 2*p.storey_height, p.width/2, g.roof_overhang
    peak, eave = h+xmid*slope, h-overhang*slope
    y0, depth = -overhang, p.depth+2*overhang
    leaves = []
    # Gable finish is inside the approved finished wall face, matching the skin below.
    triangle = [(0, h), (p.width, h), (xmid, peak)]
    from .attic_geometry import north_vent_tool
    leaves.extend([
        named(section_extrusion(triangle, 0, e.cladding_thickness), "roof:cladding:south_gable", "exterior"),
        named(section_extrusion(triangle, p.depth-e.cladding_thickness, e.cladding_thickness).cut(north_vent_tool(p,g)),
              "roof:cladding:north_gable", "exterior"),
    ])
    # Standing seams follow the fall of each roof, with nineteen ribs per side for the default plan.
    # The nominal 455 mm pitch distributes to (8180 - 12) / 18 = 453.778 mm.
    count = int(depth/e.standing_seam_spacing)+2
    for i in range(count):
        y = y0+i*(depth-e.standing_seam_width)/(count-1)
        for side, xa, xb, za, zb in [
            ("west", -overhang, xmid, eave, peak),
            ("east", xmid, p.width+overhang, peak, eave),
        ]:
            z1, z2 = za+g.roof_vertical_thickness, zb+g.roof_vertical_thickness
            section = [(xa, z1), (xb, z2), (xb, z2+e.standing_seam_height),
                       (xa, z1+e.standing_seam_height)]
            leaves.append(named(section_extrusion(section, y, e.standing_seam_width),
                                 f"roof:standing_seam:{side}_{i+1:02d}", "roof"))
    a, lift, thick = e.ridge_cap_half_width, e.ridge_cap_lift, e.ridge_cap_thickness
    cap_base = peak+g.roof_vertical_thickness
    cap = [(xmid-a, cap_base-a*slope), (xmid, cap_base+lift),
           (xmid+a, cap_base-a*slope), (xmid+a, cap_base-a*slope+thick),
           (xmid, cap_base+lift+thick), (xmid-a, cap_base-a*slope+thick)]
    leaves.append(named(section_extrusion(cap, y0, depth), "roof:ridge_cap", "charcoal"))
    for end, y in [("south", y0-e.fascia_projection), ("north", p.depth+overhang)]:
        for side, xa, xb, za, zb in [
            ("west", -overhang, xmid, eave, peak),
            ("east", xmid, p.width+overhang, peak, eave),
        ]:
            section = [(xa, za-e.soffit_thickness), (xb, zb-e.soffit_thickness),
                       (xb, zb+g.roof_vertical_thickness), (xa, za+g.roof_vertical_thickness)]
            leaves.append(named(section_extrusion(section, y, e.fascia_projection),
                                 f"roof:fascia:{end}_{side}", "charcoal"))
    # Four soffit solids meet only at edges and follow the original underside slopes.
    for side, xa, xb, za, zb in [
        ("west", -overhang, 0, eave, h), ("east", p.width, p.width+overhang, h, eave),
    ]:
        section = [(xa, za-e.soffit_thickness), (xb, zb-e.soffit_thickness), (xb, zb), (xa, za)]
        leaves.append(named(section_extrusion(section, 0, p.depth), f"roof:soffit:{side}", "soffit"))
    section = [(-overhang, eave-e.soffit_thickness), (xmid, peak-e.soffit_thickness),
               (p.width+overhang, eave-e.soffit_thickness), (p.width+overhang, eave),
               (xmid, peak), (-overhang, eave)]
    for side, y in [("south", y0), ("north", p.depth)]:
        leaves.append(named(section_extrusion(section, y, overhang), f"roof:soffit:{side}", "soffit"))
    for side, x1, x2 in [("west", -overhang-e.gutter_width, -overhang),
                         ("east", p.width+overhang, p.width+overhang+e.gutter_width)]:
        top = eave-e.gutter_top_below_eave
        bottom, t = top-e.gutter_depth, e.gutter_wall_thickness
        gutter = cuboid((x1, y0, bottom, x2, p.depth+overhang, top))
        gutter = gutter.cut(cuboid((x1+t, y0+t, bottom+t, x2-t, p.depth+overhang-t, top+1)))
        # A bottom outlet connects the offset pipe; it is a real opening in the channel.
        outlet = bd.Solid.make_cylinder(e.downpipe_radius-e.downpipe_wall_thickness,
                                        t+2, bd.Plane(origin=((x1+x2)/2, p.depth-e.downpipe_north_inset, bottom-1)))
        leaves.append(named(gutter.cut(outlet), f"roof:gutter:{side}", "charcoal"))
    return leaves


def exterior_manifest(e=E, p=None):
    if p is None:
        from .house_plan import P
        p = P
    return {
        "reference": "references/japanese-house-exterior.md",
        "design": "Contemporary Japanese new-build detached house; continuous warm-white siding, timber-tone entry door, dark standing-seam gable roof",
        "parameters_mm": asdict(e),
        "entrance_canopy_enabled": getattr(p, "entrance_canopy", True),
        "entrance_shelter": "R13 1000 mm balcony above entrance; outer 300 mm of porch exposed; cantilever, waterproofing and drainage not designed",
        "model_origin": "Original parameterized BRep geometry with original procedural finish textures; no downloaded manufacturer mesh",
        "finished_wall_footprint": "8190 x 7280 mm approved R10 demonstration footprint; 20 mm finish replaces the outer wall band and a 2 mm backing gap",
        "projecting_attachments": "12 mm window trims, 35 mm sills, entrance porch, balcony shelter, fascias, gutters and downpipes project outside the finished wall footprint",
        "assumptions": [
            "暖白外壁、木色入户门、深灰立缝金属切妻屋顶及黑色窗框为风格示意，不对应已选定产品。",
            "外饰面厚20 mm和背后2 mm示意间隙均在180 mm墙厚范围内置换，R10主体完成外轮廓为8190 × 7280 mm。",
            "外饰面连续包住200 mm楼板与顶板外缘；仅退让外侧22 mm墙厚带，确认后的室内净边界和梯间洞口不变。",
            "窗框向外调整到70 mm厚外側墙带，原平面洞口、窗宽、窗台及窗高不变；外框和窗台为独立可编辑实体。",
            "玄关木色外扇、拉手、门框、平台及单级踏步为演示附件；R13保留无独立挑檐，1000 mm阳台覆盖入口但1300 mm平台外沿300 mm露出；门洞宽高和玄关位置不变。",
            "屋面原坡度30度、450 mm出檐与150 mm竖向厚度不变，另加立缝、棟包、破风、檐底、檐沟及按楼层拆分的雨水管。",
            "饰面、雨樋和玄关附件全部尺寸为演示假设，未验证实际构造层次、排水、结构、防火、地面标高或申报要求。",
        ],
    }
