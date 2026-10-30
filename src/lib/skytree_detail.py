"""Source-guided R05 Skytree appearance detail in millimetres.

Published heights and the referenced triangular/circular controls guide this
concept. The interpolation, member layout, deck radii, gallery turn count,
route, connections and light positions are modelling assumptions, not measured
original CAD or structural design. Role-based pipe ranges do not identify the
original section of each member. The gallery is a continuous ramp, not stairs.
Only the RC shinbashira is called a central column; the upper guide frame is a
separate schematic element. All primitives share the CAD/drawing specification.
"""
from __future__ import annotations

from math import cos, sin, pi, hypot, tan, sqrt

WHITE = '#E3E9E7'
SHADOW = '#A6B6C0'
STEEL = '#657B89'
GLASS = '#7295A8'
WARM = '#D4F6FF'

# Role-based appearance ranges, not a member-by-member original section table.
SKYTREE_FRAME_DEFAULTS={
    'connection_height_mm':50000.,'ring_spacing_mm':12500.,'radial_spacing_mm':25000.,
    'body_top_mm':497000.,'ring_bays':12,'group_width_mm':4000.,'group_depth_mm':8000.,
    # Only the 315 m change and upper 5 m pitch are design-source controls.
    # Intermediate switching heights below 315 m are configurable examples.
    'ring_tiers_mm':[[0.,12500.],[150000.,10000.],[250000.,7500.],[315000.,5000.]],
    'ring_tier_scope':'12.5/10/7.5 m lower pitches; 150/250 m switches are illustrative, not disclosed construction levels; 5 m above 315 m.',
    'ring_depth_low_mm':2200.,'ring_depth_high_mm':1200.,'chunk_intervals':7,'ring_web_stride':4,
    'group_diameter_ground_mm':2300.,'group_diameter_50m_mm':1800.,'group_diameter_315m_mm':1100.,
    'group_diameter_top_mm':1016.,'group_wall_ground_mm':100.,'group_wall_top_mm':60.,
    'outer_diameter_low_mm':1100.,'outer_diameter_high_mm':1016.,
    'outer_wall_low_mm':25.,'outer_wall_high_mm':60.,
    'brace_diameter_mm':508.,'brace_wall_mm':25.,'group_brace_diameter_mm':600.,'group_brace_wall_mm':28.,
    'horizontal_diameter_mm':406.4,'horizontal_wall_mm':16.,
    'outer_horizontal_diameter_mm':406.4,'outer_horizontal_wall_mm':16.,
    'ring_rhs_width_mm':400.,'ring_rhs_depth_mm':400.,'ring_rhs_wall_mm':12.,
    'radial_rhs_width_mm':500.,'radial_rhs_depth_mm':500.,'radial_rhs_wall_mm':12.,
    'middle_radius_mm':6200.,'middle_top_radius_mm':3200.,'middle_diameter_mm':355.6,'middle_wall_mm':16.,
}
SKYTREE_BASE_WING_DEFAULTS={
    'enabled':True,'root_attachment_height_mm':750.,'top_attachment_inset_mm':100.,
    'panel_levels_mm':[12500.,25000.,37500.],'fan_curve_factor':.35,
    'chord_diameter_mm':1016.,'chord_wall_mm':40.,
    'horizontal_diameter_mm':406.4,'horizontal_wall_mm':16.,
    'brace_diameter_mm':508.,'brace_wall_mm':25.,'tie_axis_inset_mm':300.,
    'scope':'Broad steel wings on three faces grow from the existing four-column kanae feet and leave central pointed-arch pedestrian openings. Fan axes, 12.5 m modelling panels, wall attachments and section sizes are CG/photo-guided appearance assumptions, not recovered as-built joints or structural design.',
}
SKYTREE_GAIN_DEFAULTS={
    'interface_mm':497000.,'lattice_start_mm':497000.,'top_mm':634000.,'top_tie_mm':620000.,
    'column_count':6,'bay_height_mm':10000.,'column_diameter_low_mm':1200.,'column_diameter_high_mm':900.,
    'column_wall_low_mm':80.,'column_wall_high_mm':50.,'brace_diameter_mm':300.,'brace_wall_mm':22.,
    'ring_width_mm':300.,'ring_depth_mm':300.,'ring_wall_mm':12.,
    'bridge_start_mm':493000.,'bridge_end_mm':500500.,'bridge_diameter_mm':900.,'bridge_wall_mm':35.,
    # Centre axes, not the external diameter: add the 0.60/0.45 m tube radius.
    'radius_controls_mm':[[497000.,2400.],[507000.,2400.],[620000.,2550.]],
    'equipment_banks_mm':[[506000.,527000.,3500.],[537000.,556000.,3500.],
                          [579000.,587500.,3400.],[589000.,597500.,3400.],
                          [599000.,607500.,3400.],[609000.,617500.,3400.]],
    'equipment_faces':20,'equipment_rows':4,'equipment_belt_stride':2,'equipment_skin_mm':80.,
    'maintenance_levels_mm':[527000.,530000.,556000.,570000.,587500.,597500.,607500.,610000.,617500.],
    'maintenance_radius_mm':4100.,'maintenance_thickness_mm':140.,
    'tmd_bottom_mm':620000.,'tmd_middle_mm':626000.,'tmd_roof_mm':632500.,
    'tmd_radius_mm':4200.,'tmd_inner_radius_mm':3500.,'tmd_flange_radius_mm':4600.,
    'lightning_rod_radius_mm':130.,
    'equipment_scope':'Bank bounds, panel subdivision, platforms and TMD section sizes are photo-guided appearance estimates; no internal vibration mechanism is simulated.',
}

SKYTREE_DECK_DEFAULTS={
    'facade_angle_deg':71.,'radius_at350_mm':23500.,'facade_bottom_mm':335000.,'facade_top_mm':355000.,
    'facade_glass_zones_mm':[[335000.,337200.],[340000.,342400.],[345000.,347400.],[350000.,355000.]],
    'opaque_stations_mm':[[355000.,25222.],[369000.,29000.],[371000.,28900.]],
    'roof_level_mm':371000.,'roof_radius_mm':28900.,'roof_thickness_mm':350.,
    'crown_bottom_mm':371000.,'crown_top_mm':375000.,'crown_radius_mm':16000.,
    'bottom_mm':333000.,'bottom_radius_mm':16500.,'skin_mm':180.,'glass_mm':80.,
    'panels':48,'floor_inner_radius_mm':6000.,
    'appearance_scope':'71 degree outward glazing and approximate 47 m diameter at H350 follow designer controls; the designer describes the upper mouth as approximately 60 m. Opaque-band/crown sections remain image-based estimates, with published rooftop H375. The low service glazing strip is not a fourth public floor.',
}

SKYTREE_GALLERIA_DEFAULTS={
    'start_mm':445000.,'end_mm':450000.,'sorakara_level_mm':451200.,
    'path_length_mm':114000.,'segments':44,'clear_width_mm':2400.,
    'body_radius_controls_mm':[[438000.,11800.],[445000.,15600.],[455000.,18800.]],
    'facade_top_mm':455000.,'apron_top_mm':445000.,'roof_thickness_mm':350.,
    'crown_top_mm':460000.,'crown_radius_mm':12000.,'floor_inner_radius_mm':5000.,
    'floor_thickness_mm':300.,'glass_mm':80.,'skin_mm':180.,
    'tube_height_mm':3100.,'tube_bulge_mm':320.,'tube_arch_panels':4,
    'upper_route_segments':12,'upper_route_angle_rad':pi*.70,'upper_route_centre_radius_mm':15100.,
    'route_scope':'Designer route approximately 114 m; external-panel contractor approximately 110 m and approximately 40 m diameter/2.4 m clear width. Radius profile, azimuth and sectional tube are photo-guided approximations, not a surveyed as-built route.',
}

SKYTREE_LIGHT_DEFAULTS={
    'body_levels_mm':[90000.,180000.,270000.,495000.],
    'deck_roof_levels_mm':[371000.,375000.],
    'galleria_roof_level_mm':455000.,'gain_platform_levels_mm':[530000.,570000.,610000.],
    'tmd_roof_level_mm':632500.,'lens_half_mm':150.,'post_height_mm':300.,
    'scope':'Eleven controller lenses retained at illustrative exposed supports; not an obstruction-lighting compliance layout.',
}


def _frame_config(p):return {**SKYTREE_FRAME_DEFAULTS,**p.get('detail',{}).get('frame',{})}
def _base_wing_config(p):return {**SKYTREE_BASE_WING_DEFAULTS,**p.get('detail',{}).get('base_wings',{})}
def _gain_config(p):return {**SKYTREE_GAIN_DEFAULTS,**p.get('detail',{}).get('gain',{})}
def _deck_config(p):return {**SKYTREE_DECK_DEFAULTS,**p.get('detail',{}).get('tembo_deck',{})}
def _galleria_config(p):return {**SKYTREE_GALLERIA_DEFAULTS,**p.get('detail',{}).get('galleria',{})}
def _light_config(p):return {**SKYTREE_LIGHT_DEFAULTS,**p.get('detail',{}).get('lights',{})}


def _tube(group,name,a,b,diameter,wall,color,role,**data):
    return _spec(group,name,'tube',color,role,start=list(a),end=list(b),radius=diameter/2,
                 wall_thickness_mm=wall,**data)


def _rhs(group,name,a,b,width,depth,wall,color,role,**data):
    return _spec(group,name,'rhs',color,role,start=list(a),end=list(b),width_mm=width,depth_mm=depth,
                 wall_thickness_mm=wall,**data)


def _tube_loft(group,name,sections,color,role,**data):
    return _spec(group,name,'tube_loft',color,role,sections=sections,
                 section_scope='Horizontal circular annuli on interpolated centres; inclined wall sections are schematic.',**data)


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
    c=_frame_config(p);top=c['body_top_mm'];tiers=sorted(c['ring_tiers_mm'])
    stations={0.,top,c['connection_height_mm']}
    for index,(bottom,step) in enumerate(tiers):
        end=min(top,tiers[index+1][0] if index+1<len(tiers) else top)
        if step<=0 or bottom<0:raise ValueError('Frame tiers require positive pitches and nonnegative levels.')
        if bottom>top:continue
        stations.update(bottom+i*step for i in range(int((end-bottom)/step)+1))
        stations.add(end)
    stations.update(float(z) for z,_ in p['profile'] if 0<=z<=top)
    return sorted(stations)


def _group_nodes():return {index for vertex in (0,8,16) for index in ((vertex-1)%24,vertex,(vertex+1)%24)}


def _group_assignment(node):
    for group,vertex in enumerate((0,8,16)):
        if node==vertex:return group,0
        if node==(vertex+1)%24:return group,1
        if node==(vertex-1)%24:return group,3
    return None


def _outer_curve(p,ring,node,z):
    c=_frame_config(p)
    # All twenty-four axes follow the contour. An odd sample is not pulled
    # inward to the midpoint of a coarser twelve-sided structural ring.
    target=ring(z)[node]
    assignment=_group_assignment(node)
    if z>=c['connection_height_mm'] or assignment is None:return target
    group,chord=assignment;vertex=group*8;v=ring(z)[vertex];r=hypot(*v);u=[v[0]/r,v[1]/r];t=[-u[1],u[0]]
    if chord==0:return v
    start=[v[k]-u[k]*c['group_depth_mm']/2+t[k]*c['group_width_mm']/2*(1 if chord==1 else -1) for k in range(2)]
    amount=z/c['connection_height_mm'];amount=amount*amount*(3-2*amount)
    return [start[k]*(1-amount)+target[k]*amount for k in range(2)]


def _ring_depth(p,z):
    c=_frame_config(p);t=max(0.,min(1.,(z-c['connection_height_mm'])/(c['body_top_mm']-c['connection_height_mm'])))
    return c['ring_depth_low_mm']*(1-t)+c['ring_depth_high_mm']*t


def _inner_curve(p,ring,group,z):
    c=_frame_config(p);v=ring(z)[group*8];r=hypot(*v)
    depth=_ring_depth(p,z)
    if z<c['connection_height_mm']:
        t=z/c['connection_height_mm'];depth=c['group_depth_mm']*(1-t)+c['ring_depth_low_mm']*t
    return [value*(1-depth/r) for value in v]


def _actual_point(p,ring,node,z,inner_group=None):
    stations=_frame_stations(p)
    for za,zb in zip(stations,stations[1:]):
        if za<=z<=zb:
            t=(z-za)/(zb-za)
            a,b=(_inner_curve(p,ring,inner_group,za),_inner_curve(p,ring,inner_group,zb)) if inner_group is not None else (_outer_curve(p,ring,node,za),_outer_curve(p,ring,node,zb))
            return [a[k]*(1-t)+b[k]*t for k in range(2)]+[z]
    raise ValueError('Frame attachment height is outside the body.')


def _frame_point(p,ring,node,z):
    """Actual generated outer chord axis; below50m alias a real group chord."""
    if z<_frame_config(p)['connection_height_mm'] and node not in _group_nodes():
        target=ring(z)[node]
        candidates=[_actual_point(p,ring,n,z) for n in _group_nodes()]+[_actual_point(p,ring,0,z,g) for g in range(3)]
        return min(candidates,key=lambda v:sum((v[k]-target[k])**2 for k in range(2)))
    return _actual_point(p,ring,node,z)


def _chord_section(p,node,z,inner_group=None):
    c=_frame_config(p)
    if node in _group_nodes() or inner_group is not None:
        controls=[(0,c['group_diameter_ground_mm']),(c['connection_height_mm'],c['group_diameter_50m_mm']),
                  (315000,c['group_diameter_315m_mm']),(c['body_top_mm'],c['group_diameter_top_mm'])]
        diameter=_antenna_radius(controls,z);t=z/c['body_top_mm']
        wall=c['group_wall_ground_mm']*(1-t)+c['group_wall_top_mm']*t
    else:
        t=(z-c['connection_height_mm'])/(c['body_top_mm']-c['connection_height_mm'])
        diameter=c['outer_diameter_low_mm']*(1-t)+c['outer_diameter_high_mm']*t
        wall=c['outer_wall_low_mm']*(1-t)+c['outer_wall_high_mm']*t
    return diameter,wall


def _body(p,ring):
    c=_frame_config(p);parts=[];stations=_frame_stations(p);step=c['ring_spacing_mm'];start=c['connection_height_mm'];top=c['body_top_mm']
    bays=int(c['ring_bays'])
    if bays!=12:raise ValueError('The fixed24-index attachment contract requires12 structural polygon bays.')
    group_nodes=_group_nodes();chunk=int(c['chunk_intervals'])
    for node in range(24):
        levels=stations if node in group_nodes else [z for z in stations if z>=start]
        assignment=_group_assignment(node)
        for index,k in enumerate(range(0,len(levels)-1,chunk),1):
            subset=levels[k:k+chunk+1]
            if len(subset)<2:continue
            sections=[]
            for z in subset:
                diameter,wall=_chord_section(p,node,z);point=_frame_point(p,ring,node,z)
                sections.append({'z':z,'center':point[:2],'radius':diameter/2,'wall_thickness_mm':wall})
            name=f'kanae_{assignment[0]+1:02d}_chord_{assignment[1]:02d}_{index:02d}' if assignment else f'outer_chord_{node:02d}_{index:02d}'
            parts.append(_tube_loft('structure',name,sections,WHITE,'kanae_chord' if assignment else 'outer_chord',
                                    body_node=node,**({'kanae_group':assignment[0],'kanae_chord':assignment[1]} if assignment else {})))
    for group in range(3):
        for index,k in enumerate(range(0,len(stations)-1,chunk),1):
            subset=stations[k:k+chunk+1]
            if len(subset)<2:continue
            sections=[]
            for z in subset:
                diameter,wall=_chord_section(p,0,z,group);point=_actual_point(p,ring,0,z,group)
                sections.append({'z':z,'center':point[:2],'radius':diameter/2,'wall_thickness_mm':wall})
            parts.append(_tube_loft('structure',f'kanae_{group+1:02d}_chord_02_{index:02d}',sections,WHITE,'kanae_chord',
                                    kanae_group=group,kanae_chord=2))
    def group_points(group,z):
        v=group*8
        return [_frame_point(p,ring,v,z),_frame_point(p,ring,(v+1)%24,z),_actual_point(p,ring,0,z,group),_frame_point(p,ring,(v-1)%24,z)]
    # Four-member spatial groups, not three isolated columns with decorative arches.
    lower=[i*step for i in range(int(start/step)+1)]
    for group in range(3):
        for level,z in enumerate(lower):
            points=group_points(group,z)
            for face in range(4):
                parts.append(_tube('structure',f'kanae_{group+1:02d}_horizontal_{level:02d}_{face}',points[face],points[(face+1)%4],
                                   c['horizontal_diameter_mm'],c['horizontal_wall_mm'],WHITE,'kanae_horizontal',kanae_group=group,level_mm=z))
        for level,(za,zb) in enumerate(zip(lower,lower[1:])):
            a,b=group_points(group,za),group_points(group,zb)
            for face in range(4):
                parts.append(_tube('structure',f'kanae_{group+1:02d}_brace_{level:02d}_{face}',a[face],b[(face+1)%4],
                                   c['group_brace_diameter_mm'],c['group_brace_wall_mm'],SHADOW,'kanae_brace',kanae_group=group))
    ring_levels=[z for z in stations if z>=start]
    # The exterior has all 24 real axes. The 12-sided inner ring and three
    # sparse diagonal webs are deliberate plan-depth modelling reductions.
    for level,z in enumerate(ring_levels):
        outer=[_frame_point(p,ring,node,z) for node in range(24)];inner=[]
        for point in outer[::2]:
            r=hypot(*point[:2]);inner.append([point[0]*(1-_ring_depth(p,z)/r),point[1]*(1-_ring_depth(p,z)/r),z])
        for node in range(24):
            parts.append(_tube('structure',f'ring_truss_{level:02d}_{node:02d}_outer',outer[node],outer[(node+1)%24],
                              c['outer_horizontal_diameter_mm'],c['outer_horizontal_wall_mm'],WHITE,'outer_horizontal',
                              level_mm=z,terminal_interface=z==top,ring_layer='outer',body_node=node))
        for bay in range(bays):
            nxt=(bay+1)%bays
            parts.append(_rhs('structure',f'ring_truss_{level:02d}_{bay:02d}_inner',inner[bay],inner[nxt],
                              c['ring_rhs_width_mm'],c['ring_rhs_depth_mm'],c['ring_rhs_wall_mm'],WHITE,'ring_truss',
                              level_mm=z,terminal_interface=z==top,ring_layer='inner'))
            if bay%int(c['ring_web_stride'])==0:
                parts.append(_rhs('structure',f'ring_truss_{level:02d}_{bay:02d}_web',outer[bay*2],inner[nxt],
                                  c['ring_rhs_width_mm'],c['ring_rhs_depth_mm'],c['ring_rhs_wall_mm'],WHITE,'ring_truss',
                                  level_mm=z,terminal_interface=z==top,ring_layer='web',scope='Sparse appearance-model web, not original member-by-member framing.'))
    for level,(za,zb) in enumerate(zip(ring_levels,ring_levels[1:])):
        for node in range(24):
            a=_frame_point(p,ring,node if level%2==0 else (node+1)%24,za)
            b=_frame_point(p,ring,(node+1)%24 if level%2==0 else node,zb)
            parts.append(_tube('structure',f'outer_brace_{level:02d}_{node:02d}',a,b,c['brace_diameter_mm'],c['brace_wall_mm'],SHADOW,'body_brace'))
    # Above the merge, the three inner group chords still participate in the
    # spatial load path through diagonal faces, on 25 m modelling panels.
    group_levels=sorted(set([start+i*c['radial_spacing_mm'] for i in range(int((top-start)/c['radial_spacing_mm'])+1)]+[top]))
    for group in range(3):
        for level,(za,zb) in enumerate(zip(group_levels,group_levels[1:])):
            a,b=group_points(group,za),group_points(group,zb)
            for face in range(4):
                parts.append(_tube('structure',f'kanae_{group+1:02d}_upper_brace_{level:02d}_{face}',a[face],b[(face+1)%4],
                                   c['brace_diameter_mm'],c['brace_wall_mm'],WHITE,'kanae_brace',kanae_group=group))
    # Six-chord schematic steel middle tower, isolated from the 8 m RC core.
    mid_levels=sorted(set([i*c['radial_spacing_mm'] for i in range(int(top/c['radial_spacing_mm'])+1)]+[top]))
    def middle_radius(z):
        return c['middle_radius_mm'] if z<=375000 else c['middle_radius_mm']+(c['middle_top_radius_mm']-c['middle_radius_mm'])*(z-375000)/(top-375000)
    def middle_point(node,z):
        angle=pi/2+2*pi*node/6;r=middle_radius(z)
        return [r*cos(angle),r*sin(angle),z]
    for node in range(6):
        parts.append(_tube_loft('structure',f'mid_chord_{node:02d}',
                                [{'z':z,'center':middle_point(node,z)[:2],'radius':c['middle_diameter_mm']/2,'wall_thickness_mm':c['middle_wall_mm']} for z in mid_levels],
                                STEEL,'middle_tower'))
    for level,z in enumerate(mid_levels):
        for node in range(6):
            parts.append(_tube('structure',f'mid_ring_{level:02d}_{node}',middle_point(node,z),middle_point((node+1)%6,z),c['horizontal_diameter_mm'],c['horizontal_wall_mm'],STEEL,'middle_tower'))
        if z>=start and abs(z/c['radial_spacing_mm']-round(z/c['radial_spacing_mm']))<1e-6:
            for node in range(6):
                target=_frame_point(p,ring,node*4,z);r=hypot(*target[:2]);target=[target[0]*(1-_ring_depth(p,z)/r),target[1]*(1-_ring_depth(p,z)/r),z]
                parts.append(_rhs('structure',f'horizontal_link_{level:02d}_{node}',middle_point(node,z),target,
                                  c['radial_rhs_width_mm'],c['radial_rhs_depth_mm'],c['radial_rhs_wall_mm'],WHITE,'horizontal_link',level_mm=z))
        if level:
            for node in range(0,6,2):
                parts.append(_tube('structure',f'mid_brace_{level:02d}_{node}',middle_point(node,mid_levels[level-1]),middle_point((node+1)%6,z),c['horizontal_diameter_mm'],c['horizontal_wall_mm'],STEEL,'middle_tower'))
    return parts


def _base_wing_frame(p,ring,body):
    """Wide, open base framing attached to existing hollow steel walls.

    The three four-column groups remain the only ground roots. Each side's
    two fans grow towards the 50 m exterior axes; their inner edges form an
    open pointed arch. No horizontal or diagonal crosses that central opening.
    These photo/CG-guided axes are an appearance layout, not original joints.
    """
    c=_base_wing_config(p)
    if not c['enabled']:return []
    top=_frame_config(p)['connection_height_mm']+c['top_attachment_inset_mm']
    bottom=c['root_attachment_height_mm'];panels=sorted(c['panel_levels_mm'])
    if not 0<bottom<min(panels)<max(panels)<top:raise ValueError('Base wing panels must lie between root and upper attachment.')
    if not 0<=c['fan_curve_factor']<1:raise ValueError('Base wing fan curvature must be monotone.')
    inset=c['tie_axis_inset_mm'];levels=[bottom,*panels,top];parts=[]
    tie_levels=[z+inset for z in panels]+[top-inset]
    if not all(a<b for a,b in zip(tie_levels,tie_levels[1:])):raise ValueError('Base wing tie insets exceed a modelling panel.')
    columns=[part for part in body if part.get('role') in ('kanae_chord','outer_chord') and 'body_node' in part]

    def column(node,z):
        return next(part for part in columns if part['body_node']==node and part['sections'][0]['z']<=z<=part['sections'][-1]['z'])

    def column_wall(node,z,towards):
        axis=_actual_point(p,ring,node,z);diameter,wall=_chord_section(p,node,z)
        dx,dy=towards[0]-axis[0],towards[1]-axis[1];length=hypot(dx,dy)
        # Existing loft sections are horizontal annuli, so this is a real
        # wall point rather than the empty centre of an inclined tube.
        radius=(diameter-wall)/2
        return [axis[0]+radius*dx/length,axis[1]+radius*dy/length,z]

    def tube_wall(axis,direction,radius,wall,towards):
        length=sqrt(sum(v*v for v in direction));unit=[v/length for v in direction]
        delta=[towards[k]-axis[k] for k in range(3)];along=sum(delta[k]*unit[k] for k in range(3))
        radial=[delta[k]-along*unit[k] for k in range(3)];length=sqrt(sum(v*v for v in radial))
        return [axis[k]+radial[k]/length*(radius-wall/2) for k in range(3)]

    for face in range(3):
        for side,root,target_offsets in (('left',(face*8+1)%24,(2,3,4)),
                                          ('right',(face*8+7)%24,(6,5,4))):
            root_group=_group_assignment(root)[0];root_support=column(root,bottom)
            common={'wing_face':face,'wing_side':side,'wing_root_group':root_group,
                    'wing_root_node':root,'kanae_group':root_group,'scope':c['scope']}
            lane_axes={};lane_parts={}
            for lane,offset in enumerate(target_offsets,1):
                target=(face*8+offset)%24;root_axis=_actual_point(p,ring,root,bottom)
                top_axis=_actual_point(p,ring,target,top)
                a=column_wall(root,bottom,top_axis);b=column_wall(target,top,root_axis)
                def fan_point(z):
                    t=(z-bottom)/(top-bottom);weight=t+c['fan_curve_factor']*t*(1-t)
                    return [a[k]*(1-weight)+b[k]*weight for k in range(2)]+[z]
                axes=[fan_point(z) for z in levels];lane_axes[lane]=axes;lane_parts[lane]=[]
                for segment,(aa,bb) in enumerate(zip(axes,axes[1:])):
                    part=_tube('structure',f'base_wing_f{face}_{side}_lane{lane}_chord_{segment}',
                               aa,bb,c['chord_diameter_mm'],c['chord_wall_mm'],WHITE,'base_wing_chord',
                               **common,wing_lane=lane,body_node=target,wing_segment=segment,
                               root_axis_mm=root_axis,top_axis_mm=top_axis,
                               root_support_name=root_support['name'],top_support_name=column(target,top)['name'])
                    lane_parts[lane].append(part);parts.append(part)

            def support(lane,z):
                if lane==0:return _actual_point(p,ring,root,z),column(root,z)
                axes=lane_axes[lane]
                for index,(a,b) in enumerate(zip(axes,axes[1:])):
                    if a[2]<=z<=b[2]:
                        t=(z-a[2])/(b[2]-a[2])
                        return [a[k]*(1-t)+b[k]*t for k in range(3)],lane_parts[lane][index]
                raise ValueError('Base wing tie outside its fan chord.')

            def attachment(lane,z,towards):
                axis,host=support(lane,z)
                if lane==0:return column_wall(root,z,towards),host
                direction=[host['end'][k]-host['start'][k] for k in range(3)]
                return tube_wall(axis,direction,host['radius'],host['wall_thickness_mm'],towards),host

            def tie(role,label,lane_a,z_a,lane_b,z_b,diameter,wall,**extra):
                axis_a,_=support(lane_a,z_a);axis_b,_=support(lane_b,z_b)
                a,host_a=attachment(lane_a,z_a,axis_b);b,host_b=attachment(lane_b,z_b,axis_a)
                parts.append(_tube('structure',f'base_wing_f{face}_{side}_{label}',a,b,diameter,wall,
                                   WHITE if role=='base_wing_horizontal' else SHADOW,role,**common,
                                   wing_lane=lane_b,start_support_name=host_a['name'],end_support_name=host_b['name'],
                                   axis_start_mm=axis_a,axis_end_mm=axis_b,**extra))
            for level,z in enumerate(tie_levels[:-1]):
                for lane in range(3):
                    tie('base_wing_horizontal',f'horizontal_{level}_{lane}',lane,z,lane+1,z,
                        c['horizontal_diameter_mm'],c['horizontal_wall_mm'],level_mm=z)
            # The first panel is already a converging triangular fan, so no
            # duplicate root diagonals are added. All ties stay on one wing.
            for level,(za,zb) in enumerate(zip(tie_levels,tie_levels[1:])):
                for lane in range(3):
                    a,b=(lane,lane+1) if level%2==0 else (lane+1,lane)
                    tie('base_wing_brace',f'brace_{level}_{lane}',a,za,b,zb,
                        c['brace_diameter_mm'],c['brace_wall_mm'],lower_level_mm=za,upper_level_mm=zb)
    return parts


def _base(p,ring):
    parts=[_loft('base','ground_plaza',[_section(-2500,_circle(52000,48)),_section(0,_circle(52000,48))],
                 '#D2CDC3','ground')]
    for group in range(3):
        vertex=group*8
        points=[_frame_point(p,ring,node,0) for node in (vertex,(vertex+1)%24,(vertex-1)%24)]+[_actual_point(p,ring,0,0,group)]
        padding=_frame_config(p)['group_diameter_ground_mm']/2+350
        bounds=[min(v[k] for v in points)-padding for k in range(2)]+[-1500]
        bounds += [max(v[k] for v in points)+padding for k in range(2)]+[1400]
        parts.append(_box('base',f'footing_{group+1}',bounds,'#ADB3B5','foundation_placeholder',scope='Schematic group footing envelope; no foundation design.'))
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


def _shell(group,name,stations,thickness,color,role,n=48,**data):
    """Faceted annular skin; few horizontal controls, no filled central disk."""
    return [_loft(group,f'{name}_{i:02d}',
                  [_section(z,_sector(r-thickness,r,2*pi*i/n,2*pi*(i+1)/n)) for z,r in stations],
                  color,role,**data) for i in range(n)]


def _deck_radius(c,z):
    return c['radius_at350_mm']+(z-350000.)/tan(c['facade_angle_deg']*pi/180)


def _tembo_deck(p,ring):
    c=_deck_config(p);parts=[];n=int(c['panels']);bottom=c['bottom_mm'];skin=c['skin_mm']
    floors=p.get('detail',{}).get('tembo_floors_mm',[340000,345000,350000])
    parts.extend(_shell('decks','tembo_deck_apron',[(bottom,c['bottom_radius_mm']),
                         (c['facade_bottom_mm'],_deck_radius(c,c['facade_bottom_mm']))],skin,WHITE,'deck_apron',n=n))
    for floor,z in enumerate(floors):
        r=_deck_radius(c,z)
        parts.extend(_annulus('decks',f'tembo_deck_floor_{floor+1}',c['floor_inner_radius_mm'],r,z-300,z,
                              '#DDDCD4','deck_floor',n=n,floor_level_mm=z))
        parts.extend(_annulus('decks',f'tembo_deck_belt_{floor+1}',r-300,r+30,z-250,z+100,
                              WHITE,'floor_belt',n=n,floor_level_mm=z))
    zones=c['facade_glass_zones_mm'];cursor=c['facade_bottom_mm']
    for zone,(za,zb) in enumerate(zones):
        if za>cursor:
            parts.extend(_shell('decks',f'tembo_deck_spandrel_{zone}',
                                [(cursor,_deck_radius(c,cursor)),(za,_deck_radius(c,za))],skin,WHITE,'deck_spandrel',n=n))
        for i in range(n):
            a,b=2*pi*(i+.018)/n,2*pi*(i+.982)/n
            parts.append(_loft('decks',f'tembo_deck_glazing_{zone}_{i:02d}',
                               [_section(z,_sector(_deck_radius(c,z)-c['glass_mm'],_deck_radius(c,z),a,b)) for z in (za,zb)],
                               GLASS,'glazing',finish='glass',thickness_mm=c['glass_mm'],facade_angle_deg=c['facade_angle_deg'],
                               facade_band='lower_service' if zone==0 else 'public_floor_glazing'))
        cursor=zb
    for i in range(n):
        a=2*pi*i/n
        parts.append(_beam('decks',f'tembo_deck_mullion_{i:02d}',
                           (_deck_radius(c,c['facade_bottom_mm'])*cos(a),_deck_radius(c,c['facade_bottom_mm'])*sin(a),c['facade_bottom_mm']),
                           (_deck_radius(c,c['facade_top_mm'])*cos(a),_deck_radius(c,c['facade_top_mm'])*sin(a),c['facade_top_mm']),
                           75,WHITE,'window_frame'))
    opaque=[list(v) for v in c['opaque_stations_mm']]
    opaque[0]=[c['facade_top_mm'],_deck_radius(c,c['facade_top_mm'])]
    parts.extend(_shell('decks','tembo_deck_equipment_apron',opaque,skin,WHITE,'deck_equipment_enclosure',n=n,
                         scope=c['appearance_scope']))
    roof=c['roof_level_mm']
    parts.extend(_annulus('decks','tembo_deck_roof',c['floor_inner_radius_mm'],c['roof_radius_mm'],
                          roof-c['roof_thickness_mm'],roof,WHITE,'deck_roof',n=n,roof_level_mm=roof))
    parts.extend(_shell('decks','tembo_deck_equipment_crown',
                         [(c['crown_bottom_mm'],c['crown_radius_mm']),(c['crown_top_mm'],c['crown_radius_mm'])],
                         skin,WHITE,'deck_equipment_crown',n=24))
    parts.extend(_annulus('decks','tembo_deck_crown_roof',c['floor_inner_radius_mm'],c['crown_radius_mm'],
                          c['crown_top_mm']-c['roof_thickness_mm'],c['crown_top_mm'],WHITE,'deck_roof',n=24,
                          roof_level_mm=c['crown_top_mm']))
    for node in range(0,24,2):
        axis=_frame_point(p,ring,node,bottom+100);length=hypot(*axis[:2])
        reach=_chord_section(p,node,bottom+100)[0]/2+100
        anchor=[axis[k]*(1-reach/length) for k in range(2)]+[axis[2]]
        a=pi/2+2*pi*node/24;target=[c['bottom_radius_mm']*cos(a),c['bottom_radius_mm']*sin(a),bottom+100]
        parts.append(_beam('decks',f'tembo_deck_apron_connector_{node:02d}',anchor,target,180,WHITE,'deck_connector',
                           attachment_points=[anchor,target],frame_axis_mm=axis))
    return parts


def _gallery_section(theta,z,inner,outer,z0,z1):
    return [[inner*cos(theta),inner*sin(theta),z+z0],[outer*cos(theta),outer*sin(theta),z+z0],
            [outer*cos(theta),outer*sin(theta),z+z1],[inner*cos(theta),inner*sin(theta),z+z1]]


def _gallery_body_radius(c,z):
    return _antenna_radius(c['body_radius_controls_mm'],z)


def _gallery_route(c):
    # The rounded 110/114 m source lengths do not establish an exact turn count.
    # Compute an illustrative angular span, rather than silently forcing 360°.
    start,end=c['start_mm'],c['end_mm'];width=c['clear_width_mm']
    first=_gallery_body_radius(c,start)-100+width/2
    last=_gallery_body_radius(c,end)-100+width/2
    mean=(first+last)/2
    span=sqrt(c['path_length_mm']**2-(last-first)**2-(end-start)**2)/mean
    return first,last,span


def _tembo_galleria(p,ring):
    c=_galleria_config(p);parts=[];start,end=c['start_mm'],c['end_mm'];segments=int(c['segments'])
    thick=c['floor_thickness_mm'];width=c['clear_width_mm'];height=c['tube_height_mm']
    skin=c['skin_mm'];glass=c['glass_mm'];first,last,span=_gallery_route(c);facade_top=c['facade_top_mm']
    body=c['body_radius_controls_mm'];facade_n=48
    # The substantial inverted cone sits behind the attached outer passage.
    parts.extend(_shell('decks','tembo_galleria_apron',
                         [v for v in body if v[0]<=c['apron_top_mm']],skin,WHITE,'galleria_apron',n=facade_n))
    entry_angles=(0.,span%(2*pi))
    for i in range(facade_n):
        a,b=2*pi*i/facade_n,2*pi*(i+1)/facade_n
        openings=[]
        for theta,z in zip(entry_angles,(start,end)):
            if any(a-1e-9<=theta+offset<=b+1e-9 for offset in (-2*pi,0,2*pi)):
                openings.append((z,z+height))
        levels=sorted({start,facade_top}|{v for pair in openings for v in pair})
        for zone,(za,zb) in enumerate(zip(levels,levels[1:])):
            if za<start or zb>facade_top or any(lo<=za and zb<=hi for lo,hi in openings):continue
            parts.append(_loft('decks',f'tembo_galleria_inner_hall_glazing_{i:02d}_{zone}',
                               [_section(z,_sector(_gallery_body_radius(c,z)-glass,_gallery_body_radius(c,z),a,b)) for z in (za,zb)],
                               GLASS,'glazing',finish='glass',thickness_mm=glass,
                               gallery_surface='inverted_cone_hall',entrance_bay=bool(openings)))
    for floor,z in enumerate((start,end)):
        parts.extend(_annulus('decks',f'tembo_galleria_landing_floor_{floor}',c['floor_inner_radius_mm'],
                              _gallery_body_radius(c,z),z-thick,z,'#D6DBD8','deck_floor',n=facade_n,floor_level_mm=z))
    def at(t):
        z=start+(end-start)*t;centre=first+(last-first)*t
        return span*t,z,centre-width/2,centre+width/2
    def tube_profile(z,inner):
        # Builder's section: an outward bulge attached to a sloping inner wall,
        # rather than an independent symmetric semicircular glass tunnel.
        inner_top=_gallery_body_radius(c,z+height)-inner
        return [(width,0.),(width+c['tube_bulge_mm'],1050.),(width+200.,2200.),
                (width-420.,height),(inner_top,height)]
    for i in range(segments):
        a,za,ia,oa=at(i/segments);b,zb,ib,ob=at((i+1)/segments)
        route={'segment':i,'route_start':[(ia+width/2)*cos(a),(ia+width/2)*sin(a),za],
               'route_end':[(ib+width/2)*cos(b),(ib+width/2)*sin(b),zb],
               'route_assumption':c['route_scope'],'clear_width_mm':width}
        parts.append(_loft3d('decks',f'tembo_galleria_ramp_{i:02d}',
                             [_gallery_section(a,za,ia,oa,-thick,0),_gallery_section(b,zb,ib,ob,-thick,0)],
                             '#D6DBD8','galleria_ramp',**route))
        pa,pb=tube_profile(za,ia),tube_profile(zb,ib)
        for panel in range(len(pa)-1):
            sections=[]
            for theta,z,inner,profile in ((a,za,ia,pa),(b,zb,ib,pb)):
                aa,bb=profile[panel],profile[panel+1];dx,dz=bb[0]-aa[0],bb[1]-aa[1];length=hypot(dx,dz)
                normal=(dz/length*glass,-dx/length*glass)
                face=[aa,bb,(bb[0]+normal[0],bb[1]+normal[1]),(aa[0]+normal[0],aa[1]+normal[1])]
                sections.append([[(inner+r)*cos(theta),(inner+r)*sin(theta),z+h] for r,h in face])
            parts.append(_loft3d('decks',f'tembo_galleria_arch_glazing_{i:02d}_{panel}',sections,
                                 GLASS,'glazing',finish='glass',thickness_mm=glass,
                                 gallery_surface='arched_roof',segment=i,arch_panel=panel))
        if i%2==0 or i==segments-1:
            for panel,(aa,bb) in enumerate(zip(pa,pa[1:])):
                parts.append(_beam('decks',f'tembo_galleria_rib_{i:02d}_arch_{panel}',
                                   ((ia+aa[0])*cos(a),(ia+aa[0])*sin(a),za+aa[1]),
                                   ((ia+bb[0])*cos(a),(ia+bb[0])*sin(a),za+bb[1]),
                                   65,WHITE,'galleria_rib'))
        if i%4==0:
            node=round((a-pi/2)*24/(2*pi))%24;anchor=_frame_point(p,ring,node,za-thick/2)
            target=[(ia+width/2)*cos(a),(ia+width/2)*sin(a),za-thick/2]
            parts.append(_beam('decks',f'tembo_galleria_radial_support_{i:02d}',anchor,target,140,
                               WHITE,'galleria_support',attachment_points=[anchor,target],target_segment=i,frame_node=node))
    for floor,(t,z) in enumerate(((0.,start),(1.,end))):
        theta,_,inner,outer=at(t)
        parts.append(_loft('decks',f'tembo_galleria_access_pad_{floor}',
                           [_section(h,_sector(_gallery_body_radius(c,z)-500,outer,theta-.08,theta+.08)) for h in (z-thick,z)],
                           '#D6DBD8','galleria_access',floor_level_mm=z))
    # A short upper-hall incline reaches the separate 451.2 m public point.
    upper_n=int(c['upper_route_segments']);upper_r=c['upper_route_centre_radius_mm'];upper_span=c['upper_route_angle_rad']
    for i in range(upper_n):
        a=span+upper_span*i/upper_n;b=span+upper_span*(i+1)/upper_n
        za=end+(c['sorakara_level_mm']-end)*i/upper_n;zb=end+(c['sorakara_level_mm']-end)*(i+1)/upper_n
        parts.append(_loft3d('decks',f'tembo_galleria_upper_incline_{i:02d}',
                             [_gallery_section(a,za,upper_r-width/2,upper_r+width/2,-thick,0),
                              _gallery_section(b,zb,upper_r-width/2,upper_r+width/2,-thick,0)],
                             '#D6DBD8','galleria_upper_incline',segment=i,public_high_point_mm=c['sorakara_level_mm']))
    parts.append(_loft('decks','tembo_galleria_upper_access',
                       [_section(z,_sector(upper_r-width/2,_gallery_body_radius(c,end),span-.04,span+.04)) for z in (end-thick,end)],
                       '#D6DBD8','galleria_access',floor_level_mm=end))
    angle=span+upper_span;z=c['sorakara_level_mm']
    parts.append(_loft('decks','tembo_galleria_sorakara_landing',
                       [_section(h,_sector(upper_r-width/2,upper_r+width/2,angle-.05,angle+.05)) for h in (z-thick,z)],
                       '#D6DBD8','sorakara_landing',floor_level_mm=z))
    roof_radius=_gallery_body_radius(c,facade_top)
    parts.extend(_annulus('decks','tembo_galleria_inner_hall_roof',c['floor_inner_radius_mm'],roof_radius,
                          facade_top-c['roof_thickness_mm'],facade_top,WHITE,'deck_roof',n=facade_n,roof_level_mm=facade_top))
    parts.extend(_shell('decks','tembo_galleria_equipment_crown',
                         [(facade_top,c['crown_radius_mm']),(c['crown_top_mm'],c['crown_radius_mm'])],skin,
                         WHITE,'galleria_equipment_crown',n=24))
    parts.extend(_annulus('decks','tembo_galleria_crown_roof',c['floor_inner_radius_mm'],c['crown_radius_mm'],
                          c['crown_top_mm']-c['roof_thickness_mm'],c['crown_top_mm'],WHITE,'deck_roof',n=24,
                          roof_level_mm=c['crown_top_mm']))
    return parts


def _gain_point(config,node,z):
    r=_antenna_radius(config['radius_controls_mm'],z);angle=pi/2+2*pi*node/config['column_count']
    return [r*cos(angle),r*sin(angle),z]


def _gain_column_radius(config,z):
    t=max(0.,min(1.,(z-config['lattice_start_mm'])/(config['top_tie_mm']-config['lattice_start_mm'])))
    return (config['column_diameter_low_mm']*(1-t)+config['column_diameter_high_mm']*t)/2


def _antenna(p,ring):
    parts=[];c=_gain_config(p);start,cap=c['lattice_start_mm'],c['top_tie_mm'];count=int(c['column_count'])
    levels=sorted({start,cap}|{start+i*c['bay_height_mm'] for i in range(int((cap-start)/c['bay_height_mm'])+1)}
                  | {z for z in c['maintenance_levels_mm'] if start<=z<=cap}
                  | {z for z,r in c['radius_controls_mm'] if start<=z<=cap})
    for node in range(count):
        # Three controls suffice for the almost straight steel stem. Ring and
        # equipment subdivisions do not multiply its circular loft sections.
        chord_levels=sorted({start,cap}|{z for z,r in c['radius_controls_mm'] if start<z<cap})
        sections=[]
        for z in chord_levels:
            t=(z-start)/(cap-start);wall=c['column_wall_low_mm']*(1-t)+c['column_wall_high_mm']*t
            sections.append({'z':z,'center':_gain_point(c,node,z)[:2],'radius':_gain_column_radius(c,z),'wall_thickness_mm':wall})
        parts.append(_tube_loft('antenna',f'gain_chord_{node:02d}',sections,WHITE,'gain_chord',gain_node=node))
        anchor=_frame_point(p,ring,node*24//count,c['bridge_start_mm']);target=_gain_point(c,node,c['bridge_end_mm'])
        parts.append(_tube('antenna',f'gain_transition_{node:02d}',anchor,target,c['bridge_diameter_mm'],c['bridge_wall_mm'],
                           WHITE,'gain_transition',body_node=node*24//count,gain_node=node))
    for level,z in enumerate(levels):
        for node in range(count):
            a,b=_gain_point(c,node,z),_gain_point(c,(node+1)%count,z)
            parts.append(_rhs('antenna',f'gain_ring_{level:02d}_{node}',a,b,c['ring_width_mm'],c['ring_depth_mm'],c['ring_wall_mm'],
                              WHITE,'gain_ring',level_mm=z))
        if level:
            for node in range(count):
                a=_gain_point(c,node if level%2 else (node+1)%count,levels[level-1])
                b=_gain_point(c,(node+1)%count if level%2 else node,z)
                parts.append(_tube('antenna',f'gain_brace_{level:02d}_{node}',a,b,c['brace_diameter_mm'],c['brace_wall_mm'],SHADOW,'gain_brace'))
    faces=int(c['equipment_faces']);rows=int(c['equipment_rows']);skin=c['equipment_skin_mm']
    for bank,(bottom,top,radius) in enumerate(c['equipment_banks_mm']):
        for side in range(faces):
            a,b=2*pi*(side+.05)/faces,2*pi*(side+.95)/faces
            parts.append(_loft('antenna',f'gain_equipment_bank_{bank:02d}_{side:02d}',
                               [_section(z,_sector(radius-skin,radius,a,b)) for z in (bottom,top)],
                               WHITE,'broadcast_antenna_panel',bank=bank,appearance_scope=c['equipment_scope']))
        for row in sorted(set(range(0,rows+1,int(c['equipment_belt_stride'])))|{rows}):
            z=bottom+(top-bottom)*row/rows
            parts.extend(_annulus('antenna',f'gain_equipment_belt_{bank:02d}_{row:02d}',radius-skin-40,(radius+90)/cos(pi/12),
                                  z-65,z+65,SHADOW,'broadcast_antenna_belt',n=12,bank=bank))
        # Positive radial support members cross both the steel wall and panel
        # skin; the facade assembly is not a detached opaque sleeve.
        z=(bottom+top)/2
        for node in range(count):
            a=_gain_point(c,node,z);theta=pi/2+2*pi*node/count;b=[radius*cos(theta),radius*sin(theta),z]
            parts.append(_tube('antenna',f'gain_equipment_support_{bank:02d}_{node}',a,b,140,10,WHITE,
                               'broadcast_antenna_support',bank=bank))
    for index,z in enumerate(c['maintenance_levels_mm']):
        parts.extend(_annulus('antenna',f'gain_maintenance_platform_{index:02d}',2000,c['maintenance_radius_mm'],
                              z-c['maintenance_thickness_mm'],z,WHITE,'gain_maintenance_platform',n=12,level_mm=z))
        for node in range(count):
            theta=pi/2+2*pi*node/count;a=_gain_point(c,node,z-70);b=[c['maintenance_radius_mm']*cos(theta),c['maintenance_radius_mm']*sin(theta),z-70]
            parts.append(_tube('antenna',f'gain_maintenance_spoke_{index:02d}_{node}',a,b,180,12,WHITE,'gain_platform_support',level_mm=z))
    # The expanded two-storey TMD enclosure sits above the general hexagonal
    # stem. The spring/mass/damping mechanism is deliberately not simulated.
    bottom,mid,roof=c['tmd_bottom_mm'],c['tmd_middle_mm'],c['tmd_roof_mm']
    for node in range(count):
        a=_gain_point(c,node,bottom);theta=pi/2+2*pi*node/count
        b=[c['tmd_inner_radius_mm']*cos(theta),c['tmd_inner_radius_mm']*sin(theta),roof-100]
        parts.append(_tube('antenna',f'tmd_frame_post_{node}',a,b,240,16,WHITE,'tmd_enclosure_frame'))
    for floor,z in enumerate((bottom,mid,roof)):
        parts.extend(_annulus('antenna',f'tmd_machine_floor_{floor}',500,c['tmd_flange_radius_mm'],z-180,z,
                              WHITE,'tmd_machine_floor',n=12,level_mm=z,tmd_storeys=2))
    for storey,(za,zb) in enumerate(((bottom,mid),(mid,roof))):
        for side in range(12):
            a,b=2*pi*(side+.045)/12,2*pi*(side+.955)/12
            ra=c['tmd_inner_radius_mm'] if storey==0 else c['tmd_radius_mm']
            parts.append(_loft('antenna',f'tmd_machine_cladding_{storey}_{side:02d}',
                               [_section(za,_sector(ra-100,ra,a,b)),
                                _section(zb,_sector(c['tmd_radius_mm']-100,c['tmd_radius_mm'],a,b))],
                               SHADOW,'tmd_machine_room_cladding',storey=storey,appearance_scope=c['equipment_scope']))
    # The rod passes through the roof plate to a radial roof cross. Its tip,
    # rather than six open structural chords, defines the 634 m height.
    for node in range(0,count,2):
        theta=pi/2+2*pi*node/count
        parts.append(_tube('antenna',f'gain_top_link_{node:02d}',
                           (c['tmd_inner_radius_mm']*cos(theta),c['tmd_inner_radius_mm']*sin(theta),roof-100),
                           (0,0,roof-100),180,12,WHITE,'gain_top_link'))
    parts.append(_tube('antenna','gain_terminal_mast',(0,0,roof-200),(0,0,c['top_mm']),
                       2*c['lightning_rod_radius_mm'],12,WHITE,'gain_terminal_mast'))
    return parts


def _obstruction_lights(p,ring):
    """Illustrative lenses on actual steel, roof plates and service platforms."""
    parts=[];c=_light_config(p);gain=_gain_config(p);deck=_deck_config(p);hall=_galleria_config(p)
    mounts=[]
    for z in c['body_levels_mm']:
        axis=_frame_point(p,ring,0,z);length=hypot(*axis[:2]);u=[axis[0]/length,axis[1]/length]
        radius=_chord_section(p,0,z)[0]/2
        mounts.append(('structure',axis,[axis[0]+u[0]*(radius+350),axis[1]+u[1]*(radius+350),z],z,'body_chord'))
    for index,z in enumerate(c['deck_roof_levels_mm']):
        radius=(deck['roof_radius_mm'] if index==0 else deck['crown_radius_mm'])-550
        mounts.append(('decks',[0,radius,z-100],[0,radius,z+c['post_height_mm']+c['lens_half_mm']],z,'tembo_deck_roof'))
    z=c['galleria_roof_level_mm'];radius=_gallery_body_radius(hall,z)-550
    mounts.append(('decks',[0,radius,z-100],[0,radius,z+c['post_height_mm']+c['lens_half_mm']],z,'tembo_galleria_roof'))
    for z in c['gain_platform_levels_mm']:
        radius=gain['maintenance_radius_mm']-300
        mounts.append(('antenna',[0,radius,z-100],[0,radius,z+c['post_height_mm']+c['lens_half_mm']],z,'gain_maintenance_platform'))
    z=c['tmd_roof_level_mm'];radius=gain['tmd_flange_radius_mm']-450
    mounts.append(('antenna',[0,radius,z-100],[0,radius,z+c['post_height_mm']+c['lens_half_mm']],z,'tmd_machine_floor'))
    for index,(group,anchor,lens,z,surface) in enumerate(mounts):
        parts.append(_tube(group,f'obstruction_light_arm_{index}',anchor,lens,140,10,STEEL,'light_housing',
                           attachment_points=[anchor,lens],mount_surface=surface,surface_level_mm=z))
        x,y,h=lens;s=c['lens_half_mm']
        parts.append(_box(group,f'obstruction_light_lens_{index}',(x-s,y-s,h-s,x+s,y+s,h+s),'#F64B42',
                          'obstruction_light_lens',mount_surface=surface,surface_level_mm=z,
                          support_name=f'{group}:obstruction_light_arm_{index}'))
    return parts


def _antenna_radius(stations,z):
    for (za,ra),(zb,rb) in zip(stations,stations[1:]):
        if za<=z<=zb:return ra+(rb-ra)*(z-za)/(zb-za)
    raise ValueError('Antenna height outside station coverage')


def component_specs(p,ring):
    """Exact primitives for the shared Skytree CAD, drawing and GLB exporters."""
    rings={}
    def cached_ring(z):
        if z not in rings:rings[z]=ring(z)
        return rings[z]
    body=_body(p,cached_ring)
    return (_base(p,cached_ring)+body+_base_wing_frame(p,cached_ring,body)+_core(p)+_tembo_deck(p,cached_ring)
            +_tembo_galleria(p,cached_ring)+_antenna(p,cached_ring)+_obstruction_lights(p,cached_ring))
