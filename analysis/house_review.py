"""Read-only, source-bound space/relationship review and elastic beam calculator.

This companion tool does not edit CAD, choose engineering loads/materials, or
determine structural capacity, statutory floor area or regulatory compliance.
"""
from __future__ import annotations

import argparse
import copy
from collections import deque
import hashlib
import json
import math
from pathlib import Path
import sys

from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cad_release import verify  # noqa: E402

SOURCE_PATHS = (
    "output/review/design_manifest.json",
    "output/review/engineering_inputs_R06.json",
    "output/review/house_3d_assumptions_R01.json",
)
KNOWN_ROOMS = {"ldk", "foyer", "bath", "wash", "wc", "stairs", "under_stairs",
               "master", "bed2", "bed3", "hall", "balcony"}
VALUES = ("span_mm", "uniform_load_kN_m", "point_load_kN", "E_N_mm2",
          "I_mm4", "W_mm3", "allowable_bending_N_mm2", "deflection_limit_mm")
REQUIRED = VALUES[:6]
GLOBAL_PENDING = [
    "gravity/wind/snow/seismic combinations and actual tributary load paths",
    "wall resistance/distribution/torsion, diaphragm and storey drift",
    "column stability, shear, vibration and long-term deformation",
    "joints, anchorage, uplift, balcony backspan and connection rotation",
    "attic hatch reinforcement and concentrated storage/support loads",
    "foundation reactions, soil bearing/settlement and reinforcement",
    "fire, site/road/zoning and statutory floor/storey classification",
]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def number(value, name, *, zero_ok=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name}: expected a finite number")
    if not math.isfinite(value) or (value < 0 if zero_ok else value <= 0):
        raise ValueError(f"{name}: expected {'nonnegative' if zero_ok else 'positive'} finite number")
    return float(value)


def elastic_beam(values, support):
    """Small-deflection Euler-Bernoulli beam; one downward full-span UDL.

    Optional point load is at midspan for simple supports, at the free end for
    a cantilever. Prismatic constant E/I; no shear deformation, creep, torsion,
    instability, composite action or connection flexibility. 1 kN/m = 1 N/mm.
    These are elastic demands; this function never returns an overall pass.
    """
    if support not in {"simple", "cantilever"}:
        raise ValueError("support must be simple or cantilever")
    v = {k: number(values[k], k, zero_ok=k in REQUIRED[1:3]) for k in REQUIRED}
    L, w, P = v["span_mm"], v["uniform_load_kN_m"], v["point_load_kN"] * 1000
    EI = v["E_N_mm2"] * v["I_mm4"]
    if not math.isfinite(EI) or EI <= 0:
        raise ValueError("Nonfinite or zero flexural stiffness: check E/I units and magnitudes")
    if support == "simple":
        moment = w * L**2 / 8 + P * L / 4
        shear = (w * L + P) / 2
        deflection = 5 * w * L**4 / (384 * EI) + P * L**3 / (48 * EI)
        reactions = {"left_kN": shear / 1000, "right_kN": shear / 1000}
    else:
        moment = w * L**2 / 2 + P * L
        shear = w * L + P
        deflection = w * L**4 / (8 * EI) + P * L**3 / (3 * EI)
        reactions = {"fixed_vertical_kN": shear / 1000,
                     "fixed_moment_kN_m_magnitude": moment / 1e6}
    result = {"max_moment_kN_m_magnitude": moment / 1e6,
              "max_shear_kN_magnitude": shear / 1000,
              "max_deflection_mm_magnitude": deflection,
              "elastic_bending_stress_N_mm2": moment / v["W_mm3"],
              "reactions": reactions}
    if not all(math.isfinite(result[k]) for k in result if k != "reactions"):
        raise ValueError("Nonfinite result: check units and magnitudes")
    comparisons = {}
    for limit, demand in (("allowable_bending_N_mm2", "elastic_bending_stress_N_mm2"),
                          ("deflection_limit_mm", "max_deflection_mm_magnitude")):
        if values.get(limit) is not None:
            ratio = result[demand] / number(values[limit], limit)
            comparisons[limit] = {"demand_to_user_limit": ratio, "exceeds_user_limit": ratio > 1}
    result["user_limit_comparisons"] = comparisons
    result["structural_capacity_result"] = None
    return result


def assess_case(case):
    if case.get("system") not in {"W", "S", "RC"}:
        raise ValueError("case.system must be W, S or RC")
    if case.get("support") not in {"simple", "cantilever"}:
        raise ValueError("Unsupported support model")
    values = case["values"]
    if set(values) != set(VALUES):
        raise ValueError("Unexpected or missing input keys; use the generated template")
    for k, v in values.items():
        if v is not None:
            number(v, k, zero_ok=k in REQUIRED[1:3])
    if type(case.get("assumptions_reviewed")) is not bool:
        raise ValueError("assumptions_reviewed must be boolean")
    missing = [k for k in REQUIRED if values[k] is None]
    for k in ("load_and_material_reference", "support_and_member_reference"):
        if not isinstance(case.get(k), str) or not case[k].strip():
            missing.append(k)
    if not case["assumptions_reviewed"]:
        missing.append("assumptions_reviewed")
    result = {"id": case["id"], "system": case["system"], "support": case["support"],
              "missing_inputs": missing, "input": copy.deepcopy(case),
              "elastic_demand": None, "structural_capacity_result": None}
    if case["system"] == "RC":
        result["status"] = "specialist_RC_model_required"
    elif missing:
        result["status"] = "awaiting_inputs"
    else:
        result["status"] = "elastic_demand_only"
        result["elastic_demand"] = elastic_beam(values, case["support"])
    return result


def space_review(plan, model):
    if plan.get("units") != "mm":
        raise ValueError("Plan units must be mm")
    p = plan["parameters"]
    w, d = number(p["width"], "width"), number(p["depth"], "depth")
    outline, results, living = box(0, 0, w, d), [], 0
    if {f["floor"] for f in plan["floors"]} != {1, 2} or len(plan["floors"]) != 2:
        raise ValueError("This review requires exactly two distinct floors")
    for floor in sorted(plan["floors"], key=lambda f: f["floor"]):
        shapes, rooms, outside = [], [], []
        ids = set()
        for room in floor["rooms"]:
            rid = room["id"]
            if rid not in KNOWN_ROOMS or rid in ids:
                raise ValueError(f"Unknown/duplicate room classification: {rid}")
            ids.add(rid)
            coordinates = room["polygon_mm"]
            for point in coordinates:
                if len(point) != 2 or any(isinstance(x, bool) or not isinstance(x, (float, int)) or
                                           not math.isfinite(x) for x in point):
                    raise ValueError(f"Invalid room coordinates: {rid}")
            shape = Polygon(coordinates)
            if not shape.is_valid or shape.is_empty or shape.area <= 0:
                raise ValueError(f"Invalid polygon: {rid}")
            area = shape.area / 1e6
            if abs(area - number(room["area_m2"], rid)) > 0.000001:
                raise ValueError(f"Room area disagrees with polygon: {rid}")
            item = {"id": rid, "name": room["name"], "polygon_area_m2": area}
            if rid == "balcony":
                outside.append(item)
                continue
            if not outline.buffer(0.000001).covers(shape):
                raise ValueError(f"Room outside building: {rid}")
            shapes.append(shape)
            rooms.append(item)
            if rid in {"ldk", "master", "bed2", "bed3"}:
                living += area
        union_area = unary_union(shapes).area / 1e6
        overlap = sum(r["polygon_area_m2"] for r in rooms) - union_area
        if overlap > 0.000001:
            raise ValueError(f"Floor {floor['floor']} has overlapping room areas: {overlap}")
        gross = outline.area / 1e6
        if abs(gross - number(floor["outline_area_m2"], "outline_area_m2")) > 0.000001:
            raise ValueError("Outline area disagrees with geometry")
        stairs = sum(r["polygon_area_m2"] for r in rooms if r["id"] == "stairs")
        results.append({"floor": floor["floor"], "outline_projection_m2": gross,
                        "assigned_indoor_projection_m2": union_area,
                        "stairs_projection_m2": stairs,
                        "assigned_excluding_stairs_m2": union_area - stairs,
                        "assigned_ratio_percent": 100 * union_area / gross,
                        "excluding_stairs_ratio_percent": 100 * (union_area - stairs) / gross,
                        "unassigned_outline_projection_m2": gross - union_area,
                        "rooms": rooms, "external_rooms_excluded": outside})
    gross = sum(f["outline_projection_m2"] for f in results)
    indoor = sum(f["assigned_indoor_projection_m2"] for f in results)
    stairs = sum(f["stairs_projection_m2"] for f in results)
    attic = model["attic"]
    deck, hatch = attic["deck_bounds_mm"], attic["hatch_bounds_mm"]
    for bounds in [deck, hatch]:
        if len(bounds) != 6 or not all(isinstance(x, (int, float)) and not isinstance(x, bool)
                                        and math.isfinite(x) for x in bounds):
            raise ValueError("Invalid attic bounds")
        if bounds[3] <= bounds[0] or bounds[4] <= bounds[1]:
            raise ValueError("Attic bounds must have positive width and depth")
    deck_shape = box(deck[0], deck[1], deck[3], deck[4])
    hatch_shape = box(hatch[0], hatch[1], hatch[3], hatch[4])
    attic_area = deck_shape.difference(hatch_shape).area / 1e6
    if abs(attic_area - attic["storage_projection_area_m2"]) > 0.000001:
        raise ValueError("Attic projection disagrees with deck/hatch")
    return {"basis": "Room polygon union / exterior-outline projection; millimetres squared / 1e6",
            "floors": results,
            "combined": {"outline_projection_m2": gross, "assigned_indoor_projection_m2": indoor,
                         "stairs_projection_m2": stairs, "assigned_excluding_stairs_m2": indoor - stairs,
                         "assigned_ratio_percent": 100 * indoor / gross,
                         "excluding_stairs_ratio_percent": 100 * (indoor - stairs) / gross,
                         "ldk_and_bedrooms_m2": living},
            "attic_separate": {"storage_projection_m2": attic_area,
                               "maximum_clear_height_mm": attic["clear_height_mm"]["maximum"]},
            "statutory_floor_area_m2": None, "walkable_unobstructed_area_m2": None,
            "limitations": ["Not statutory wall-centre floor area; attic/balcony excluded from two-floor totals",
                            "Stairs include projected stairwell/opening; not all solid walkable floor",
                            "Furniture, fixtures, low clearances and door operating space are not deducted",
                            "Unassigned remainder includes wall strips/thresholds/gaps; not a wall-only area",
                            "No efficiency grade or W/S/RC net-area equivalence is inferred"]}


def projected_bounds(bounds, name, dimensions=4):
    """Validate saved axis-aligned bounds without treating them as a solid."""
    if not isinstance(bounds, (list, tuple)) or len(bounds) != dimensions or any(
        isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x)
        for x in bounds
    ):
        raise ValueError(f"Invalid {name} bounds")
    end = dimensions // 2
    if any(bounds[i + end] <= bounds[i] for i in range(end)):
        raise ValueError(f"Nonpositive {name} bounds")
    return box(bounds[0], bounds[1], bounds[end], bounds[end + 1])


def line_parts(geometry):
    if geometry.geom_type == "LineString":
        return [geometry] if geometry.length > 1e-6 else []
    return [part for child in getattr(geometry, "geoms", ()) for part in line_parts(child)]


def polygon_parts(geometry):
    if geometry.geom_type == "Polygon":
        return [geometry]
    return [part for child in getattr(geometry, "geoms", ()) for part in polygon_parts(child)]


def circulation_review(plan, model):
    """Measure saved plan relationships; do not infer usable width or egress.

    Door side lines are 2 mm beyond the assumed wall face, consistent with the
    existing CAD topology check. Furniture records are rectangular envelopes,
    not precise solids. No normative minimum width is introduced here.
    """
    if plan.get("units") != "mm" or model.get("units") != "mm":
        raise ValueError("Circulation source units must be mm")
    p = plan["parameters"]
    outline = box(0, 0, number(p["width"], "width"), number(p["depth"], "depth"))
    external = number(p["external_wall"], "external_wall")
    internal = number(p["internal_wall"], "internal_wall")
    floors, floor_shapes, conflicts = [], {}, []
    furniture = {1: [], 2: []}
    furnishing_floors = set()
    for group in model["furnishings"]:
        if group.get("model") != "house" or group.get("units") != "mm" or \
                group.get("floor") not in furniture or group["floor"] in furnishing_floors:
            raise ValueError("Unexpected furniture model, floor or units")
        furnishing_floors.add(group["floor"])
        for obj in group["objects"]:
            shape = projected_bounds(obj["footprint_mm"], "furniture")
            furniture[group["floor"]].append((obj, shape))
    if furnishing_floors != {1, 2}:
        raise ValueError("Missing saved furniture envelope group for a floor")
    for floor in sorted(plan["floors"], key=lambda f: f["floor"]):
        n = floor["floor"]
        if n not in furniture or n in floor_shapes:
            raise ValueError("Circulation requires distinct floors 1 and 2")
        rooms = {r["id"]: Polygon(r["polygon_mm"]) for r in floor["rooms"]}
        if len(rooms) != len(floor["rooms"]) or any(not s.is_valid or s.is_empty for s in rooms.values()):
            raise ValueError("Invalid or duplicate circulation room polygons")
        floor_shapes[n] = rooms
        graph = {rid: set() for rid in rooms}
        graph["outside"] = set()
        portals, ids, furniture_containment = [], set(), []
        object_ids = set()
        for obj, shape in furniture[n]:
            key = (obj["room"], obj["id"])
            if key in object_ids or obj["room"] not in rooms:
                raise ValueError("Unknown room or duplicate furniture identity")
            object_ids.add(key)
            outside_area = shape.difference(rooms[obj["room"]]).area
            item = {"id": obj["id"], "room": obj["room"],
                    "envelope_outside_assigned_room_mm2": outside_area}
            furniture_containment.append(item)
            if outside_area > .01:
                conflicts.append({"id": f"F{n}/furniture/{obj['room']}/{obj['id']}",
                                  "kind": "envelope_outside_assigned_room", "evidence": item})
        for door in floor["doors"]:
            did, a, b, axis = door["id"], door["a"], door["b"], door["axis"]
            if did in ids or a not in graph or b not in graph or a == b or axis not in {"h", "v"}:
                raise ValueError("Invalid/duplicate door identity, rooms or axis")
            ids.add(did)
            width = number(door["width"], f"{did}.width")
            start, at = door["start"], door["at"]
            if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x)
                   for x in (start, at)):
                raise ValueError(f"Invalid door coordinates: {did}")
            thickness = external if {a, b} & {"outside", "balcony"} else internal
            sides = []
            for sign in (-1, 1):
                coordinate = at + sign * (thickness / 2 + 2)
                segment = LineString([(start, coordinate), (start + width, coordinate)]) if axis == "h" else \
                    LineString([(coordinate, start), (coordinate, start + width)])
                coverage = {rid: segment.intersection(shape).length for rid, shape in rooms.items()}
                coverage = {rid: length for rid, length in coverage.items() if length > 1e-6}
                if not coverage and segment.disjoint(outline):
                    coverage["outside"] = width
                owners = sorted(rid for rid, length in coverage.items() if abs(length - width) < 1e-6)
                sides.append({"normal_sign": sign, "full_width_owners": owners,
                              "room_coverage_mm": coverage})
            adjacent = all(len(side["full_width_owners"]) == 1 for side in sides) and \
                sorted(side["full_width_owners"][0] for side in sides) == sorted([a, b])
            opening = box(start, at-thickness/2, start+width, at+thickness/2) if axis == "h" else \
                box(at-thickness/2, start, at+thickness/2, start+width)
            overlaps = [{"id": obj["id"], "room": obj["room"],
                         "envelope_overlap_mm2": opening.intersection(shape).area}
                        for obj, shape in furniture[n] if opening.intersection(shape).area > .01]
            item = {"id": did, "declared_rooms": [a, b], "kind": door["kind"],
                    "nominal_aperture_width_mm": width, "sides": sides,
                    "full_width_room_adjacency": adjacent,
                    "furniture_envelope_overlaps": overlaps}
            portals.append(item)
            if not adjacent:
                conflicts.append({"id": f"F{n}/{did}", "kind": "door_room_adjacency", "evidence": item})
            else:
                graph[a].add(b)
                graph[b].add(a)
            if overlaps:
                conflicts.append({"id": f"F{n}/{did}", "kind": "door_furniture_envelope_overlap",
                                  "evidence": overlaps})
        origin = "outside" if n == 1 else "stairs"
        if origin not in graph:
            raise ValueError("Missing floor circulation origin")
        paths, queue = {origin: [origin]}, deque([origin])
        while queue:
            parent = queue.popleft()
            for target in sorted(graph[parent]):
                if target not in paths:
                    paths[target] = paths[parent] + [target]
                    queue.append(target)
        unreachable = sorted(set(rooms) - set(paths))
        if unreachable:
            conflicts.append({"id": f"F{n}/room_graph", "kind": "unreachable_room",
                              "evidence": {"origin": origin, "rooms": unreachable}})
        floors.append({"floor": n, "origin": origin, "doors": portals,
                       "room_paths": {rid: paths[rid] for rid in sorted(rooms) if rid in paths},
                       "unreachable_rooms": unreachable,
                       "furniture_envelopes_examined": len(furniture[n]),
                       "furniture_envelope_containment": furniture_containment})
    if set(floor_shapes) != {1, 2}:
        raise ValueError("Circulation requires both floors")
    vertical = {}
    for rid in ("stairs", "wc"):
        if any(rid not in rooms for rooms in floor_shapes.values()):
            raise ValueError(f"Missing vertical coordination room: {rid}")
        lower, upper = floor_shapes[1][rid], floor_shapes[2][rid]
        vertical[rid] = {"lower_projection_outside_upper_mm2": lower.difference(upper).area,
                         "upper_projection_outside_lower_mm2": upper.difference(lower).area,
                         "projection_bounds_equal": lower.bounds == upper.bounds}
        # F1 under-stair storage intentionally removes part of the stair room.
        if lower.difference(upper).area > .01 or (rid == "wc" and upper.difference(lower).area > .01):
            conflicts.append({"id": f"vertical/{rid}", "kind": "projection_misalignment",
                              "evidence": vertical[rid]})
    attic, hall = model["attic"], floor_shapes[2]["hall"]
    deck = projected_bounds(attic["deck_bounds_mm"], "attic deck", 6)
    hatch = projected_bounds(attic["hatch_bounds_mm"], "attic hatch", 6)
    ladder = attic["ladder"]
    deployed = projected_bounds(ladder["deployed_plan_bounds_mm"], "deployed ladder")
    bottom = projected_bounds(ladder["bottom_landing_bounds_mm"], "ladder bottom landing")
    upper = projected_bounds(ladder["upper_landing_bounds_mm"], "ladder upper landing")
    access = {"hatch_outside_deck_mm2": hatch.difference(deck).area,
              "hatch_outside_F2_hall_mm2": hatch.difference(hall).area,
              "deployed_ladder_outside_F2_hall_mm2": deployed.difference(hall).area,
              "bottom_landing_outside_F2_hall_mm2": bottom.difference(hall).area,
              "upper_landing_outside_attic_deck_mm2": upper.difference(deck.difference(hatch)).area}
    for name, area in access.items():
        if area > .01:
            conflicts.append({"id": f"attic/{name}", "kind": "access_projection_outside_assigned_space",
                              "evidence": {"outside_area_mm2": area}})
    occupied = unary_union([deployed, bottom])
    free_hall = hall.difference(occupied)
    # Scan every rectilinear x interval in the saved hall and operation envelope.
    # Report each interval, rather than claiming a global route clearance.
    xs = sorted({x for shape in polygon_parts(hall) + polygon_parts(occupied)
                 for x, _ in shape.exterior.coords})
    scans = []
    for left, right in zip(xs, xs[1:]):
        x = (left + right) / 2
        line = LineString([(x, -1), (x, p["depth"]+1)])
        if occupied.intersection(line).length <= 1e-6:
            continue
        parts = sorted(line_parts(free_hall.intersection(line)), key=lambda s: s.bounds[1])
        scans.append({"x_interval_mm": [left, right], "station_x_mm": x,
                      "remaining_y_spans_mm": [[s.bounds[1], s.bounds[3]] for s in parts],
                      "remaining_span_lengths_mm": [s.length for s in parts]})
    access.update({"deployed_operation_occupied_hall_projection_m2": hall.intersection(occupied).area / 1e6,
                   "deployed_hall_vertical_cross_sections": scans,
                   "simultaneous_hall_passage_result": None,
                   "headroom_and_ladder_product_safety_result": None})
    return {"status": "geometry_relationship_review", "units": "mm",
            "door_probe_offset_beyond_wall_face_mm": 2,
            "floors": floors, "vertical_coordination": vertical, "attic_access": access,
            "conflicts": conflicts, "statutory_egress_result": None,
            "pending": ["Actual frame clear width, handles, leaf movement and pocket construction",
                        "Continuous occupied-room routes and all fixed kitchen/bathroom/storage equipment",
                        "Deployed attic ladder occupies the hall; simultaneous passage and safe operation require design review",
                        "Stair/hatch headroom, guarding, product selection and structural support",
                        "Site-specific accessibility, fire and evacuation requirements"],
            "limitations": ["Room paths are a door-adjacency graph, not collision-free walking paths",
                            "Furniture checks use saved rectangular envelopes; empty parts of corner sofas and space below tables remain included",
                            "Cross sections are local vertical line measurements, not minimum route width or a clearance approval",
                            "Projection coordination does not prove pipe routing or a continuous structural/load path"]}


def load_sources(root=ROOT):
    verify(root)  # Refuse stale CAD; never update its provenance.
    data = [json.loads((root / p).read_text()) for p in SOURCE_PATHS]
    plan, engineering, model = data
    if plan["revision"] != engineering["revision"] or plan["revision"] != model["attic"]["revision"]:
        raise ValueError("Mixed source revisions")
    if model["plan_parameters"] != plan["parameters"]:
        raise ValueError("Model and plan parameter mismatch")
    binding = {"revision": plan["revision"],
               "source_sha256": {p: digest(root / p) for p in SOURCE_PATHS}}
    return data, binding


def input_template(engineering, binding):
    cases = []
    for cid, support in (("ldk_transfer_beam", "simple"), ("balcony_candidate", "cantilever"),
                         ("attic_joist_or_header", "simple")):
        cases.append({"id": cid, "system": "W", "support": support,
                      "assumptions_reviewed": False, "load_and_material_reference": None,
                      "support_and_member_reference": None, "values": dict.fromkeys(VALUES)})
    return {"schema_version": 1, "source_binding": binding,
            "scope": "Unfilled engineering handoff; demonstration geometry is not engineering input",
            "site_inputs": copy.deepcopy(engineering["site_inputs"]),
            "material_inputs": copy.deepcopy(engineering["material_inputs"]),
            "load_inputs": copy.deepcopy(engineering["load_inputs"]),
            "system_specific_inputs": {
                "W": dict.fromkeys(["species_grade_design_values", "wall_and_connector_capacities", "creep_and_duration"]),
                "S": dict.fromkeys(["steel_grade_sections", "local_and_global_buckling", "connection_design"]),
                "RC": dict.fromkeys(["concrete_rebar_design_values", "reinforcement_and_cover", "cracked_stiffness_and_creep"])},
            "member_cases": cases}


def build_report(data, binding, inputs):
    if inputs.get("schema_version") != 1 or inputs.get("source_binding") != binding:
        raise ValueError("Input template is stale or from another model; review a fresh template")
    plan, engineering, model = data
    gaps = []
    for group in ("site_inputs", "material_inputs", "load_inputs"):
        supplied = inputs.get(group, {})
        if set(supplied) != set(engineering[group]):
            raise ValueError(f"Unexpected keys in {group}")
        gaps.extend(f"{group}.{k}" for k, v in supplied.items() if v is None or v == "")
    cases = inputs["member_cases"]
    if not isinstance(cases, list) or not cases or any(
        not isinstance(c.get("id"), str) or not c["id"].strip() for c in cases
    ) or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Expected distinct nonempty member cases")
    system_template = input_template(engineering, binding)["system_specific_inputs"]
    systems = inputs.get("system_specific_inputs", {})
    if set(systems) != set(system_template) or any(
        set(systems[k]) != set(system_template[k]) for k in system_template
    ):
        raise ValueError("Unexpected system-specific input keys")
    system_gaps = {system: [k for k, v in supplied.items() if v is None or v == ""]
                   for system, supplied in systems.items()}
    return {"schema_version": 1, "source_binding": binding,
            "analysis_code_sha256": digest(Path(__file__)),
            "input_sha256": hashlib.sha256(json.dumps(inputs, sort_keys=True, allow_nan=False).encode()).hexdigest(),
            "status": "concept_review_only", "structural_capacity_result": None,
            "statutory_compliance_result": None, "missing_engineering_inputs": gaps,
            "engineering_inputs": {k: copy.deepcopy(inputs[k]) for k in
                                   ("site_inputs", "material_inputs", "load_inputs")},
            "system_specific_missing_inputs": system_gaps,
            "system_specific_inputs": inputs["system_specific_inputs"],
            "pending_global_checks": GLOBAL_PENDING,
            "member_cases": [assess_case(c) for c in cases], "space": space_review(plan, model),
            "circulation": circulation_review(plan, model)}


def markdown(report):
    space = report["space"]
    c = space["combined"]
    lines = [f"# {report['source_binding']['revision']} 承重输入与空间利用率分析", "",
             "这是演示方案的计算准备与几何统计。整体承重、基础承载和法规合规均未判定。", "",
             "## 空间面积", "",
             "全部毫米尺寸为演示假设。面积按房间多边形并集重算，分母为建筑外轮廓投影。", "",
             "| 楼层 | 外轮廓投影㎡ | 室内分配投影㎡ | 排除楼梯区㎡ | 排除楼梯比例 |",
             "| --- | ---: | ---: | ---: | ---: |"]
    for f in space["floors"]:
        lines.append(f"| {f['floor']}F | {f['outline_projection_m2']:.4f} | {f['assigned_indoor_projection_m2']:.4f} | {f['assigned_excluding_stairs_m2']:.4f} | {f['excluding_stairs_ratio_percent']:.2f}% |")
    lines += [f"| 合计 | {c['outline_projection_m2']:.4f} | {c['assigned_indoor_projection_m2']:.4f} | {c['assigned_excluding_stairs_m2']:.4f} | {c['excluding_stairs_ratio_percent']:.2f}% |", "",
              f"包含楼梯投影的分配比例为 **{c['assigned_ratio_percent']:.2f}%**。LDK及三卧室合计 **{c['ldk_and_bedrooms_m2']:.4f}㎡**。", "",
              f"阁楼储物板面另计 **{space['attic_separate']['storage_projection_m2']:.4f}㎡**，扣除检修口；最高净高 **{space['attic_separate']['maximum_clear_height_mm']} mm**，不加入两层分母或分子。二层阳台也单列排除。", "",
              "这些指标不是法定延床面积，也不是扣除家具的自由通行面积。楼梯区包含楼梯洞口投影；外轮廓余量包含墙带、门槛和间隙。尚未给出效率优劣等级。", ""]
    for f in space["floors"]:
        lines += [f"### {f['floor']}F 房间", "", "| 房间 | 净分配投影㎡ |", "| --- | ---: |"]
        lines += [f"| {r['name']} | {r['polygon_area_m2']:.4f} |" for r in f["rooms"]]
        lines += [f"| {r['name']}（室外，排除） | {r['polygon_area_m2']:.4f} |" for r in f["external_rooms_excluded"]]
        lines += [""]
    circulation = report["circulation"]
    lines += ["## 门、房间与阁楼入口关系", "",
              "读取保存后的CAD清单，沿每个名义洞口的全宽测量墙面外2 mm处的房间覆盖。关联图只表示房间之间存在对应洞口，不代表无障碍通行、门扇操作或疏散合格。门宽未扣除实际门框、把手及安装间隙。", "",
              "| 楼层 | 洞口 | 关联房间 | 名义宽mm | 全宽对应关系 | 家具包络重叠数 |",
              "| --- | --- | --- | ---: | --- | ---: |"]
    for floor in circulation["floors"]:
        for door in floor["doors"]:
            relation = "对应" if door["full_width_room_adjacency"] else "冲突"
            lines.append(f"| {floor['floor']}F | {door['id']} | {' ↔ '.join(door['declared_rooms'])} | {door['nominal_aperture_width_mm']:g} | {relation} | {len(door['furniture_envelope_overlaps'])} |")
    lines += ["", "房间关联路径：", ""]
    for floor in circulation["floors"]:
        for rid, path in floor["room_paths"].items():
            lines.append(f"- {floor['floor']}F {rid}：{' → '.join(path)}")
        if floor["unreachable_rooms"]:
            lines.append(f"- {floor['floor']}F 无关联路径：{', '.join(floor['unreachable_rooms'])}")
    access = circulation["attic_access"]
    lines += ["", f"检修梯展开包络与底端站位合计占用二层走廊投影 **{access['deployed_operation_occupied_hall_projection_m2']:.4f}㎡**。以下为占用区域各X区间中点的局部南北向截线，不是连续绕行路径的最小净宽：", "",
              "| X区间mm | 剩余南北向线段长度mm |", "| --- | --- |"]
    for scan in access["deployed_hall_vertical_cross_sections"]:
        lengths = " / ".join(f"{length:.2f}" for length in scan["remaining_span_lengths_mm"]) or "无"
        lines.append(f"| {scan['x_interval_mm'][0]:.2f}–{scan['x_interval_mm'][1]:.2f} | {lengths} |")
    lines += ["", "展开期间的同时通行、上下口净高和选定产品安全操作仍待核定。不能因房间关联图连通或局部余留投影存在，就认定检修梯展开时可安全绕行。", "",
              f"几何关系冲突记录 **{len(circulation['conflicts'])} 项**。阁楼口/上下站位范围、楼梯和厕所的跨层投影差值、每扇门两侧的实际覆盖长度保留在JSON。", ""]
    if circulation["conflicts"]:
        lines += ["```json", json.dumps(circulation["conflicts"], ensure_ascii=False, indent=2), "```", ""]
    lines += ["家具检查采用保存的矩形包络，转角沙发内空及桌下空间也包含在包络中；尚未计入全部厨房、浴室、收纳固定设备，也未模拟门扇开合、人体通行或高度。投影对齐不能证明设备管线、结构支承或传力连续。", ""]
    lines += ["## 承重计算准备", "", f"未填写工程资料 **{len(report['missing_engineering_inputs'])} 项**。", "",
              "| 部位 | 候选简化模型 | 输入状态 |", "| --- | --- | --- |"]
    for case in report["member_cases"]:
        lines.append(f"| {case['id']} | {case['system']} / {case['support']} | {case['status']} |")
    for case in report["member_cases"]:
        demand = case["elastic_demand"]
        if demand:
            lines += ["", f"### {case['id']} 的理想单梁弹性需求", "",
                      f"弯矩 {demand['max_moment_kN_m_magnitude']:.4f} kN·m；剪力 {demand['max_shear_kN_magnitude']:.4f} kN；挠度 {demand['max_deflection_mm_magnitude']:.4f} mm；弯曲应力 {demand['elastic_bending_stress_N_mm2']:.4f} N/mm²。", "",
                      "限值比较仅对用户输入的弯曲应力与挠度限值，整体承载仍未判定：", "",
                      "```json", json.dumps(demand["user_limit_comparisons"], ensure_ascii=False, indent=2), "```"]
    lines += ["", "JSON保留每项缺失输入、原始输入、源文件SHA-256和计算程序SHA-256。每个部位必须重新确认构件、实际支承、有效跨距、分担荷载和材料参数；候选简支/悬臂类型也须复核。", "",
              "工具只支持等截面小挠度弹性梁：全跨向下均布荷载，加简支梁跨中或悬臂梁自由端点荷载。输出弯矩、剪力、弹性挠度、弹性弯曲应力和支座反力。支座弯矩按绝对值报告。输入单位为mm、kN/m、kN、N/mm²、mm⁴和mm³，1 kN/m = 1 N/mm。", "",
              "输入必须完整、支承/荷载来源非空并显式确认假设，才计算该单梁弹性需求。用户可提供弯曲应力和挠度限值，结果只比较这两个限值。即使二者满足，整体承载结论仍为null。RC案例要求专用配筋/裂缝/刚度模型，本工具不计算其承载。", "",
              "不能把展示梁截面、阳台进深、房间跨度或楼板厚度直接当作工程选型。尤其悬臂阳台还需支座、回跨梁、连接、挠曲转角及防水细节设计。", "",
              "未完成的整体验算：", ""]
    lines += [f"- {x}" for x in report["pending_global_checks"]]
    lines += ["", "## 下一项设计工作", "",
              "先由结构设计者确认LDK梁、阳台和阁楼床组的传力与支承，选择实际W/S/RC材料体系，再填写工程输入。几何面积统计可现在复算；承重计算不以未知荷载代入默认值。当地法规适配仍待真实地块、道路和用途分区。", "",
              "方法依据及边界见 [使用说明](../../../analysis/README.md)。本报告没有变更STEP、GLB或已确认户型。", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--init-inputs", type=Path, help="Create an unfilled editable template; refuse overwrite")
    parser.add_argument("--inputs", type=Path, help="Review a previously created, source-bound input JSON")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "output/analysis/current")
    args = parser.parse_args()
    if args.init_inputs and args.inputs:
        parser.error("Choose --init-inputs or --inputs, not both")
    data, binding = load_sources()
    template = input_template(data[1], binding)
    if args.init_inputs:
        target = args.init_inputs.resolve()
        if target.is_relative_to(ROOT) and not target.is_relative_to(ROOT / "output/analysis"):
            parser.error("Repository input templates must remain under output/analysis")
        args.init_inputs.parent.mkdir(parents=True, exist_ok=True)
        with args.init_inputs.open("x") as f:
            f.write(json.dumps(template, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
        print(f"Created unfilled inputs: {args.init_inputs.resolve()}")
        return
    inputs = json.loads(args.inputs.read_text()) if args.inputs else template
    report = build_report(data, binding, inputs)
    out = args.output_dir.resolve()
    # Protect both engineering inputs and the CAD freshness source/artifact set.
    if not out.is_relative_to(ROOT / "output/analysis") and out.is_relative_to(ROOT):
        parser.error("Repository outputs must remain under output/analysis")
    paths = [out / "house_review.json", out / "house_review.md"]
    if args.inputs and args.inputs.resolve() in paths:
        parser.error("Output would overwrite the engineering input file")
    out.mkdir(parents=True, exist_ok=True)
    paths[0].write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    paths[1].write_text(markdown(report))
    print(json.dumps({"revision": binding["revision"], "structural_capacity_result": None,
                      "excluding_stairs_ratio_percent": report["space"]["combined"]["excluding_stairs_ratio_percent"],
                      "circulation_conflict_count": len(report["circulation"]["conflicts"]),
                      "attic_simultaneous_hall_passage_result": None,
                      "outputs": [str(p) for p in paths]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
