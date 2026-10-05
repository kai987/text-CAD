"""A millimetre-based, single-dwelling Japanese 2LDK concept.

Every dimension is a demonstration assumption. X is east, Y is north;
the common-corridor entrance is north and the balcony is south. This is
one apartment, not an entire apartment building or a permit design.
"""
from dataclasses import asdict, dataclass
from shapely.geometry import box
from shapely.ops import unary_union
from .house_plan import Door, Floor, rectangle


@dataclass(frozen=True)
class ApartmentParameters:
    width: float = 7800
    depth: float = 8400
    storey_height: float = 2800
    external_wall: float = 200
    internal_wall: float = 100
    clear_height: float = 2500
    slab_thickness: float = 200
    balcony_depth: float = 1500
    balcony_guard_height: float = 1100
    west_room_width: float = 3100
    hall_width: float = 1400
    ldk_depth: float = 3000
    bedroom_depth: float = 3000
    bath_width: float = 1400
    toilet_width: float = 1000
    foyer_depth: float = 1300
    door_height: float = 2100
    cabinet_height: float = 2100
    roof_type: str = 'flat ceiling / 単一住戸の天井'


P = ApartmentParameters()


def dimensions(p=P):
    e, t = p.external_wall, p.internal_wall
    xm, ym = p.width-e, p.depth-e
    west = e+p.west_room_width
    hall_left, hall_right = west+t, west+t+p.hall_width
    east = hall_right+t
    ldk_top, bed_bottom = e+p.ldk_depth, ym-p.bedroom_depth
    wet_bottom, wet_top = ldk_top+t, bed_bottom-t
    bath_right, toilet_right = e+p.bath_width, east+p.toilet_width
    assert xm-east >= 2500 and wet_top-wet_bottom >= 1700
    assert p.hall_width >= 1300 and west-bath_right-t >= 1500
    return dict(e=e,t=t,xm=xm,ym=ym,west=west,hl=hall_left,hr=hall_right,
                east=east,lt=ldk_top,bb=bed_bottom,wb=wet_bottom,wt=wet_top,
                br=bath_right,tr=toilet_right,fy=ym-p.foyer_depth)


def window_specs(p=P):
    d=dimensions(p); e,xm,ym=d['e'],d['xm'],d['ym']
    # The south glazing is a pair of full-height sliding balcony doors.
    return [dict(id='W01',axis='h',at=e/2,start=e+700,width=2100,sill=0,height=2100),
            dict(id='W02',axis='h',at=e/2,start=xm-2800,width=2100,sill=0,height=2100),
            dict(id='W03',axis='h',at=ym+e/2,start=e+600,width=1800,sill=1100,height=1100),
            dict(id='W04',axis='h',at=ym+e/2,start=d['east']+350,width=1800,sill=1100,height=1100)]


def apartment_plan(p=P):
    d=dimensions(p)
    e,t,xm,ym,west,hl,hr,east,lt,bb,wb,wt,br,tr,fy=(d[k] for k in
        ('e','t','xm','ym','west','hl','hr','east','lt','bb','wb','wt','br','tr','fy'))
    rooms=[rectangle('ldk','LDK',e,e,xm,lt,(4000,1500)),
           rectangle('master','洋室 1',e,bb,west,ym,(e+1550,bb+1250)),
           rectangle('bed2','洋室 2',east,bb,xm,ym,(east+1350,bb+1250)),
           rectangle('bath','浴室',e,wb,br,wt,(e+700,wb+450),'wet'),
           rectangle('wash','洗面・脱衣',br+t,wb,west,wt,(br+t+800,wb+500),'wet'),
           rectangle('wc','トイレ',east,wb,tr,wt,(east+500,wb+500),'wet'),
           rectangle('storage','納戸',tr+t,wb,xm,wt,(tr+t+800,wb+750),'storage'),
           rectangle('foyer','玄関',hl,fy,hr,ym,(hl+700,fy+600),'hall'),
           rectangle('hall','廊下',hl,wb,hr,fy,(hl+700,wb+1600),'hall'),
           rectangle('balcony','バルコニー',0,-p.balcony_depth,p.width,0,
                     (p.width/2,-p.balcony_depth/2),'balcony')]
    raw=[box(0,0,p.width,p.depth).difference(box(e,e,xm,ym)),
         box(west,wb,hl,ym),box(hr,wb,east,ym),
         box(e,lt,xm,wb),box(e,wt,west,bb),box(east,wt,xm,bb),
         box(br,wb,br+t,wt),box(tr,wb,tr+t,wt)]
    doors=[Door('D01','outside','foyer','h',ym+e/2,hl+400,900,'swing',1),
           Door('D02','hall','ldk','h',lt+t/2,hl,p.hall_width,'open'),
           Door('D03','hall','master','v',west+t/2,bb+350,800,'slide',1),
           Door('D04','hall','bed2','v',hr+t/2,bb+350,800,'slide',1),
           Door('D05','hall','wash','v',west+t/2,wb+200,800,'slide',1),
           Door('D06','wash','bath','v',br+t/2,wb+100,750,'slide',1),
           Door('D07','hall','wc','v',hr+t/2,wb+200,700,'slide',1),
           Door('D08','ldk','storage','h',lt+t/2,tr+t+300,800,'slide',-1)]
    windows=[(w['axis'],w['at'],w['start'],w['width']) for w in window_specs(p)]
    cuts=[door.opening(e if door.a=='outside' else t) for door in doors]
    cuts += [Door('window','','',*w).opening(e) for w in windows]
    fixtures=[('靴収納',(hl,fy+300,hl+350,ym-100)),
              ('収納',(e,bb+300,e+600,bb+1800)),
              ('収納',(xm-600,bb+300,xm,bb+1800)),
              ('収納棚',(xm-400,wb+150,xm-100,wt-150)),
              ('キッチン',(e+100,lt-650,e+2400,lt-50)),
              ('浴槽',(e+100,wt-850,br-100,wt-100)),
              ('洗濯',(br+t+100,wt-700,br+t+700,wt-100)),
              ('洗面',(west-750,wt-650,west-100,wt-100)),
              ('WC',(east+250,wt-800,tr-250,wt-150))]
    floor=Floor(1,rooms,doors,unary_union(raw).difference(unary_union(cuts)),windows,fixtures)
    return floor,unary_union(raw)


def manifest(p=P):
    from .furniture_geometry import furniture_manifest
    floor,_=apartment_plan(p)
    d=dimensions(p)
    interior=sum(r.area for r in floor.rooms if r.id!='balcony')
    return {'id':'apartment','title':'日本の集合住宅 / 2LDK','revision':'A01',
            'drawingRevision':'A01','modelRevision':'A02-3D','units':'mm',
            'interior_reference':'references/interior-furnishings.md','furnishings':[furniture_manifest(floor,'apartment',p)],
            'stage':'concept_proposal','parameters':asdict(p),
            'areas':{'outline':p.width*p.depth/1e6,'interior':round(interior,4),
                     'balcony':p.width*p.balcony_depth/1e6},
            'assumptions':[
                f'{p.width:g} × {p.depth:g} mm 外轮廓、{p.storey_height:g} mm 层高、{p.clear_height:g} mm 室内净高及全部细部尺寸均为演示假设。',
                f'{p.width*p.depth/1e6:.2f}㎡是本示例外轮廓投影面积，包含外墙与隔墙，不代表房产登记面积、专有面积或法定建筑面积。',
                f'{interior:.2f}㎡是房间净边界面积之和，包含柜体和设备占地，排除所有墙体和阳台。',
                f'{p.width*p.balcony_depth/1e6:.2f}㎡阳台为{p.width:g} × {p.balcony_depth:g} mm示意板面投影，单独计算，包含栏板投影。',
                '北侧公共走廊入户、南侧阳台及北向均为展示假设，未提供地块或整栋建筑资料。',
                f'外墙/户间墙{p.external_wall:g} mm、室内隔墙{p.internal_wall:g} mm，楼板{p.slab_thickness:g} mm；模型为单一住户，无内部楼梯和坡屋顶。',
                f'中部走廊宽{p.hall_width:g} mm；玄关鞋柜深350 mm后剩余通行宽{p.hall_width-350:g} mm。',
                '两卧室北侧设高窗，LDK南侧设两组落地移门通向阳台；户间墙无侧窗。',
                '玄关高差用分界线示意；模型完成面统一Z=0，未生成防水、排水坡度或门槛构造。',
                '室内门洞700/750/800 mm；移门使用外挂轨道概念并留出墙边空间，门洞为毛洞尺寸。',
                f'浴室{p.bath_width:g} × {d["wt"]-d["wb"]:g} mm、洗面脱衣{d["west"]-d["br"]-p.internal_wall:g} × {d["wt"]-d["wb"]:g} mm、厕所{p.toilet_width:g} × {d["wt"]-d["wb"]:g} mm为方案预留。',
                '顶板及阳台栏板仅表达外形；家具与卫浴根据公开尺寸参考进行原创参数化建模，未选实际产品。',
                f'顶板为Z={p.clear_height:g}至{p.clear_height+p.slab_thickness:g} mm；至{p.storey_height:g} mm楼层基准面余{p.storey_height-p.clear_height-p.slab_thickness:g} mm层间构造未建模。',
                '未验证结构、采光通风、消防疏散、设备管井、阳台隔板或日本建筑确认申报要求。'],
            'floors':[{'floor':1,'rooms':[{'id':r.id,'name':r.name,
                       'area':round(r.area,4),'size':r.size_note} for r in floor.rooms]}],
            'doors':[asdict(door) for door in floor.doors],
            'connections':[['foyer','hall'],['ldk','balcony']],
            'windows':window_specs(p),'axis_convention':'X east, Y north, Z up; GLB metres and Y up'}
