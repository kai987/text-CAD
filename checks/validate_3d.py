"""Acceptance checks against the saved named STEP and metre/Y-up GLB."""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import math
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))

from cadgen import read_scene
from cadgen.geometry import overlap_volume
from lib.house_plan import P, dimensions, floor_plan
from lib.house_geometry import G, cuboid, extruded_polygon, opening_box, window_vertical_range
from lib.exterior_geometry import E


results = []


def check(name, ok, actual=None, expected=None):
    results.append({"check": name, "pass": bool(ok), "actual": actual, "expected": expected})


def close(name, actual, expected, tolerance=0.01):
    check(name, abs(actual-expected) <= tolerance, round(actual, 6), expected)


def bounds(shape):
    b = shape.bounding_box()
    return [b.min.X, b.min.Y, b.min.Z, b.max.X, b.max.Y, b.max.Z]


def intersects_bounds(a, b):
    return all(a[i] < b[i+3]-1e-7 and b[i] < a[i+3]-1e-7 for i in range(3))


def overlap(shapes, tool):
    tb = bounds(tool)
    tool_solids = tool.solids()
    total = 0.0
    for shape in shapes:
        for solid in shape.solids():
            if intersects_bounds(bounds(solid), tb):
                total += sum(overlap_volume(solid, ts) for ts in tool_solids)
    return total


def exterior_core_tool(axis, at, start, width, z1, z2):
    """A test region through the retained backing, excluding the finish gap.

    The approved 180 mm wall still ends at the same interior room boundary.
    The outer 22 mm is now 20 mm finish plus a 2 mm visual separation. This
    region tests the remaining backing with 1 mm clearance from each face.
    """
    setback = E.cladding_thickness+E.backing_gap
    limit = P.depth if axis == "h" else P.width
    low_side = at < limit/2
    center = P.external_wall/2+setback/2 if low_side else limit-P.external_wall/2-setback/2
    return opening_box(axis, center, start, width, P.external_wall-setback-4, z1, z2)


step_path = ROOT/"STEP"/"house_3d.step"
glb_path = ROOT/"GLB"/"house_3d.glb"
check("saved_STEP_is_nonempty", step_path.stat().st_size > 1000, step_path.stat().st_size)
check("saved_GLB_is_nonempty", glb_path.stat().st_size > 1000, glb_path.stat().st_size)
scene = read_scene(step_path)
leaves = list(scene.leaves())
check("all_STEP_leaf_labels_unique", len({o.label for o in leaves}) == len(leaves), len(leaves))
native = {}
solid_count = 0
for occurrence in leaves:
    shape = occurrence.shape()
    native[occurrence.label] = shape
    solids = shape.solids()
    check(f"{occurrence.label}:contains_solid", len(solids) > 0, len(solids))
    for i, solid in enumerate(solids, 1):
        solid_count += 1
        check(f"{occurrence.label}:solid_{i}_valid", solid.is_valid)
        check(f"{occurrence.label}:solid_{i}_positive_volume", solid.volume > 0, round(solid.volume, 3))


for number in (1, 2):
    plan = floor_plan(number)
    z = (number-1)*P.storey_height
    wall_height = P.storey_height-G.slab_thickness
    setback = E.cladding_thickness+E.backing_gap
    core = [shape for label, shape in native.items()
            if label.startswith(f"F{number}:wall_external_")]
    cladding = [shape for label, shape in native.items()
                if label.startswith(f"F{number}:exterior:cladding:")]
    partitions = [shape for label, shape in native.items()
                  if label.startswith(f"F{number}:wall_partition_")]
    walls = core+partitions+cladding
    check(f"F{number}:four_external_backing_walls", len(core) == 4, len(core), 4)
    check(f"F{number}:independent_external_finish", bool(cladding), len(cladding))
    core_bounds = [min(bounds(s)[i] for s in core) for i in range(3)]+ \
                  [max(bounds(s)[i+3] for s in core) for i in range(3)]
    expected_core_bounds = [setback, setback, z, P.width-setback, P.depth-setback, z+wall_height]
    for coordinate, (actual, expected) in enumerate(zip(core_bounds, expected_core_bounds)):
        close(f"F{number}:external_backing_bound_{coordinate}", actual, expected)
    finish_bounds = [min(bounds(s)[i] for s in cladding) for i in range(3)]+ \
                    [max(bounds(s)[i+3] for s in cladding) for i in range(3)]
    expected_finish_bounds = [0, 0, z-G.slab_thickness, P.width, P.depth,
                              z+wall_height+(G.slab_thickness if number == 2 else 0)]
    for coordinate, (actual, expected) in enumerate(zip(finish_bounds, expected_finish_bounds)):
        close(f"F{number}:approved_finished_outline_bound_{coordinate}", actual, expected)
    core_area = (P.width-2*setback)*(P.depth-2*setback)- \
                (P.width-2*P.external_wall)*(P.depth-2*P.external_wall)
    exterior_aperture_area = sum(d.width*G.door_height for d in plan.doors if d.a == "outside")+ \
                             sum(window[3]*window_vertical_range(window)[1] for window in plan.windows)
    close(f"F{number}:backing_volume_preserves_inner_room_boundary_mm3", sum(s.volume for s in core),
          core_area*wall_height-exterior_aperture_area*(P.external_wall-setback), 0.1)
    close(f"F{number}:finish_backing_no_coincident_solids_mm3", sum(overlap(core, s) for s in cladding), 0)
    for direction in ("south", "north", "west", "east"):
        # Safe spans below all window sills and clear of the south entrance.
        a, b = E.cladding_thickness, setback
        cx, cy = P.width/2, P.depth/2
        sample_bounds = {
            "south": (cx-50, a+.1, z+100, cx+50, b-.1, z+200),
            "north": (cx-50, P.depth-b+.1, z+100, cx+50, P.depth-a-.1, z+200),
            "west": (a+.1, cy-50, z+100, b-.1, cy+50, z+200),
            "east": (P.width-b+.1, cy-50, z+100, P.width-a-.1, cy+50, z+200),
        }[direction]
        close(f"F{number}:{direction}:finish_backing_gap_is_clear_mm3", overlap(core+cladding, cuboid(sample_bounds)), 0)
    for room in plan.rooms:
        room_clearance = extruded_polygon(room.shape.buffer(-.1), z+1, wall_height-2)
        close(f"F{number}:{room.id}:approved_net_room_not_encroached_mm3", overlap(walls, room_clearance), 0)
    # Test physical clear openings through the new projecting attachments as
    # well as the retained backing. Window jambs/glass and the intentionally
    # closed entrance door are excluded; their approved opening dimensions are
    # tested separately below. Trim, sill, canopy and accent are not excluded.
    attachments = [shape for label, shape in native.items()
                   if label.startswith(f"F{number}:exterior:") or
                   (label.startswith(f"F{number}:W") and label.endswith((":exterior_trim", ":sill"))) or
                   (label.startswith(f"F{number}:D") and label.endswith((":frame", ":canopy", ":porch", ":porch_step", ":threshold")))]
    for door in plan.doors:
        if door.a == "outside":
            swept = opening_box(door.axis, door.at, door.start+.1, door.width-.2, 1400,
                                z+.1, z+G.door_height-.1)
            close(f"F{number}:{door.id}:projecting_attachments_clear_of_aperture_mm3", overlap(attachments, swept), 0)
    for i, window in enumerate(plan.windows, 1):
        axis, at, start, width = window
        sill, height = window_vertical_range(window)
        swept = opening_box(axis, at, start+.1, width-.2, 1400, z+sill+.1, z+sill+height-.1)
        close(f"F{number}:W{i:02d}:projecting_attachments_clear_of_aperture_mm3", overlap(attachments, swept), 0)
    slab = native[f"F{number}:floor_slab"]
    slab_bounds = bounds(slab)
    close(f"F{number}:floor_datum_mm", slab_bounds[5], z)
    close(f"F{number}:slab_thickness_mm", slab_bounds[5]-slab_bounds[2], G.slab_thickness)
    for coordinate, expected in ((0, setback), (1, setback), (3, P.width-setback), (4, P.depth-setback)):
        close(f"F{number}:slab_edge_backing_bound_{coordinate}", slab_bounds[coordinate], expected)
    if number == 1:
        close("F1:slab_net_volume_mm3", slab.volume,
              (P.width-2*setback)*(P.depth-2*setback)*G.slab_thickness, 0.1)
    for door in plan.doors:
        thickness = P.external_wall if door.a == "outside" else P.internal_wall
        tool = opening_box(door.axis, door.at, door.start, door.width,
                           thickness, z, z+G.door_height)
        close(f"F{number}:{door.id}:wall_opening_volume_mm3", overlap(walls, tool), 0)
        if door.a == "outside":
            head = exterior_core_tool(door.axis, door.at, door.start, door.width,
                                      z+G.door_height+1, z+wall_height-1)
            backing_walls = core
        else:
            head = opening_box(door.axis, door.at, door.start, door.width,
                               thickness-2, z+G.door_height+1, z+wall_height-1)
            backing_walls = partitions
        close(f"F{number}:{door.id}:overdoor_wall_preserved_mm3",
              overlap(backing_walls, head), head.volume, 0.1)
    for i, window in enumerate(plan.windows, 1):
        sill, height = window_vertical_range(window)
        tool = opening_box(*window, P.external_wall, z+sill, z+sill+height)
        close(f"F{number}:W{i:02d}:wall_opening_volume_mm3", overlap(walls, tool), 0)
        below = exterior_core_tool(*window, z+1, z+sill-1)
        above = exterior_core_tool(*window, z+sill+height+1, z+wall_height-1)
        close(f"F{number}:W{i:02d}:wall_below_preserved_mm3", overlap(core, below), below.volume, 0.1)
        close(f"F{number}:W{i:02d}:wall_above_preserved_mm3", overlap(core, above), above.volume, 0.1)
        original_frames = [native[f"F{number}:W{i:02d}:frame_{j}"] for j in range(1, 5)]
        wb = [min(bounds(s)[j] for s in original_frames) for j in range(3)]+ \
             [max(bounds(s)[j+3] for s in original_frames) for j in range(3)]
        axis, at, start, width = window
        tangent, normal = (0, 1) if axis == "h" else (1, 0)
        limit = P.depth if axis == "h" else P.width
        expected_normal = (0, G.window_frame_depth) if at < limit/2 else (limit-G.window_frame_depth, limit)
        for coordinate, expected in ((tangent, start), (tangent+3, start+width),
                                     (normal, expected_normal[0]), (normal+3, expected_normal[1]),
                                     (2, z+sill), (5, z+sill+height)):
            close(f"F{number}:W{i:02d}:unchanged_aperture_and_flush_frame_bound_{coordinate}", wb[coordinate], expected)


d = dimensions(P)
stair_footprint = next(r.shape for r in floor_plan(2).rooms if r.id == "stairs")
x1, y1, x2, y2 = stair_footprint.bounds
slab2 = native["F2:floor_slab"]
opening = cuboid((x1, y1, P.storey_height-G.slab_thickness-1,
                   x2, y2, P.storey_height+1))
close("F2:complete_stairwell_opening_volume_mm3", overlap([slab2], opening), 0)
close("F2:slab_net_volume_mm3", slab2.volume,
      ((P.width-2*setback)*(P.depth-2*setback)-stair_footprint.area)*G.slab_thickness, 0.1)
stair_shapes = [shape for label, shape in native.items() if label.startswith("stairs:")]
close("stairs:no_F2_slab_overlap_mm3", overlap(stair_shapes, slab2.solids()[0]), 0)
check("stairs:no_final_riser_consuming_tread", "stairs:upper_final_riser" not in native)
rise = P.storey_height/P.risers
close("stairs:specified_rise_mm", rise, 175)
landing_bounds = bounds(native["stairs:mid_landing"])
close("stairs:mid_landing_top_mm", landing_bounds[5], P.storey_height/2)
close("stairs:mid_landing_depth_mm", landing_bounds[4]-landing_bounds[1], P.stair_landing)
close("stairs:mid_landing_thickness_mm", landing_bounds[5]-landing_bounds[2], G.landing_thickness)
for flight, base_top in [("lower", 0), ("upper", P.storey_height/2)]:
    for i in range(1, P.risers//2):
        label = f"stairs:{flight}_tread_{i:02d}"
        sb = bounds(native[label])
        close(f"{label}:width_mm", sb[3]-sb[0], P.stair_width)
        close(f"{label}:tread_depth_mm", sb[4]-sb[1], P.tread)
        close(f"{label}:top_elevation_mm", sb[5], base_top+i*rise)
last_top = bounds(native["stairs:upper_tread_07"])[5]
close("stairs:final_floor_rise_mm", bounds(slab2)[5]-last_top, rise)
for side in ("lower", "upper"):
    end = native[f"stairs:{side}_tread_{'07' if side == 'lower' else '01'}"]
    landing = native["stairs:mid_landing"]
    close(f"stairs:{side}_landing_connection_distance_mm", end.distance_to(landing), 0)
wc1 = next(r.shape for r in floor_plan(1).rooms if r.id == "wc")
wc2 = next(r.shape for r in floor_plan(2).rooms if r.id == "wc")
check("WC:upper_lower_footprints_aligned", wc1.equals(wc2), list(wc1.bounds))


roof = native["roof:west_plane"]
rb = bounds(roof)
close("roof:west_eave_x_mm", rb[0], -G.roof_overhang)
close("roof:ridge_x_mm", rb[3], P.width/2)
close("roof:south_overhang_mm", rb[1], -G.roof_overhang)
close("roof:north_edge_mm", rb[4], P.depth+G.roof_overhang)
pitch = math.degrees(math.atan((rb[5]-G.roof_vertical_thickness-rb[2])/(rb[3]-rb[0])))
close("roof:pitch_degrees", pitch, G.roof_pitch_degrees)
for side in ("south", "north"):
    gable = native[f"roof:{side}_gable_wall"]
    close(f"roof:{side}_gable_base_mm", bounds(gable)[2], 2*P.storey_height)
    close(f"roof:{side}_gable_ridge_mm", bounds(gable)[5],
          2*P.storey_height+(P.width/2)*math.tan(math.radians(G.roof_pitch_degrees)))
    close(f"roof:{side}_gable_backing_volume_mm3", gable.volume,
          .5*P.width*(P.width/2)*math.tan(math.radians(G.roof_pitch_degrees))*(P.external_wall-setback), .1)
ceiling = native["roof:attic_ceiling_slab"]
close("roof:ceiling_backing_volume_mm3", ceiling.volume,
      (P.width-2*setback)*(P.depth-2*setback)*G.slab_thickness, .1)
close("roof:ceiling_finished_floor_datum_mm", bounds(ceiling)[5], 2*P.storey_height)


data = glb_path.read_bytes()
magic, version, total = struct.unpack_from("<4sII", data)
check("GLB:valid_container", magic == b"glTF" and version == 2 and total == len(data))
json_size, chunk_kind = struct.unpack_from("<II", data, 12)
document = json.loads(data[20:20+json_size])
nodes = document["nodes"]
mesh_nodes = [node for node in nodes if "mesh" in node]
check("GLB:all_STEP_leaf_names_retained", {node["name"] for node in mesh_nodes} == set(native), len(mesh_nodes), len(native))
check("GLB:named_groups_retained", {"house_3d", "F1", "F2", "stairs", "roof"}.issubset({n["name"] for n in nodes}))
check("GLB:all_nodes_metres_Y_up", all(n.get("extras", {}).get("cadUnits") == "m" and
                                     n.get("extras", {}).get("cadUpAxis") == "y" for n in nodes))
check("GLB:static_mesh_has_no_animation", not document.get("animations"))
check("GLB:identity_groups_world_meshes", all(not any(k in n for k in ("matrix", "translation", "rotation", "scale")) for n in nodes))
positions = [document["accessors"][primitive["attributes"]["POSITION"]]
             for mesh in document["meshes"] for primitive in mesh["primitives"]]
glb_bounds = [min(a["min"][i] for a in positions) for i in range(3)] + \
             [max(a["max"][i] for a in positions) for i in range(3)]
house_bounds = bounds(scene.resolve("#house_3d").shape())
expected_glb = [house_bounds[0]/1000, house_bounds[2]/1000, -house_bounds[4]/1000,
                house_bounds[3]/1000, house_bounds[5]/1000, -house_bounds[1]/1000]
for i, (actual, expected) in enumerate(zip(glb_bounds, expected_glb)):
    close(f"GLB:metre_Y_up_bound_{i}", actual, expected, 1e-5)
glass_nodes = [n for n in mesh_nodes if n["name"].endswith(":glass")]
glass_materials = [document["materials"][p["material"]]
                   for n in glass_nodes for p in document["meshes"][n["mesh"]]["primitives"]]
check("GLB:glazing_transparency_retained", all(m.get("alphaMode") == "BLEND" and
            m["pbrMetallicRoughness"]["baseColorFactor"][3] < 1 for m in glass_materials), len(glass_materials))
children = [child for n in nodes for child in n.get("children", [])]
scene_roots = document["scenes"][document.get("scene", 0)]["nodes"]
check("GLB:each_node_has_single_parent_or_scene_root", len(children)+len(scene_roots) == len(nodes) and
      len(set(children+scene_roots)) == len(nodes))

report = {
    "revision": "R03-3D", "units": "STEP mm; GLB metres / Y-up",
    "summary": {"checks": len(results), "passed": sum(r["pass"] for r in results),
                "failed": sum(not r["pass"] for r in results), "STEP_leaf_occurrences": len(leaves),
                "native_solids": solid_count, "GLB_mesh_nodes": len(mesh_nodes), "GLB_all_nodes": len(nodes)},
    "artifacts": {p.name: {"bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                  for p in (step_path, glb_path)},
    "thresholds": {"length_mm": 0.01, "opening_overlap_mm3": 0.01, "GLB_bound_metres": 1e-5},
    "exterior_wall_test_basis": {"approved_total_wall_thickness_mm": P.external_wall,
                                 "finish_thickness_mm": E.cladding_thickness,
                                 "visual_backing_gap_mm": E.backing_gap,
                                 "backing_thickness_mm": P.external_wall-setback,
                                 "approved_room_net_boundaries": "Unchanged; tested as exact native clear-room volumes",
                                 "finished_footprint_mm": [P.width, P.depth]},
    "not_verified": ["Structure or building regulations", "Actual stair headroom and handrail design",
                     "Door pockets and selected products", "Site conditions and permit drawings"],
    "checks": results,
}
destination = ROOT/"output"/"review"/"validation_3d.json"
destination.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps(report["summary"]))
for result in results:
    if not result["pass"]:
        print(json.dumps(result))
sys.exit(0 if all(r["pass"] for r in results) else 1)
