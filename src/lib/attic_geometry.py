"""R06 low storage-attic concept within the unchanged R03 gable envelope.

All dimensions are millimetre-based demonstration assumptions. The existing
thin subfloor panel and capped finished ceiling replace the former solid
concept slab and high roof void. Separate demonstration framing is assembled
by the house module; no load rating or statutory classification is implied.
"""
from __future__ import annotations

from .orientation import orient_shape, orient_record

from dataclasses import asdict, dataclass
from math import cos, radians, sin, tan

from cadgen import build123d as bd

from .exterior_geometry import wall_setback


@dataclass(frozen=True)
class AtticParameters:
    north_vent_width: float = 600
    north_vent_height: float = 300
    north_vent_sill: float = 850
    north_vent_offset_from_ridge: float = 600
    deck_width: float = 3680
    deck_end_inset: float = 200
    deck_thickness: float = 18
    subfloor_thickness: float = 24
    maximum_finished_clear_height: float = 1350
    flat_ceiling_thickness: float = 50
    lining_vertical_allowance: float = 50
    knee_wall_thickness: float = 50
    gable_lining_thickness: float = 20
    hatch_x: float = 4100
    hatch_y: float = 3505
    hatch_length: float = 1200
    hatch_width: float = 650
    hatch_trim_width: float = 35
    hatch_trim_drop: float = 35
    hatch_lid_thickness: float = 18
    hinge_mount_width: float = 35
    hinge_mount_height: float = 12
    deployed_lid_vertical_gap: float = 20
    guardrail_post_width: float = 40
    guardrail_height: float = 750
    guardrail_rail_height: float = 40
    shelf_width: float = 600
    shelf_depth: float = 1500
    shelf_height: float = 650
    shelf_panel_thickness: float = 18
    shelf_side_inset: float = 100
    shelf_north_inset: float = 380
    storage_box_width: float = 450
    storage_box_depth: float = 600
    storage_box_height: float = 450
    storage_box_lid_thickness: float = 20
    storage_box_side_inset: float = 500
    storage_box_y: float = 650
    ladder_width: float = 600
    ladder_angle_degrees: float = 65
    ladder_stringer_width: float = 40
    ladder_stringer_vertical_depth: float = 100
    ladder_treads: int = 10
    ladder_tread_depth: float = 100
    ladder_tread_thickness: float = 25
    ladder_bottom_landing_depth: float = 600


A = AtticParameters()


def north_vent_bounds(p,g,a=A):
    center=p.width/2+a.north_vent_offset_from_ridge
    z=2*p.storey_height+a.deck_thickness+a.north_vent_sill
    return (center-a.north_vent_width/2,p.depth-p.external_wall-a.gable_lining_thickness-1,z,
            center+a.north_vent_width/2,p.depth+1,z+a.north_vent_height)


def north_vent_tool(p,g,a=A):
    cuboid,_,_=_helpers()
    return cuboid(north_vent_bounds(p,g,a))


def _north_vent_group(p,g,a=A):
    cuboid,named,_=_helpers();x1,_,z1,x2,_,z2=north_vent_bounds(p,g,a)
    y=p.depth-35;fw=35;leaves=[]
    for i,b in enumerate([(x1,y-35,z1,x2,y+15,z1+fw),(x1,y-35,z2-fw,x2,y+15,z2),
                          (x1,y-35,z1+fw,x1+fw,y+15,z2-fw),(x2-fw,y-35,z1+fw,x2,y+15,z2-fw)],1):
        leaves.append(named(cuboid(b),f'attic:north_vent:frame_{i}','frame'))
    # Top-hung sash is tilted outward 15 degrees, so the aperture is genuinely open.
    sash=cuboid((x1+fw,y-6,z1+fw,x2-fw,y+6,z2-fw))
    hinge=bd.Axis((x1,y,z2-fw),(1,0,0))
    sash=sash.rotate(hinge,15)
    leaves.append(named(sash,'attic:north_vent:open_glass','glass',.35))
    leaves.append(named(cuboid((x1-20,p.depth,z1-30,x2+20,p.depth+35,z1-15)),
                        'attic:north_vent:sill','charcoal'))
    return bd.Compound(children=leaves,label='attic:windows')


def _helpers():
    # Lazy imports avoid a cycle with the house assembly integration.
    from .house_geometry import cuboid, named, section_extrusion
    return cuboid, named, section_extrusion


def attic_dimensions(p, g, a=A):
    """Shared exact dimensions for geometry and the recorded proposal manifest."""
    zbase = 2 * p.storey_height
    deck_top = zbase + a.deck_thickness
    deck_left = (p.width - a.deck_width) / 2
    deck_right = deck_left + a.deck_width
    hatch_right = a.hatch_x + a.hatch_length
    hatch_north = a.hatch_y + a.hatch_width
    ladder_rise = deck_top - p.storey_height
    ladder_run = ladder_rise / tan(radians(a.ladder_angle_degrees))
    panel_bottom = zbase - a.subfloor_thickness
    ceiling_bottom = deck_top + a.maximum_finished_clear_height
    ceiling_left = (ceiling_bottom + a.lining_vertical_allowance - zbase) / tan(radians(g.roof_pitch_degrees))
    if not (0 < a.flat_ceiling_thickness <= a.lining_vertical_allowance):
        raise ValueError("Attic flat ceiling thickness must fit the lining's vertical allowance")
    if not (deck_left < ceiling_left < p.width / 2):
        raise ValueError("Attic capped ceiling must meet both roof slopes within the finished deck")
    # The deployed cover hangs below the stringers. Its conceptual hinge drop
    # follows the new panel underside, rather than relying on the old slab.
    ladder_back_depth = max(a.ladder_stringer_vertical_depth,
                            a.ladder_tread_depth / 2 * tan(radians(a.ladder_angle_degrees))
                            + a.ladder_tread_thickness)
    lid_hinge_drop = max(a.hatch_trim_drop + a.hinge_mount_height,
                        ladder_back_depth - a.subfloor_thickness
                        - a.deck_thickness + a.deployed_lid_vertical_gap)
    return {
        "base_z": zbase, "deck_top_z": deck_top,
        "panel_bottom_z": panel_bottom,
        "ceiling_bottom_z": ceiling_bottom,
        "ceiling_top_z": ceiling_bottom + a.flat_ceiling_thickness,
        "ceiling_left": ceiling_left, "ceiling_right": p.width - ceiling_left,
        "lid_hinge_z": panel_bottom - lid_hinge_drop,
        "lid_hinge_drop": lid_hinge_drop,
        "ladder_back_depth": ladder_back_depth,
        "deck_left": deck_left, "deck_right": deck_right,
        "hatch_right": hatch_right, "hatch_north": hatch_north,
        "ladder_center_y": a.hatch_y + a.hatch_width / 2,
        "ladder_rise": ladder_rise, "ladder_run": ladder_run,
        "ladder_foot_x": hatch_right - ladder_run,
    }


def roof_underside_z(x, p, g):
    return 2 * p.storey_height + min(x, p.width - x) * tan(radians(g.roof_pitch_degrees))


def attic_clear_height(x, p, g, a=A):
    """Finished height to the physical sloping/flat ceiling, not roof space."""
    d = attic_dimensions(p, g, a)
    return min(roof_underside_z(x, p, g) - a.lining_vertical_allowance,
               d["ceiling_bottom_z"]) - d["deck_top_z"]


def _hatch_cut(p, g, a=A):
    cuboid, _, _ = _helpers()
    d = attic_dimensions(p, g, a)
    # One over-length tool cuts both the 24 mm panel and the 18 mm finish.
    return cuboid((a.hatch_x, a.hatch_y, d["panel_bottom_z"] - 1,
                   d["hatch_right"], d["hatch_north"], d["deck_top_z"] + 1))


def _floor_group(p, g, a=A):
    cuboid, named, _ = _helpers()
    d = attic_dimensions(p, g, a)
    setback = wall_setback()
    tool = _hatch_cut(p, g, a)
    slab = cuboid((setback, setback, d["panel_bottom_z"],
                   p.width - setback, p.depth - setback, d["base_z"])).cut(tool)
    # The old leaf name survives the real hierarchy move for stable selection.
    slab = named(slab, "roof:attic_ceiling_slab", "slab")
    finish = cuboid((d["deck_left"], a.deck_end_inset, d["base_z"],
                     d["deck_right"], p.depth - a.deck_end_inset, d["deck_top_z"])).cut(tool)
    finish = named(finish, "attic:deck_finish", "attic_wood")
    return bd.Compound(children=[slab, finish], label="attic:floor_slab")


def _partition_group(p, g, a=A):
    _, named, section_extrusion = _helpers()
    d = attic_dimensions(p, g, a)
    left, right = d["deck_left"], d["deck_right"]
    outer_left, outer_right = left - a.knee_wall_thickness, right + a.knee_wall_thickness
    south = p.external_wall
    depth = p.depth - 2 * south
    offset = a.lining_vertical_allowance

    def lining_section(x1, x2):
        z1, z2 = roof_underside_z(x1, p, g), roof_underside_z(x2, p, g)
        return [(x1, z1 - offset), (x2, z2 - offset), (x2, z2), (x1, z1)]

    leaves = [
        named(section_extrusion(lining_section(outer_left, d["ceiling_left"]), south, depth),
              "attic:lining:west_slope", "attic_lining"),
        named(section_extrusion(lining_section(d["ceiling_right"], outer_right), south, depth),
              "attic:lining:east_slope", "attic_lining"),
        named(section_extrusion([(d["ceiling_left"], d["ceiling_bottom_z"]),
                                 (d["ceiling_right"], d["ceiling_bottom_z"]),
                                 (d["ceiling_right"], d["ceiling_top_z"]),
                                 (d["ceiling_left"], d["ceiling_top_z"])], south, depth),
              "attic:lining:flat_ceiling", "attic_lining"),
    ]
    for side, x1, x2 in [("west", outer_left, left), ("east", right, outer_right)]:
        # Sloping tops touch the underside of the lining without entering it.
        points = [(x1, d["base_z"]), (x2, d["base_z"]),
                  (x2, roof_underside_z(x2, p, g) - offset),
                  (x1, roof_underside_z(x1, p, g) - offset)]
        leaves.append(named(section_extrusion(points, south, depth),
                            f"attic:knee_wall:{side}", "attic_lining"))
    gable_points = [(left, d["deck_top_z"]), (right, d["deck_top_z"]),
                    (right, roof_underside_z(right, p, g) - offset),
                    (d["ceiling_right"], d["ceiling_bottom_z"]),
                    (d["ceiling_left"], d["ceiling_bottom_z"]),
                    (left, roof_underside_z(left, p, g) - offset)]
    for side, y in [("south", south), ("north", p.depth - south - a.gable_lining_thickness)]:
        lining=section_extrusion(gable_points,y,a.gable_lining_thickness)
        if side=='north':lining=lining.cut(north_vent_tool(p,g,a))
        leaves.append(named(lining,
                            f"attic:gable_lining:{side}", "attic_lining"))
    return bd.Compound(children=leaves, label="attic:partition_walls")


def _shelf(side, x1, x2, y1, y2, z1, a=A):
    cuboid, _, _ = _helpers()
    prefix = f"attic:storage:{side}_shelf"
    t, z2 = a.shelf_panel_thickness, z1 + a.shelf_height
    bx1, bx2 = (x1, x1 + t) if side == "west" else (x2 - t, x2)
    ix1, ix2 = (x1 + t, x2) if side == "west" else (x1, x2 - t)
    panels = {
        "back": (bx1, y1, z1, bx2, y2, z2),
        "side_south": (ix1, y1, z1 + t, ix2, y1 + t, z2 - t),
        "side_north": (ix1, y2 - t, z1 + t, ix2, y2, z2 - t),
        "bottom": (ix1, y1, z1, ix2, y2, z1 + t),
        "middle": (ix1, y1 + t, z1 + a.shelf_height / 2 - t / 2,
                   ix2, y2 - t, z1 + a.shelf_height / 2 + t / 2),
        "top": (ix1, y1, z2 - t, ix2, y2, z2),
    }
    return bd.Compound(children=[cuboid(bounds, f"{prefix}:{part}", "attic_wood")
                                 for part, bounds in panels.items()], label=prefix)


def _storage_group(p, g, a=A):
    cuboid, _, _ = _helpers()
    d = attic_dimensions(p, g, a)
    shelf_y2 = p.depth - a.shelf_north_inset
    shelf_y1 = shelf_y2 - a.shelf_depth
    west_x1 = d["deck_left"] + a.shelf_side_inset
    east_x2 = d["deck_right"] - a.shelf_side_inset
    children = [_shelf("west", west_x1, west_x1 + a.shelf_width, shelf_y1, shelf_y2, d["deck_top_z"], a),
                _shelf("east", east_x2 - a.shelf_width, east_x2, shelf_y1, shelf_y2, d["deck_top_z"], a)]
    for side, x in [("southwest", d["deck_left"] + a.storage_box_side_inset),
                    ("southeast", d["deck_right"] - a.storage_box_side_inset - a.storage_box_width)]:
        prefix = f"attic:storage:{side}_box"
        z1, z2 = d["deck_top_z"], d["deck_top_z"] + a.storage_box_height
        children.append(bd.Compound(children=[
            cuboid((x, a.storage_box_y, z1, x + a.storage_box_width,
                    a.storage_box_y + a.storage_box_depth, z2 - a.storage_box_lid_thickness),
                   f"{prefix}:body", "storage"),
            cuboid((x, a.storage_box_y, z2 - a.storage_box_lid_thickness,
                    x + a.storage_box_width, a.storage_box_y + a.storage_box_depth, z2),
                   f"{prefix}:lid", "attic_wood"),
        ], label=prefix))
    return bd.Compound(children=children, label="attic:storage_fixtures")


def _guardrail_group(p, g, a=A):
    cuboid, _, _ = _helpers()
    d = attic_dimensions(p, g, a)
    w, x1, x2, y1, y2 = a.guardrail_post_width, a.hatch_x, d["hatch_right"], a.hatch_y, d["hatch_north"]
    z1, z2 = d["deck_top_z"], d["deck_top_z"] + a.guardrail_height
    leaves = []
    for side, x, y in [("southwest", x1 - w, y1 - w), ("southeast", x2, y1 - w),
                       ("northwest", x1 - w, y2), ("northeast", x2, y2)]:
        leaves.append(cuboid((x, y, z1, x + w, y + w, z2),
                             f"attic:guardrail:post_{side}", "attic_wood"))
    rail_z = z2 - a.guardrail_rail_height
    rails = {
        "west": (x1 - w, y1, rail_z, x1, y2, z2),
        "south": (x1, y1 - w, rail_z, x2, y1, z2),
        "north": (x1, y2, rail_z, x2, y2 + w, z2),
    }
    leaves += [cuboid(bounds, f"attic:guardrail:{side}_rail", "attic_wood")
               for side, bounds in rails.items()]
    return bd.Compound(children=leaves, label="attic:guardrails")


@orient_shape
def attic_group(p, g, a=A):
    return bd.Compound(children=[_floor_group(p, g, a), _partition_group(p, g, a),
                                 _storage_group(p, g, a), _guardrail_group(p, g, a),_north_vent_group(p,g,a)], label="attic")


@orient_shape
def attic_access_group(p, g, a=A):
    cuboid, named, section_extrusion = _helpers()
    d = attic_dimensions(p, g, a)
    theta = radians(a.ladder_angle_degrees)
    slope = tan(theta)
    x0, x1 = d["ladder_foot_x"], d["hatch_right"]
    z0, z1 = p.storey_height, d["deck_top_z"]
    y0 = d["ladder_center_y"] - a.ladder_width / 2
    y1 = y0 + a.ladder_width
    depth = a.ladder_stringer_vertical_depth
    # Clip the low toe at the F2 floor rather than extending a rail below it.
    rail_points = [(x0, z0), (x0 + depth / slope, z0),
                   (x1, z1 - depth), (x1, z1)]
    leaves = [named(section_extrusion(rail_points, y0, a.ladder_stringer_width),
                    "attic_access:left_stringer", "attic_wood"),
              named(section_extrusion(rail_points, y1 - a.ladder_stringer_width, a.ladder_stringer_width),
                    "attic_access:right_stringer", "attic_wood")]
    rise = d["ladder_rise"] / (a.ladder_treads + 1)
    for index in range(1, a.ladder_treads + 1):
        z = z0 + index * rise
        x = x0 + index * rise / slope
        leaves.append(cuboid((x - a.ladder_tread_depth / 2, y0 + a.ladder_stringer_width,
                              z - a.ladder_tread_thickness, x + a.ladder_tread_depth / 2,
                              y1 - a.ladder_stringer_width, z),
                             f"attic_access:tread_{index:02d}", "attic_wood"))
    ceiling_bottom = d["panel_bottom_z"]
    trim = a.hatch_trim_width
    outer = cuboid((a.hatch_x - trim, a.hatch_y - trim, ceiling_bottom - a.hatch_trim_drop,
                    d["hatch_right"] + trim, d["hatch_north"] + trim, ceiling_bottom))
    tool = cuboid((a.hatch_x, a.hatch_y, ceiling_bottom - a.hatch_trim_drop - 1,
                   d["hatch_right"], d["hatch_north"], ceiling_bottom + 1))
    leaves.append(named(outer.cut(tool), "attic_access:hatch_trim", "attic_lining"))
    lid_top = (d["hatch_right"], d["lid_hinge_z"])
    lid_bottom = (lid_top[0] - a.hatch_length * cos(theta), lid_top[1] - a.hatch_length * sin(theta))
    # Offset to the back (+X/-Z), away from the ladder's lower rail surface.
    back = (a.hatch_lid_thickness * sin(theta), -a.hatch_lid_thickness * cos(theta))
    # The thick sheet's hinge end is cut at X=hatch_right. Keeping its entire
    # thickness inside that edge avoids a hidden overlap with the outer trim.
    lid_points = [lid_bottom, lid_top,
                  (lid_top[0], lid_top[1] + back[1] - back[0] * slope),
                  (lid_bottom[0] + back[0], lid_bottom[1] + back[1])]
    leaves.append(named(section_extrusion(lid_points, a.hatch_y, a.hatch_width),
                        "attic_access:hatch_lid", "attic_lining"))
    # These conceptual drop brackets connect the trim underside to the lid
    # hinge. They do not model a selected folding-ladder product or mechanism.
    for side, y in [("left", a.hatch_y), ("right", d["hatch_north"] - a.hinge_mount_width)]:
        mount_top = ceiling_bottom - a.hatch_trim_drop
        leaves.append(cuboid((d["hatch_right"], y, d["lid_hinge_z"],
                              d["hatch_right"] + a.hinge_mount_width, y + a.hinge_mount_width,
                              mount_top),
                             f"attic_access:hinge_{side}", "frame"))
    return bd.Compound(children=leaves, label="attic_access")


@orient_record
def attic_manifest(p, g, a=A):
    d = attic_dimensions(p, g, a)
    theta = radians(a.ladder_angle_degrees)
    finished_depth = p.depth - 2 * a.deck_end_inset
    ladder_y0 = d["ladder_center_y"] - a.ladder_width / 2
    ladder_y1 = ladder_y0 + a.ladder_width
    assumptions = [
        "R10阁楼采用纯储物用途的演示方案，保留已确认的一、二层房间净边界及 R10 切妻屋顶外形；未指定所在地，不认定为获准免计面积的阁楼或第三层居室。",
        "原厚200 mm概念顶板由24 mm示意基层板替换，Z=5576–5600 mm；净检修口1200 × 650 mm贯穿基层板与18 mm饰面，完成面为 Z=5618 mm。基层板本身不代表承重能力。",
        "阁楼板面净范围3680 × 6880 mm，扣除检修口的几何投影面积为24.5384㎡；该面积不是建筑法规或申报面积结论。",
        "新增实体平顶与两侧斜内衬，完成净高不超过1350 mm，平顶底面Z=6968 mm、实体厚50 mm，两侧板面边缘净高约1233.93 mm；1350 mm是演示设计目标，不是所在地法规合格结论。",
        "斜屋面内衬仍采用50 mm竖向展示预留，平顶上方剩余屋顶空间不作为储物可用空间；真实保温、通风、天花吊挂、防火和构造层次仍待设计。采用固定平顶控制净高仅为候选做法；当地对完成天花及上方残余空腔的计量、楼层认定待确认，不能认定增设天花即可免计面积或楼层。",
        "两侧50 mm厚低墙和南北20 mm厚内衬、650 mm高开放收纳架及450 mm高储物箱均为原创可修改占位参数，未选实际产品。",
        "检修梯以展开状态示意，宽600 mm、角度65度、跨高2818 mm，11等踢高约256.18 mm并显示10级踏步；阁楼板面承担最后一级，不另设遮挡检修口的面板。",
        "检修梯展开包络及600 mm深底端站位位于二层廊下，展开期间占用廊下通行；上口站位最低净高约1254.13 mm，仅表达低净高储物检修关系，未确认实际产品、安全操作或同时通行。",
        "检修口饰框依24 mm基层板底面定位，展开盖板以20 mm最小竖向展示间隙避开踏板及梯梁，并通过独立命名的示意下挂支架连接；不是可施工的折叠机械设计。",
        "独立木构件仅为结构传力方案展示，不构成梁柱、楼面承载、接合、基础或法规验算；所在地、地盘、荷载、材料和最终尺寸均待日本建筑士核定。全部新增尺寸为演示假设。",
    ]
    return {
        "purpose": "storage attic / 小屋裏収納 / 储物阁楼",
        "revision": "R15",
        "status": "demonstration proposal, not structural or statutory design",
        "statutory_area_status": "geometric projection only; local floor/storey classification pending",
        "parameters": asdict(a),
        "north_vent_bounds_mm": list(north_vent_bounds(p,g,a)),
        "north_vent_status": "600 x 300 mm top-hung demonstration aperture; airflow, insect screen, flashing, fire and rain details unverified",
        "unchanged": ["R15 reflected F1/F2 room topology and areas", "R10 roof geometry and exterior silhouette"],
        "existing_floor_leaf": "roof:attic_ceiling_slab",
        "floor_group": "attic:floor_slab",
        "slab_bounds_mm": [wall_setback(), wall_setback(), d["panel_bottom_z"],
                           p.width - wall_setback(), p.depth - wall_setback(), d["base_z"]],
        "deck_bounds_mm": [d["deck_left"], a.deck_end_inset, d["base_z"],
                           d["deck_right"], p.depth - a.deck_end_inset, d["deck_top_z"]],
        "hatch_bounds_mm": [a.hatch_x, a.hatch_y, d["panel_bottom_z"],
                            d["hatch_right"], d["hatch_north"], d["deck_top_z"]],
        "storage_projection_area_m2": (a.deck_width * finished_depth - a.hatch_length * a.hatch_width) / 1e6,
        "flat_ceiling_bounds_mm": [d["ceiling_left"], p.external_wall, d["ceiling_bottom_z"],
                                   d["ceiling_right"], p.depth - p.external_wall, d["ceiling_top_z"]],
        "finished_ceiling_profile_xz_mm": [
            [d["deck_left"], d["deck_top_z"] + attic_clear_height(d["deck_left"], p, g, a)],
            [d["ceiling_left"], d["ceiling_bottom_z"]],
            [d["ceiling_right"], d["ceiling_bottom_z"]],
            [d["deck_right"], d["deck_top_z"] + attic_clear_height(d["deck_right"], p, g, a)],
        ],
        "clear_height_mm": {"maximum": a.maximum_finished_clear_height,
                             "ridge": attic_clear_height(p.width / 2, p, g, a),
                             "deck_edge": attic_clear_height(d["deck_left"], p, g, a),
                             "formula": "min(tan(roof_pitch) * min(x, width-x) - lining_vertical_allowance - deck_thickness, maximum_finished_clear_height)"},
        "ladder": {
            "state": "deployed concept, independently hideable",
            "top_mm": [d["hatch_right"], d["ladder_center_y"], d["deck_top_z"]],
            "foot_mm": [d["ladder_foot_x"], d["ladder_center_y"], p.storey_height],
            "rise_mm": d["ladder_rise"], "horizontal_run_mm": d["ladder_run"],
            "inclined_length_mm": d["ladder_rise"] / sin(theta),
            "riser_count": a.ladder_treads + 1, "tread_count": a.ladder_treads,
            "riser_mm": d["ladder_rise"] / (a.ladder_treads + 1),
            "deployed_plan_bounds_mm": [d["ladder_foot_x"], ladder_y0, d["hatch_right"], ladder_y1],
            "bottom_landing_bounds_mm": [d["ladder_foot_x"] - a.ladder_bottom_landing_depth,
                                         a.hatch_y, d["ladder_foot_x"], d["hatch_north"]],
            "upper_landing_bounds_mm": [d["hatch_right"], a.hatch_y,
                                        d["hatch_right"] + a.ladder_bottom_landing_depth, d["hatch_north"]],
            "upper_landing_min_clear_height_mm": min(
                attic_clear_height(x, p, g, a)
                for x in (d["hatch_right"], d["hatch_right"] + a.ladder_bottom_landing_depth)),
            "lid_hinge_z_mm": d["lid_hinge_z"],
            "lid_hinge_drop_below_panel_mm": d["lid_hinge_drop"],
            "lid_to_stringer_gap_mm": (d["deck_top_z"] - a.ladder_stringer_vertical_depth - d["lid_hinge_z"]) * cos(theta),
            "lid_to_ladder_back_vertical_gap_mm": d["deck_top_z"] - d["ladder_back_depth"] - d["lid_hinge_z"],
        },
        "assumptions": assumptions,
    }
