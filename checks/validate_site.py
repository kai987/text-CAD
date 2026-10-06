"""Validate the saved R11 foundation, yard and fence without rebuilding them.

Run .venv/bin/python checks/validate_site.py. An optional --baseline points to
an earlier saved snapshot and proves that its original native solids, GLB
geometry/material payloads and protected files remain unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from shapely.geometry import box
import ezdxf
from ezdxf.lldxf import const
import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cadgen import read_scene
from cadgen.geometry import overlap_volume
from lib.house_geometry import cuboid
from lib.house_geometry import G
from lib.house_plan import P, floor_plan
from lib.site_geometry import site_manifest,S

SITE_PREFIXES = ("foundation:", "yard:", "fence:")
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--baseline", type=Path)
args = parser.parse_args()
results = []


def check(name, condition, actual=None, expected=None):
    results.append({"check": name, "pass": bool(condition), "actual": actual, "expected": expected})


def close(name, actual, expected, tolerance=.01):
    check(name, abs(actual - expected) <= tolerance, round(actual, 6), expected)


def bounds(shape):
    b = shape.bounding_box()
    return [b.min.X, b.min.Y, b.min.Z, b.max.X, b.max.Y, b.max.Z]


def bounds_overlap(a, b):
    return all(a[i] < b[i + 3] - 1e-7 and b[i] < a[i + 3] - 1e-7 for i in range(3))


def overlap(a, b):
    if not bounds_overlap(bounds(a), bounds(b)):
        return 0.
    return sum(overlap_volume(sa, sb) for sa in a.solids() for sb in b.solids())


def glb_document(path):
    raw = path.read_bytes()
    magic, version, total = struct.unpack_from("<4sII", raw)
    if magic != b"glTF" or version != 2 or total != len(raw):
        raise ValueError(f"Invalid saved GLB: {path}")
    size = struct.unpack_from("<I", raw, 12)[0]
    document = json.loads(raw[20:20 + size])
    offset = 20 + size
    binary_size, _ = struct.unpack_from("<II", raw, offset)
    return document, raw[offset + 8:offset + 8 + binary_size]


def glb_payloads(document, binary):
    components = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}
    sizes = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}

    def accessor(index):
        a = document["accessors"][index]
        view = document["bufferViews"][a["bufferView"]]
        width = components[a["type"]] * sizes[a["componentType"]]
        start = view.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = view.get("byteStride", width)
        payload = b"".join(binary[start + i * stride:start + i * stride + width] for i in range(a["count"]))
        return {"type": a["type"], "componentType": a["componentType"], "count": a["count"],
                "sha256": hashlib.sha256(payload).hexdigest(), "min": a.get("min"), "max": a.get("max")}

    meshes = {}
    for node in document["nodes"]:
        if "mesh" not in node:
            continue
        primitives = []
        for primitive in document["meshes"][node["mesh"]]["primitives"]:
            material = document["materials"][primitive["material"]]
            primitives.append({
                "attributes": {key: accessor(value) for key, value in primitive["attributes"].items()},
                "indices": accessor(primitive["indices"]) if "indices" in primitive else None,
                "mode": primitive.get("mode", 4),
                "material": {"pbrMetallicRoughness": material.get("pbrMetallicRoughness"),
                             "alphaMode": material.get("alphaMode"), "doubleSided": material.get("doubleSided")},
            })
        meshes[node["name"]] = primitives
    return meshes


step_path, glb_path = ROOT / "STEP/house_3d.step", ROOT / "GLB/house_3d.glb"
scene = read_scene(step_path)
native = {o.label: o.shape() for o in scene.leaves()}
site = {label: shape for label, shape in native.items() if label.startswith(SITE_PREFIXES)}
saved = json.loads((ROOT / "output/review/house_3d_assumptions_R01.json").read_text())
record = saved["site"]
check("site:saved_metadata_matches_current_parameters", record == site_manifest(P, G))
check("revision:house_R10_with_site_R11", saved["revision"] == "R12-3D", saved["revision"], "R12-3D")
legacy = {label for label in native if not label.startswith(SITE_PREFIXES+("structure:",))
          and label != "attic:lining:flat_ceiling"}
check("R10:house_and_balcony_labels_present", all(label in legacy for label in ("F1:floor_slab","F2:floor_slab","balcony:slab","balcony:drying_rail")))
check("site:three_nonempty_top_groups", all(any(label.startswith(prefix) for label in site) for prefix in SITE_PREFIXES))
new_supports = {label: shape for label, shape in site.items() if label.startswith("foundation:internal_supports:")}
check("site:R11_site_leaf_contract", len(site)-len(new_supports) == 100, len(site)-len(new_supports), 100)
check("foundation:internal_supports_added", bool(new_supports))
for group in ("foundation:raft", "foundation:stem_walls", "foundation:existing_plinth", "foundation:entrance_supports", "foundation:internal_supports",
              "yard:soil", "yard:ground_surfaces", "yard:entrance_path", "yard:parking", "yard:planting",
              "fence:posts", "fence:panels", "fence:footings"):
    occurrence = scene.resolve(f"#{group}")
    check(f"{group}:saved_selectable_group_is_nonempty", bool(occurrence.children))

lot = [S.lot_west,S.lot_south,S.lot_east,S.lot_north]
for label, shape in site.items():
    b = bounds(shape)
    check(f"{label}:inside_demo_lot", b[0] >= lot[0] - .01 and b[1] >= lot[1] - .01
          and b[3] <= lot[2] + .01 and b[4] <= lot[3] + .01, b, lot)
    check(f"{label}:valid_positive_saved_solids", bool(shape.solids())
          and all(s.is_valid and s.volume > 0 for s in shape.solids()))

close("datum:first_floor_finished_top_mm", bounds(native["F1:floor_slab"])[5], 0)
close("datum:second_floor_finished_top_mm", bounds(native["F2:floor_slab"])[5], 2800)
close("datum:attic_finished_top_mm", bounds(native["attic:deck_finish"])[5], 5618)
close("site:minimum_saved_Z_is_fence_footing_mm", min(bounds(s)[2] for s in native.values()), -950)
for label, shape in new_supports.items():
    close(f"{label}:bottom_joins_raft_mm", bounds(shape)[2], record["foundation"]["raft_bounds_mm"][5])
    close(f"{label}:top_reaches_timber_support_datum_mm", bounds(shape)[5], -G.slab_thickness)
    close(f"{label}:physical_raft_contact_mm", shape.distance_to(native["foundation:raft:slab"]), 0)

# The new support actually joins the old perimeter instead of moving the old
# model or leaving a gap under it. Check every independently saved side.
for side in ("south", "north", "west", "east"):
    old = native[f"F1:exterior:foundation:{side}"]
    stem = native[f"foundation:stem_walls:{side}"]
    ob, sb = bounds(old), bounds(stem)
    check(f"foundation:{side}:aligned_to_existing_plinth", all(abs(ob[i] - sb[i]) <= .01 for i in (0, 1, 3, 4)))
    close(f"foundation:{side}:top_touches_existing_plinth_mm", sb[5], ob[2])
    close(f"foundation:{side}:bottom_touches_raft_mm", sb[2], bounds(native["foundation:raft:slab"])[5])
    close(f"foundation:{side}:native_connection_to_old_plinth_mm", stem.distance_to(old), 0)
    close(f"foundation:{side}:native_connection_to_raft_mm", stem.distance_to(native["foundation:raft:slab"]), 0)
for name, old_label in (("porch", "F1:D01:porch"), ("upper_step", "F1:D01:porch_step")):
    support = native[f"foundation:entrance_supports:{name}"]
    old = native[old_label]
    close(f"entrance:{name}:support_touches_retained_part_mm", support.distance_to(old), 0)
    close(f"entrance:{name}:support_top_reaches_original_bottom_mm", bounds(support)[5], bounds(old)[2])
    close(f"entrance:{name}:support_reaches_entrance_footing_mm", support.distance_to(native["foundation:raft:entrance_footing"]), 0)

path = native["yard:entrance_path:paving"]
lower_step = native["yard:entrance_path:lower_step"]
upper_step = native["F1:D01:porch_step"]
porch = native["F1:D01:porch"]
actual_levels = [bounds(path)[5], bounds(lower_step)[5], bounds(upper_step)[5], bounds(porch)[5],
                 bounds(native["F1:floor_slab"])[5]]
check("entrance:actual_saved_levels_match_record", actual_levels == record["entrance"]["levels_mm"], actual_levels)
actual_rises = [b - a for a, b in zip(actual_levels, actual_levels[1:])]
check("entrance:actual_saved_rises_match_record", actual_rises == record["entrance"]["rises_mm"], actual_rises)
for previous, following, name in ((path, lower_step, "path_to_lower_step"),
                                  (lower_step, native["foundation:entrance_supports:upper_step"],
                                   "lower_step_to_supported_upper_riser"),
                                  (upper_step, porch, "original_upper_step_to_porch")):
    close(f"entrance:{name}:native_faces_are_connected_mm", previous.distance_to(following), 0)
entrance_door = next(d for d in floor_plan(1).doors if d.a == "outside")
pb = bounds(path)
check("entrance:path_projection_covers_actual_entry_door_width", pb[0] <= entrance_door.start
      and pb[3] >= entrance_door.start + entrance_door.width)
close("entrance:path_from_lot_street_edge_mm", pb[1], lot[1])
close("entrance:path_joins_lower_step_south_edge_mm", pb[4], bounds(lower_step)[1])

soil = native["yard:soil:base"]
surface_labels = ["yard:ground_surfaces:gravel", "yard:entrance_path:paving", "yard:parking:paving"] + \
                [f"yard:planting:lawn_{name}" for name in ("north", "east", "west")]
surface_volume = 0.
for label in surface_labels:
    part = native[label]
    close(f"{label}:actual_grade_top_mm", bounds(part)[5], -500)
    close(f"{label}:actual_finish_thickness_mm", bounds(part)[5] - bounds(part)[2], 50)
    surface_volume += part.volume
close("yard:soil_actual_bottom_mm", bounds(soil)[2], -650)
close("yard:soil_actual_top_mm", bounds(soil)[5], -550)
# The gross lot, house and entrance footprint are disjoint; the counted post
# holes lie away from them. This area identity detects ground accidentally
# passing through footings, or duplicate paving/lawn meshes.
gross_area = (lot[2] - lot[0]) * (lot[3] - lot[1])
open_area = gross_area - P.width * P.depth - 1500 * 1900
close("yard:soil_area_accounts_for_full_footing_exclusions_mm2", soil.volume / 100,
      open_area - len(record["fence"]["posts"])*300*300, .1)
close("yard:finished_surfaces_tile_site_around_post_exclusions_mm2", surface_volume / 50,
      open_area - len(record["fence"]["posts"])*50*50, .1)
close("yard:recorded_soil_area_matches_saved_native_mm2", soil.volume / 100, record["surfaces"]["soil_area_mm2"], .1)
close("yard:recorded_finish_area_matches_saved_native_mm2", surface_volume / 50,
      record["surfaces"]["finish_total_area_mm2"], .1)

for post in record["fence"]["posts"]:
    name, x, y = post["id"], post["x"], post["y"]
    footing = native[f"fence:footings:{name}"]
    upright = native[f"fence:posts:{name}"]
    fb, ub = bounds(footing), bounds(upright)
    close(f"fence:{name}:post_height_above_grade_mm", ub[5] + 500, 1200)
    close(f"fence:{name}:post_embedment_below_grade_mm", -500 - ub[2], 250)
    close(f"fence:{name}:footing_width_mm", fb[3] - fb[0], 300)
    close(f"fence:{name}:footing_depth_mm", fb[4] - fb[1], 300)
    close(f"fence:{name}:footing_volume_retains_post_pocket_mm3", footing.volume, 300 * 300 * 400 - 50 * 50 * 200, .1)
    close(f"fence:{name}:post_matches_footing_center_X_mm", (ub[0] + ub[3]) / 2, (fb[0] + fb[3]) / 2)
    close(f"fence:{name}:post_matches_footing_center_Y_mm", (ub[1] + ub[4]) / 2, (fb[1] + fb[4]) / 2)
    close(f"fence:{name}:post_and_cut_footing_touch_mm", footing.distance_to(upright), 0)

fence_shapes = [s for label, s in native.items() if label.startswith("fence:")]
for label, limits in (("car", record["fence"]["car_clear_opening_mm"]),
                      ("pedestrian", record["fence"]["pedestrian_clear_opening_mm"])):
    # Stay 1 mm inside the actual declared clear faces and test the full above-
    # grade opening across the front fence line, including the post height.
    probe = cuboid((limits[0] + 1, -5400, -499, limits[1] - 1, -5200, 701))
    close(f"fence:{label}:actual_clear_opening_unobstructed_mm3", sum(overlap(s, probe) for s in fence_shapes), 0, .1)
walk_probe = cuboid((pb[0] + 1, pb[1] + 1, -499, pb[3] - 1, pb[4] - 1, 1900))
walk_obstacles = [s for label, s in native.items() if label.startswith(("fence:", "yard:planting:"))]
close("entrance:entire_1500mm_path_above_grade_clear_of_fence_and_planting_mm3",
      sum(overlap(s, walk_probe) for s in walk_obstacles), 0, .1)
for panel in record["fence"]["panels"]:
    actual = native[f"fence:panels:{panel['id']}"]
    along = (panel["start"] + panel["end"]) / 2
    x, y = (along, panel["at"]) if panel["axis"] == "h" else (panel["at"], along)
    solid_probe = cuboid((x - 5, y - 5, -385, x + 5, y + 5, -375))
    gap_probe = cuboid((x - 5, y - 5, -325, x + 5, y + 5, -315))
    close(f"fence:{panel['id']}:actual_slat_midspan_is_solid_mm3", overlap(actual, solid_probe), 1000, .1)
    close(f"fence:{panel['id']}:actual_40mm_slat_gap_remains_open_mm3", overlap(actual, gap_probe), 0, .1)

# Independent R11 parking/lot checks against the actual saved solids.
check("R11:no_saved_shrub_bodies", not any("yard:planting:shrub_" in label for label in native))
check("R11:lot_dimensions_and_area", record["lot_dimensions_mm"]==[10190,13780]
      and abs(record["lot_area_mm2"]-140418200)<.01)
check("R11:two_parallel_bays_2800_5000", record["parking"]["count"]==2
      and record["parking"]["bay_dimensions_mm"]==[2800,5000])
check("R11:four_named_wheel_stops", len([label for label in site if "wheel_stop" in label])==4)
check("R11:shared_marking_is_editable_and_clear_of_footing", "yard:parking:line_divider_1" in native
      and not any(name.startswith("balcony:footing_") for name in native))
for i,b in enumerate(record["parking"]["vehicle_envelopes_mm"],1):
    probe=cuboid((b[0],b[1],-499,b[2],b[3],1400))
    obstacles=[shape for label,shape in native.items()
               if label.startswith(("fence:","balcony:support_post_","balcony:footing_","lighting:"))]
    close(f"R11:vehicle_{i}_static_envelope_clear_mm3",sum(overlap(shape,probe)
          for shape in obstacles if bounds_overlap(bounds(shape),bounds(probe))),0,.1)
    check(f"R11:vehicle_{i}_fits_bay",box(*record["parking"]["bays_bounds_mm"][i-1]).covers(box(*b)))

dxf_path = ROOT / "DXF/house_site_plan.dxf"
doc = ezdxf.readfile(dxf_path)
check("site_DXF:millimetre_units", doc.units == 4)
check("site_DXF:clean_audit", not doc.audit().has_errors)
dimensions = list(doc.modelspace().query("DIMENSION"))
check("site_DXF:editable_dimensions", len(dimensions) >= 5, len(dimensions))
measurements = sorted(round(dimension.get_measurement(), 6) for dimension in dimensions)
check("site_DXF:actual_lot_house_and_opening_measurements", measurements == sorted([1800.,5675.,float(P.width),S.lot_east-S.lot_west,S.lot_north-S.lot_south]), measurements)
check("site_DXF:adaptive_black_white_annotation", all(entity.dxf.color in (7, 256)
      for entity in doc.modelspace().query("TEXT MTEXT DIMENSION")))
layout = doc.layouts.get("SITE_A3_1_100")
viewports = [viewport for viewport in layout.query("VIEWPORT") if viewport.dxf.id > 1]
check("site_DXF:single_locked_1_100_viewport", len(viewports) == 1
      and bool(viewports[0].dxf.flags & const.VSF_LOCK_ZOOM)
      and abs(viewports[0].dxf.view_height / viewports[0].dxf.height - 100) <= .01)
pdf = fitz.open(ROOT / "output/pdf/house_site_plan_R05_JP.pdf")
check("site_PDF:one_A3_landscape_page", len(pdf) == 1 and abs(pdf[0].rect.width - 420 * 72 / 25.4) < .01
      and abs(pdf[0].rect.height - 297 * 72 / 25.4) < .01)
pdf_text = "\n".join(page.get_text() for page in pdf)
check("site_PDF:site_entry_and_concept_scope_legends", all(label in pdf_text for label in
      ("外構・基礎", "車両開口", "歩行開口", "外部地盤", "施工図", "1:100", "1:25")))

# Actual saved intersections, not comparisons against the same shape factories.
# Broad-phase bounds keep these independent native boolean checks inexpensive.
site_items = sorted(site.items())
for index, (label, shape) in enumerate(site_items):
    for other_label, other in site_items[index + 1:]:
        if bounds_overlap(bounds(shape), bounds(other)):
            close(f"{label}:{other_label}:no_positive_native_overlap_mm3", overlap(shape, other), 0, .1)
    for other_label, other in native.items():
        if not other_label.startswith(SITE_PREFIXES) and bounds_overlap(bounds(shape), bounds(other)):
            close(f"{label}:{other_label}:clear_of_R04_solid_mm3", overlap(shape, other), 0, .1)

# Baseline checking is opt-in so the ordinary verifier stays portable. During a
# release it additionally proves every old shape, not merely old leaf counts.
if args.baseline:
    baseline = json.loads(args.baseline.read_text())
    original = {o.label: o.shape() for o in read_scene(baseline["saved_originals"]["STEP"]).leaves()}
    document, binary = glb_document(glb_path)
    payloads = glb_payloads(document, binary)
    for index, original_image in enumerate(baseline.get("glb_images", [])):
        image = document["images"][index]
        view = document["bufferViews"][image["bufferView"]]
        start = view.get("byteOffset", 0)
        payload = binary[start:start + view["byteLength"]]
        check(f"GLB:original_embedded_texture_{index}_unchanged", {
            "mimeType": image.get("mimeType"), "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload)} == original_image)
    original_textures = baseline.get("glb_textures", [])
    check("GLB:original_texture_references_retained", document.get("textures", [])[:len(original_textures)] == original_textures)
    for label, shape in original.items():
        check(f"{label}:R04_original_leaf_retained", label in native)
        if label not in native:
            continue
        delta = max(0., shape.volume + native[label].volume - 2 * overlap(shape, native[label]))
        close(f"{label}:R04_native_symmetric_difference_mm3", delta, 0, .1)
        check(f"{label}:R04_GLB_payload_and_material_unchanged",
              payloads.get(label) == baseline["glb_leaf_payloads"][label])
    for path, metadata in baseline["protected_paths"].items():
        target = ROOT / path
        check(f"{path}:protected_file_unchanged", target.is_file()
              and hashlib.sha256(target.read_bytes()).hexdigest() == metadata["sha256"])

report = {
    "revision": "R12-3D", "units": "native STEP mm; GLB m/Y-up",
    "summary": {"checks": len(results), "passed": sum(r["pass"] for r in results),
                "failed": sum(not r["pass"] for r in results), "saved_native_leaves": len(native),
                "new_site_leaves": len(site)},
    "baseline": str(args.baseline) if args.baseline else None,
    "scope": "Concept geometry, labelled hierarchy, circulation and unchanged prior geometry only",
    "not_verified": ["Ground bearing capacity and reinforcement", "Actual setback or site survey",
                     "Fence product installation and wind loads", "Regulatory or permit compliance"],
    "checks": results,
}
(ROOT / "output/review/validation_site_R05.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(report["summary"]))
for row in results:
    if not row["pass"]:
        print(json.dumps(row))
sys.exit(0 if all(row["pass"] for row in results) else 1)
