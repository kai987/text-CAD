"""Editable landmark CAD sheets from the same component specs as STEP/GLB.

Run from the repository root with the CAD Python environment. Drawing units
are millimetres at modelspace 1:1; only the locked A3 viewport applies scale.
Public landmark heights are distinguished from illustrative member geometry.
"""
from __future__ import annotations

import hashlib
import html
import json
import argparse
from math import cos, hypot, pi, sin, sqrt
import os
from pathlib import Path

import ezdxf
from ezdxf.enums import TextEntityAlignment
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from lib.tower_geometry import (TOWERS, REVISION, component_specs, ring_points,
                                geometry_manifest, geometry_source_paths, revision_for)

ROOT = Path(__file__).resolve().parents[1]
PAPER = (420, 297)
FONT = Path(os.environ.get('TEXT_CAD_CJK_FONT',
    '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'))
LAYERS = {
    'base': 'D-STR-BASE', 'structure': 'D-STR-STRC', 'core': 'D-STR-CORE',
    'decks': 'D-STR-DECK', 'antenna': 'D-STR-ANTN', 'axis': 'D-BMK-AXIS',
    'dimension': 'D-STR-DIM', 'text': 'D-STR-TXT',
    'sheet': 'D-TTL-FRAM', 'sheet_text': 'D-TTL-TXT', 'viewport': 'D-TTL-VPRT',
}
DECK_LABELS = {
    'tokyo-tower': ['メインデッキ', 'トップデッキ'],
    'tokyo-skytree': ['天望デッキ', '天望回廊'],
}


class TowerDrawing:
    """One set of paper primitives drives both SVG and print PDF output."""
    def __init__(self, tower_id, view, scale, origin):
        self.tower_id, self.view = tower_id, view
        self.parameters = TOWERS[tower_id]
        self.revision = revision_for(tower_id)
        self.scale, self.origin = scale, origin
        self.doc = ezdxf.new('R2018', setup=True)
        self.doc.units = ezdxf.units.MM
        self.doc.header['$MEASUREMENT'] = 1
        self.doc.header['$LWDISPLAY'] = True
        self.doc.header['$DIMASSOC'] = 2
        self.doc.styles.new('TOWER_UNICODE', dxfattribs={'font': 'Arial Unicode.ttf'})
        self.doc.appids.new('TOWER_PART')
        for key, name in LAYERS.items():
            self.doc.layers.new(name, dxfattribs={
                'color': 7, 'lineweight': 13 if key in ('text', 'dimension', 'axis') else 25})
        self.doc.layers.get(LAYERS['viewport']).dxf.plot = 0
        self.msp = self.doc.modelspace()
        self.layout = self.doc.layouts.new(f'LANDMARK_A3_1_{scale}')
        self.layout.page_setup(size=PAPER, margins=(0, 0, 0, 0), units='mm')
        metadata = self.doc.ezdxf_metadata()
        metadata['REVISION'] = self.revision
        metadata['UNITS'] = 'mm'
        metadata['SCALE'] = f'1:{scale}; modelspace 1:1'
        metadata['SCOPE'] = '公表値を参考にした外観模式図。測量図・構造図・施工図ではない。'
        self.operations = []
        self.dimensions = []
        self.labels = []
        self.details = []
        self.frame()

    def paper_point(self, point):
        return (self.origin[0] + point[0] / self.scale,
                self.origin[1] + point[1] / self.scale)

    def operation(self, kind, points, **options):
        self.operations.append({'kind': kind, 'points': points, **options})

    def paper_poly(self, points, closed=False, color='#253444', width=.2, fill=None):
        self.operation('poly', points, closed=closed, color=color, width=width, fill=fill)
        self.layout.add_lwpolyline(points, close=closed,
            dxfattribs={'layer': LAYERS['sheet'], 'color': 256,
                        'lineweight': max(13, round(width * 100))})

    def paper_text(self, value, point, height=2.8, align='left'):
        self.operation('text', point, text=value, height=height, align=align)
        text = self.layout.add_text(value, dxfattribs={
            'layer': LAYERS['sheet_text'], 'color': 256,
            'style': 'TOWER_UNICODE', 'height': height})
        text.set_placement(point, align={
            'left': TextEntityAlignment.MIDDLE_LEFT,
            'center': TextEntityAlignment.MIDDLE_CENTER,
            'right': TextEntityAlignment.MIDDLE_RIGHT}[align])

    def poly(self, points, group='structure', closed=True, color='#4d6472',
             fill=None, width=.15, part=None):
        entity = self.msp.add_lwpolyline(points, close=closed,
            dxfattribs={'layer': LAYERS[group], 'color': 256})
        if part:
            entity.set_xdata('TOWER_PART', [(1000, part)])
        self.operation('poly', [self.paper_point(p) for p in points],
                       closed=closed, color=color, fill=fill, width=width)
        return entity

    def line(self, a, b, group='axis', color='#72818a', width=.13, part=None):
        entity = self.msp.add_line(a, b, dxfattribs={'layer': LAYERS[group], 'color': 256})
        if part:
            entity.set_xdata('TOWER_PART', [(1000, part)])
        self.operation('poly', [self.paper_point(a), self.paper_point(b)],
                       closed=False, color=color, width=width)

    def circle(self, center, radius, group='structure', color='#4d6472', part=None):
        entity = self.msp.add_circle(center, radius,
            dxfattribs={'layer': LAYERS[group], 'color': 256})
        if part:
            entity.set_xdata('TOWER_PART', [(1000, part)])
        self.operation('circle', self.paper_point(center), radius=radius/self.scale,
                       color=color, width=.15)

    def text(self, value, at, height=2.8, align='left', dimension=None, rotation=0):
        entity = self.msp.add_text(value, dxfattribs={
            'layer': LAYERS['text'], 'height': height*self.scale,
            'style': 'TOWER_UNICODE', 'color': 256, 'rotation': rotation})
        entity.set_placement(at, align=TextEntityAlignment.MIDDLE_CENTER
                             if align == 'center' else TextEntityAlignment.MIDDLE_LEFT)
        self.operation('text', self.paper_point(at), text=value, height=height,
                       align=align, dimension=dimension, rotation=rotation)

    def dim(self, a, b, distance, precision=0, text_height=2.8, arrow_size=1.25):
        """True aligned dimension; its value is never adjusted for sheet scale."""
        measure = hypot(b[0]-a[0], b[1]-a[1])
        if measure <= 0:
            raise ValueError('A landmark dimension must have positive length.')
        dim = self.msp.add_aligned_dim(a, b, distance=distance,
            dimstyle='EZDXF', override={
                'dimtxt': text_height*self.scale, 'dimasz': arrow_size*self.scale,
                'dimgap': .7*self.scale, 'dimexo': .6*self.scale,
                'dimexe': .7*self.scale, 'dimclrd': 7, 'dimclre': 7,
                'dimclrt': 7, 'dimdec': precision, 'dimlfac': 1,
                'dimlunit': 2, 'dimtad': 1, 'dimtxsty': 'TOWER_UNICODE'},
            dxfattribs={'layer': LAYERS['dimension'], 'color': 256})
        dim.render()
        for entity in self.doc.blocks.get(dim.dimension.dxf.geometry):
            entity.dxf.layer = LAYERS['dimension']
        normal = (-(b[1]-a[1])/measure, (b[0]-a[0])/measure)
        ends = [(p[0] + normal[0]*distance, p[1] + normal[1]*distance) for p in (a, b)]
        # The DXF already owns these lines through its native DIMENSION block.
        # Additional independent CAD lines would become stale when a user
        # edits the dimension, so the following operations are preview-only.
        self.operation('poly',[self.paper_point(p) for p in ends],
                       closed=False,color='#354957',width=.13)
        for start, end in zip((a, b), ends):
            self.operation('poly',[self.paper_point(start),self.paper_point(end)],
                           closed=False,color='#8a969f',width=.1)
        pa, pb = [self.paper_point(p) for p in ends]
        ux, uy = (pb[0]-pa[0])/(measure/self.scale), (pb[1]-pa[1])/(measure/self.scale)
        arrow_length=arrow_size+.05
        for tip, sign in ((pa, 1), (pb, -1)):
            self.operation('poly', [tip,
                (tip[0] + sign*ux*arrow_length - uy*.4, tip[1] + sign*uy*arrow_length + ux*.4),
                (tip[0] + sign*ux*arrow_length + uy*.4, tip[1] + sign*uy*arrow_length - ux*.4)],
                closed=True, color='#354957', fill='#354957', width=.1)
        center = ((ends[0][0]+ends[1][0])/2, (ends[0][1]+ends[1][1])/2)
        # Vertical values stay beside the line; all SVG values are mm, just
        # like the native DIMENSION, rather than mislabeled metre strings.
        vertical = abs(b[0]-a[0]) < 1e-6
        label = (center[0] - 2.0*self.scale if vertical else center[0],
                 center[1] if vertical else center[1] + 2.2*self.scale)
        self.operation('text', self.paper_point(label), text=f'{measure:,.{precision}f}',
                       height=text_height, align='center', dimension=measure,
                       rotation=90 if vertical else 0)
        self.dimensions.append(measure)

    def frame(self):
        name = self.parameters['names']['ja']
        view_name = '基座平面図' if self.view == 'plan' else '正立面図'
        title = f'{name} / {view_name}'
        self.labels = [name, view_name, '外観模式図', '公表値', '仮定', '単位 mm']
        self.paper_poly([(7.5,7.5),(412.5,7.5),(412.5,289.5),(7.5,289.5)], True, width=.7)
        self.paper_text(title, (16,277), 5)
        self.paper_text(f'{self.revision} | A3 | 1:{self.scale} | 単位 mm | 外観模式図', (16,267), 2.8)
        self.paper_text('公表値を参照 / 未測量・未計算 / NOT FOR CONSTRUCTION', (16,16), 2.6)
        self.paper_poly([(250,38),(401,38),(401,253),(250,253)], True, width=.2)
        self.paper_poly([(250,16),(401,16),(401,33),(250,33)], True, width=.2)
        self.paper_text(f'text-CAD | {self.revision} | 2026-10-30', (256,25), 2.7)
        self.paper_text('モデル寸法と図面の対応', (257,244), 3.5)
        deck_names = DECK_LABELS[self.tower_id]
        if self.tower_id == 'tokyo-tower' and self.view == 'elevation':
            floor_levels=self.parameters['detail']['main_floor_levels_mm']
            notes = [
                (232, '01 公表値とモデル座標'),
                (225, '公式案内: メイン150 m / トップ250 m'),
                (218, f'全高 {self.parameters["height_mm"]:,.0f} mm / 公表値'),
                (211, '施工GLの構架帯に関連付けた解釈的配置:'),
                (204, f'モデル下層{floor_levels[0]:,.0f} / 上層{floor_levels[1]:,.0f} mm'),
                (197, f'上部外殻参照{self.parameters["deck_levels_mm"][1]:,.0f} mm（H23帯）'),
                (190, '床との対応・5,000 mm層間はモデル仮定。'),
                (183, '公式案内値との換算・完成面実測ではない。'),
                (176, '部材断面・接合・外形は独自の仮定。'),
                (166, '02 メインデッキ付近 / 1:300'),
                (66, '宮地技報 No18 p86 図1 / 施工GL参照'),
                (58, '公式案内の150/250 mを変更するものではない。'),
                (50, 'CAD mm / X-Z正投影 / 編集可能な文字・寸法'),
                (42, '未測量・未計算 / tokyotower.co.jp/guidance/'),
            ]
            for y, note in notes:
                self.paper_text(note, (257, y), 2.7 if y >= 166 else 2.4)
            self.labels += ['メインデッキ付近','施工GL','公式案内値との換算・完成面実測ではない。']
            return
        if self.tower_id == 'tokyo-tower' and self.view == 'plan':
            floor_levels=self.parameters['detail']['main_floor_levels_mm']
            notes=[
                '01 公式案内の公表値',
                f'全高 {self.parameters["height_mm"]:,.0f} mm',
                'メインデッキ150 m / トップデッキ250 m',
                '', '02 モデル座標・参照資料',
                '施工GLの構架帯を参考に外殻を配置。',
                f'下層{floor_levels[0]:,.0f} / 上層{floor_levels[1]:,.0f} mm（解釈）',
                f'上部外殻参照{self.parameters["deck_levels_mm"][1]:,.0f} mm（H23帯）',
                'H11/H23からの床同定・層間は仮定。',
                '公式案内値との換算・完成面実測ではない。',
                '塔脚基準軸線間80,000 mmは図1参照。',
                '部材断面・接合・平面外形は仮定。',
                '', '03 座標とデータ',
                'CADモデル空間は実寸1:1、単位mm。',
                '平面はX/Y、立面はX/Zの正投影。',
                '方位はモデル用。測量方位は未設定。',
                '基座平面は上部投影外形も重ねて表示。',
                '文字・寸法はDXFで編集可能。',
                '', '04 参照資料（2026-10-30）',
                '宮地技報 No18 p86 図1（2002年改修）',
                'tokyotower.co.jp/guidance/',
                '観光床の完成面・現況構造は未測量。',
            ]
            for index,note in enumerate(notes):
                if note:self.paper_text(note,(257,232-index*7.5),2.7)
            self.labels += ['施工GL','公式案内値との換算・完成面実測ではない。']
            return
        if self.tower_id == 'tokyo-skytree' and self.view == 'elevation':
            notes = [
                (232, '01 公式公表値 / 全高 634,000 mm'),
                (225, '天望デッキ 350,000 / 天望回廊 450,000 mm'),
                (218, '開口・半径・部材寸法・曲率の詳細は仮定。'),
                (211, '未測量・未計算。施工図ではない。'),
                (201, '02 天望デッキ付近 / 1:500'),
                (132, 'FL 340,000 / 345,000 / 350,000 mm'),
                (122, '03 天望回廊付近 / 1:500'),
                (52, 'FL 445,000 → 450,000 mm / 上昇する回廊'),
                (44, 'tokyo-skytree.jp/floor/  /about/outline/'),
            ]
            for y,note in notes:
                self.paper_text(note,(257,y),2.7 if y>=201 else 2.5)
            self.labels += ['天望デッキ付近','天望回廊付近','上昇する回廊']
            return
        notes = [
            '01 公式公表値',
            f'全高  {self.parameters["height_mm"]:,.0f} mm',
            f'{deck_names[0]}  {self.parameters["deck_levels_mm"][0]:,.0f} mm',
            f'{deck_names[1]}  {self.parameters["deck_levels_mm"][1]:,.0f} mm',
            '', '02 図面の範囲',
            '塔高・展望標高は公式施設案内を参照。',
        ]
        if self.tower_id == 'tokyo-skytree':
            notes += ['基部三角形の辺長は約68,000 mm。',
                      '地上315,000 mmで円形に移行。',
                      '直径約32,000 mmは旧設計資料の制御値。',
                      '三角形・移行高さは東京都の紹介を参照。']
        else:
            notes += ['基脚間80,000 mmはこのモデルの仮定。',
                      'フットタウン外形・開口配置はモデル仮定。']
        notes += [
            '部材径・接合部・展望台外形・基礎は仮定。',
            '補間形状は原建物の実施設計と異なる。',
            '測量図・構造図・施工図ではない。',
            '', '03 座標とデータ',
            'CADモデル空間は実寸1:1、単位mm。',
            '平面はX/Y、立面はX/Zの正投影。',
            '方位はモデル用。測量方位は未設定。',
            '基座平面は上部投影外形も重ねて表示。',
            'DXFの文字・寸法は編集可能。',
            'SVGとPDFは同じ投影・標注を使用。',
            '', '04 参照資料（2026-10-30）',
        ]
        if self.tower_id == 'tokyo-tower':
            notes += ['tokyotower.co.jp/guidance/', 'tokyotower.co.jp/plan/towerpedia/']
        else:
            notes += ['東京スカイツリー公式 floor / 構造案内',
                      'tokyo-skytree.jp/floor/', '東京都 地域資源紹介']
        for index, note in enumerate(notes):
            if note:
                self.paper_text(note, (257,232-index*6.8), 2.7)

    def svg_fragments(self, operations):
        fragments = []
        for index, op in enumerate(operations):
            kind, points = op['kind'], op['points']
            color, width = op.get('color', '#1c2d3a'), op.get('width', .15)
            if kind == 'detail':
                x1,y1,x2,y2=points
                clip=f'detail-{self.tower_id}-{self.view}-{index}'
                fragments.append(f'<defs><clipPath id="{clip}"><rect x="{x1*4:g}" y="{(297-y2)*4:g}" width="{(x2-x1)*4:g}" height="{(y2-y1)*4:g}"/></clipPath></defs>')
                fragments.append(f'<g clip-path="url(#{clip})" data-detail-id="{op["id"]}">')
                fragments.extend(self.svg_fragments(op['operations']))
                fragments.append('</g>')
            elif kind == 'poly':
                tag = 'polygon' if op.get('closed') else 'polyline'
                coords = ' '.join(f'{x*4:.4f},{(297-y)*4:.4f}' for x,y in points)
                fragments.append(f'<{tag} points="{coords}" stroke="{color}" fill="{op.get("fill") or "none"}" stroke-width="{width*4:.3f}" stroke-linejoin="round"/>')
            elif kind == 'circle':
                x,y=points
                fragments.append(f'<circle cx="{x*4:.4f}" cy="{(297-y)*4:.4f}" r="{op["radius"]*4:.4f}" stroke="{color}" fill="none" stroke-width="{width*4:.3f}"/>')
            else:
                x,y=points[0]*4,(297-points[1])*4
                anchor={'left':'start','center':'middle','right':'end'}[op.get('align','left')]
                dimension = op.get('dimension')
                data = f' data-dimension-mm="{dimension:.6f}"' if dimension is not None else ''
                rotation = op.get('rotation',0)
                transform = f' transform="rotate({-rotation:g} {x:.4f} {y:.4f})"' if rotation else ''
                fragments.append(f'<text x="{x:.4f}" y="{y:.4f}" font-size="{op["height"]*4:.3f}" text-anchor="{anchor}" dominant-baseline="middle" fill="#172b3c"{data}{transform}>{html.escape(op["text"])}</text>')
        return fragments

    def svg(self):
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="1680" height="1188" '
            f'viewBox="0 0 1680 1188" data-units="mm" data-revision="{self.revision}">'
            '<style>text{font-family:"Arial Unicode MS","Noto Sans JP",sans-serif}</style>'
            '<rect width="1680" height="1188" fill="white"/>' + ''.join(self.svg_fragments(self.operations)) + '</svg>\n')

    def draw_pdf(self, pdf, operations=None):
        for op in self.operations if operations is None else operations:
            kind, points = op['kind'], op['points']
            pdf.saveState()
            pdf.setStrokeColor(HexColor(op.get('color','#1c2d3a')))
            pdf.setLineWidth(op.get('width',.15)*mm)
            if kind == 'detail':
                x1,y1,x2,y2=points
                path=pdf.beginPath();path.rect(x1*mm,y1*mm,(x2-x1)*mm,(y2-y1)*mm)
                pdf.clipPath(path,stroke=0,fill=0)
                self.draw_pdf(pdf,op['operations'])
            elif kind == 'poly':
                path=pdf.beginPath();path.moveTo(points[0][0]*mm,points[0][1]*mm)
                for x,y in points[1:]:path.lineTo(x*mm,y*mm)
                if op.get('closed'):path.close()
                if op.get('fill'):pdf.setFillColor(HexColor(op['fill']))
                pdf.drawPath(path,stroke=1,fill=int(bool(op.get('fill'))))
            elif kind == 'circle':
                pdf.circle(points[0]*mm,points[1]*mm,op['radius']*mm,stroke=1,fill=0)
            else:
                pdf.setFillColor(HexColor('#172b3c'))
                pdf.setFont('LandmarkUnicode',op['height']*mm)
                pdf.translate(points[0]*mm,points[1]*mm)
                pdf.rotate(op.get('rotation',0))
                draw={'left':pdf.drawString,'center':pdf.drawCentredString,'right':pdf.drawRightString}[op.get('align','left')]
                draw(0,-op['height']*.32*mm,op['text'])
            pdf.restoreState()

    def save(self, root=ROOT):
        suffix='steel_nodes' if self.view=='steel-nodes' else self.view
        stem = f'{self.parameters["file_stem"]}_{suffix}'
        dxf, svg = f'DXF/{stem}.dxf', f'output/svg/{stem}.svg'
        for rel in (dxf,svg):(root/rel).parent.mkdir(parents=True,exist_ok=True)
        # A fixed viewport matches the left drawing panel without scaling
        # native geometry or dimension measurements in modelspace.
        center=(0, self.parameters['height_mm']/2) if self.view=='elevation' else (0,0)
        view_size=(232,232)
        if self.view=='steel-nodes':
            center=self.index_viewport['view_center_mm']
            x1,y1,x2,y2=self.index_viewport['paper_bounds_mm']
            view_size=(x2-x1,y2-y1)
        viewport_center=(self.origin[0]+center[0]/self.scale,
                         self.origin[1]+center[1]/self.scale)
        self.layout.add_viewport(center=viewport_center,size=view_size,
            view_center_point=center,view_height=view_size[1]*self.scale,
            dxfattribs={'layer':LAYERS['viewport'],'status':2,'flags':16384})
        for detail in self.details:
            x1,y1,x2,y2=detail['paper_bounds_mm']
            viewport=self.layout.add_viewport(center=((x1+x2)/2,(y1+y2)/2),
                size=(x2-x1,y2-y1),view_center_point=detail['view_center_mm'],
                view_height=(y2-y1)*detail['scale'],
                dxfattribs={'layer':LAYERS['viewport'],'status':2,'flags':16384})
            # Overview dimensions must not be repeated across the enlarged
            # deck; only the shared component projection is shown here.
            for layer in detail['frozen_layers']:viewport.freeze(layer)
        self.doc.set_modelspace_vport(height=view_size[1]*self.scale,center=center)
        audit=self.doc.audit()
        if audit.has_errors:raise ValueError(f'Invalid landmark DXF: {audit.errors}')
        self.doc.saveas(root/dxf)
        (root/svg).write_text(self.svg(),encoding='utf-8')
        saved=ezdxf.readfile(root/dxf)
        actual=[float(dim.get_measurement()) for dim in saved.modelspace().query('DIMENSION')]
        if len(actual)!=len(self.dimensions) or any(abs(a-b)>.01 for a,b in zip(actual,self.dimensions)):
            raise ValueError('Saved native dimensions differ from source geometry.')
        return {'id':self.view,'dxf':dxf,'svg':svg,'scale':self.scale,
                'dimensions_mm':self.dimensions,'required_labels':self.labels,
                **({'sections':self.sections,'node_index':self.node_index,
                    'index_viewport':self.index_viewport} if self.view=='steel-nodes' else {}),
                **({'details':self.details} if self.details else {})}


def _projection(point, view):
    return (point[0],point[2]) if view=='elevation' else (point[0],point[1])


def _drawing_parts(tower_id):
    """Keep the editable principal projection legible at its printed scale."""
    return [part for part in component_specs(tower_id)
            if part.get('detail_level') not in ('micro','steel_micro')
            and not part.get('steel_node_id')
            and part.get('role') not in ('bolt', 'light_lens')]


def draw_components(drawing, parts=None):
    """Project CAD-owned component descriptions, never a separate silhouette."""
    parts=_drawing_parts(drawing.tower_id) if parts is None else parts
    order={'base':0,'core':1,'structure':2,'antenna':3,'decks':4}
    for part in sorted(parts,key=lambda p:order[p['group']]):
        group,name=part['group'],part['name']
        color=part.get('color','#9caeb8')
        # A transparent gallery is shown with its actual outlines. Opaque
        # glass fills would conceal the genuine sloping floor underneath.
        glass_outline=drawing.tower_id=='tokyo-skytree' and part.get('finish')=='glass'
        outline='#465c69'
        if drawing.tower_id=='tokyo-tower' and color.upper()=='#E34C25':outline='#af452d'
        if drawing.view=='plan' and group=='antenna':continue
        if part['kind']=='beam':
            start,end=part['start'],part['end']
            if drawing.view=='plan' and group=='structure' and min(start[2],end[2])>30000:continue
            a,b=_projection(start,drawing.view),_projection(end,drawing.view)
            length=hypot(b[0]-a[0],b[1]-a[1]);r=part['radius']
            if length<.001:
                drawing.circle(a,r,group,outline,name)
            else:
                nx,ny=-(b[1]-a[1])/length*r,(b[0]-a[0])/length*r
                drawing.poly([(a[0]+nx,a[1]+ny),(b[0]+nx,b[1]+ny),
                              (b[0]-nx,b[1]-ny),(a[0]-nx,a[1]-ny)],
                             group,color=outline,fill=color,width=.10,part=name)
        elif part['kind']=='box':
            x1,y1,z1,x2,y2,z2=part['bounds']
            lo,hi=(z1,z2) if drawing.view=='elevation' else (y1,y2)
            drawing.poly([(x1,lo),(x2,lo),(x2,hi),(x1,hi)],group,
                         color=outline,fill=color if drawing.view=='elevation' else None,part=name)
        elif part['kind']=='loft':
            sections=part['sections']
            if drawing.view=='elevation':
                left=[(min(p[0] for p in s['points']),s['z']) for s in sections]
                right=[(max(p[0] for p in s['points']),s['z']) for s in reversed(sections)]
                drawing.poly(left+right,group,color=outline,
                             fill=None if glass_outline else color,part=name)
            else:
                # Lowest/highest sections show both the footprint and the
                # projected canopy, using coordinates from the real loft.
                drawing.poly(sections[0]['points'],group,color=outline,width=.16,part=name)
                if sections[-1]['points']!=sections[0]['points']:
                    drawing.poly(sections[-1]['points'],group,color=outline,width=.12,part=name)
        elif part['kind']=='loft3d':
            # The ramp and its glass corridor have sloped section vertices.
            # Project real end/side faces instead of inventing horizontal
            # sections from their minimum/maximum heights.
            sections=part['sections']
            faces=[*sections]
            for start,end in zip(sections,sections[1:]):
                if len(start)!=len(end) or len(start)<3:
                    raise ValueError('A loft3d drawing needs matching polygon sections.')
                for index in range(len(start)):
                    following=(index+1)%len(start)
                    faces.append([start[index],start[following],end[following],end[index]])
            seen=set()
            for face in faces:
                projected=[_projection(point,drawing.view) for point in face]
                # Front and rear faces can coincide in an orthographic view.
                # Draw that exact polygon once, retaining the source part ID.
                key=tuple(sorted(set((float(x),float(y)) for x,y in projected)))
                if len(key)<2 or key in seen:continue
                seen.add(key)
                area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(projected,projected[1:]+projected[:1]))
                drawing.poly(projected,group,color=outline,
                             fill=color if drawing.view=='elevation' and abs(area)>1e-8 and not glass_outline else None,
                             width=.12,part=name)
        else:
            raise ValueError(f'Unsupported landmark primitive: {part["kind"]}')


class _DetailProjection:
    """Preview-only projection; DXF uses a locked viewport of the same msp."""
    def __init__(self,tower_id,scale,origin):
        self.tower_id,self.view,self.scale,self.origin=tower_id,'elevation',scale,origin
        self.operations=[]

    operation=TowerDrawing.operation
    paper_point=TowerDrawing.paper_point

    def poly(self,points,group='structure',closed=True,color='#4d6472',fill=None,width=.15,part=None):
        self.operation('poly',[self.paper_point(point) for point in points],
                       closed=closed,color=color,fill=fill,width=width)

    def line(self,a,b,group='axis',color='#72818a',width=.13,part=None):
        self.operation('poly',[self.paper_point(a),self.paper_point(b)],
                       closed=False,color=color,width=width)

    def circle(self,center,radius,group='structure',color='#4d6472',part=None):
        self.operation('circle',self.paper_point(center),radius=radius/self.scale,color=color,width=.15)


def _projected_bounds(part):
    if part['kind']=='box':
        x1,_,z1,x2,_,z2=part['bounds']
        return x1,z1,x2,z2
    if part['kind']=='beam':
        points=(part['start'],part['end']);radius=part['radius']
        return min(p[0] for p in points)-radius,min(p[2] for p in points)-radius, \
            max(p[0] for p in points)+radius,max(p[2] for p in points)+radius
    sections=part['sections']
    if part['kind']=='loft3d':
        vertices=[point for section in sections for point in section]
        return min(point[0] for point in vertices),min(point[2] for point in vertices), \
            max(point[0] for point in vertices),max(point[2] for point in vertices)
    return min(p[0] for section in sections for p in section['points']),min(s['z'] for s in sections), \
        max(p[0] for section in sections for p in section['points']),max(s['z'] for s in sections)


def _add_component_detail(drawing,ident,bounds,scale,center,prefix,levels=None):
    """Inset is a second view, never a scaled copy of editable CAD geometry."""
    x1,y1,x2,y2=bounds
    paper_center=[(x1+x2)/2,(y1+y2)/2]
    width,height=(x2-x1)*scale,(y2-y1)*scale
    world=[center[0]-width/2,center[1]-height/2,
           center[0]+width/2,center[1]+height/2]
    candidates=_drawing_parts(drawing.tower_id)
    selected=[]
    for part in candidates:
        a,b,c,d=_projected_bounds(part)
        # Prefixes include group and trailing underscore: "main_" must
        # never accidentally match a maintenance platform or another deck.
        context=part['group'] in ('structure','core')
        if not context and not part['name'].startswith(prefix):continue
        if a<=world[2] and c>=world[0] and b<=world[3] and d>=world[1]:selected.append(part)
    detail=_DetailProjection(drawing.tower_id,scale,
                            (paper_center[0]-center[0]/scale,paper_center[1]-center[1]/scale))
    draw_components(detail,selected)
    drawing.operation('detail',bounds,id=ident,operations=detail.operations)
    drawing.paper_poly([(x1,y1),(x2,y1),(x2,y2),(x1,y2)],True,width=.2)
    drawing.details.append({'id':ident,'view':'elevation','scale':scale,
        'source_geometry_revision':drawing.revision,'paper_bounds_mm':bounds,
        'view_center_mm':center,'bounds_mm':world,
        'source_parts':[part['name'] for part in selected],
        'frozen_layers':[LAYERS[key] for key in ('dimension','text','axis')],
        'small_parts_omitted':True,
        **({'levels_mm':levels,'source_part_prefix':prefix} if levels is not None else {})})


def add_main_deck_detail(drawing):
    _add_component_detail(drawing,'main_deck',[257,75,394,159],300,[0,TOWERS['tokyo-tower']['deck_levels_mm'][0]],
                          'decks:main_')


def add_skytree_details(drawing):
    _add_component_detail(drawing,'tembo_deck',[257,139,394,195],500,[0,345000],
                          'decks:tembo_deck_',[340000,345000,350000])
    _add_component_detail(drawing,'tembo_galleria',[257,59,394,115],500,[0,449000],
                          'decks:tembo_galleria_',[445000,450000])


def build_plan(tower_id):
    p=TOWERS[tower_id]
    d=TowerDrawing(tower_id,'plan',500,(130,157))
    draw_components(d)
    radius=52000
    # Leave a clear gap between the X axis and Tokyo's right-hand vertical
    # 80m dimension text instead of drawing the axis through its digits.
    axis_end=43500 if tower_id=='tokyo-tower' else radius
    d.line((-radius,0),(axis_end,0))
    # Keep Skytree's axis clear of the base-side dimension and its caption.
    axis_bottom=-24500 if tower_id=='tokyo-skytree' else -48000
    d.line((0,axis_bottom),(0,48000))
    d.text('X', (axis_end+1000,2200) if tower_id=='tokyo-tower' else (radius+1500,0),height=3)
    d.text('Y', (0,53000 if tower_id=='tokyo-skytree' else 51000),height=3,align='center')
    feet=ring_points(tower_id,0)
    if tower_id=='tokyo-skytree':
        feet=feet[::8]
        d.poly(feet,'axis',color='#6b7b85',width=.22)
        # These are actual 3D support points, so this dimension measures a
        # 68m triangle edge rather than its 78.5m circumcircle diameter.
        d.dim(feet[1],feet[2],-8500)
        d.text('基部三角形の辺長（約）', (0,-36500),height=2.8,align='center')
    else:
        d.dim(feet[0],feet[1],-8500)
        d.dim(feet[1],feet[2],-8500)
    d.paper_text('基座・足元 / 上部の投影外形を重ねた模式配置', (21,48),2.8)
    d.paper_text('方位はモデル軸のみ。実際の敷地方位・配置とは異なります。', (21,39),2.5)
    return d


def build_elevation(tower_id):
    p=TOWERS[tower_id]
    scale=1500 if tower_id=='tokyo-tower' else 3000
    d=TowerDrawing(tower_id,'elevation',scale,(130,28))
    draw_components(d)
    width=p['base_width_mm']
    d.line((-width*.75,0),(width*.75,0))
    d.line((0,-3000),(0,p['height_mm']+5000),color='#82919b',width=.1)
    d.dim((0,0),(0,p['height_mm']),width/2+26*scale)
    for index,(level,label) in enumerate(zip(p['deck_levels_mm'],DECK_LABELS[tower_id])):
        d.dim((0,0),(0,level),-(width/2+(30+index*21)*scale))
        # Short level ticks sit beside the silhouette; names and dimension
        # numbers have independent positions to avoid double annotations.
        r=16000 if tower_id=='tokyo-tower' else 23000
        d.line((r,level),(r+6*scale,level),'axis',color='#526a7b')
        label_x=100 if tower_id=='tokyo-tower' else 112
        plotted_label=(['主展望外殻（モデル）','上部外殻（モデル）'][index]
                       if tower_id=='tokyo-tower' else label)
        d.text(plotted_label,((label_x-d.origin[0])*scale,level+3*scale),height=2.6,align='center')
        d.labels.append(plotted_label)
    d.paper_text('基準 GL ±0', (21,29),2.6)
    d.paper_text('正投影 / 展望施設の形状・鉄骨径は模式表現', (21,24),2.6)
    if tower_id=='tokyo-tower':add_main_deck_detail(d)
    else:add_skytree_details(d)
    return d


def _primitive_faces(part):
    """Faceted XYZ faces matching the CAD exporter, including octagonal beams."""
    kind=part['kind']
    if kind=='box':
        x1,y1,z1,x2,y2,z2=part['bounds']
        vertices=[[x1,y1,z1],[x2,y1,z1],[x2,y2,z1],[x1,y2,z1],
                  [x1,y1,z2],[x2,y1,z2],[x2,y2,z2],[x1,y2,z2]]
        return [[vertices[i] for i in face] for face in
                ((0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))]
    if kind=='beam':
        a,b=part['start'],part['end'];delta=[b[i]-a[i] for i in range(3)]
        length=sqrt(sum(value*value for value in delta));direction=[value/length for value in delta]
        reference=[0.,0.,1.] if abs(direction[2])<.95 else [1.,0.,0.]
        cross=lambda u,v:[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
        u=cross(direction,reference);norm=sqrt(sum(value*value for value in u));u=[value/norm for value in u]
        v=cross(direction,u);radius=part['radius']
        sections=[[[center[k]+radius*(u[k]*cos(2*pi*i/8)+v[k]*sin(2*pi*i/8))
                    for k in range(3)] for i in range(8)] for center in (a,b)]
    elif kind=='loft':
        sections=[[[x,y,section['z']] for x,y in section['points']] for section in part['sections']]
    elif kind=='loft3d':sections=part['sections']
    else:raise ValueError(f'Unsupported steel-node primitive: {kind}')
    faces=[sections[0],sections[-1]]
    for a,b in zip(sections,sections[1:]):
        if len(a)!=len(b):raise ValueError('Steel-node CAD faces need matching sections.')
        faces.extend([[a[i],a[(i+1)%len(a)],b[(i+1)%len(a)],b[i]] for i in range(len(a))])
    return faces


def _local_projection(point,frame):
    delta=[point[i]-frame['origin_mm'][i] for i in range(3)]
    return tuple(sum(delta[i]*frame[axis][i] for i in range(3)) for axis in ('u','v'))


def _clip_polygon(points,bounds):
    """Clip projected context faces only; node plates/rivets stay unaltered."""
    result=list(points)
    for axis,limit,sign in ((0,bounds[0],1),(0,bounds[2],-1),(1,bounds[1],1),(1,bounds[3],-1)):
        source=result;result=[]
        if not source:break
        previous=source[-1];previous_inside=sign*(previous[axis]-limit)>=-1e-8
        for current in source:
            current_inside=sign*(current[axis]-limit)>=-1e-8
            if current_inside!=previous_inside:
                fraction=(limit-previous[axis])/(current[axis]-previous[axis])
                result.append(tuple(previous[i]+fraction*(current[i]-previous[i]) for i in range(2)))
            if current_inside:result.append(tuple(current))
            previous,previous_inside=current,current_inside
    return result


class _NativeNodeProjection(_DetailProjection):
    """A translated 1:1 CAD projection isolated from the tower's index view."""
    def __init__(self,owner,node,scale,paper_origin,native_translation):
        super().__init__('tokyo-tower',scale,
                         tuple(paper_origin[i]-native_translation[i]/scale for i in range(2)))
        self.owner,self.node=owner,node
        self.doc,self.msp,self.dimensions=owner.doc,owner.msp,owner.dimensions
        self.native_translation=native_translation

    def native_point(self,point):
        return tuple(point[i]+self.native_translation[i] for i in range(2))

    def poly(self,points,group='structure',closed=True,color='#4d6472',fill=None,width=.15,part=None):
        entity=TowerDrawing.poly(self,[self.native_point(point) for point in points],
                                group,closed,color,fill,width,part)
        entity.set_xdata('STEEL_NODE',[(1000,self.node['id'])])
        return entity

    def dim(self,a,b,distance):
        TowerDrawing.dim(self,self.native_point(a),self.native_point(b),distance,
                         precision=1,text_height=2.2,arrow_size=.8)


class SteelNodeDrawing(TowerDrawing):
    def frame(self):
        self.labels=['東京タワー','鋼接合部・節点詳細','外観模式図','公表値','仮定','単位 mm']
        self.paper_poly([(7.5,7.5),(412.5,7.5),(412.5,289.5),(7.5,289.5)],True,width=.7)
        self.paper_text('東京タワー / 鋼接合部・節点詳細', (16,277),5)
        self.paper_text(f'{self.revision} | A3 | モデル空間 1:1 | 単位 mm | 外観模式図',(16,267),2.8)
        levels=self.parameters['deck_levels_mm']
        self.paper_text(f'公表値: 全高333,000 mm・公式案内150/250 m / モデル外殻{levels[0]/1000:g}/{levels[1]/1000:g} mは解釈配置（完成面未測量）。',(16,257),2.5)
        self.paper_text('板面の正投影。板厚は注記、板幅とリベット心々は実寸の編集可能な寸法。',(153,29),2.5)
        self.paper_text('未測量・未計算 / NOT FOR CONSTRUCTION / 原建物の接合詳細ではありません。',(16,16),2.6)


def _add_steel_node_detail(drawing,node,parts,bounds,preferred_scale,index):
    frame=node['local_frame'];source_by_name={part['name']:part for part in parts}
    selected=[source_by_name[name] for name in node['part_names']]
    all_points=[_local_projection(vertex,frame) for part in selected
                for face in _primitive_faces(part) for vertex in face]
    extent=[min(p[0] for p in all_points),min(p[1] for p in all_points),
            max(p[0] for p in all_points),max(p[1] for p in all_points)]
    x1,y1,x2,y2=bounds;paper_center=((x1+x2)/2,(y1+y2)/2)
    scale=next((value for value in (10,15,20,25,30)
                if value>=preferred_scale and (extent[2]-extent[0]+450)/value<=x2-x1
                and (extent[3]-extent[1]+450)/value<=y2-y1),None)
    if scale is None:raise ValueError(f'{node["id"]} does not fit the 1:10–1:30 steel-node sheet.')
    center=((extent[0]+extent[2])/2,(extent[1]+extent[3])/2)
    roi=[center[0]-(x2-x1)*scale/2,center[1]-(y2-y1)*scale/2,
         center[0]+(x2-x1)*scale/2,center[1]+(y2-y1)*scale/2]
    translation=[1000000+index*20000,0]
    projection=_NativeNodeProjection(drawing,node,scale,
                                     tuple(paper_center[i]-center[i]/scale for i in range(2)),translation)
    contexts=[source_by_name[name] for name in node['member_names'] if name in source_by_name]
    source_parts=[]
    for part,is_context in [(part,True) for part in contexts]+[(part,False) for part in selected]:
        seen=set();saved=False
        for face in _primitive_faces(part):
            points=[_local_projection(vertex,frame) for vertex in face]
            if is_context:points=_clip_polygon(points,roi)
            key=tuple(sorted(set((round(x,8),round(y,8)) for x,y in points)))
            if len(key)<2 or key in seen:continue
            seen.add(key);saved=True
            projection.poly(points,color='#9aa5ad' if is_context else '#8c3d29',
                            width=.09 if is_context else .16,part=part['name'])
        if saved:source_parts.append(part['name'])
    features=[]
    for feature in node['feature_dimensions']:
        a,b=[_local_projection(point,frame) for point in feature['points_mm']]
        measure=hypot(b[0]-a[0],b[1]-a[1])
        actual=sqrt(sum((feature['points_mm'][1][i]-feature['points_mm'][0][i])**2 for i in range(3)))
        if abs(measure-actual)>1e-4:raise ValueError('A steel-node dimension is foreshortened in its selected projection.')
        normal=(-(b[1]-a[1])/measure,(b[0]-a[0])/measure)
        corners=[(extent[0],extent[1]),(extent[2],extent[1]),(extent[2],extent[3]),(extent[0],extent[3])]
        projections=[sum(p[i]*normal[i] for i in range(2)) for p in corners]
        target=(min(projections)-150 if feature['kind']=='plate_width' else max(projections)+150)
        distance=target-sum(a[i]*normal[i] for i in range(2))
        projection.dim(a,b,distance)
        features.append({**feature,'measurement_mm':measure,'projected_points_mm':[a,b],
                         'native_points_mm':[projection.native_point(point) for point in (a,b)]})
    drawing.operation('detail',bounds,id=node['id'],operations=projection.operations)
    drawing.paper_poly([(x1,y1),(x2,y1),(x2,y2),(x1,y2)],True,width=.2)
    label=node['names']['ja'];drawing.paper_text(f'{node["id"]} {label} / 1:{scale}',(x1,y2+7),2.8)
    thickness=node['parameters']['plate_thickness_mm']
    drawing.paper_text(f'板厚 t={thickness:g} mm / 板幅・心々寸法 mm / 全て仮定',(x1,y1-7),2.3)
    drawing.labels += [node['id'],label]
    drawing.details.append({'id':node['id'],'view':'local-orthographic','scale':scale,
        'source_geometry_revision':drawing.revision,'paper_bounds_mm':bounds,
        'view_center_mm':[translation[i]+center[i] for i in range(2)],
        'bounds_mm':[translation[0]+roi[0],translation[1]+roi[1],translation[0]+roi[2],translation[1]+roi[3]],
        'source_parts':source_parts,'node_part_names':node['part_names'],
        'context_part_names':[part['name'] for part in contexts],'context_clipped':True,
        'local_frame':frame,'native_translation_mm':translation,'local_roi_mm':roi,
        'feature_dimensions':features,'plate_thickness_mm':thickness,'frozen_layers':[],
        'small_parts_omitted':False,'status':'original_assumption_not_original_design'})


def build_steel_nodes():
    nodes=geometry_manifest('tokyo-tower')['steel_nodes']
    if len(nodes)!=20:raise ValueError('The Tokyo steel-node index must contain twenty catalogued nodes.')
    parts=component_specs('tokyo-tower')
    minimum=min(node['anchor_mm'][2] for node in nodes)-10000
    maximum=max(node['anchor_mm'][2] for node in nodes)+15000
    scale=max(1000,100*int((maximum-minimum)/19300+1))
    center=(0,(minimum+maximum)/2);bounds=[17,45,143,239]
    paper_center=((bounds[0]+bounds[2])/2,(bounds[1]+bounds[3])/2)
    origin=tuple(paper_center[i]-center[i]/scale for i in range(2))
    drawing=SteelNodeDrawing('tokyo-tower','steel-nodes',scale,origin)
    drawing.doc.appids.new('STEEL_NODE')
    drawing.sections=[{'id':node['id'],'type':node['type'],'names':node['names'],
                       'anchor_mm':node['anchor_mm'],'part_names':node['part_names'],
                       'member_names':node['member_names']} for node in nodes]
    drawing.node_index=[{'id':node['id'],'anchor_mm':node['anchor_mm']} for node in nodes]
    drawing.index_viewport={'paper_bounds_mm':bounds,'view_center_mm':center,'scale':scale,
                            'source_parts':[part['name'] for part in _drawing_parts('tokyo-tower')]}
    # A clipped index shows the actual lower tower containing all 20 nodes.
    index_projection=_DetailProjection('tokyo-tower',scale,origin)
    draw_components(index_projection)
    drawing.operation('detail',bounds,id='node-index',operations=index_projection.operations)
    # Reuse the exact same native principal projection; its preview was
    # captured above so it cannot paint outside the index frame.
    operation_start=len(drawing.operations);drawing.view='elevation'
    draw_components(drawing);drawing.view='steel-nodes'
    del drawing.operations[operation_start:]
    drawing.paper_poly([(17,45),(143,45),(143,239),(17,239)],True,width=.2)
    drawing.paper_text(f'節点位置 / 下部〜主展望台 / 1:{scale}',(17,247),2.8)
    grouped={}
    for node in nodes:
        key=(round(node['anchor_mm'][0],1),round(node['anchor_mm'][2],1))
        grouped.setdefault(key,[]).append(node)
    for (x,z),group in grouped.items():
        point=drawing.paper_point((x,z));right=x>=0;label_x=123 if right else 20
        endpoint_x=121 if right else 38
        drawing.paper_poly([point,(endpoint_x,point[1])],width=.1)
        for i,node in enumerate(group):
            drawing.paper_text(node['id'],(label_x,point[1]+(len(group)-1)*1.5-i*3),2.1)
    configurations=[('TT-N01',[153,151,274,239],20),('TT-N05',[282,151,403,239],20),
                    ('TT-N13',[153,45,274,133],15),('TT-N17',[282,45,403,133],20)]
    by_id={node['id']:node for node in nodes}
    for index,(ident,panel,preferred_scale) in enumerate(configurations):
        _add_steel_node_detail(drawing,by_id[ident],parts,panel,preferred_scale,index)
    return drawing


def generate(root=ROOT,tower_ids=None):
    root=Path(root)
    if not FONT.is_file():
        raise ValueError('Set TEXT_CAD_CJK_FONT to a usable CJK TrueType font before regenerating tower drawings.')
    pdfmetrics.registerFont(TTFont('LandmarkUnicode',str(FONT)))
    outputs=[]
    selected=list(TOWERS) if tower_ids is None else list(tower_ids)
    if any(tower_id not in TOWERS for tower_id in selected):
        raise ValueError('Unknown landmark selection.')
    for tower_id in selected:
        p=TOWERS[tower_id]
        revision=revision_for(tower_id)
        sources=[*geometry_source_paths(tower_id),'src/generate_tower_plans.py']
        source_snapshot={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in sources}
        sheets=[build_plan(tower_id),build_elevation(tower_id)]
        if tower_id=='tokyo-tower':sheets.append(build_steel_nodes())
        drawings=[sheet.save(root) for sheet in sheets]
        pdf_path=f'output/pdf/{p["file_stem"]}_sheets.pdf'
        (root/pdf_path).parent.mkdir(parents=True,exist_ok=True)
        pdf=canvas.Canvas(str(root/pdf_path),pagesize=(420*mm,297*mm),invariant=1)
        pdf.setTitle(p['names']['ja']+' / 基座平面・正立面'+('・鋼節点' if tower_id=='tokyo-tower' else '')+' / '+revision)
        pdf.setAuthor('text-CAD')
        for sheet in sheets:sheet.draw_pdf(pdf);pdf.showPage()
        pdf.save()
        paths=[d[k] for d in drawings for k in ('dxf','svg')]+[pdf_path]
        sha=lambda rel:hashlib.sha256((root/rel).read_bytes()).hexdigest()
        # Code lives in ROOT even when tests render into an isolated directory.
        if any(hashlib.sha256((ROOT/s).read_bytes()).hexdigest()!=value
               for s,value in source_snapshot.items()):
            raise RuntimeError('Tower drawing sources changed during export; regenerate from a stable source snapshot.')
        metadata={'schema_version':1,'revision':revision,'units':'mm',
            'status':'reference_concept_only','source_geometry_revision':revision,
            'source_sha256':source_snapshot,
            'artifacts':{rel:{'sha256':sha(rel),'bytes':(root/rel).stat().st_size} for rel in paths},
            'drawings':drawings}
        metadata_path=root/f'output/review/{p["file_stem"]}_drawings.json'
        metadata_path.parent.mkdir(parents=True,exist_ok=True)
        metadata_path.write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
        outputs.extend(paths)
    print(json.dumps({'revisions':{tower_id:TOWERS[tower_id].get('revision',REVISION) for tower_id in selected},'outputs':outputs},ensure_ascii=False))
    return outputs


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',action='append',choices=list(TOWERS),help='Regenerate only the selected landmark; repeat to select both.')
    args=parser.parse_args()
    generate(tower_ids=args.model)
