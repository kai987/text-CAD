"""Generate the approved R10 editable floor drawings and canonical aliases."""
import json
from pathlib import Path
from shutil import copyfile
from lib.jp_sheet import add_paper_layout, draw_pdf_sheet

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from generate_plans import Drawing, FONT
from lib.house_plan_r01 import floor_plan as original_plan
from lib.house_redesign_plan import P, REVISION, dimensions, floor_plan, manifest

ROOT=Path(__file__).resolve().parents[1]


def stairs(g,n):
    d=dimensions();x,y=d['sx'],d['sy'];sw=P.stair_width;t=P.internal_wall
    run=(P.risers//2-1)*P.tread
    for side in (0,sw+t):
        for i in range(P.risers//2):
            yy=y+i*P.tread;g.line((x+side,yy),(x+side+sw,yy),'STAIR')
    g.rect((x+sw,y,x+sw+t,y+run),'STAIR')
    g.line((x,y+run),(d['xm'],y+run),'STAIR')
    path=[(x+sw/2,y+150),(x+sw/2,y+run+100),
          (x+sw+t+sw/2,y+run+100),(x+sw+t+sw/2,y+150)]
    if n==2:path=path[::-1]
    for a,b in zip(path,path[1:]):g.line(a,b,'STAIR')
    end=path[-1]
    for offset in (-80,80):g.line(end,(end[0]+offset,end[1]+160),'STAIR')
    g.text('階段 UP' if n==1 else '階段 DOWN',(x+950,y+run+730),175)
    g.text('16R x 175 / T260',(x+950,y+run+430),125)
    g.text('W900 / 踊場900',(x+950,y+run+190),125)


def draw(g,f):
    for wall in (list(f.walls.geoms) if hasattr(f.walls,'geoms') else [f.walls]):
        g.poly(wall.exterior.coords,'WALL','#222222')
        for hole in wall.interiors:g.poly(hole.coords,'WALL','#ffffff')
    for axis,at,start,width in f.windows:
        for o in (-40,0,40):
            a,b=((start,at+o),(start+width,at+o)) if axis=='h' else ((at+o,start),(at+o,start+width))
            g.line(a,b,'WINDOW')
    for name,b in f.fixtures:
        g.rect(b,'FURNITURE');g.text(name,((b[0]+b[2])/2,(b[1]+b[3])/2),90)
    for door in f.doors:
        if door.kind=='open':
            # Actual open passage, with no invented door leaf.
            continue
        s,w,a=door.start,door.width,door.at
        if door.kind=='bifold':
            for edge,sign in ((s,1),(s+w,-1)):
                mid=(edge+sign*w/8,a+door.direction*w/4)
                g.line((edge,a),mid,'DOOR')
                g.line(mid,(edge+sign*w/4,a),'DOOR')
            g.text(f'{door.id} / {w:.0f} 折戸',(s+w/2,a-180),125)
        elif door.kind=='slide':
            parked=s+door.direction*w
            if door.axis=='h':
                g.line((s,a+10),(s+w,a+10),'DOOR')
                g.line((parked,a+30),(parked+w,a+30),'DOOR')
                label=(s+w/2,a-175)
            else:
                g.line((a-10,s),(a-10,s+w),'DOOR')
                g.line((a-30,parked),(a-30,parked+w),'DOOR')
                label=(a-450,s+w/2)
                if door.id=='D04':label=(a+450,s+300)
            g.text(f'{door.id} / {w:.0f}',label,125)
        else:
            g.line((s,a),(s,a+door.direction*w),'DOOR')
            g.arc((s,a),w,0 if door.direction>0 else 270,90 if door.direction>0 else 360)
            g.text(f'{door.id} / {w:.0f}',(s+w/2,a-door.direction*175),125)
    for r in f.rooms:
        if r.id=='stairs':continue
        x,y=r.label
        if r.id=='wc_hall':
            g.text(r.name,(x,y+125),175);g.text(f'{r.area:.2f} m2',(x,y-125),125);continue
        if r.id=='closet':
            g.text(r.name,(750,y),175);g.text(f'{r.area:.2f} m2',(1450,y),125);g.text(r.size_note,(2500,y),125);continue
        g.text(r.name,(x,y+180),175)
        g.text(f'{r.area:.2f} m2',(x,y-25),125)
        if r.id not in ('ldk','hall'):
            g.text(r.size_note,(x,y-220),125)
    stairs(g,f.number)
    d=dimensions()
    if f.number==1:
        g.dim((0,0),(P.width,0),(0,-650))
        g.dim((d['bathr']+100,d['ym']),(d['wcl']-100,d['ym']),(0,P.depth+350))
        g.dim((d['wcl'],d['ym']),(d['wcr'],d['ym']),(0,P.depth+350))
    else:
        bx=d['bx'];g.dim((bx,-P.balcony_depth),(bx+P.balcony_width,-P.balcony_depth),(0,-2200))
        g.dim((bx+P.balcony_width,-P.balcony_depth),(bx+P.balcony_width,0),(bx+P.balcony_width+650,0),90)
        g.dim((180,180),(P.access_left-100,180),(0,-1750))
        g.dim((P.access_left,180),(d['ar'],180),(0,-1750))
        g.dim((d['ar']+100,180),(d['xm'],180),(0,-1750))
    g.dim((0,P.depth),(P.width,P.depth),(0,P.depth+1000))
    g.dim((0,0),(0,P.depth),(-650,0),90)
    g.text('北 N (仮定)',(P.width+750,P.depth-500),125)
    g.line((P.width+750,P.depth-1400),(P.width+750,P.depth-700),'NORTH')
    g.line((P.width+750,P.depth-700),(P.width+650,P.depth-900),'NORTH')
    g.line((P.width+750,P.depth-700),(P.width+850,P.depth-900),'NORTH')
    # Explicit entry and balcony usable door widths stay editable native TEXT.
    g.text('南 / 入口方向は仮定',(P.width/2,-2550 if f.number==2 else -1250),125)


def main():
    pdfmetrics.registerFont(TTFont('HouseUnicode',str(FONT)))
    dest=ROOT/'output/pdf/house_floor_plans_R10_JP.pdf';dest.parent.mkdir(parents=True,exist_ok=True)
    c=canvas.Canvas(str(dest),pagesize=(420*mm,297*mm))
    c.setTitle('R12 balcony revision - engineering pending');c.setAuthor('text-to-CAD')
    for n in (1,2):
        f=floor_plan(n);draw_pdf_sheet(c,f)
        g=Drawing(c);g.ox=37*mm;g.oy=76*mm
        g.doc.ezdxf_metadata()['REVISION']=REVISION
        g.doc.ezdxf_metadata()['SCOPE']='住宅参考計画に東京都共通製図規定を準用。R12室内平面確認済み・バルコニー変更・構造計算と法規適合は未検証。'
        draw(g,f)
        add_paper_layout(g.doc,f)
        source=ROOT/f'DXF/house_redesign_R10_{n}f.dxf'
        g.doc.saveas(source)
        copyfile(source,ROOT/f'DXF/house_{n}f_plan.dxf')
        copyfile(source,ROOT/f'DXF/{n:03d}D0PL2-{n}FPLAN.DXF')
        c.showPage()
    c.save()
    data=manifest()
    data['drawing_revision']=REVISION
    old=[original_plan(n) for n in (1,2)]
    data['comparison']={'old_outline_m2_per_floor':7280*7280/1e6,
        'new_outline_m2_per_floor':P.width*P.depth/1e6,
        'old_toilet_m2':next(r.area for r in old[0].rooms if r.id=='wc'),
        'old_f1_hall_m2':next(r.area for r in old[0].rooms if r.id=='hall'),
        'new_f1_hall_m2':sum(r.area for r in floor_plan(1).rooms if r.kind=='hall'),
        'old_f1_ldk_m2':next(r.area for r in old[0].rooms if r.id=='ldk'),
        'new_f1_ldk_m2':next(r.area for r in floor_plan(1).rooms if r.id=='ldk'),
        'caveat':'LDK now includes open circulation and footprint grows; hall reduction is not a pure same-area efficiency score.'}
    (ROOT/'output/review/house_redesign_R10.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'output/review/design_manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(dest)


if __name__=='__main__':main()
