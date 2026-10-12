"""Editable, true-size river DXFs and matching A3 SVG review sheets.

No survey, hydraulic calculation, construction approval or real river is implied.
All drawing geometry is read from the same module as the named STEP/GLB.
"""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path

import ezdxf
from ezdxf.enums import TextEntityAlignment

from lib.river_geometry import (
    R, REVISION, center_x, sample_ys, section_offsets, cross_section,
    bridge_dimensions, stairs_positions, tree_positions, bench_positions, lamp_positions,
)

ROOT = Path(__file__).resolve().parents[1]
LAYERS = {
    "terrain": "D-STR-GRND", "water": "D-STR-WATR", "bank": "D-STR-RBNK",
    "path": "D-BYP-PATH", "bridge": "D-STR-BRDG", "stairs": "D-STR-STAI",
    "vegetation": "D-BYP-TREE", "furniture": "D-BYP-FURN", "light": "D-BYP-LGHT",
    "text": "D-STR-TXT", "dimension": "D-STR-DIM", "axis": "D-BMK-AXIS",
    "sheet": "D-TTL-FRAM", "sheet_text": "D-TTL-TXT", "viewport": "D-TTL-VPRT",
}


class RiverDrawing:
    """One drawing API writes CAD primitives and a readable review sheet."""
    def __init__(self, title, scale, origin, centre=(0, 0)):
        self.doc = ezdxf.new("R2018", setup=True)
        self.doc.units = ezdxf.units.MM
        self.doc.header["$MEASUREMENT"] = 1
        self.doc.header["$LWDISPLAY"] = True
        self.doc.header["$DIMASSOC"] = 2
        self.doc.styles.new("RIVER_UNICODE", dxfattribs={"font": "Arial Unicode.ttf"})
        for key, name in LAYERS.items():
            self.doc.layers.new(name, dxfattribs={"color": 7, "lineweight": 13 if key in ("text", "dimension") else 25})
        self.doc.layers.get(LAYERS["viewport"]).dxf.plot = 0
        metadata = self.doc.ezdxf_metadata()
        metadata["REVISION"] = REVISION
        metadata["UNITS"] = "mm"
        metadata["SCALE"] = f"1:{scale}; modelspace 1:1"
        metadata["SCOPE"] = "日本近郊河川のデモ仮定。測量図・水理計算・施工図ではない。"
        self.msp = self.doc.modelspace()
        self.scale, self.origin, self.centre = scale, origin, centre
        self.svg = []
        self.layout = self.doc.layouts.new(f"RIVER_A3_1_{scale}")
        self.layout.page_setup(size=(420, 297), margins=(0, 0, 0, 0), units="mm")
        self.paper_poly([(7.5, 7.5), (412.5, 7.5), (412.5, 289.5), (7.5, 289.5)], close=True)
        self.paper_text(title, (15, 277), 5)
        self.paper_text(f"{REVISION}  |  A3  |  1:{scale}  |  単位 mm  |  全寸法はデモ仮定", (15, 267), 2.8)
        self.paper_text("作成 2026-10-12  /  text-CAD  /  非実在・未計算の参考モデル", (15, 16), 2.8)

    def xy(self, p):
        x = self.origin[0] + (p[0] - self.centre[0]) / self.scale
        y = self.origin[1] + (p[1] - self.centre[1]) / self.scale
        return x * 4, (297 - y) * 4

    @staticmethod
    def paper_xy(p):
        return p[0] * 4, (297 - p[1]) * 4

    def svg_poly(self, points, fill="none", stroke="#253444", width=1, close=False):
        pts = " ".join(f"{x:.3f},{y:.3f}" for x, y in points)
        tag = "polygon" if close else "polyline"
        self.svg.append(f'<{tag} points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round"/>')

    def poly(self, points, layer="terrain", fill=None, close=True):
        self.msp.add_lwpolyline(points, close=close, dxfattribs={"layer": LAYERS[layer]})
        self.svg_poly([self.xy(p) for p in points], fill or "none", close=close)

    def rect(self, bounds, layer="terrain", fill=None):
        x1, y1, x2, y2 = bounds
        self.poly([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], layer, fill)

    def line(self, a, b, layer="axis", stroke="#253444", width=1):
        self.msp.add_line(a, b, dxfattribs={"layer": LAYERS[layer]})
        self.svg_poly([self.xy(a), self.xy(b)], stroke=stroke, width=width)

    def circle(self, at, radius, layer="vegetation", fill=None):
        self.msp.add_circle(at, radius, dxfattribs={"layer": LAYERS[layer]})
        x, y = self.xy(at)
        self.svg.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{radius / self.scale * 4:.3f}" fill="{fill or "none"}" stroke="#253444" stroke-width="1"/>')

    def text(self, value, at, paper_height=3.2, align="left"):
        height = paper_height * self.scale
        entity = self.msp.add_text(value, dxfattribs={"height": height, "style": "RIVER_UNICODE", "layer": LAYERS["text"], "color": 7})
        entity.set_placement(at, align=TextEntityAlignment.MIDDLE_CENTER if align == "center" else TextEntityAlignment.MIDDLE_LEFT)
        self.svg_text(value, self.xy(at), paper_height * 4, align)

    def svg_text(self, value, point, height, align="left", dimension=None):
        anchor = "middle" if align == "center" else "start"
        attr = f' data-dimension-mm="{dimension:g}"' if dimension is not None else ""
        self.svg.append(f'<text x="{point[0]:.3f}" y="{point[1]:.3f}" font-size="{height:.3f}" text-anchor="{anchor}" dominant-baseline="middle" fill="#172536"{attr}>{html.escape(value)}</text>')

    def paper_poly(self, points, close=False):
        self.layout.add_lwpolyline(points, close=close, dxfattribs={"layer": LAYERS["sheet"], "color": 7})
        self.svg_poly([self.paper_xy(p) for p in points], close=close)

    def paper_text(self, value, at, height=3.2):
        entity = self.layout.add_text(value, dxfattribs={"height": height, "style": "RIVER_UNICODE", "layer": LAYERS["sheet_text"], "color": 7})
        entity.set_placement(at, align=TextEntityAlignment.MIDDLE_LEFT)
        self.svg_text(value, self.paper_xy(at), height * 4)

    def dim(self, a, b, base, angle=0):
        dimension = self.msp.add_linear_dim(base=base, p1=a, p2=b, angle=angle,
            dimstyle="EZDXF", override={"dimtxt": 2.8 * self.scale, "dimasz": 1.3 * self.scale,
                "dimgap": .7 * self.scale, "dimexo": .6 * self.scale, "dimexe": .7 * self.scale,
                "dimclrd": 7, "dimclre": 7, "dimclrt": 7, "dimdec": 0,
                "dimlfac": 1, "dimlunit": 2, "dimtad": 1, "dimtxsty": "RIVER_UNICODE"},
            dxfattribs={"layer": LAYERS["dimension"]})
        dimension.render()
        for entity in self.doc.blocks.get(dimension.dimension.dxf.geometry):
            entity.dxf.layer = LAYERS["dimension"]
        measure = abs(b[1] - a[1]) if angle == 90 else abs(b[0] - a[0])
        ends = [(base[0], a[1]), (base[0], b[1])] if angle == 90 else [(a[0], base[1]), (b[0], base[1])]
        self.svg_poly([self.xy(p) for p in ends])
        for point, end in zip((a, b), ends):
            self.svg_poly([self.xy(point), self.xy(end)], stroke="#667584", width=.6)
        tip1, tip2 = map(self.xy, ends)
        direction = (0, -1) if angle == 90 else (1, 0)
        for tip, sign in ((tip1, 1), (tip2, -1)):
            vx, vy = direction[0] * 5.2 * sign, direction[1] * 5.2 * sign
            self.svg_poly([tip, (tip[0] + vx + vy*.5, tip[1] + vy - vx*.5),
                           (tip[0] + vx - vy*.5, tip[1] + vy + vx*.5)], fill="#253444", close=True)
        middle = ((tip1[0] + tip2[0])/2, (tip1[1] + tip2[1])/2)
        label = (middle[0] - 26 if angle == 90 else middle[0], middle[1] if angle == 90 else middle[1] - 8)
        self.svg_text(f"{measure:g}", label, 11.2, "center", measure)

    def finish(self, stem, viewport_size, labels, dimensions):
        self.layout.add_viewport(center=self.origin, size=viewport_size,
            view_center_point=self.centre, view_height=viewport_size[1] * self.scale,
            dxfattribs={"layer": LAYERS["viewport"], "status": 2, "flags": 16384})
        self.doc.set_modelspace_vport(height=viewport_size[1] * self.scale, center=self.centre)
        dxf_path, svg_path = f"DXF/{stem}.dxf", f"output/svg/{stem}.svg"
        for path in (dxf_path, svg_path):
            (ROOT / path).parent.mkdir(parents=True, exist_ok=True)
        auditor = self.doc.audit()
        if auditor.has_errors:
            raise ValueError(f"Invalid river DXF: {auditor.errors}")
        self.doc.saveas(ROOT / dxf_path)
        source = ('<svg xmlns="http://www.w3.org/2000/svg" width="1680" height="1188" '
            f'viewBox="0 0 1680 1188" data-units="mm" data-revision="{REVISION}">'
            '<style>text{font-family:"Arial Unicode MS","Noto Sans JP",sans-serif}</style>'
            '<rect width="1680" height="1188" fill="#fff"/>' + "".join(self.svg) + "</svg>\n")
        (ROOT / svg_path).write_text(source, encoding="utf-8")
        return {"id": "plan" if stem.endswith("plan") else "section", "dxf": dxf_path, "svg": svg_path,
                "scale": self.scale, "dimensions_mm": dimensions, "required_labels": labels}


def plan():
    d = RiverDrawing("近郊河川モデル / 河川平面図", 1000, (120, 155))
    o, ys, bridge = section_offsets(), sample_ys(), bridge_dimensions()
    def band(left, right, layer, fill):
        points = [(center_x(y) + left, y) for y in ys] + [(center_x(y) + right, y) for y in reversed(ys)]
        d.poly(points, layer, fill)
    d.rect((-R.width/2, -R.length/2, R.width/2, R.length/2), "terrain", "#e1e9d2")
    for sign in (-1, 1):
        band(sign*o["path_inner"], sign*o["path_outer"], "path", "#dddcd6")
        band(sign*o["platform_outer"], sign*o["path_inner"], "terrain", "#acc790")
        band(sign*o["platform_inner"], sign*o["platform_outer"], "path", "#e1dacb")
        band(sign*o["water_edge"], sign*o["platform_inner"], "bank", "#c0c4bf")
    band(-R.water_width/2, R.water_width/2, "water", "#b2dce7")
    for tree in tree_positions():
        d.circle((tree["x"], tree["y"]), tree["radius"], fill="#e8bacb" if tree["kind"] == "sakura" else "#779f6b")
    for bench in bench_positions():
        d.rect((bench["x"]-450, bench["y"]-1000, bench["x"]+450, bench["y"]+1000), "furniture", "#bd936f")
    for lamp in lamp_positions():
        d.circle((lamp["x"], lamp["y"]), 500, "light", "#ffe2a0")
    for stairs in stairs_positions():
        x1, x2 = sorted((stairs["lower_x"], stairs["upper_x"]))
        d.rect((x1, stairs["y"]-stairs["width"]/2, x2, stairs["y"]+stairs["width"]/2), "stairs", "#d4d0c7")
        for i in range(1, stairs["risers"]):
            x = x1 + (x2-x1)*i/stairs["risers"]
            d.line((x, stairs["y"]-stairs["width"]/2), (x, stairs["y"]+stairs["width"]/2), "stairs")
    d.rect((bridge["start_x"], R.bridge_y-R.bridge_width/2, bridge["end_x"], R.bridge_y+R.bridge_width/2), "bridge", "#a6b4bd")
    d.text("人道橋", (center_x(R.bridge_y), R.bridge_y+6500), align="center")
    for y in (-65000, 62000):
        x = center_x(y)
        d.line((x, y+6000), (x, y-6000), "water", stroke="#335c6f", width=2)
        d.line((x, y-6000), (x-1600, y-3400), "water")
        d.line((x, y-6000), (x+1600, y-3400), "water")
    d.text("流下方向", (0, -35000), align="center")
    # Shared section station crosses the bridge, not an unrelated nominal channel.
    d.line((-R.width/2, R.bridge_y), (R.width/2, R.bridge_y), "axis", stroke="#a83c49")
    d.text("A", (-R.width/2-4500, R.bridge_y), align="center")
    d.text("A", (R.width/2+4500, R.bridge_y), align="center")
    d.text("歩道", (25000, 78000))
    d.text("石護岸", (-38000, 68000))
    d.text("親水階段", (24000, 48000))
    north_x = R.width/2 + 10000
    d.text("N", (north_x, 105000), paper_height=4, align="center")
    d.line((north_x, 93500), (north_x, 101000), "axis")
    d.line((north_x, 101000), (north_x-1700, 98000), "axis")
    d.line((north_x, 101000), (north_x+1700, 98000), "axis")
    d.dim((-R.width/2, R.length/2), (R.width/2, R.length/2), (0, R.length/2+7000))
    d.dim((-R.width/2, -R.length/2), (-R.width/2, R.length/2), (-R.width/2-12000, 0), 90)
    water_y = -10000
    cx = center_x(water_y)
    d.dim((cx-R.water_width/2, water_y), (cx+R.water_width/2, water_y), (0, water_y))
    d.dim((bridge["start_x"], R.bridge_y), (bridge["end_x"], R.bridge_y), (0, R.bridge_y-11000))
    d.dim((bridge["end_x"], R.bridge_y-R.bridge_width/2), (bridge["end_x"], R.bridge_y+R.bridge_width/2), (bridge["end_x"]+9000, 0), 90)
    path_y = -82000
    cx = center_x(path_y)
    d.dim((cx+o["path_inner"], path_y), (cx+o["path_outer"], path_y), (0, path_y-12000))
    d.paper_poly([(231, 252), (400, 252), (400, 58), (231, 58)], close=True)
    notes = ["日本近郊河川の参考景観", "", "01 河道・護岸・親水空間", f"モデル南北延長  {R.length:g} mm", f"モデル幅  {R.width:g} mm", f"常水面幅  {R.water_width:g} mm", f"河床  Z={R.bed_z:g} / 水面  Z=0", "", "02 歩道・人道橋", f"堤頂歩道幅  {R.path_width:g} mm", f"橋面  {bridge['span']:g} × {R.bridge_width:g} mm", "河道内橋脚なし（参考形状）", "親水階段は左右岸に各1か所", "", "03 図面の読み方", "A-A：橋中心位置の横断面", "X：東西 / Y：南北 / Z：高さ", "流れ：北から南（模式）", "CADモデル空間は実寸1:1", "DXFの文字・寸法は編集可能", "", "04 デモ仮定", "実在河川・測量地形ではない", "治水・橋梁耐力・地盤は未計算", "洪水位・河川占用等は未確定", "水面・地盤は水平の模式形状"]
    for i, text in enumerate(notes):
        if text:
            d.paper_text(text, (237, 241-i*6.4), 3.1)
    labels = ["近郊河川モデル", "河川平面図", "流下方向", "歩道", "人道橋", "石護岸", "親水階段", "デモ仮定"]
    return d.finish("river_demo_plan", (222, 224), labels,
                    [R.length, R.width, R.water_width, bridge["span"], R.bridge_width, R.path_width])


def section():
    bridge, cx = bridge_dimensions(), center_x(R.bridge_y)
    d = RiverDrawing("近郊河川モデル / A-A 横断面", 250, (210, 131), (cx, 0))
    points = [(cx-R.width/2, R.crest_z), *cross_section(R.bridge_y), (cx+R.width/2, R.crest_z)]
    # The fixed site edges, rather than a shifted rectangle, close the earth.
    points[0] = (-R.width/2, R.crest_z)
    points[-1] = (R.width/2, R.crest_z)
    d.poly([(-R.width/2, R.base_bottom_z), *points, (R.width/2, R.base_bottom_z)], "terrain", "#e5d8c3")
    bed_inner = section_offsets()["bed_inner"]
    d.poly([(cx-R.water_width/2, R.water_z), (cx-bed_inner, R.bed_z),
            (cx+bed_inner, R.bed_z), (cx+R.water_width/2, R.water_z)], "water", "#b2dce7")
    d.rect((bridge["start_x"], bridge["underside_z"], bridge["end_x"], R.bridge_top_z), "bridge", "#a6b4bd")
    d.rect((bridge["start_x"], bridge["beam_bottom_z"], bridge["end_x"], bridge["underside_z"]), "bridge", "#687d8b")
    for x in (bridge["start_x"], bridge["end_x"]):
        d.rect((x-650, R.terrain_bottom_z, x+650, bridge["beam_bottom_z"]), "bridge", "#bbc0ba")
    d.dim((-R.width/2, R.crest_z), (R.width/2, R.crest_z), (0, 21000))
    d.dim((bridge["start_x"], R.bridge_top_z), (bridge["end_x"], R.bridge_top_z), (0, 13000))
    d.dim((cx-R.water_width/2, R.water_z), (cx+R.water_width/2, R.water_z), (0, -14000))
    d.dim((cx+25000, R.water_z), (cx+25000, R.crest_z), (cx+29000, 0), 90)
    d.dim((cx-3000, R.bed_z), (cx-3000, R.water_z), (cx-7000, 0), 90)
    d.text("水面 Z=0", (cx-5000, -7500), paper_height=3.4)
    d.text(f"河床 Z={R.bed_z:g}", (cx-5000, -10000), paper_height=3.4)
    d.text(f"歩道 Z={R.crest_z:g}", (cx+19000, 6500), paper_height=3.4)
    d.text(f"橋面 Z={R.bridge_top_z:g}", (cx-12000, 6500), paper_height=3.4)
    d.paper_text(f"横断位置 Y={R.bridge_y:g} mm / 橋中心 / 水平方向・鉛直方向とも1:250（鉛直倍率なし）", (18, 243), 3.4)
    d.paper_text("西（右岸）", (35, 227), 3.4)
    d.paper_text("東（左岸）", (341, 227), 3.4)
    d.paper_poly([(18, 62), (401, 62)])
    notes = ["デモ仮定：全寸法・高さ・水位・護岸厚は参考値。", "水面 Z=0 は任意の基準であり、海抜・計画高水位を示さない。", "河床・堤防は横断形の模式モデル。河床勾配・流量・洪水流下能力は未設定。", "橋梁断面、橋台・基礎の耐力、洗掘および河川法上の許可条件は未計算・未確定。"]
    for i, text in enumerate(notes):
        d.paper_text(text, (18, 53-i*7.2), 3.1)
    return d.finish("river_demo_section", (394, 226),
        ["A-A 横断面", "水面 Z=0", f"河床 Z={R.bed_z:g}", f"歩道 Z={R.crest_z:g}", "デモ仮定"],
        [R.width, R.water_width, bridge["span"], R.crest_z-R.water_z, R.water_z-R.bed_z])


def generate():
    drawings = [plan(), section()]
    paths = [d[key] for d in drawings for key in ("dxf", "svg")]
    sources = ["src/lib/river_geometry.py", "src/generate_river_plans.py"]
    digest = lambda p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
    metadata = {"schema_version": 1, "revision": REVISION, "units": "mm", "status": "concept_demo_only",
        "source_geometry_revision": REVISION,
        "source_sha256": {p: digest(p) for p in sources},
        "artifacts": {p: {"sha256": digest(p), "bytes": (ROOT/p).stat().st_size} for p in paths},
        "drawings": drawings}
    path = ROOT / "output/review/river_demo_drawings.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({"revision": REVISION, "outputs": paths}, ensure_ascii=False))


if __name__ == "__main__":
    generate()
