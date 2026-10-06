"""Named R12 cantilever balcony proposal; no structural adequacy claim."""
from dataclasses import asdict, dataclass

from cadgen import build123d as bd
from .house_redesign_plan import dimensions, balcony_drying_bounds


@dataclass(frozen=True)
class BalconyParameters:
    slab_thickness: float = 150
    finish_thickness: float = 25
    guard_height: float = 1100
    guard_bar_width: float = 25
    post_width: float = 100
    footing_width: float = 450
    footing_bottom_z: float = -850
    footing_top_z: float = -450


B=BalconyParameters()


def support_positions(p):
    """Keep west/east CAD identifiers stable; add a midpoint on wider balconies."""
    if not p.balcony_supports:
        return ()
    x1=dimensions(p)["bx"]+p.balcony_rail_thickness/2
    x2=dimensions(p)["bx"]+p.balcony_width-p.balcony_rail_thickness/2
    return (x1,x2,(x1+x2)/2) if x2-x1>4000 else (x1,x2)


def balcony_group(p,g,b=B):
    from .house_geometry import cuboid,named
    d=dimensions(p);x1=d['bx'];x2=x1+p.balcony_width;y1=-p.balcony_depth;z=p.storey_height
    r=p.balcony_rail_thickness
    parts=[cuboid((x1,y1,z-b.slab_thickness,x2,0,z-b.finish_thickness),'balcony:slab','concrete'),
           cuboid((x1+r,y1+r,z-b.finish_thickness,x2-r,0,z),'balcony:finish','site_paving')]
    # Open aluminium rail: lower and upper rails plus individual vertical bars.
    for side,bounds in [('south',(x1,y1,x2,y1+r)),('west',(x1,y1+r,x1+r,0)),('east',(x2-r,y1+r,x2,0))]:
        a,c,aa,cc=bounds
        for tag,h in [('lower',80),('top',b.guard_height-b.guard_bar_width)]:
            parts.append(cuboid((a,c,z+h,aa,cc,z+h+b.guard_bar_width),f'balcony:{side}_rail_{tag}','charcoal'))
        length=(aa-a) if side=='south' else (cc-c)
        count=int(length/110)+1
        for i in range(count+1):
            offset=(length-b.guard_bar_width)*i/count
            bx,by=(a+offset,c) if side=='south' else (a,c+offset)
            parts.append(cuboid((bx,by,z+80,bx+(b.guard_bar_width if side=='south' else r),
                                 by+(r if side=='south' else b.guard_bar_width),z+b.guard_height),
                                f'balcony:{side}_bar_{i:02d}','charcoal'))
    for i,x in enumerate(support_positions(p),1):
        y=y1+r/2;half=b.post_width/2;fw=b.footing_width/2
        parts.extend([cuboid((x-half,y-half,b.footing_top_z,x+half,y+half,z-b.slab_thickness),
                            f'balcony:support_post_{i}','charcoal'),
                      cuboid((x-fw,y-fw,b.footing_bottom_z,x+fw,y+fw,b.footing_top_z),
                            f'balcony:footing_{i}','concrete')])
    dl,dy,dr,_=balcony_drying_bounds(p)
    for i,x in enumerate((dl,dr),1):
        parts.append(cuboid((x-15,dy,z,x+15,dy+30,z+1600),f'balcony:drying_post_{i}','charcoal'))
    parts.append(cuboid((dl,dy,z+1575,dr,dy+30,z+1600),'balcony:drying_rail','charcoal'))
    # An exposed scupper placeholder labels drainage rather than implying a
    # finished waterproofing detail or simulated water flow.
    parts.append(cuboid((x2-r,-400,z-50,x2+60,-300,z-25),'balcony:drain_outlet','frame'))
    return bd.Compound(children=parts,label='balcony')
