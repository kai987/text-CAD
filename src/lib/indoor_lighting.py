"""R17 original room luminaires. Sizes, colour and intensity are demo inputs.

No product selection, photometry, wiring, wet-area rating or installation design.
Lamps belong to the floor's equipment layer, independent of loose furniture.
"""
from .orientation import orient_shape, orient_record
from cadgen import build123d as bd, srgb


@orient_record
def indoor_fixture_layout(p,g):
    from .house_plan import floor_plan
    fixtures=[]
    for n in (1,2):
        for room in floor_plan(n,p).rooms:
            if room.kind=='outside':continue
            # Use known clear positions rather than the bedroom labels or beds.
            point=room.shape.representative_point();x,y=point.x,point.y
            if room.id=='hall':x,y=6000,3800  # Outside deployed attic ladder envelope.
            if room.id=='under_stairs':x,y=room.label
            if room.id=='stairs':x,y=room.shape.bounds[2]-450,room.shape.bounds[3]-50
            z=(n-1)*p.storey_height
            ceiling=z+p.storey_height-g.slab_thickness
            if room.id=='under_stairs':
                landing_y=room.shape.bounds[3]+60
                step=int((landing_y-y)//p.tread)+1
                rise=p.storey_height/p.risers
                ya=landing_y-step*p.tread
                ceiling=p.storey_height/2+step*rise-g.stair_tread_thickness+20-g.stair_stringer_depth-10-(y-ya)/p.tread*rise-35
            emitter=ceiling-(100 if room.id=='stairs' else 320)
            prefix=f'F{n}:indoor_light:{room.id}'
            fixtures.append({'id':f'indoor_F{n}_{room.id}','category':'indoor','room':room.id,'floor':n,
                'style':'wall' if room.id=='stairs' else 'pendant','group':prefix,'diffuser_label':prefix+':diffuser','mount_center_mm':[x,y,ceiling],
                'light_position_glb_m':[x/1000,emitter/1000,-y/1000],
                'target_glb_m':[x/1000,(z+650)/1000,-y/1000],
                'color_hex':'#FFE1B8','beam_angle_degrees':130,
                'visual_intensity':3.0 if room.id in ('ldk','master','bed2','bed3') else 1.2,
                'visual_range_m':4.8})
    # Attic fixture is below the low roof centre, independent of house floors.
    from .attic_geometry import A,attic_dimensions
    d=attic_dimensions(p,g);x=p.width/2;y=p.depth-1300;z=d['deck_top_z']
    fixtures.append({'id':'indoor_attic','category':'indoor','room':'attic','floor':3,
        'group':'attic:indoor_light:attic','diffuser_label':'attic:indoor_light:attic:diffuser',
        'mount_center_mm':[x,y,d['ceiling_bottom_z']], 'light_position_glb_m':[x/1000,(d['ceiling_bottom_z']-60)/1000,-y/1000],
        'target_glb_m':[x/1000,(z+300)/1000,-y/1000],'color_hex':'#FFE1B8',
        'beam_angle_degrees':130,'visual_intensity':1.5,'visual_range_m':3.0})
    return fixtures


def _lamp(f):
    from .house_geometry import cuboid
    x,y,top=f['mount_center_mm'];prefix=f['group'];attic=f['floor']==3
    if f.get('style')=='wall':
        body=cuboid((x-80,y-30,top-200,x+80,y+50,top))
        diffuser=cuboid((x-65,y-35,top-180,x+65,y-30,top-20))
        body.label=prefix+':shade';body.color=srgb('#30363B')
        diffuser.label=prefix+':diffuser';diffuser.color=srgb('#FFE7C6')
        return bd.Compound(children=[body,diffuser],label=prefix)
    bottom=top-(55 if attic else 320)
    parts=[(cuboid((x-45,y-45,top-12,x+45,y+45,top)),':mount','#30363B'),
           (cuboid((x-4,y-4,bottom+55,x+4,y+4,top-12)),':stem','#30363B')] if not attic else []
    outer=bd.Solid.make_cylinder(105,55,bd.Plane(origin=(x,y,bottom)))
    bore=bd.Solid.make_cylinder(97,55,bd.Plane(origin=(x,y,bottom)))
    parts.extend([(outer.cut(bore),':shade','#F1EEE7'),
                  (bd.Solid.make_cylinder(97,5,bd.Plane(origin=(x,y,bottom))),':diffuser','#FFE7C6')])
    children=[]
    for shape,suffix,color in parts:
        shape.label=prefix+suffix;shape.color=srgb(color);children.append(shape)
    return bd.Compound(children=children,label=prefix)


@orient_shape
def indoor_lighting_group(floor_number,p,g):
    return bd.Compound(children=[_lamp(f) for f in indoor_fixture_layout(p,g) if f['floor']==floor_number],
                       label=f'F{floor_number}:indoor_lights' if floor_number<3 else 'attic:indoor_lights')


def apply_indoor_lighting_metadata(document,p,g):
    fixtures={f['diffuser_label']:f for f in indoor_fixture_layout(p,g)}
    for node in document['nodes']:
        if node.get('name') in fixtures:node.setdefault('extras',{})['indoorLight']=fixtures[node['name']]
    document['asset'].setdefault('extras',{})['indoorLighting']={'revision':'R17','fixtures':list(fixtures.values())}


def indoor_lighting_manifest(p,g):
    return {'revision':'R17','fixtures':indoor_fixture_layout(p,g),
            'assumptions':['R17室内灯具按房间分别命名；吊灯及阁楼灯尺寸、暖白色和相对亮度为演示假设，可独立一键开关；照度、电气、防水等级和施工安装未设计。']}
