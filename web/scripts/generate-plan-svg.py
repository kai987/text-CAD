"""Convert the approved R02 PDF to committed, font-independent vector previews.

Run locally: uv pip install --python .venv/bin/python PyMuPDF==1.26.7
             .venv/bin/python web/scripts/generate-plan-svg.py

GitHub Pages builds consume these committed files; they do not need Python.
The original PDF, DXF and house geometry are never rewritten by this script.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
PDF = "output/pdf/house_floor_plans_R09_JP.pdf"
POINTS_PER_MM = 72 / 25.4
# Paper coordinates measured from the top-left of the existing A3 sheet.
# Includes both overall dimensions, door arcs, room labels and north arrow.
CROP_MM = (18.0, 50.0, 207.0, 225.0)
REQUIRED_LABELS = {
    1: ["7280", "LDK", "浴室", "洗面", "玄関", "トイレ", "階段"],
    2: ["7280", "主寝室", "洋室 2", "洋室 3", "収納", "トイレ", "階段"],
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    pdf_bytes = (ROOT / PDF).read_bytes()
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    if len(document) != 2:
        raise ValueError("The approved floor-plan PDF must contain two pages.")
    crop_box = [round(value * POINTS_PER_MM, 6) for value in CROP_MM]
    crop = fitz.Rect(crop_box[0], crop_box[1],
                     crop_box[0] + crop_box[2], crop_box[1] + crop_box[3])
    metadata = {
        "version": 1,
        "source": {"path": PDF, "sha256": sha(pdf_bytes), "pages": 2},
        "generator": {"script": "web/scripts/generate-plan-svg.py",
                      "engine": "PyMuPDF", "version": fitz.VersionBind,
                      "textAsPath": True},
        "cropPaperMm": list(CROP_MM),
        "floors": [],
    }
    for index, page in enumerate(document):
        floor = index + 1
        if not page.rect.contains(crop):
            raise ValueError("The plan crop extends beyond the source page.")
        annotations = []
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    bounds = fitz.Rect(span["bbox"])
                    if crop.contains(bounds):
                        annotations.append({"text": span["text"],
                                            "bounds": [round(v, 6) for v in bounds]})
        labels = [span["text"] for span in annotations]
        for required in REQUIRED_LABELS[floor]:
            if not any(required in text for text in labels):
                raise ValueError(f"Floor {floor} crop omits required label {required!r}.")
        if labels.count("7280") < 1 or labels.count("8190") < 1:
            raise ValueError("Both overall R09 dimensions must be retained.")
        svg = page.get_svg_image(text_as_path=True).encode("utf-8")
        if b"<text" in svg or b"<image" in svg:
            raise ValueError("Expected vector-only shapes and outlined text.")
        path = f"output/vector/house_{floor}f_plan.svg"
        output = ROOT / path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(svg)
        metadata["floors"].append({
            "floor": floor, "page": floor,
            "path": path, "bytes": len(svg), "sha256": sha(svg),
            "fullViewBox": [0, 0, round(page.rect.width, 6), round(page.rect.height, 6)],
            "planViewBox": crop_box,
            "requiredLabels": REQUIRED_LABELS[floor],
            "annotations": annotations,
        })
    metadata_path = ROOT / "web/src/plan-preview-metadata.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    print(f"Converted {len(document)} approved PDF pages to outlined SVG; source {sha(pdf_bytes)}.")


if __name__ == "__main__":
    main()
