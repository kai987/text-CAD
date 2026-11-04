"""Photo-guided open, battened/laced lower Tokyo Tower assemblies.

The inherited member axes and envelopes are retained. Plate thicknesses,
openings and diaphragms are modelling assumptions, not surveyed sections or a
structural design. Pure parameter generation deliberately has no CAD imports.
"""
from __future__ import annotations

from copy import deepcopy
from math import ceil, isfinite, sqrt


DEFAULTS = {
    'cover_thickness_mm': 20., 'web_thickness_mm': 16.,
    'border_width_mm': 40., 'batten_width_mm': 55.,
    'lacing_width_mm': 45., 'pitch_depth_ratio': 2.,
    'min_cells': 4, 'max_cells': 12, 'diaphragm_length_mm': 100.,
    'max_pieces_per_member': 24,
}
SCOPE = 'photo_guided_open_built_up_not_surveyed'


def _add(a,b): return [x+y for x,y in zip(a,b)]
def _sub(a,b): return [x-y for x,y in zip(a,b)]
def _mul(a,s): return [x*s for x in a]
def _dot(a,b): return sum(x*y for x,y in zip(a,b))
def _cross(a,b): return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def _unit(a): return _mul(a,1/sqrt(_dot(a,a)))


def is_target(spec):
    """Explicit R08 lower-member whitelist; no adjoining connection parts."""
    n=spec['name'];role=spec.get('role')
    if n.startswith('structure:leg_') and role=='primary_chord': return True
    if spec.get('steel_role')=='arch_plate_chord': return True
    if role in ('leg_brace','leg_tie','lower_belt','lower_panel_brace','lower_panel_vertical'): return True
    if role=='arch_spandrel': return not n.startswith('structure:arch_spandrel_crown_bridge_')
    return role=='open_cross_frame' and spec.get('arch_member_kind') in ('diagonal','in_plane_tie','depth_tie')


def _config(p):
    cfg={**DEFAULTS,**p['detail']['lower_built_up']}
    for k in DEFAULTS:
        if isinstance(cfg[k],bool) or not isinstance(cfg[k],(int,float)) or not isfinite(cfg[k]) or cfg[k]<=0:
            raise ValueError('Invalid lower_built_up setting: '+k)
    for k in ('min_cells','max_cells','max_pieces_per_member'):
        if not isinstance(cfg[k],int): raise ValueError('Built-up count must be an integer: '+k)
    if not 1<=cfg['min_cells']<=cfg['max_cells']<=24: raise ValueError('Invalid built-up cell bounds')
    if not 6<=cfg['max_pieces_per_member']<=24: raise ValueError('Built-up piece budget must be 6..24')
    return cfg


def _frame(spec):
    a=list(spec.get('axis_start',spec.get('start',[])))
    b=list(spec.get('axis_end',spec.get('end',[])))
    if not a or not b: raise ValueError('Built-up source requires explicit member axis')
    w=_unit(_sub(b,a));length=sqrt(_dot(_sub(b,a),_sub(b,a)))
    if spec['kind']=='loft3d':
        first=spec['sections'][0];last=spec['sections'][-1]
        u=_unit(_sub(first[1],first[0]));v=_cross(w,u)
        width=spec['section_profile']['width_mm'];depth=spec['section_profile']['depth_mm']
        # Arch chords retain their source end laps, while nominal axes stay exact.
        lo=sum(_dot(_sub(q,a),w) for q in first)/len(first)
        hi=sum(_dot(_sub(q,a),w) for q in last)/len(last)
        origin=_add(a,_mul(w,lo));length=hi-lo
    else:
        ref=[0.,0.,1.] if abs(w[2])<.95 else [1.,0.,0.]
        u=_unit(_cross(w,ref));v=_cross(w,u);origin=a
        width=2*spec['radius'];depth=min(1100.,max(240.,4*spec['radius']))
    return {'origin_mm':origin,'u':u,'v':v,'normal':w,'length_mm':length,
            'width_mm':width,'depth_mm':depth}


def _point(f,x,y,z):
    return [f['origin_mm'][i]+f['u'][i]*x+f['v'][i]*y+f['normal'][i]*z for i in range(3)]


def _plate(f,piece_id,x1,x2,y1,y2,z1,z2,**metadata):
    return {'piece_id':piece_id,'kind':'plate_loft',
            'sections':[[_point(f,x,y,z) for x,y in ((x1,y1),(x2,y1),(x2,y2),(x1,y2))] for z in (z1,z2)],
            **metadata}


def _attachment_positions(parts):
    positions={}
    for s in parts:
        points=s.get('attachment_points',[])
        for key,index in (('source_member',0),('target_member',1)):
            if s.get(key) and len(points)>index:
                positions.setdefault(s[key],[]).append({'point':list(points[index]),'connection':s['name']})
    return positions


def _diaphragm_spans(f,anchors,cfg):
    length=f['length_mm'];half=min(cfg['diaphragm_length_mm']/2,length/12)
    spans=[(0.,min(length,2*half)),(max(0.,length-2*half),length)]
    records=[]
    for item in anchors:
        z=max(0.,min(length,_dot(_sub(item['point'],f['origin_mm']),f['normal'])))
        spans.append((max(0.,z-half),min(length,z+half)))
        records.append({**item,'axial_mm':z})
    merged=[]
    for lo,hi in sorted(spans):
        if merged and lo<=merged[-1][1]+1e-6: merged[-1]=(merged[-1][0],max(hi,merged[-1][1]))
        else: merged.append((lo,hi))
    if len(merged)+4>cfg['max_pieces_per_member']:
        raise ValueError('Built-up diaphragm count exceeds explicit piece budget')
    return merged,records


def _holes(f,family,cfg,spans):
    length=f['length_mm'];depth=f['depth_mm']
    border=min(cfg['border_width_mm'],depth*.18)
    inner=depth/2-border
    count=int(max(cfg['min_cells'],min(cfg['max_cells'],ceil(length/(cfg['pitch_depth_ratio']*depth)))))
    pitch=length/count;batten=min(cfg['batten_width_mm'],pitch*.18)
    holes=[]
    for i in range(count):
        lo=i*pitch+batten/2;hi=(i+1)*pitch-batten/2
        # The diaphragms occupy genuine solid sections; subdivide the open web
        # around them rather than making an intersecting solid hide a void.
        intervals=[(lo,hi)]
        for a,b in spans:
            next_intervals=[]
            for c,d in intervals:
                if b<=c or a>=d: next_intervals.append((c,d))
                else:
                    if c<a: next_intervals.append((c,a))
                    if b<d: next_intervals.append((b,d))
            intervals=next_intervals
        for lo,hi in intervals:
            if hi-lo<max(50.,depth*.22): continue
            if family=='battened': holes.append([(-inner,lo),(inner,lo),(inner,hi),(-inner,hi)])
            else:
                # Two separated triangles leave an actual diagonal lacing strip.
                gap=min(cfg['lacing_width_mm'],inner*.30,(hi-lo)*.20)
                holes.extend([[(-inner,lo+gap),(-inner,hi),(inner-gap,hi)],
                              [(-inner+gap,lo),(inner,lo),(inner,hi-gap)]])
    return holes,count


def _refine(spec,cfg,anchors):
    f=_frame(spec);width,depth,length=f['width_mm'],f['depth_mm'],f['length_mm']
    family='battened' if spec.get('role') in ('primary_chord','leg_tie','lower_belt') else 'laced'
    # The verticals use lacing, matching the diagonal family rather than
    # pretending all members share an original proprietary steel section.
    cover=min(cfg['cover_thickness_mm'],depth*.12)
    web=min(cfg['web_thickness_mm'],width*.12)
    spans,records=_diaphragm_spans(f,anchors,cfg)
    holes,count=_holes(f,family,cfg,spans)
    if not holes: raise ValueError('Built-up member has no usable web opening: '+spec['name'])
    pieces=[_plate(f,'cover_negative',-width/2,width/2,-depth/2,-depth/2+cover,0,length,member_function='continuous_cover'),
            _plate(f,'cover_positive',-width/2,width/2,depth/2-cover,depth/2,0,length,member_function='continuous_cover')]
    for side in (-1,1):
        x=side*width/2;extrusion=_mul(f['u'],-side*web)
        outer=[_point(f,x,y,z) for y,z in ((-depth/2,0),(depth/2,0),(depth/2,length),(-depth/2,length))]
        openings=[[_point(f,x,y,z) for y,z in loop] for loop in holes]
        probe=[sum(q[i] for q in openings[0])/len(openings[0])+extrusion[i]/2 for i in range(3)]
        pieces.append({'piece_id':'web_'+('negative' if side<0 else 'positive'),'kind':'perforated_plate',
                       'outer':outer,'holes':openings,'extrusion':extrusion,'void_probe_mm':probe,
                       'opening_type':'rectangle' if family=='battened' else 'triangle',
                       'cell_count':count,'member_function':'open_battened_web' if family=='battened' else 'open_laced_web'})
    for i,(lo,hi) in enumerate(spans):
        pieces.append(_plate(f,f'diaphragm_{i:02d}',-width/2,width/2,-depth/2,depth/2,lo,hi,
                             member_function='solid_attachment_diaphragm',axial_interval_mm=[lo,hi]))
    result=deepcopy(spec)
    # Keep the R08 descriptions as explicit provenance, not current section
    # specifications. Native geometry below is the R09 perforated assembly.
    for key in ('section_profile','profile_type','section_assumption','continuation_scope'):
        if key in spec: result['source_'+key]=deepcopy(spec[key])
    profile_type='built_up_'+family
    result.update(profile_type=profile_type,
                  section_profile={'type':profile_type,'family':family,'width_mm':width,'depth_mm':depth,
                                   'cover_thickness_mm':cover,'web_thickness_mm':web,
                                   'opening_type':'rectangle' if family=='battened' else 'triangle',
                                   'dimensions_status':'photo_guided_demonstration_assumption'},
                  section_assumption='R09 photo-guided open built-up assembly with continuous cover plates, '
                                     +('rectangular battened' if family=='battened' else 'triangular laced')
                                     +' webs and local attachment diaphragms. Inherited envelope and assumed '
                                     'plate dimensions are not surveyed original sections or structural design.')
    if 'continuation_scope' in spec:
        result['continuation_scope']=('R09 open built-up appearance continuation using inherited R08 member axes, '
                                      'end laps and envelope; cover plates, open webs and attachment diaphragms '
                                      'are photo-guided assumptions, not recovered original section specifications.')
    result.update(kind='built_up',axis_start=list(spec.get('axis_start',spec.get('start'))),
                  axis_end=list(spec.get('axis_end',spec.get('end'))),built_up_family=family,
                  built_up_scope=SCOPE,built_up_frame=f,pieces=pieces,
                  built_up_attachment_points=records,built_up_piece_budget=int(cfg['max_pieces_per_member']),
                  built_up_dimensions_status='photo_guided_demonstration_assumption')
    return result


def refine_built_up(p, refined_R08_parts):
    """Retain named members and metadata; opt in only through explicit config."""
    setting=p.get('detail',{}).get('lower_built_up')
    if setting is not None and not isinstance(setting,dict): raise ValueError('lower_built_up must be a mapping')
    if setting and not isinstance(setting.get('enabled',False),bool): raise ValueError('lower_built_up enabled must be boolean')
    if not setting or not setting.get('enabled',False): return refined_R08_parts
    cfg=_config(p);positions=_attachment_positions(refined_R08_parts)
    return [_refine(s,cfg,positions.get(s['name'],[])) if is_target(s) else s for s in refined_R08_parts]


def shape(spec,bd):
    """Build true connected native solids, with real holes in each open web."""
    solids=[]
    for p in spec['pieces']:
        if p['kind']=='perforated_plate':
            outer=bd.Wire.make_polygon(p['outer'],close=True)
            holes=[bd.Wire.make_polygon(loop,close=True) for loop in p['holes']]
            face=bd.Face(outer,holes)
            solids.append(bd.Solid.extrude(face,p['extrusion']))
        elif p['kind']=='plate_loft':
            solids.append(bd.Solid.make_loft([bd.Wire.make_polygon(r,close=True) for r in p['sections']],ruled=True))
        else: raise ValueError('Unknown built-up piece kind: '+p['kind'])
    result=solids[0].fuse(*solids[1:])
    if len(result.solids())!=1 or not result.is_valid:
        raise ValueError('Built-up member is not one valid connected solid: '+spec['name'])
    return result


def faces(spec):
    """CAD-space triangular boundary faces, including every opening sidewall."""
    from ezdxf.math import Vec3
    from ezdxf.math.triangulation import mapbox_earcut_3d
    result=[]
    def triangle_face(loop,holes=(),normal=None):
        for tri in mapbox_earcut_3d([Vec3(q) for q in loop],[[Vec3(q) for q in h] for h in holes]):
            points=[list(q) for q in tri]
            if normal is not None and _dot(_cross(_sub(points[1],points[0]),_sub(points[2],points[0])),normal)<0:
                points.reverse()
            result.append(points)
    for p in spec['pieces']:
        if p['kind']=='perforated_plate':
            e=p['extrusion'];outer=p['outer'];holes=p['holes']
            triangle_face(outer,holes,_mul(e,-1))
            triangle_face([_add(q,e) for q in outer],[[_add(q,e) for q in h] for h in holes],e)
            for is_hole,loop in [(False,outer),*((True,h) for h in holes)]:
                centre=[sum(q[i] for q in loop)/len(loop) for i in range(3)]
                for a,b in zip(loop,loop[1:]+loop[:1]):
                    outward=_sub(centre,a) if is_hole else _sub(a,centre)
                    triangle_face([a,b,_add(b,e),_add(a,e)],normal=outward)
        else:
            a,b=p['sections'];axis=_sub(b[0],a[0])
            triangle_face(a,normal=_mul(axis,-1));triangle_face(b,normal=axis)
            for i in range(len(a)):
                j=(i+1)%len(a)
                triangle_face([a[i],a[j],b[j],b[i]],normal=_cross(_sub(a[j],a[i]),axis))
    return result
