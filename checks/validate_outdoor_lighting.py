"""Validate actual saved R08 light solids, export metadata and retained model.

The optional pre-export snapshot is taken before adding fixtures, not generated
from the current factories. Run with --baseline tmp/lighting-r08-baseline to
prove native geometry, GLB geometry/materials and protected artifacts survive.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from math import sqrt
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))
from cadgen import build123d as bd, read_scene
from cadgen.geometry import overlap_volume
from lib.house_geometry import G, cuboid
from lib.house_plan import P, floor_plan
from lib.outdoor_lighting import outdoor_lighting_manifest
from lib.site_geometry import S, site_dimensions


def bounds(shape):
    b = shape.bounding_box()
    return [b.min.X, b.min.Y, b.min.Z, b.max.X, b.max.Y, b.max.Z]


def bbox_intersects(a, b):
    return all(a[i] < b[i+3]-1e-7 and b[i] < a[i+3]-1e-7 for i in range(3))


def overlap(a, b, ab=None, bb=None):
    if not bbox_intersects(ab or bounds(a), bb or bounds(b)):
        return 0.
    return sum(overlap_volume(sa, sb) for sa in a.solids() for sb in b.solids())


def glb_document(path):
    raw = path.read_bytes()
    magic, version, total = struct.unpack_from("<4sII", raw)
    if magic != b"glTF" or version != 2 or total != len(raw):
        raise ValueError(f"Invalid GLB: {path}")
    size, kind = struct.unpack_from("<II", raw, 12)
    if kind != 0x4E4F534A:
        raise ValueError("Expected JSON first chunk")
    document = json.loads(raw[20:20+size])
    binary_size, binary_kind = struct.unpack_from("<II", raw, 20+size)
    if binary_kind != 0x004E4942:
        raise ValueError("Expected BIN second chunk")
    return document, raw[28+size:28+size+binary_size]


def mesh_payloads(document, binary):
    components = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
    sizes = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}

    def accessor(index):
        a = document["accessors"][index]
        view = document["bufferViews"][a["bufferView"]]
        width = components[a["type"]]*sizes[a["componentType"]]
        start = view.get("byteOffset", 0)+a.get("byteOffset", 0)
        stride = view.get("byteStride", width)
        raw = b"".join(binary[start+i*stride:start+i*stride+width] for i in range(a["count"]))
        return {"count": a["count"], "type": a["type"], "componentType": a["componentType"],
                "sha256": hashlib.sha256(raw).hexdigest(), "min": a.get("min"), "max": a.get("max")}

    result = {}
    for node in document["nodes"]:
        if "mesh" not in node:
            continue
        parts = []
        for primitive in document["meshes"][node["mesh"]]["primitives"]:
            parts.append({"attributes": {k: accessor(v) for k, v in primitive["attributes"].items()},
                          "indices": accessor(primitive["indices"]) if "indices" in primitive else None,
                          "material": document["materials"][primitive["material"]],
                          "mode": primitive.get("mode", 4)})
        result[node["name"]] = parts
    return result


def native_signature(shape):
    vertices = sorted([round(v.X, 6), round(v.Y, 6), round(v.Z, 6)] for v in shape.vertices())
    return {"bounds": [round(v, 6) for v in bounds(shape)], "volume": round(shape.volume, 5),
            "vertices": vertices, "edge_lengths": sorted(round(edge.length, 5) for edge in shape.edges()),
            "face_areas": sorted(round(face.area, 4) for face in shape.faces())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    results = []

    def check(name, condition, actual=None, expected=None):
        results.append({"check": name, "pass": bool(condition), "actual": actual, "expected": expected})

    def close(name, actual, expected, tolerance=.01):
        check(name, abs(actual-expected) <= tolerance, round(actual, 6), expected)

    saved = json.loads((ROOT/"output/review/house_3d_assumptions_R01.json").read_text())
    metadata = saved["outdoor_lighting"]
    current = outdoor_lighting_manifest(P, G)
    check("manifest:parameters_and_fixture_layout_match", metadata == current)
    check("manifest:lighting_revision_matches_source", metadata["revision"] == current["revision"])
    check("manifest:seven_fixtures_four_categories", metadata["fixture_count"] == 7
          and {f["category"] for f in metadata["fixtures"]} == {"wall", "path", "garden", "gate"})
    check("manifest:engineering_results_remain_uncomputed", all(v is None for v in metadata["engineering_results"].values()))
    scene = read_scene(ROOT/"STEP/house_3d.step")
    native = {o.label: o.shape() for o in scene.leaves()}
    nb = {name: bounds(shape) for name, shape in native.items()}
    lights = {name: shape for name, shape in native.items() if name.startswith("lighting:")}
    retained = {name: shape for name, shape in native.items() if not name.startswith("lighting:")}
    # The whole-house count changes with layout revisions. Its exact contents are
    # checked by validate_3d; retain the independent fixture-count assertion here.
    check("assembly:32_lighting_leaves_in_current_house", bool(retained) and len(lights) == 32,
          len(lights), 32)
    group = scene.resolve("#lighting")
    check("assembly:four_immediate_named_categories", {q.label for q in group.children}
          == {"lighting:wall", "lighting:path", "lighting:garden", "lighting:gate"})
    document, binary = glb_document(ROOT/"GLB/house_3d.glb")
    nodes = {node["name"]: node for node in document["nodes"]}
    payloads = mesh_payloads(document, binary)
    check("GLB:named_leaves_match_STEP", set(payloads) == set(native), len(payloads), len(native))
    check("GLB:lighting_metadata_embedded", document["asset"]["extras"]["outdoorLighting"] == current)
    lot = site_dimensions(P, G)["lot"]
    for name, shape in lights.items():
        bb = nb[name]
        check(f"{name}:valid_saved_positive_solid", bool(shape.solids())
              and all(s.is_valid and s.volume > 0 for s in shape.solids()))
        check(f"{name}:inside_demo_lot", bb[0] >= lot[0] and bb[1] >= lot[1]
              and bb[3] <= lot[2] and bb[4] <= lot[3], bb, lot)
        check(f"{name}:above_grade", bb[2] >= S.ground_z-1e-4, bb[2], S.ground_z)
        geometry = payloads[name][0]["attributes"]["POSITION"]
        expected_min = [bb[0]/1000, bb[2]/1000, -bb[4]/1000]
        expected_max = [bb[3]/1000, bb[5]/1000, -bb[1]/1000]
        # Rotated CAD cylinder meshing can miss an analytic extremum by <=1mm.
        check(f"{name}:GLB_metre_Y_up_bounds", all(abs(a-b) <= .0011 for a, b in
              zip(geometry["min"]+geometry["max"], expected_min+expected_max)),
              geometry["min"]+geometry["max"], expected_min+expected_max)
        intersections = [(old_name, overlap(shape, old_shape, bb, nb[old_name]))
                         for old_name, old_shape in retained.items() if bbox_intersects(bb, nb[old_name])]
        conflicts = [(old_name, round(volume, 5)) for old_name, volume in intersections if volume > .1]
        check(f"{name}:no_retained_model_volume_collision", not conflicts, conflicts)
    for fixture in metadata["fixtures"]:
        prefix = fixture["group"]
        leaves = {name: shape for name, shape in lights.items() if name.startswith(prefix+":")}
        lens = fixture["diffuser_label"]
        check(f"{prefix}:one_saved_diffuser", lens in leaves and sum(name.endswith(":diffuser") for name in leaves) == 1)
        check(f"{prefix}:GLB_diffuser_runtime_metadata_exact", nodes[lens]["extras"]["outdoorLight"] == fixture)
        p, target, direction = fixture["light_position_mm"], fixture["target_mm"], fixture["direction_cad"]
        check(f"{prefix}:runtime_coordinate_transform", fixture["light_position_glb_m"] == [p[0]/1000, p[2]/1000, -p[1]/1000]
              and fixture["target_glb_m"] == [target[0]/1000, target[2]/1000, -target[1]/1000]
              and fixture["direction_glb"] == [direction[0], direction[2], -direction[1]])
        close(f"{prefix}:unit_light_direction", sqrt(sum(q*q for q in direction)), 1, 1e-8)
        check(f"{prefix}:warm_3000K_visual_only", fixture["color_temperature_K"] == 3000
              and 0 < fixture["visual_intensity"] <= 3 and 0 < fixture["visual_range_m"] <= 5)
        mount_name = prefix+(":mount" if fixture["category"] in ("wall", "gate") else ":base")
        close(f"{prefix}:physical_mount_contacts_saved_support", native[mount_name].distance_to(native[fixture["mount_to"]]), 0)
        if fixture["category"] in ("path", "garden"):
            close(f"{prefix}:mount_base_rests_on_grade", nb[mount_name][2], S.ground_z)
        # The light starts beyond its diffuser and leaves the fixture unobstructed.
        ray = bd.Solid.make_cylinder(1, 35, bd.Plane(origin=p, z_dir=direction))
        close(f"{prefix}:emitter_ray_leaves_own_fixture", sum(overlap(s, ray) for s in leaves.values()), 0, .1)
        for name, shape in leaves.items():
            if name != mount_name:
                close(f"{name}:assembly_physically_connected", min(shape.distance_to(other)
                      for other_name, other in leaves.items() if other_name != name), 0)
    d = site_dimensions(P, G)
    x1, y1, x2, y2 = d["path"]
    probes = {
        "entrance_path_1500mm": cuboid((x1, y1, S.ground_z+.1, x2, y2, 2200)),
        "parking_bay_2800x5000": cuboid((*d["parking_bay"][:2], S.ground_z+.1,
                                        *d["parking_bay"][2:], 2200)),
        "pedestrian_fence_opening_1800mm": cuboid((S.pedestrian_opening_west, -5400, -499,
                                                  S.pedestrian_opening_east, -5200, 2200)),
        "car_fence_opening_3000mm": cuboid((S.car_opening_west, -5400, -499,
                                          S.car_opening_east, -5200, 2200)),
    }
    door = next(q for q in floor_plan(1).doors if q.a == "outside")
    probes["actual_entrance_door_900mm"] = cuboid((door.start, -1400, -.1, door.start+door.width, 120, G.door_height))
    for name, probe in probes.items():
        close(f"clearance:{name}:saved_luminaires_leave_space_clear", sum(overlap(s, probe) for s in lights.values()), 0, .1)
    baseline_status = "not_requested"
    if args.baseline:
        baseline = args.baseline.resolve()
        previous_scene = read_scene(baseline/"house_3d.step")
        previous_native = {o.label: o.shape() for o in previous_scene.leaves()}
        previous_doc, previous_bin = glb_document(baseline/"house_3d.glb")
        previous_payloads = mesh_payloads(previous_doc, previous_bin)
        check("preservation:original_saved_leaf_labels_exact", set(previous_native) == set(retained))
        for name, previous_shape in previous_native.items():
            check(f"preservation:{name}:native_geometry_signature_exact", name in retained
                  and native_signature(previous_shape) == native_signature(retained[name]))
            check(f"preservation:{name}:GLB_geometry_and_material_payload_exact", payloads.get(name) == previous_payloads.get(name))
        previous_manifest = json.loads((baseline/"house_3d_assumptions_R01.json").read_text())
        for key in ("plan_parameters", "geometry_parameters", "exterior", "attic", "site", "structure", "furnishings"):
            check(f"preservation:manifest:{key}:unchanged", previous_manifest[key] == saved[key])
        hashes = json.loads((baseline/"protected-hashes.json").read_text())
        for relative, digest in hashes.items():
            check(f"preservation:{relative}:SHA256_unchanged", hashlib.sha256((ROOT/relative).read_bytes()).hexdigest() == digest)
        baseline_status = "independent_pre_export_snapshot"
    report = {"revision": saved["revision"], "lighting_revision": metadata["revision"], "pass": all(r["pass"] for r in results),
              "passed": sum(r["pass"] for r in results), "total": len(results),
              "baseline": baseline_status, "results": results}
    destination = ROOT/"output/review/outdoor_lighting_validation_R08.json"
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
    failures = [r for r in results if not r["pass"]]
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, ensure_ascii=False))
    for failure in failures[:30]:
        print(json.dumps(failure, ensure_ascii=False))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
