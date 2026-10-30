"""Reference-informed R04 Tokyo Tower appearance detail, in mm; not an engineered copy.

Only published tower/deck heights, the two Main Deck levels and the existence
of the approximately 600-step outdoor route are references. The member layout,
floor heights other than explicitly cited construction GL levels, connections, glazing, route and light
positions below are explicitly adjustable modelling assumptions.

All returned primitives use the shared box/beam/loft contract. Thus CAD,
editable drawings and the web model retain one source of geometry.
"""
from __future__ import annotations

from math import cos, sin, pi

ORANGE = '#E34C25'
WHITE = '#F4F0E7'
STEEL = '#6D7880'
GLASS = '#658C9E'
WARM = '#FFE0A3'


def profile_radius(profile, z):
    """Monotone cubic Hermite interpolation through the assumed leg controls."""
    if z <= profile[0][0]:
        return profile[0][1]
    if z >= profile[-1][0]:
        return profile[-1][1]
    slopes = [(b[1] - a[1]) / (b[0] - a[0]) for a, b in zip(profile, profile[1:])]
    derivatives = [slopes[0]]
    for left, right in zip(slopes, slopes[1:]):
        derivatives.append(0. if left * right <= 0 else 2 * left * right / (left + right))
    derivatives.append(slopes[-1])
    for index, ((z0, r0), (z1, r1)) in enumerate(zip(profile, profile[1:])):
        if z0 <= z <= z1:
            h = z1 - z0
            t = (z - z0) / h
            return ((2*t**3 - 3*t**2 + 1)*r0 + (t**3 - 2*t**2 + t)*h*derivatives[index]
                    + (-2*t**3 + 3*t**2)*r1 + (t**3 - t**2)*h*derivatives[index + 1])
    raise AssertionError('Tokyo leg profile is not covered.')


def _box(group, name, bounds, color, role=None, **metadata):
    return {'group': group, 'name': f'{group}:{name}', 'kind': 'box',
            'bounds': list(bounds), 'color': color, **({'role': role} if role else {}), **metadata}


def _beam(group, name, a, b, radius, color, role=None, **metadata):
    return {'group': group, 'name': f'{group}:{name}', 'kind': 'beam',
            'start': list(a), 'end': list(b), 'radius': radius, 'color': color,
            **({'role': role} if role else {}), **metadata}


def _loft(group, name, sections, color, role=None, **metadata):
    return {'group': group, 'name': f'{group}:{name}', 'kind': 'loft',
            'sections': sections, 'color': color, **({'role': role} if role else {}), **metadata}


def _section(z, points):
    return {'z': z, 'points': [list(point) for point in points]}


def _square(r, center=(0, 0)):
    x, y = center
    return [[x-r, y-r], [x+r, y-r], [x+r, y+r], [x-r, y+r]]


def _octagon(half, chamfer=.18):
    c = half * chamfer
    return [[-half+c,-half], [half-c,-half], [half,-half+c], [half,half-c],
            [half-c,half], [-half+c,half], [-half,half-c], [-half,-half+c]]


def _circle(radius, count=16):
    return [[radius*cos(2*pi*i/count), radius*sin(2*pi*i/count)] for i in range(count)]


def _rect_chord(name, a, b, half, color):
    return _loft('structure', name, [_section(a[2], _square(half, a[:2])),
                                   _section(b[2], _square(half, b[:2]))], color,
                 'primary_chord', section_assumption='solid rectangular appearance member')


def _edge_panel(group, name, a, b, z0, z1, thickness, color, upper_scale=1., role=None):
    """Thin facade strip, not an opaque full deck volume."""
    dx, dy = b[0]-a[0], b[1]-a[1]
    length = (dx*dx + dy*dy)**.5
    nx, ny = -dy/length*thickness, dx/length*thickness
    low = [a, b, [b[0]+nx,b[1]+ny], [a[0]+nx,a[1]+ny]]
    high = [[x*upper_scale,y*upper_scale] for x,y in low]
    return _loft(group, name, [_section(z0,low), _section(z1,high)], color, role,
                 **({'finish':'glass'} if role == 'glazing' else {}))


def _floor_with_stair_opening(name, half, z, color):
    """Six non-overlapping slabs form a chamfered deck with a real stair void."""
    c = half*.18
    x1,x2,y1,y2 = 4700., 9300., -8000., 1800.
    pieces = [
        _loft('decks',name+'_south',[_section(z-300,[[-half+c,-half],[half-c,-half],[half,-half+c],[-half,-half+c]]),
                                  _section(z,[[-half+c,-half],[half-c,-half],[half,-half+c],[-half,-half+c]])],color,'deck_floor'),
        _loft('decks',name+'_north',[_section(z-300,[[-half,half-c],[half,half-c],[half-c,half],[-half+c,half]]),
                                  _section(z,[[-half,half-c],[half,half-c],[half-c,half],[-half+c,half]])],color,'deck_floor'),
    ]
    for suffix,bounds in [('west',(-half,-half+c,z-300,x1,half-c,z)),
                          ('east',(x2,-half+c,z-300,half,half-c,z)),
                          ('south_middle',(x1,-half+c,z-300,x2,y1,z)),
                          ('north_middle',(x1,y2,z-300,x2,half-c,z))]:
        pieces.append(_box('decks',name+'_'+suffix,bounds,color,'deck_floor'))
    return pieces


def _lower_frame(p, ring, paint):
    parts=[]
    levels=p['detail']['leg_stations_mm']
    corners=[(-1,-1),(1,-1),(1,1),(-1,1)]
    for leg,(sx,sy) in enumerate(corners,1):
        for index,(za,zb) in enumerate(zip(levels,levels[1:]),1):
            ra=ring(za)[0][0]*-1;rb=ring(zb)[0][0]*-1
            cage_a=max(950,1800-za*.010);cage_b=max(950,1800-zb*.010)
            a=_square(cage_a,(sx*ra,sy*ra));b=_square(cage_b,(sx*rb,sy*rb))
            color=paint((za+zb)/2)
            for chord in range(4):
                parts.append(_rect_chord(f'leg_{leg:02d}_chord_{chord:02d}_{index:02d}',
                                        (*a[chord],za),(*b[chord],zb),max(180,360-za*.0015),color))
            # Four-face lacing expresses a built-up leg, rather than two open
            # decorative rails. Exact bar sizes and pitch remain assumptions.
            for face in range(4):
                nxt=(face+1)%4
                parts.append(_beam('structure',f'leg_{leg:02d}_web_{face}_{index:02d}',
                                   (*a[face],za),(*b[nxt],zb),135,color,'leg_brace'))
                parts.append(_beam('structure',f'leg_{leg:02d}_tie_{face}_{index:02d}',
                                   (*b[face],zb),(*b[nxt],zb),155,color,'leg_tie'))
        r=-ring(levels[-1])[0][0]
        parts.append(_box('structure',f'leg_{leg:02d}_head_plate',
                          (sx*r-1300,sy*r-1300,levels[-1]-100,
                           sx*r+1300,sy*r+1300,levels[-1]+100),ORANGE,
                          'connection_detail',detail_level='micro'))
        x,y=sx*40000,sy*40000
        parts.append(_box('base',f'footing_{leg:02d}',(x-2600,y-2600,-1500,x+2600,y+2600,1100),'#A8A7A0','foundation_placeholder'))
        parts.append(_box('structure',f'leg_{leg:02d}_shoe_plate',(x-2200,y-2200,1100,x+2200,y+2200,1300),STEEL,'connection_detail',detail_level='micro'))
    def cage_outer_radius(z):
        # Endpoints use the straight native chord interpolation, not the smooth
        # envelope control curve; otherwise new panels would float in the cage.
        i=next(i for i,(za,zb) in enumerate(zip(levels,levels[1:])) if za<=z<=zb)
        za,zb=levels[i:i+2];t=(z-za)/(zb-za)
        ra,rb=-ring(za)[0][0],-ring(zb)[0][0]
        ca,cb=max(950,1800-za*.010),max(950,1800-zb*.010)
        return (ra+ca)*(1-t)+(rb+cb)*t
    # The contractor's p86 elevation puts the arch crown at H3 / GL+40m.
    # Its exact curve, rib offset and all intermediate points are digitised
    # modelling approximations. The previous floating 26–67m arch was wrong.
    crown=p['detail']['arch_crown_mm'];foot=1300.
    for side in range(4):
        normal=(0,1) if side in (0,2) else (1,0)
        def side_point(x,z):
            r=-ring(z)[0][0]
            return ([x,-r,z] if side==0 else [r,x,z] if side==1 else
                    [-x,r,z] if side==2 else [-r,-x,z])
        span=40000.-1800.
        path=[]
        for i in range(17):
            q=(i-8)/8
            path.append(side_point(q*span,foot+(crown-foot)*(1-q*q)))
        for lane,offset in enumerate((-650,650)):
            line=[[x+normal[0]*offset,y+normal[1]*offset,z] for x,y,z in path]
            for i,(a,b) in enumerate(zip(line,line[1:])):
                parts.append(_beam('structure',f'lower_arch_{side}_{lane}_{i}',a,b,300,ORANGE,'open_cross_frame'))
            for end,point in enumerate((line[0],line[-1])):
                z=point[2]
                interval=next(i for i,(a,b) in enumerate(zip(levels,levels[1:])) if a<=z<=b)
                za,zb=levels[interval],levels[interval+1];t=(z-za)/(zb-za)
                ra,rb=-ring(za)[0][0],-ring(zb)[0][0]
                ca,cb=max(950,1800-za*.010),max(950,1800-zb*.010)
                candidates=[]
                for leg,(sx,sy) in enumerate(corners,1):
                    a,b=_square(ca,(sx*ra,sy*ra)),_square(cb,(sx*rb,sy*rb))
                    for chord in range(4):
                        target=[a[chord][k]*(1-t)+b[chord][k]*t for k in range(2)]+[z]
                        candidates.append((sum((target[k]-point[k])**2 for k in range(3)),leg,chord,target))
                _,leg,chord,target=min(candidates,key=lambda value:value[0])
                dx,dy=target[0]-point[0],target[1]-point[1];length=(dx*dx+dy*dy)**.5
                ux,uy=dx/length,dy/length;nx,ny=-uy*180,ux*180
                a=[point[0]-ux*180,point[1]-uy*180];b=[target[0]+ux*180,target[1]+uy*180]
                outline=[[a[0]+nx,a[1]+ny],[b[0]+nx,b[1]+ny],[b[0]-nx,b[1]-ny],[a[0]-nx,a[1]-ny]]
                parts.append(_loft('structure',f'lower_arch_anchor_{side}_{lane}_{end}',
                                   [_section(z-100,outline),_section(z+100,outline)],ORANGE,
                                   'connection_detail',detail_level='micro',
                                   source_member=f'structure:lower_arch_{side}_{lane}_{0 if end==0 else 15}',
                                   target_member=f'structure:leg_{leg:02d}_chord_{chord:02d}_{interval+1:02d}',
                                   attachment_points=[list(point),target]))
        for i,point in enumerate(path):
            a=[point[0]-normal[0]*650,point[1]-normal[1]*650,point[2]]
            b=[point[0]+normal[0]*650,point[1]+normal[1]*650,point[2]]
            parts.append(_beam('structure',f'lower_arch_web_{side}_{i}',a,b,100,ORANGE,'open_cross_frame'))
        # Infill only outside the arch opening; radial webs join the inner rib
        # to the sloping outer legs. They must never cross Foot Town's entrance.
        for half_sign in (-1,1):
            inner=[];outer=[]
            for i in range(1,9):
                q=half_sign*(1-i/9);z=foot+(crown-foot)*(1-q*q)
                inner.append(side_point(q*span,z))
                r=cage_outer_radius(z)
                outer.append(([half_sign*r,-r,z] if side==0 else [r,half_sign*r,z] if side==1 else
                              [-half_sign*r,r,z] if side==2 else [-r,-half_sign*r,z]))
            for i,(a,b) in enumerate(zip(inner,outer)):
                parts.append(_beam('structure',f'arch_spandrel_tie_{side}_{half_sign}_{i}',a,b,125,ORANGE,'arch_spandrel'))
                if i:
                    parts.append(_beam('structure',f'arch_spandrel_diagonal_{side}_{half_sign}_{i}',outer[i-1],a,105,ORANGE,'arch_spandrel'))
        # Continuous lower shaft above H3: four panels across, X braces with a
        # hierarchy of primary, secondary and vertical members. No random webs.
        bay_levels=p['detail']['lower_belt_levels_mm']
        for band,(za,zb) in enumerate(zip(bay_levels,bay_levels[1:])):
            ra,rb=cage_outer_radius(za),cage_outer_radius(zb)
            def outer_point(q,r,z):
                return ([q*r,-r,z] if side==0 else [r,q*r,z] if side==1 else
                        [-q*r,r,z] if side==2 else [-r,-q*r,z])
            aa=[outer_point(-1+2*i/4,ra,za) for i in range(5)]
            bb=[outer_point(-1+2*i/4,rb,zb) for i in range(5)]
            parts.append(_beam('structure',f'lower_belt_{side}_{band}',bb[0],bb[-1],200,ORANGE,'lower_belt'))
            for col in range(4):
                parts.append(_beam('structure',f'lower_panel_a_{side}_{band}_{col}',aa[col],bb[col+1],160,ORANGE,'lower_panel_brace'))
                parts.append(_beam('structure',f'lower_panel_b_{side}_{band}_{col}',aa[col+1],bb[col],105,ORANGE,'lower_panel_brace'))
            for col in (1,2,3):
                parts.append(_beam('structure',f'lower_panel_vertical_{side}_{band}_{col}',aa[col],bb[col],110,ORANGE,'lower_panel_vertical'))

    return parts


def _upper_frame_levels():
    # H-belt spacing traced from Miyaji No18 p86, anchored to printed GL levels.
    # Unlabelled intermediate belts are approximate, not construction dimensions.
    return [80000.,88000.,98000.,106000.,114000.,120000.,125000.,130000.,
            141000.,152000.,163000.,172000.,182000.,191000.,200000.,209000.,
            217000.,223550.,231000.,239000.,246000.,252650.]


def _upper_frame_ring(ring, z):
    """Interpolate the actual straight upper chord, rather than its control curve."""
    levels=_upper_frame_levels()
    for za,zb in zip(levels,levels[1:]):
        if za<=z<=zb:
            t=(z-za)/(zb-za);a,b=ring(za),ring(zb)
            return [[a[i][k]*(1-t)+b[i][k]*t for k in range(2)] for i in range(4)]
    raise ValueError('Upper frame attachment height is outside the chord range.')


def _upper_frame(p, ring, paint):
    levels=_upper_frame_levels()
    parts=[]
    for index,(za,zb) in enumerate(zip(levels,levels[1:]),1):
        a,b=ring(za),ring(zb);color=paint((za+zb)/2)
        for side in range(4):
            nxt=(side+1)%4
            parts.append(_rect_chord(f'upper_chord_{side}_{index}',(*a[side],za),(*b[side],zb),max(160,400-za*.0008),color))
            mid_low=[(a[side][k]+a[nxt][k])/2 for k in range(2)]+[za]
            mid_high=[(b[side][k]+b[nxt][k])/2 for k in range(2)]+[zb]
            radius=max(75,200-za*.0004)
            parts.append(_beam('structure',f'upper_diagonal_{side}_{index}',(*a[side],za),mid_high,radius,color,'upper_brace'))
            parts.append(_beam('structure',f'upper_return_{side}_{index}',mid_high,(*a[nxt],za),radius,color,'upper_brace'))
            parts.append(_beam('structure',f'upper_secondary_{side}_{index}',mid_low,(*b[nxt],zb),radius*.6,color,'upper_secondary'))
            parts.append(_beam('structure',f'upper_secondary_return_{side}_{index}',(*b[side],zb),mid_low,radius*.6,color,'upper_secondary'))
            parts.append(_beam('structure',f'upper_ring_{side}_{index}',(*b[side],zb),(*b[nxt],zb),max(120,280-za*.0005),color,'upper_ring'))
            if za<130000:
                parts.append(_beam('structure',f'upper_vertical_{side}_{index}',mid_low,mid_high,90,color,'upper_secondary'))
    return parts


def _foot_town(p):
    parts=[];half=18500.;roof=p['detail']['foot_town_roof_mm']
    floors=[0.,4500.,9000.,13500.,roof]
    # The separate overhanging roof is also the top floor: do not put another
    # coplanar full slab on it, which would flicker in the web presentation.
    for index,z in enumerate(floors[1:-1]):
        parts.append(_box('base',f'foot_town_floor_{index}',(-half,-half,z-220,half,half,z),'#C7C7BF','building_floor'))
    parts.append(_box('base','foot_town_roof',(-19500,-19500,roof-300,19500,19500,roof),'#70777A','building_roof'))
    for side in range(4):
        for index,(za,zb) in enumerate(zip(floors,floors[1:])):
            line=[(-half,-half),(half,-half)]
            if side==1:line=[(half,-half),(half,half)]
            elif side==2:line=[(half,half),(-half,half)]
            elif side==3:line=[(-half,half),(-half,-half)]
            a,b=line
            slab_thickness=300 if zb==roof else 220
            parts.append(_edge_panel('base',f'foot_town_fascia_{side}_{index}',a,b,zb-900,zb-slab_thickness,400,WHITE,role='building_cladding'))
            for bay in range(4):
                t0=(bay+.06)/4;t1=(bay+.94)/4
                start=[a[k]*(1-t0)+b[k]*t0 for k in range(2)]
                end=[a[k]*(1-t1)+b[k]*t1 for k in range(2)]
                parts.append(_edge_panel('base',f'foot_town_glazing_{side}_{index}_{bay}',start,end,za+850,zb-1050,90,GLASS,role='glazing'))
        # The following facade owns the shared corner pier.
        for bay in range(4):
            t=bay/4
            x,y=([(1-t)*-half+t*half,-half] if side==0 else
                 [half,(1-t)*-half+t*half] if side==1 else
                 [(1-t)*half-t*half,half] if side==2 else [-half,(1-t)*half-t*half])
            parts.append(_box('base',f'foot_town_pier_{side}_{bay}',(x-230,y-230,0,x+230,y+230,roof),WHITE,'building_column'))
    # A readable original entrance and canopy; no operator logo is reproduced.
    parts.append(_box('base','foot_town_entry_canopy',(-5700,-21600,3800,5700,-18200,4050),STEEL,'entrance_canopy'))
    for index,x in enumerate((-5400,5400)):
        parts.append(_box('base',f'entry_post_{index}',(x-150,-21000,0,x+150,-20700,3800),STEEL,'entrance_post'))
    for index,(a,b) in enumerate(((-2900,-100),(100,2900))):
        parts.append(_box('base',f'entry_door_glazing_{index}',(a,-18630,0,b,-18550,3300),GLASS,'glazing',finish='glass'))
    for index,x in enumerate((-3000,0,3000)):
        parts.append(_box('base',f'entry_door_frame_{index}',(x-90,-18680,0,x+90,-18480,3400),STEEL,'door_frame'))
    for side in range(4):
        ring=_square(19100);a,b=ring[side],ring[(side+1)%4]
        for z in (roof+600,roof+1200):
            parts.append(_beam('base',f'roof_guard_{side}_{int(z)}',(*a,z),(*b,z),60,STEEL,'roof_guard'))
        parts.append(_beam('base',f'roof_guard_post_{side}',(*a,roof),(*a,roof+1200),65,STEEL,'roof_guard'))
    return parts


def _stairs(p):
    parts=[];start=p['detail']['foot_town_roof_mm'];end=p['deck_levels_mm'][0]
    flights=24;risers=600;per_flight=risers//flights;rise=(end-start)/risers;run=260.
    for flight in range(flights):
        forward=flight%2==0;x0=5000. if forward else 7250.;x1=x0+1500
        za=start+flight*per_flight*rise;zb=za+per_flight*rise
        for index in range(per_flight):
            number=flight*per_flight+index+1
            y0=-6500+index*run if forward else -(index+1)*run
            z=za+(index+1)*rise
            parts.append(_box('core',f'external_stair_tread_{number:03d}',(x0,y0,z-80,x1,y0+run,z),'#9CA4A6','stair_tread',flight=flight+1,riser_index=number))
        for side,x in enumerate((x0-90,x1+90)):
            a=(x,-6500 if forward else 0,za-70)
            b=(x,0 if forward else -6500,zb-70)
            parts.append(_beam('core',f'external_stair_stringer_{flight}_{side}',a,b,110,STEEL,'stair_stringer',flight=flight+1))
            # One rail plus end posts is enough to reveal every switchback.
            parts.append(_beam('core',f'external_stair_rail_{flight}_{side}',(a[0],a[1],a[2]+1200),(b[0],b[1],b[2]+1200),45,STEEL,'stair_guard',flight=flight+1))
        y0=0 if forward else -8000
        parts.append(_box('core',f'external_stair_landing_{flight+1:02d}',(4700,y0,zb-200,9300,y0+1500,zb),'#9CA4A6','stair_landing',flight=flight+1))
        for x in (4700,9300):
            parts.append(_beam('core',f'external_stair_landing_post_{flight}_{x}',(x,y0+750,zb),(x,y0+750,zb+1150),55,STEEL,'stair_guard',flight=flight+1))
        guard_y=y0+1500 if forward else y0
        parts.append(_beam('core',f'external_stair_landing_guard_{flight}',(4700,guard_y,zb+1150),(9300,guard_y,zb+1150),45,STEEL,'stair_guard',flight=flight+1))
    # Four slender guide-frame posts replace the monolithic shaft block.
    for index,(x,y) in enumerate(_square(2000)):
        parts.append(_box('core',f'elevator_guide_post_{index}',(x-160,y-160,start,x+160,y+160,p['deck_levels_mm'][1]+1000),STEEL,'elevator_frame'))
    for level in range(20000,int(p['deck_levels_mm'][1])+1000,20000):
        points=_square(2000)
        for side in range(4):
            parts.append(_beam('core',f'elevator_guide_tie_{level}_{side}',(*points[side],level),(*points[(side+1)%4],level),90,STEEL,'elevator_frame'))
    for index,z in enumerate((70000,190000)):
        parts.append(_box('core',f'elevator_cabin_{index}',(-1400,-1400,z,1400,1400,z+3000),'#9CA7AE','elevator_cabin'))
    return parts


def _decks(p, ring):
    parts=[]
    for deck in p['deck_specs']:
        ident=deck['id'];half=deck['half_width_mm'];low=deck['bottom_mm'];glass=deck['glass_bottom_mm'];top=deck['top_mm']
        lower=_octagon(half*.85);outer=_octagon(half)
        support_z=deck['support_mm']
        support_ring=_upper_frame_ring(ring,support_z)
        support_half=abs(support_ring[0][0])
        if ident=='top':
            for side in range(4):
                parts.append(_beam('decks',f'{ident}_support_ring_{side}',
                                   (*support_ring[side],support_z),(*support_ring[(side+1)%4],support_z),
                                   170,ORANGE,'deck_support_ring'))
        for side in range(8):
            nxt=(side+1)%8
            # Thin faceted apron; the observation space is genuinely hollow.
            a,b=lower[side],lower[nxt];c,d=outer[side],outer[nxt]
            inward0=[[v*.985 for v in a],[v*.985 for v in b]]
            inward1=[[v*.985 for v in c],[v*.985 for v in d]]
            parts.append(_loft('decks',f'{ident}_apron_{side}',
                               [_section(low,[a,b,inward0[1],inward0[0]]),_section(glass,[c,d,inward1[1],inward1[0]])],ORANGE,'deck_apron'))
        levels=p['detail']['main_floor_levels_mm'] if ident=='main' else [deck['level_mm']]
        for index,z in enumerate(levels):
            if ident=='main':parts.extend(_floor_with_stair_opening(f'{ident}_reference_floor_{index+1}',half*.95,z,'#E1DCCE'))
            else:parts.append(_loft('decks',f'{ident}_reference_floor',[_section(z-300,_octagon(half*.95)),_section(z,_octagon(half*.95))],'#E1DCCE','deck_floor'))
        zones=[(glass,deck['level_mm']-350),(deck['level_mm']+250,top-1300)] if ident=='main' else [(glass,top-1300)]
        for side in range(8):
            a,b=outer[side],outer[(side+1)%8]
            bays=3 if side%2==0 else 1
            for bay in range(bays):
                t0=(bay+.045)/bays;t1=(bay+.955)/bays
                aa=[a[k]*(1-t0)+b[k]*t0 for k in range(2)]
                bb=[a[k]*(1-t1)+b[k]*t1 for k in range(2)]
                for zone,(za,zb) in enumerate(zones):
                    sa=1-.08*(za-glass)/(top-1300-glass)
                    sb=1-.08*(zb-glass)/(top-1300-glass)
                    parts.append(_edge_panel('decks',f'{ident}_glazing_{side}_{bay}_{zone}',
                                             [v*sa for v in aa],[v*sa for v in bb],za,zb,90,GLASS,
                                             upper_scale=sb/sa,role='glazing'))
            # Shared facade corners have one mullion, not two coincident ones.
            for bay in range(bays):
                t=bay/bays;x=a[0]*(1-t)+b[0]*t;y=a[1]*(1-t)+b[1]*t
                parts.append(_beam('decks',f'{ident}_mullion_{side}_{bay}',(x,y,glass),(x*.92,y*.92,top-1300),100 if ident=='main' else 70,WHITE,'window_frame'))
            if ident=='main':
                parts.append(_edge_panel('decks',f'{ident}_midfloor_belt_{side}',[v*.96 for v in a],[v*.96 for v in b],deck['level_mm']-300,deck['level_mm']+200,180,WHITE,role='floor_belt'))
            parts.append(_edge_panel('decks',f'{ident}_roof_edge_{side}',[v*.98 for v in a],[v*.98 for v in b],top-1300,top-250,220,WHITE,role='roof_fascia'))
            # Small supports and guard rails give the underside a readable scale.
            midpoint=[(a[k]+b[k])/2 for k in range(2)]
            radial=max(abs(value) for value in midpoint)
            anchor=[value/radial*support_half for value in midpoint]
            target=[(lower[side][k]+lower[(side+1)%8][k])/2 for k in range(2)]
            parts.append(_beam('decks',f'{ident}_underside_bracket_{side}',
                               (*anchor,support_z),(*target,low),200,ORANGE,'deck_bracket',
                               attachment_points=[[*anchor,support_z],[*target,low]],
                               target_member=f'decks:{ident}_apron_{side}'))
        parts.append(_loft('decks',f'{ident}_roof_cover',[_section(top-250,_octagon(half*.98)),_section(top,_octagon(half*.98))],WHITE,'deck_roof'))
        roof_ring=_octagon(half*.90)
        for side in range(8):
            a,b=roof_ring[side],roof_ring[(side+1)%8]
            parts.append(_beam('decks',f'{ident}_maintenance_guard_{side}',(*a,top+850),(*b,top+850),45,STEEL,'maintenance_guard'))
            parts.append(_beam('decks',f'{ident}_maintenance_post_{side}',(*a,top),(*a,top+850),50,STEEL,'maintenance_guard'))
    return parts


def _antenna(p,paint):
    start,split,end=p['antenna_start_mm'],p['antenna_lattice_top_mm'],p['height_mm'];parts=[]
    # Contractor H27 and SG/ST zone controls. Exact member sizes and all
    # intermediate antenna equipment stations are visual assumptions.
    levels=[start]+[z for z in range(258000,312000,4500)]+[split]
    def radius(z):return 1500.-1000.*(z-start)/(split-start)
    for index,(za,zb) in enumerate(zip(levels,levels[1:])):
        a,b=_square(radius(za)),_square(radius(zb));color=paint((za+zb)/2)
        for side in range(4):
            nxt=(side+1)%4
            parts.append(_beam('antenna',f'support_chord_{side}_{index}',(*a[side],za),(*b[side],zb),95,color,'antenna_support_chord'))
            parts.append(_beam('antenna',f'support_lacing_{side}_{index}',(*a[side],za),(*b[nxt],zb),40,color,'antenna_support_lacing'))
            parts.append(_beam('antenna',f'support_tie_{side}_{index}',(*b[side],zb),(*b[nxt],zb),50,color,'antenna_support_tie'))
    # The top 20.4m is a separate, slender ST appearance mast, not a solid
    # 80m cone masking the antenna-support lattice.
    edges=sorted({split,end,323000.}|{125000+i*(333000-125000)/7 for i in range(8) if split<125000+i*(333000-125000)/7<end})
    for index,(za,zb) in enumerate(zip(edges,edges[1:]),1):
        ra=500-350*(za-split)/(end-split);rb=500-350*(zb-split)/(end-split)
        parts.append(_loft('antenna',f'mast_{index:02d}',[_section(za,_circle(ra)),_section(zb,_circle(rb))],paint((za+zb)/2),'antenna_mast'))
    for index,z in enumerate((259000,273000,291000,306000),1):
        r=radius(z)
        # Equipment bands frame the open support mast; thin per-edge strips
        # do not fill its entire height with an opaque cylinder.
        ring=_square(r+230)
        for side in range(4):
            parts.append(_edge_panel('antenna',f'service_collar_{index}_{side}',ring[side],ring[(side+1)%4],z,z+650,180,paint(z),role='antenna_collar'))
    return parts


def _lights(p):
    parts=[]
    for index,(sx,sy) in enumerate(((-1,-1),(1,-1),(1,1),(-1,1)),1):
        x,y=sx*33000,sy*33000
        parts.append(_box('base',f'foot_uplight_housing_{index}',(x-650,y-450,1100,x+650,y+450,1800),STEEL,'light_housing',detail_level='micro'))
        parts.append(_box('base',f'foot_uplight_light_lens_{index}',(x-540,y-340,1800,x+540,y+340,1850),WARM,'light_lens',detail_level='micro'))
    for index,x in enumerate((-4600,4600),1):
        parts.append(_box('base',f'entry_wall_light_housing_{index}',(x-220,-18850,2700,x+220,-18400,3700),STEEL,'light_housing',detail_level='micro'))
        parts.append(_box('base',f'entry_wall_light_lens_{index}',(x-160,-18900,2800,x+160,-18860,3600),WARM,'light_lens',detail_level='micro'))
    for deck in p['deck_specs']:
        ident=deck['id'];h=deck['half_width_mm']*.75;z=deck['top_mm']+850
        for index,(x,y) in enumerate(_square(h),1):
            parts.append(_box('decks',f'{ident}_obstruction_light_housing_{index}',(x-170,y-170,z-180,x+170,y+170,z+100),STEEL,'light_housing',detail_level='micro'))
            parts.append(_box('decks',f'{ident}_obstruction_light_lens_{index}',(x-135,y-135,z+100,x+135,y+135,z+350),'#EB5B43','obstruction_light_lens',detail_level='micro'))
    for index,z in enumerate((270000,300000,325000),1):
        split=p['antenna_lattice_top_mm']
        if z<split:
            radius=1500-1000*(z-p['antenna_start_mm'])/(split-p['antenna_start_mm']);y=radius
        else:
            radius=500-350*(z-split)/(p['height_mm']-split);y=0
        parts.append(_beam('antenna',f'obstruction_light_bracket_{index}',(radius-50,y,z),(radius+350,y,z),55,STEEL,'light_housing',detail_level='micro'))
        parts.append(_box('antenna',f'obstruction_light_lens_{index}',(radius+220,y-150,z,radius+480,y+150,z+350),'#EB5B43','obstruction_light_lens',detail_level='micro'))

    return parts


def component_specs(parameters, ring_at_height, paint_at_height):
    p=parameters
    parts=[_box('base','ground_slab',(-48000,-48000,-2000,48000,48000,0),'#D2CDC3','ground')]
    parts.extend(_lower_frame(p,ring_at_height,paint_at_height))
    parts.extend(_upper_frame(p,ring_at_height,paint_at_height))
    parts.extend(_foot_town(p))
    parts.extend(_stairs(p))
    parts.extend(_decks(p,ring_at_height))
    parts.extend(_antenna(p,paint_at_height))
    parts.extend(_lights(p))
    return parts
