"""A3 sheet furniture shared by editable DXF layouts and print PDFs.

Dimensions below are paper millimetres. The house remains in modelspace at
1:1; the locked viewport is the only place where the 1:50 scale is applied.
Tokyo's civil CAD standard (April 2024), clauses 1-4-3 and 1-4-4 / figure
1-3, is adapted here for a residential concept drawing. This is not an SXF
electronic-delivery implementation or a statutory architectural design.
"""
from __future__ import annotations

from dataclasses import dataclass
import unicodedata

from ezdxf.enums import TextEntityAlignment
from ezdxf.lldxf import const
from reportlab.lib.units import mm

from .house_plan import P

PAPER_SIZE = (420.0, 297.0)
FRAME_BOUNDS = (7.5, 7.5, 412.5, 289.5)
TITLE_BOUNDS = (352.5, 7.5, 412.5, 52.5)
LAYOUT_NAME = "JP_A3_1_50"
MODEL_PAPER_ORIGIN = (37.0, 76.0)
MODEL_SCALE = 50.0
FRAME_LAYER = "D-TTL-FRAM"
TABLE_LAYER = "D-TTL-LINE"
TITLE_TEXT_LAYER = "D-TTL-TXT"
NOTE_LAYER = "D-DOC-TXT"
VIEWPORT_LAYER = "D-TTL-VPRT"
FONT_HEIGHTS = (1.8, 2.5, 3.5, 5.0)


def _text_width(text, height):
    """Conservative paper width for Japanese full-width and Roman glyphs."""
    return height * sum(1.0 if unicodedata.east_asian_width(c) in "WF" else .6
                        for c in text)


def _wrap(text, width, height):
    lines, current = [], ""
    for char in text:
        if char == "\n":
            lines.append(current)
            current = ""
        elif current and _text_width(current + char, height) > width:
            lines.append(current)
            current = char
        else:
            current += char
    if current:
        lines.append(current)
    return lines or [""]


@dataclass
class _DxfSheet:
    layout: object
    font_style: str

    def line(self, a, b, width=.13, layer=TABLE_LAYER):
        return self.layout.add_line(a, b, dxfattribs={
            "layer": layer, "color": 7, "linetype": "Continuous",
            "lineweight": round(width * 100),
        })

    def rect(self, bounds, width=.13, layer=TABLE_LAYER, role=None):
        x1, y1, x2, y2 = bounds
        entity = self.layout.add_lwpolyline(
            [(x1, y1), (x2, y1), (x2, y2), (x1, y2)], close=True,
            dxfattribs={"layer": layer, "color": 7,
                        "linetype": "Continuous", "lineweight": round(width * 100)})
        if role:
            entity.set_xdata("JP_SHEET", [(1000, role)])
        return entity

    def text(self, value, at, height=2.5, align="left", layer=NOTE_LAYER):
        if height not in FONT_HEIGHTS:
            raise ValueError(f"Unsupported standard text height: {height}")
        entity = self.layout.add_text(value, dxfattribs={
            "layer": layer, "style": self.font_style, "height": height,
            "color": 7, "linetype": "Continuous", "lineweight": 13,
        })
        alignment = {"left": TextEntityAlignment.MIDDLE_LEFT,
                     "center": TextEntityAlignment.MIDDLE_CENTER,
                     "right": TextEntityAlignment.MIDDLE_RIGHT}[align]
        entity.set_placement(at, align=alignment)
        return entity


@dataclass
class _PdfSheet:
    canvas: object
    font_name: str

    def line(self, a, b, width=.13, layer=TABLE_LAYER):
        self.canvas.setStrokeColorRGB(0, 0, 0)
        self.canvas.setLineWidth(width * mm)
        self.canvas.line(a[0] * mm, a[1] * mm, b[0] * mm, b[1] * mm)

    def rect(self, bounds, width=.13, layer=TABLE_LAYER, role=None):
        x1, y1, x2, y2 = bounds
        self.canvas.setStrokeColorRGB(0, 0, 0)
        self.canvas.setLineWidth(width * mm)
        self.canvas.rect(x1 * mm, y1 * mm, (x2-x1) * mm, (y2-y1) * mm,
                         stroke=1, fill=0)

    def text(self, value, at, height=2.5, align="left", layer=NOTE_LAYER):
        if height not in FONT_HEIGHTS:
            raise ValueError(f"Unsupported standard text height: {height}")
        self.canvas.setFillColorRGB(0, 0, 0)
        self.canvas.setFont(self.font_name, height * mm)
        # Both outputs use middle alignment; this baseline accommodates the
        # Japanese glyph em-box rather than the Roman cap-height alone.
        x, y = at[0] * mm, (at[1] - .32 * height) * mm
        draw = {"left": self.canvas.drawString,
                "center": self.canvas.drawCentredString,
                "right": self.canvas.drawRightString}[align]
        draw(x, y, value)


def _cell(sheet, text, bounds, height=1.8, layer=TITLE_TEXT_LAYER):
    x1, y1, x2, y2 = bounds
    lines = _wrap(text, x2-x1-2, height)
    spacing = height * 1.4
    if len(lines) * spacing > y2-y1:
        raise ValueError(f"Text exceeds cell height without reducing font: {text}")
    first_y = (y1+y2)/2 + (len(lines)-1)*spacing/2
    for index, line in enumerate(lines):
        sheet.text(line, ((x1+x2)/2, first_y-index*spacing), height,
                   "center", layer)


def _title_block(sheet, floor):
    """Figure 1-3: 60 x 45, 14/46 columns and 12.5-wide number area."""
    x1, y1, x2, y2 = TITLE_BOUNDS
    split, number_x = x1+14, x2-12.5
    sheet.rect(TITLE_BOUNDS, role="title_block")
    for y in (45.5, 38.5, 31.5, 22.5):
        sheet.line((x1, y), (x2, y))
    for y in (15.5, 11.5):
        sheet.line((x1, y), (number_x, y))
    sheet.line((split, 11.5), (split, y2))
    sheet.line((number_x, y1), (number_x, 22.5))
    sheet.line((number_x, 18.5), (x2, 18.5))
    for label, value, bottom, top in (
        ("施設名", "住宅参考", 45.5, 52.5),
        ("工事件名", "日本一戸建て計画", 38.5, 45.5),
        ("工事箇所", "未定", 31.5, 38.5),
        ("図面名称", f"{floor.number}階平面図", 22.5, 31.5),
    ):
        _cell(sheet, label, (x1, bottom, split, top))
        _cell(sheet, value, (split, bottom, x2, top))
    _cell(sheet, "縮尺", (x1, 15.5, split, 22.5))
    _cell(sheet, "1:50", (split, 15.5, number_x, 22.5), 2.5)
    _cell(sheet, "作製年月日", (x1, 11.5, split, 15.5))
    _cell(sheet, "令和8年10月7日", (split, 11.5, number_x, 15.5))
    _cell(sheet, "事業所名　未定", (x1, y1, number_x, 11.5))
    _cell(sheet, "図面番号", (number_x, 18.5, x2, 22.5))
    sheet.text(f"{floor.number:03d}", ((number_x+x2)/2, 14.8), 2.5,
               "center", TITLE_TEXT_LAYER)
    sheet.text("全2枚", ((number_x+x2)/2, 10.2), 1.8,
               "center", TITLE_TEXT_LAYER)


def _draw_sheet(sheet, floor):
    sheet.rect(FRAME_BOUNDS, .7, FRAME_LAYER, "frame")
    sheet.text(f"{floor.number}階平面図", (112.8, 260), 5.0, "center", TITLE_TEXT_LAYER)
    sheet.text("R19参考平面　1:50　単位 mm", (112.8, 249), 2.5, "center")
    sheet.text("室別面積表（内法）", (230, 262), 3.5)

    left, right, divide, top, row_h = 230, 400, 352, 250, 7
    bottom = top - row_h * (len(floor.rooms) + 1)
    sheet.rect((left, bottom, right, top))
    sheet.line((divide, bottom), (divide, top))
    _cell(sheet, "室名", (left, top-row_h, divide, top), 2.5, NOTE_LAYER)
    _cell(sheet, "面積（m²）", (divide, top-row_h, right, top), 2.5, NOTE_LAYER)
    for index, room in enumerate(floor.rooms):
        yt = top - row_h * (index + 1)
        yb = yt - row_h
        sheet.line((left, yt), (right, yt))
        label = room.name + ("（階段室）" if room.kind == "stair" else "")
        sheet.text(label, (left+3, (yb+yt)/2), 2.5)
        sheet.text(f"{room.area:.2f}", (right-3, (yb+yt)/2), 2.5, "right")

    sheet.text("注意事項・仮定条件", (230, 177), 3.5)
    notes = [
        f"建物外形 {P.width:,.0f}×{P.depth:,.0f}、階高 {P.storey_height:,.0f} mm はデモ用の仮定寸法。",
        f"外壁 {P.external_wall:.0f}、内壁 {P.internal_wall:.0f} mm。家具・建具の寸法は計画上の仮定。",
        "R19：便所南壁を揃え、収納壁撤去・寝室入口・灯具を修正。",
        "面積は壁内法の概算で家具占有分を含む。建築確認申請の面積ではない。",
        "廊下面積は階段を除く。階段面積は階段室の確保範囲を示す。",
        f"階段：{P.risers}R×{P.storey_height/P.risers:.0f}、T{P.tread:.0f}、階段幅 {P.stair_width:.0f}、踊場 {P.stair_landing:.0f} mm。",
        "対面キッチン2550×650・背面通路900。小屋裏北側換気窓600×300は仮定。",
        "南LDK窓H2200、2寝室は引違い戸H2100。ガラス・防水・耐力は未設計。",
        "便所：内法 900×1,820 mm。出入口 700 mm は枠厚を控除する前の寸法。",
        "構造・防火・耐震・法令適合は未検証。施工図として使用不可。",
        "東京都土木CAD製図基準（令和6年4月）を住宅の図式に準用。",
        "南側バルコニー8190×1000は仮定。柱なし・ポーチ先端300露出。耐力・防水・排水は未設計。",
    ]
    y = 168
    for index, note in enumerate(notes, 1):
        lines = _wrap(f"{index:02d}. {note}", 170, 2.5)
        for line in lines:
            sheet.text(line, (230, y), 2.5)
            y -= 4.4
        y -= .6

    sheet.text("凡例", (230, 95), 3.5)
    for value, y in (
        ("実線：壁・建具・家具の平面輪郭", 87),
        ("寸法線：壁内法・建物外形・建具開口幅", 81),
        ("D01 等：建具番号　UP：上り方向", 75),
        ("北矢印：仮定方位　R19：左右反転・対面キッチン・北側換気窓・構造未計算", 69),
    ):
        sheet.text(value, (230, y), 2.5)
    _title_block(sheet, floor)


def add_paper_layout(doc, floor, font_style="HOUSE_UNICODE"):
    """Return the named A3 DXF layout with editable text and locked viewport."""
    if font_style not in doc.styles:
        raise ValueError(f"DXF text style must be registered first: {font_style}")
    if "JP_SHEET" not in doc.appids:
        doc.appids.new("JP_SHEET")
    for name, weight, plot in (
        (FRAME_LAYER, 70, True), (TABLE_LAYER, 13, True),
        (TITLE_TEXT_LAYER, 13, True), (NOTE_LAYER, 13, True),
        (VIEWPORT_LAYER, 13, False),
    ):
        layer = doc.layers.get(name) if name in doc.layers else doc.layers.new(name)
        layer.dxf.color = 7
        layer.dxf.linetype = "Continuous"
        layer.dxf.lineweight = weight
        layer.dxf.plot = int(plot)
        layer.dxf.discard("true_color")
    if LAYOUT_NAME in doc.layouts:
        doc.layouts.delete(LAYOUT_NAME)
    layout = doc.layouts.new(LAYOUT_NAME)
    layout.page_setup(size=PAPER_SIZE, margins=(0, 0, 0, 0), units="mm",
                      offset=(0, 0), rotation=0, scale=(1, 1), name="ISO_A3",
                      device="")
    # The automatically created id=1 viewport describes the paper itself.
    # Keep its administrative entity on the same non-plotting layer.
    for paper_viewport in layout.query("VIEWPORT"):
        paper_viewport.dxf.layer = VIEWPORT_LAYER
    _draw_sheet(_DxfSheet(layout, font_style), floor)
    vp_min, vp_max = (18.0, 20.0), (225.0, 245.0)
    center = tuple((a+b)/2 for a, b in zip(vp_min, vp_max))
    size = tuple(b-a for a, b in zip(vp_min, vp_max))
    model_center = tuple((p-o)*MODEL_SCALE for p, o in zip(center, MODEL_PAPER_ORIGIN))
    viewport = layout.add_viewport(
        center=center, size=size, view_center_point=model_center,
        view_height=size[1]*MODEL_SCALE,
        dxfattribs={"layer": VIEWPORT_LAYER, "flags": const.VSF_LOCK_ZOOM,
                    "view_target_point": (0, 0, 0),
                    "view_direction_vector": (0, 0, 1), "ucs_icon": 0},
    )
    viewport.set_xdata("JP_SHEET", [(1000, "model_viewport"), (1040, MODEL_SCALE)])
    doc.layouts.set_active_layout(LAYOUT_NAME)
    doc.header["$TILEMODE"] = 0
    doc.header["$LWDISPLAY"] = True
    return layout


def draw_pdf_sheet(canvas, floor, font_name="HouseUnicode"):
    """Draw exactly the same sheet furniture in paper millimetres on a PDF."""
    canvas.saveState()
    try:
        _draw_sheet(_PdfSheet(canvas, font_name), floor)
    finally:
        canvas.restoreState()
