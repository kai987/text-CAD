"""R15 authoring-to-world reflection. X points east; text is never reflected.

The internal authoring topology stays stable. Public plans, named CAD trees and
coordinate records are reflected once at their boundary, about X=width/2.
"""
from dataclasses import replace
from functools import wraps
from inspect import signature
import re


def canonical(p):
    return replace(p, mirror_layout=False) if getattr(p, 'mirror_layout', False) else p


def point(value, width):
    return [width-value[0], *value[1:]]


def bounds(value, width):
    n=len(value)//2
    return [width-value[n], *value[1:n], width-value[0], *value[n+1:]]


def side_name(value):
    return re.sub(r'(?<![a-z])(southwest|southeast|northwest|northeast|west|east)(?![a-z])',
                  lambda m: m[0].replace('west','east') if 'west' in m[0] else m[0].replace('east','west'), value)


def shape(value, width, parent_location=None):
    from cadgen import build123d as bd
    if not value:
        empty=bd.Compound(label=side_name(value.label));empty.color=value.color
        return empty
    parent_location=parent_location or bd.Location()
    world_location=parent_location*value.location
    if value.children:
        mirrored=bd.Compound(children=[shape(child,width,world_location) for child in value.children],label=side_name(value.label))
    else:
        # Strip assembly ancestry before build123d deepcopy-based transforms.
        # Copying a parented leaf otherwise duplicates the whole house per leaf.
        local=bd.Compound.cast(value.wrapped)
        mirrored=local.located(world_location).mirror(bd.Plane(origin=(width/2,0,0),z_dir=(1,0,0)))
        mirrored.label=side_name(value.label)
    mirrored.color=value.color
    return mirrored


def record(value, width, key=''):
    """Reflect explicit coordinate fields, retaining dimensions, areas and IDs."""
    if isinstance(value,dict):
        result={side_name(k):record(v,width,k) for k,v in value.items()}
        if 'x' in value: result['x']=width-value['x']
        if 'axis' in value and 'at' in value:
            if value['axis']=='h':
                if 'end' in value: result.update(start=width-value['end'],end=width-value['start'])
            else:
                result['at']=width-value['at']
                if 'normal_start' in value:result['normal_start']=width-value['normal_start']-value['thickness']
        for left,right in [('deck_left','deck_right'),('ceiling_left','ceiling_right')]:
            if left in value and right in value:result[left],result[right]=width-value[right],width-value[left]
        if 'hatch_x' in value: result['hatch_x']=width-value['hatch_x']-value['hatch_length']
        for name in value:
            if name.endswith('_west') and name[:-5]+'_east' in value and isinstance(value[name],(int,float)):
                right=name[:-5]+'_east';result[name],result[right]=width-value[right],width-value[name]
        return result
    if isinstance(value,(list,tuple)):
        if value and all(isinstance(v,(int,float)) for v in value):
            if len(value) in (4,6) and ('bounds' in key or 'outline' in key or key.endswith('_envelopes_mm') or key in ('hatch','footprint_mm')):return bounds(value,width)
            if len(value)==4 and isinstance(value,tuple):return tuple(bounds(value,width))
            if key in ('mount_center_mm','light_position_mm','target_mm','head_origin_mm','top_mm','foot_mm'):return point(value,width)
            if key in ('light_position_glb_m','target_glb_m'):return point(value,width/1000)
            if key in ('direction_cad','direction_glb'):return [-value[0],*value[1:]]
            if key in ('car_clear_opening_mm','pedestrian_clear_opening_mm'):return [width-value[1],width-value[0]]
            if key=='purlin_x':return sorted(width-v for v in value)
            if key=='finished_ceiling_profile_xz_mm':return point(value,width)
        return [record(v,width,key) for v in value]
    if isinstance(value,str) and key in ('id','name','member','mount_to','label'):return side_name(value)
    return value


def oriented(transform):
    """Normalize explicit p inside a builder; transform its result exactly once."""
    def decorate(fn):
        sig=signature(fn)
        @wraps(fn)
        def call(*args,**kwargs):
            bound=sig.bind(*args,**kwargs);bound.apply_defaults();p=bound.arguments['p']
            if not getattr(p,'mirror_layout',False):return fn(*args,**kwargs)
            bound.arguments['p']=canonical(p)
            return transform(fn(*bound.args,**bound.kwargs),p.width)
        return call
    return decorate


orient_shape=oriented(shape)
orient_record=oriented(record)
