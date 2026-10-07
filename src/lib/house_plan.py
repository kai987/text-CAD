"""Active user-requested R21 reflected layout; historical R01 data is in house_plan_r01.

Compatibility dimension names describe canonical authoring partitions; public floor plans are world-space. Normalize p with orientation.canonical before creating nested builders. All values are demo inputs.
"""
from .house_plan_r01 import Door, Floor, Room, rectangle
from .house_redesign_plan import P, RedesignParameters as Parameters, floor_plan, manifest
from .house_redesign_plan import dimensions as redesign_dimensions


def dimensions(p=P):
    d=redesign_dimensions(p)
    return dict(d,xmax=d['xm'],ymax=d['ym'],ldk_right=d['wcr'],
                south_top=d['st'],master_right=p.access_left-p.internal_wall,
                bath_right=d['bathr'],wash_left=d['bathr']+p.internal_wall,
                wash_right=d['wcl']-p.internal_wall,wc_left=d['wcl'],
                wc_bottom=d['ym']-p.toilet_depth)


def design_manifest(p=P):
    data=manifest(p)
    data['drawing_revision']='R21'
    return data
