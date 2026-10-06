"""R10 editable A3 structural demonstration supplement (two sheets).

Approved architectural floor plans stay unchanged. Every section is a drawing
input; this supplement contains no strength result or construction detail.
"""
from __future__ import annotations

from pathlib import Path

import ezdxf
from ezdxf import disassemble
from ezdxf.lldxf import const
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from generate_plans import Drawing, FONT
from lib.house_plan import P, floor_plan
from lib.house_geometry import G
from lib.attic_geometry import A, attic_dimensions, roof_underside_z
from lib.structure_geometry import T, structure_manifest, structure_dimensions
from lib.jp_drafting import LAYERS
from shapely.geometry import box

ROOT=Path(__file__).resolve().parents[1]


class StructureDrawing(Drawing):
    def dim(self,p1,p2,base,angle=0):
        # Dimension lettering remains 2.5 mm on paper on BOTH 1:50 and 1:75
        # sheets. The inherited architectural drawing method fixes 1:50.
        ratio=mm/self.scale
        dimension=self.msp.add_linear_dim(base=base,p1=p1,p2=p2,angle=angle,dimstyle='EZDXF',override={
            'dimtxt':2.5*ratio,'dimasz':2*ratio,'dimgap':1.5*ratio,'dimexo':1.5*ratio,'dimexe':1.5*ratio,
            'dimclrd':7,'dimclre':7,'dimclrt':7,'dimlwd':13,'dimlwe':13,'dimblk':ezdxf.ARROWS.closed_filled,
            'dimtxsty':'HOUSE_UNICODE','dimdec':0,'dimtad':1,'dimlfac':1,'dimlunit':2},dxfattribs={'layer':LAYERS['DIM']})
        dimension.render()
        for e in self.doc.blocks.get(dimension.dimension.dxf.geometry):
            e.dxf.layer=LAYERS['DIM']
            if e.dxftype()=='MTEXT':e.set_bg_color('canvas',scale=1.2)
        self.pdf.setStrokeColorRGB(0,0,0);self.pdf.setFillColorRGB(0,0,0);self.pdf.setLineWidth(.13*mm)
        for e in disassemble.recursive_decompose(dimension.dimension.virtual_entities()):
            kind=e.dxftype()
            if kind=='LINE':self.pdf.line(*self.xy(e.dxf.start),*self.xy(e.dxf.end))
            elif kind in ('SOLID','LWPOLYLINE'):
                points=list(e.wcs_vertices()) if kind=='SOLID' else list(e.get_points('xy'))
                path=self.pdf.beginPath();path.moveTo(*self.xy(points[0]))
                for point in points[1:]:path.lineTo(*self.xy(point))
                if kind=='SOLID' or e.closed:path.close()
                self.pdf.drawPath(path,fill=kind=='SOLID',stroke=kind!='SOLID')
            elif kind=='MTEXT':
                self.pdf.saveState();self.pdf.translate(*self.xy(e.dxf.insert));self.pdf.rotate(e.get_rotation())
                height=e.dxf.char_height*self.scale;self.pdf.setFont('HouseUnicode',height)
                width=pdfmetrics.stringWidth(e.plain_text(),'HouseUnicode',height)
                self.pdf.setFillColorRGB(1,1,1)
                self.pdf.rect(-width/2-height*.15,-height*.65,width+height*.3,height*1.3,fill=1,stroke=0)
                self.pdf.setFillColorRGB(0,0,0)
                self.pdf.drawCentredString(0,-height*.32,e.plain_text());self.pdf.restoreState()


def generate():
    path=ROOT/'output/pdf/house_structural_scheme_R06_JP.pdf'
    path.parent.mkdir(parents=True,exist_ok=True)
    pdfmetrics.registerFont(TTFont('HouseUnicode',str(FONT)))
    pdf=canvas.Canvas(str(path),pagesize=(420*mm,297*mm),invariant=1)
    pdf.setTitle('木造軸組・基礎・小屋裏 候補構造図 R10 / Demonstration only')
    pdf.setAuthor('text-CAD')
    d=StructureDrawing(pdf)
    d.doc.ezdxf_metadata()['REVISION']='R10-STRUCTURE'
    d.doc.ezdxf_metadata()['SCOPE']='構造候補の説明図。断面はデモ入力。構造計算・施工図・法規判定ではない。'
    d.doc.ezdxf_metadata()['SCALE']='Sheet 01 1:50; Sheet 02 1:75; labelled foundation section 1:25'
    d.doc.header['$PSLTSCALE']=0
    d.doc.linetypes.new('STRUCTURE_AXIS',dxfattribs={'description':'3/1/0.5/1 mm at 1:50','pattern':[275,150,-50,25,-50]})
    d.doc.layers.new('D-TTL-FRAM',dxfattribs={'color':7,'lineweight':70})
    d.doc.layers.new('D-TTL-VPRT',dxfattribs={'color':7,'plot':0})
    manifest=structure_manifest(P,G)
    sd=structure_dimensions(P,G)

    def frame(layout_name,scale,origin_mm,offset_y=0):
        pdf.setLineWidth(.7*mm);pdf.rect(7.5*mm,7.5*mm,405*mm,282*mm)
        layout=d.doc.layouts.new(layout_name)
        layout.page_setup(size=(420,297),margins=(0,0,0,0),units='mm')
        layout.add_lwpolyline([(7.5,7.5),(412.5,7.5),(412.5,289.5),(7.5,289.5)],close=True,dxfattribs={'layer':'D-TTL-FRAM'})
        layout.add_viewport(center=(210,148.5),size=(400,278),
            view_center_point=((210-origin_mm[0])*scale,(148.5-origin_mm[1])*scale+offset_y),view_height=278*scale,
            dxfattribs={'layer':'D-TTL-VPRT','flags':const.VSF_LOCK_ZOOM})

    def shifted(bounds,x=0,y=0):return (bounds[0]+x,bounds[1]+y,bounds[2]+x,bounds[3]+y)

    def axis_bounds(segment):
        a,b,at,w=segment['start'],segment['end'],segment['at'],segment['width']/2
        return (a,at-w,b,at+w) if segment['axis']=='h' else (at-w,a,at+w,b)

    placed_markers=[]
    def marker(value,at,height=100):
        # Opaque canvas MTEXT mask in editable CAD; white patch in print. The
        # label remains readable when a candidate axis passes beneath it.
        width=pdfmetrics.stringWidth(value,'HouseUnicode',height*d.scale)/d.scale
        # A small deterministic placement pass also resolves corner tag pairs
        # and closely spaced pillar IDs; masks alone cannot fix text on text.
        for dx,dy in ((0,0),(0,220),(0,-220),(280,0),(-280,0),(280,220),(-280,-220),(0,440),(0,-440)):
            candidate=(at[0]+dx,at[1]+dy)
            marker_bounds=(candidate[0]-width/2-25,candidate[1]-height*.7,
                           candidate[0]+width/2+25,candidate[1]+height*.7)
            if not any(marker_bounds[0]<old[2] and old[0]<marker_bounds[2] and
                       marker_bounds[1]<old[3] and old[1]<marker_bounds[3] for old in placed_markers):
                at=candidate;placed_markers.append(marker_bounds);break
        else:raise ValueError(f'Cannot place structural label {value}; adjust diagram layout')
        x,y=d.xy(at);padding=height*d.scale*.15
        pdf.setFillColorRGB(1,1,1)
        pdf.rect(x-width*d.scale/2-padding,y-height*d.scale*.55-padding,
                 width*d.scale+2*padding,height*d.scale*1.1+2*padding,fill=1,stroke=0)
        d.write_dxf=False;d.text(value,at,height);d.write_dxf=True
        m=d.msp.add_mtext(value,dxfattribs={'insert':at,'char_height':height,'width':width+height*.3,
            'style':'HOUSE_UNICODE','attachment_point':5,'layer':LAYERS['TEXT']})
        m.set_bg_color('canvas',scale=1.2)

    # Sheet 01: frame plans keep the architectural wall outlines as context.
    for floor,xoff in ((1,0),(2,9000)):
        f=floor_plan(floor)
        d.text(f'0{floor} {floor}階 柱・梁・耐力壁候補 / 1:50',(xoff+3640,9400),175)
        walls=list(f.walls.geoms) if hasattr(f.walls,'geoms') else [f.walls]
        for wall in walls:
            d.poly([(x+xoff,y) for x,y in wall.exterior.coords],'FURNITURE')
        for b in manifest['floor_beam_axes'][f'F{floor}']:
            footprint=box(*axis_bounds(b))
            if floor==2:footprint=footprint.difference(box(A.hatch_x,A.hatch_y,A.hatch_x+A.hatch_length,A.hatch_y+A.hatch_width))
            for piece in ([footprint] if footprint.geom_type=='Polygon' else footprint.geoms):
                if not piece.is_empty:d.poly([(x+xoff,y) for x,y in piece.exterior.coords],'DOOR')
            along=(b['start']+b['end'])/2
            at=(along,b['at']) if b['axis']=='h' else (b['at'],along)
            if b['id'] in ('B01','B02','B05','B06','B07','B12','B13','B14'):
                label_x,label_y=at[0],at[1]+250
                if b['id']=='B01':label_x=4000;label_y=500
                if b['id']=='B02':label_x=4000;label_y=P.depth-300
                if b['id']=='B06':label_x=4200;label_y=at[1]+340
                if b['id']=='B07':label_x-=330
                marker(b['id'],(xoff+label_x,label_y))
        for wall in manifest['bearing_wall_candidates']:
            a,b,v,t=wall['start'],wall['end'],wall['normal_start'],wall['thickness']
            bounds=(a,v,b,v+t) if wall['axis']=='h' else (v,a,v+t,b)
            d.rect(shifted(bounds,xoff),'WALL')
            normal_offset=-300 if wall['external'] and wall['axis']=='h' and wall['at']>P.depth/2 else 300
            at=((a+b)/2,wall['at']+normal_offset) if wall['axis']=='h' else (wall['at']+300,(a+b)/2)
            marker(wall['id'],(xoff+at[0],at[1]))
        for c in manifest['columns']:
            if floor not in c['floors']:continue
            h=c['width']/2;x,y=c['x'],c['y']
            d.rect((xoff+x-h,y-h,xoff+x+h,y+h),'WALL')
            label_y=y+200 if int(c['id'][1:])%2 else y-200
            if y<200:label_y=-220
            if y>P.depth-200:label_y=P.depth+230
            label_x=x+230 if x<200 else x-230 if x>P.width-200 else x
            if c['width']==T.internal_column_width and abs(x-5150)<.1:label_x-=250
            if c['width']==T.internal_column_width and abs(x-6150)<.1:label_x-=250
            marker(c['id'],(xoff+label_x,label_y))
        d.dim((xoff,P.depth),(xoff+P.width,P.depth),(0,8250))
        d.dim((xoff,0),(xoff,P.depth),(xoff-700,0),90)
        d.text(f'柱: 外周120角 / 内部90角 / 梁: 120・90・180 × H300',(xoff+3640,-650),100)
        d.text('断面寸法はデモ入力。材種・等級・壁倍率・接合耐力は未設定。',(xoff+3640,-950),100)
    d.text('木造軸組 候補構造図 / R10',(0,10800),250,align='left')
    d.text('単位 mm / A3 / 確認済み平面を保持 / 演示方案・構造計算未実施 / 2026-10-07',(0,10300),125,align='left')
    for i,text in enumerate([
        'C：柱 / B：梁 / BW：耐力壁候補（倍率未設定）。必要壁量・偏心・耐震等級を示さない。',
        'B05：LDK上部の長スパン梁候補。2階壁荷重・たわみ・接合部を含め再設計が必要。',
        '柱位置は両階の閉じた壁内。検修口下はB12〜B14で幾何調整。部材・接合耐力は未計算。',
    ]):d.text(text,(0,-1400-i*240),105,align='left')
    frame('STRUCTURE_01_A3_1_50',50,(38,55))
    pdf.showPage()

    # Sheet 02 uses a separate model-space region for clean editable viewports.
    offset=18000;d.scale=mm/75;d.ox=38*mm;d.oy=130*mm-offset*d.scale
    def text(value,at,height=187.5,align='center'):d.text(value,(at[0],at[1]+offset),height,align=align)
    def line(a,b,layer='FURNITURE'):d.line((a[0],a[1]+offset),(b[0],b[1]+offset),layer)
    def rect(bounds,layer='FURNITURE'):d.rect(shifted(bounds,0,offset),layer)
    def dim(a,b,base,angle=0):d.dim((a[0],a[1]+offset),(b[0],b[1]+offset),(base[0],base[1]+offset),angle)
    text('基礎支持線・小屋裏床組 候補図 / R10',(0,10800),375,align='left')
    text('単位 mm / A3 / 平面・断面1:75 / 基礎参考断面のみ1:25 / 全寸法はデモ入力',(0,10000),187.5,align='left')
    text('01 基礎支持線候補 / 1:75',(3640,8500),262.5)
    text('02 小屋裏床組・検修口 / 1:75',(14140,8500),262.5)
    rect((0,0,P.width,P.depth),'WALL')
    # Actual root foundation width is a recorded drawing input, never rebar.
    from lib.exterior_geometry import E
    for s in manifest['foundation_support_axes']:
        profile=dict(s,width=E.foundation_wall_thickness)
        rect(axis_bounds(profile),'DOOR')
        along=(s['start']+s['end'])/2
        at=(along,s['at']) if s['axis']=='h' else (s['at'],along)
        text(s['id'],(at[0]+250,at[1]+300),150)
    for c in manifest['columns']:
        h=c['width']/2;rect((c['x']-h,c['y']-h,c['x']+h,c['y']+h),'WALL')
    dim((0,P.depth),(P.width,P.depth),(0,7800))
    text('I01～I07：内側支持肋 / 幅140 / 上端Z=-200（仮定）',(3640,-500),180)
    text('地盤・反力・配筋・沈下を計算して断面を決める。',(3640,-850),165)
    sx=10500;ad=attic_dimensions(P,G)
    rect((sx+sd['deck_left'],A.deck_end_inset,sx+sd['deck_right'],P.depth-A.deck_end_inset),'WALL')
    # Read the real candidate native members to show all splits and trimmers.
    from lib.structure_geometry import _attic_members
    joists,headers=_attic_members(P,G,sd,[])
    for shape in joists+headers:
        b=shape.bounding_box()
        rect((sx+b.min.X,b.min.Y,sx+b.max.X,b.max.Y),'DOOR')
    hx1,hy1,hx2,hy2=sd['hatch']
    rect((sx+hx1,hy1,sx+hx2,hy2),'WALL')
    text('検修口',(sx+(hx1+hx2)/2,(hy1+hy2)/2),180)
    dim((sx+hx1,hy2),(sx+hx2,hy2),(0,hy2+450))
    dim((sx+hx2,hy1),(sx+hx2,hy2),(sx+hx2+650,0),90)
    dim((sx+sd['deck_left'],P.depth-A.deck_end_inset),(sx+sd['deck_right'],P.depth-A.deck_end_inset),(0,7800))
    text('根太60×H180・間隔≤455 / 開口両側120幅',(sx+3640,-500),180)
    text('開口補強梁60×H180 / 全て断面未計算',(sx+3640,-850),165)

    # True-height roof/attic cross-section, local datum Z5396, at 1:75.
    sy=-5300;zref=sd['F2_beam_top_z']
    text('03 東西参考断面 / 1:75（Zは実座標）',(0,sy+3300),262.5,align='left')
    for a,b in (((0,roof_underside_z(0,P,G)),(P.width/2,roof_underside_z(P.width/2,P,G))),
                ((P.width/2,roof_underside_z(P.width/2,P,G)),(P.width,roof_underside_z(P.width,P,G)))):
        line((a[0],sy+a[1]-zref),(b[0],sy+b[1]-zref),'WALL')
        line((a[0],sy+a[1]-zref+150),(b[0],sy+b[1]-zref+150),'DOOR')
    deckz=ad['deck_top_z']
    capz=deckz+A.maximum_finished_clear_height
    xcap=(capz+A.lining_vertical_allowance-2*P.storey_height)/__import__('math').tan(__import__('math').radians(G.roof_pitch_degrees))
    line((sd['deck_left'],sy+deckz-zref),(sd['deck_right'],sy+deckz-zref),'WALL')
    line((sd['deck_left'],sy+roof_underside_z(sd['deck_left'],P,G)-50-zref),(xcap,sy+capz-zref),'DOOR')
    line((xcap,sy+capz-zref),(P.width-xcap,sy+capz-zref),'DOOR')
    line((P.width-xcap,sy+capz-zref),(sd['deck_right'],sy+roof_underside_z(sd['deck_right'],P,G)-50-zref),'DOOR')
    rect((sd['deck_left'],sy,sd['deck_right'],sy+T.attic_joist_depth),'DOOR')
    text('収納 CH最大1350（仮定）',(3640,sy+800),165)
    text('板18＋下地24 / 根太180 / 梁300（候補）',(3640,sy-300),165)
    text('屋根材内部の表示用材寸法は未計算。屋根構成・梁せいを再設計。',(0,sy-700),165,align='left')

    # Enlarged conceptual foundation section: 1:25 on the 1:75 sheet.
    fx,fy=12000,-3300;enlarge=3
    text('04 基礎参考断面 / 1:25',(fx,fy+1300),262.5,align='left')
    def section(bounds):
        x1,z1,x2,z2=bounds
        rect((fx+x1*enlarge,fy+z1*enlarge,fx+x2*enlarge,fy+z2*enlarge),'DOOR')
    section((0,-800,850,-650));section((0,-650,140,-200))
    section((30,-200,150,-80));section((45,-80,135,200))
    for z,label in ((-200,'基礎上端 -200'),(-80,'土台上端 -80'),(-650,'底板上端 -650'),(-800,'底板下面 -800')):
        at=fy+z*enlarge
        line((fx+2800,at),(fx+3500,at),'DIM');text(label,(fx+3650,at),165,align='left')
    text('底板150・立上り140・土台120：デモ入力',(fx,fy-2950),165,align='left')
    text('支持肋は外周と交差部を整理。接触は耐力の証明ではない。',(fx,fy-3350),165,align='left')

    for i,note in enumerate([
        '所在地・地盤・材料等級・積載荷重は未指定。engineering_inputs_R06.jsonの未設定項目を要入力。',
        '耐力壁量・偏心・梁の曲げ／せん断／たわみ・接合部・基礎支持力・配筋・沈下は未計算。',
        '収納の不算入・用途・天井処理は所在地で要確認。図面は構造計算書・確認申請・施工図ではない。',
    ]):text(note,(0,-7700-i*350),172.5,align='left')
    frame('STRUCTURE_02_A3_1_75',75,(38,130),offset)
    d.doc.layouts.set_active_layout('STRUCTURE_01_A3_1_50')
    d.doc.header['$TILEMODE']=0
    d.doc.saveas(ROOT/'DXF/house_structural_scheme.dxf')
    pdf.showPage();pdf.save()
    print(f'Saved {path} and DXF/house_structural_scheme.dxf')


if __name__=='__main__':generate()
