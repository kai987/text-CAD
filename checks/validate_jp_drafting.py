"""Inspect saved R10 architectural DXFs and the A3 PDF against adapted common rules.

This is an artifact check, not a generator test or an SXF/building certification.
Run after src/generate_plans.py; it writes only its JSON validation report.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import ezdxf
from ezdxf import bbox
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "src"))
from lib.house_plan import P, floor_plan  # noqa: E402

LAYOUT = "JP_A3_1_50"
SCALE = 50
PAPER_HEIGHTS = (1.8, 2.5, 3.5, 5, 7, 10, 14, 20)
LAYERS = {
    "D-STR-WALL": 50, "D-STR-DOOR": 25, "D-STR-WIND": 25,
    "D-STR-STAI": 13, "D-BYP-FIXT": 13, "D-STR-TXT": 13,
    "D-STR-DIM": 13, "D-BMK-NORT": 13, "D-TTL-FRAM": 70,
    "D-TTL-LINE": 13, "D-TTL-TXT": 13, "D-TTL-VPRT": 13,
    "D-DOC-TXT": 13,
}
checks: list[dict] = []


def check(name, passed, evidence, floor=None):
    item = {"check": name, "status": "pass" if passed else "fail", "evidence": evidence}
    if floor is not None:
        item["floor"] = floor
    checks.append(item)


def close(a, b, tolerance=1e-6):
    return abs(float(a) - float(b)) <= tolerance


def matches(values, expected):
    return len(values) == len(expected) and all(close(a, b) for a, b in zip(values, expected))


def text(entity):
    if entity.dxftype() == "TEXT":
        return entity.dxf.text
    if entity.dxftype() == "MTEXT":
        return entity.plain_text()
    return ""


def height(entity):
    return entity.dxf.height if entity.dxftype() == "TEXT" else entity.dxf.char_height


def role(entity):
    if not entity.has_xdata("JP_SHEET"):
        return ""
    return " ".join(str(tag.value) for tag in entity.get_xdata("JP_SHEET") if tag.code == 1000)


def extents(entity):
    e = bbox.extents([entity])
    return [e.extmin.x, e.extmin.y, e.extmax.x, e.extmax.y] if e.has_data else []


def validate_dxf(number):
    path = ROOT / f"DXF/house_{number}f_plan.dxf"
    canonical = ROOT / f"DXF/{number:03d}D0PL2-{number}FPLAN.DXF"
    check("canonical_files_exist", path.is_file() and canonical.is_file(),
          {"alias": str(path.relative_to(ROOT)), "canonical": str(canonical.relative_to(ROOT))}, number)
    if not path.is_file():
        return
    if canonical.is_file():
        check("canonical_name_and_byte_identity",
              re.fullmatch(r"[0-9]{3}D0PL2-[12]FPLAN\.DXF", canonical.name) is not None
              and canonical.read_bytes() == path.read_bytes(),
              {"canonical": canonical.name, "alias_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
               "canonical_sha256": hashlib.sha256(canonical.read_bytes()).hexdigest()}, number)
    doc = ezdxf.readfile(path)
    audit = doc.audit()
    check("native_dxf_audit", not audit.errors and not audit.fixes,
          {"errors": len(audit.errors), "fixes": len(audit.fixes)}, number)
    check("model_units_real_mm", doc.units == ezdxf.units.MM and doc.header.get("$INSUNITS") == 4,
          {"units": doc.units, "INSUNITS": doc.header.get("$INSUNITS")}, number)
    used = Counter(e.dxf.layer for e in doc.modelspace())
    check("architectural_layers_present", all(layer in doc.layers for layer in LAYERS),
          {"expected": LAYERS, "model_entity_counts": dict(used)}, number)
    old_layers = [l.dxf.name for l in doc.layers if "REFERENCE" in l.dxf.name]
    check("legacy_reference_layers_replaced", not old_layers, {"legacy_layers": old_layers}, number)
    for layer_name, weight in LAYERS.items():
        if layer_name not in doc.layers:
            continue
        layer = doc.layers.get(layer_name)
        check(f"layer/{layer_name}/name", bool(re.fullmatch(r"D-[A-Z]{3}-[A-Z0-9]{1,4}", layer_name)),
              {"name": layer_name, "scope": "住宅用追加作図要素は対応表に記録"}, number)
        check(f"layer/{layer_name}/color", layer.dxf.color == 7 and not layer.dxf.hasattr("true_color"),
              {"ACI": layer.dxf.color, "true_color": layer.dxf.get("true_color")}, number)
        check(f"layer/{layer_name}/lineweight", layer.dxf.lineweight == weight,
              {"hundredth_mm": layer.dxf.lineweight, "expected_hundredth_mm": weight}, number)
        check(f"layer/{layer_name}/linetype", layer.dxf.linetype.upper() == "CONTINUOUS",
              {"linetype": layer.dxf.linetype}, number)
    entities = [e for e in doc.entitydb.values() if e.is_alive and hasattr(e, "dxf")
                and e.dxf.is_supported("layer") and e.dxf.is_supported("color")]
    # Standard arrow symbol definitions use ByBlock=0. They inherit the neutral
    # INSERT color and are not a separately chosen display color. Model/paper
    # entities themselves must remain ACI7/ByLayer.
    symbol_owner_handles = {block.block_record_handle for block in doc.blocks
                            if block.name in ("_ARCHTICK", "_CLOSEDFILLED", "_CLOSEDBLANK")}
    bad_colors = [{"handle": e.dxf.handle, "type": e.dxftype(), "layer": e.dxf.layer,
                   "ACI": e.dxf.get("color", 256), "RGB": e.dxf.get("true_color")}
                  for e in entities if (e.dxf.get("color", 256) not in (7, 256)
                  and not (e.dxf.get("color", 256) == 0 and e.dxf.owner in symbol_owner_handles))
                  or e.dxf.hasattr("true_color")]
    check("all_graphic_colors_aci7_or_bylayer_no_rgb", not bad_colors,
          {"graphic_entities_checked": len(entities), "invalid": bad_colors,
           "internal_arrow_definitions": "ByBlock=0 inherits ACI7/ByLayer INSERT"}, number)
    msp = doc.modelspace()
    walls = list(msp.query('*[layer=="D-STR-WALL"]'))
    wall_extents = bbox.extents(walls)
    wall_bounds = [wall_extents.extmin.x, wall_extents.extmin.y, wall_extents.extmax.x,
                   wall_extents.extmax.y] if wall_extents.has_data else []
    check("approved_outer_boundary_preserved", matches(wall_bounds, [0, -P.balcony_depth if number == 2 else 0, P.width, P.depth]),
          {"wall_bounds_mm": wall_bounds, "demo_assumptions": [P.width, P.depth, P.storey_height]}, number)
    mtexts = list(msp.query("TEXT MTEXT"))
    bad_heights = [{"value": text(e), "height_mm": height(e), "paper_height_mm": height(e) / SCALE}
                   for e in mtexts if not any(close(height(e) / SCALE, h) for h in PAPER_HEIGHTS)]
    check("model_text_paper_heights", bool(mtexts) and not bad_heights,
          {"model_to_paper": "height / 50", "paper_height_counts": dict(Counter(height(e) / SCALE for e in mtexts)),
           "invalid": bad_heights}, number)
    for room in floor_plan(number).rooms:
        if room.id == "stairs":
            continue
        labels = [e for e in mtexts if text(e) == room.name]
        check(f"room/{room.id}/name_height", len(labels) == 1 and close(height(labels[0]) / SCALE, 3.5),
              {"room": room.name, "found": len(labels), "model_height": height(labels[0]) if labels else None}, number)
        values = [e for e in mtexts if text(e) in (f"{room.area:.2f} m2", f"{room.area:.2f} m²")]
        check(f"room/{room.id}/area_height", bool(values) and all(close(height(e) / SCALE, 2.5) for e in values),
              {"area_m2": room.area, "matches": [text(e) for e in values],
               "heights_mm": [height(e) for e in values]}, number)
    dims = list(msp.query("DIMENSION"))
    check("native_dimensions_present", len(dims) >= 5, {"native_dimension_count": len(dims)}, number)
    measurements = []
    for index, dim in enumerate(dims):
        override = dim.override()
        angle = math.radians(dim.dxf.angle)
        a, b = dim.dxf.defpoint2, dim.dxf.defpoint3
        true_value = abs((b.x - a.x) * math.cos(angle) + (b.y - a.y) * math.sin(angle))
        actual = float(dim.get_measurement())
        measurements.append(actual)
        check(f"dimension/{index}/actual_measurement", close(actual, true_value) and actual > 0,
              {"measurement_mm": actual, "projected_definition_points_mm": true_value,
               "display_text": dim.dxf.text}, number)
        check(f"dimension/{index}/scale_and_style", close(override.get("dimlfac", 1), 1)
              and close(override.get("dimtxt", 0) / SCALE, 2.5),
              {"DIMLFAC": override.get("dimlfac", 1), "DIMTXT_model_mm": override.get("dimtxt", 0)}, number)
        check(f"dimension/{index}/lineweight", override.get("dimlwd", -1) == 13
              and override.get("dimlwe", -1) == 13,
              {"DIMLWD": override.get("dimlwd", -1), "DIMLWE": override.get("dimlwe", -1)}, number)
        block = doc.blocks.get(dim.dxf.geometry) if dim.dxf.geometry else None
        btexts = list(block.query("TEXT MTEXT")) if block is not None else []
        check(f"dimension/{index}/editable_block_text", bool(btexts) and all(
              close(height(e) / SCALE, 2.5) for e in btexts),
              {"block": dim.dxf.geometry, "text": [text(e) for e in btexts],
               "paper_heights_mm": [height(e) / SCALE for e in btexts]}, number)
    check("outer_dimensions_7280", all(any(close(value, size) for value in measurements) for size in (P.width,P.depth)),
          {"native_measurements_mm": measurements}, number)
    check("paper_layout_exists", LAYOUT in doc.layouts, {"layout_names": list(doc.layout_names())}, number)
    if LAYOUT not in doc.layouts:
        return
    paper = doc.layouts.get(LAYOUT)
    props = paper.dxf_layout.dxf
    check("paper_A3_landscape_mm", matches([props.paper_width, props.paper_height], [420, 297])
          and props.plot_paper_units == 1,
          {"width_mm": props.paper_width, "height_mm": props.paper_height,
           "plot_paper_units": props.plot_paper_units}, number)
    frame = [e for e in paper if e.dxftype() == "LWPOLYLINE" and "frame" in role(e)]
    check("paper_frame_7_5_margin_0_7_solid", len(frame) == 1 and frame[0].closed
          and matches(extents(frame[0]), [7.5, 7.5, 412.5, 289.5])
          and doc.layers.get(frame[0].dxf.layer).dxf.lineweight == 70
          and doc.layers.get(frame[0].dxf.layer).dxf.linetype.upper() == "CONTINUOUS",
          {"count": len(frame), "bounds_paper_mm": [extents(e) for e in frame]}, number)
    title = [e for e in paper if e.dxftype() == "LWPOLYLINE" and "title_block" in role(e)]
    check("title_block_60x45_bottom_right", len(title) == 1 and title[0].closed
          and matches(extents(title[0]), [352.5, 7.5, 412.5, 52.5]),
          {"count": len(title), "bounds_paper_mm": [extents(e) for e in title]}, number)
    ptexts = list(paper.query("TEXT MTEXT"))
    titletexts = [text(e) for e in ptexts if e.dxf.layer == "D-TTL-TXT"]
    required_fields = ["施設名", "工事件名", "工事箇所", "図面名称", "縮尺", "図面番号", "作製年月日", "事業所名"]
    check("title_block_eight_residential_fields", all(any(s.startswith(label) for s in titletexts) for label in required_fields),
          {"required_labels": required_fields, "title_texts": titletexts}, number)
    check("title_block_revision_date_scale_sheet", any("令和8年10月7日" in s for s in titletexts)
          and any("1:50" in s for s in titletexts) and any("R20" in text(e) for e in ptexts)
          and f"{number:03d}" in titletexts and "全2枚" in titletexts,
          {"title_texts": titletexts}, number)
    invalid_paper_heights = [{"value": text(e), "height_paper_mm": height(e)} for e in ptexts
                            if not any(close(height(e), h) for h in PAPER_HEIGHTS)]
    check("paperspace_text_heights", bool(ptexts) and not invalid_paper_heights,
          {"paper_height_counts": dict(Counter(height(e) for e in ptexts)), "invalid": invalid_paper_heights}, number)
    viewports = [e for e in paper.query("VIEWPORT") if e.dxf.id > 1]
    check("single_model_viewport", len(viewports) == 1,
          {"viewport_ids": [e.dxf.id for e in paper.query("VIEWPORT")]}, number)
    for viewport in viewports:
        layer = doc.layers.get(viewport.dxf.layer)
        ratio = viewport.dxf.height / viewport.dxf.view_height
        check("viewport_1_50_locked_nonprinting", close(ratio, 1 / SCALE)
              and bool(viewport.dxf.flags & 16384) and layer.dxf.plot == 0,
              {"paper_height_mm": viewport.dxf.height, "model_view_height_mm": viewport.dxf.view_height,
               "ratio": ratio, "flags": viewport.dxf.flags, "layer": viewport.dxf.layer,
               "layer_plot": layer.dxf.plot}, number)
    all_texts = mtexts + ptexts + [e for block in doc.blocks for e in block.query("TEXT MTEXT")]
    disallowed = [{"text": text(e), "handle": e.dxf.handle} for e in all_texts
                  if any(0xFF61 <= ord(c) <= 0xFF9F or 0x2460 <= ord(c) <= 0x2473
                         or 0x2160 <= ord(c) <= 0x217F or c == "㎡" for c in text(e))]
    check("no_disallowed_example_characters", not disallowed,
          {"scanned_text_entities": len(all_texts), "invalid": disallowed}, number)
    metadata = doc.ezdxf_metadata()
    meta = {key: metadata.get(key, "") for key in ("REVISION", "STANDARD", "SCOPE", "SCALE")}
    check("document_standard_metadata", meta["REVISION"] == "R20" and "東京都" in meta["STANDARD"]
          and "住宅" in meta["SCOPE"] and ("準用" in meta["SCOPE"] or "准用" in meta["SCOPE"])
          and meta["SCALE"] == "1:50", meta, number)


def validate_pdf():
    path = ROOT / "output/pdf/house_floor_plans_R10_JP.pdf"
    check("R10_pdf_exists", path.is_file(), {"path": str(path.relative_to(ROOT))})
    if not path.is_file():
        return
    pdf = PdfReader(path)
    check("pdf_two_pages", len(pdf.pages) == 2, {"pages": len(pdf.pages)})
    for index, page in enumerate(pdf.pages, 1):
        width, height_mm = float(page.mediabox.width) * 25.4 / 72, float(page.mediabox.height) * 25.4 / 72
        check("pdf_A3_landscape", close(width, 420, 1e-4) and close(height_mm, 297, 1e-4),
              {"paper_mm": [width, height_mm]}, index)
        value = (page.extract_text() or "").replace(",", "")
        check("pdf_standard_revision_date_and_demo_notes", "R20" in value and "1:50" in value
              and "令和8年10月7日" in value and "8190" in value and "7280" in value and "2800" in value,
              {"R10": "R20" in value, "scale": "1:50" in value,
               "wareki": "令和8年10月7日" in value, "outer": "7280" in value,
               "storey": "2800" in value}, index)


def main():
    for number in (1, 2):
        try:
            validate_dxf(number)
        except Exception as exc:
            check("dxf_check_execution_completed", False, {"exception": f"{type(exc).__name__}: {exc}"}, number)
    try:
        validate_pdf()
    except Exception as exc:
        check("pdf_check_execution_completed", False, {"exception": f"{type(exc).__name__}: {exc}"})
    paths = [ROOT / f"DXF/house_{n}f_plan.dxf" for n in (1, 2)] + [
        ROOT / f"DXF/{n:03d}D0PL2-{n}FPLAN.DXF" for n in (1, 2)] + [
        ROOT / "output/pdf/house_floor_plans_R10_JP.pdf", Path(__file__),
        ROOT / "docs/tokyo_cad_standard_mapping_R02.md", ROOT / "src/generate_plans.py",
        ROOT / "src/lib/jp_sheet.py"]
    report = {
        "revision": "R20", "standard": "東京都建設局 CAD製図基準 令和6年4月 土木202404-01",
        "standard_url": "https://www.kensetsu.metro.tokyo.lg.jp/documents/d/kensetsu/000067788",
        "scope": "住宅に準用した共通製図項目の保存物チェック。土木電子納品又は建築法令の全項目適合ではない。",
        "checked_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
        "artifact_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in paths if p.is_file()},
        "summary": {"checks": len(checks), "passed": sum(c["status"] == "pass" for c in checks),
                    "failed": sum(c["status"] == "fail" for c in checks)},
        "checks": checks,
        "limitations": ["A3 is a recorded A-series alternative to the standard A1.",
                        "Residential layers and eight title labels are recorded adaptations.",
                        "No SXF(P21/P2Z), DRAWING.XML or full electronic-delivery package.",
                        "3D STEP is not 2D SXF and is not certified by this check.",
                        "Typography overlap, font rendering and print readability require visual PDF/CAD review.",
                        "Unchanged room/door/stair geometry is checked separately by validate_plans.py."]}
    output = ROOT / "output/review/validation_jp_drafting.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"]))
    for item in checks:
        if item["status"] == "fail":
            print(json.dumps(item, ensure_ascii=False))
    print(f"Report: {output}")
    return 1 if report["summary"]["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
