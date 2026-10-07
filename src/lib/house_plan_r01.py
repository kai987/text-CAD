"""Shared, millimetre-based parameters for the R01 house proposal.

Coordinates: X east, Y north. North and the south entrance are demo assumptions.
This is a layout proposal, not a structural or statutory design.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from shapely.geometry import box, Polygon
from shapely.ops import unary_union


@dataclass(frozen=True)
class Parameters:
    width: float = 7280
    depth: float = 7280
    storey_height: float = 2800
    external_wall: float = 180
    internal_wall: float = 100
    stair_width: float = 900
    stair_landing: float = 900
    risers: int = 16
    tread: float = 260
    bath_width: float = 1820
    wash_width: float = 1820
    master_width: float = 3370
    toilet_depth: float = 1700
    roof_type: str = "gable / 切妻屋根 - stage 2"


P = Parameters()


@dataclass
class Room:
    id: str
    name: str
    shape: Polygon
    label: tuple[float, float]
    kind: str = "living"
    size_note: str = ""

    @property
    def area(self):
        return self.shape.area / 1e6


@dataclass
class Door:
    id: str
    a: str
    b: str
    axis: str
    at: float
    start: float
    width: float
    kind: str = "slide"
    direction: int = 1
    hinge_at_end: bool = False

    def opening(self, thickness):
        half = thickness / 2 + 1
        if self.axis == "h":
            return box(self.start, self.at-half, self.start+self.width, self.at+half)
        return box(self.at-half, self.start, self.at+half, self.start+self.width)


@dataclass
class Floor:
    number: int
    rooms: list[Room]
    doors: list[Door]
    walls: object
    windows: list[tuple[str, float, float, float]]
    fixtures: list[tuple[str, tuple[float,float,float,float]]]


def rectangle(id, name, x1, y1, x2, y2, label=None, kind="living"):
    return Room(id, name, box(x1,y1,x2,y2), label or ((x1+x2)/2,(y1+y2)/2),
                kind, f"{x2-x1:.0f} × {y2-y1:.0f}")


def dimensions(p=P):
    e, t = p.external_wall, p.internal_wall
    xmax, ymax = p.width-e, p.depth-e
    stair_w = 2*p.stair_width+t
    stair_d = (p.risers//2-1)*p.tread+p.stair_landing
    sx, sy = xmax-stair_w, ymax-stair_d
    return dict(e=e,t=t,xmax=xmax,ymax=ymax,sx=sx,sy=sy,
                ldk_right=sx-t, south_top=sy-1100,
                master_right=e+p.master_width,
                bath_right=e+p.bath_width,
                wash_left=e+p.bath_width+t,
                wash_right=e+p.bath_width+t+p.wash_width,
                wc_left=sx+p.stair_width+t,
                wc_bottom=sy-1100-p.toilet_depth)


def floor_plan(number, p=P):
    d = dimensions(p)
    e,t,xm,ym,sx,sy = (d[k] for k in ("e","t","xmax","ymax","sx","sy"))
    lr,st,mr,br,wl,wr,wcl,wcb = (d[k] for k in
        ("ldk_right","south_top","master_right","bath_right","wash_left","wash_right","wc_left","wc_bottom"))
    foyer_top=wcb-t
    core_left=sx+p.stair_width
    stairs=rectangle("stairs","階段",sx,sy,xm,ym,(sx+950,sy+1450),"stair")
    wc=rectangle("wc","トイレ",wcl,wcb,xm,st,(wcl+450,wcb+850),"wet")
    outer=box(0,0,p.width,p.depth).difference(box(e,e,xm,ym))
    # Shared toilet footprint and stair opening; partition doors differ by floor.
    walls=[outer,box(core_left,foyer_top,wcl,st+t),box(core_left,foyer_top,xm,wcb),
           box(wcl,st,xm,st+t)]
    if number == 1:
        rooms=[rectangle("ldk","LDK",e,e,lr,sy-t,(3200,2000)),
               rectangle("bath","浴室",e,sy,br,ym,kind="wet"),
               rectangle("wash","洗面・脱衣",wl,sy,wr,ym,(3010,6100),"wet"),
               rectangle("pantry","食品庫",wr+t,sy,lr,ym,(4560,sy+650),"storage"),
               rectangle("foyer","玄関",sx,e,xm,foyer_top,(sx+800,800)),wc,
               Room("hall","廊下",Polygon([(sx,foyer_top),(core_left,foyer_top),
                    (core_left,st+t),(xm,st+t),(xm,sy),(sx,sy)]),(sx+950,st+600),"hall","有効幅 900"),stairs]
        walls += [box(lr,e,sx,ym),box(e,sy-t,sx,sy),
                  box(br,sy,wl,ym),box(wr,sy,wr+t,ym)]
        doors=[Door("D01","outside","foyer","h",e/2,sx+180,900,"swing",-1),
               Door("D02","hall","ldk","v",lr+t/2,1880,900,"slide",1),
               Door("D03","ldk","wash","h",sy-t/2,2500,800,"slide",-1),
               Door("D04","wash","bath","v",br+t/2,4700,750,"slide",1),
               Door("D05","ldk","pantry","h",sy-t/2,4160,800,"slide",-1),
               Door("D06","hall","wc","v",core_left+t/2,2200,700,"slide",-1)]
        windows=[("h",e/2,900,2100),("v",e/2,1500,1800),
                 ("h",ym+e/2,700,600),("h",ym+e/2,2650,600),
                 ("h",ym+e/2,4210,600),("v",xm+e/2,wcb+550,450),
                 ("v",xm+e/2,6200,600)]
        fixtures=[("靴収納",(xm-400,300,xm,1200)),("キッチン",(300,3600,2200,4180)),
                  ("浴槽",(330,ym-850,1830,ym-150)),
                  ("洗面",(wl+150,ym-650,wr-150,ym-100)),
                  ("洗濯",(wl+150,sy+850,wl+750,sy+1450)),
                  ("WC",(wcl+200,st-800,xm-200,st-150)),
                  ("食品棚",(lr-350,sy+1050,lr,ym-100))]
    else:
        lroom=Polygon([(mr+t,e),(xm,e),(xm,foyer_top),(core_left,foyer_top),
                       (core_left,st),(mr+t,st)])
        rooms=[rectangle("master","主寝室",e,e,mr,st,(2600,1600)),
               Room("bed2","洋室 2",lroom,(5300,2850),"living","L型 / 面積は実形状"),
               rectangle("bed3","洋室 3",e,sy,mr,ym,(2450,5750)),
               rectangle("storage","納戸",mr+t,sy,lr,ym,kind="storage"),wc,
               Room("hall","廊下",Polygon([(e,st+t),(xm,st+t),(xm,sy),
                    (sx,sy),(sx,sy-t),(e,sy-t)]),(3600,st+600),"hall","有効幅 900"),stairs]
        walls += [box(mr,e,mr+t,st),box(e,st,core_left,st+t),
                  box(e,sy-t,sx,sy),box(mr,sy,mr+t,ym),box(lr,sy,sx,ym)]
        doors=[Door("D21","hall","master","h",st+t/2,2700,800,"swing",-1),
               Door("D22","hall","bed2","h",st+t/2,4000,800,"swing",-1),
               Door("D23","hall","bed3","h",sy-t/2,2600,800,"swing",1),
               Door("D24","hall","storage","h",sy-t/2,3800,800,"swing",1),
               Door("D25","hall","wc","h",st+t/2,wcl+100,700,"slide",-1)]
        windows=[("h",e/2,650,1800),("h",e/2,4300,1800),
                 ("v",e/2,900,1200),("v",e/2,5000,1200),
                 ("h",ym+e/2,650,1700),("h",ym+e/2,3950,600),
                 ("v",xm+e/2,wcb+550,450),("v",xm+e/2,6200,600)]
        fixtures=[("収納",(300,st-600,2200,st)),("ベッド",(450,400,1850,2400)),
                  ("収納",(xm-600,350,xm,1350)),("ベッド",(4300,500,5700,2500)),
                  ("収納",(1850,ym-600,3350,ym)),("ベッド",(450,sy+200,1450,sy+2200)),
                  ("収納棚",(mr+t,sy+1200,mr+t+450,ym-100)),
                  ("WC",(wcl+200,st-800,xm-200,st-150))]
    cuts=[door.opening(p.external_wall if door.a=="outside" else t) for door in doors]
    for axis,at,start,width in windows:
        cuts.append(Door("window","","",axis,at,start,width).opening(p.external_wall))
    geometry=unary_union(walls).difference(unary_union(cuts))
    return Floor(number,rooms,doors,geometry,windows,fixtures)


def design_manifest(p=P):
    floors=[floor_plan(n,p) for n in (1,2)]
    return {"revision":"R01", "stage":"floor_plan_approved", "units":"mm",
            "parameters":asdict(p), "assumptions":[
                "7280 × 7280 mm外轮廓及2800 mm层高为用户指定的演示假设。",
                "图面北向和南侧入口仅为展示假设；尚无地块、道路和场地资料。",
                "外墙180 mm、内墙100 mm及门窗、家具尺寸为方案占位参数。",
                "楼梯16个踢面×175 mm，踏面260 mm，梯宽及中间平台900 mm。",
                "房间面积按墙内净边界计算，含家具占地；廊下面积不含楼梯。",
                "楼梯面积为梯间预留面积；二层含楼板开口，不能作为可用楼板面积。",
                "移门按墙内收纳表达，门袋构造与框厚留待深化，不视为已确定产品。",
                "二层厕所900 × 1700 mm偏紧凑；门洞700 mm是平面开口，未扣门框。",
                "层高为楼层基准面间距；楼板、梁及完成面尚未设计。",
                "切妻屋根坡度、屋檐、窗台及门窗高度在三维阶段采用演示参数并单独记录。",
                "尚未验证结构、设备、消防、法规定义面积或实际楼梯头部净空。",
                "用户已确认R01平面布局；STEP和GLB按此布局生成。"],
            "floors":[{"floor":f.number,"gross_outline_area_m2":p.width*p.depth/1e6,
                        "rooms":[{"id":r.id,"name":r.name,"area_m2":round(r.area,4),
                                  "polygon_mm":list(r.shape.exterior.coords),"size_note":r.size_note}
                                 for r in f.rooms],
                        "doors":[asdict(d) for d in f.doors]} for f in floors]}
