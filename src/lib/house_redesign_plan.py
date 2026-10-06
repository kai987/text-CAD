"""Active R10 layout: approved R09 rooms, east-extended entrance-sheltering balcony.

Millimetres; all dimensions are demonstration assumptions. Structural adequacy
and site-specific code compliance have not been established.
"""
from dataclasses import asdict, dataclass

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from lib.house_plan_r01 import Door, Floor, Room, rectangle


@dataclass(frozen=True)
class RedesignParameters:
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
    balcony_left: float = 2010
    balcony_width: float = 6180
    entrance_canopy: bool = False
    balcony_depth: float = 1500
    balcony_rail_thickness: float = 100


P = RedesignParameters()
REVISION = 'R10'
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


def floor_plan(number, p=P):
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
        rooms=[Room('ldk','LDK',ldk,(3500,2250),size_note='L型 / 有効寸法は寸法線参照'),
               rectangle('foyer','玄関',sx,e,xm,foyer_top,(sx+800,850)),
               rectangle('bath','浴室',e,wb,br,ym,(br-800,wb+600),'wet'),
               rectangle('wash','洗面・脱衣 / 洗濯',br+t,wb,wcl-t,ym,
                         ((br+t+wcl-t)/2,wb+750),'wet'),wc,vest,stairs]
        doors=[Door('D01','outside','foyer','h',e/2,sx+200,900,'swing',-1),
               Door('D02','foyer','ldk','h',foyer_top+t/2,sx+250,900,'swing',1),
               Door('D03','ldk','wash','h',wb-t/2,br+t+1050,800,'slide',-1),
               Door('D04','wash','bath','v',br+t/2,wb+150,750,'slide',1),
               Door('O01','ldk','wc_hall','h',sy-t/2,wcl,900,'open'),
               Door('D05','wc_hall','wc','h',ym-p.toilet_depth-t/2,wcl+100,700,'swing',-1),
               Door('O02','ldk','stairs','h',sy-t/2,sx,900,'open')]
        windows=[('h',e/2,650,2100),('v',e/2,1700,1800),
                 ('h',ym+e/2,700,600),('h',ym+e/2,3000,900),
                 ('h',ym+e/2,wcl+220,450),('v',xm+e/2,6200,600)]
        fixtures=[('靴収納',(xm-400,350,xm,1450)),
                  ('キッチン',(450,wb-800,3000,wb-t-100)),
                  ('ダイニング',(3500,2700,4900,3500)),
                  ('ソファ',(650,850,2450,1700)),('TV',(e,2300,e+400,3500)),
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
        rooms=[rectangle('master','主寝室',e,e,p.access_left-t,st,(2530,1300)),
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
        windows=[('h',e/2,650,1600),('h',e/2,5200,1800),
                 ('v',e/2,700,1200),('h',ym+e/2,650,1800),
                 ('h',ym+e/2,wcl+220,450),('v',xm+e/2,6200,600)]
        fixtures=[('ベッド 1400',(430,500,1830,2500)),
                  ('衣類棚',(e+100,sy-t-600,p.access_left-t-100,sy-t)),
                  ('ベッド 1000',(5500,450,6500,2450)),
                  ('CL',(xm-600,200,xm,1200)),
                  ('ベッド 1000',(500,sy+300,1500,sy+2300)),
                  ('CL',(2500,ym-600,4800,ym)),
                  ('WC',(wcl+200,ym-800,wcr-200,ym-150)),
                  ('物干し',(bx+250,-1150,bx+250+1900,-950))]
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


def manifest(p=P):
    return {'revision':REVISION,'stage':'floor_plan_approved','approved_on':'2026-10-07','units':'mm',
            'parameters':asdict(p),'sources':SOURCES,
            'assumptions':[
                'User permits footprint adjustment and requires three bedrooms and a drying balcony.',
                '8190 x 7280 mm replaces the earlier 7280 x 7280 demo outline; heights remain 2800 mm.',
                'South entrance / south balcony / north direction are assumptions without site survey.',
                '6180 x 1500 balcony is outside the main outline; net space excludes 100 mm railing footprint; east edge aligns with the external wall and replaces the separate entry canopy.',
                'Walls 180/100 mm and all doors, windows and furniture are demonstration placeholders.',
                'Toilets remain 900 x 1700 mm, now vertically aligned beside stairs; not wheelchair adapted.',
                '16 risers x 175, tread 260, clear flights/landing 900 mm; slab and headroom not evaluated.',
                'Room areas include fixtures/storage within each room. Stairwell is an opening reservation.',
                'Areas are geometric comparison only, not legal floor/building area measurements.',
                'R10 attic, site, foundation, facade and W/S/RC geometry are coordinated to the approved layout; engineering is pending.',
                'Balcony support, waterproofing, threshold, drainage and railing height/anchorage are pending.',
                'No structural, fire, daylight, ventilation, code, equipment or soil verification is asserted.',
                'User approved R09 rooms on 2026-10-07 and requested an east-extended balcony with the separate canopy removed; R10 keeps the room layout.'],
            'floors':[{'floor':n,'outline_area_m2':p.width*p.depth/1e6,
                       'rooms':[{'id':r.id,'name':r.name,'area_m2':round(r.area,4),
                                 'polygon_mm':list(r.shape.exterior.coords),'size_note':r.size_note}
                                for r in floor_plan(n,p).rooms],
                       'doors':[asdict(d) for d in floor_plan(n,p).doors]}
                      for n in (1,2)]}
