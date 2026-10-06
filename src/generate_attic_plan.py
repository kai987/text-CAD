"""Generate a supplemental editable attic plan from the same R04 parameters.

The approved R02 two-floor sheets are not rewritten. Units are millimetres;
all attic dimensions and storage purpose are demonstration assumptions.
"""
from pathlib import Path
import math

import ezdxf
from ezdxf.lldxf import const
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from generate_plans import Drawing, FONT
from lib.house_plan import P
from lib.house_geometry import G
from lib.attic_geometry import A, attic_dimensions, attic_manifest

ROOT = Path(__file__).resolve().parents[1]


def generate():
    out = ROOT / 'output/pdf/house_attic_plan_R04_JP.pdf'
    out.parent.mkdir(parents=True, exist_ok=True)
    pdfmetrics.registerFont(TTFont('HouseUnicode', str(FONT)))
    pdf = canvas.Canvas(str(out), pagesize=(420*mm, 297*mm))
    pdf.setTitle('小屋裏収納 補足計画図 R04 / Storage attic demonstration')
    pdf.setAuthor('text-CAD')
    drawing = Drawing(pdf)
    # Paper dash lengths × 50: setup's inch-based defaults are too short here.
    drawing.doc.linetypes.new('ATTIC_DEPLOYED', dxfattribs={'description':'2/1 mm at 1:50', 'pattern':[150,100,-50]})
    drawing.doc.linetypes.new('ATTIC_HEIGHT', dxfattribs={'description':'1/1 mm at 1:50', 'pattern':[100,50,-50]})
    drawing.doc.linetypes.new('ATTIC_RIDGE', dxfattribs={'description':'3/1/0.5/1 mm at 1:50', 'pattern':[275,150,-50,25,-50]})
    drawing.doc.header['$PSLTSCALE'] = 0
    drawing.doc.ezdxf_metadata()['REVISION'] = 'R04-ATTIC'
    drawing.doc.ezdxf_metadata()['SCOPE'] = '小屋裏収納の補足デモ計画。確認済み1・2階図面は変更しない。'
    d = attic_dimensions(P, G)
    m = attic_manifest(P, G)
    x0, x1 = d['deck_left'], d['deck_right']
    y0, y1 = A.deck_end_inset, P.depth - A.deck_end_inset
    hatch = (A.hatch_x, A.hatch_y, d['hatch_right'], d['hatch_north'])
    drawing.text('小屋裏収納 補足計画図 / R04', (0, 10800), 250, align='left')
    drawing.text('単位 mm / A3・1:50 / 全寸法はデモ仮定 / 2026-10-06', (0, 10300), 125, align='left')
    drawing.rect((0, 0, P.width, P.depth), 'WALL')
    drawing.rect((x0, y0, x1, y1), 'WALL')
    drawing.rect(hatch, 'DOOR')
    drawing.text('小屋裏収納（デモ）', (3640, 2450), 175)
    drawing.text('板面 3680 × 6880', (3640, 2150), 125)
    drawing.text(f'開口控除後の投影 {m["storage_projection_area_m2"]:.4f} m²', (3640, 1825), 125)
    drawing.text('※ 法定面積ではない', (3640, 1550), 125)
    drawing.text('N', (7700, 7150), 175)
    drawing.line((7700, 6650), (7700, 7000))
    drawing.line((7700, 7000), (7600, 6850))
    drawing.line((7700, 7000), (7800, 6850))
    for side, shelf_x in [('西', x0+100), ('東', x1-100-A.shelf_width)]:
        shelf_y = P.depth - A.shelf_north_inset - A.shelf_depth
        drawing.rect((shelf_x, shelf_y, shelf_x+A.shelf_width, shelf_y+A.shelf_depth))
        drawing.text(f'{side}棚 H650', (shelf_x+A.shelf_width/2, shelf_y+750), 100)
    for box_x in (x0+A.storage_box_side_inset, x1-A.storage_box_side_inset-A.storage_box_width):
        drawing.rect((box_x, A.storage_box_y, box_x+A.storage_box_width, A.storage_box_y+A.storage_box_depth))
        drawing.text('箱 H450', (box_x+225, A.storage_box_y+300), 90)
    # Dashed projection of the ladder and its bottom standing area on 2F.
    pdf.saveState()
    pdf.setDash(2*mm, 1*mm)
    before = set(drawing.msp)
    drawing.rect(m['ladder']['deployed_plan_bounds_mm'], 'STAIR')
    drawing.rect(m['ladder']['bottom_landing_bounds_mm'], 'STAIR')
    for e in drawing.msp:
        if e not in before:
            e.dxf.linetype = 'ATTIC_DEPLOYED'
    pdf.restoreState()
    drawing.line((d['ladder_foot_x'], d['ladder_center_y']), (d['hatch_right'], d['ladder_center_y']), 'STAIR')
    drawing.text('検修口 1200 × 650', (6250, 3650), 115)
    drawing.line((4800, 3650), (hatch[2], 3830), 'DOOR')
    drawing.text('破線：展開梯子・2階立ち位置', (3600, 3150), 105)
    # Ridge and clear-height 1800 mm boundary as editable reference lines.
    pdf.saveState(); pdf.setDash([3*mm, 1*mm, .5*mm, 1*mm])
    drawing.line((3640, 5200), (3640, y1), 'DIM'); pdf.restoreState()
    list(drawing.msp)[-1].dxf.linetype = 'ATTIC_RIDGE'
    threshold_x = (1800+A.lining_vertical_allowance+A.deck_thickness) / math.tan(math.radians(G.roof_pitch_degrees))
    for x in (threshold_x, P.width-threshold_x):
        pdf.saveState(); pdf.setDash(1*mm, 1*mm)
        drawing.line((x, 4400), (x, y1), 'DIM'); pdf.restoreState()
        list(drawing.msp)[-1].dxf.linetype = 'ATTIC_HEIGHT'
    drawing.text('中央点線間のみ CH ≥ 1800', (3640, 5100), 105)
    drawing.dim((0, P.depth), (P.width, P.depth), (0, 8300))
    drawing.dim((x0, y1), (x1, y1), (0, 7700))
    drawing.dim((0, 0), (0, P.depth), (-900, 0), 90)
    drawing.dim((x0, y0), (x0, y1), (x0-350, 0), 90)
    drawing.dim((hatch[0], hatch[3]), (hatch[2], hatch[3]), (0, hatch[3]+450))
    drawing.dim((hatch[2], hatch[1]), (hatch[2], hatch[3]), (hatch[2]+400, 0), 90)
    # Roof cross-section uses local height above Z5600, drawn at the same scale.
    sx, sy = 9000, 5950
    drawing.text('参考断面（東西）/ 屋根外形は維持', (sx, sy+3000), 175, align='left')
    ridge = P.width/2*math.tan(math.radians(G.roof_pitch_degrees))
    drawing.line((sx, sy), (sx+3640, sy+ridge), 'WALL')
    drawing.line((sx+3640, sy+ridge), (sx+7280, sy), 'WALL')
    drawing.line((sx+x0, sy+18), (sx+x1, sy+18), 'WALL')
    edge_top = 18+m['clear_height_mm']['deck_edge']
    drawing.line((sx+x0, sy+18), (sx+x0, sy+edge_top), 'WALL')
    drawing.line((sx+x1, sy+18), (sx+x1, sy+edge_top), 'WALL')
    drawing.line((sx+x0, sy+edge_top), (sx+3640, sy+ridge-50), 'WALL')
    drawing.line((sx+3640, sy+ridge-50), (sx+x1, sy+edge_top), 'WALL')
    drawing.text('板面 Z=5618', (sx+3640, sy-350), 125)
    drawing.text(f'中央 CH ≈ {m["clear_height_mm"]["ridge"]:.0f}', (sx+3640, sy+1000), 125)
    drawing.text(f'両側 CH ≈ {m["clear_height_mm"]["deck_edge"]:.0f}', (sx+3640, sy+650), 125)
    notes = [
        '収納用デモ。居室・第3階の確定計画ではない。',
        '確認済み1・2階平面とR03屋根外形を維持。',
        'CH：板面から内張りまで。50は鉛直表示余裕。',
        '検修梯子：幅600・65°・高さ2818・踏板10枚。',
        '2階廊下に展開。展開中は通行を占有する。',
        '入口蓋と梯子は命名済み。入口組を独立表示。',
        '梁・耐荷重・構造接合・断熱換気は未設計。',
        '実使用の頭上空間・避難・法規は未検証。',
        '本図は補足図。既存R02図面を書き換えない。',
    ]
    for i, note in enumerate(notes):
        drawing.text(note, (9200, 4400-i*350), 125, align='left')
    # Same model-space graphics in the PDF and a locked editable A3 viewport.
    pdf.setLineWidth(.7*mm); pdf.rect(7.5*mm, 7.5*mm, 405*mm, 282*mm)
    drawing.doc.layers.new('D-TTL-FRAM', dxfattribs={'color':7,'lineweight':70})
    drawing.doc.layers.new('D-TTL-VPRT', dxfattribs={'color':7,'plot':0})
    layout = drawing.doc.layouts.new('ATTIC_A3_1_50')
    layout.page_setup(size=(420, 297), margins=(0,0,0,0), units='mm')
    layout.add_lwpolyline([(7.5,7.5),(412.5,7.5),(412.5,289.5),(7.5,289.5)], close=True,
                          dxfattribs={'layer':'D-TTL-FRAM'})
    layout.add_viewport(center=(210,148.5),size=(400,278),
        view_center_point=((210-38)*50,(148.5-55)*50), view_height=278*50,
        dxfattribs={'layer':'D-TTL-VPRT','flags':const.VSF_LOCK_ZOOM})
    drawing.doc.layouts.set_active_layout('ATTIC_A3_1_50')
    drawing.doc.header['$TILEMODE'] = 0
    drawing.doc.saveas(ROOT/'DXF/house_attic_plan.dxf')
    pdf.showPage(); pdf.save()
    print(f'Saved {out} and DXF/house_attic_plan.dxf')


if __name__ == '__main__':
    generate()
