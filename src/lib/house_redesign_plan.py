"""Active R15 layout: reflected rooms, east glazing and a facing kitchen.

Millimetres; all dimensions are demonstration assumptions. Structural adequacy
and site-specific code compliance have not been established.
"""
from dataclasses import asdict, dataclass, replace

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from lib.house_plan_r01 import Door, Floor, Room, rectangle


@dataclass(frozen=True)
class RedesignParameters:
    mirror_layout: bool = True
    kitchen_width: float = 2550
    kitchen_depth: float = 650
    kitchen_south: float = 3180
    kitchen_wall_gap: float = 1020
    width: float = 8190
    depth: float = 7280
    storey_height: float = 2800
    external_wall: float = 180
    internal_wall: float = 100
    stair_width: float = 900
    stair_landing: float = 900
    risers: int = 16
    tread: float = 260
    bath_width: float = 1820
    bath_depth: float = 1820
    toilet_width: float = 900
    toilet_depth: float = 1700
    foyer_depth: float = 1600
    south_room_depth: float = 3100
    hall_width: float = 900
    access_left: float = 3380
    balcony_left: float = 0
    balcony_width: float = 8190
    entrance_canopy: bool = False
    balcony_depth: float = 1000
    balcony_supports: bool = False
    south_living_window_width: float = 2100
    south_master_window_width: float = 1600
    south_bedroom_window_width: float = 1800
    south_window_sill: float = 0
    south_window_height: float = 2200
    balcony_rail_thickness: float = 100


P = RedesignParameters()
REVISION = 'R15'
SOURCES = [
    {'title': 'ヤマト住建 加古川店 / 27-35坪参考プラン',
     'url': 'https://www.yamatojk.co.jp/wordpress/wp-content/uploads/2023/01/kakogawa-1116.pdf',
     'observed': 'PDF p2: compact wet cores, 3 bedrooms, stairs/halls, south balconies; organization reference only.'},
    {'title': '一条工務店 HUGme S34-4045-0002',
     'url': 'https://www.ichijo.co.jp/lineup/hugme/madori/plandetail/?id=S34-4045-0002&type=2f',
     'observed': 'Official 3LDK two-storey south-entry plan, living stairs and storage; 7280 x 8190 example. Not copied.'},
    {'title': 'ミサワホーム九州 SMART STYLE Roomie',
     'url': 'https://kyushu.misawa.co.jp/smart_style_roomie/',
     'observed': 'Official compact housework / circulation / storage design approach; no performance claim inherited.'},
]


def dimensions(p=P):
    e, t = p.external_wall, p.internal_wall
    xm, ym = p.width-e, p.depth-e
    sw = 2*p.stair_width+t
    sd = (p.risers//2-1)*p.tread+p.stair_landing
    sx, sy = xm-sw, ym-sd
    wcr, wcl = sx-t, sx-t-p.toilet_width
    bathr = e+p.bath_width
    wetbottom = ym-p.bath_depth
    st = e+p.south_room_depth
    ar = p.access_left+p.hall_width
    bx = p.balcony_left
    if bx < 0 or bx+p.balcony_width > p.width:
        raise ValueError("Balcony must stay within the south facade extent.")
    if not (wetbottom >= sy+p.hall_width and wcl-t > bathr+t and
            p.access_left-t > e+2400 and sx > ar+t):
        raise ValueError('Parameters do not preserve this proposal topology; redesign partitions first.')
    return dict(e=e,t=t,xm=xm,ym=ym,sx=sx,sy=sy,wcl=wcl,wcr=wcr,
                bathr=bathr,wetbottom=wetbottom,st=st,ar=ar,bx=bx)


def south_floor_window(window,p=P):
    """Only the three wide south living/bedroom apertures are floor-height."""
    axis,at,_,width=window
    return axis=='h' and abs(at-p.external_wall/2)<1e-6 and width>1000


from .orientation import orient_record

@orient_record
def balcony_drying_bounds(p=P):
    """Move the 1900 mm rack east of the unchanged 800 mm balcony-door swing."""
    left=p.access_left+p.hall_width+200
    bottom=-p.balcony_depth+350
    bounds=(left,bottom,left+1900,bottom+200)
    if not box(dimensions(p)['bx']+p.balcony_rail_thickness,
               -p.balcony_depth+p.balcony_rail_thickness,
               dimensions(p)['bx']+p.balcony_width-p.balcony_rail_thickness,0).covers(box(*bounds)):
        raise ValueError('Drying rack must remain within the clear balcony.')
    return bounds


def _canonical_floor_plan(number, p=P):
    if number not in (1, 2):
        raise ValueError('Two-storey proposal only')
    d=dimensions(p)
    e,t,xm,ym,sx,sy,wcl,wcr,br,wb,st,ar,bx=(d[k] for k in
        ('e','t','xm','ym','sx','sy','wcl','wcr','bathr','wetbottom','st','ar','bx'))
    wc=rectangle('wc','トイレ',wcl,ym-p.toilet_depth,wcr,ym,
                 (wcl+p.toilet_width/2,ym-p.toilet_depth+650),'wet')
    stairs=rectangle('stairs','階段',sx,sy,xm,ym,kind='stair')
    vest=rectangle('wc_hall','ホール',wcl,sy,wcr,ym-p.toilet_depth-t,kind='hall')
    if number == 1:
        foyer_top=e+p.foyer_depth
        ldk=Polygon([(e,e),(wcr,e),(wcr,foyer_top+t),(xm,foyer_top+t),
                     (xm,sy-t),(wcl-t,sy-t),
                     (wcl-t,wb-t),(e,wb-t)])
        # Remove the enclosed WC forecourt; retain the WC itself and its door.
        ldk=unary_union([ldk,box(wcl-t,sy-t,wcr,ym-p.toilet_depth-t)])
        landing_y=sy+(p.risers//2-1)*p.tread
        storage_left=xm-p.stair_width
        stairs.shape=stairs.shape.difference(box(storage_left,sy,xm,landing_y))
        stairs.label=(sx+p.stair_width/2,sy+500)
        store=rectangle('under_stairs','階段下収納',storage_left+50,sy,xm-50,landing_y-60,
                        ((storage_left+xm)/2,sy+650),'storage')
        rooms=[Room('ldk','LDK',ldk,(3500,2250),size_note='L型 / 有効寸法は寸法線参照'),
               rectangle('foyer','玄関',sx,e,xm,foyer_top,(sx+800,850)),
               rectangle('bath','浴室',e,wb,br,ym,(br-800,wb+600),'wet'),
               rectangle('wash','洗面・脱衣 / 洗濯',br+t,wb,wcl-t,ym,
                         ((br+t+wcl-t)/2,wb+750),'wet'),wc,stairs,store]
        doors=[Door('D01','outside','foyer','h',e/2,sx+200,900,'swing',-1),
               Door('D02','foyer','ldk','h',foyer_top+t/2,sx+250,900,'swing',1),
               Door('D03','ldk','wash','h',wb-t/2,br+t+1050,800,'slide',-1),
               Door('D04','wash','bath','v',br+t/2,wb+150,750,'slide',1),
               Door('D05','ldk','wc','h',ym-p.toilet_depth-t/2,wcl+100,700,'swing',-1),
               Door('O02','ldk','stairs','h',sy-t/2,sx,900,'open'),
               Door('D07','ldk','under_stairs','h',sy-t/2,storage_left+100,700,'swing',-1)]
        windows=[('h',e/2,650,p.south_living_window_width),('v',e/2,1700,1800),
                 ('h',ym+e/2,700,600),('h',ym+e/2,3000,900),
                 ('h',ym+e/2,wcl+220,450),('v',xm+e/2,6200,600)]
        fixtures=[('靴収納',(xm-400,350,xm,1450)),
                  ('対面キッチン',(e+p.kitchen_wall_gap,p.kitchen_south,e+p.kitchen_wall_gap+p.kitchen_width,p.kitchen_south+p.kitchen_depth)),
                  ('冷蔵庫',(e+20,wb-t-750,e+920,wb-t)),
                  ('カップボード',(1200,wb-t-450,2950,wb-t)),
                  ('ダイニング',(1000,1150,1850,2750)),
                  ('ソファ',(3200,850,5800,2400)),('TV',(4250,e,5650,e+350)),
                  ('食品収納',(4200,wb-700,wcl-t,wb-t)),
                  ('浴槽',(330,ym-850,br-150,ym-150)),
                  ('洗面',(br+t+100,ym-600,br+t+1100,ym-100)),
                  ('洗濯機',(br+t+1350,ym-700,br+t+2000,ym-50)),
                  ('リネン',(wcl-t-500,wb+100,wcl-t,wb+700)),
                  ('WC',(wcl+200,ym-800,wcr-200,ym-150))]
    else:
        # Public passage reaches the balcony without passing through a bedroom.
        hall=unary_union([box(p.access_left,e,ar,st+t),box(p.access_left,st+t,xm,sy-t)])
        r=p.balcony_rail_thickness
        balcony=rectangle('balcony','バルコニー / 物干し',bx+r,-p.balcony_depth+r,
                          bx+p.balcony_width-r,0,(bx+p.balcony_width-850,-450),'outside')
        balcony.name='バルコニー'
        rooms=[rectangle('master','主寝室',e,e,p.access_left-t,st,(2820,1300)),
               rectangle('closet','収納',e,st+t,p.access_left-t,sy-t,(1700,st+t+150),'storage'),
               rectangle('bed2','洋室 2',ar+t,e,xm,st,(7350,1450)),
               rectangle('bed3','洋室 3',e,sy,wcl-t,ym,(3000,5500)),
               Room('hall','ホール / 物干し通路',hall,(5400,st+t+440),'hall','通路幅 900'),
               wc,vest,stairs,balcony]
        doors=[Door('D21','hall','master','v',p.access_left-t/2,1900,800,'slide',-1),
               Door('D22','hall','bed2','v',ar+t/2,1900,800,'slide',-1),
               Door('D23','hall','bed3','h',sy-t/2,p.access_left+50,800,'slide',-1),
               Door('D24','master','closet','h',st+t/2,430,2600,'bifold',-1),
               Door('O21','hall','wc_hall','h',sy-t/2,wcl,900,'open'),
               Door('D25','wc_hall','wc','h',ym-p.toilet_depth-t/2,wcl+100,700,'swing',-1),
               Door('O22','hall','stairs','h',sy-t/2,sx+p.stair_width+t,900,'open'),
               Door('D26','hall','balcony','h',e/2,p.access_left+50,800,'swing',-1)]
        windows=[('h',e/2,650,p.south_master_window_width),('h',e/2,5200,p.south_bedroom_window_width),
                 ('v',e/2,700,1200),('v',e/2,5400,1000),('h',ym+e/2,650,1800),
                 ('h',ym+e/2,wcl+220,450),('v',xm+e/2,6200,600)]
        fixtures=[('ベッド 1400',(430,950,2430,2350)),
                  ('衣類棚',(e+100,sy-t-600,p.access_left-t-100,sy-t)),
                  ('ベッド 1000',(5500,850,6500,2850)),
                  ('CL',(xm-600,200,xm,1200)),
                  ('ベッド 1000',(500,sy+300,1500,sy+2300)),
                  ('CL',(2500,ym-600,4800,ym)),
                  ('WC',(wcl+200,ym-800,wcr-200,ym-150)),
                  ('物干し',balcony_drying_bounds(p))]
    building=box(0,0,p.width,p.depth)
    interior_rooms=[r.shape for r in rooms if r.kind!='outside']
    walls=building.difference(unary_union(interior_rooms))
    if number == 2:
        r=p.balcony_rail_thickness
        rails=unary_union([box(bx,-p.balcony_depth,bx+r,0),
                          box(bx+p.balcony_width-r,-p.balcony_depth,bx+p.balcony_width,0),
                          box(bx,-p.balcony_depth,bx+p.balcony_width,-p.balcony_depth+r)])
        walls=unary_union([walls,rails])
    cuts=[door.opening(p.external_wall if 'outside' in (door.a,door.b) or
                       'balcony' in (door.a,door.b) else t) for door in doors]
    cuts += [Door('window','','',axis,at,start,width).opening(p.external_wall)
             for axis,at,start,width in windows]
    return Floor(number,rooms,doors,walls.difference(unary_union(cuts)),windows,fixtures)


def floor_plan(number, p=P):
    """World-space plan; the west entry is a reflection of the authoring topology."""
    from shapely.affinity import scale
    from .orientation import canonical, bounds
    f=_canonical_floor_plan(number,canonical(p))
    if not p.mirror_layout:return f
    reflect=lambda geom:scale(geom,xfact=-1,yfact=1,origin=(p.width/2,0))
    for r in f.rooms:
        r.shape=reflect(r.shape);r.label=(p.width-r.label[0],r.label[1])
    for d in f.doors:
        if d.axis=='h':
            d.start=p.width-d.start-d.width
            d.hinge_at_end=d.kind=='swing'
            if d.kind=='slide':d.direction=-d.direction
        else:d.at=p.width-d.at
    f.walls=reflect(f.walls)
    f.windows=[(axis,p.width-at,start,w) if axis=='v' else (axis,at,p.width-start-w,w) for axis,at,start,w in f.windows]
    f.fixtures=[(name,tuple(bounds(b,p.width))) for name,b in f.fixtures]
    return f


def manifest(p=P):
    return {'revision':REVISION,'stage':'user_requested_storage_and_four_person_furnishings','requested_on':'2026-10-07','units':'mm',
            'parameters':asdict(p),'sources':SOURCES,
            'assumptions':[
                'User permits footprint adjustment and requires three bedrooms and a drying balcony.',
                '8190 x 7280 mm replaces the earlier 7280 x 7280 demo outline; heights remain 2800 mm.',
                'South entrance / south balcony / north direction are assumptions without site survey.',
                '8190 x 1000 balcony is outside the main outline; net space excludes 100 mm railing footprint; both ends align with the external walls and retains no separate entry canopy; the 1300 mm porch projects 300 mm beyond the balcony.',
                'Walls 180/100 mm and all doors, windows and furniture are demonstration placeholders.',
                'Three south living/bedroom windows retain 2100/1600/1800 mm widths, with 0 mm sill and 2200 mm height; glazing, opening mechanism, waterproofing and structural headers remain pending.',
                'Toilets remain 900 x 1700 mm, now vertically aligned beside stairs; not wheelchair adapted.',
                '16 risers x 175, tread 260, clear flights/landing 900 mm; slab and headroom not evaluated.',
                'Room areas include fixtures/storage within each room. Stairwell is an opening reservation.',
                'Areas are geometric comparison only, not legal floor/building area measurements.',
                'R10 attic, site, foundation, facade and W/S/RC geometry are coordinated to the approved layout; engineering is pending.',
                'R13 removes balcony support posts and footings; cantilever capacity, connections, waterproofing, threshold, drainage and guard anchorage remain pending.',
                'No structural, fire, daylight, ventilation, code, equipment or soil verification is asserted.',
                'R15 mirrors both floors left/right at user request: southwest entrance and northwest stairs. East windows serve the LDK and both east bedrooms; west windows serve stairs only.',
                'R15 removes the F1 enclosed WC forecourt and opens this area to the LDK; the 900 x 1700 mm WC and F2 rooms stay fixed.',
                'R15 adds an 800 x 1760 mm stair-under storage room with a 700 mm door, stepped low ceiling, and shelves. Upper stair treads use a 200 mm illustrative thickness; load capacity, connections and fire separation remain uncalculated.',
                'R15 uses a four-seat 2600 x 1550 mm L sofa, opposing south-wall TV, coffee table, 1600 x 850 mm dining table with four chairs, and 900 x 750 mm side-by-side refrigerator. Furniture clearances are demo design targets.',
                '2550 x 650 mm island facing kitchen, 850 mm worktop, main rear aisle 900 mm and 1750 x 450 mm cupboard are demonstration assumptions; actual products, exhaust duct, services and fire clearances remain pending.'],
            'floors':[{'floor':n,'outline_area_m2':p.width*p.depth/1e6,
                       'rooms':[{'id':r.id,'name':r.name,'area_m2':round(r.area,4),
                                 'polygon_mm':list(r.shape.exterior.coords),'size_note':r.size_note}
                                for r in floor_plan(n,p).rooms],
                       'doors':[asdict(d) for d in floor_plan(n,p).doors]}
                      for n in (1,2)]}
