"""Independent checks of the R01 plan source and saved editable DXFs.

Run from any directory with the project interpreter. Only validation.json is
written; model sources and CAD artifacts are never regenerated or repaired.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import ezdxf
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import linemerge, unary_union

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "src"))
from lib.house_plan import P, floor_plan  # noqa: E402
from lib.jp_drafting import LAYERS  # noqa: E402
from cadgen.drawing_checks import (  # noqa: E402
    layer_allows_open_geometry,
    layer_intent,
    validate_dxf_file,
)

AREA_TOL_MM2 = 1e-4
LENGTH_TOL_MM = 1e-6
checks: list[dict] = []


def check(name, passed, evidence, floor=None):
    item = {"check": name, "status": "pass" if passed else "fail", "evidence": evidence}
    if floor is not None:
        item["floor"] = floor
    checks.append(item)


def near(a, b):
    return abs(a - b) <= LENGTH_TOL_MM


def opening(d):
    thickness = P.external_wall if "outside" in (d.a, d.b) else P.internal_wall
    half = thickness / 2 + 1
    if d.axis == "h":
        return box(d.start, d.at - half, d.start + d.width, d.at + half)
    return box(d.at - half, d.start, d.at + half, d.start + d.width)


def window_opening(w):
    axis, at, start, width = w
    half = P.external_wall / 2 + 1
    if axis == "h":
        return box(start, at - half, start + width, at + half)
    return box(at - half, start, at + half, start + width)


def line_parts(shape):
    if shape.geom_type == "LineString":
        return [shape] if shape.length > LENGTH_TOL_MM else []
    return [line for child in getattr(shape, "geoms", []) for line in line_parts(child)]


def door_side_segments(d):
    thickness = P.external_wall if "outside" in (d.a, d.b) else P.internal_wall
    offset, trim = thickness / 2 + 2, 0.01
    if d.axis == "h":
        return [LineString([(d.start + trim, d.at + sign * offset),
                            (d.start + d.width - trim, d.at + sign * offset)])
                for sign in (-1, 1)]
    return [LineString([(d.at + sign * offset, d.start + trim),
                        (d.at + sign * offset, d.start + d.width - trim)])
            for sign in (-1, 1)]


def swing_sector(d):
    # Source drawings use a left hinge on horizontal door openings. A filled
    # quarter disk checks every leaf position, rather than just the open leaf.
    center = (d.start, d.at)
    points = [center] + [(center[0] + d.width * math.cos(math.pi / 2 * i / 720),
                         center[1] + d.direction * d.width * math.sin(math.pi / 2 * i / 720))
                        for i in range(721)]
    return Polygon(points)


def parking_envelope(d):
    # The actual drawing places parked leaves 20 mm from their closed line:
    # horizontal a+30 and vertical a-30. A nominal 30 mm panel is tested here.
    start = d.start - d.width if d.direction < 0 else d.start + d.width
    if d.axis == "h":
        return box(start, d.at + 15, start + d.width, d.at + 45)
    return box(d.at - 45, start, d.at - 15, start + d.width)


def validate_floor(f):
    n = f.number
    inner = box(P.external_wall, P.external_wall,
                P.width - P.external_wall, P.depth - P.external_wall)
    building = box(0, 0, P.width, P.depth)
    rooms = {r.id: r for r in f.rooms}
    check("unique_room_and_door_ids", len(rooms) == len(f.rooms) and
          len({d.id for d in f.doors}) == len(f.doors),
          {"rooms": list(rooms), "doors": [d.id for d in f.doors]}, n)
    for r in f.rooms:
        outside = r.shape.difference(inner).area
        wall_overlap = r.shape.intersection(f.walls).area
        check(f"room/{r.id}/valid_and_inside", r.shape.is_valid and r.shape.area > 0 and
              outside <= AREA_TOL_MM2, {"net_area_m2": r.area, "outside_area_mm2": outside}, n)
        check(f"room/{r.id}/label_inside", r.shape.covers(Point(r.label)), {"label_mm": r.label}, n)
        check(f"room/{r.id}/no_wall_overlap", wall_overlap <= AREA_TOL_MM2,
              {"overlap_area_mm2": wall_overlap}, n)
    overlaps = []
    for i, a in enumerate(f.rooms):
        for b in f.rooms[i + 1:]:
            area = a.shape.intersection(b.shape).area
            if area > AREA_TOL_MM2:
                overlaps.append({"a": a.id, "b": b.id, "area_mm2": area})
    check("room_pair_non_overlap", not overlaps,
          {"pairs_checked": len(f.rooms) * (len(f.rooms) - 1) // 2, "overlaps": overlaps}, n)
    holes = inner.difference(unary_union([r.shape for r in f.rooms] + [f.walls] +
                                         [opening(d) for d in f.doors] +
                                         [window_opening(w) for w in f.windows]))
    check("interior_fully_partitioned", holes.area <= AREA_TOL_MM2,
          {"unassigned_area_mm2": holes.area, "unassigned_wkt": holes.wkt}, n)
    fixtures = [(i, name, box(*bounds)) for i, (name, bounds) in enumerate(f.fixtures)]
    for i, name, fixture in fixtures:
        containers = [r.id for r in f.rooms if r.shape.covers(fixture)]
        check(f"fixture/{i}/contained", len(containers) == 1,
              {"name": name, "bounds_mm": fixture.bounds, "rooms": containers}, n)
    widths = {"D01": 900, "D02": 900, "D03": 800, "D04": 750, "D05": 800,
              "D06": 700, "D21": 800, "D22": 800, "D23": 800, "D24": 800, "D25": 700}
    for d in f.doors:
        check(f"door/{d.id}/specified_opening", d.id in widths and near(d.width, widths[d.id]),
              {"width_mm": d.width, "expected_mm": widths.get(d.id), "frame_deduction": "unverified"}, n)
        owners = []
        for segment in door_side_segments(d):
            side = [r.id for r in f.rooms if r.shape.covers(segment)]
            if segment.disjoint(building):
                side.append("outside")
            owners.append(side)
        check(f"door/{d.id}/connects_rooms", all(len(side) == 1 for side in owners) and
              sorted(side[0] for side in owners if len(side) == 1) == sorted([d.a, d.b]),
              {"specified": [d.a, d.b], "full_width_side_owners": owners}, n)
        wall_area = opening(d).intersection(f.walls).area
        check(f"door/{d.id}/opening_clear", wall_area <= AREA_TOL_MM2,
              {"remaining_wall_area_mm2": wall_area}, n)
        if d.kind == "slide":
            parked = parking_envelope(d)
            outside_wall = parked.difference(f.walls).area
            overlap_doors = [{"door": other.id, "area_mm2": parked.intersection(opening(other)).area}
                             for other in f.doors if other.id != d.id and
                             parked.intersection(opening(other)).area > AREA_TOL_MM2]
            check(f"door/{d.id}/parking_inside_wall", outside_wall <= AREA_TOL_MM2,
                  {"parking_bounds_mm": parked.bounds, "nominal_panel_thickness_mm": 30,
                   "outside_wall_area_mm2": outside_wall}, n)
            check(f"door/{d.id}/parking_avoids_other_openings", not overlap_doors,
                  {"overlaps": overlap_doors}, n)
        elif d.kind == "swing" and "outside" not in (d.a, d.b):
            sector = swing_sector(d)
            target = rooms[d.b].shape.union(opening(d))
            outside = sector.difference(target).area
            hits_wall = sector.intersection(f.walls).area
            collisions = [{"fixture": i, "name": name, "area_mm2": sector.intersection(shape).area}
                          for i, name, shape in fixtures if sector.intersection(shape).area > AREA_TOL_MM2]
            check(f"door/{d.id}/swing_inside_room_and_no_walls", outside <= AREA_TOL_MM2 and
                  hits_wall <= AREA_TOL_MM2,
                  {"target_room": d.b, "outside_area_mm2": outside, "wall_hit_area_mm2": hits_wall,
                   "method": "quarter-disk swept region, 720 arc subdivisions"}, n)
            check(f"door/{d.id}/swing_avoids_furniture", not collisions,
                  {"collisions": collisions, "minimum_clearance_mm": min(sector.distance(shape)
                   for _, _, shape in fixtures)}, n)
    hall = rooms["hall"].shape
    stations = []
    for axis in (0, 1):
        coords = sorted({point[axis] for point in hall.exterior.coords})
        for lo, hi in zip(coords, coords[1:]):
            mid = (lo + hi) / 2
            scan = LineString([(mid, -1), (mid, P.depth + 1)]) if axis == 0 else \
                   LineString([(-1, mid), (P.width + 1, mid)])
            for segment in line_parts(hall.intersection(scan)):
                stations.append({"scan": "vertical" if axis == 0 else "horizontal",
                                 "station_mm": mid, "clear_span_mm": segment.length})
    minimum = min(s["clear_span_mm"] for s in stations)
    hall_obstructions = hall.intersection(unary_union([f.walls] + [s for _, _, s in fixtures])).area
    check("hall_minimum_clear_width", minimum >= 900 - LENGTH_TOL_MM and hall_obstructions <= AREA_TOL_MM2,
          {"minimum_span_mm": minimum, "rectilinear_cross_sections": stations,
           "wall_or_fixture_obstruction_mm2": hall_obstructions,
           "doorways_excluded": "700/750/800 openings checked separately"}, n)


def matching_line(msp, a, b):
    def same(p, q):
        return near(p[0], q[0]) and near(p[1], q[1])
    return any((same(e.dxf.start, a) and same(e.dxf.end, b)) or
               (same(e.dxf.start, b) and same(e.dxf.end, a))
               for e in msp.query(f'LINE[layer=="{LAYERS["DOOR"]}"]'))


def validate_dxf(f):
    n = f.number
    path = ROOT / f"DXF/house_{n}f_plan.dxf"
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    counts = Counter(e.dxftype() for e in msp)
    check("dxf/native_text_and_dimensions", counts["TEXT"] > 0 and counts["DIMENSION"] > 0,
          {"modelspace_entity_counts": dict(counts)}, n)
    check("dxf/millimetres", doc.units == ezdxf.units.MM and doc.header.get("$INSUNITS") == 4,
          {"units": doc.units, "INSUNITS": doc.header.get("$INSUNITS"),
           "MEASUREMENT": doc.header.get("$MEASUREMENT")}, n)
    names = {e.dxf.text for e in msp.query("TEXT")}
    missing = [r.name for r in f.rooms if r.id != "stairs" and r.name not in names]
    check("dxf/editable_room_names", not missing, {"missing_TEXT_values": missing}, n)
    for d in f.doors:
        if d.kind == "slide":
            a, b = ((d.start, d.at + 10), (d.start + d.width, d.at + 10)) if d.axis == "h" else \
                   ((d.at - 10, d.start), (d.at - 10, d.start + d.width))
        else:
            a, b = (d.start, d.at), (d.start, d.at + d.direction * d.width)
        check(f"dxf/door/{d.id}/leaf_and_annotation", matching_line(msp, a, b) and
              f"{d.id} / {d.width:.0f}" in names,
              {"actual_required_line_mm": [a, b], "opening_mm": d.width}, n)
    # The viewer uses native LINE boundaries to avoid filling room interiors.
    # Rejoin those edges into closed loops; symmetric difference of outer and
    # inner loops reconstructs solids without assuming ring order.
    saved_walls = Polygon()
    edges = [LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)])
             for e in msp.query(f'LINE[layer=="{LAYERS["WALL"]}"]')]
    merged = linemerge(edges) if edges else LineString()
    wall_loops = list(merged.geoms) if hasattr(merged, "geoms") else [merged]
    for i, loop in enumerate(wall_loops):
        check(f"dxf/wall_loop/{i}/closed", loop.is_ring,
              {"vertices": len(loop.coords)}, n)
        if loop.is_ring:
            saved_walls = saved_walls.symmetric_difference(Polygon(loop.coords))
    delta = saved_walls.symmetric_difference(f.walls).area
    check("dxf/walls_match_source", bool(wall_loops) and delta <= AREA_TOL_MM2,
          {"native_LINE_edges": len(edges), "closed_loops": len(wall_loops),
           "symmetric_difference_area_mm2": delta}, n)
    values = []
    for dim in msp.query("DIMENSION"):
        measured = float(dim.get_measurement())
        values.append(measured)
        style = doc.dimstyles.get(dim.dxf.dimstyle)
        overrides = dim.get_acad_dstyle(style)
        factor = overrides.get("dimlfac", style.dxf.dimlfac)
        block = doc.blocks.get(dim.dxf.geometry)
        texts = [(e.plain_text() if e.dxftype() == "MTEXT" else e.dxf.text)
                 for e in block if e.dxftype() in ("TEXT", "MTEXT")]
        check(f"dxf/dimension/{dim.dxf.handle}/unscaled_correct_value",
              near(factor, 1) and overrides.get("dimlfac") == 1 and texts == [f"{measured:.0f}"],
              {"measurement_mm": measured, "dimlfac": factor, "explicit_dimlfac": overrides.get("dimlfac"),
               "anonymous_block": dim.dxf.geometry, "block_TEXT_MTEXT": texts}, n)
    expected = [7280, 7280, 1820, 1820, 1080, 1900] if n == 1 else [7280, 7280, 3370, 1450, 1900]
    check("dxf/dimension_measurements", sorted(values) == sorted(expected),
          {"actual_mm": values, "expected_mm": expected,
           "overall_dimension_text_must_be": "7280; never 728000"}, n)
    auditor = doc.audit()
    check("dxf/ezdxf_audit", not auditor.errors and not auditor.fixes,
          {"errors": [str(x) for x in auditor.errors], "fixes": [str(x) for x in auditor.fixes]}, n)
    used_layers = sorted({e.dxf.layer for e in msp})
    intents = {name: {"intent": layer_intent(name), "open_geometry_allowed": layer_allows_open_geometry(name)}
               for name in used_layers}
    check("dxf/architectural_layers", set(used_layers).issubset(set(LAYERS.values())),
          {"layers": intents, "scope": "Dimensioned architectural drawing; CAM cut-profile closure is not required."}, n)
    findings = validate_dxf_file(path)
    check("dxf/cadgen_validate_dxf_file", not any(x.severity == "error" for x in findings),
          {"findings": [{"severity": x.severity, "code": x.code, "message": x.message} for x in findings]}, n)


def main():
    check("specified_plan_parameters", all(near(actual, expected) for actual, expected in
          [(P.width, 7280), (P.depth, 7280), (P.external_wall, 180), (P.internal_wall, 100),
           (P.storey_height, 2800), (P.stair_width, 900), (P.stair_landing, 900), (P.tread, 260)]) and P.risers == 16,
          {"outer_mm": [P.width, P.depth], "walls_mm": [P.external_wall, P.internal_wall],
           "storey_height_mm": P.storey_height})
    floors = [floor_plan(1), floor_plan(2)]
    for name in ("wc", "stairs"):
        shapes = [next(r.shape for r in f.rooms if r.id == name) for f in floors]
        delta = shapes[0].symmetric_difference(shapes[1]).area
        check(f"floor_alignment/{name}", delta <= AREA_TOL_MM2,
              {"bounds_1f_mm": shapes[0].bounds, "bounds_2f_mm": shapes[1].bounds,
               "symmetric_difference_area_mm2": delta})
    bounds = next(r.shape.bounds for r in floors[0].rooms if r.id == "stairs")
    width, depth = bounds[2] - bounds[0], bounds[3] - bounds[1]
    check("stairs/rise_and_run", P.risers == 16 and near(P.storey_height / P.risers, 175) and
          near(16 * 175, P.storey_height) and near(depth, 7 * 260 + 900) and
          near(width, 2 * 900 + 100),
          {"risers": 16, "riser_mm": P.storey_height / P.risers, "treads_per_flight": 7,
           "tread_mm": P.tread, "landing_mm": P.stair_landing, "reserve_mm": [width, depth],
           "plan_only": "floor openings and stair headroom require later 3D verification"})
    for f in floors:
        try:
            validate_floor(f)
            validate_dxf(f)
        except Exception as exc:
            check("check_execution_completed", False, {"exception": f"{type(exc).__name__}: {exc}"}, f.number)
    unverified = [
        "R01 plan is user-approved; 3D, STEP and GLB validation belongs to the separate 3D report.",
        "Actual stair headroom, floor opening construction, beams, slab and finished-floor thickness.",
        "Structure, foundation, seismic design, engineering calculations and statutory compliance.",
        "Site boundaries, road, actual north, setbacks, services, daylight and site measurements.",
        "Door frames, net product opening after frames, hinges and proprietary pocket-door construction.",
        "30 mm sliding-panel envelope is a drawing assumption; 100 mm wall feasibility is not certified.",
        "Sliding pockets crossing partition junctions, concealed services and support structure need detailing.",
        "Swing sectors use a zero-thickness leaf and 720-segment arc approximation; hardware is not modeled.",
        "Hall cross sections test this rectilinear geometry; accessibility/manoeuvring criteria are not assessed.",
        "This plan report does not assess window/door heights, roof geometry, lighting, ventilation, drainage, or furniture product specifications.",
        "PDF typography, paper printing scale and user visual acceptance are separate from this geometric/DXF check.",
    ]
    paths = [ROOT / "src/lib/house_plan.py", ROOT / "src/generate_plans.py", Path(__file__)] + \
            [ROOT / f"DXF/house_{n}f_plan.dxf" for n in (1, 2)]
    report = {"revision": "R01", "stage": "floor_plan_approved", "units": "mm",
              "checked_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
              "scope": "Independent plan geometry and saved DXF validation; not a building approval.",
              "tolerances": {"area_mm2": AREA_TOL_MM2, "length_mm": LENGTH_TOL_MM},
              "artifact_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in paths if p.exists()},
              "summary": {"checks": len(checks), "passed": sum(c["status"] == "pass" for c in checks),
                          "failed": sum(c["status"] == "fail" for c in checks)},
              "checks": checks, "unverified": unverified}
    path = ROOT / "output/review/validation.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"]))
    for item in checks:
        if item["status"] == "fail":
            print(json.dumps(item, ensure_ascii=False))
    print(f"Report: {path}")
    return 1 if report["summary"]["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
