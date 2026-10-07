"""Original, parametric furniture for the two demonstration dwellings.

All source geometry is millimetres, X east / Y north / Z up. Local furniture
front faces -Y and a bed's head is +Y. Placement x/y is the *rotated* footprint's
south-west corner; positive rotation is counter-clockwise about Z. Every visible
piece is a closed solid, named below F#:furniture for optional display/sectioning.

The furniture is original illustrative geometry informed by published compact
furniture dimensions, not downloaded assets or a replica of a branded product.
The apartment's 1200 mm bed frame is a deliberately narrow custom concept to
retain 650 mm access to both the entry and existing wardrobe. Dimensions describe
the generated furniture, not a claim that an off-the-shelf product will fit.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from math import cos, pi, sin

from cadgen import build123d as bd, srgb
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from .native_spatial import polygon_metrics


COLORS={
    'oak':'#BA9470','oak_light':'#D5B797','oak_dark':'#8B7058',
    'linen':'#EDE8DE','pillow':'#F5F2EB','blanket':'#819691',
    'upholstery':'#92A5A1','seat':'#A4B5AE','metal':'#43484A',
    'black':'#22272C','screen':'#30454E','handle':'#AAA69B',
}


@dataclass(frozen=True)
class Placement:
    id: str
    room: str
    kind: str
    x: float
    y: float
    width: float
    depth: float
    rotation: float = 0
    height: float = 0
    mirror_local_x: bool = False

    def footprint(self):
        shape=affinity.rotate(box(0,0,self.width,self.depth),self.rotation,origin=(0,0))
        x1,y1,_,_=shape.bounds
        return affinity.translate(shape,self.x-x1,self.y-y1)


def _named(shape,label,color):
    shape.label=label;shape.color=srgb(COLORS[color])
    return shape


def _box(bounds,label,color,radius=0):
    x,y,z,x2,y2,z2=bounds
    shape=bd.Box(x2-x,y2-y,z2-z,align=(bd.Align.MIN,bd.Align.MIN,bd.Align.MIN))
    if radius:
        shape=bd.fillet(shape.edges(),radius=min(radius,(x2-x)/3,(y2-y)/3,(z2-z)/3))
    return _named(shape.moved(bd.Location((x,y,z))),label,color)


def _leg(x,y,z,radius,height,label,color='oak_dark'):
    shape=bd.Cylinder(radius,height,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))
    return _named(shape.moved(bd.Location((x,y,z))),label,color)


def _feet(prefix,w,d,height,inset=60,radius=22,color='oak_dark'):
    return [_leg(x,y,0,radius,height,f'{prefix}:leg_{i}',color)
            for i,(x,y) in enumerate([(inset,inset),(w-inset,inset),
                                      (inset,d-inset),(w-inset,d-inset)],1)]


def bed(prefix,w=1470,d=2020):
    """Low timber bed: separate feet, rounded mattress, pillows and duvet."""
    parts=_feet(prefix,w,d-70,135,inset=85,radius=30)
    parts += [_box((0,0,135,w,d-70,285),f'{prefix}:frame','oak',18),
              _box((0,d-70,80,w,d,800),f'{prefix}:headboard','oak_light',14),
              _box((22,22,285,w-22,d-92,480),f'{prefix}:mattress','linen',45),
              _box((28,28,481,w-28,d*.65,528),f'{prefix}:blanket','blanket',15)]
    # Pillows remain above the mattress and clear of the duvet's head edge.
    count=2 if w>=1300 else 1
    pw=min(570,(w-150-(count-1)*40)/count)
    start=(w-(count*pw+(count-1)*40))/2
    for i in range(count):
        x=start+i*(pw+40)
        parts.append(_box((x,d-510,481,x+pw,d-140,585),f'{prefix}:pillow_{i+1}','pillow',34))
    return bd.Compound(children=parts,label=prefix)


def sofa(prefix,w=1600,d=850):
    """Two-seat sofa with timber feet, rounded arms and individual cushions."""
    parts=_feet(prefix,w,d,145,inset=90,radius=24)
    parts += [_box((35,30,145,w-35,d-35,285),f'{prefix}:base','upholstery',28),
              _box((20,d-155,270,w-20,d,800),f'{prefix}:back','upholstery',35),
              _box((0,0,245,115,d-65,645),f'{prefix}:arm_left','upholstery',32),
              _box((w-115,0,245,w,d-65,645),f'{prefix}:arm_right','upholstery',32)]
    inner=w-240;cw=(inner-12)/2
    for i in range(2):
        x=120+i*(cw+12)
        parts.append(_box((x,30,286,x+cw,d-172,452),f'{prefix}:seat_{i+1}','seat',34))
        parts.append(_box((x,d-167,453,x+cw,d-82,750),f'{prefix}:back_cushion_{i+1}','seat',25))
    return bd.Compound(children=parts,label=prefix)


def table(prefix,w,d,height=380):
    top_thickness=35 if height<500 else 32
    legs=_feet(prefix,w,d,height-top_thickness,inset=70,radius=22)
    legs.append(_box((0,0,height-top_thickness,w,d,height),f'{prefix}:top','oak_light',12))
    return bd.Compound(children=legs,label=prefix)


def chair(prefix,w=450,d=420):
    parts=_feet(prefix,w,d,430,inset=45,radius=17)
    parts += [_box((0,0,420,w,d-30,450),f'{prefix}:seat_frame','oak',9),
              _box((12,8,451,w-12,d-42,485),f'{prefix}:seat_cushion','linen',11),
              _box((12,d-55,430,47,d-15,740),f'{prefix}:back_post_left','oak',7),
              _box((w-47,d-55,430,w-12,d-15,740),f'{prefix}:back_post_right','oak',7),
              _box((0,d-50,640,w,d,790),f'{prefix}:backrest','oak_light',15)]
    return bd.Compound(children=parts,label=prefix)


def television(prefix,w=1200,d=350):
    """Low console, split drawer fronts, television stand and opaque screen."""
    parts=_feet(prefix,w,d,100,inset=55,radius=19)
    parts.append(_box((0,15,100,w,d,425),f'{prefix}:console','oak',8))
    for i in range(2):
        x=10+i*w/2
        parts.append(_box((x,0,114,x+w/2-20,13,395),f'{prefix}:drawer_{i+1}','oak_light',4))
        parts.append(_box((x+w/4-55,1,368,x+w/4+55,8,376),f'{prefix}:pull_{i+1}','handle',2))
    sw=min(1060,w-100);sh=sw*9/16;left=(w-sw)/2
    parts += [_box((w/2-150,d/2-65,425,w/2+150,d/2+65,440),f'{prefix}:tv_foot','metal',5),
              _box((w/2-28,d/2-17,440,w/2+28,d/2+17,545),f'{prefix}:tv_stem','metal',4),
              _box((left,d/2-22,525,left+sw,d/2+22,525+sh),f'{prefix}:tv_bezel','black',10),
              _box((left+14,d/2-25,539,left+sw-14,d/2-22,525+sh-14),f'{prefix}:tv_screen','screen',.8)]
    return bd.Compound(children=parts,label=prefix)


def furniture_placements(floor,model_id,p):
    """Stable placements derived from the supplied approved room boundaries."""
    if model_id=='house' and getattr(p,'mirror_layout',False):
        from .orientation import canonical, side_name
        from .house_redesign_plan import floor_plan
        q=canonical(p)
        return [replace(item,id=side_name(item.id),x=p.width-item.footprint().bounds[2],rotation=-item.rotation,mirror_local_x=True) for item in furniture_placements(floor_plan(floor.number,q),model_id,q)]
    rooms={r.id:r for r in floor.rooms}
    result=[]
    def put(id,room,kind,x,y,w,d,angle=0,height=0):
        result.append(Placement(id,room,kind,x,y,w,d,angle,height))
    if model_id=='house':
        fixtures={name:bounds for name,bounds in floor.fixtures}
        if floor.number==1:
            x,y,x2,y2=fixtures['ソファ']
            put('sofa','ldk','sofa',x,y,x2-x,y2-y)
            put('coffee_table','ldk','table',1100,2000,900,500,0,380)
            x,y,x2,y2=fixtures['TV']
            put('television','ldk','television',x,y,y2-y,x2-x,90)
            x,y,x2,y2=fixtures['ダイニング']
            put('dining_table','ldk','table',x,y,x2-x,y2-y,0,730)
            put('dining_chair_west','ldk','chair',x-530,y+200,450,420,90)
            put('dining_chair_east','ldk','chair',x2+200,y+200,450,420,270)
        else:
            beds=[bounds for name,bounds in floor.fixtures if name.startswith('ベッド')]
            for room,bounds in zip(('master','bed2','bed3'),beds):
                x,y,x2,y2=bounds
                if room=='master' and x2-x>y2-y:
                    put('bed',room,'bed',x,y,y2-y,x2-x,90)
                else:
                    put('bed',room,'bed',x,y,x2-x,y2-y)
    elif model_id=='apartment':
        x,y,x2,y2=rooms['ldk'].shape.bounds
        put('sofa','ldk','sofa',x2-900,y+800,1500,850,270)
        put('coffee_table','ldk','table',x2-1900,y+1050,900,450,90,380)
        put('television','ldk','television',x2-2700,y+950,1200,350,90)
        put('dining_table','ldk','table',x+850,y+800,1200,650,0,730)
        put('dining_chair_west','ldk','chair',x+380,y+850,450,420,90)
        put('dining_chair_east','ldk','chair',x+2100,y+850,450,420,270)
        x,y,x2,y2=rooms['master'].shape.bounds
        put('bed','master','bed',x+1250,y2-2160,1200,2020)
        x,y,x2,y2=rooms['bed2'].shape.bounds
        put('bed','bed2','bed',x+300,y2-1080,1030,2020,270)
    else:
        raise ValueError(f'Unknown furniture model: {model_id}')
    return result


def furniture_group(floor,model_id,p):
    if model_id=='house' and getattr(p,'mirror_layout',False):
        from .orientation import canonical, shape
        from .house_redesign_plan import floor_plan
        q=canonical(p)
        return shape(furniture_group(floor_plan(floor.number,q),'house',q),p.width)
    """Return the named F#:furniture assembly; preserve every object/part name."""
    children=[];z=(floor.number-1)*p.storey_height
    for item in furniture_placements(floor,model_id,p):
        label=f'F{floor.number}:furniture:{item.room}:{item.id}'
        if item.kind=='bed':local=bed(label,item.width,item.depth)
        elif item.kind=='sofa':local=sofa(label,item.width,item.depth)
        elif item.kind=='table':local=table(label,item.width,item.depth,item.height)
        elif item.kind=='chair':local=chair(label,item.width,item.depth)
        else:local=television(label,item.width,item.depth)
        raw=affinity.rotate(box(0,0,item.width,item.depth),item.rotation,origin=(0,0))
        x1,y1,_,_=raw.bounds
        children.append(local.rotate(bd.Axis.Z,item.rotation).moved(bd.Location((item.x-x1,item.y-y1,z))))
    return bd.Compound(children=children,label=f'F{floor.number}:furniture')


def door_sweep(door):
    if door.kind!='swing':return Polygon()
    if door.axis!='h':raise ValueError('Only horizontal hinged openings currently occur in these plans')
    return Polygon([(door.start,door.at)]+[(door.start+door.width*cos(pi*i/180/2),
        door.at+door.direction*door.width*sin(pi*i/180/2)) for i in range(181)])


def clearance_zones(floor,model_id,p):
    """Named project-layout targets; 650 mm is a design target, not a code claim."""
    if model_id=='house' and getattr(p,'mirror_layout',False):
        from .orientation import canonical, side_name
        from .house_redesign_plan import floor_plan
        q=canonical(p)
        return [(side_name(name),affinity.scale(geom,xfact=-1,yfact=1,origin=(p.width/2,0))) for name,geom in clearance_zones(floor_plan(floor.number,q),model_id,q)]
    rooms={r.id:r for r in floor.rooms};zones=[]
    # A full-width 650 mm approach on the furnished room side of every doorway.
    furnished={item.room for item in furniture_placements(floor,model_id,p)}
    for door in floor.doors:
        for room_id in {door.a,door.b}&furnished:
            room=rooms[room_id].shape
            thick=p.external_wall if {'outside','balcony'} & {door.a,door.b} else p.internal_wall
            half=thick/2
            if door.axis=='h':
                candidates=[box(door.start,door.at-half-650,door.start+door.width,door.at-half),
                            box(door.start,door.at+half,door.start+door.width,door.at+half+650)]
            else:
                candidates=[box(door.at-half-650,door.start,door.at-half,door.start+door.width),
                            box(door.at+half,door.start,door.at+half+650,door.start+door.width)]
            for candidate in candidates:
                if room.intersection(candidate).area>candidate.area*.99:
                    zones.append((f'{door.id}:{room_id}:650mm_approach',candidate))
        if door.kind=='swing':zones.append((f'{door.id}:door_sweep',door_sweep(door)))
    # Retain the actual cabinet front, not a blanket buffer behind solid walls.
    for index,(name,bounds) in enumerate(floor.fixtures):
        if name not in ({'収納','衣類棚','CL'} if model_id=='house' else {'収納'}):continue
        x1,y1,x2,y2=bounds
        if model_id=='apartment':
            zone=box(x2,y1,x2+650,y2) if x1<p.width/2 else box(x1-650,y1,x1,y2)
        elif x2>p.width-1000:
            zone=box(x1-650,y1,x1,y2)
        else:zone=box(x1,y1-650,x2,y1)
        zones.append((f'wardrobe_{index}:650mm_front',zone))
    if 'ldk' in rooms:
        room=rooms['ldk'].shape;x,y,x2,y2=room.bounds
        for name,bounds in floor.fixtures:
            if name=='対面キッチン':
                a,b,c,d=bounds;zones.append(('kitchen:900mm_working_rear',box(a,d,c,d+900)))
            if name=='キッチン':
                a,b,c,d=bounds;zones.append(('kitchen:900mm_working_front',box(a,b-900,c,b)))
        if model_id=='house':
            routes=[[(6800,3100),(6560,3700),(6560,4500)],
                    [(6800,3100),(6800,3700),(5560,3700),(5560,5800)],
                    [(5560,3900),(4600,3900),(3900,4200),(3550,4900),(3550,5700)]]
        else:
            routes=[[(4100,y2-20),(4100,600),(1500,600),(1500,y+10)],
                    [(4100,600),(5900,600),(5900,y+10)],
                    [(4100,y2-350),(6700,y2-350),(6700,y2-20)],
                    [(4100,2100),(1500,2100)]]
            # Broad continuous 800 mm balcony landing in front of both sliders.
            for axis,at,start,width in floor.windows:
                if axis=='h' and at<p.external_wall:
                    zones.append((f'balcony_slider_{start:g}:800mm_landing',box(start,y,start+width,y+800)))
        for i,path in enumerate(routes,1):
            zones.append((f'ldk:route_{i}:650mm',LineString(path).buffer(325,cap_style='flat').intersection(room)))
    if model_id=='house':
        from .house_redesign_plan import south_floor_window
        for axis,at,start,width in floor.windows:
            if south_floor_window((axis,at,start,width),p):
                zones.append((f'south_window_{start:g}:650mm_approach',box(start,p.external_wall,start+width,p.external_wall+650)))
    return zones


def clearance_report(floor,model_id,p,*,backend='auto'):
    placements=furniture_placements(floor,model_id,p)
    furnished={item.room for item in placements}
    rooms={r.id:r.shape.buffer(.001) for r in floor.rooms if r.id in furnished}
    footprints=[item.footprint() for item in placements]
    placeholders={'ベッド'}
    if model_id=='house':placeholders.update({'ソファ','TV','ダイニング','ベッド 1400','ベッド 1000'})
    fixtures=[(name,bounds,box(*bounds)) for name,bounds in floor.fixtures if name not in placeholders]
    zones=clearance_zones(floor,model_id,p)
    checks=[];geometries=[];geometry_indices={};area_pairs=[];cover_pairs=[];evaluations=[]
    def geometry_index(shape):
        # Shared room, wall, fixture and path polygons are uploaded once. Retain
        # the objects in geometries so their identity cannot be recycled.
        key=id(shape)
        if key not in geometry_indices:
            geometry_indices[key]=len(geometries);geometries.append(shape)
        return geometry_indices[key]
    def add(name,a,b,*,covers=False,evidence=None):
        checks.append({'check':name,'pass':False,'evidence':evidence})
        pairs=cover_pairs if covers else area_pairs
        evaluations.append((covers,len(pairs)))
        pairs.append((geometry_index(a),geometry_index(b)))
    for index,item in enumerate(placements):
        shape=footprints[index]
        add(f'{item.room}:{item.id}:inside_room',rooms[item.room],shape,covers=True,evidence=list(shape.bounds))
        add(f'{item.room}:{item.id}:clear_walls',floor.walls,shape)
        for name,bounds,fixture in fixtures:
            add(f'{item.room}:{item.id}:clear_fixture:{name}:{bounds}',shape,fixture)
        for name,zone in zones:
            add(f'{item.room}:{item.id}:clear_zone:{name}',shape,zone)
        for other_index in range(index+1,len(placements)):
            other=placements[other_index]
            add(f'{item.room}:{item.id}:separate_from:{other.room}:{other.id}',shape,footprints[other_index])
    areas,covered=polygon_metrics(geometries,area_pairs,cover_pairs,backend=backend)
    for row,(covers,index) in zip(checks,evaluations):
        row['pass']=bool(covered[index] if covers else areas[index]<.001)
    return checks


def furniture_manifest(floor,model_id,p):
    return {'model':model_id,'floor':floor.number,'units':'mm','layer':f'F{floor.number}:furniture',
            'coordinate_convention':'X east, Y north, Z up; x/y is the rotated footprint minimum; furniture front is local -Y',
            'assumptions':['Original conceptual furniture, not branded-product geometry or a procurement specification.',
                           'Wardrobe/door approach target 650 mm, kitchen working strip 900 mm; project layout assumptions, not compliance certification.',
                           'Apartment master uses a custom 1200 mm frame to retain 650 mm side access. House bedroom 2 uses a single bed.',
                           'Chairs are shown pulled clear of the table; paths and door sweeps are checked in this displayed position.'],
            'objects':[{**asdict(item),'footprint_mm':list(item.footprint().bounds)} for item in furniture_placements(floor,model_id,p)]}
