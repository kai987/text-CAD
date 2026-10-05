"""Named conceptual solids for a single Japanese 2LDK dwelling."""
from cadgen import build123d as bd
from shapely.geometry import box
from .furniture_geometry import furniture_group
from .fixture_geometry import fixture_group
from .apartment_plan import P, apartment_plan, window_specs
from .house_geometry import cuboid, named, extruded_polygon, polygons, opening_box


def assembly(p=P):
    floor,raw=apartment_plan(p)
    e,t=p.external_wall,p.internal_wall
    outer=box(0,0,p.width,p.depth).difference(box(e,e,p.width-e,p.depth-e))
    cuts=[opening_box(d.axis,d.at,d.start,d.width,e if d.a=='outside' else t,
                     0,p.clear_height if d.kind=='open' else p.door_height) for d in floor.doors]
    cuts += [opening_box(w['axis'],w['at'],w['start'],w['width'],e,
                         w['sill'],w['sill']+w['height']) for w in window_specs(p)]
    exterior=[]
    for side,profile in [('south',box(0,0,p.width,e)),('north',box(0,p.depth-e,p.width,p.depth)),
                         ('west',box(0,e,e,p.depth-e)),('east',box(p.width-e,e,p.width,p.depth-e))]:
        exterior.append(named(extruded_polygon(profile,0,p.clear_height).cut(*cuts),
                              f'F1:wall_external_{side}','external'))
    partitions=[named(extruded_polygon(poly,0,p.clear_height).cut(*cuts),
                      f'F1:wall_partition_{i:02d}','internal')
                for i,poly in enumerate(polygons(raw.difference(outer)),1)]
    doors=[]
    for door in floor.doors:
        if door.kind=='open':continue
        doors.append(named(opening_box(door.axis,door.at,door.start+10,door.width-20,34,
                                       10,p.door_height-10),f'F1:{door.id}_door_{door.kind}','door'))
    windows=[]
    for w in window_specs(p):
        x,y,z,width,height=w['start'],w['at'],w['sill'],w['width'],w['height']
        frame=45; label=f"F1:{w['id']}"
        bounds=[(x,y-35,z,x+width,y+35,z+frame),
                (x,y-35,z+height-frame,x+width,y+35,z+height),
                (x,y-35,z+frame,x+frame,y+35,z+height-frame),
                (x+width-frame,y-35,z+frame,x+width,y+35,z+height-frame),
                (x+width/2-frame/2,y-35,z+frame,x+width/2+frame/2,y+35,z+height-frame)]
        parts=[cuboid(b,f'{label}:frame_{i}','frame') for i,b in enumerate(bounds,1)]
        for pane,a,b in [(1,x+frame,x+width/2-frame/2),(2,x+width/2+frame/2,x+width-frame)]:
            parts.append(named(cuboid((a,y-5,z+frame,b,y+5,z+height-frame)),
                               f'{label}:glass_{pane}','glass',.45))
        windows.append(bd.Compound(children=parts,label=label))
    storage=[]
    for i,(name,bounds) in enumerate(floor.fixtures,1):
        x1,y1,x2,y2=bounds
        if name in ('靴収納','収納','収納棚'):
            storage.append(cuboid((x1,y1,0,x2,y2,1800 if name=='靴収納' else p.cabinet_height),
                                   f'F1:storage_{i:02d}','storage'))
    groups=[cuboid((0,0,-p.slab_thickness,p.width,p.depth,0),'F1:floor_slab','slab'),
            bd.Compound(children=exterior,label='F1:external_walls'),
            bd.Compound(children=partitions,label='F1:partition_walls'),
            bd.Compound(children=doors,label='F1:doors'),bd.Compound(children=windows,label='F1:windows'),
            bd.Compound(children=storage,label='F1:storage_fixtures'),
            fixture_group(floor,p,'apartment'), furniture_group(floor,'apartment',p)]
    balcony=[cuboid((0,-p.balcony_depth,-p.slab_thickness,p.width,0,0),'balcony:slab','slab'),
             cuboid((0,-p.balcony_depth,0,p.width,-p.balcony_depth+100,p.balcony_guard_height),
                    'balcony:south_guard','external'),
             cuboid((0,-p.balcony_depth+100,0,100,0,p.balcony_guard_height),'balcony:west_guard','external'),
             cuboid((p.width-100,-p.balcony_depth+100,0,p.width,0,p.balcony_guard_height),
                    'balcony:east_guard','external')]
    ceiling=cuboid((0,0,p.clear_height,p.width,p.depth,p.clear_height+p.slab_thickness),
                   'ceiling:slab','internal')
    return bd.Compound(children=[bd.Compound(children=groups,label='F1'),
                                 bd.Compound(children=balcony,label='balcony'),
                                 bd.Compound(children=[ceiling],label='ceiling')],label='apartment_2ldk')
