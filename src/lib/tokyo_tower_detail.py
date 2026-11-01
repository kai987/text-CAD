"""Reference-informed R07 Tokyo Tower appearance detail, in mm; not an engineered copy.

Published controls include construction GL heights, the H11/H12 27/28m plan
widths, H23 D13m plan, replacement ST BOX450 section, and the approximately
600-step outdoor route. Identifying these historical bands with present-day
floors, intermediate member layouts, shell trims, equipment stations, walls,
connections, glazing, route and light positions remains a modelling assumption.

All returned primitives use the shared box/beam/loft contract. Thus CAD,
editable drawings and the web model retain one source of geometry.
"""
from __future__ import annotations

from math import cos, sin, pi, sqrt, isfinite

ORANGE = '#E34C25'
WHITE = '#F4F0E7'
STEEL = '#6D7880'
GLASS = '#658C9E'
WARM = '#FFE0A3'

BASE_APPEARANCE_DEFAULTS = {
    'leg_cage_transition_start_mm': 80000., 'leg_cage_top_mm': 125000.,
    'leg_cage_top_half_width_mm': 450.,
    'leg_continuation_levels_mm': [88000.,98000.,106000.,114000.,120000.,125000.],
    'leg_continuation_chord_half_width_mm': 262.5,
    'leg_continuation_overlap_mm': 40., 'leg_transition_link_radius_mm': 100.,
    'leg_attachment_inset_mm': 150.,
    'leg_continuation_scope': 'The four-member gross leg assemblies continue smoothly from ground '
                              'through the former 80m modelling boundary to the Main Deck. '
                              'Continuation stations, cage taper, constant 525mm H appearance '
                              'sections, short branch links and fitted end laps are visual '
                              'assumptions, not recovered original member or connection designs.',
    'arch_rib_depth_mm': 1800., 'arch_plane_half_depth_mm': 650.,
    'arch_panel_count': 16, 'arch_profile_width_mm': 450.,
    'arch_profile_depth_mm': 600., 'arch_web_thickness_mm': 20.,
    'arch_flange_thickness_mm': 24., 'arch_joint_overlap_mm': 40.,
    'arch_web_radius_mm': 85., 'arch_cross_tie_radius_mm': 75.,
    'foot_town_width_mm': 48000., 'foot_town_depth_mm': 44000.,
    'foot_town_floor_levels_mm': [0.,3600.,7200.,10800.,14400.,18300.],
    'foot_town_glazed_bands': 2, 'foot_town_bays_per_face': 8,
    'foot_town_wall_thickness_mm': 350., 'foot_town_roof_overhang_mm': 900.,
    'foot_town_upper_color': '#76584B', 'foot_town_canopy_width_mm': 14000.,
    'foot_town_canopy_projection_mm': 2800., 'foot_town_door_height_mm': 3000.,
    'foot_town_roof_housing_bounds_mm': [-4200.,8000.,18300.,4200.,13000.,21000.],
    'scope': 'H3 GL40m and 80m foot-axis spacing are published structural controls. '
             'Arch depth, profile and web sizes, panel layout, FootTown 48x44m plan, '
             'facade bands, cladding and rooftop equipment are photograph/drawing-guided '
             'appearance assumptions, not surveyed dimensions or structural design.',
}


def _base_config(p):
    return {**BASE_APPEARANCE_DEFAULTS,**p.get('detail',{}).get('base_appearance',{})}


def _leg_frame_levels(p):
    c=_base_config(p)
    levels=sorted(set([*p['detail']['leg_stations_mm'],*c['leg_continuation_levels_mm']]))
    if levels[0]!=0 or levels[-1]!=c['leg_cage_top_mm']:
        raise ValueError('Continuous leg stations must run from ground to the fitted deck junction.')
    if c['leg_cage_transition_start_mm'] not in levels:
        raise ValueError('The retained lower-leg boundary must be an explicit station.')
    return levels


def _leg_cage_half(p,z):
    """Retain the legacy0–80m axes, then smoothly taper the gross assembly."""
    c=_base_config(p);start=c['leg_cage_transition_start_mm'];top=c['leg_cage_top_mm']
    if z<=start:return max(950,1800-z*.010)
    begin=max(950,1800-start*.010);end=c['leg_cage_top_half_width_mm']
    if not 0<end<begin or top<=start:raise ValueError('Invalid fitted continuation taper.')
    if z>=top:return end
    h=top-start;t=(z-start)/h;slope=-.010*h
    return ((2*t**3-3*t**2+1)*begin+(t**3-2*t**2+t)*slope
            +(-2*t**3+3*t**2)*end+(t**3-t**2)*slope)


def _arch_plate_chord(name,a,b,normal,p,**metadata):
    """An open H-like built-up rib, with its broad web in the arch plane.

    Nominal axes remain explicit for drawing/connection clients. Forty-mm
    end laps prevent fitted polygonal bends from being disconnected solids;
    they represent appearance joints rather than designed fabrication splices.
    """
    c=_base_config(p);delta=[b[k]-a[k] for k in range(3)]
    length=sqrt(sum(v*v for v in delta));w=[v/length for v in delta]
    u=list(normal);v=[w[1]*u[2]-w[2]*u[1],w[2]*u[0]-w[0]*u[2],w[0]*u[1]-w[1]*u[0]]
    length=sqrt(sum(x*x for x in v));v=[x/length for x in v]
    # Re-orthogonalise the face normal for the mildly warped four-sided frame.
    u=[v[1]*w[2]-v[2]*w[1],v[2]*w[0]-v[0]*w[2],v[0]*w[1]-v[1]*w[0]]
    x,y=c['arch_profile_width_mm']/2,c['arch_profile_depth_mm']/2
    t,q=c['arch_web_thickness_mm']/2,c['arch_flange_thickness_mm']
    if not 0<t<x or not 0<q<y:raise ValueError('Invalid fitted arch plate profile.')
    outline=[[-x,-y],[x,-y],[x,-y+q],[t,-y+q],[t,y-q],[x,y-q],
             [x,y],[-x,y],[-x,y-q],[-t,y-q],[-t,-y+q],[-x,-y+q]]
    lap=c['arch_joint_overlap_mm']
    ends=[[a[k]-w[k]*lap for k in range(3)],[b[k]+w[k]*lap for k in range(3)]]
    sections=[[[o[k]+u[k]*xx+v[k]*yy for k in range(3)] for xx,yy in outline] for o in ends]
    return {'group':'structure','name':'structure:'+name,'kind':'loft3d','color':ORANGE,
            'role':'open_cross_frame','sections':sections,'start':list(a),'end':list(b),
            'axis_start':list(a),'axis_end':list(b),'steel_role':'arch_plate_chord',
            'section_profile':{'type':'H','width_mm':2*x,'depth_mm':2*y,
                               'web_thickness_mm':2*t,'flange_thickness_mm':q},
            'section_scope':c['scope'],**metadata}

# The shell and equipment controls below are appearance assumptions, not
# recovered fabrication dimensions. Keep the construction GL controls in p.
DECK_APPEARANCE_DEFAULTS = {
    'main_lower_half_width_mm': 13500., 'main_upper_half_width_mm': 14000.,
    'main_chamfer_factor': .18, 'main_glass_top_scale': 1.,
    'main_long_face_bays': 24, 'main_corner_face_bays': 4,
    'main_mullion_radius_mm': 32., 'main_transom_height_mm': 65.,
    'main_glass_color': '#284C61', 'main_soffit_thickness_mm': 180.,
    'main_fascia_height_mm': 350., 'main_roof_fascia_height_mm': 180.,
    'main_cleaning_track_radius_mm': 48.,
    'top_facets': 48, 'top_glass_color': '#385C6C',
    'top_lower_radius_factor': .86, 'top_glass_radius_factor': 1.,
    'top_roof_radius_factor': 1.04, 'top_mullion_radius_mm': 28.,
    'top_glass_top_offset_mm': 850.,
    'top_service_platform_mm': 231000., 'top_service_radius_mm': 6800.,
    'top_service_inner_radius_mm': 4500., 'top_service_rail_height_mm': 1100.,
}
ANTENNA_APPEARANCE_DEFAULTS = {
    'digital_panel_bottom_mm': 240550.,
    'digital_group_height_mm': 5300., 'digital_group_gap_mm': 500.,
    'digital_lower_diameter_mm': 13400., 'digital_upper_diameter_mm': 12876.,
    'digital_support_diameter_mm': 11800.,
    'digital_panel_columns': 30, 'digital_panel_rows': 5,
    'digital_panel_depth_mm': 220., 'digital_panel_azimuth_gap_degrees': .25,
    'digital_panel_gap_mm': 50.,
    'mx_panel_bottom_mm': 237600., 'mx_panel_height_mm': 650.,
    'mx_panel_row_pitch_mm': 950., 'mx_panel_radius_mm': 6200.,
    'sg_bay_height_mm': 4500., 'sg_inner_half_width_low_mm': 1500.,
    'sg_inner_half_width_high_mm': 500., 'sg_outer_offset_mm': 440.,
    'sg_inner_chord_radius_mm': 95., 'sg_outer_chord_radius_mm': 105.,
    'sg_inner_brace_radius_mm': 40., 'sg_outer_brace_radius_mm': 50.,
    'sg_link_radius_mm': 48., 'sg_link_layer_offset_mm': 160.,
    'st_width_mm': 450., 'st_depth_mm': 450., 'st_wall_mm': 16.,
    'st_equipment_levels_mm': [315000., 318000., 321000., 324000., 327000., 330000.],
    'st_equipment_half_width_mm': 380.,
}


UPPER_SHAFT_OUTLINE_DEFAULTS = {
    'enabled': True,
    'start_mm': 130000., 'end_mm': 223550.,
    'start_half_width_mm': 9900., 'end_half_width_mm': 3950.,
    'start_slope_mm_per_mm': -.06827586206896552,
    'end_slope_mm_per_mm': -.041757602211552454,
    'method': 'convex integrated power tangent blend',
    'scope': 'Photo-guided appearance fit of the shaft between the Main Deck roof '
             'and historical H23 roof control. End radii and tangents match the '
             'retained reference profile; intermediate half-widths are fitted, '
             'not original surveyed coordinates or a structural member schedule.',
}


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


def body_radius(p, z):
    """Use an explicit local, convex taper without changing the reference outside.

    R06 parameter records do not opt in. The active R07 fit integrates a
    monotone tangent field, so it matches both endpoint radii/tangents and
    cannot form a shoulder outside their connecting line. The original
    profile stays available for the unchanged lower frame and upper antenna.
    """
    configured=p.get('detail',{}).get('upper_shaft_outline')
    if configured is None:return profile_radius(p['profile'],z)
    if not isinstance(configured,dict):raise ValueError('Upper shaft outline must be a configuration object.')
    c={**UPPER_SHAFT_OUTLINE_DEFAULTS,**configured}
    if not c['enabled']:return profile_radius(p['profile'],z)
    start,end=c['start_mm'],c['end_mm']
    if not all(isfinite(v) for v in (start,end)) or not 0<=start<end:
        raise ValueError('Upper shaft fit requires finite, increasing height bounds.')
    if z<=start or z>=end:return profile_radius(p['profile'],z)
    r0,r1=c['start_half_width_mm'],c['end_half_width_mm']
    m0,m1=c['start_slope_mm_per_mm'],c['end_slope_mm_per_mm']
    if not all(isfinite(v) for v in (r0,r1,m0,m1)) or not 0<r1<r0:
        raise ValueError('Upper shaft fit requires finite decreasing positive half-widths.')
    if c['method']!=UPPER_SHAFT_OUTLINE_DEFAULTS['method']:
        raise ValueError('Unsupported upper shaft fit method.')
    if any(abs(profile_radius(p['profile'],height)-radius)>1e-7
           for height,radius in ((start,r0),(end,r1))):
        raise ValueError('Upper shaft fit radii must meet the retained reference at both boundaries.')
    height=end-start;secant=(r1-r0)/height
    if not m0<secant<m1<0:
        raise ValueError('Upper shaft tangents must bracket its negative secant slope.')
    power=(m1-m0)/(secant-m0)-1.
    if power<1:
        raise ValueError('Upper shaft tangent blend must have finite nonnegative curvature.')
    t=(z-start)/height
    return r0+height*(m0*t+(m1-m0)*t**(power+1)/(power+1))


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
    parts=[];c=_base_config(p)
    levels=_leg_frame_levels(p)
    corners=[(-1,-1),(1,-1),(1,1),(-1,1)]
    for leg,(sx,sy) in enumerate(corners,1):
        for index,(za,zb) in enumerate(zip(levels,levels[1:]),1):
            ra=ring(za)[0][0]*-1;rb=ring(zb)[0][0]*-1
            cage_a=_leg_cage_half(p,za);cage_b=_leg_cage_half(p,zb)
            a=_square(cage_a,(sx*ra,sy*ra));b=_square(cage_b,(sx*rb,sy*rb))
            color=paint((za+zb)/2)
            for chord in range(4):
                start=[*a[chord],za];end=[*b[chord],zb]
                if za>=c['leg_cage_transition_start_mm']:
                    delta=[end[k]-start[k] for k in range(3)];length=sqrt(sum(v*v for v in delta))
                    lap=c['leg_continuation_overlap_mm']
                    aa=[start[k]-delta[k]/length*lap for k in range(3)]
                    bb=[end[k]+delta[k]/length*lap for k in range(3)]
                    part=_rect_chord(f'leg_{leg:02d}_chord_{chord:02d}_{index:02d}',aa,bb,
                                     c['leg_continuation_chord_half_width_mm'],color)
                    part.update(nominal_axis_start=start,nominal_axis_end=end,leg_continuation=True,
                                continuation_scope=c['leg_continuation_scope'])
                    parts.append(part)
                else:
                    parts.append(_rect_chord(f'leg_{leg:02d}_chord_{chord:02d}_{index:02d}',
                                            start,end,max(180,360-za*.0015),color))
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
        # Bind the continuing cage to the retained, independently named
        # central upper H chord. Points use the actual straight source axes,
        # not the smooth envelope between their stations.
        upper_levels=_upper_frame_levels()
        for station,level in enumerate([c['leg_cage_transition_start_mm'],*c['leg_continuation_levels_mm']]):
            z=level+(c['leg_attachment_inset_mm'] if level<levels[-1] else -c['leg_attachment_inset_mm'])
            interval=next(i for i,(a,b) in enumerate(zip(levels,levels[1:])) if a<=z<=b)
            za,zb=levels[interval:interval+2];t=(z-za)/(zb-za)
            aa=_square(_leg_cage_half(p,za),(sx*-ring(za)[0][0],sy*-ring(za)[0][0]))
            bb=_square(_leg_cage_half(p,zb),(sx*-ring(zb)[0][0],sy*-ring(zb)[0][0]))
            centre=[*_upper_frame_ring(ring,z)[leg-1],z]
            upper_index=next(i for i,(a,b) in enumerate(zip(upper_levels,upper_levels[1:]),1) if a<=z<=b)
            for chord in range(4):
                source=[aa[chord][k]*(1-t)+bb[chord][k]*t for k in range(2)]+[z]
                parts.append(_beam('structure',f'leg_{leg:02d}_continuation_link_{station}_{chord}',source,centre,
                                   c['leg_transition_link_radius_mm'],color,'leg_transition_link',
                                   source_member=f'structure:leg_{leg:02d}_chord_{chord:02d}_{interval+1:02d}',
                                   target_member=f'structure:upper_chord_{leg-1}_{upper_index}',
                                   attachment_points=[source,centre],level_mm=level,attachment_z_mm=z,
                                   leg_group=leg,leg_chord=chord,scope=c['leg_continuation_scope']))
    def cage_outer_radius(z):
        # Endpoints use the straight native chord interpolation, not the smooth
        # envelope control curve; otherwise new panels would float in the cage.
        i=next(i for i,(za,zb) in enumerate(zip(levels,levels[1:])) if za<=z<=zb)
        za,zb=levels[i:i+2];t=(z-za)/(zb-za)
        ra,rb=-ring(za)[0][0],-ring(zb)[0][0]
        ca,cb=_leg_cage_half(p,za),_leg_cage_half(p,zb)
        return (ra+ca)*(1-t)+(rb+cb)*t
    # The contractor's p86 elevation puts the arch crown at H3 / GL+40m.
    # Its exact curve, rib offset and all intermediate points are digitised
    # modelling approximations. The previous floating 26–67m arch was wrong.
    crown=p['detail']['arch_crown_mm'];foot=1300.
    for side in range(4):
        normal=((0,1),(-1,0),(0,-1),(1,0))[side]
        def side_point(x,z):
            r=-ring(z)[0][0]
            return ([x,-r,z] if side==0 else [r,x,z] if side==1 else
                    [-x,r,z] if side==2 else [-r,-x,z])
        span=40000.-1800.
        c=_base_config(p);panels=int(c['arch_panel_count'])
        if panels<8 or panels%2:raise ValueError('Arch modelling panels must be even and at least eight.')
        if not 0<c['arch_rib_depth_mm']<crown-foot:raise ValueError('Invalid fitted arch depth.')
        path=[];inner_path=[]
        for i in range(panels+1):
            q=-1+2*i/panels;rise=1-q*q
            path.append(side_point(q*span,foot+(crown-foot)*rise))
            inner_path.append(side_point(q*span,foot+(crown-foot-c['arch_rib_depth_mm'])*rise))
        normal3=[*normal,0.]
        for lane,offset in enumerate((-c['arch_plane_half_depth_mm'],c['arch_plane_half_depth_mm'])):
            line=[[x+normal[0]*offset,y+normal[1]*offset,z] for x,y,z in path]
            lower=[[x+normal[0]*offset,y+normal[1]*offset,z] for x,y,z in inner_path]
            for layer,points in (('outer',line),('inner',lower)):
                for i,(a,b) in enumerate(zip(points,points[1:])):
                    name=f'lower_arch_{side}_{lane}_{i}' if layer=='outer' else f'lower_arch_inner_{side}_{lane}_{i}'
                    parts.append(_arch_plate_chord(name,a,b,normal3,p,arch_side=side,arch_lane=lane,
                                                   arch_layer=layer,arch_segment=i,arch_member_kind='chord'))
            # Each visible face has a genuinely deep curved truss. Its
            # triangular webs connect the distinct upper/lower chord axes;
            # the old front/back-only ribbons had no in-plane truss depth.
            for i in range(panels):
                a,b=(line[i],lower[i+1]) if i%2==0 else (lower[i],line[i+1])
                parts.append(_beam('structure',f'lower_arch_diagonal_{side}_{lane}_{i}',a,b,
                                   c['arch_web_radius_mm'],ORANGE,'open_cross_frame',
                                   arch_side=side,arch_lane=lane,arch_member_kind='diagonal'))
            for i in range(1,panels):
                parts.append(_beam('structure',f'lower_arch_inplane_tie_{side}_{lane}_{i}',lower[i],line[i],
                                   c['arch_web_radius_mm']*.8,ORANGE,'open_cross_frame',
                                   arch_side=side,arch_lane=lane,arch_member_kind='in_plane_tie'))
            for end,point in enumerate((line[0],line[-1])):
                z=point[2]
                interval=next(i for i,(a,b) in enumerate(zip(levels,levels[1:])) if a<=z<=b)
                za,zb=levels[interval],levels[interval+1];t=(z-za)/(zb-za)
                ra,rb=-ring(za)[0][0],-ring(zb)[0][0]
                ca,cb=_leg_cage_half(p,za),_leg_cage_half(p,zb)
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
                                   source_member=f'structure:lower_arch_{side}_{lane}_{0 if end==0 else panels-1}',
                                   target_member=f'structure:leg_{leg:02d}_chord_{chord:02d}_{interval+1:02d}',
                                   attachment_points=[list(point),target]))
        for layer,points in (('outer',path),('inner',inner_path)):
            for i,point in enumerate(points):
                half=c['arch_plane_half_depth_mm']
                a=[point[0]-normal[0]*half,point[1]-normal[1]*half,point[2]]
                b=[point[0]+normal[0]*half,point[1]+normal[1]*half,point[2]]
                name=f'lower_arch_web_{side}_{i}' if layer=='outer' else f'lower_arch_inner_web_{side}_{i}'
                parts.append(_beam('structure',name,a,b,c['arch_cross_tie_radius_mm'],ORANGE,'open_cross_frame',
                                   arch_side=side,arch_layer=layer,arch_member_kind='depth_tie'))
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
                parts.append(_beam('structure',f'arch_spandrel_tie_{side}_{half_sign}_{i}',a,b,125,ORANGE,'arch_spandrel',arch_side=side))
                if i:
                    parts.append(_beam('structure',f'arch_spandrel_diagonal_{side}_{half_sign}_{i}',outer[i-1],a,105,ORANGE,'arch_spandrel',arch_side=side))
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

        # The H3 face lies at the outer leg-cage plane, not at the smooth
        # envelope used by the curved arch. Bridge the actual nearest rib to
        # the unchanged central lower-panel axis instead of leaving a gap.
        target=outer_point(0,cage_outer_radius(crown),crown)
        candidates=[[v+normal3[k]*offset for k,v in enumerate(side_point(0,crown))]
                    for offset in (-c['arch_plane_half_depth_mm'],c['arch_plane_half_depth_mm'])]
        lane=min(range(2),key=lambda i:sum((candidates[i][k]-target[k])**2 for k in range(3)))
        source=candidates[lane]
        parts.append(_beam('structure',f'arch_spandrel_crown_bridge_{side}',source,target,100,ORANGE,'arch_spandrel',
                           arch_side=side,
                           source_member=f'structure:lower_arch_{side}_{lane}_{panels//2-1}',
                           target_member=f'structure:lower_panel_vertical_{side}_0_2',
                           attachment_points=[source,target],scope=c['scope']))

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
        a,b=ring(za),ring(zb);color=WHITE if za>=217000 else paint((za+zb)/2)
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
    c=_base_config(p);parts=[];hx=c['foot_town_width_mm']/2;hy=c['foot_town_depth_mm']/2
    roof=p['detail']['foot_town_roof_mm'];floors=list(c['foot_town_floor_levels_mm'])
    if floors[0]!=0 or floors[-1]!=roof or any(b<=a for a,b in zip(floors,floors[1:])):
        raise ValueError('FootTown fitted facade levels must be increasing from ground to the retained roof.')
    glazed=int(c['foot_town_glazed_bands']);bays=int(c['foot_town_bays_per_face']);wall=c['foot_town_wall_thickness_mm']
    if not 0<glazed<len(floors)-1 or bays<4 or bays%2:raise ValueError('Invalid fitted FootTown facade subdivision.')
    outer=[[-hx,-hy],[hx,-hy],[hx,hy],[-hx,hy]]
    # Internal slabs stop at the wall's inner face: no coplanar grey strip
    # fights with opaque upper cladding on the exterior.
    for index,z in enumerate(floors[1:-1]):
        parts.append(_box('base',f'foot_town_floor_{index}',(-hx+wall,-hy+wall,z-220,hx-wall,hy-wall,z),
                          '#C7C7BF','building_floor',floor_level_mm=z))
    overhang=c['foot_town_roof_overhang_mm']
    parts.append(_box('base','foot_town_roof',(-hx-overhang,-hy-overhang,roof-300,
                                            hx+overhang,hy+overhang,roof),'#70777A','building_roof'))
    for side,(a,b) in enumerate(zip(outer,outer[1:]+outer[:1])):
        dx,dy=b[0]-a[0],b[1]-a[1];length=sqrt(dx*dx+dy*dy);inside=[-dy/length,dx/length]
        for index,(za,zb) in enumerate(zip(floors,floors[1:])):
            top=zb-(300 if zb==roof else 0)
            if index<glazed:
                parts.append(_edge_panel('base',f'foot_town_fascia_{side}_{index}',a,b,zb-550,zb-220,wall,
                                         WHITE,role='building_cladding'))
                for bay in range(bays):
                    # The actual entrance leaves a clear central pair of
                    # ground-floor bays; no second pane sits behind its doors.
                    if side==0 and index==0 and bay in (bays//2-1,bays//2):continue
                    t0=(bay+.05)/bays;t1=(bay+.95)/bays
                    start=[a[k]*(1-t0)+b[k]*t0 for k in range(2)]
                    end=[a[k]*(1-t1)+b[k]*t1 for k in range(2)]
                    parts.append(_edge_panel('base',f'foot_town_glazing_{side}_{index}_{bay}',
                                             start,end,za+350,zb-650,90,GLASS,role='glazing'))
            else:
                parts.append(_edge_panel('base',f'foot_town_upper_cladding_{side}_{index}',a,b,za,top-100,wall,
                                         c['foot_town_upper_color'],role='building_cladding'))
                parts.append(_edge_panel('base',f'foot_town_upper_joint_{side}_{index}',a,b,top-100,top,wall,
                                         '#62473D',role='building_cladding'))
        # White piers and glazed openings are confined to the lower public
        # frontage. Upper floors form an opaque brown/bronze mass in photos.
        for bay in range(bays):
            t=bay/bays;x,y=[a[k]*(1-t)+b[k]*t for k in range(2)]
            parts.append(_box('base',f'foot_town_pier_{side}_{bay}',
                              (x-230,y-230,0,x+230,y+230,floors[glazed]),WHITE,'building_column'))
        # Shallow standing joints give the opaque facade a vertical panel
        # rhythm. Their fronts project6mm, rather than occupying coplanar skins.
        for bay in range(1,bays):
            t=bay/bays;centre=[a[k]*(1-t)+b[k]*t-inside[k]*6 for k in range(2)]
            tangent=[dx/length,dy/length]
            start=[centre[k]-tangent[k]*25 for k in range(2)]
            end=[centre[k]+tangent[k]*25 for k in range(2)]
            parts.append(_edge_panel('base',f'foot_town_vertical_joint_{side}_{bay}',start,end,
                                     floors[glazed],roof-300,20,'#62473D',role='building_cladding'))
    face=-hy;canopy_half=c['foot_town_canopy_width_mm']/2;projection=c['foot_town_canopy_projection_mm']
    parts.append(_box('base','foot_town_entry_canopy',(-canopy_half,face-projection,3800,
                                                     canopy_half,face+300,4050),STEEL,'entrance_canopy'))
    for index,x in enumerate((-canopy_half+300,canopy_half-300)):
        parts.append(_box('base',f'entry_post_{index}',(x-150,face-projection+400,0,
                                                     x+150,face-projection+700,3800),WHITE,'entrance_post'))
    height=c['foot_town_door_height_mm']
    for index,(a,b) in enumerate(((-2900,-100),(100,2900))):
        parts.append(_box('base',f'entry_door_glazing_{index}',(a,face+20,0,b,face+100,height),
                          GLASS,'glazing',finish='glass'))
    for index,x in enumerate((-3000,0,3000)):
        parts.append(_box('base',f'entry_door_frame_{index}',(x-90,face-50,0,x+90,face+130,height+100),
                          STEEL,'door_frame'))
    parts.append(_box('base','foot_town_entry_door_header',(-3090,face-50,height,3090,face+130,height+100),
                      STEEL,'door_frame'))
    # The side lights replace the omitted ground-floor centre windows.
    for index,(a,b) in enumerate(((-5700,-3300),(3300,5700))):
        parts.append(_box('base',f'entry_sidelight_glazing_{index}',(a,face+20,350,b,face+100,height),
                          GLASS,'glazing',finish='glass'))
    housing=list(c['foot_town_roof_housing_bounds_mm'])
    if housing[2]!=roof:raise ValueError('Fitted rooftop housing must start on the retained roof.')
    parts.append(_box('base','foot_town_rooftop_housing',housing,c['foot_town_upper_color'],
                      'building_roof_housing',dimensions_status='photo_guided_appearance_assumption'))
    rail=[[-hx-overhang/2,-hy-overhang/2],[hx+overhang/2,-hy-overhang/2],
          [hx+overhang/2,hy+overhang/2],[-hx-overhang/2,hy+overhang/2]]
    for side,(a,b) in enumerate(zip(rail,rail[1:]+rail[:1])):
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


def _deck_shell_band(parts, name, lower, upper, za, zb, color, role):
    """Perimeter strips leave deck interiors and tower openings visible."""
    for side,(a,b) in enumerate(zip(lower,lower[1:]+lower[:1])):
        c,d=upper[side],upper[(side+1)%len(upper)]
        parts.append(_loft('decks',f'{name}_{side}',[
            _section(za,[a,b,[v*.985 for v in b],[v*.985 for v in a]]),
            _section(zb,[c,d,[v*.985 for v in d],[v*.985 for v in c]])],color,role,
            dimensions_status='demonstration_assumption'))


def _deck_brackets(parts, deck, lower, support_ring):
    """Eight load-path markers meet apron edges independently of facet count."""
    support_z=deck['support_mm'];support_half=abs(support_ring[0][0])
    for index in range(8):
        side=index*len(lower)//8
        a,b=lower[side],lower[(side+1)%len(lower)]
        target=[(a[k]+b[k])/2 for k in range(2)]
        radial=max(abs(value) for value in target)
        anchor=[value/radial*support_half for value in target]
        parts.append(_beam('decks',f'{deck["id"]}_underside_bracket_{index}',
                           (*anchor,support_z),(*target,deck['bottom_mm']),200,
                           WHITE if deck['id']=='top' else ORANGE,'deck_bracket',
                           attachment_points=[[*anchor,support_z],[*target,deck['bottom_mm']]],
                           target_member=f'decks:{deck["id"]}_apron_{side}',
                           dimensions_status='demonstration_assumption'))


def _main_deck(p, deck, ring, cfg):
    """Two upright curtain-wall levels with a shallow soffit and cleaning rail.

    The 27/28m control widths are from Naito's published H11/H12 plans.
    Current narrow-window rhythm follows LIXIL's 2019 exterior photographs;
    present-day floor identification, bays, frames and trim remain assumptions.
    """
    parts=[];low=deck['bottom_mm'];glass=deck['glass_bottom_mm'];top=deck['top_mm'];level=deck['level_mm']
    halves=[cfg['main_lower_half_width_mm'],cfg['main_upper_half_width_mm']]
    chamfer=cfg['main_chamfer_factor'];outer=[_octagon(half,chamfer) for half in halves]
    lower=_octagon(halves[0]*.995,chamfer)
    glass_top=top-cfg['main_roof_fascia_height_mm']-120.
    roof_ring=[[v*cfg['main_glass_top_scale'] for v in q] for q in outer[1]]
    support_ring=_upper_frame_ring(ring,deck['support_mm'])
    _deck_shell_band(parts,'main_apron',lower,outer[0],low,glass,WHITE,'deck_apron')
    _deck_brackets(parts,deck,lower,support_ring)
    floor_halves=p['detail'].get('main_floor_half_widths_mm',halves)
    for index,(z,half) in enumerate(zip(p['detail']['main_floor_levels_mm'],floor_halves)):
        parts.extend(_floor_with_stair_opening(f'main_reference_floor_{index+1}',half*.985,z,'#E1DCCE'))
    support_half=abs(support_ring[0][0]);inner=_octagon(support_half,chamfer)
    thickness=cfg['main_soffit_thickness_mm']
    for side,(a,b) in enumerate(zip(lower,lower[1:]+lower[:1])):
        c,d=inner[side],inner[(side+1)%8];outline=[a,b,d,c]
        parts.append(_loft('decks',f'main_soffit_panel_{side}',
                           [_section(low-thickness,outline),_section(low,outline)],'#D9DAD4','deck_soffit',
                           dimensions_status='demonstration_assumption'))
        count=8 if side%2==0 else 3
        for rib in range(count):
            t=(rib+.5)/count
            start=[c[k]*(1-t)+d[k]*t for k in range(2)]
            end=[a[k]*(1-t)+b[k]*t for k in range(2)]
            parts.append(_beam('decks',f'main_soffit_rib_{side}_{rib}',
                               (*start,low-thickness-70),(*end,low-thickness-70),65,WHITE,'soffit_rib',
                               dimensions_status='demonstration_assumption'))
    zones=[(glass,level-350),(level+250,glass_top)]
    for zone,((za,zb),points) in enumerate(zip(zones,outer)):
        for side,(a,b) in enumerate(zip(points,points[1:]+points[:1])):
            bays=cfg['main_long_face_bays'] if side%2==0 else cfg['main_corner_face_bays']
            for bay in range(bays):
                t0=(bay+.025)/bays;t1=(bay+.975)/bays
                aa=[a[k]*(1-t0)+b[k]*t0 for k in range(2)]
                bb=[a[k]*(1-t1)+b[k]*t1 for k in range(2)]
                parts.append(_edge_panel('decks',f'main_glazing_{side}_{bay}_{zone}',aa,bb,za,zb,70,
                                         cfg['main_glass_color'],upper_scale=cfg['main_glass_top_scale'],role='glazing'))
                t=bay/bays;point=[a[k]*(1-t)+b[k]*t for k in range(2)]
                parts.append(_beam('decks',f'main_mullion_{side}_{bay}_{zone}',(*point,za),
                                   (*[v*cfg['main_glass_top_scale'] for v in point],zb),
                                   cfg['main_mullion_radius_mm'],WHITE,'window_frame'))
            # Two fine transoms per storey retain a large central pane.
            for edge,z in enumerate((za+430,zb-430)):
                h=cfg['main_transom_height_mm']
                parts.append(_edge_panel('decks',f'main_transom_{side}_{zone}_{edge}',a,b,z,z+h,110,WHITE,
                                         role='window_frame'))
    _deck_shell_band(parts,'main_midfloor_belt',outer[0],outer[1],level-350,level+250,WHITE,'floor_belt')
    for side in range(8):
        parts.append(_edge_panel('decks',f'main_lower_fascia_{side}',lower[side],lower[(side+1)%8],
                                 low,low+cfg['main_fascia_height_mm'],140,WHITE,role='deck_fascia'))
        parts.append(_edge_panel('decks',f'main_roof_edge_{side}',roof_ring[side],roof_ring[(side+1)%8],
                                 glass_top,top-120,140,WHITE,role='roof_fascia'))
        # The shallow dark perimeter is cleaning equipment, not a heavy cap.
        track_a=[v*1.012 for v in roof_ring[side]];track_b=[v*1.012 for v in roof_ring[(side+1)%8]]
        parts.append(_beam('decks',f'main_cleaning_track_{side}',(*track_a,top+150),(*track_b,top+150),
                           cfg['main_cleaning_track_radius_mm'],'#34444B','cleaning_track',
                           dimensions_status='demonstration_assumption'))
        parts.append(_beam('decks',f'main_cleaning_track_support_{side}',(*track_a,top-80),(*track_a,top+150),
                           32,STEEL,'cleaning_track_support',dimensions_status='demonstration_assumption'))
    parts.append(_loft('decks','main_roof_cover',[_section(top-120,roof_ring),_section(top,roof_ring)],WHITE,'deck_roof'))
    return parts


def _top_deck(p, deck, ring, cfg):
    """Fine circular H23 envelope and a separate open H24 service platform.

    H23 is a historical structural/roof datum, not the operator's current
    nominal250m finished-floor height. Local trim, H24 and dish sizes are fits.
    """
    parts=[];half=deck['half_width_mm'];low=deck['bottom_mm']
    glass=deck['glass_bottom_mm'];top=deck['top_mm'];count=cfg['top_facets']
    if count<8 or count%8:raise ValueError('Top deck facets must be a multiple of eight.')
    shape=lambda factor:_circle(half*factor,count)
    lower=shape(cfg['top_lower_radius_factor']);outer=shape(cfg['top_glass_radius_factor'])
    glass_top=top-cfg['top_glass_top_offset_mm'];upper=shape(1.015);roof=shape(cfg['top_roof_radius_factor'])
    support_z=deck['support_mm'];support_ring=_upper_frame_ring(ring,support_z)
    for side in range(4):
        parts.append(_beam('decks',f'top_support_ring_{side}',(*support_ring[side],support_z),
                           (*support_ring[(side+1)%4],support_z),170,WHITE,'deck_support_ring'))
    _deck_shell_band(parts,'top_apron',lower,outer,low,glass,'#E5E6DF','deck_apron')
    _deck_brackets(parts,deck,lower,support_ring)
    z=deck['level_mm']
    parts.append(_loft('decks','top_reference_floor',[_section(z-300,shape(.95)),_section(z,shape(.95))],
                       '#E1DCCE','deck_floor'))
    _deck_shell_band(parts,'top_upper_equipment_band',upper,upper,glass_top,top-650.,WHITE,'deck_equipment_band')
    _deck_shell_band(parts,'top_crown',upper,roof,top-650.,top,WHITE,'deck_crown')
    for station,radius_factor,height in [('lower',1.035,glass-180),('upper',1.045,glass_top+300)]:
        points=shape(radius_factor)
        for side,(a,b) in enumerate(zip(points,points[1:]+points[:1])):
            parts.append(_beam('decks',f'top_equipment_ring_{station}_{side}',(*a,height),(*b,height),
                               65,WHITE,'deck_equipment_ring',dimensions_status='demonstration_assumption'))
    for side,(a,b) in enumerate(zip(outer,outer[1:]+outer[:1])):
        parts.append(_edge_panel('decks',f'top_glazing_{side}_0_0',a,b,glass,glass_top,70,
                                 cfg['top_glass_color'],upper_scale=1.015,role='glazing'))
        parts.append(_beam('decks',f'top_mullion_{side}_0',(*a,glass),(*[v*1.015 for v in a],glass_top),
                           cfg['top_mullion_radius_mm'],WHITE,'window_frame'))
        for transom,height in enumerate((glass+380,glass_top-380)):
            scale=1+.015*(height-glass)/(glass_top-glass)
            parts.append(_edge_panel('decks',f'top_transom_{side}_{transom}',
                                     [v*scale for v in a],[v*scale for v in b],height,height+45,85,
                                     WHITE,role='window_frame'))
        end=roof[(side+1)%count]
        parts.append(_beam('decks',f'top_crown_connector_{side}',
                           (*[v*1.045 for v in a],glass_top+300),
                           (*end,top-120),45,WHITE,'deck_crown_connector',
                           dimensions_status='demonstration_assumption'))
        parts.append(_beam('decks',f'top_lower_ring_connector_{side}',
                           (*lower[side],low),(*[v*1.035 for v in a],glass-180),45,WHITE,'deck_lower_ring_connector',
                           dimensions_status='demonstration_assumption'))
    parts.append(_loft('decks','top_roof_cover',[_section(top-120,roof),_section(top,roof)],WHITE,'deck_roof'))
    parts.extend(_top_service_platform(p,ring,cfg))
    return parts


def _annular_strips(group,name,inner,outer,z0,z1,color,role,count=48,**metadata):
    parts=[]
    for i in range(count):
        a,b=2*pi*i/count,2*pi*(i+1)/count
        points=[[r*cos(t),r*sin(t)] for r,t in ((inner,a),(outer,a),(outer,b),(inner,b))]
        parts.append(_loft(group,f'{name}_{i:02d}',[_section(z0,points),_section(z1,points)],color,role,**metadata))
    return parts


def _top_service_platform(p,ring,cfg):
    """An open annular platform above H23, with supported dishes and railings."""
    parts=[];z=cfg['top_service_platform_mm'];outer=cfg['top_service_radius_mm']
    inner=cfg['top_service_inner_radius_mm'];rail=z+cfg['top_service_rail_height_mm']
    parts.extend(_annular_strips('decks','top_service_platform',inner,outer,z-180,z,WHITE,
                                'service_platform',dimensions_status='image_fit'))
    circle=_circle(outer,48)
    for side,(a,b) in enumerate(zip(circle,circle[1:]+circle[:1])):
        for tier,height in enumerate((z+550,rail)):
            parts.append(_beam('decks',f'top_service_guard_{side}_{tier}',(*a,height),(*b,height),35,WHITE,'service_guard'))
        if side%2==0:
            parts.append(_beam('decks',f'top_service_post_{side}',(*a,z-90),(*a,rail),40,WHITE,'service_guard'))
    for side in range(8):
        theta=pi/4+2*pi*side/8;dx,dy=cos(theta),sin(theta)
        q=_upper_frame_ring(ring,z-90);half=abs(q[0][0]);k=half/max(abs(dx),abs(dy))
        parts.append(_beam('decks',f'top_service_spoke_{side}',(k*dx,k*dy,z-90),
                           (outer*dx,outer*dy,z-90),110,WHITE,'service_platform_support'))
        if side%2==0:
            anchor=_upper_frame_ring(ring,z-4500)[side//2]
            parts.append(_beam('decks',f'top_service_strut_{side}',(*anchor,z-4500),
                               (outer*cos(pi*5/4+side*pi/4),outer*sin(pi*5/4+side*pi/4),z-90),
                               110,WHITE,'service_platform_support'))
    # Four modest outward-facing reflectors are an appearance fit, not an
    # assertion of current equipment count, station use or pointing azimuth.
    for dish in range(4):
        theta=pi/4+dish*pi/2;normal=[cos(theta),sin(theta),0.];tangent=[-sin(theta),cos(theta),0.]
        center=[6200*cos(theta),6200*sin(theta),z+2100]
        anchor=_upper_frame_ring(ring,center[2])[(dish+2)%4]
        parts.append(_beam('decks',f'top_service_dish_mount_{dish}',(*anchor,center[2]),center,85,WHITE,'dish_mount'))
        def point(radius,angle,back=0.):
            depth=150*(radius/550)**2+back
            return [center[k]+normal[k]*depth+tangent[k]*radius*cos(angle)+(radius*sin(angle) if k==2 else 0) for k in range(3)]
        for sector in range(12):
            a,b=2*pi*sector/12,2*pi*(sector+1)/12
            front=[point(r,t) for r,t in ((25,a),(550,a),(550,b),(25,b))]
            back=[point(r,t,-35) for r,t in ((25,a),(550,a),(550,b),(25,b))]
            parts.append({'group':'decks','name':f'decks:top_service_dish_{dish}_{sector}','kind':'loft3d',
                          'sections':[back,front],'color':WHITE,'role':'service_dish','dimensions_status':'image_fit'})
        parts.append(_beam('decks',f'top_service_dish_feed_{dish}',center,
                           [center[k]+normal[k]*380 for k in range(3)],35,STEEL,'dish_feed'))
    return parts


def _decks(p, ring):
    cfg={**DECK_APPEARANCE_DEFAULTS,**p['detail'].get('deck_appearance',{})}
    parts=[]
    for deck in p['deck_specs']:
        parts.extend(_main_deck(p,deck,ring,cfg) if deck['id']=='main' else _top_deck(p,deck,ring,cfg))
    return parts


def _digital_antenna_panels(p, paint, cfg):
    """Two circular five-tier arrays following the supplier's2012 Fig5.

    Published diameters/heights and300 panels are distinct from the fitted
    absolute elevation, shell thickness, seam gaps, supporting steel and MX
    short arrays. Historic station names do not assert present operating use.
    """
    parts=[];bottom=cfg['digital_panel_bottom_mm'];height=cfg['digital_group_height_mm']
    gap=cfg['digital_group_gap_mm'];columns=cfg['digital_panel_columns'];rows=cfg['digital_panel_rows']
    if columns!=30 or rows!=5:raise ValueError('Published Tokyo arrays require30 panels per row and5 rows per group.')
    if not 0<bottom<bottom+2*height+gap+1000<=p['antenna_start_mm']:
        raise ValueError('Digital arrays and1m top frame must remain below H27.')
    half_gap=cfg['digital_panel_azimuth_gap_degrees']*pi/360
    wall=cfg['digital_panel_depth_mm'];row_gap=cfg['digital_panel_gap_mm']
    if not 0<wall<500 or not 0<=row_gap<height/rows or not 0<=half_gap<pi/columns:
        raise ValueError('Panel thickness or seam exceeds its array cell.')
    def ring_at(z):return _upper_frame_ring(lambda value:_square(body_radius(p,value)),z)
    for bank,(z0,diameter,color) in enumerate(((bottom,cfg['digital_lower_diameter_mm'],WHITE),
                                             (bottom+height+gap,cfg['digital_upper_diameter_mm'],ORANGE))):
        radius=diameter/2
        for col in range(columns):
            a,b=2*pi*col/columns+half_gap,2*pi*(col+1)/columns-half_gap
            points=[[r*cos(t),r*sin(t)] for r,t in ((radius-wall,a),(radius,a),(radius,b),(radius-wall,b))]
            for row in range(rows):
                za=z0+row*height/rows+row_gap/2;zb=z0+(row+1)*height/rows-row_gap/2
                parts.append(_loft('antenna',f'digital_panel_{bank}_{col:02d}_{row}',
                                   [_section(za,points),_section(zb,points)],color,'digital_antenna_panel',
                                   panel_bank=bank,panel_column=col,panel_row=row,
                                   published_diameter_mm=diameter,published_group_height_mm=height,
                                   dimensions_status='published envelope; fitted shell thickness, seams and absolute elevation'))
        support=cfg['digital_support_diameter_mm']/2
        for tier in range(rows+1):
            z=z0+tier*height/rows
            # Face-midpoint chords are inset slightly; the radial width overlaps
            # the panel wall while retaining the empty central tower volume.
            parts.extend(_annular_strips('antenna',f'digital_rail_{bank}_{tier}',support-90,radius-35,
                                        z-45,z+45,color,'digital_antenna_rail',count=30))
        for station,z in enumerate((z0+35,z0+height-35)):
            actual=ring_at(z)
            for side,anchor in enumerate(actual):
                theta=pi*5/4+side*pi/2;target=[(support+50)*cos(theta),(support+50)*sin(theta),z]
                parts.append(_beam('antenna',f'digital_bracket_{bank}_{station}_{side}',(*anchor,z),target,
                                   110,WHITE,'digital_antenna_bracket',attachment_points=[[*anchor,z],target],
                                   target_member=f'antenna:digital_rail_{bank}_{0 if station==0 else rows}_{int((theta%(2*pi))/(2*pi/30)):02d}',
                                   dimensions_status='image_fit'))
        # A small open triangular head follows Fig5, not an extra opaque cap.
        if bank==1:
            z=z0+height
            for side,anchor in enumerate(ring_at(z+45)):
                parts.append(_beam('antenna',f'digital_top_head_{side}',(*anchor,z+45),(0,0,z+1000),
                                   80,ORANGE,'digital_array_head'))
    # Two short lower rings preserve the photograph's separate narrow layer.
    radius=cfg['mx_panel_radius_mm'];count=30
    for row in range(2):
        za=cfg['mx_panel_bottom_mm']+row*cfg['mx_panel_row_pitch_mm'];zb=za+cfg['mx_panel_height_mm']
        for col in range(count):
            a,b=2*pi*(col+.12)/count,2*pi*(col+.88)/count
            points=[[r*cos(t),r*sin(t)] for r,t in ((radius-180,a),(radius,a),(radius,b),(radius-180,b))]
            parts.append(_loft('antenna',f'mx_short_panel_{row}_{col:02d}',[_section(za,points),_section(zb,points)],
                               WHITE,'short_antenna_panel',dimensions_status='image_fit; historic envelope only'))
        parts.extend(_annular_strips('antenna',f'mx_support_ring_{row}',5500,radius-80,za-40,za+50,WHITE,
                                    'short_antenna_support',count=30))
        for side,anchor in enumerate(ring_at(za)):
            theta=pi*5/4+side*pi/2
            parts.append(_beam('antenna',f'mx_support_spoke_{row}_{side}',(*anchor,za),
                               (5600*cos(theta),5600*sin(theta),za),95,WHITE,'short_antenna_support'))
    return parts


def _antenna(p,paint):
    cfg={**ANTENNA_APPEARANCE_DEFAULTS,**p['detail'].get('antenna_appearance',{})}
    start,split,end=p['antenna_start_mm'],p['antenna_lattice_top_mm'],p['height_mm']
    parts=_digital_antenna_panels(p,paint,cfg)
    # The SG internal lattice and the later exterior reinforcement are distinct.
    # Miyaji No28 Fig2 establishes this topology, not these assumed bar sizes.
    step=cfg['sg_bay_height_mm'];levels=[start];z=start+step
    while z<split:
        levels.append(z);z+=step
    levels.append(split)
    def radius(z):
        return cfg['sg_inner_half_width_low_mm']+(cfg['sg_inner_half_width_high_mm']-cfg['sg_inner_half_width_low_mm'])*(z-start)/(split-start)
    offset=cfg['sg_outer_offset_mm']
    # H27 has an explicit path from the tower body into the SG exterior frame.
    # These short links mark the published transfer/damper zone schematically;
    # they do not represent a calculated lock or damping mechanism.
    body=_square(body_radius(p,start));base_outer=_square(radius(start)+offset)
    for side in range(4):
        parts.append(_beam('antenna',f'h27_transfer_link_{side}',(*body[side],start),(*base_outer[side],start),
                           110,paint(start),'antenna_h27_transfer_link',
                           target_member=f'antenna:reinforcement_chord_{side}_0',
                           dimensions_status='demonstration_assumption'))
    for index,(za,zb) in enumerate(zip(levels,levels[1:])):
        a,b=_square(radius(za)),_square(radius(zb));outer_a,outer_b=_square(radius(za)+offset),_square(radius(zb)+offset)
        color=paint((za+zb)/2)
        for side in range(4):
            nxt=(side+1)%4
            parts.append(_beam('antenna',f'support_chord_{side}_{index}',(*a[side],za),(*b[side],zb),
                               cfg['sg_inner_chord_radius_mm'],color,'antenna_support_chord',
                               dimensions_status='demonstration_assumption'))
            for direction,(q,r) in enumerate(((a[side],b[nxt]),(a[nxt],b[side]))):
                parts.append(_beam('antenna',f'support_lacing_{side}_{index}_{direction}',(*q,za),(*r,zb),
                                   cfg['sg_inner_brace_radius_mm'],color,'antenna_support_lacing'))
            parts.append(_beam('antenna',f'support_tie_{side}_{index}',(*b[side],zb),(*b[nxt],zb),50,color,'antenna_support_tie'))
            parts.append(_beam('antenna',f'reinforcement_chord_{side}_{index}',(*outer_a[side],za),(*outer_b[side],zb),
                               cfg['sg_outer_chord_radius_mm'],color,'antenna_reinforcement_chord',
                               dimensions_status='demonstration_assumption'))
            for direction,(q,r) in enumerate(((outer_a[side],outer_b[nxt]),(outer_a[nxt],outer_b[side]))):
                parts.append(_beam('antenna',f'reinforcement_brace_{side}_{index}_{direction}',(*q,za),(*r,zb),
                                   cfg['sg_outer_brace_radius_mm'],color,'antenna_reinforcement_brace'))
            parts.append(_beam('antenna',f'reinforcement_tie_{side}_{index}',(*outer_b[side],zb),(*outer_b[nxt],zb),
                               60,color,'antenna_reinforcement_tie'))
    # Each ring station has two layers of radial ties, with no duplicate bars.
    layer=cfg['sg_link_layer_offset_mm']
    for station,z in enumerate(levels):
        zs=(z+layer,z+3*layer) if station==0 else (z-3*layer,z-layer) if station==len(levels)-1 else (z-layer,z+layer)
        for tier,height in enumerate(zs):
            index=next(i for i,(za,zb) in enumerate(zip(levels,levels[1:])) if za<=height<=zb)
            inner,outer=_square(radius(height)),_square(radius(height)+offset)
            for side in range(4):
                parts.append(_beam('antenna',f'sg_radial_link_{station}_{tier}_{side}',
                                   (*inner[side],height),(*outer[side],height),cfg['sg_link_radius_mm'],paint(height),
                                   'antenna_radial_link',
                                   linked_chords=[f'antenna:support_chord_{side}_{index}',f'antenna:reinforcement_chord_{side}_{index}'],
                                   dimensions_status='demonstration_assumption'))
    # The post-2014 ST is a 450mm BOX rather than the previous tapered circle.
    # Only its outer 450mm dimension is published; the wall is an assumption.
    paint_edges={125000+i*(333000-125000)/7 for i in range(8)}
    edges=sorted({split,end}|{z for z in paint_edges if split<z<end})
    for index,(za,zb) in enumerate(zip(edges,edges[1:]),1):
        parts.append({'group':'antenna','name':f'antenna:mast_{index:02d}','kind':'rhs',
                      'start':[0.,0.,za],'end':[0.,0.,zb],'width_mm':cfg['st_width_mm'],
                      'depth_mm':cfg['st_depth_mm'],'wall_thickness_mm':cfg['st_wall_mm'],
                      'color':paint((za+zb)/2),'role':'antenna_mast',
                      'section_reference':'Miyaji No28 p66: replacement ST BOX 450mm',
                      'wall_dimensions_status':'demonstration_assumption'})
    equipment_half=cfg['st_equipment_half_width_mm']
    for index,z in enumerate(cfg['st_equipment_levels_mm']):
        if not split+300<z<end-500:raise ValueError('ST equipment must stay within the published tip controls.')
        inner=_square(max(cfg['st_width_mm'],cfg['st_depth_mm'])/2);outer=_square(equipment_half)
        for side in range(4):
            parts.append(_beam('antenna',f'st_equipment_arm_{index}_{side}',(*inner[side],z),(*outer[side],z),
                               30,paint(z),'antenna_equipment_arm',dimensions_status='demonstration_assumption'))
            a,b=outer[side],outer[(side+1)%4]
            parts.append(_beam('antenna',f'st_equipment_element_{index}_{side}',(*a,z),(*b,z),
                               22,paint(z),'antenna_equipment_element',dimensions_status='demonstration_assumption'))
        # A square annulus surrounds the BOX without plugging its real bore.
        collar_width=max(cfg['st_width_mm'],cfg['st_depth_mm'])+170.
        parts.append({'group':'antenna','name':f'antenna:st_insulator_collar_{index}','kind':'rhs',
                      'start':[0.,0.,z-80],'end':[0.,0.,z+80],
                      'width_mm':collar_width,'depth_mm':collar_width,'wall_thickness_mm':85.,
                      'color':'#E8E4D7','role':'antenna_insulator_collar',
                      'dimensions_status':'demonstration_assumption'})
    return parts


def _lights(p):
    parts=[]
    for index,(sx,sy) in enumerate(((-1,-1),(1,-1),(1,1),(-1,1)),1):
        x,y=sx*33000,sy*33000
        parts.append(_box('base',f'foot_uplight_housing_{index}',(x-650,y-450,1100,x+650,y+450,1800),STEEL,'light_housing',detail_level='micro'))
        parts.append(_box('base',f'foot_uplight_light_lens_{index}',(x-540,y-340,1800,x+540,y+340,1850),WARM,'light_lens',detail_level='micro'))
    c=_base_config(p);face=-c['foot_town_depth_mm']/2
    pitch=c['foot_town_width_mm']/c['foot_town_bays_per_face']
    for index,x in enumerate((-pitch,pitch),1):
        parts.append(_box('base',f'entry_wall_light_housing_{index}',(x-220,face-350,2700,x+220,face+100,3700),STEEL,'light_housing',detail_level='micro'))
        parts.append(_box('base',f'entry_wall_light_lens_{index}',(x-160,face-390,2800,x+160,face-340,3600),WARM,'light_lens',detail_level='micro'))
    deck_cfg={**DECK_APPEARANCE_DEFAULTS,**p['detail'].get('deck_appearance',{})}
    for deck in p['deck_specs']:
        ident=deck['id'];h=deck['half_width_mm']*.75;z=deck['top_mm']+180
        if ident=='top':
            # The crown is circular, so square-corner coordinates must be
            # derived from a radius inside its real roof polygon.
            h=deck['half_width_mm']*deck_cfg['top_roof_radius_factor']*.82/(2**.5)
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
