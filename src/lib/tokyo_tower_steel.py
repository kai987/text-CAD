"""R04 Tokyo Tower steel appearance, informed by construction/retrofit photos.

Wide built-up faces and edge fastener patterns guide this approximation.
Section families, dimensions, selected nodes and joints are not surveyed
original sections or a capacity/retrofit design. The model retains its source
member axes inside each section web and keeps every unrelated named part.
"""
from __future__ import annotations

from copy import deepcopy
from math import cos, sin, pi, sqrt

STEEL_PROFILE_DEFAULTS={
    'lower':{'type':'H','width_factor':1.,'depth_factor':.85,'web_thickness_mm':24.,'flange_thickness_mm':30.},
    'middle':{'type':'H','width_factor':.90,'depth_factor':.80,'web_thickness_mm':18.,'flange_thickness_mm':24.},
    'upper':{'type':'I','width_factor':.62,'depth_factor':1.,'web_thickness_mm':14.,'flange_thickness_mm':18.},
}
STEEL_NODE_DEFAULTS={
    'base':{'width_mm':1200.,'height_mm':1000.,'plate_thickness_mm':30.,'stiffener_thickness_mm':16.,'stiffener_depth_mm':160.,'rivet_radius_mm':18.,'rivet_projection_mm':12.},
    'lower_truss':{'width_mm':1100.,'height_mm':1200.,'plate_thickness_mm':20.,'stiffener_thickness_mm':16.,'stiffener_depth_mm':140.,'rivet_radius_mm':18.,'rivet_projection_mm':12.},
    'splice':{'width_mm':620.,'height_mm':1050.,'plate_thickness_mm':16.,'stiffener_thickness_mm':14.,'stiffener_depth_mm':100.,'rivet_radius_mm':18.,'rivet_projection_mm':12.},
    'deck_support':{'width_mm':1100.,'height_mm':1000.,'plate_thickness_mm':24.,'stiffener_thickness_mm':16.,'stiffener_depth_mm':180.,'rivet_radius_mm':18.,'rivet_projection_mm':12.},
}


def _add(a,b):return [x+y for x,y in zip(a,b)]
def _sub(a,b):return [x-y for x,y in zip(a,b)]
def _mul(a,s):return [x*s for x in a]
def _dot(a,b):return sum(x*y for x,y in zip(a,b))
def _cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def _unit(a):return _mul(a,1/sqrt(_dot(a,a)))


def _axis(spec):
    if 'axis_start' in spec:return list(spec['axis_start']),list(spec['axis_end'])
    result=[]
    for s in (spec['sections'][0],spec['sections'][-1]):
        points=s['points'];result.append([sum(v[i] for v in points)/len(points) for i in range(2)]+[s['z']])
    return result


def _basis(a,b):
    w=_unit(_sub(b,a));radial=[(a[0]+b[0])/2,(a[1]+b[1])/2,0.]
    u=_unit(_sub(radial,_mul(w,_dot(radial,w))))
    return u,_cross(w,u),w


def _point(o,u,v,n,x,y,z):return [o[i]+u[i]*x+v[i]*y+n[i]*z for i in range(3)]


def _loft(name,sections,color,role,**data):
    return {'group':'structure','name':'structure:'+name,'kind':'loft3d','sections':sections,
            'color':color,'role':role,**data}


def _profile(p,spec):
    a,b=_axis(spec);size=2*max(abs(x-a[0]) for x,y in spec['sections'][0]['points'])
    zone='lower' if spec['name'].startswith('structure:leg_') else 'middle' if a[2]<150000 else 'upper'
    config={**STEEL_PROFILE_DEFAULTS[zone],**p.get('detail',{}).get('steel_profile_families',{}).get(zone,{})}
    width=size*config['width_factor'];depth=size*config['depth_factor']
    web=config['web_thickness_mm'];flange=config['flange_thickness_mm']
    if not 0<web<width or not 0<2*flange<depth:raise ValueError('Invalid built-up appearance profile dimensions')
    x,y,t,q=width/2,depth/2,web/2,flange
    outline=[[-x,-y],[x,-y],[x,-y+q],[t,-y+q],[t,y-q],[x,y-q],
             [x,y],[-x,y],[-x,y-q],[-t,y-q],[-t,-y+q],[-x,-y+q]]
    return outline,{'type':config['type'],'family':zone,'width_mm':width,'depth_mm':depth,
                    'web_thickness_mm':web,'flange_thickness_mm':flange,'axis_inside_web':True,
                    'dimensions_status':'demonstration_assumption'}


def _refined_chord(p,spec):
    result=deepcopy(spec);a,b=_axis(spec);u,v,w=_basis(a,b);outline,profile=_profile(p,spec)
    result.update(kind='loft3d',sections=[[_point(o,u,v,w,x,y,0) for x,y in outline] for o in (a,b)],
                  axis_start=a,axis_end=b,profile_type=profile['type'],steel_role='built_up_chord',
                  section_profile=profile,local_frame={'origin_mm':a,'u':u,'v':v,'normal':w},
                  section_assumption='Wide built-up H/I appearance family; no original section dimensions are claimed.')
    return result


def _at_z(spec,z):
    a,b=_axis(spec);t=(z-a[2])/(b[2]-a[2]);return [a[i]+t*(b[i]-a[i]) for i in range(3)]


def _select(by,prefix,z):
    matches=[s for name,s in by.items() if name.startswith(prefix) and s.get('role')=='primary_chord'
             and _axis(s)[0][2]-1e-6<=z<=_axis(s)[1][2]+1e-6]
    if not matches:raise ValueError(f'No source primary member at {prefix} / Z={z}')
    return min(matches,key=lambda s:(abs(_axis(s)[1][2]-z),s['name']))


def _node_config(p,kind):
    return {**STEEL_NODE_DEFAULTS[kind],**p.get('detail',{}).get('steel_node_families',{}).get(kind,{})}


def _plans(p,base_parts):
    by={s['name']:s for s in base_parts};plans=[]
    def add(kind,index,source,z,others):
        a,b=_axis(source);anchor=_at_z(source,z);u,tangent,w=_basis(a,b)
        if kind=='base':
            normal=[0.,0.,1.];u=_unit([anchor[0],anchor[1],0.]);v=_cross(normal,u);origin=list(anchor)
        else:
            v=w;normal=_cross(u,v);profile=_profile(p,source)[1]
            offset=profile['depth_mm']/2+_node_config(p,kind)['plate_thickness_mm']/2-1.
            origin=_add(anchor,_mul(normal,offset))
        labels={'base':{'zh':f'塔脚板组 {index}','ja':f'塔脚板組 {index}','en':f'Leg base plate group {index}'},
                'lower_truss':{'zh':f'下部汇交节点 {index}','ja':f'下部集合節点 {index}','en':f'Lower converging joint {index}'},
                'splice':{'zh':f'主材双面接长 {index}','ja':f'主材両面継手 {index}','en':f'Two-face chord splice {index}'},
                'deck_support':{'zh':f'主展望台支承 {index}','ja':f'主展望台支持節点 {index}','en':f'Main deck support {index}'}}
        members=[source['name']]+[n for n in others if n in by]
        plans.append({'id':f'TT-N{len(plans)+1:02d}','names':labels[kind],'type':kind,'anchor_mm':anchor,
                      'member_names':members,'local_frame':{'origin_mm':origin,'u':u,'v':v,'normal':normal}})
    for leg in range(1,5):
        source=_select(by,f'structure:leg_{leg:02d}_chord_00_',1300)
        add('base',leg,source,1300,[f'structure:leg_{leg:02d}_shoe_plate'])
    for level,z in ((1,18000),(2,52000)):
        for leg in range(1,5):
            source=_select(by,f'structure:leg_{leg:02d}_chord_01_',z)
            anchor=_at_z(source,z)
            related=[n for n,s in by.items() if n.startswith(f'structure:leg_{leg:02d}_') and s.get('role') in ('leg_brace','leg_tie')
                     and min(sum((q[i]-anchor[i])**2 for i in range(3)) for q in (s['start'],s['end']))<900**2]
            add('lower_truss',(level-1)*4+leg,source,z,related[:3])
    for leg in range(1,5):
        source=_select(by,f'structure:leg_{leg:02d}_chord_00_',40000)
        others=[n for n,s in by.items() if n.startswith(f'structure:leg_{leg:02d}_chord_00_') and n!=source['name']
                and abs(_axis(s)[0][2]-40000)<1e-6]
        add('splice',leg,source,40000,others)
    support=p.get('detail',{}).get('steel_main_support_z_mm',115000)
    for side in range(4):
        source=_select(by,f'structure:upper_chord_{side}_',support);anchor=_at_z(source,support)
        related=[]
        for n,s in by.items():
            if s.get('role') not in ('upper_ring','deck_bracket'):continue
            if min(sum((point[i]-anchor[i])**2 for i in range(3)) for point in (s['start'],s['end']))<1800**2:related.append(n)
        add('deck_support',side+1,source,support,related[:4])
    return plans


def _shape_and_rivets(kind,w,h):
    if kind=='base':
        c=.12;shape=[[-.5+c,-.5],[.5-c,-.5],[.5,-.5+c],[.5,.5-c],[.5-c,.5],[-.5+c,.5],[-.5,.5-c],[-.5,-.5+c]]
        rivets=[(x,y) for x in (-.36,.36) for y in (-.32,0,.32)]+[(x,y) for x in (-.15,.15) for y in (-.36,.36)]
    elif kind=='lower_truss':
        shape=[[-.5,-.5],[.5,-.5],[.5,-.15],[.20,.16],[.13,.5],[-.13,.5],[-.30,.08],[-.5,-.15]]
        rivets=[(x,y) for x in (-.34,-.20,.20,.34) for y in (-.35,-.20)]+[(x,y) for x in (-.065,.065) for y in (.25,.39)]
    elif kind=='splice':
        shape=[[-.5,-.5],[.5,-.5],[.5,.5],[-.5,.5]]
        rivets=[(x,y) for x in (-.32,.32) for y in (-.36,-.12,.12,.36)]
    else:
        shape=[[-.5,-.5],[.5,-.5],[.5,.05],[.28,.05],[.28,.5],[-.28,.5],[-.28,.05],[-.5,.05]]
        rivets=[(x,y) for x in (-.35,.35) for y in (-.36,-.20,-.04)]+[(x,y) for x in (-.16,.16) for y in (.18,.31,.44)]
    return [[x*w,y*h] for x,y in shape],[(x*w,y*h) for x,y in rivets]


def _node_parts(p,node):
    cfg=_node_config(p,node['type']);width,height,thick=cfg['width_mm'],cfg['height_mm'],cfg['plate_thickness_mm']
    stiff,depth=cfg['stiffener_thickness_mm'],cfg['stiffener_depth_mm'];radius,projection=cfg['rivet_radius_mm'],cfg['rivet_projection_mm']
    frame=node['local_frame'];o=frame['origin_mm'];u,v,n=frame['u'],frame['v'],frame['normal']
    pt=lambda x,y,z:_point(o,u,v,n,x,y,z)
    stem='steel_'+node['id'];plate_name='structure:'+stem+'_plate';shape,rivets=_shape_and_rivets(node['type'],width,height)
    common={'steel_node_id':node['id'],'dimensions_status':'demonstration_assumption'}
    parts=[_loft(stem+'_plate',[[pt(x,y,z) for x,y in shape] for z in (-thick/2,thick/2)],
                 '#D54724','steel_connection_plate',steel_detail_kind='plate',contact_with=node['member_names'][0],
                 plate_thickness_mm=thick,plate_outline_family=node['type'],**common)]
    # Four foot ribs, no invented generic ribs on the fan/splice, and two
    # shorter support ribs make the four photo-informed families distinct.
    ribs=[(-width*.20,0),(width*.20,0),(0,1),(0,-1)] if node['type']=='base' else [(-width*.18,0),(width*.18,0)] if node['type']=='deck_support' else []
    for i,(centre,rotation) in enumerate(ribs):
        sections=[]
        for x in (centre-stiff/2,centre+stiff/2):
            triangle=[(x,-height*.24,0),(x,-height*.24,depth),(x,height*.24,0)]
            sections.append([pt(y,x,z) if rotation else pt(x,y,z) for x,y,z in triangle])
        # The two transverse foot ribs occupy separate sides of the central
        # footprint rather than duplicate the same triangular surface.
        if node['type']=='base' and rotation:
            sections=[[[q[j]+v[j]*rotation*height*.20 for j in range(3)] for q in section] for section in sections]
        parts.append(_loft(stem+f'_stiffener_{i}',sections,'#D54724','steel_stiffener',steel_detail_kind='stiffener',
                           contact_with=plate_name,**common))
    faces=[(1,plate_name,o,u,n)]
    if node['type']=='splice':
        offset=sum((o[i]-node['anchor_mm'][i])*n[i] for i in range(3));back_o=_add(node['anchor_mm'],_mul(n,-offset))
        back_u=_mul(u,-1);back_n=_mul(n,-1)
        back=lambda x,y,z:_point(back_o,back_u,v,back_n,x,y,z)
        back_name='structure:'+stem+'_back_plate'
        parts.append(_loft(stem+'_back_plate',[[back(x,y,z) for x,y in shape] for z in (-thick/2,thick/2)],
                           '#D54724','steel_splice_plate',steel_detail_kind='plate',contact_with=node['member_names'][0],
                           plate_thickness_mm=thick,plate_outline_family='splice_back',**common))
        faces.append((-1,back_name,back_o,back_u,back_n))
    front_centres=[]
    for sign,contact,origin,axis_u,axis_n in faces:
        place=lambda x,y,z:_point(origin,axis_u,v,axis_n,x,y,z)
        for index,(x,y) in enumerate(rivets):
            embed=min(6.,thick*.3)
            sections=[[place(x+r*cos(2*pi*k/8),y+r*sin(2*pi*k/8),z) for k in range(8)]
                      for z,r in ((thick/2-embed,radius),(thick/2+projection*.45,radius),(thick/2+projection,radius*.55))]
            centre=place(x,y,thick/2+projection*.5)
            if sign==1:front_centres.append(centre)
            parts.append(_loft(stem+f'_rivet_{"front" if sign==1 else "back"}_{index:02d}',sections,'#BD3F21','rivet_head',
                               steel_detail_kind='rivet',detail_level='steel_micro',contact_with=contact,rivet_centre_mm=centre,
                               face_sign=sign,face_normal=axis_n,**common))
    # A real horizontal outline edge provides the editable width, and the first
    # two edge heads provide a real pitch without implied nominal dimensions.
    bottom=sorted((q for q in shape if abs(q[1]-min(v[1] for v in shape))<1e-6),key=lambda q:q[0])
    dimensions=[{'id':'plate-width','kind':'plate_width','label':{'zh':'节点板下缘宽','ja':'節点板下縁幅','en':'Plate lower-edge width'},
                 'points_mm':[pt(*bottom[0],thick/2),pt(*bottom[-1],thick/2)]},
                {'id':'rivet-pitch','kind':'rivet_pitch','label':{'zh':'代表边缘铆钉间距','ja':'代表縁リベット間隔','en':'Representative edge rivet pitch'},
                 'points_mm':[front_centres[0],front_centres[1]]}]
    parameters={'plate_width_mm':width,'plate_height_mm':height,'plate_thickness_mm':thick,
                'stiffener_thickness_mm':stiff,'stiffener_depth_mm':depth,'rivet_radius_mm':radius,
                'rivet_projection_mm':projection,'rivet_count':len(rivets)*len(faces),'outline_family':node['type'],
                'rivet_pitch_mm':sqrt(sum((front_centres[1][i]-front_centres[0][i])**2 for i in range(3))),
                'dimensioned_plate_width_mm':bottom[-1][0]-bottom[0][0]}
    return parts,dimensions,parameters


def refine_steel(p,base_parts):
    """Private appearance geometry with source axes and unrelated parts intact."""
    parts=[_refined_chord(p,s) if s.get('role')=='primary_chord' else deepcopy(s) for s in base_parts]
    for node in _plans(p,base_parts):parts.extend(_node_parts(p,node)[0])
    return parts


def node_catalog(p,base_parts):
    """Twenty real geometry-linked, family-specific inspection/drawing records."""
    result=[]
    for node in _plans(p,base_parts):
        parts,dimensions,parameters=_node_parts(p,node);points=[v for s in parts for section in s['sections'] for v in section]
        result.append({**node,'part_names':[s['name'] for s in parts],'feature_dimensions':dimensions,'parameters':parameters,
                       'bounds_mm':[min(v[i] for v in points) for i in range(3)]+[max(v[i] for v in points) for i in range(3)],
                       'dimensions_status':'demonstration_assumption'})
    return result
