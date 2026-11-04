"""R10 gross built-up Tokyo Tower legs and arches, fitted to reference photos.

The R09 member axes are retained as provenance and connection aliases. Four
corner submembers become one assembly with broad continuous cover plates and
real open side webs. Plate dimensions and opening layouts are assumptions, not
surveyed original sections. No CAD dependency is needed for parameter replay.
"""
from __future__ import annotations

from copy import deepcopy
from math import ceil, isfinite, sqrt
import re

DEFAULTS = {'cover_thickness_mm':20.,'web_thickness_mm':16.,
            'border_width_mm':180.,'batten_width_mm':180.,
            'pitch_depth_ratio':1.35,'min_cells':2,'max_cells':8,
            'diaphragm_length_mm':60.,'end_overlap_mm':40.,
            'diaphragm_edge_clearance_mm':1.,
            'seam_width_mm':120.,'max_pieces_per_assembly':24}


def _add(a,b):return [x+y for x,y in zip(a,b)]
def _sub(a,b):return [x-y for x,y in zip(a,b)]
def _mul(a,s):return [x*s for x in a]
def _dot(a,b):return sum(x*y for x,y in zip(a,b))
def _cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def _norm(a):return sqrt(_dot(a,a))
def _unit(a):return _mul(a,1/_norm(a))
def _mean(points):return [sum(q[i] for q in points)/len(points) for i in range(3)]
def _mix(a,b,t):return _add(_mul(a,1-t),_mul(b,t))


def _axis(s):
    return [list(s.get('axis_start',s.get('start'))),list(s.get('axis_end',s.get('end')))]


def _key(s,arch_last):
    n=s['name'];role=s.get('role')
    if role in ('primary_chord','leg_brace','leg_tie'):
        match=re.fullmatch(r'structure:leg_(\d+)_'+(r'chord_\d+_' if role=='primary_chord' else r'web_\d+_' if role=='leg_brace' else r'tie_\d+_')+r'(\d+)',n)
        if match:return ('leg',int(match[1]),int(match[2]))
    if s.get('steel_role')=='arch_plate_chord' or s.get('arch_member_kind')=='diagonal':
        return ('arch',s['arch_side'],s.get('arch_segment',int(n.rsplit('_',1)[1])))
    if s.get('arch_member_kind') in ('in_plane_tie','depth_tie'):
        return ('arch',s['arch_side'],min(int(n.rsplit('_',1)[1]),arch_last[s['arch_side']]))
    return None


def _name(key):
    kind,side,index=key
    return f'structure:leg_{side:02d}_assembly_{index:02d}' if kind=='leg' else f'structure:arch_assembly_{side}_{index:02d}'


def alias_map(specs):
    """Resolve every consumed R09 name to its current gross assembly."""
    return {old:s['name'] for s in specs for old in s.get('replaces_names',[])}


def _remap(s,aliases):
    result=deepcopy(s)
    for k in ('source_member','target_member','contact_with'):
        if result.get(k) in aliases:result[k]=aliases[result[k]]
    if 'member_names' in result:
        result['member_names']=list(dict.fromkeys(aliases.get(n,n) for n in result['member_names']))
    return result


def remap_node_catalog(catalog,specs):
    aliases=alias_map(specs)
    return [_remap(node,aliases) for node in catalog] if aliases else catalog


def _cfg(p):
    cfg={**DEFAULTS,**p['detail']['integrated_lower']}
    for k in DEFAULTS:
        if isinstance(cfg[k],bool) or not isinstance(cfg[k],(int,float)) or not isfinite(cfg[k]) or cfg[k]<=0:
            raise ValueError('Invalid integrated_lower setting: '+k)
    for k in ('min_cells','max_cells','max_pieces_per_assembly'):
        if not isinstance(cfg[k],int):raise ValueError('Integrated count must be an integer: '+k)
    if not 1<=cfg['min_cells']<=cfg['max_cells']<=16:raise ValueError('Invalid integrated cell budget')
    if not 10<=cfg['max_pieces_per_assembly']<=32:raise ValueError('Invalid integrated piece budget')
    if cfg['diaphragm_edge_clearance_mm']>=min(cfg['cover_thickness_mm'],cfg['web_thickness_mm'])/2:
        raise ValueError('Integrated diaphragm clearance must retain positive plate overlap')
    return cfg


def _leg_rings(members,leg):
    chords=sorted([s for s in members if s.get('role')=='primary_chord'],key=lambda s:s['name'])
    if len(chords)!=4:raise ValueError('A gross leg bay requires four source corner chords')
    axes=[_axis(s) for s in chords];centres=[_mean([a[i] for a in axes]) for i in (0,1)]
    rings=[]
    for i in (0,1):
        points=[q for s in chords for q in s['sections'][i]]
        x1,x2=min(q[0] for q in points),max(q[0] for q in points)
        y1,y2=min(q[1] for q in points),max(q[1] for q in points)
        z=centres[i][2]
        ring=[[x1,y1,z],[x2,y1,z],[x2,y2,z],[x1,y2,z]]
        # The same construction rotates with each perimeter leg; covers must
        # not remain on the same two global planes for all four legs.
        phase=(leg-1)%4
        rings.append([ring[(j+phase)%4] for j in range(4)])
    return rings,centres


def _arch_rings(members):
    chords={(s['arch_layer'],s['arch_lane']):s for s in members if s.get('steel_role')=='arch_plate_chord'}
    if len(chords)!=4:raise ValueError('A gross arch panel requires four source corner chords')
    axes={k:_axis(s) for k,s in chords.items()};centres=[_mean([a[i] for a in axes.values()]) for i in (0,1)]
    rings=[]
    for i in (0,1):
        out=[axes['outer',lane][i] for lane in (0,1)]
        inside=[axes['inner',lane][i] for lane in (0,1)]
        transverse=_unit(_sub(out[1],out[0]))
        def edge(layer,sign):
            chord=chords[layer,0];w=_unit(_sub(axes[layer,0][1],axes[layer,0][0]))
            v=_unit(_cross(w,transverse))
            inward=_sub(_mean(inside),_mean(out))
            if _norm(inward)<1e-6:inward=_mul(v,-1)
            if _dot(v,inward)<0:v=_mul(v,-1)
            half_depth=chord['source_section_profile']['depth_mm']/2
            half_width=chord['source_section_profile']['width_mm']/2
            return [_add(_add(axes[layer,lane][i],_mul(transverse,(-1 if lane==0 else 1)*half_width)),_mul(v,sign*half_depth)) for lane in (0,1)]
        outer=edge('outer',-1);inner=edge('inner',1)
        rings.append([outer[0],outer[1],inner[1],inner[0]])
    return rings,centres


def _ring(rings,t):return [_mix(a,b,t) for a,b in zip(*rings)]


def _inset_ring(ring,clearance):
    centre=_mean(ring)
    return [_add(q,_mul(_unit(_sub(centre,q)),clearance)) for q in ring]


def _loft(piece_id,rings,**data):
    rings=deepcopy(rings)
    direction=_sub(rings[1][0],rings[0][0])
    if _dot(_cross(_sub(rings[0][1],rings[0][0]),_sub(rings[0][2],rings[0][0])),direction)<0:
        rings=[list(reversed(r)) for r in rings]
    return {'piece_id':piece_id,'kind':'plate_loft','sections':rings,**data}


def _cover(rings,face,thick):
    i,j=face,(face+1)%4;profiles=[]
    for r in rings:
        centre=_mean(r);mid=_mean([r[i],r[j]]);inward=_mul(_unit(_sub(centre,mid)),thick)
        profiles.append([r[i],r[j],_add(r[j],inward),_add(r[i],inward)])
    return _loft('cover_'+str(face),profiles,member_function='gross_continuous_cover')


def _face_point(quad,x,t):return _mix(_mix(quad[0],quad[1],x),_mix(quad[3],quad[2],x),t)


def _web_piece(piece_id,outer,holes,centre,thick,opening):
    normal=_unit(_cross(_sub(outer[1],outer[0]),_sub(outer[2],outer[0])))
    if _dot(normal,_sub(centre,_mean(outer)))<0:normal=_mul(normal,-1)
    extrusion=_mul(normal,thick)
    probe=_add(_mean(holes[0]),_mul(extrusion,.5))
    return {'piece_id':piece_id,'kind':'perforated_plate','outer':outer,'holes':holes,
            'extrusion':extrusion,'void_probe_mm':probe,'opening_type':opening,
            'member_function':'gross_open_side_web'}


def _clip_opening(points,values,lo,hi):
    """Clip an opening against a station interval, retaining a real polygon."""
    polygon=list(zip(points,values))
    for edge,lower in ((lo,True),(hi,False)):
        clipped=[]
        for a,b in zip(polygon,polygon[1:]+polygon[:1]):
            inside_a=a[1]>=edge if lower else a[1]<=edge
            inside_b=b[1]>=edge if lower else b[1]<=edge
            if inside_a:clipped.append(a)
            if inside_a!=inside_b:
                t=(edge-a[1])/(b[1]-a[1]);clipped.append((_mix(a[0],b[0],t),edge))
        polygon=clipped
        if not polygon:return []
    return [q for q,_ in polygon] if len(polygon)>=3 else []


def _webs(rings,face,cfg,solid_spans,centre):
    i,j=face,(face+1)%4
    quad=[rings[0][i],rings[0][j],rings[1][j],rings[1][i]]
    normal=_unit(_cross(_sub(quad[1],quad[0]),_sub(quad[2],quad[0])))
    warp=abs(_dot(_sub(quad[3],quad[0]),normal))
    if warp<1e-4:
        length=(_norm(_sub(quad[3],quad[0]))+_norm(_sub(quad[2],quad[1])))/2
        depth=min(_norm(_sub(quad[1],quad[0])),_norm(_sub(quad[2],quad[3])))
        border=min(cfg['border_width_mm'],depth*.20)
        xmargin=border/depth
        cells=max(cfg['min_cells'],min(cfg['max_cells'],ceil(length/(depth*cfg['pitch_depth_ratio']))))
        half_batten=min(cfg['batten_width_mm']/length/2,.15/cells)
        holes=[]
        for cell in range(cells):
            intervals=[(cell/cells+half_batten,(cell+1)/cells-half_batten)]
            for a,b in solid_spans:
                intervals=[piece for lo,hi in intervals for piece in
                           ([(lo,hi)] if b<=lo or a>=hi else ([(lo,a)] if lo<a else [])+([(b,hi)] if b<hi else []))]
            for lo,hi in intervals:
                if hi-lo<.025:continue
                holes.append([_face_point(quad,x,t) for x,t in ((xmargin,lo),(1-xmargin,lo),(1-xmargin,hi),(xmargin,hi))])
        if not holes:raise ValueError('Gross planar web has no usable opening')
        return [_web_piece(f'web_{face}',quad,holes,centre,cfg['web_thickness_mm'],'quadrilateral_battened')]
    # A warped arch face is two genuinely planar triangular plates. Their
    # shared diagonal has a narrow solid splice strip, not a fake texture.
    pieces=[]
    for index,tri in enumerate(([quad[0],quad[1],quad[2]],[quad[0],quad[2],quad[3]])):
        lengths=[_norm(_sub(tri[(i+1)%3],tri[(i+2)%3])) for i in range(3)]
        inc=_mul([sum(tri[i][k]*lengths[i] for i in range(3)) for k in range(3)],1/sum(lengths))
        area=_norm(_cross(_sub(tri[1],tri[0]),_sub(tri[2],tri[0])))/2
        radius=2*area/sum(lengths);border=min(cfg['border_width_mm'],radius*.48)
        scale=1-border/radius;hole=[_add(inc,_mul(_sub(q,inc),scale)) for q in tri]
        station_values=[0.,0.,1.] if index==0 else [0.,1.,1.]
        centre_fraction=sum(lengths[i]*station_values[i] for i in range(3))/sum(lengths)
        values=[centre_fraction+(v-centre_fraction)*scale for v in station_values]
        allowed=[(0.,1.)]
        # Thin bulkheads may be inserted at actual connection stations. Keep
        # web holes clear of those solid slabs, including the face warp error.
        length=(_norm(_sub(quad[3],quad[0]))+_norm(_sub(quad[2],quad[1])))/2
        allowance=(warp+cfg['web_thickness_mm'])/length
        for a,b in solid_spans:
            a=max(0.,a-allowance);b=min(1.,b+allowance)
            allowed=[piece for lo,hi in allowed for piece in
                     ([(lo,hi)] if b<=lo or a>=hi else ([(lo,a)] if lo<a else [])+([(b,hi)] if b<hi else []))]
        holes=[clipped for lo,hi in allowed if hi-lo>.015 for clipped in [_clip_opening(hole,values,lo,hi)] if clipped]
        if not holes:raise ValueError('Gross triangular web has no usable opening')
        pieces.append(_web_piece(f'web_{face}_patch_{index}',tri,holes,centre,cfg['web_thickness_mm'],'triangular_laced'))
    a,b=quad[0],quad[2];w=_unit(_sub(b,a));n=_unit(_add(_unit(pieces[0]['extrusion']),_unit(pieces[1]['extrusion'])))
    across=_unit(_cross(w,n));width=cfg['seam_width_mm']/2;thick=cfg['web_thickness_mm']
    profiles=[[_add(q,_add(_mul(across,x),_mul(n,y))) for x,y in ((-width,-thick/2),(width,-thick/2),(width,thick*1.5),(-width,thick*1.5))] for q in (a,b)]
    pieces.append(_loft(f'web_{face}_diagonal_splice',profiles,member_function='planar_patch_splice'))
    return pieces


def _attachment_records(parts,aliases,by):
    records={}
    for s in parts:
        candidates=[]
        for field,index in (('source_member',0),('target_member',1)):
            points=s.get('attachment_points',[])
            if s.get(field) in aliases and len(points)>index:candidates.append((s[field],points[index]))
        if s.get('contact_with') in aliases:
            points=[q for section in s.get('sections',[]) for q in section]
            if points:candidates.append((s['contact_with'],_mean(points)))
        for old,point in candidates:
            a,b=_axis(by[old]);delta=_sub(b,a)
            t=max(0.,min(1.,_dot(_sub(point,a),delta)/_dot(delta,delta)))
            records.setdefault(aliases[old],[]).append({'legacy_member':old,'connection':s['name'],'point_mm':list(point),'station_fraction':t})
    return records


def _assembly(key,members,cfg,records):
    rings,centres=_leg_rings(members,key[1]) if key[0]=='leg' else _arch_rings(members)
    original_rings=deepcopy(rings);axis=_sub(centres[1],centres[0]);length=_norm(axis);w=_unit(axis)
    lap=cfg['end_overlap_mm'];rings=[[_add(q,_mul(w,-lap)) for q in rings[0]],[_add(q,_mul(w,lap)) for q in rings[1]]]
    body_length=length+2*lap;half=cfg['diaphragm_length_mm']/2/body_length
    spans=[(0.,2*half),(1-2*half,1.)]
    for record in records:
        t=(record['station_fraction']*length+lap)/body_length
        spans.append((max(0.,t-half),min(1.,t+half)))
    merged=[]
    for a,b in sorted(spans):
        if merged and a<=merged[-1][1]+1e-9:merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
        else:merged.append((a,b))
    pieces=[_cover(rings,face,cfg['cover_thickness_mm']) for face in (0,2)]
    for face in (1,3):pieces.extend(_webs(rings,face,cfg,merged,_mean(centres)))
    for i,(a,b) in enumerate(merged):
        # Slightly inset bulkheads overlap the thin plates by positive volume
        # while avoiding long exactly-coplanar outer edges in the native fuse.
        profiles=[_inset_ring(_ring(rings,t),cfg['diaphragm_edge_clearance_mm']) for t in (a,b)]
        pieces.append(_loft(f'diaphragm_{i:02d}',profiles,member_function='gross_attachment_diaphragm',
                            station_interval=[a,b],edge_clearance_mm=cfg['diaphragm_edge_clearance_mm']))
    if len(pieces)>cfg['max_pieces_per_assembly']:raise ValueError('Integrated assembly exceeds explicit piece budget')
    names=sorted(s['name'] for s in members);name=_name(key)
    source_axes={s['name']:{'axis_start':_axis(s)[0],'axis_end':_axis(s)[1]} for s in members}
    widths=[_norm(_sub(r[1],r[0])) for r in original_rings]
    depths=[_norm(_sub(r[3],r[0])) for r in original_rings]
    return {'group':'structure','name':name,'kind':'built_up','role':key[0]+'_assembly',
            'color':members[0]['color'],'axis_start':centres[0],'axis_end':centres[1],
            'built_up_family':'integrated_gross_battened' if key[0]=='leg' else 'integrated_gross_laced',
            'built_up_scope':'photo_guided_gross_assembly_not_surveyed',
            'pieces':pieces,'built_up_piece_budget':cfg['max_pieces_per_assembly'],
            'replaces_names':names,'legacy_member_axes':source_axes,'legacy_aliases':{n:name for n in names},
            'gross_source_sections':original_rings,'gross_sections':rings,'gross_axis_reference':'mean_of_four_legacy_corner_chords',
            'built_up_attachment_points':records,'assembly_side':key[1],'assembly_station':key[2],
            'profile_type':'integrated_built_up_battened' if key[0]=='leg' else 'integrated_built_up_laced',
            'section_profile':{'type':'integrated_open_built_up','cover_thickness_mm':cfg['cover_thickness_mm'],
                               'web_thickness_mm':cfg['web_thickness_mm'],'width_mm':max(widths),'depth_mm':max(depths),
                               'endpoint_widths_mm':widths,'endpoint_depths_mm':depths,
                               'dimensions_status':'photo_guided_demonstration_assumption'},
            'section_assumption':'One gross built-up assembly with continuous broad cover plates and genuinely open thin side webs; inherited corner positions and fitted end laps remain visual assumptions, not original rolled steel or structural design.'}


def refine_integrated(p,R09parts):
    setting=p.get('detail',{}).get('integrated_lower')
    if setting is not None and not isinstance(setting,dict):raise ValueError('integrated_lower must be a mapping')
    if setting and not isinstance(setting.get('enabled',False),bool):raise ValueError('integrated_lower enabled must be boolean')
    if not setting or not setting.get('enabled',False):return R09parts
    cfg=_cfg(p);groups={};by={s['name']:s for s in R09parts}
    arch_last={}
    for s in R09parts:
        if s.get('steel_role')=='arch_plate_chord':
            side=s['arch_side'];arch_last[side]=max(arch_last.get(side,-1),s['arch_segment'])
    for s in R09parts:
        key=_key(s,arch_last)
        if key:
            if s['kind']!='built_up' or not s.get('pieces'):
                raise ValueError('integrated_lower requires the enabled R09 lower_built_up refinement')
            groups.setdefault(key,[]).append(s)
    aliases={s['name']:_name(key) for key,members in groups.items() for s in members}
    records=_attachment_records(R09parts,aliases,by)
    assemblies={key:_assembly(key,members,cfg,records.get(_name(key),[])) for key,members in groups.items()}
    result=[];emitted=set()
    for s in R09parts:
        key=_key(s,arch_last)
        if key:
            if key not in emitted:result.append(assemblies[key]);emitted.add(key)
        else:result.append(_remap(s,aliases))
    return result
