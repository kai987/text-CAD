"""Original R02 Skytree appearance detail in millimetres.

Published heights and the referenced triangular/circular controls guide this
concept. The interpolation, member layout, deck radii, gallery turn count,
route, connections and light positions are modelling assumptions, not measured
original CAD or structural design. The gallery is a continuous ramp, not stairs.
Only the RC shinbashira is called a central column; the upper guide frame is a
separate schematic element. All primitives share the CAD/drawing specification.
"""
from __future__ import annotations

from math import cos, sin, pi, hypot

WHITE = '#E3E9E7'
SHADOW = '#A6B6C0'
STEEL = '#657B89'
GLASS = '#7295A8'
WARM = '#D4F6FF'


def profile_radius(profile, z):
    """Monotone Hermite interpolation through the recorded radius controls."""
    if z <= profile[0][0]:return profile[0][1]
    if z >= profile[-1][0]:return profile[-1][1]
    slopes=[(b[1]-a[1])/(b[0]-a[0]) for a,b in zip(profile,profile[1:])]
    d=[slopes[0]]+[0. if a*b<=0 else 2*a*b/(a+b) for a,b in zip(slopes,slopes[1:])]+[slopes[-1]]
    for i,((za,ra),(zb,rb)) in enumerate(zip(profile,profile[1:])):
        if za<=z<=zb:
            h=zb-za;t=(z-za)/h
            return ((2*t**3-3*t*t+1)*ra+(t**3-2*t*t+t)*h*d[i]
                    +(-2*t**3+3*t*t)*rb+(t**3-t*t)*h*d[i+1])
    raise AssertionError('Skytree profile coverage failure')


def _spec(group,name,kind,color,role=None,**data):
    return {'group':group,'name':f'{group}:{name}','kind':kind,'color':color,
            **({'role':role} if role else {}),**data}


def _box(group,name,bounds,color,role=None,**data):
    return _spec(group,name,'box',color,role,bounds=list(bounds),**data)


def _beam(group,name,a,b,radius,color,role=None,**data):
    return _spec(group,name,'beam',color,role,start=list(a),end=list(b),radius=radius,**data)


def _section(z,points):return {'z':z,'points':[list(v) for v in points]}


def _loft(group,name,sections,color,role=None,**data):
    return _spec(group,name,'loft',color,role,sections=sections,**data)


def _loft3d(group,name,sections,color,role=None,**data):
    return _spec(group,name,'loft3d',color,role,sections=sections,**data)


def _circle(r,n=16,centre=(0,0)):
    return [[centre[0]+r*cos(2*pi*i/n),centre[1]+r*sin(2*pi*i/n)] for i in range(n)]


def _sector(inner,outer,a,b):
    return [[inner*cos(a),inner*sin(a)],[outer*cos(a),outer*sin(a)],
            [outer*cos(b),outer*sin(b)],[inner*cos(b),inner*sin(b)]]


def _annulus(group,name,inner,outer,z0,z1,color,role,n=24,**data):
    return [_loft(group,f'{name}_{i:02d}',[_section(z0,_sector(inner,outer,2*pi*i/n,2*pi*(i+1)/n)),
                                          _section(z1,_sector(inner,outer,2*pi*i/n,2*pi*(i+1)/n))],
                  color,role,**data) for i in range(n)]


def _frame_stations(p):
    # Mid-stations make the control curve readable; loft chunks share their
    # actual end sections, so neither primary chords nor secondary chords jump.
    controls=[v[0] for v in p['profile']]
    return sorted(set(controls+[.5*(a+b) for a,b in zip(controls,controls[1:])]
                      +[9000.,12000.,18000.,30000.,45000.,100000.,315000.,333000.,340000.,345000.,
                        350000.,375000.,443000.,445000.,450000.,452500.,495000.]))


def _chord_radius(node,z):
    return max(420.,1450.-z*.0020) if node%8==0 else max(180.,560.-z*.00065)


def _frame_point(p,ring,node,z):
    """Point on the actual piecewise-linear chord, also used for attachments."""
    stations=_frame_stations(p)
    for za,zb in zip(stations,stations[1:]):
        if za<=z<=zb:
            t=(z-za)/(zb-za);a,b=ring(za)[node],ring(zb)[node]
            return [a[k]*(1-t)+b[k]*t for k in range(2)]+[z]
    raise ValueError('Frame attachment height is outside the body.')


def _body(p,ring):
    parts=[];stations=_frame_stations(p)
    for node in range(24):
        levels=stations if node%8==0 else [z for z in stations if z>=45000]
        for chunk,start in enumerate(range(0,len(levels)-1,7),1):
            subset=levels[start:start+8]
            if len(subset)<2:continue
            parts.append(_loft('structure',f'primary_leg_{node//8+1}_{chunk:02d}' if node%8==0
                               else f'longitudinal_{node:02d}_{chunk:02d}',
                               [_section(z,_circle(_chord_radius(node,z),8,ring(z)[node])) for z in subset],
                               WHITE,'primary_leg' if node%8==0 else 'secondary_chord',
                               node=node,section_assumption='octagonal solid appearance member'))
    # Adjacent rings and alternating diagonal triangles remain open; no solid
    # envelope and no ground-level perimeter of twenty-four artificial legs.
    lattice=[z for z in stations if z>=45000]
    for level,z in enumerate(lattice):
        if level%2==0 or z in (315000,350000,445000,450000,495000):
            points=ring(z)
            for node in range(24):
                parts.append(_beam('structure',f'ring_{level:02d}_{node:02d}',(*points[node],z),(*points[(node+1)%24],z),
                                   max(105,260-z*.00027),WHITE,'body_ring'))
    for level,(za,zb) in enumerate(zip(lattice,lattice[1:])):
        a,b=ring(za),ring(zb)
        for node in range(level%2,24,2):
            parts.append(_beam('structure',f'lattice_{level:02d}_{node:02d}',(*a[node],za),(*b[(node+1)%24],zb),
                               max(90,220-za*.00022),SHADOW,'body_brace'))
    # Three arch-shaped transverse frames join the real main legs to the
    # 45 m secondary perimeter. Endpoints coincide with chord centre lines.
    for side in range(3):
        line=[]
        for k in range(9):
            t=k/8;z=12000+33000*sin(pi*t)
            if k in (0,8):z=12000.
            points=ring(z);a,b=points[side*8],points[((side+1)*8)%24]
            if k in (0,8):point=_frame_point(p,ring,(side*8+k)%24,z)
            elif k==4:point=[*ring(45000)[side*8+4],45000.]
            else:point=[a[j]*(1-t)+b[j]*t for j in range(2)]+[z]
            line.append(point)
        for k,(a,b) in enumerate(zip(line,line[1:])):
            parts.append(_beam('structure',f'lower_arch_{side}_{k}',a,b,480,WHITE,'lower_arch'))
        for k in (4,):
            x,y,z=line[k]
            parts.append(_box('structure',f'lower_arch_node_{side}_{k}',(x-630,y-630,z-600,x+630,y+630,z+600),
                              WHITE,'connection_detail',detail_level='micro'))
    return parts


def _base(p,ring):
    parts=[_loft('base','ground_plaza',[_section(-2500,_circle(52000,48)),_section(0,_circle(52000,48))],
                 '#D2CDC3','ground')]
    for i,(x,y) in enumerate(ring(0)[::8],1):
        parts.append(_box('base',f'footing_{i}',(x-2700,y-2700,-1500,x+2700,y+2700,1400),'#ADB3B5','foundation_placeholder'))
        parts.append(_box('structure',f'leg_shoe_{i}',(x-2100,y-2100,1100,x+2100,y+2100,1600),STEEL,
                          'connection_detail',detail_level='micro'))
    parts.append(_box('base','entrance_floor',(-10000,-18500,0,10000,-8500,250),'#B5B6B1','entrance_floor'))
    parts.append(_box('base','entrance_roof',(-10500,-19000,5100,10500,-8000,5400),WHITE,'entrance_roof'))
    for side,x in enumerate((-10000,9700)):
        parts.append(_box('base',f'entrance_sidewall_{side}',(x,-18500,250,x+300,-8500,5100),WHITE,'entrance_wall'))
    parts.append(_box('base','entrance_rear',(-10000,-8800,250,10000,-8500,5100),WHITE,'entrance_wall'))
    for i,(a,b) in enumerate(((-9700,-3900),(-3700,-150),(150,3700),(3900,9700))):
        parts.append(_box('base',f'entrance_glazing_{i}',(a,-18500,400,b,-18400,4950),GLASS,'glazing',finish='glass'))
    for i,x in enumerate((-9700,-3800,0,3800,9700)):
        parts.append(_box('base',f'entrance_mullion_{i}',(x-75,-18550,250,x+75,-18350,5100),STEEL,'window_frame'))
    parts.append(_box('base','entrance_canopy',(-6500,-21500,4800,6500,-18500,5000),WHITE,'entrance_canopy'))
    for i,x in enumerate((-3600,3600)):
        parts.append(_box('base',f'entrance_door_handle_{i}',(x-35,-18620,1700,x+35,-18500,2600),STEEL,'entrance_detail'))
    for i in range(3):
        parts.append(_box('base',f'entrance_step_{i}',(-7000,-23000+500*i,80*i,7000,-22500+500*i,80*(i+1)),
                          '#B5B6B1','entrance_step'))
    for i in range(6):
        a=2*pi*i/6;x,y=45000*cos(a),45000*sin(a)
        parts.append(_box('base',f'plaza_light_housing_{i}',(x-230,y-230,0,x+230,y+230,1200),STEEL,'light_housing'))
        parts.append(_box('base',f'plaza_light_lens_{i}',(x-235,y-235,1200,x+235,y+235,1460),WARM,'light_lens'))
    return parts


def _core(p):
    parts=[];detail=p.get('detail',{});height=detail.get('shinbashira_height_mm',375000)
    radius=detail.get('shinbashira_diameter_mm',8000)/2
    for index,(za,zb,thickness) in enumerate(((0,100000,detail.get('shinbashira_wall_lower_mm',400)),
                                             (100000,height,detail.get('shinbashira_wall_upper_mm',600)))):
        parts.extend(_annulus('core',f'shinbashira_wall_{index}',radius-thickness,radius,za,zb,'#8D9EA5',
                              'shinbashira_wall',n=24,wall_thickness_mm=thickness))
    # Above the RC column, clearly independent schematic elevator guides.
    for i,(x,y) in enumerate(((-2400,-2400),(2400,-2400),(2400,2400),(-2400,2400))):
        parts.append(_box('core',f'upper_elevator_guide_{i}',(x-120,y-120,height,x+120,y+120,452500),
                          STEEL,'elevator_guide'))
    for i,z in enumerate((390000,415000,440000,450000)):
        points=[(-2400,-2400),(2400,-2400),(2400,2400),(-2400,2400)]
        for side in range(4):
            parts.append(_beam('core',f'upper_elevator_tie_{i}_{side}',(*points[side],z),(*points[(side+1)%4],z),90,
                               STEEL,'elevator_guide'))
    return parts


def _tembo_deck(p,ring):
    parts=[];deck=next(v for v in p['deck_specs'] if v['id']=='tembo_deck')
    radius=deck['radius_mm'];bottom=deck['bottom_mm'];glass=deck['glass_bottom_mm'];top=deck['top_mm'];n=24
    floors=p.get('detail',{}).get('tembo_floors_mm',[340000,345000,350000])
    facade_top=top-1000
    def outer(z):return radius*(1-.09*(z-glass)/(facade_top-glass))
    for i in range(n):
        a,b=2*pi*i/n,2*pi*(i+1)/n
        parts.append(_loft('decks',f'tembo_deck_apron_{i:02d}',
                           [_section(bottom,_sector(radius*.66-220,radius*.66,a,b)),
                            _section(glass,_sector(radius-220,radius,a,b))],WHITE,'deck_apron'))
    for floor,z in enumerate(floors):
        r=outer(z)
        parts.extend(_annulus('decks',f'tembo_deck_floor_{floor+1}',6000,r-220,z-300,z,'#DDDCD4','deck_floor',n=n,
                              floor_level_mm=z))
        parts.extend(_annulus('decks',f'tembo_deck_belt_{floor+1}',r-220,r,z-300,z+300,WHITE,'floor_belt',n=n))
    for zone,(za,zb) in enumerate(zip([z+300 for z in floors],[floors[1]-300,floors[2]-300,facade_top])):
        for i in range(n):
            a,b=2*pi*(i+.035)/n,2*pi*(i+.965)/n
            parts.append(_loft('decks',f'tembo_deck_glazing_{zone}_{i:02d}',
                               [_section(za,_sector(outer(za)-90,outer(za),a,b)),
                                _section(zb,_sector(outer(zb)-90,outer(zb),a,b))],
                               GLASS,'glazing',finish='glass',thickness_mm=90))
    for i in range(n):
        a=2*pi*i/n
        parts.append(_beam('decks',f'tembo_deck_mullion_{i:02d}',
                           (outer(glass)*cos(a),outer(glass)*sin(a),glass),
                           (outer(facade_top)*cos(a),outer(facade_top)*sin(a),facade_top),
                           95,WHITE,'window_frame'))
    # Ring roof pieces keep the central void open instead of an opaque disk.
    parts.extend(_annulus('decks','tembo_deck_roof',6000,radius*.94,top-350,top,WHITE,'deck_roof',n=n))
    parts.extend(_annulus('decks','tembo_deck_roof_edge',radius*.91-150,radius*.94,facade_top,top-350,WHITE,'roof_fascia',n=n))
    for node in range(0,24,2):
        anchor=_frame_point(p,ring,node,bottom+100)
        a=pi/2+2*pi*node/24;target=[radius*.66*cos(a),radius*.66*sin(a),bottom+100]
        parts.append(_beam('decks',f'tembo_deck_apron_connector_{node:02d}',anchor,target,180,WHITE,'deck_connector',
                           attachment_points=[anchor,target]))
    return parts


def _gallery_section(theta,z,inner,outer,z0,z1):
    return [[inner*cos(theta),inner*sin(theta),z+z0],[outer*cos(theta),outer*sin(theta),z+z0],
            [outer*cos(theta),outer*sin(theta),z+z1],[inner*cos(theta),inner*sin(theta),z+z1]]


def _tembo_galleria(p,ring):
    parts=[];detail=p.get('detail',{});start=detail.get('galleria_start_mm',445000);end=detail.get('galleria_end_mm',450000)
    hall_top=next(v['top_mm'] for v in p['deck_specs'] if v['id']=='tembo_galleria')
    segments=detail.get('galleria_segments',32);centre=detail.get('galleria_centre_radius_mm',12850.)
    width=detail.get('galleria_width_mm',1800.);height=detail.get('galleria_side_height_mm',2200.)
    thick=detail.get('galleria_floor_thickness_mm',250.);glass_thick=detail.get('galleria_glass_thickness_mm',80.)
    rise=detail.get('galleria_arch_rise_mm',900.);panels=detail.get('galleria_arch_panels',4)
    inner=centre-width/2;outer=centre+width/2
    arch=[(centre+width/2*cos(pi-j*pi/panels),height+rise*sin(pi-j*pi/panels)) for j in range(panels+1)]
    arch_outer=[(centre+(r-centre)*(1+glass_thick/(width/2)),height+(z-height)*(1+glass_thick/rise)) for r,z in arch]
    # A one-turn original route, not a claim about the original 110 m route.
    for i in range(segments):
        a,b=2*pi*i/segments,2*pi*(i+1)/segments;za=start+(end-start)*i/segments;zb=start+(end-start)*(i+1)/segments
        for suffix,ri,ro,z0,z1,color,role in (
            ('ramp',inner,outer,-thick,0,'#D6DBD8','galleria_ramp'),
            ('inner_glazing',inner-glass_thick,inner,0,height,GLASS,'glazing'),
            ('outer_glazing',outer,outer+glass_thick,0,height,GLASS,'glazing')):
            # Two complete side-entry bays connect the radial pads to the
            # gallery. A closed inner glass wall would seal the route.
            if suffix=='inner_glazing' and i in (0,segments-1):continue
            parts.append(_loft3d('decks',f'tembo_galleria_{suffix}_{i:02d}',
                                 [_gallery_section(a,za,ri,ro,z0,z1),_gallery_section(b,zb,ri,ro,z0,z1)],color,role,
                                 **({'finish':'glass','thickness_mm':glass_thick} if role=='glazing' else {}),
                                 segment=i,route_start=[centre*cos(a),centre*sin(a),za],
                                 route_end=[centre*cos(b),centre*sin(b),zb],
                                 route_assumption='one illustrative turn; radius, route and tube section unmeasured'))
        for panel in range(panels):
            profile=[arch[panel],arch[panel+1],arch_outer[panel+1],arch_outer[panel]]
            def section(theta,z):
                return [[r*cos(theta),r*sin(theta),z+height] for r,height in profile]
            parts.append(_loft3d('decks',f'tembo_galleria_arch_glazing_{i:02d}_{panel}',
                                 [section(a,za),section(b,zb)],GLASS,'glazing',finish='glass',thickness_mm=glass_thick,
                                 gallery_surface='arched_roof',segment=i,arch_panel=panel))
    for i in range(0,segments+1,2):
        a=2*pi*i/segments;z=start+(end-start)*i/segments
        for side,r in enumerate((inner-glass_thick/2,outer+glass_thick/2)):
            parts.append(_beam('decks',f'tembo_galleria_rib_{i:02d}_{side}',
                               (r*cos(a),r*sin(a),z),(r*cos(a),r*sin(a),z+height),55,WHITE,'galleria_rib'))
        for panel in range(panels):
            aa,bb=arch[panel],arch[panel+1]
            parts.append(_beam('decks',f'tembo_galleria_rib_{i:02d}_arch_{panel}',
                               (aa[0]*cos(a),aa[0]*sin(a),z+aa[1]),
                               (bb[0]*cos(a),bb[0]*sin(a),z+bb[1]),55,WHITE,'galleria_rib'))
    for floor,z in enumerate((start,end)):
        parts.extend(_annulus('decks',f'tembo_galleria_landing_floor_{floor}',5000,11250,z-thick,z,'#D6DBD8','deck_floor',n=24,
                              floor_level_mm=z))
        # Radial access pad bridges the inner observation floor to both ramp
        # ends. Its shared top edge is the ramp endpoint, with a true centre void.
        parts.append(_loft('decks',f'tembo_galleria_access_pad_{floor}',
                           [_section(z-thick,_sector(11100,outer+glass_thick,-.09,.09)),
                            _section(z,_sector(11100,outer+glass_thick,-.09,.09))],
                           '#D6DBD8','galleria_access',floor_level_mm=z))
    for i in range(24):
        a,b=2*pi*(i+.035)/24,2*pi*(i+.965)/24
        zones=[(start+300,hall_top-350)] if i not in (0,23) else [(start+height,end),(end+height,hall_top-350)]
        for zone,(za,zb) in enumerate(zones):
            parts.append(_loft('decks',f'tembo_galleria_inner_hall_glazing_{i:02d}_{zone}',
                               [_section(za,_sector(11170,11250,a,b)),_section(zb,_sector(11170,11250,a,b))],
                               GLASS,'glazing',finish='glass',thickness_mm=80,entrance_bay=i in (0,23)))
    parts.extend(_annulus('decks','tembo_galleria_inner_hall_roof',5000,11350,hall_top-350,hall_top,WHITE,'deck_roof',n=24))
    # Twelve radial supports start at actual lattice chord centres and terminate
    # inside the ramp slab. They do not float below the glass tube.
    for i in range(0,segments,4):
        a=2*pi*i/segments;z=start+(end-start)*i/segments-thick/2
        # Frame node0 points north; route angle0 points east, hence -6 offset.
        node=(i*24//segments-6)%24;anchor=_frame_point(p,ring,node,z)
        target=[centre*cos(a),centre*sin(a),z]
        parts.append(_beam('decks',f'tembo_galleria_radial_support_{i:02d}',anchor,target,105,WHITE,'galleria_support',
                           attachment_points=[anchor,target],target_segment=i,frame_node=node))
    return parts


def _antenna(p,ring):
    parts=[];stations=[(495000,3400),(510000,3100),(525000,2800),(540000,2400),(555000,2050),
                      (570000,1700),(585000,1350),(600000,1000),(612000,760),(624000,540),(634000,330)]
    for i,((za,ra),(zb,rb)) in enumerate(zip(stations,stations[1:])):
        parts.append(_loft('antenna',f'gain_tower_{i:02d}',[_section(za,_circle(ra,16)),_section(zb,_circle(rb,16))],
                           WHITE,'gain_tower'))
        for j in range(4):
            a=j*pi/2
            parts.append(_beam('antenna',f'aerial_{i:02d}_{j}',((ra+120)*cos(a),(ra+120)*sin(a),za+600),
                               ((rb+120)*cos(a),(rb+120)*sin(a),zb-600),100,SHADOW,'aerial'))
    for i,z in enumerate((505000,530000,555000,580000,605000,625000)):
        r=_antenna_radius(stations,z)
        parts.extend(_annulus('antenna',f'maintenance_ring_{i}',max(0,r-100),r+650,z-130,z+130,WHITE,
                              'maintenance_ring',n=12))
        for j in range(0,12,3):
            a=2*pi*j/12
            parts.append(_beam('antenna',f'maintenance_guard_{i}_{j}',((r+550)*cos(a),(r+550)*sin(a),z+130),
                               ((r+550)*cos(a),(r+550)*sin(a),z+950),45,STEEL,'maintenance_guard'))
    # This flange really reaches from the body head to the gain-tower base.
    parts.extend(_annulus('antenna','gain_tower_base_flange',2900,6300,494750,495000,WHITE,'antenna_flange',n=24))
    for i,z in enumerate((90000,180000,270000,350000,375000,450000,495000,530000,570000,610000,632500)):
        if z<495000:
            anchor=_frame_point(p,ring,0,z);length=hypot(anchor[0],anchor[1]);u=[anchor[0]/length,anchor[1]/length]
            lens=[anchor[0]+u[0]*900,anchor[1]+u[1]*900,z]
        else:
            r=_antenna_radius(stations,z);anchor=[r-40,0,z];lens=[r+300,0,z]
        parts.append(_beam('antenna' if z>=495000 else 'structure',f'obstruction_light_arm_{i}',anchor,lens,70,
                           STEEL,'light_housing'))
        x,y,z=lens
        parts.append(_box('antenna' if z>=495000 else 'structure',f'obstruction_light_lens_{i}',
                          (x-150,y-150,z-150,x+150,y+150,z+150),'#F64B42','obstruction_light_lens'))
    return parts


def _antenna_radius(stations,z):
    for (za,ra),(zb,rb) in zip(stations,stations[1:]):
        if za<=z<=zb:return ra+(rb-ra)*(z-za)/(zb-za)
    raise ValueError('Antenna height outside station coverage')


def component_specs(p,ring):
    """Exact primitives for the shared Skytree CAD, drawing and GLB exporters."""
    return (_base(p,ring)+_body(p,ring)+_core(p)+_tembo_deck(p,ring)
            +_tembo_galleria(p,ring)+_antenna(p,ring))
