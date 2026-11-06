"""Editable Seto Ohashi reference drawings, projected from the native specification.

Modelspace is 1:1 millimetres. Locked A3 viewports and the matching SVG/PDF
apply the stated scale, with no vertical exaggeration. Public dimensions and
photo-fit assumptions remain distinct; these are not construction drawings.
"""
from __future__ import annotations

import hashlib
import html
import json
import math
import os
from pathlib import Path

import ezdxf
from ezdxf.enums import TextEntityAlignment
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from lib.seto_bridge_geometry import (
    MODEL_ID, REVISION, parameters, bridges, stations, cable_z, component_specs, tower_column_outline,
    shared_anchor_profile,
)
from lib.seto_bridge_activity import activity_manifest

ROOT = Path(__file__).resolve().parents[1]
FONT = Path(os.environ.get('TEXT_CAD_CJK_FONT', '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'))
SOURCES = ['src/lib/seto_bridge_geometry.py', 'src/lib/seto_bridge_activity.py', 'src/generate_seto_bridge_plans.py']
LAYERS = {
    'environment': 'D-BGD-SEAS', 'foundations': 'D-STR-BASE', 'towers': 'D-STR-TOWR',
    'cables': 'D-STR-CABL', 'hangers': 'D-STR-HANG', 'truss': 'D-STR-TRUS',
    'road': 'D-STR-ROAD', 'railway': 'D-STR-RAIL', 'traffic': 'D-BYP-CARS',
    'vessels': 'D-BYP-SHIP', 'trains':'D-BYP-EMU', 'axis': 'D-BMK-AXIS',
    'text': 'D-STR-TXT', 'dimension': 'D-STR-DIM',
    'sheet': 'D-TTL-FRAM', 'sheet_text': 'D-TTL-TXT', 'viewport': 'D-TTL-VPRT',
}
INK = '#243642'


class BridgeDrawing:
    def __init__(self, view, title, scale, origin):
        self.view, self.scale, self.origin = view, scale, origin
        self.center = (0., 0.)
        self.model_offset = (0., 0.)
        self.operations, self.dimensions, self.labels = [], [], []
        self.doc = ezdxf.new('R2018', setup=True)
        self.doc.units = ezdxf.units.MM
        self.doc.header['$MEASUREMENT'] = 1
        self.doc.header['$DIMASSOC'] = 2
        self.doc.header['$LWDISPLAY'] = True
        self.doc.styles.new('SETO_UNICODE', dxfattribs={'font': 'Arial Unicode.ttf'})
        self.doc.appids.new('SETO_PART')
        for key, layer in LAYERS.items():
            self.doc.layers.new(layer, dxfattribs={'color': 7, 'lineweight': 13 if key in ('axis', 'text', 'dimension') else 25})
        self.doc.layers.get(LAYERS['viewport']).dxf.plot = 0
        self.msp = self.doc.modelspace()
        self.layout = self.doc.layouts.new(f'SETO_A3_{view.upper()}')
        self.layout.page_setup(size=(420, 297), margins=(0, 0, 0, 0), units='mm')
        metadata = self.doc.ezdxf_metadata()
        for key, value in {'REVISION': REVISION, 'MODEL_ID': MODEL_ID, 'UNITS': 'mm',
                'SCALE': f'1:{scale}; modelspace 1:1; no vertical exaggeration',
                'SCOPE': '公表値と実景を参考にした外観模式図。未測量・未計算。'}.items():
            metadata[key] = value
        self.paper_poly([(8, 8), (412, 8), (412, 289), (8, 289)], True, width=.55)
        self.paper_text('瀬戸大橋 / 南北備讃瀬戸大橋', (17, 277), 5)
        self.paper_text(title, (17, 266), 3.8)
        self.paper_text(f'{REVISION}  |  A3  |  1:{scale}  |  単位 mm  |  外観参考図', (402, 277), 2.8, 'right')
        self.paper_poly([(17, 25), (402, 25)], width=.2)
        self.paper_text('公表値と実景を参照 / 未測量・未計算 / NOT FOR CONSTRUCTION', (17, 17), 2.8)
        self.paper_text(f'text-CAD  2026-11-07  {view.upper()}', (402, 17), 2.8, 'right')

    def paper_point(self, p):
        return (self.origin[0] + (p[0]-self.center[0])/self.scale,
                self.origin[1] + (p[1]-self.center[1])/self.scale)

    def model_point(self, p):
        return (p[0]+self.model_offset[0], p[1]+self.model_offset[1])

    def paper_poly(self, points, closed=False, color=INK, fill=None, width=.15):
        self.operations.append(dict(kind='poly', points=points, closed=closed, color=color, fill=fill, width=width))
        self.layout.add_lwpolyline(points, close=closed, dxfattribs={'layer': LAYERS['sheet'], 'color': 7})

    def paper_text(self, value, point, height=3, align='left'):
        self.labels.append(value)
        self.operations.append(dict(kind='text', points=point, text=value, height=height, align=align))
        item = self.layout.add_text(value, dxfattribs={'layer': LAYERS['sheet_text'], 'height': height,
            'style': 'SETO_UNICODE', 'color': 7})
        item.set_placement(point, align={'left': TextEntityAlignment.MIDDLE_LEFT,
            'center': TextEntityAlignment.MIDDLE_CENTER, 'right': TextEntityAlignment.MIDDLE_RIGHT}[align])

    def poly(self, points, group='truss', closed=False, color=INK, fill=None, width=.12, name=None):
        entity = self.msp.add_lwpolyline([self.model_point(p) for p in points], close=closed,
            dxfattribs={'layer': LAYERS[group], 'color': 7})
        if name:
            entity.set_xdata('SETO_PART', [(1000, name)])
        self.operations.append(dict(kind='poly', points=[self.paper_point(p) for p in points],
            closed=closed, color=color, fill=fill, width=width))

    def line(self, a, b, group='axis', color=INK, width=.12, name=None):
        self.poly([a, b], group, color=color, width=width, name=name)

    def rect(self, bounds, group='truss', color=INK, fill=None, width=.12, name=None):
        x, y, a, b = bounds
        self.poly([(x, y), (a, y), (a, b), (x, b)], group, True, color, fill, width, name)

    def text(self, value, point, height=3, align='left'):
        self.labels.append(value)
        item = self.msp.add_text(value, dxfattribs={'layer': LAYERS['text'], 'height': height*self.scale,
            'style': 'SETO_UNICODE', 'color': 7})
        item.set_placement(self.model_point(point), align=TextEntityAlignment.MIDDLE_CENTER
            if align == 'center' else TextEntityAlignment.MIDDLE_LEFT)
        self.operations.append(dict(kind='text', points=self.paper_point(point), text=value, height=height, align=align))

    def dim(self, a, b, base, vertical=False):
        """Native editable linear DIMENSION, without stale independent CAD lines."""
        value = abs(b[1]-a[1]) if vertical else abs(b[0]-a[0])
        dim = self.msp.add_linear_dim(base=self.model_point(base), p1=self.model_point(a), p2=self.model_point(b),
            angle=90 if vertical else 0, dimstyle='EZDXF', override={
                'dimtxt': 3*self.scale, 'dimasz': 1.2*self.scale, 'dimgap': .7*self.scale,
                'dimexo': .6*self.scale, 'dimexe': .8*self.scale, 'dimdec': 0,
                'dimlfac': 1, 'dimlunit': 2, 'dimtad': 1, 'dimtsep': 44,
                'dimclrd': 7, 'dimclre': 7, 'dimclrt': 7, 'dimtxsty': 'SETO_UNICODE'},
            dxfattribs={'layer': LAYERS['dimension'], 'color': 7})
        dim.render()
        for entity in self.doc.blocks.get(dim.dimension.dxf.geometry):
            entity.dxf.layer = LAYERS['dimension']
        ends = [(base[0], a[1]), (base[0], b[1])] if vertical else [(a[0], base[1]), (b[0], base[1])]
        pa, pb = [self.paper_point(p) for p in ends]
        self.operations.append(dict(kind='poly', points=[pa, pb], closed=False, color='#445C68', width=.13))
        for p, end in zip((a, b), ends):
            self.operations.append(dict(kind='poly', points=[self.paper_point(p), self.paper_point(end)],
                closed=False, color='#8A979C', width=.08))
        dx, dy = (0, 1) if vertical else (1, 0)
        for tip, sign in ((pa, 1), (pb, -1)):
            triangle = [tip, (tip[0]+dx*1.3*sign-dy*.4, tip[1]+dy*1.3*sign+dx*.4),
                (tip[0]+dx*1.3*sign+dy*.4, tip[1]+dy*1.3*sign-dx*.4)]
            self.operations.append(dict(kind='poly', points=triangle, closed=True, color='#445C68', fill='#445C68', width=.1))
        middle = ((pa[0]+pb[0])/2, (pa[1]+pb[1])/2)
        at = (middle[0]-2.1, middle[1]) if vertical else (middle[0], middle[1]+2.2)
        self.operations.append(dict(kind='text', points=at, text=f'{value:,.0f}', height=3,
            align='center', dimension=value, rotation=90 if vertical else 0))
        self.dimensions.append(value)

    def viewport(self, size, paper_center, model_center=(0, 0), scale=None):
        self.layout.add_viewport(center=paper_center, size=size, view_center_point=self.model_point(model_center),
            view_height=size[1]*(scale or self.scale), dxfattribs={'layer': LAYERS['viewport'], 'status': 2, 'flags': 16384})

    def finish(self, required_labels):
        self.doc.set_modelspace_vport(height=220*self.scale, center=self.center)
        audit = self.doc.audit()
        if audit.has_errors:
            raise ValueError(f'Invalid Seto DXF: {audit.errors}')
        stem = f'seto_ohashi_{self.view}'
        dxf, svg = f'DXF/{stem}.dxf', f'output/svg/{stem}.svg'
        (ROOT/'DXF').mkdir(exist_ok=True)
        (ROOT/'output/svg').mkdir(parents=True, exist_ok=True)
        self.doc.saveas(ROOT/dxf)
        fragments = []
        for op in self.operations:
            if op['kind'] == 'poly':
                tag = 'polygon' if op.get('closed') else 'polyline'
                xy = ' '.join(f'{x*4:.4f},{(297-y)*4:.4f}' for x, y in op['points'])
                fragments.append(f'<{tag} points="{xy}" stroke="{op.get("color", INK)}" '
                    f'fill="{op.get("fill") or "none"}" stroke-width="{op.get("width", .12)*4:.3f}" stroke-linejoin="round"/>')
            else:
                x, y = op['points'][0]*4, (297-op['points'][1])*4
                anchor = {'left': 'start', 'center': 'middle', 'right': 'end'}[op.get('align', 'left')]
                dimension = f' data-dimension-mm="{op["dimension"]:g}"' if 'dimension' in op else ''
                rotate = f' transform="rotate({-op["rotation"]:g} {x:.4f} {y:.4f})"' if op.get('rotation') else ''
                fragments.append(f'<text x="{x:.4f}" y="{y:.4f}" font-size="{op["height"]*4:g}" '
                    f'text-anchor="{anchor}" dominant-baseline="middle" fill="{INK}"{dimension}{rotate}>{html.escape(op["text"])}</text>')
        source = ('<svg xmlns="http://www.w3.org/2000/svg" width="1680" height="1188" viewBox="0 0 1680 1188" '
            f'data-units="mm" data-revision="{REVISION}"><style>text{{font-family:"Arial Unicode MS","Noto Sans JP",sans-serif}}</style>'
            '<rect width="1680" height="1188" fill="white"/>'+''.join(fragments)+'</svg>\n')
        (ROOT/svg).write_text(source, encoding='utf-8')
        return {'id': self.view, 'dxf': dxf, 'svg': svg, 'scale': self.scale,
            'dimensions_mm': self.dimensions, 'required_labels': required_labels}

    def pdf(self, pdf):
        for op in self.operations:
            pdf.saveState()
            pdf.setStrokeColor(HexColor(op.get('color', INK)))
            pdf.setLineWidth(op.get('width', .12)*mm)
            if op['kind'] == 'poly':
                path = pdf.beginPath()
                path.moveTo(op['points'][0][0]*mm, op['points'][0][1]*mm)
                for x, y in op['points'][1:]:
                    path.lineTo(x*mm, y*mm)
                if op.get('closed'):
                    path.close()
                if op.get('fill'):
                    pdf.setFillColor(HexColor(op['fill']))
                pdf.drawPath(path, stroke=1, fill=1 if op.get('fill') else 0)
            else:
                pdf.setFillColor(HexColor(INK))
                pdf.setFont('SetoUnicode', op['height']*mm)
                x, y = op['points']
                pdf.translate(x*mm, y*mm)
                pdf.rotate(op.get('rotation', 0))
                align = op.get('align', 'left')
                draw = pdf.drawCentredString if align == 'center' else pdf.drawRightString if align == 'right' else pdf.drawString
                draw(0, -.34*op['height']*mm, op['text'])
            pdf.restoreState()
        pdf.showPage()


def actor_outline(actor, center=None, heading=None):
    """Actual-size t=0 footprint, with original annotation kept editable."""
    length, width = actor['length_mm'], actor['width_mm']
    x, y = (actor['origin_mm'][:2] if center is None else center)
    angle = actor['heading_rad'] if heading is None else heading
    if actor['group'] == 'vessels':
        local = [(-length/2, -width*.38), (-length*.25, -width/2),
                 (length*.3, -width/2), (length/2, 0), (length*.3, width/2),
                 (-length*.25, width/2), (-length/2, width*.38)]
    else:
        local = [(-length/2, -width/2), (length/2, -width/2),
                 (length/2, width/2), (-length/2, width/2)]
    return [(x+u*math.cos(angle)-v*math.sin(angle), y+u*math.sin(angle)+v*math.cos(angle)) for u,v in local]


def draw_activity_details(d, activity):
    """Separate actual-scale CAD details; not an enlarged object on the main plan."""
    car = next(a for a in activity['actors'] if a['kind'] == 'sedan')
    boat = next(a for a in activity['actors'] if a['group'] == 'vessels')
    d.paper_text('車・船・電車はt=0の静止位置。経路・速度は説明用の仮定。', (222, 112), 2.7)
    d.paper_text('車両（1:100）', (224, 100), 3.1)
    d.paper_text('遊覧船（1:500）', (316, 100), 3.1)
    for actor, scale, origin, offset, viewport_width in [
            (car, 100, (254, 78), (4000000, -1000000), 74),
            (boat, 500, (356, 78), (4200000, -1000000), 90)]:
        d.scale, d.origin, d.center, d.model_offset = scale, origin, (0, 0), offset
        group = actor['group']; length, width = actor['length_mm'], actor['width_mm']
        d.poly(actor_outline(actor, (0,0), 0), group, True, '#485F6C', '#E7ECEC', .25,
               f'{group}:{actor["id"]}:plan_detail')
        if group == 'traffic':
            d.rect((-length*.25,-width*.4,length*.2,width*.4), group, '#485F6C', '#BACDD4', .2)
            for u in (-length*.3,length*.3):
                for v in (-width/2,width/2):
                    d.rect((u-length*.07,v-width*.04,u+length*.07,v+width*.04), group, '#263B49', '#263B49', .18)
        else:
            d.rect((-length*.27,-width*.31,length*.2,width*.31), group, '#485F6C', '#BACDD4', .2)
            for u in (-.17,-.05,.07):
                d.rect((length*u,-width*.25,length*(u+.08),width*.25), group, '#485F6C', '#F4F6F5', .12)
            d.line((-length*.12,0),(length*.27,0),group,'#485F6C',.16)
        d.dim((-length/2, -width/2), (length/2, -width/2), (0,-width/2-4*scale))
        d.viewport((viewport_width, 41), (origin[0],76), ((origin[0]-d.origin[0])*scale,(76-d.origin[1])*scale), scale)
    d.scale, d.origin, d.center, d.model_offset = 10000, (191.07,183), (0,0), (0,0)
    d.paper_text('車体・船体・速度・配置は説明用の仮定。Webのみ移動し、CADは静止。', (222, 43), 2.7)


def draw_plan():
    p = parameters()
    d = BridgeDrawing('plan', '橋梁全体平面図 / 橋軸X・横断Y', 10000, (191.07, 183))
    x1, x2 = p['north_outer_end_mm'], p['south_outer_end_mm']
    d.rect((x1-45000, -350000, x2+45000, 350000), 'environment', color='#B6CCD2', fill='#F0F6F7')
    for spec in component_specs():
        if spec['kind'] == 'island':
            x, y = spec['centre']; rx, ry = spec['radii']
            points = [(x+rx*math.cos(i*math.pi/16), y+ry*math.sin(i*math.pi/16)) for i in range(32)]
            d.poly(points, 'environment', True, '#B5BEAD', '#ECF0E4', name=spec['name'])
        elif spec['kind'] == 'box' and spec['group'] in ('road', 'foundations') and any(
                label in spec['name'] for label in ('deck', 'base', 'continuation', 'marine_caisson', ':pier')):
            x, y, z, a, b, c = spec['bounds']
            d.rect((x, y, a, b), spec['group'], '#536C73', '#D9E0DE', name=spec['name'])
        elif spec['kind']=='tower_column':
            d.poly([(x,y) for x,y,z in tower_column_outline(spec)],'towers',True,'#536C73','#C8D3D0',name=spec['name'])
        elif spec['kind']=='anchorage':
            low,high=min(x for x,z in spec['outline_xz']),max(x for x,z in spec['outline_xz'])
            d.rect((low,-spec['width_mm']/2,high,spec['width_mm']/2),'foundations',
                '#536C73',None,.12,spec['name']+':plan_envelope')
    activity = activity_manifest(p)
    for actor in activity['actors']:
        if actor['group']!='vessels': continue
        x=actor['route']['fixed_mm']
        for y in range(-300000,300000,40000):
            d.line((x,y),(x,y+23000),'vessels','#729CA9',.12)
        y=actor['direction']*245000
        d.poly([(x-9000,y-actor['direction']*14000),(x,y),
                (x+9000,y-actor['direction']*14000)],'vessels',color='#477C91',width=.25)
    for actor in activity['actors']:
        group = actor['group']
        d.poly(actor_outline(actor), group, True, '#386077' if group in ('vessels','trains') else '#6A6258',
               '#9CB8C7' if group=='trains' else '#E6F0F3' if group == 'vessels' else '#BBB8A9', .15 if group=='trains' else .12,
               f'{group}:{actor["id"]}:static_plan_symbol')
    d.text('遊覧船：中央径間を横断（仮定）',(0,-315000),2.8,'center')
    for b in bridges(p):
        for sign in (-1, 1):
            d.line((b['start'], sign*17500), (b['end'], sign*17500), 'cables', '#526D76', .2)
        d.dim((b['start'], 35000), (b['end'], 35000), (0, 510000))
        mid = (b['start']+b['end'])/2
        d.text('北備讃瀬戸大橋' if b['id'] == 'north' else '南備讃瀬戸大橋', (mid, 400000), 3.4, 'center')
    d.dim((x1, -350000), (x2, -350000), (0, -470000))
    for i, (label, x) in enumerate(zip(('BB1A', 'BB2P', 'BB3P', 'BB4A', 'BB5P', 'BB6P', 'BB7A'),
            (p['north_start_mm']-24000, *p['tower_stations_mm'][:2], 0, *p['tower_stations_mm'][2:], p['south_end_mm']+30000))):
        d.line((x, 30000), (x, 135000 if i % 2 else 200000), 'axis', '#88999D', .1)
        d.text(label, (x, 165000 if i % 2 else 230000), 3, 'center')
    section_x = (bridges(p)[0]['tower_a']+bridges(p)[0]['tower_b'])/2
    d.line((section_x, -95000), (section_x, 95000), 'axis', '#7D5368', .25)
    d.text('A', (section_x, 125000), 3.5, 'center')
    d.text('A', (section_x, -125000), 3.5, 'center')
    d.text('N / 与島側', (x1, 610000), 3.2)
    d.text('S / 坂出・番の州側', (x2-310000, 610000), 3.2)
    d.viewport((380, 134), (201, 192), ((201-d.origin[0])*d.scale, (192-d.origin[1])*d.scale))
    d.paper_poly([(17, 124), (402, 124)], width=.2)
    rows = ['01 対象範囲と公表寸法',
        '北：274,000 + 990,000 + 274,000 = 1,538,000 mm',
        '南：274,000 + 1,100,000 + 274,000 = 1,648,000 mm',
        'BB4Aは一つの共用アンカレイジ。接続区間は49,000 mm。',
        '橋端間3,333,800 mm：公表区間1611+1723 mとの丸め差。',
        'A-A：北橋中央径間。下層電車は4両×2編成を投影表示。']
    for i, left in enumerate(rows):
        d.paper_text(left, (20, 113-i*10), 3.2 if not i else 3)
    draw_activity_details(d, activity)
    d.paper_text('参照：JB本四高速 / 川崎製鉄技報。自動車24台・遊覧船4隻・電車2編成は説明用の配置。', (20, 33), 2.8)
    return d, d.finish(['橋梁全体平面図', '北備讃瀬戸大橋', '南備讃瀬戸大橋', 'BB4A', '車両', '遊覧船', '電車', '単位 mm'])


def draw_tower_fronts(d):
    """Native 1:1 Y/Z front projections in separately positioned CAD insets."""
    d.paper_text('主塔正面図（参考）1:2000', (222,163),3.8)
    for ident,number,origin,offset,label in [
            ('north',2,(264,43),(4600000,-1000000),'北橋・3P型'),
            ('south',1,(350,43),(4800000,-1000000),'南橋・5P型')]:
        d.scale,d.origin,d.center,d.model_offset=2000,origin,(0,0),offset
        prefix=f'towers:{ident}:tower_{number}:'
        own=[s for s in component_specs() if s['name'].startswith(prefix)]
        for spec in component_specs():
            if spec['name'] not in (f'foundations:{ident}:tower_{number}:pier',
                    f'foundations:{ident}:tower_{number}:marine_caisson_assumed'):continue
            x,y,z,a,b,c=spec['bounds']
            d.rect((y,max(0,z),b,c),'foundations','#758179','#E1E5DF',.12,spec['name'])
        for spec in own:
            if spec['kind']=='tower_column':
                a,b=spec['base_centre_mm'],spec['top_centre_mm'];half=spec['width_mm']/2
                d.poly([(a[1]-half,a[2]),(a[1]+half,a[2]),(b[1]+half,b[2]),(b[1]-half,b[2])],
                    'towers',True,'#536971','#E5ECE8',.15,spec['name'])
            elif spec['kind']=='beam':
                a,b=spec['start'],spec['end'];dy,dz=b[1]-a[1],b[2]-a[2];length=math.hypot(dy,dz)
                if not length:continue
                ny,nz=-dz/length*spec['depth_mm']/2,dy/length*spec['depth_mm']/2
                d.poly([(a[1]+ny,a[2]+nz),(b[1]+ny,b[2]+nz),(b[1]-ny,b[2]-nz),(a[1]-ny,a[2]-nz)],
                    'towers',True,'#536971','#E5ECE8',.13,spec['name'])
            elif spec['kind']=='box':
                x,y,z,a,b,c=spec['bounds'];d.rect((y,z,b,c),'towers','#536971','#E5ECE8',.12,spec['name'])
            elif spec['kind']=='prism':
                d.poly([(y,z) for x,y,z in spec['outline']],'towers',True,'#536971','#D9E3DF',.12,spec['name'])
        station=next(s['base_centre_mm'][0] for s in own if s['kind']=='tower_column')
        road=parameters()['road_deck_z_mm']-.01*abs(station);rail=road-13000
        d.rect((-15000,rail-700,15000,rail),'railway','#536971','#B7C8CC',.12)
        d.rect((-13000,road-700,13000,road),'road','#536971','#B7C8CC',.12)
        for y in (-15000,15000):d.line((y,rail),(y,road),'truss','#536971',.13)
        d.text('道路',(0,road+3500),2.2,'center')
        d.text('鉄道',(0,rail+3500),2.2,'center')
        top=184000 if ident=='north' else 194000
        d.line((-27000,0),(27000,0),'axis','#92A5AC',.10)
        d.dim((-17500,top),(17500,top),(0,top+8000))
        d.dim((17500,0),(17500,top),(42000,0),True)
        d.viewport((72,110),(origin[0]+4,96),(8000,106000),2000)
        d.paper_text(label,(origin[0],153),3.1,'center')
    d.scale,d.origin,d.center,d.model_offset=10000,(191.07,210),(0,0),(0,0)
    d.paper_text('上部2X / 下部X＋山形。塔柱は十字形3セル外包の近似。',(222,35),2.7)


def draw_elevation():
    p = parameters()
    d = BridgeDrawing('elevation', '橋梁全体側面図1:10000（鉛直倍率なし） / 主塔正面1:2000・参考', 10000, (191.07, 210))
    for spec in component_specs():
        if spec['group'] == 'environment':
            continue
        if spec['kind'] == 'beam':
            a, b = spec['start'], spec['end']
            if a[1] > 0 or b[1] > 0:
                continue
            d.line((a[0], a[2]), (b[0], b[2]), spec['group'],
                '#58707A' if spec['group'] in ('cables', 'hangers') else '#627478',
                .13 if spec['group'] == 'cables' else .085, spec['name'])
        elif spec['kind']=='tower_column' and spec['base_centre_mm'][1]<0:
            a,b=spec['base_centre_mm'],spec['top_centre_mm'];h1,h2=spec['base_depth_mm']/2,spec['top_depth_mm']/2
            d.poly([(a[0]-h1,a[2]),(a[0]+h1,a[2]),(b[0]+h2,b[2]),(b[0]-h2,b[2])],
                'towers',True,'#627478','#E4E8E5',.09,spec['name'])
        elif spec['kind'] == 'box' and spec['group'] in ('foundations', 'road', 'railway') and 'mark' not in spec['name'] and 'track' not in spec['name']:
            x, y, z, a, b, c = spec['bounds']
            gradient = spec.get('longitudinal_gradient', 0)
            d.poly([(x, z-gradient*abs(x)), (a, z-gradient*abs(a)),
                (a, c-gradient*abs(a)), (x, c-gradient*abs(x))], spec['group'], True,
                '#78868A', '#E4E8E5', .09, spec['name'])
        elif spec['kind'] == 'anchorage':
            d.poly(spec['outline_xz'], 'foundations', True, '#77847D', '#D5DBD4', .14, spec['name'])
    d.line((p['north_outer_end_mm']-40000, 0), (p['south_outer_end_mm']+40000, 0), 'environment', '#6D9EAE', .18)
    for b in bridges(p):
        d.dim((b['start'], 194000), (b['end'], 194000), (0, 410000))
        d.dim((b['tower_a'], 0), (b['tower_b'], 0), (0, -100000))
        d.text('北橋' if b['id'] == 'north' else '南橋', ((b['start']+b['end'])/2, 270000), 3.2, 'center')
    d.dim((p['north_outer_end_mm'], 0), (p['south_outer_end_mm'], 0), (0, -230000))
    d.viewport((380, 85), (201, 221), ((201-d.origin[0])*d.scale, (221-d.origin[1])*d.scale))
    d.paper_text('全体側面図：模型の橋面はBB4Aから両側へ約1%低下。北側勾配は南側の対称仮定。', (20, 170), 3)
    d.paper_poly([(17, 158), (402, 158)], width=.2)
    d.paper_text('公式の支配寸法', (20, 145), 3.8)
    facts = [
        ('北橋・中央径間', '990,000 mm'), ('南橋・中央径間', '1,100,000 mm'),
        ('北橋・主塔頂高', 'T.P. +184,000 mm'), ('南橋・主塔頂高', 'T.P. +194,000 mm'),
        ('北橋・主ケーブル径', '998 mm（被覆を除く）'), ('南橋・主ケーブル径', '1,062 mm（被覆を除く）'),
    ]
    for i, (label, value) in enumerate(facts):
        y = 132-i*12
        d.paper_text(label, (22, y), 3.2)
        d.paper_text(value, (107, y), 3.2)
    draw_tower_fronts(d)
    d.paper_text('出典：JB本四高速・本四公団 / 塔正面：建設の機械化1986.5 Fig.3・駒井1986 Fig.1。',(20,40),2.7)
    return d, d.finish(['橋梁全体側面図', '北橋', '南橋', 'T.P.', '主塔正面図', '上部2X', '下部X＋山形', '単位 mm'])


def draw_section():
    p=parameters();north=bridges(p)[0];specs=component_specs()
    xstation=(north['tower_a']+north['tower_b'])/2
    zhi=p['road_deck_z_mm']-.01*abs(xstation)
    zlo=p['rail_deck_z_mm']-.01*abs(xstation)
    d=BridgeDrawing('section','A-A 横断面 1:250 / BB4A通過部 1:750 / 軌頂詳細 1:20',250,(112,139))
    road=p['road_deck_z_mm']-p['rail_deck_z_mm']
    crest=420
    d.rect((-13000,road-700,13000,road),'road','#53666E','#D7DFE0')
    d.rect((-15000,-700,15000,0),'railway','#53666E','#E1E5E1')
    # The floorbeam top is exactly at the deck underside, below the rails.
    d.rect((-15000,-1700,15000,-700),'truss','#72858C','#CDD5D2')
    for sign in (-1,1):
        d.rect((sign*15000-550,-600,sign*15000+550,road+600),'truss','#53666E','#CDD5D2')
        d.rect((sign*12800-175,road,sign*12800+175,road+1600),'road','#53666E','#D7DFE0')
        d.line((sign*15000,road),(sign*17500,road),'truss','#53666E',.4)
        cz=cable_z(xstation,north,p)-zlo;radius=p['north_cable_diameter_mm']/2
        points=[(sign*17500+radius*math.cos(i*math.pi/12),cz+radius*math.sin(i*math.pi/12)) for i in range(24)]
        d.poly(points,'cables',True,'#526A73','#C6D3D3',.2)
        d.line((sign*17500,road),(sign*17500,cz-radius),'hangers','#526A73',.25)
    for y in (-10500,-5500):
        for sign in (-1,1):
            d.rect((y+sign*533.5-65,200,y+sign*533.5+65,crest),'railway','#5B6870','#5B6870')
            d.rect((y+sign*533.5-75,crest,y+sign*533.5+75,crest+860),'trains','#526B76','#526B76')
        d.rect((y-1425,crest+1100,y+1425,crest+3850),'trains','#536D7A','#DFE7E9')
        d.rect((y-1311,crest+3850,y+1311,crest+3970),'trains','#536D7A','#B7C8CE')
        d.poly([(y-650,crest+4140),(y,crest+4660),(y+650,crest+5170)],'trains',color='#536D7A',width=.22)
        d.line((y-900,crest+5300),(y+900,crest+5300),'trains','#536D7A',.3)
        d.line((y-1800,crest+5400),(y+1800,crest+5400),'railway','#5D7C81',.15)
    d.rect((-500,road,500,road+1200),'road','#53666E','#D7DFE0')
    d.dim((-17500,cz),(17500,cz),(0,30000))
    d.dim((-15000,0),(15000,0),(0,-11000))
    d.dim((-11250,road),(11250,road),(0,road+7000))
    d.dim((15000,0),(15000,road),(22000,0),True)
    d.dim((-5500,crest),(-5500,crest+5300),(-2300,0),True)
    d.text('上層：道路4車線',(0,road+3800),3.2,'center')
    d.text('在来線（複線）',(-8000,-5000),3.1,'center')
    d.text('新幹線の留保空間',(7000,-5000),3.1,'center')
    d.text('A-A',(-18000,26000),3.5)
    d.viewport((221,203),(123,165),((123-d.origin[0])*250,(165-d.origin[1])*250))
    for i,note in enumerate([
        f'断面 X={xstation:,.0f} mm / 北橋中央径間',
        f'上層 T.P.+{zhi:,.0f} / 下層 T.P.+{zlo:,.0f} mm（近似）',
        '車両高5,300・架線高5,400 mmは軌頂からの仮定。',
        '横桁を1,200 mm下げ、車輪との干渉を解消。',
        '公表値：主桁間30m・桁高13m・ケーブル間35m。',
        '車両限界・動揺・電気離隔の法定照査は未実施。']):
        d.paper_text(note,(22,86-i*9),2.9)

    # Native longitudinal section through the railway, not an outer silhouette
    # hiding the actual subtraction. The lower foundation is intentionally
    # cropped at +18m; the documented V-bottom remains visible at +52.5m.
    d.scale,d.origin,d.center,d.model_offset=750,(326,140),(0,52500),(1000000,0)
    anchor=next(s for s in specs if s['name']=='foundations:BB4A_shared:V_notched_body')
    cut=anchor['clearance_cuts'][0]['bounds'];cut_bottom=cut[2]
    # At Y=-5500 the blind end-face recesses also remove the outer 4500mm.
    # Preserve the real V contour and crop the omitted base, instead of
    # splicing positional vertices from an older anchorage polygon.
    polygon=[list(point) for point in anchor['outline_xz']]
    outer_indices={0,1,2,3,4,len(polygon)-3,len(polygon)-2,len(polygon)-1}
    for index in outer_indices:
        polygon[index][0]-=math.copysign(shared_anchor_profile()['recess_depth_mm'],polygon[index][0])
    # Clip the true X-Z polygon to the remaining material below the bore.
    def clip_top(points,height):
        clipped=[]
        for a,b in zip(points,points[1:]+points[:1]):
            inside_a,inside_b=a[1]<=height,b[1]<=height
            if inside_a:clipped.append(a)
            if inside_a!=inside_b:
                ratio=(height-a[1])/(b[1]-a[1]);clipped.append((a[0]+ratio*(b[0]-a[0]),height))
        return clipped
    polygon=clip_top(polygon,cut_bottom)
    polygon=[(x,-z) for x,z in clip_top([(x,-z) for x,z in polygon],-18000)]
    d.poly(polygon,'foundations',True,'#77847D','#E1E6DE',.24,anchor['name']+':railway_section')
    road_here=p['road_deck_z_mm']-245
    rail_here=p['rail_deck_z_mm']-245
    for nominal,depth,group in ((road_here,700,'road'),(rail_here,700,'railway')):
        points=[]
        for x in (-45000,-24500,24500,45000):
            z=nominal-.01*(max(abs(x),24500)-24500);points.append((x,z))
        d.poly([*points,*[(x,z-depth) for x,z in reversed(points)]],group,True,'#536D75','#D3DDE0',.22)
    # Carriage side elevation, positioned at the passage to explain clearance.
    rail_top=rail_here+crest
    outline=[(-10000,rail_top+1100),(-10000,rail_top+1850),(-9000,rail_top+3850),
        (9000,rail_top+3850),(10000,rail_top+1850),(10000,rail_top+1100)]
    d.poly(outline,'trains',True,'#486877','#C3D6DE',.22)
    d.poly([(-2300,rail_top+3970),(-1300,rail_top+4660),(-2250,rail_top+5170)],'trains',color='#486877',width=.2)
    d.line((-2380,rail_top+5300),(-2020,rail_top+5300),'trains','#486877',.3)
    for x in (-7950,-5850,5850,7950):
        ring=[(x+430*math.cos(i*math.pi/8),rail_top+430+430*math.sin(i*math.pi/8)) for i in range(16)]
        d.poly(ring,'trains',True,'#486877','#486877',.1)
    d.dim((39500,rail_top),(39500,road_here-700),(52000,0),True)
    d.text('BB4A：下層鉄道の通過断面',(0,118000),3.2,'center')
    d.text('通行有効高さ 11,880 mm（仮定）',(0,108000),2.9,'center')
    d.text('V底 T.P.+52,500 mm',(0,42000),2.8,'center')
    d.text('下部省略 / 中央Y=-5,500 mm',(0,25500),2.7,'center')
    d.viewport((154,167),(326,173),((326-d.origin[0])*750,(173-d.origin[1])*750+52500),750)
    d.paper_text('実際の経路・地盤・安全性を保証する断面図ではない。',(249,34),2.6)

    # A separate 1:20 editable detail keeps the 420mm rail crest dimension
    # legible instead of squeezing a 1.7mm dimension into the 1:250 view.
    d.scale,d.origin,d.center,d.model_offset=20,(282,62),(0,0),(1300000,0)
    d.rect((-350,-140,350,0),'railway','#536D75','#E1E6DE',.18)
    d.rect((-65,200,65,420),'railway','#536D75','#536D75',.22)
    d.line((-300,0),(300,0),'railway','#72858C',.16)
    d.dim((0,0),(0,420),(820,0),True)
    d.viewport((70,46),(300,68),((300-d.origin[0])*20,(68-d.origin[1])*20),20)
    d.paper_text('軌頂詳細 1:20（仮定）',(249,94),2.9)
    d.paper_text('寸法はレール頂と下層床上面との差。',(343,77),2.7)
    d.paper_text('開口は説明用の仮定。',(343,67),2.7)
    d.paper_text('原図のアンカレイジを',(343,57),2.7)
    d.paper_text('再現する施工図ではない。',(343,47),2.7)
    # Full external side profile, separate from the cropped railway section.
    # Native 1:1 geometry/dimensions share the same parameter source as STEP.
    d.scale,d.origin,d.center,d.model_offset=2000,(179,36),(0,0),(1700000,0)
    d.rect((-28500,0,28500,5000),'foundations','#758179','#CBD2CB',.12)
    d.poly(anchor['outline_xz'],'foundations',True,'#64776A','#E1E6DE',.16,anchor['name']+':full_external_profile')
    d.line((-44000,33000),(44000,33000),'axis','#92A5AC',.1)
    d.dim((-39500,33000),(39500,33000),(0,94000))
    d.dim((-26500,5000),(26500,5000),(0,-7000))
    d.dim((39500,0),(39500,86000),(53500,0),True)
    d.viewport((73,58),(181,58),(4000,44000),2000)
    d.paper_text('BB4A外形 1:2000',(149,92),2.8)
    d.scale=250
    return d,d.finish(['A-A 横断面','上層：道路4車線','在来線（複線）','新幹線の留保空間',
        'BB4A','BB4A外形','通行有効高さ','軌頂詳細','単位 mm'])


def generate():
    before = {path: hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in SOURCES}
    results = [draw_plan(), draw_elevation(), draw_section()]
    pdfmetrics.registerFont(TTFont('SetoUnicode', str(FONT)))
    pdf_path = 'output/pdf/seto_ohashi_sheets.pdf'
    (ROOT/'output/pdf').mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(ROOT/pdf_path), pagesize=(420*mm, 297*mm), invariant=1)
    pdf.setTitle(f'瀬戸大橋・南北備讃瀬戸大橋 / {REVISION}')
    pdf.setAuthor('text-CAD')
    for drawing, row in results:
        drawing.pdf(pdf)
    pdf.save()
    if before != {path: hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in SOURCES}:
        raise RuntimeError('Drawing sources changed during generation; regenerate from a stable snapshot.')
    paths = [row[key] for _, row in results for key in ('dxf', 'svg')]+[pdf_path]
    manifest = {'schema_version': 1, 'id': MODEL_ID, 'model_id': MODEL_ID, 'revision': REVISION,
        'units': 'mm', 'status': 'reference_concept_only', 'source_geometry_revision': REVISION,
        'source_sha256': before, 'artifacts': {path: {'sha256': hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),
            'bytes': (ROOT/path).stat().st_size} for path in paths}, 'drawings': [row for _, row in results]}
    target = ROOT/'output/review/seto_ohashi_drawings.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'id': MODEL_ID, 'revision': REVISION, 'outputs': paths}, ensure_ascii=False))
    return manifest


if __name__ == '__main__':
    generate()
