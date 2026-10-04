"""Generate R02 Tokyo common-rule adapted architectural DXFs and A3 PDF.

text-to-cad supplies the runtime, validation and viewer. Its @dxf contract
is for manufacturing profiles, so architectural TEXT and DIMENSION entities
are deliberately authored with ezdxf. All outputs share house_plan.py.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import ezdxf
from ezdxf import disassemble
from ezdxf.enums import TextEntityAlignment
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from lib.house_plan import P, floor_plan, dimensions, design_manifest
from lib.jp_drafting import REVISION, SCALE, STANDARD, SOURCE_URL, LAYERS, PENS_MM, TEXT_MM, canonical_filename
from lib.jp_sheet import add_paper_layout, draw_pdf_sheet

ROOT=Path(__file__).resolve().parents[1]
FONT=Path('/System/Library/Fonts/Supplemental/Arial Unicode.ttf')
COLORS={key:'#000000' for key in LAYERS}


class Drawing:
    """Write each primitive to editable DXF and to the review PDF."""
    def __init__(self, pdf):
        self.pdf=pdf
        self.doc=ezdxf.new('R2018',setup=True)
        self.doc.units=ezdxf.units.MM
        self.doc.header['$MEASUREMENT']=1
        self.doc.header['$LUNITS']=2
        self.doc.header['$LUPREC']=0
        self.doc.header['$LWDISPLAY']=True
        self.doc.header['$DIMASSOC']=2
        self.doc.styles.new('HOUSE_UNICODE',dxfattribs={'font':FONT.name})
        for key,name in LAYERS.items():
            self.doc.layers.new(name,dxfattribs={'color':7,'linetype':'Continuous',
                                                'lineweight':round(PENS_MM[key]*100)})
        metadata=self.doc.ezdxf_metadata()
        metadata['REVISION']=REVISION
        metadata['STANDARD']=STANDARD
        metadata['SCOPE']='住宅参考計画：土木基準の共通規定を準用。SXF電子納品ではない。'
        metadata['SCALE']='1:50'
        metadata['SOURCE_URL']=SOURCE_URL
        self.msp=self.doc.modelspace()
        self.write_dxf=True
        self.scale=mm/SCALE
        self.ox,self.oy=38*mm,55*mm

    def xy(self,p):
        return self.ox+p[0]*self.scale,self.oy+p[1]*self.scale

    def line(self,a,b,layer='FURNITURE'):
        if self.write_dxf:self.msp.add_line(a,b,dxfattribs={'layer':LAYERS[layer]})
        self.pdf.setStrokeColor(HexColor(COLORS[layer])); self.pdf.setLineWidth(PENS_MM[layer]*mm)
        self.pdf.line(*self.xy(a),*self.xy(b))

    def poly(self,points,layer='FURNITURE',fill=None,dxf=True):
        pts=list(points)
        if pts[-1]==pts[0]: pts=pts[:-1]
        if dxf:
            if layer=='WALL':
                # Explicit boundary lines keep architectural wall junctions
                # easy to inspect and edit; the PDF fills the same geometry.
                for a,b in zip(pts,pts[1:]+pts[:1]):
                    self.msp.add_line(a,b,dxfattribs={'layer':LAYERS['WALL']})
            else:
                self.msp.add_lwpolyline(pts,close=True,dxfattribs={'layer':LAYERS[layer]})
        path=self.pdf.beginPath();path.moveTo(*self.xy(pts[0]))
        for pt in pts[1:]:path.lineTo(*self.xy(pt))
        path.close()
        self.pdf.setStrokeColor(HexColor(COLORS[layer]));self.pdf.setLineWidth(PENS_MM[layer]*mm)
        if fill:self.pdf.setFillColor(HexColor(fill))
        self.pdf.drawPath(path,stroke=1 if dxf else 0,fill=bool(fill))

    def rect(self,bounds,layer='FURNITURE',fill=None):
        x1,y1,x2,y2=bounds
        self.poly([(x1,y1),(x2,y1),(x2,y2),(x1,y2)],layer,fill)

    def text(self,value,at,height=125,layer='TEXT',align='center'):
        if self.write_dxf:
            entity=self.msp.add_text(value,dxfattribs={'height':height,'style':'HOUSE_UNICODE','layer':LAYERS['TEXT']})
            entity.set_placement(at,align=TextEntityAlignment.MIDDLE_CENTER if align=='center' else TextEntityAlignment.MIDDLE_LEFT)
        # Text stays near-black on the light PDF, including furniture and doors.
        self.pdf.setFillColor(HexColor(COLORS['TEXT']));self.pdf.setFont('HouseUnicode',height*self.scale)
        x,y=self.xy(at)
        (self.pdf.drawCentredString if align=='center' else self.pdf.drawString)(x,y-height*self.scale*.32,value)

    def arc(self,center,radius,start,end):
        self.msp.add_arc(center,radius,start,end,dxfattribs={'layer':LAYERS['DOOR']})
        pts=[(center[0]+radius*math.cos(math.radians(start+(end-start)*i/24)),
              center[1]+radius*math.sin(math.radians(start+(end-start)*i/24))) for i in range(25)]
        path=self.pdf.beginPath();path.moveTo(*self.xy(pts[0]))
        for pt in pts[1:]:path.lineTo(*self.xy(pt))
        self.pdf.setStrokeColor(HexColor(COLORS['DOOR']));self.pdf.setLineWidth(PENS_MM['DOOR']*mm)
        self.pdf.drawPath(path)

    def dim(self,p1,p2,base,angle=0):
        dim=self.msp.add_linear_dim(base=base,p1=p1,p2=p2,angle=angle,
            dimstyle='EZDXF',override={'dimtxt':TEXT_MM['value']*SCALE,'dimasz':100,'dimgap':75,
              'dimexo':75,'dimexe':75,'dimclrd':7,'dimclre':7,'dimclrt':7,
              'dimlwd':13,'dimlwe':13,'dimblk':ezdxf.ARROWS.closed_filled,
              'dimtxsty':'HOUSE_UNICODE','dimdec':0,'dimtad':1,'dimlfac':1,'dimlunit':2},
            dxfattribs={'layer':LAYERS['DIM']})
        dim.render()
        for entity in self.doc.blocks.get(dim.dimension.dxf.geometry):
            entity.dxf.layer=LAYERS['DIM']
        # Draw the actual DIMENSION graphics in the PDF, including its arrows
        # and text placement, so the two deliverables use the same geometry.
        self.pdf.setStrokeColor(HexColor('#000000'))
        self.pdf.setFillColor(HexColor('#000000'))
        self.pdf.setLineWidth(PENS_MM['DIM']*mm)
        for entity in disassemble.recursive_decompose(dim.dimension.virtual_entities()):
            kind=entity.dxftype()
            if kind=='LINE':self.pdf.line(*self.xy(entity.dxf.start),*self.xy(entity.dxf.end))
            elif kind in ('SOLID','LWPOLYLINE'):
                points=list(entity.wcs_vertices()) if kind=='SOLID' else list(entity.get_points('xy'))
                path=self.pdf.beginPath();path.moveTo(*self.xy(points[0]))
                for point in points[1:]:path.lineTo(*self.xy(point))
                if kind=='SOLID' or entity.closed:path.close()
                self.pdf.drawPath(path,fill=kind=='SOLID',stroke=kind!='SOLID')
            elif kind=='MTEXT':
                self.pdf.saveState();self.pdf.translate(*self.xy(entity.dxf.insert))
                self.pdf.rotate(entity.get_rotation())
                height=entity.dxf.char_height*self.scale
                self.pdf.setFont('HouseUnicode',height)
                self.pdf.drawCentredString(0,-height*.32,entity.plain_text())
                self.pdf.restoreState()


def draw_door(g,door):
    s,w,a=door.start,door.width,door.at
    if door.kind=='slide':
        if door.axis=='h':
            y=a+10
            g.line((s,y),(s+w,y),'DOOR')
            target=s-w if door.direction<0 else s+w
            g.line((target,y+20),(target+w,y+20),'DOOR')
            # The F2 WC tag belongs in the hall, clear of the WC fixture.
            offset=175 if door.a=='hall' and door.b=='wc' else -175
            g.text(f'{door.id} / {w:.0f}',(s+w/2,a+offset),125)
        else:
            x=a-10
            g.line((x,s),(x,s+w),'DOOR')
            target=s-w if door.direction<0 else s+w
            g.line((x-20,target),(x-20,target+w),'DOOR')
            g.text(f'{door.id} / {w:.0f}',(a-450,s+w/2),125)
    else:
        assert door.axis=='h'
        hinge=(s,a)
        g.line(hinge,(s,a+door.direction*w),'DOOR')
        g.arc(hinge,w,0 if door.direction>0 else 270,90 if door.direction>0 else 360)
        g.text(f'{door.id} / {w:.0f}',(s+w/2,a-door.direction*175),125)


def draw_stairs(g,f):
    d=dimensions();x,y=d['sx'],d['sy'];sw=P.stair_width;t=P.internal_wall
    run=(P.risers//2-1)*P.tread
    for side in (0,sw+t):
        for i in range(P.risers//2):
            yy=y+i*P.tread
            g.line((x+side,yy),(x+side+sw,yy),'STAIR')
    g.rect((x+sw,y,x+sw+t,y+run),'STAIR')
    g.line((x,y+run),(d['xmax'],y+run),'STAIR')
    path=[(x+450,y+150),(x+450,y+run+40),(x+1450,y+run+40),(x+1450,y+150)]
    if f.number==2:path=path[::-1]
    for a,b in zip(path,path[1:]):g.line(a,b,'STAIR')
    end,prev=path[-1],path[-2]
    sign=1 if end[1]>prev[1] else -1
    g.line(end,(end[0]-80,end[1]-sign*150),'STAIR')
    g.line(end,(end[0]+80,end[1]-sign*150),'STAIR')
    # Place labels on landing and outside flight arrows.
    g.text('階段  UP' if f.number==1 else '階段  DOWN',(x+950,y+run+760),175)
    g.text('16R × 175 / T260',(x+950,y+run+160),125)
    g.text('W900 / 踊場900',(x+950,y+run+540),125)


def draw_floor(g,f):
    d=dimensions()
    for wall in (list(f.walls.geoms) if hasattr(f.walls,'geoms') else [f.walls]):
        g.poly(wall.exterior.coords,'WALL',COLORS['WALL'])
        for hole in wall.interiors:g.poly(hole.coords,'WALL','#ffffff')
    for axis,at,start,width in f.windows:
        for offset in (-40,0,40):
            if axis=='h':g.line((start,at+offset),(start+width,at+offset),'WINDOW')
            else:g.line((at+offset,start),(at+offset,start+width),'WINDOW')
    for name,bounds in f.fixtures:
        g.rect(bounds,'FURNITURE')
        g.text(name,((bounds[0]+bounds[2])/2,(bounds[1]+bounds[3])/2),90)
    for door in f.doors:draw_door(g,door)
    for room in f.rooms:
        if room.id=='stairs':continue
        x,y=room.label
        # Keep the room label below the sanitary-fixture outline.
        if room.id=='wc':y-=400
        g.text(room.name,(x,y+175),175)
        area_x=x+150 if room.id=='storage' else x
        g.text(f'{room.area:.2f} m2',(area_x,y-40),125)
        if room.id not in ('hall','bed2'):
            # Allow clearance for both the CAD viewer and the PDF font metrics.
            size_offset=-180 if room.id=='wash' else -285 if room.id=='storage' else -235
            g.text(room.size_note,(x,y+size_offset),125)
    draw_stairs(g,f)
    if f.number==1:
        g.line((d['sx'],d['wc_bottom']-P.internal_wall),(d['sx']+900,d['wc_bottom']-P.internal_wall),'FURNITURE')
        g.text('上がり框',(d['sx']+450,d['wc_bottom']-P.internal_wall+125),90)
    # Overall dimensions and useful net-width dimensions.
    g.dim((0,P.depth),(P.width,P.depth),(0,P.depth+1180))
    g.dim((0,0),(0,P.depth),(-650,0),90)
    if f.number==1:
        intervals=[(180,d['bath_right']),(d['wash_left'],d['wash_right']),
                   (d['wash_right']+100,d['ldk_right']),(d['sx'],d['xmax'])]
    else:
        intervals=[(180,d['master_right']),(d['master_right']+100,d['ldk_right']),
                   (d['sx'],d['xmax'])]
    for lo,hi in intervals:g.dim((lo,d['ymax']),(hi,d['ymax']),(0,P.depth+380))
    g.text('寸法単位 mm / 外形・階高は仮定',(P.width/2,P.depth+750),125)
    g.line((P.width+650,P.depth-450),(P.width+650,P.depth+100),'NORTH')
    g.line((P.width+650,P.depth+100),(P.width+580,P.depth-50),'NORTH')
    g.line((P.width+650,P.depth+100),(P.width+720,P.depth-50),'NORTH')
    g.text('N*',(P.width+650,P.depth+310),125)
    g.text('* 方位は仮定',(P.width+650,P.depth-650),90)
    # Readable review title also retained in modelspace.
    g.text(f'{REVISION} / {f.number}階 平面図（参考計画）',(P.width/2,-1200),250)
    # Modelspace dimensions remain 1:1. Paper layouts are not inferred from text.


def generate():
    for folder in ('DXF','output/pdf','output/review','checks'):(ROOT/folder).mkdir(parents=True,exist_ok=True)
    pdfmetrics.registerFont(TTFont('HouseUnicode',str(FONT)))
    pdf_path=ROOT/'output/pdf/house_floor_plans_R02_JP.pdf'
    c=canvas.Canvas(str(pdf_path),pagesize=(420*mm,297*mm),invariant=1)
    c.setTitle('日本一戸建て - R02 東京都共通製図規定準用')
    c.setAuthor('Parametric concept model / text-to-cad')
    for number in (1,2):
        f=floor_plan(number)
        c.setFillColor(HexColor('#ffffff'));c.rect(0,0,420*mm,297*mm,stroke=0,fill=1)
        draw_pdf_sheet(c,f)
        g=Drawing(c);draw_floor(g,f)
        add_paper_layout(g.doc,f)
        path=ROOT/'DXF'/canonical_filename(number)
        g.doc.saveas(path)
        (ROOT/f'DXF/house_{number}f_plan.dxf').write_bytes(path.read_bytes())
        c.showPage()
    c.save()
    manifest=design_manifest()
    manifest['drawing_revision']=REVISION
    manifest['drafting_standard']={'name':STANDARD,'url':SOURCE_URL,'edition':'令和6年4月',
        'scope':'住宅に土木CAD基準の共通規定を準用。DXF/PDFでありSXF電子納品ではない。',
        'paper':'A3 420 × 297 mm, landscape, unbound','scale':'1:50',
        'model_units':'mm, 1:1','editable_paper_layout':'JP_A3_1_50',
        'canonical_files':[canonical_filename(n) for n in (1,2)]}
    (ROOT/'output/review/design_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Created {pdf_path}')
    print('Created canonical R02 DXFs and updated house_1f_plan.dxf / house_2f_plan.dxf aliases')


if __name__=='__main__':generate()
