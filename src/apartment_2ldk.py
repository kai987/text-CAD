"""Generate the A01 2LDK concept: STEP, GLB, editable DXF, PDF and previews.

Run from the repository root: .venv/bin/python src/apartment_2ldk.py
The parametric source is lib/apartment_plan.py; no house files are modified.
"""
from pathlib import Path
import hashlib
import json
import math
import os
import struct
import subprocess
import sys

import ezdxf
import fitz
from cadgen import glb, step
from ezdxf.enums import TextEntityAlignment
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from generate_plans import Drawing, FONT
from house_3d import STATIC_PARTS, restore_glb_hierarchy
from lib.apartment_geometry import assembly
from lib.apartment_plan import P, apartment_plan, dimensions, manifest, window_specs
from lib.house_geometry import polygons
from lib.jp_drafting import LAYERS, SOURCE_URL, STANDARD

ROOT=Path(__file__).resolve().parents[1]
MATERIALS={'definitions':{
    'glass':{'name':'Concept glazing','roughness':.15,'opacity':.45},
    'wall_finish':{'name':'Concept plaster','roughness':.86},
    'wood':{'name':'Concept timber','roughness':.65}},
    'assignments':[
        {'targets':['#F1:external_walls','#F1:partition_walls','#ceiling'],'material':'wall_finish'},
        {'targets':['#F1:floor_slab','#F1:doors','#F1:storage_fixtures'],'material':'wood'},
        {'targets':[f'#F1:W{i:02d}:glass_{j}' for i in range(1,5) for j in (1,2)],'material':'glass'}]}


@step(out='../STEP/apartment_2ldk.step',materials=MATERIALS,animation=STATIC_PARTS)
@glb(out='../GLB/apartment_2ldk.glb')
def apartment_2ldk():
    return assembly()


def model():
    apartment_2ldk()
    step_path=ROOT/'STEP/apartment_2ldk.step'
    glb_path=ROOT/'GLB/apartment_2ldk.glb'
    glb.build(step_path,glb_path,animation={'clip':'named_parts','fps':1,'seconds':1},force=True)
    details=restore_glb_hierarchy(step_path,glb_path)
    # The shared hierarchy restorer uses the original house's display metadata.
    data=glb_path.read_bytes(); size,kind=struct.unpack_from('<II',data,12)
    document=json.loads(data[20:20+size]);document['scenes'][0]['name']='apartment_2ldk'
    document['asset']['extras']['source']='Parametric Japanese 2LDK concept A01; demonstration dimensions'
    encoded=json.dumps(document,ensure_ascii=False,separators=(',',':')).encode()
    encoded += b' '*((-len(encoded))%4)
    body=struct.pack('<II',len(encoded),kind)+encoded+data[20+size:]
    glb_path.write_bytes(struct.pack('<4sII',b'glTF',2,12+len(body))+body)
    return details


def paper_text(c,value,x,y,height=2.5):
    c.setFillColorRGB(0,0,0);c.setFont('HouseUnicode',height*mm)
    c.drawString(x*mm,y*mm,value)


def plan():
    floor,_=apartment_plan();d=dimensions()
    area=manifest()['areas']
    pdfmetrics.registerFont(TTFont('HouseUnicode',str(FONT)))
    pdf_path=ROOT/'output/pdf/apartment_2ldk_plan.pdf'
    c=canvas.Canvas(str(pdf_path),pagesize=(420*mm,297*mm),invariant=1)
    c.setTitle('日本の集合住宅 2LDK - A01 参考計画')
    c.setAuthor('text-to-cad / parametric demonstration')
    c.setFillColorRGB(1,1,1);c.rect(0,0,420*mm,297*mm,stroke=0,fill=1)
    c.setStrokeColorRGB(0,0,0);c.setLineWidth(.25*mm)
    c.rect(7.5*mm,7.5*mm,405*mm,282*mm)
    g=Drawing(c);g.ox,g.oy=40*mm,80*mm
    g.doc.ezdxf_metadata()['REVISION']='A01'
    g.doc.ezdxf_metadata()['SCOPE']='単一住戸2LDK参考計画・全寸法仮定。土木CAD共通規定の準用。'
    balcony=next(r for r in floor.rooms if r.id=='balcony')
    g.rect(balcony.shape.bounds,'FURNITURE',fill='#F4F4F4')
    for bounds in [(0,-P.balcony_depth,P.width,-P.balcony_depth+100),
                   (0,-P.balcony_depth+100,100,0),(P.width-100,-P.balcony_depth+100,P.width,0)]:
        g.rect(bounds,'WALL',fill='#D8D8D8')
    for polygon in polygons(floor.walls):
        g.poly(polygon.exterior.coords,'WALL',fill='#D8D8D8')
        for ring in polygon.interiors:g.poly(ring.coords,'WALL',fill='#FFFFFF')
    for w in window_specs():
        x,y,width=w['start'],w['at'],w['width']
        for offset in (-35,35):g.line((x,y+offset),(x+width,y+offset),'WINDOW')
        g.line((x+width/2,y-35),(x+width/2,y+35),'WINDOW')
    for door in floor.doors:
        if door.kind=='open':continue
        s,w,a=door.start,door.width,door.at
        if door.kind=='swing':
            g.line((s,a),(s,a+w),'DOOR');g.arc((s,a),w,0,90)
        elif door.axis=='h':
            # D08 is an exposed track on the LDK (south) side.
            y=a-P.internal_wall/2-25
            g.line((s,y),(s+w,y),'DOOR')
            target=s+door.direction*w
            g.line((target,y-25),(target+w,y-25),'DOOR')
        else:
            # West-side doors use the east face; east-side doors the west face.
            x=a+(P.internal_wall/2+25)*(1 if a<d['hl'] else -1)
            g.line((x,s),(x,s+w),'DOOR')
            target=s+door.direction*w
            g.line((x+15,target),(x+15,target+w),'DOOR')
    for name,bounds in floor.fixtures:
        g.rect(bounds,'FURNITURE',fill='#F4F4F4')
        x1,y1,x2,y2=bounds
        if name in ('浴槽','洗面'):
            g.rect((x1+80,y1+80,x2-80,y2-80),'FURNITURE')
        if name in ('収納','靴収納','収納棚'):
            # Vertical labels avoid squeezing Japanese glyphs across narrow cabinets.
            cx=(x1+x2)/2;cy=(y1+y2)/2
            for i,ch in enumerate(name):g.text(ch,(cx,cy+(len(name)-1)*65-i*130),90)
        else:g.text(name,((x1+x2)/2,(y1+y2)/2),90)
    g.line((d['hl'],d['fy']),(d['hr'],d['fy']),'FURNITURE')
    for room in floor.rooms:
        x,y=room.label
        g.text(room.name,(x,y+180),175)
        g.text(f'{room.area:.2f} m2',(x,y-35),125)
        g.text(room.size_note,(x,y-225),125)
    # Keep door IDs and rough widths inside the cropped, editable plan too.
    door_labels={
        'D01':(d['hr']-300,d['ym']-120),
        'D02':((d['hl']+d['hr'])/2,d['lt']-250),
        'D03':(d['west']-450,d['bb']+580),
        'D04':(d['east']+450,d['bb']+580),
        'D05':(d['west']-500,d['wb']+100),
        'D06':(d['br']-450,d['wb']+80),
        'D07':(d['east']+500,d['wb']+100),
        'D08':(d['tr']+800,d['lt']-180),
    }
    for door in floor.doors:g.text(f'{door.id} / {door.width:g}',door_labels[door.id],90)
    g.dim((0,P.depth),(P.width,P.depth),(0,P.depth+1500))
    g.dim((0,0),(0,P.depth),(-700,0),90)
    g.dim((P.width,-P.balcony_depth),(P.width,0),(P.width+500,0),90)
    for lo,hi in [(d['e'],d['west']),(d['hl'],d['hr']),(d['east'],d['xm'])]:
        g.dim((lo,d['ym']),(hi,d['ym']),(0,P.depth+1100))
    g.line((P.width+700,P.depth-300),(P.width+700,P.depth+250),'NORTH')
    g.line((P.width+700,P.depth+250),(P.width+620,P.depth+50),'NORTH')
    g.line((P.width+700,P.depth+250),(P.width+780,P.depth+50),'NORTH')
    g.text('N*',(P.width+700,P.depth+440),125)
    g.text('2LDK / 平面図 / A01',(P.width/2,-P.balcony_depth-700),250)
    g.text('寸法単位 mm / 全寸法・方位は仮定',(P.width/2,-P.balcony_depth-1030),125)
    # The A3 layout retains real editable TEXT and DIMENSION entities.
    layout=g.doc.layouts.new('JP_A3_APARTMENT_1_50')
    layout.page_setup(size=(420,297),margins=(0,0,0,0),units='mm')
    layout.add_lwpolyline([(7.5,7.5),(412.5,7.5),(412.5,289.5),(7.5,289.5)],close=True,
                         dxfattribs={'color':7,'lineweight':25})
    vp=layout.add_viewport(center=(120,159),size=(210,262),
                           view_center_point=((120-40)*50,(159-80)*50),view_height=262*50)
    vp.dxf.flags |= 16384
    def sheet_text(value,x,y,height=2.5):
        paper_text(c,value,x,y,height)
        layout.add_text(value,dxfattribs={'height':height,'style':'HOUSE_UNICODE','color':7,
                         'lineweight':13}).set_placement((x,y),align=TextEntityAlignment.LEFT)
    sheet_text('日本の集合住宅 / 2LDK',235,272,5)
    sheet_text('単一住戸の参考計画',235,263,3.5)
    lines=[
        '面積の区分 / AREA DEFINITIONS',
        f'外輪郭面積  {area["outline"]:.2f} m2  ({P.width:g} × {P.depth:g})',
        f'室内正味面積  {area["interior"]:.2f} m2  (壁を除く各室合計)',
        f'バルコニー  {area["balcony"]:.2f} m2  (別計上・板面投影)',
        '室内面積は収納・設備の占有部分を含む。',
        '登記面積・専有面積・法定床面積ではない。',
        '', '計画条件 / DEMONSTRATION ASSUMPTIONS',
        '全寸法・北向・北側共用廊下・南側バルコニーは仮定。',
        f'階高{P.storey_height:g} / 室内有効高さ{P.clear_height:g} / 床スラブ{P.slab_thickness:g}。',
        f'外壁・戸境壁{P.external_wall:g} / 間仕切{P.internal_wall:g} / 廊下幅{P.hall_width:g}。',
        f'玄関の靴収納350を除いた通路は{P.hall_width-350:g}。',
        f'浴室{P.bath_width:g} × {d["wt"]-d["wb"]:g} / 洗面脱衣{d["west"]-d["br"]-P.internal_wall:g} × {d["wt"]-d["wb"]:g}。',
        '洋室の北窓は腰高1100、LDK南面は掃き出し窓。',
        '北側出入口は外開き。共用廊下の寸法は未検討。',
        '移動経路: 玄関 → 廊下 → 両洋室・洗面・便所・LDK。',
        'LDK → 納戸・バルコニー / 洗面脱衣 → 浴室。',
        '', '建具 / OPENINGS (rough widths in mm)',
        f'D01 玄関900 / D02 LDK開口{P.hall_width:g}',
        'D03 洋室1 800 / D04 洋室2 800',
        'D05 洗面800 / D06 浴室750 / D07 便所700',
        'D08 納戸800: LDK側の外付けレールで西へ引く。',
        '室内引戸は外付け概念。3Dの戸は閉位置で表示。',
        '', '図面情報 / DRAWING INFORMATION',
        'A3 横 420 × 297 / 縮尺1:50 / 単位mm / A01',
        '令和8年10月5日 / text-to-cad + ezdxf',
        '東京都建設局 CAD製図基準 令和6年4月: 共通規定準用。',
        '土木基準の住宅への参考適用。SXF電子納品ではない。',
        '構造・設備・採光換気・消防・法規適合は未検証。',
        '家具・建具・バルコニー手すりは概念形状。',
    ]
    y=248
    for line in lines:
        sheet_text(line,235,y,2.5 if line and not line.isupper() else 2.5)
        y-=6.4
    # A compact title block uses the common black/white A3 drawing language.
    for yy in (32,42):
        c.line(235*mm,yy*mm,402*mm,yy*mm)
        layout.add_line((235,yy),(402,yy),dxfattribs={'color':7,'lineweight':13})
    sheet_text('2LDK 住戸計画',237,35,3.5);sheet_text('1:50 | A01 | 001',355,35,2.5)
    g.doc.saveas(ROOT/'DXF/apartment_2ldk_plan.dxf')
    c.showPage();c.save()
    return preview(pdf_path)


def preview(pdf_path):
    source=pdf_path.read_bytes();doc=fitz.open(stream=source,filetype='pdf');page=doc[0]
    crop_mm=[15,15,210,267];crop=[n*mm for n in crop_mm]
    rect=fitz.Rect(crop[0],crop[1],crop[0]+crop[2],crop[1]+crop[3])
    annotations=[]
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines',[]):
            for span in line['spans']:
                if rect.contains(fitz.Rect(span['bbox'])):
                    annotations.append({'text':span['text'],'bounds':[round(v,6) for v in span['bbox']]})
    svg=page.get_svg_image(text_as_path=True).encode()
    assert b'<text' not in svg and b'<image' not in svg
    svg_path=ROOT/'output/vector/apartment_2ldk_plan.svg';svg_path.write_bytes(svg)
    page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(ROOT/'output/review/apartment_2ldk_plan.png')
    required=[f'{P.width:g}',f'{P.depth:g}',f'{P.balcony_depth:g}','LDK','洋室 1','洋室 2',
              '浴室','洗面','トイレ','納戸','玄関','廊下','バルコニー']+[f'D{i:02d}' for i in range(1,9)]
    for text in required:assert any(text in a['text'] for a in annotations),f'Missing preview label: {text}'
    data={'version':1,'source':{'path':str(pdf_path.relative_to(ROOT)),'sha256':hashlib.sha256(source).hexdigest(),'pages':1},
          'generator':{'script':'src/apartment_2ldk.py','engine':'PyMuPDF','version':fitz.VersionBind,'textAsPath':True},
          'cropPaperMm':crop_mm,'floors':[{'floor':1,'page':1,'path':str(svg_path.relative_to(ROOT)),
          'bytes':len(svg),'sha256':hashlib.sha256(svg).hexdigest(),'fullViewBox':[0,0,round(page.rect.width,6),round(page.rect.height,6)],
          'planViewBox':[round(v,6) for v in crop],'requiredLabels':required,'annotations':annotations}]}
    (ROOT/'output/review/apartment_2ldk_preview.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    return data


def main():
    for folder in ('DXF','STEP','GLB','output/pdf','output/vector','output/review'):
        (ROOT/folder).mkdir(parents=True,exist_ok=True)
    details=model();plan();data=manifest();data['glb_export']=details
    data['drafting_standard']={'name':STANDARD,'url':SOURCE_URL,'scale':'1:50','paper':'A3 landscape',
                              'scope':'Common civil CAD drawing conventions adapted to a residential concept; not SXF delivery.'}
    (ROOT/'output/review/apartment_2ldk_manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    subprocess.run([str(Path(sys.executable).parent/'cadgen'),'step','snapshot',
        str(ROOT/'STEP/apartment_2ldk.step'),str(ROOT/'output/review/apartment_2ldk_iso.png'),
        '--hide','#ceiling','--camera','iso','--width','1600','--height','1200'],
        check=True,cwd=ROOT,env={**os.environ,'CADGEN_DAEMON':'0'})
    print(json.dumps({'model':details,'areas':data['areas'],'outputs':'apartment_2ldk A01'},ensure_ascii=False))


if __name__=='__main__':main()
