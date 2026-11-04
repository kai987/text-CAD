"""R11 continuation of the fitted four-column lower face grid to GL120m.

This opt-in pass replaces the former large face diagonals and dense belts.
The inherited gross legs, arches and upper primary chords are unchanged.
Member dimensions, grid stations and local clips are photo-guided assumptions.
"""
from __future__ import annotations

from copy import deepcopy
from math import isfinite, sqrt
import re

DEFAULTS={'band_levels_mm':[80000.,93000.,106000.,120000.], 'columns':4,
          'primary_brace_radius_mm':160.,'secondary_brace_radius_mm':105.,
          'vertical_radius_mm':110.,'belt_radius_mm':200.,
          'corner_clip_radius_mm':90.,'support_link_radius_mm':110.,
          'corner_clip_source_overlap_mm':20.,
          'support_height_mm':114000.}
_PATTERN=re.compile(r'structure:upper_(diagonal|return|secondary|secondary_return|vertical|ring)_(\d+)_(\d+)$')


def _add(a,b):return [x+y for x,y in zip(a,b)]
def _sub(a,b):return [x-y for x,y in zip(a,b)]
def _dot(a,b):return sum(x*y for x,y in zip(a,b))
def _norm(a):return sqrt(_dot(a,a))
def _mix(a,b,t):return [x*(1-t)+y*t for x,y in zip(a,b)]
def _axis(s):return list(s.get('axis_start',s.get('start'))),list(s.get('axis_end',s.get('end')))
def _at_z(a,b,z):return _mix(a,b,(z-a[2])/(b[2]-a[2]))
def _node_key(p):return tuple(round(v,5) for v in p)


def is_replaced(spec,start=80000.,end=120000.):
    match=_PATTERN.fullmatch(spec['name'])
    if not match:return False
    a,b=_axis(spec)
    return start-1e-6<=min(a[2],b[2]) and max(a[2],b[2])<=end+1e-6 and max(a[2],b[2])>start+1e-6


def _config(p):
    cfg={**DEFAULTS,**p['detail']['lower_grid_continuity']}
    levels=cfg['band_levels_mm']
    if not isinstance(levels,list) or len(levels)!=4 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(v) for v in levels):
        raise ValueError('Grid continuity needs four finite station heights')
    if levels[0]!=80000 or levels[-1]!=120000 or any(b<=a for a,b in zip(levels,levels[1:])):
        raise ValueError('Grid continuity must have three increasing bands from GL80m to GL120m')
    if isinstance(cfg['columns'],bool) or cfg['columns']!=4 or not isinstance(cfg['columns'],int):
        raise ValueError('Grid continuity requires four columns')
    for key in DEFAULTS:
        if key in ('band_levels_mm','columns'):continue
        v=cfg[key]
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not isfinite(v) or v<=0:
            raise ValueError('Invalid grid continuity setting: '+key)
    if not levels[0]<cfg['support_height_mm']<levels[-1]:raise ValueError('Grid support must lie inside the replacement interval')
    return cfg


def _legacy_corner_axes(assembly):
    return [v for n,v in assembly['legacy_member_axes'].items() if re.fullmatch(r'structure:leg_\d+_chord_\d+_\d+',n)]


def _leg_at_z(parts,corner,z):
    candidates=[]
    for s in parts:
        if s.get('role')!='leg_assembly' or s.get('assembly_side')!=corner+1:continue
        axes=_legacy_corner_axes(s)
        lo=min(v['axis_start'][2] for v in axes);hi=max(v['axis_end'][2] for v in axes)
        if lo-1e-6<=z<=hi+1e-6:candidates.append(s)
    if not candidates:raise ValueError('No unchanged R10 gross leg at grid station')
    return min(candidates,key=lambda s:min(abs(s['axis_start'][2]-z),abs(s['axis_end'][2]-z)))


def _outer_radius(parts,z):
    assembly=_leg_at_z(parts,0,z)
    points=[_at_z(v['axis_start'],v['axis_end'],z) for v in _legacy_corner_axes(assembly)]
    return -min(q[0] for q in points)


def _face(side,q,r,z):
    return ([q*r,-r,z] if side==0 else [r,q*r,z] if side==1 else
            [-q*r,r,z] if side==2 else [-r,-q*r,z])


def _cover_mount(assembly,point,z):
    """Project to the centre of an actual uninterrupted R10 cover plate."""
    candidates=[]
    for piece in assembly['pieces']:
        if piece.get('member_function')!='gross_continuous_cover':continue
        first,last=piece['sections'];t=(z-first[0][2])/(last[0][2]-first[0][2])
        section=[_mix(a,b,t) for a,b in zip(first,last)]
        limits=[(min(q[i] for q in section),max(q[i] for q in section)) for i in (0,1)]
        thin=min((0,1),key=lambda i:limits[i][1]-limits[i][0]);along=1-thin
        target=list(point);target[thin]=sum(limits[thin])/2
        target[along]=max(limits[along][0]+1,min(limits[along][1]-1,point[along]));target[2]=z
        candidates.append((_norm(_sub(target,point)),target,piece['piece_id']))
    if not candidates:raise ValueError('Gross leg has no real continuous cover to mount grid')
    _,target,piece_id=min(candidates,key=lambda x:x[0])
    return target,piece_id


def _beam(name,a,b,radius,role,**metadata):
    return {'group':'structure','name':'structure:'+name,'kind':'beam','start':list(a),'end':list(b),
            'axis_start':list(a),'axis_end':list(b),'radius':radius,'color':'#E34C25','role':role,**metadata}


def _primary_grid(cfg,parts):
    levels=cfg['band_levels_mm'];radii=[_outer_radius(parts,z) for z in levels];raw=[]
    # Exact reuse of the retained GL80m face axes, including the quarter nodes.
    old=next(s for s in parts if s['name']=='structure:lower_belt_0_2')
    radii[0]=abs(_axis(old)[0][0])
    for side in range(4):
        for band,(za,zb) in enumerate(zip(levels,levels[1:])):
            aa=[_face(side,-1+2*i/4,radii[band],za) for i in range(5)]
            bb=[_face(side,-1+2*i/4,radii[band+1],zb) for i in range(5)]
            common={'grid_side':side,'grid_band':band,'grid_levels_mm':list(levels),'grid_band_levels_mm':[za,zb],
                    'grid_scope':'photo_guided_four_column_continuation_not_structural_design'}
            raw.append(_beam(f'grid_belt_{side}_{band}',bb[0],bb[-1],cfg['belt_radius_mm'],'lower_belt',grid_column=None,**common))
            for col in range(4):
                raw.append(_beam(f'grid_panel_a_{side}_{band}_{col}',aa[col],bb[col+1],cfg['primary_brace_radius_mm'],'lower_panel_brace',grid_column=col,grid_diagonal='a',**common))
                raw.append(_beam(f'grid_panel_b_{side}_{band}_{col}',aa[col+1],bb[col],cfg['secondary_brace_radius_mm'],'lower_panel_brace',grid_column=col,grid_diagonal='b',**common))
            for col in (1,2,3):raw.append(_beam(f'grid_vertical_{side}_{band}_{col}',aa[col],bb[col],cfg['vertical_radius_mm'],'lower_panel_vertical',grid_column=col,**common))
    return raw,radii


def _native_open_grid(p,raw,cfg):
    from .tokyo_tower_builtup import refine_built_up
    if not p.get('detail',{}).get('lower_built_up',{}).get('enabled'):
        raise ValueError('Grid continuity requires enabled R09 lower_built_up profiles')
    joints=[]
    for belt in [s for s in raw if s['role']=='lower_belt']:
        a,b=_axis(belt)
        for col in (1,2,3):
            joints.append({'name':belt['name']+f'_joint_descriptor_{col}','kind':'reference',
                           'source_member':belt['name'],'attachment_points':[_mix(a,b,col/4)]})
    refined=refine_built_up(p,[*raw,*joints])[:len(raw)]
    roles={'lower_belt':'grid_belt','lower_panel_brace':'grid_panel_brace','lower_panel_vertical':'grid_panel_vertical'}
    for s in refined:s['role']=roles[s['role']]
    return refined


def _clips(cfg,parts,grid,radii):
    result=[];levels=cfg['band_levels_mm']
    for station,z in enumerate(levels):
        for corner in range(4):
            point=_face(corner,-1,radii[station],z);host=_leg_at_z(parts,corner,z)
            target,piece=_cover_mount(host,point,z)
            delta=_sub(target,point);distance=_norm(delta)
            start=_sub(point,[v/distance*cfg['corner_clip_source_overlap_mm'] for v in delta])
            incident=[s['name'] for s in grid if any(_node_key(q)==_node_key(point) for q in _axis(s))]
            result.append(_beam(f'grid_corner_link_{corner}_{station}',start,target,cfg['corner_clip_radius_mm'],'grid_attachment',
                                grid_corner=corner,grid_station=station,level_mm=z,source_members=incident,
                                target_member=host['name'],target_piece_id=piece,attachment_points=[point,target],
                                nominal_axis_start=point,nominal_axis_end=target,source_embedding_mm=cfg['corner_clip_source_overlap_mm'],
                                attachment_scope='short_visible_clip_to_actual_solid_R10_cover'))
    return result


def _support_links(cfg,parts):
    result=[];z=cfg['support_height_mm'];r=_outer_radius(parts,z)
    for corner in range(4):
        candidates=[s for s in parts if s['name'].startswith(f'structure:upper_chord_{corner}_') and
                    min(q[2] for q in _axis(s))-1e-6<=z<=max(q[2] for q in _axis(s))+1e-6]
        if not candidates:raise ValueError('No retained upper primary at actual support height')
        source=max(candidates,key=lambda s:_axis(s)[1][2]);point=_at_z(*_axis(source),z)
        host=_leg_at_z(parts,corner,z);desired=_face(corner,-1,r,z);target,piece=_cover_mount(host,desired,z)
        result.append(_beam(f'grid_support_link_{corner}',point,target,cfg['support_link_radius_mm'],'grid_support_link',
                            grid_corner=corner,level_mm=z,source_member=source['name'],
                            attached_members=sorted(s['name'] for s in candidates),target_member=host['name'],
                            target_piece_id=piece,attachment_points=[point,target],
                            attachment_scope='short_local_support_at_retained_historical_belt_height'))
    return result


def _connections(grid,clips):
    nodes={}
    for s in grid:
        for p in _axis(s):nodes.setdefault(_node_key(p),[]).append(s['name'])
        if s['role']=='grid_belt':
            a,b=_axis(s)
            for col in (1,2,3):nodes.setdefault(_node_key(_mix(a,b,col/4)),[]).append(s['name'])
    for s in clips:nodes.setdefault(_node_key(s['attachment_points'][0]),[]).append(s['name'])
    for s in grid:
        ends=[]
        for point in _axis(s):
            names=[n for n in nodes[_node_key(point)] if n!=s['name']]
            if abs(point[2]-80000)<1e-6:
                side=s['grid_side'];names.append(f'structure:lower_belt_{side}_2')
            ends.append(list(dict.fromkeys(names)))
        s['endpoint_connection_names']=ends


def remap_node_catalog(catalog,specs):
    audit=next((s for s in specs if 'grid_catalog_aliases' in s),None)
    if audit is None:return catalog
    aliases=audit['grid_catalog_aliases'];removed=set(audit['grid_replaced_names']);by={s['name']:s for s in specs}
    result=[]
    for row in catalog:
        item=deepcopy(row);names=[];primary=row['member_names'][0]
        for name in row['member_names']:
            if name in aliases:
                matches=[candidate for candidate in aliases[name] if primary in by[candidate]['attached_members']]
                if not matches:raise ValueError('No actual local support for removed node-catalog member: '+name)
                names.extend(matches)
            elif name in removed:raise ValueError('Removed grid member has no physical node-catalog replacement: '+name)
            else:names.append(name)
        item['member_names']=list(dict.fromkeys(names));result.append(item)
    return result


def refine_grid(p,R10specs):
    setting=p.get('detail',{}).get('lower_grid_continuity')
    if setting is not None and not isinstance(setting,dict):raise ValueError('lower_grid_continuity must be a mapping')
    if setting and not isinstance(setting.get('enabled',False),bool):raise ValueError('Grid continuity enabled must be boolean')
    if not setting or not setting.get('enabled',False):return R10specs
    cfg=_config(p);removed=[s for s in R10specs if is_replaced(s)]
    if not removed:raise ValueError('Grid continuity requires the unchanged R10 upper face source members')
    raw,radii=_primary_grid(cfg,R10specs);grid=_native_open_grid(p,raw,cfg)
    clips=_clips(cfg,R10specs,grid,radii);support=_support_links(cfg,R10specs);_connections(grid,clips)
    aliases={}
    for s in removed:
        match=_PATTERN.fullmatch(s['name'])
        if match[1]=='ring' and abs(_axis(s)[0][2]-cfg['support_height_mm'])<1e-6:
            side=int(match[2]);aliases[s['name']]=[f'structure:grid_support_link_{side}',f'structure:grid_support_link_{(side+1)%4}']
    grid[0].update(grid_replaced_names=sorted(s['name'] for s in removed),
                   grid_legacy_member_axes={s['name']:{'axis_start':_axis(s)[0],'axis_end':_axis(s)[1]} for s in removed},
                   grid_catalog_aliases=aliases,grid_face_radii_mm=radii)
    removed_names={s['name'] for s in removed}
    return [s for s in R10specs if s['name'] not in removed_names]+grid+clips+support
