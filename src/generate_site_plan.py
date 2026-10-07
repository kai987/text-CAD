"""Editable R11 site supplement, sharing the native model's millimetre parameters.

The approved R10 floor plans and attic plan are not regenerated. Main plan
is A3 / 1:100. The explicitly labelled conceptual section is enlarged to 1:25.
"""
from pathlib import Path

import ezdxf
from ezdxf import disassemble
from ezdxf.lldxf import const
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from generate_plans import Drawing, FONT
from lib.jp_drafting import LAYERS, PENS_MM
from lib.house_plan import P, floor_plan
from lib.house_geometry import G
from lib.exterior_geometry import E
from lib.site_geometry import S, site_dimensions, fence_layout

from lib.orientation import canonical
P=canonical(P)

ROOT = Path(__file__).resolve().parents[1]


class SiteDrawing(Drawing):
    def __init__(self, pdf):
        super().__init__(pdf)
        self.scale = mm / 100
        self.ox, self.oy = 70 * mm, 105 * mm
        metadata = self.doc.ezdxf_metadata()
        metadata['REVISION'] = 'R22-SITE'
        metadata['SCALE'] = '1:100; labelled conceptual foundation section 1:25'
        metadata['SCOPE'] = '外構・基礎のデモ補足計画。敷地測量・構造設計・施工図ではない。'
        self.doc.header['$PSLTSCALE'] = 0
        self.doc.linetypes.new('SITE_DASH', dxfattribs={
            'description': '2/1 mm paper at 1:100', 'pattern': [300, 200, -100]})

    def dim(self, p1, p2, base, angle=0):
        p1,p2,base=self.orient_dim(p1,p2,base,angle)
        dim = self.msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=angle,
            dimstyle='EZDXF', override={
                'dimtxt': 250, 'dimasz': 150, 'dimgap': 150, 'dimexo': 100,
                'dimexe': 100, 'dimclrd': 7, 'dimclre': 7, 'dimclrt': 7,
                'dimlwd': 13, 'dimlwe': 13, 'dimblk': ezdxf.ARROWS.closed_filled,
                'dimtxsty': 'HOUSE_UNICODE', 'dimdec': 0, 'dimtad': 1,
                'dimlfac': 1, 'dimlunit': 2}, dxfattribs={'layer': LAYERS['DIM']})
        dim.render()
        for entity in self.doc.blocks.get(dim.dimension.dxf.geometry):
            entity.dxf.layer = LAYERS['DIM']
        self.pdf.setStrokeColorRGB(0, 0, 0)
        self.pdf.setFillColorRGB(0, 0, 0)
        self.pdf.setLineWidth(PENS_MM['DIM'] * mm)
        for entity in disassemble.recursive_decompose(dim.dimension.virtual_entities()):
            kind = entity.dxftype()
            if kind == 'LINE':
                self.pdf.line(*self.xy(entity.dxf.start), *self.xy(entity.dxf.end))
            elif kind in ('SOLID', 'LWPOLYLINE'):
                points = list(entity.wcs_vertices()) if kind == 'SOLID' else list(entity.get_points('xy'))
                path = self.pdf.beginPath(); path.moveTo(*self.xy(points[0]))
                for point in points[1:]: path.lineTo(*self.xy(point))
                if kind == 'SOLID' or entity.closed: path.close()
                self.pdf.drawPath(path, fill=kind == 'SOLID', stroke=kind != 'SOLID')
            elif kind == 'MTEXT':
                self.pdf.saveState(); self.pdf.translate(*self.xy(entity.dxf.insert))
                self.pdf.rotate(entity.get_rotation())
                height = entity.dxf.char_height * self.scale
                self.pdf.setFont('HouseUnicode', height)
                self.pdf.drawCentredString(0, -height * .32, entity.plain_text())
                self.pdf.restoreState()

    def circle(self, at, radius):
        at=self.orient_point(at)
        self.msp.add_circle(at, radius, dxfattribs={'layer': LAYERS['FURNITURE']})
        self.pdf.setLineWidth(PENS_MM['FURNITURE'] * mm)
        self.pdf.circle(*self.xy(at), radius * self.scale, stroke=1, fill=0)


def generate():
    out = ROOT / 'output/pdf/house_site_plan_R05_JP.pdf'
    out.parent.mkdir(parents=True, exist_ok=True)
    pdfmetrics.registerFont(TTFont('HouseUnicode', str(FONT)))
    pdf = canvas.Canvas(str(out), pagesize=(420 * mm, 297 * mm), invariant=1)
    pdf.setTitle('外構・基礎 補足計画図 R22 / Site and foundation demonstration')
    pdf.setAuthor('text-CAD')
    d = site_dimensions(P, G)
    fence = fence_layout(p=P)
    drawing = SiteDrawing(pdf)
    drawing.text('外構・基礎 補足計画図 / R22', (-4500, 15500), 500, align='left')
    drawing.text('単位 mm / 配置 1:100 / A3 / 全寸法・方位・敷地はデモ仮定 / 2026-10-07',
                 (-4500, 14600), 250, align='left')
    drawing.text('01 配置図', (-2000, 11500), 350, align='left')
    drawing.mirror_width=P.width
    drawing.rect(d['lot'], 'WALL')
    drawing.rect(d['building'], 'WALL')
    drawing.text('一戸建て（確認済み平面）', (P.width/2, 4300), 300)
    drawing.text(f'外形 {P.width:g} × {P.depth:g}', (P.width/2, 3650), 250)
    drawing.text('1階仕上げ床 Z=0', (P.width/2, 3000), 250)
    # 2F balcony projection is distinguished from ground-level site solids.
    from lib.house_plan import dimensions
    bx=dimensions(P)['bx']
    pdf.saveState(); pdf.setDash(2*mm,1*mm)
    before=set(drawing.msp)
    drawing.rect((bx,-P.balcony_depth,bx+P.balcony_width,0),'DOOR')
    for entity in drawing.msp:
        if entity not in before:entity.dxf.linetype='SITE_DASH'
    pdf.restoreState()
    drawing.text('2階バルコニー投影',(bx+P.balcony_width/2,-700),250)

    for part in ('porch', 'upper_step', 'lower_step', 'path'):
        drawing.rect(d[part], 'DOOR')
    entrance=next(door for door in floor_plan(1,P).doors if door.a=='outside')
    entry_x=entrance.start+entrance.width/2
    drawing.line((entrance.start, 0), (entrance.start+entrance.width, 0), 'DOOR')
    drawing.text('入口', (entry_x, 650), 250)
    drawing.text('歩道', (entry_x, -2950), 250)
    drawing.text(f'W{d["path"][2]-d["path"][0]:g}', (entry_x, -3400), 250)
    drawing.rect(d['parking'], 'FURNITURE')
    pdf.saveState(); pdf.setDash(2 * mm, 1 * mm)
    before = len(list(drawing.msp))
    drawing.rect(d['parking_bay'], 'FURNITURE')
    for e in list(drawing.msp)[before:]: e.dxf.linetype = 'SITE_DASH'
    pdf.restoreState()
    for i,(left,bottom,right,top) in enumerate(d['parking_bays'],1):
        middle=(left+right)/2
        drawing.line((left,bottom),(left,top),'FURNITURE')
        drawing.text(f'駐車 {i}',(middle,-2850),250)
        drawing.text('2800 × 5000',(middle,-3300),250)
        # Vehicle boxes are optional-use demonstrations, not swept-path results.
        drawing.rect((middle-900,bottom+100,middle+900,bottom+4600),'FURNITURE')
        for x in (left+300,right-300-S.wheel_stop_width):
            drawing.rect((x,top-350,x+S.wheel_stop_width,top-350+S.wheel_stop_depth))
    from lib.balcony_geometry import support_positions,B
    for x in support_positions(P):
        y=-P.balcony_depth+P.balcony_rail_thickness/2
        h=B.footing_width/2
        drawing.rect((x-h,y-h,x+h,y+h),'FURNITURE')
        drawing.rect((x-50,y-50,x+50,y+50),'WALL')
    for name,bounds in d['lawns'].items():
        drawing.rect(bounds)
    for x, y, r in d['shrubs']: drawing.circle((x, y), r)
    for panel in fence['panels']:
        a, b = ((panel['start'], panel['at']), (panel['end'], panel['at'])) if panel['axis'] == 'h' else (
            (panel['at'], panel['start']), (panel['at'], panel['end']))
        drawing.line(a, b, 'WALL')
    for post in fence['posts']:
        half = S.fence_post_width / 2
        drawing.rect((post['x']-half, post['y']-half, post['x']+half, post['y']+half), 'WALL')
    drawing.text(f'敷地外形 {(S.lot_east-S.lot_west)*(S.lot_north-S.lot_south)/1e6:.4f} m²（幾何面積）', (P.width/2, -6900), 250)
    drawing.text('南側アクセスを仮定 / 道路・境界条件は未確定', (P.width/2, -7400), 250)
    drawing.dim((S.lot_west, S.lot_north), (S.lot_east, S.lot_north), (0, 10180))
    drawing.dim((S.lot_west,S.lot_south),(S.lot_west,S.lot_north),(S.lot_west-1000,0),90)
    drawing.dim((0, P.depth), (P.width, P.depth), (0, 7540))
    drawing.dim((S.car_opening_west,S.fence_south),(S.car_opening_east,S.fence_south),(0,-6100))
    drawing.dim((S.pedestrian_opening_west, -5300), (S.pedestrian_opening_east, -5300), (0, -6100))
    drawing.text('車両開口', ((S.car_opening_west+S.car_opening_east)/2,-6500),250)
    drawing.text('歩行開口', (entry_x, -6500), 250)
    nx=S.lot_east+500; ny=S.lot_north+900
    drawing.text('N*',(nx,ny),300)
    drawing.line((nx,ny-1400),(nx,ny-550),'NORTH')
    drawing.line((nx,ny-550),(nx-200,ny-900),'NORTH')
    drawing.line((nx,ny-550),(nx+200,ny-900),'NORTH')

    drawing.mirror_width=None
    drawing.text('02 基礎参考断面 / 1:25（模式図）', (12600, 11500), 350, align='left')
    sx, sy, enlarged = 13900, 9000, 4
    def section_box(bounds, layer='WALL', fill=None):
        x1, z1, x2, z2 = bounds
        drawing.rect((sx+x1*enlarged, sy+z1*enlarged,
                      sx+x2*enlarged, sy+z2*enlarged), layer, fill)
    # Coordinates are the actual cross-section at the building's west edge;
    # only horizontal view extent is cropped to show the outer supporting wall.
    section_box((22, -200, 600, 0))
    section_box((0, d['old_plinth_bottom_z'], E.foundation_wall_thickness, -200))
    section_box((0, d['raft_top_z'], E.foundation_wall_thickness, d['old_plinth_bottom_z']))
    section_box((0, S.raft_bottom_z, 600, d['raft_top_z']))
    section_box((-600, d['soil_bottom_z'], 0, d['finish_bottom_z']), 'FURNITURE')
    section_box((-600, d['finish_bottom_z'], 0, S.ground_z), 'FURNITURE')
    for z, text in [(0, '1階床 Z=0'), (-200, '既存床板下面 -200'),
                    (-500, '外部地盤 -500'), (-650, '底板上面 -650'), (-800, '底板下面 -800')]:
        y = sy + z * enlarged
        drawing.line((sx+2400, y), (sx+3900, y), 'DIM')
        drawing.text(text, (sx+4100, y), 250, align='left')
    drawing.text('底板厚150 / 立上り幅140（仮定）', (12600, 5100), 250, align='left')
    drawing.text('フェンス基礎：300角 / Z=-950～-550', (12600, 4600), 250, align='left')
    drawing.text('地盤面からフェンス天端まで1200', (12600, 4100), 250, align='left')
    drawing.text('03 玄関への高さ関係（模式・縮尺なし）', (12600, 3100), 350, align='left')
    for i, text in enumerate([
        '地盤 -500 → 追加段 -330 → 既存段 -160',
        '→ 既存ポーチ -25 → 玄関床 0',
        '段差：170 / 170 / 135 / 25',
        f'追加段・歩道幅{d["path"][2]-d["path"][0]:g} / 追加段奥行300',
    ]): drawing.text(text, (12600, 2400-i*500), 250, align='left')
    drawing.text('04 計画の前提', (12600, -500), 350, align='left')
    for i, text in enumerate([
        '敷地・駐車場・地盤は仮定。無舗装部は砂利。',
        f'並列2台：各2800×5000。車両開口{S.car_opening_east-S.car_opening_west:g}。',
        f'フェンス{len(fence["panels"])}面・柱{len(fence["posts"])}本。横桟間の隙間40。',
        '東・西・北の余白1000、南5500（仮定）。',
        '室内・小屋裏は保持。陽台奥行1000、柱なし。',
        '地盤調査・配筋・耐力・排水・車両軌跡は未設計。',
        '玄関ポーチ先端300は陽台の外（仮定）。',
        '本図は施工図・構造計算・測量図ではない。',
    ]): drawing.text(text, (12600, -1200-i*550), 250, align='left')
    drawing.text('text-CAD / R22-SITE / 参考デモ', (12600, -6900), 250, align='left')

    pdf.setLineWidth(.7 * mm); pdf.rect(7.5*mm, 7.5*mm, 405*mm, 282*mm)
    drawing.doc.layers.new('D-TTL-FRAM', dxfattribs={'color':7, 'lineweight':70})
    drawing.doc.layers.new('D-TTL-VPRT', dxfattribs={'color':7, 'plot':0})
    layout = drawing.doc.layouts.new('SITE_A3_1_100')
    layout.page_setup(size=(420,297), margins=(0,0,0,0), units='mm')
    layout.add_lwpolyline([(7.5,7.5),(412.5,7.5),(412.5,289.5),(7.5,289.5)],
                         close=True, dxfattribs={'layer':'D-TTL-FRAM'})
    layout.add_viewport(center=(210,148.5), size=(400,278),
        view_center_point=((210-70)*100,(148.5-105)*100), view_height=278*100,
        dxfattribs={'layer':'D-TTL-VPRT', 'flags':const.VSF_LOCK_ZOOM})
    drawing.doc.layouts.set_active_layout('SITE_A3_1_100')
    drawing.doc.header['$TILEMODE'] = 0
    drawing.doc.saveas(ROOT / 'DXF/house_site_plan.dxf')
    pdf.showPage(); pdf.save()
    print(f'Saved {out} and DXF/house_site_plan.dxf')


if __name__ == '__main__':
    generate()
