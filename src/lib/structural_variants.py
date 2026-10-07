"""R07 material alternatives: editable geometry, never calculated capacity.

W retains the R06 timber candidate. S models thin-wall hollow members and
strap bracing, rather than calling a recoloured timber or heavy H-frame light
steel. RC preserves the user-confirmed interior perimeter faces by projecting its
300 mm column/beam band outside the 180 mm architectural wall. That exterior
coordination conflict is explicit. Every section and foundation is an assumed
drawing input; material grades, connections, loads and results remain unset.
"""
from __future__ import annotations

from .orientation import orient_shape, orient_record

from dataclasses import asdict, dataclass
from math import ceil, radians, sqrt, tan

from cadgen import build123d as bd, srgb
from cadgen.geometry import overlap_volume
from shapely.geometry import box
from shapely.ops import unary_union

from .attic_geometry import A
from .house_geometry import G, extruded_polygon, opening_box, polygons, window_vertical_range
from .house_plan import P, floor_plan
from .native_spatial import aabb_candidates
from .site_geometry import foundation_group
from .structure_geometry import (floor_beam_segments,attic_beam_opening,T, _beam_segments, _bounds, _positions,
    bearing_wall_candidates, column_layout, foundation_support_segments,
    structure_dimensions, structure_group, structure_manifest)


@dataclass(frozen=True)
class SteelParameters:
    exterior_column_width: float = 120
    interior_column_width: float = 90
    column_wall_thickness: float = 2.3
    beam_wall_thickness: float = 3.2
    joist_wall_thickness: float = 2.3
    roof_wall_thickness: float = 2.3
    brace_width: float = 60
    brace_thickness: float = 2
    gusset_width: float = 100
    gusset_thickness: float = 4
    base_plate_thickness: float = 16
    base_plate_edge_allowance: float = 20
    foundation_raft_thickness: float = 200
    foundation_raft_top_z: float = -800
    foundation_stem_width: float = 180
    foundation_top_z: float = -200


@dataclass(frozen=True)
class ConcreteParameters:
    column_width: float = 300
    beam_width: float = 300
    beam_depth: float = 400
    floor_slab_thickness: float = 180
    attic_slab_thickness: float = 180
    roof_slab_vertical_thickness: float = 120
    shear_wall_thickness: float = 300
    foundation_raft_thickness: float = 300
    foundation_raft_top_z: float = -900
    foundation_stem_width: float = 300
    foundation_top_z: float = -200


S, RC = SteelParameters(), ConcreteParameters()


def named(shape, label, color):
    if isinstance(shape,list):shape=bd.Compound(shape)
    shape.label, shape.color = label, srgb(color)
    return shape


def solid_box(bounds, label, color):
    x1, y1, z1, x2, y2, z2 = bounds
    return named(bd.Box(x2-x1, y2-y1, z2-z1, align=(bd.Align.MIN,)*3)
                 .moved(bd.Location((x1,y1,z1))), label, color)


def shape_bounds(shape):
    b = shape.bounding_box()
    return [b.min.X,b.min.Y,b.min.Z,b.max.X,b.max.Y,b.max.Z]


def leaves(shape):
    if not shape.children:
        yield shape
    else:
        for child in shape.children:
            yield from leaves(child)


def _tube(start, end, width, depth, thickness, label, color="#8C9CA7"):
    """One straight rectangular hollow thin-wall section with open ends.

    width/depth are perpendicular to the member axis. Sloped roof members use
    the true perpendicular depth; vertical envelope allowances are adapted by
    the caller. The unassigned manufacturing specification is not inferred.
    """
    vector=tuple(b-a for a,b in zip(start,end)); length=sqrt(sum(v*v for v in vector))
    if length<=0 or min(width,depth)<=2*thickness or thickness<=0:
        raise ValueError("Invalid thin-wall section or member length")
    direction=tuple(v/length for v in vector)
    if abs(direction[2])>.999:
        u,v=(1.,0.,0.),(0.,1.,0.)
    else:
        planar=sqrt(direction[0]**2+direction[1]**2)
        u=(-direction[1]/planar,direction[0]/planar,0.)
        v=(direction[1]*u[2]-direction[2]*u[1],
           direction[2]*u[0]-direction[0]*u[2],
           direction[0]*u[1]-direction[1]*u[0])
    def wire(w,d):
        return bd.Wire.make_polygon([tuple(start[i]+a*u[i]+b*v[i] for i in range(3))
            for a,b in [(-w/2,-d/2),(w/2,-d/2),(w/2,d/2),(-w/2,d/2)]])
    face=bd.Face(wire(width,depth),[wire(width-2*thickness,depth-2*thickness)])
    return named(bd.extrude(face,amount=length,dir=direction),label,color)


def _axis_tube(bounds, axis, thickness, label, color="#8C9CA7"):
    x1,y1,z1,x2,y2,z2=bounds
    if axis=="h":
        return _tube((x1,(y1+y2)/2,(z1+z2)/2),(x2,(y1+y2)/2,(z1+z2)/2),
                     y2-y1,z2-z1,thickness,label,color)
    if axis=="v":
        return _tube(((x1+x2)/2,y1,(z1+z2)/2),((x1+x2)/2,y2,(z1+z2)/2),
                     x2-x1,z2-z1,thickness,label,color)
    return _tube(((x1+x2)/2,(y1+y2)/2,z1),((x1+x2)/2,(y1+y2)/2,z2),
                 x2-x1,y2-y1,thickness,label,color)


def _profile_parts(profile,z1,z2,label,color):
    pieces=[extruded_polygon(poly,z1,z2-z1) for poly in polygons(profile)]
    return named(pieces[0] if len(pieces)==1 else bd.Compound(pieces),label,color)


def _foundation(p, width, raft_top, raft_thickness, top, projection=0):
    """Raft and nonduplicating perimeter/internal ribs; no reinforcement claim."""
    outer=box(-projection,-projection,p.width+projection,p.depth+projection)
    inner=box(width-projection,width-projection,
              p.width+projection-width,p.depth+projection-width)
    perimeter=outer.difference(inner)
    raft=_profile_parts(outer,raft_top-raft_thickness,raft_top,"foundation:raft:slab","#9DA29F")
    stem=_profile_parts(perimeter,raft_top,top,"foundation:stem_walls:perimeter","#AEB2AE")
    occupied=perimeter
    ribs=[]
    for index, segment in enumerate(foundation_support_segments(p),1):
        axis,at,start,end=(segment[k] for k in ("axis","at","start","end"))
        footprint=box(start,at-width/2,end,at+width/2) if axis=="h" else box(at-width/2,start,at+width/2,end)
        profile=footprint.intersection(outer).difference(occupied)
        occupied=occupied.union(footprint)
        if not profile.is_empty and profile.area>.01:
            ribs.append(_profile_parts(profile,raft_top,top,f"foundation:internal_supports:I{index:02d}","#AEB2AE"))
    return bd.Compound(children=[bd.Compound(children=[raft],label="foundation:raft"),
        bd.Compound(children=[stem],label="foundation:stem_walls"),
        bd.Compound(children=ribs,label="foundation:internal_supports")],label="foundation")


def timber_variant(p=P,g=G):
    foundation=foundation_group(p,g)
    for item in leaves(foundation):
        item.label=item.label.replace('F1:exterior:foundation:', 'foundation:existing_plinth:')
    return bd.Compound(children=[structure_group(p,g),foundation],label="variant_W")


def _brace(wall,bottom,top,index,n,s=S):
    """Opposite 2 mm straps in separate depth bands, with endpoint gussets."""
    start,end=wall["start"],wall["end"]; normal=wall["normal_start"]
    width=s.brace_width; length=sqrt((end-start)**2+(top-bottom)**2)
    delta=width/2*(top-bottom)/length
    dz=width/2*(end-start)/length
    pieces=[]
    for suffix,a,b,za,zb,offset in (("A",start,end,bottom,top,0),("B",start,end,top,bottom,s.brace_thickness+.5)):
        signed=1 if zb>za else -1
        points=[(a-delta,za+signed*dz),(b-delta,zb+signed*dz),
                (b+delta,zb-signed*dz),(a+delta,za-signed*dz)]
        if wall["axis"]=="h":
            face=bd.Face(bd.Wire.make_polygon([(x,normal+offset,z) for x,z in points]))
            brace=bd.extrude(face,amount=s.brace_thickness,dir=(0,1,0))
            clip=solid_box((start,normal,bottom,end,normal+wall["thickness"],top),"clip","#FFFFFF")
        else:
            face=bd.Face(bd.Wire.make_polygon([(normal+offset,x,z) for x,z in points]))
            brace=bd.extrude(face,amount=s.brace_thickness,dir=(1,0,0))
            clip=solid_box((normal,start,bottom,normal+wall["thickness"],end,top),"clip","#FFFFFF")
        brace=brace.intersect(clip)
        pieces.append(named(brace,f"structure:F{n}:strap_brace_BW{index:02d}_{suffix}","#D18B55"))
    # These only depict where a tested connection must be developed. They do
    # not encode hole spacing, bolts, anchors or any connection resistance.
    for suffix,along,z in (("SW",start,bottom),("SE",end-s.gusset_width,bottom),
                           ("NW",start,top-s.gusset_width),("NE",end-s.gusset_width,top-s.gusset_width)):
        extent=min(s.gusset_width,end-start)
        coords=(along,normal,z,along+extent,normal+s.gusset_thickness,z+extent) if wall["axis"]=="h" else \
               (normal,along,z,normal+s.gusset_thickness,along+extent,z+extent)
        pieces.append(solid_box(coords,f"structure:F{n}:gusset_BW{index:02d}_{suffix}","#748793"))
    return pieces


def steel_variant(p=P,g=G,s=S):
    d=structure_dimensions(p,g)
    columns=[];beams=[];sills=[];braces=[];joists=[];headers=[];roof=[]
    for n in (1,2):
        bottom=d["sill_top_z"]+s.base_plate_thickness if n==1 else d["F1_beam_top_z"]
        top=d[f"F{n}_beam_bottom_z"]
        for c in column_layout(p):
            if n not in c["floors"]:continue
            width=s.exterior_column_width if c["width"]==T.external_column_width else s.interior_column_width
            h=width/2
            columns.append(_axis_tube((c["x"]-h,c["y"]-h,bottom,c["x"]+h,c["y"]+h,top),
                                      "z",s.column_wall_thickness,f"structure:F{n}:column_{c['id']}"))
        current=[]
        for segment in floor_beam_segments(n,p):
            shape=_axis_tube(_bounds(segment,d[f"F{n}_beam_bottom_z"],d[f"F{n}_beam_top_z"]),
                             segment["axis"],s.beam_wall_thickness,f"structure:F{n}:beam_{segment['id']}")
            if n==2:
                opening=attic_beam_opening(p,d[f"F{n}_beam_bottom_z"],d[f"F{n}_beam_top_z"])
                if _overlap(shape,opening)>.01:shape=named(shape.cut(opening),shape.label,"#8C9CA7")
            cutters=[prior for prior in current if all(shape_bounds(shape)[i]<shape_bounds(prior)[i+3] and shape_bounds(prior)[i]<shape_bounds(shape)[i+3] for i in range(3))]
            if cutters:shape=named(shape.cut(*cutters),shape.label,"#8C9CA7")
            current.append(shape)
        beams.extend(current)
        for i,wall in enumerate(bearing_wall_candidates(p),1):
            braces.extend(_brace(wall,bottom,top,i,n,s))
    for c in column_layout(p):
        width=c["width"]+2*s.base_plate_edge_allowance;h=width/2
        sills.append(solid_box((c["x"]-h,c["y"]-h,s.foundation_top_z,c["x"]+h,c["y"]+h,
                               s.foundation_top_z+s.base_plate_thickness),f"structure:F1:base_plate_{c['id']}","#748793"))
    for segment in _beam_segments(p):
        sills.append(_axis_tube(_bounds(segment,d["sill_bottom_z"]+s.base_plate_thickness,d["sill_top_z"]+s.base_plate_thickness),
                               segment["axis"],s.beam_wall_thickness,f"structure:F1:sill_{segment['id']}"))
    # Retain the timber candidate's coordinated joist/header placement while
    # replacing its solid cross-sections with real hollow profiles.
    reference=structure_group(p,g)
    roof_source=[]
    for item in leaves(reference):
        label=item.label;b=shape_bounds(item)
        if ':attic:joist_' in label:
            joists.append(named(_axis_tube(b,"v",s.joist_wall_thickness,label).intersect(item),label,"#8C9CA7"))
        elif ':attic:trimmer_' in label:
            headers.append(named(_axis_tube(b,"v",s.joist_wall_thickness,label).intersect(item),label,"#8C9CA7"))
        elif ':attic:header_' in label:
            headers.append(_axis_tube(b,"h",s.joist_wall_thickness,label))
        elif ':roof:' in label:roof_source.append(item)
    slope=tan(radians(g.roof_pitch_degrees));ridge=p.width/2
    under=lambda x:2*p.storey_height+min(x,p.width-x)*slope
    for item in roof_source:
        label=item.label;b=shape_bounds(item)
        if ':post_' in label:
            # A horizontal contact top is selected conservatively below the
            # sloped source cap; its top tube is trimmed by the source solid.
            shape=_axis_tube(b,"z",s.roof_wall_thickness,label).intersect(item)
            roof.append(named(shape,label,"#8C9CA7"))
        elif ':rafter_' in label:
            x1,x2=b[0],b[3];y=(b[1]+b[4])/2
            vertical_depth=T.roof_rafter_vertical_depth
            shift=T.roof_purlin_vertical_depth+vertical_depth/2
            # perpendicular depth d*cos(pitch) has the same vertical section
            # extent as the retained 90 mm envelope at fixed X.
            depth=vertical_depth/sqrt(1+slope*slope)
            shape=_tube((x1,y,under(x1)+shift),(x2,y,under(x2)+shift),
                        T.roof_rafter_width,depth,s.roof_wall_thickness,label)
            # Cut X ends to their exact coordinated ridge/eave planes.
            clip=solid_box((x1,b[1],b[2]-.1,x2,b[4],b[5]+.1),"clip","#FFFFFF")
            roof.append(named(shape.intersect(clip),label,"#8C9CA7"))
        elif ':purlin_' in label:
            # This member has a parallelogram XZ section following the roof,
            # so hollowing its axis-aligned bounding box would leave two
            # disconnected side strips. Offset the real sloped faces instead.
            x1,x2=b[0],b[3];t=s.roof_wall_thickness
            vertical_offset=t*sqrt(1+slope*slope)
            def section(left,right,offset):
                return bd.Wire.make_polygon([(left,b[1],under(left)+offset),
                    (right,b[1],under(right)+offset),
                    (right,b[1],under(right)+T.roof_purlin_vertical_depth-offset),
                    (left,b[1],under(left)+T.roof_purlin_vertical_depth-offset)])
            face=bd.Face(section(x1,x2,0),[section(x1+t,x2-t,vertical_offset)])
            roof.append(named(bd.extrude(face,amount=b[4]-b[1],dir=(0,1,0)),label,"#8C9CA7"))
        else:
            roof.append(named(_axis_tube(b,"v",s.roof_wall_thickness,label).intersect(item),label,"#8C9CA7"))
    # Gussets/straps are deliberate overlapping connection illustrations; tube
    # intersections are trimmed so no architectural aperture is obscured.
    frame=bd.Compound(children=[bd.Compound(children=items,label=f"structure:{category}")
        for category,items in (("columns",columns),("beams",beams),("sills",sills),
          ("attic_joists",joists),("attic_headers",headers),("roof_framing",roof),("bearing_walls",braces))],label="structure")
    return bd.Compound(children=[frame,_foundation(p,s.foundation_stem_width,s.foundation_raft_top_z,
                s.foundation_raft_thickness,s.foundation_top_z)],label="variant_S")


def concrete_column_layout(p=P,c=RC):
    # Interior faces coincide with 180 / 7100 mm, preserving stair travel and
    # the user-confirmed room edges. The structural footprint grows outside them.
    near=p.external_wall-c.column_width/2;far=p.width-near;back=p.depth-near
    return [{"id":f"C{i:02d}","x":x,"y":y,"width":c.column_width,"floors":[1,2]}
        for i,(x,y) in enumerate(((near,near),(far,near),(near,back),(far,back),
            (p.access_left-p.internal_wall-c.column_width/2-10,near),
            (p.width/2,back),(near,4000),(far,4000)),1)]


def concrete_variant(p=P,g=G,c=RC):
    projection=max(0,c.column_width-p.external_wall)
    near=p.external_wall-c.column_width/2;far=p.width-near;back=p.depth-near
    w=c.beam_width;h=c.column_width/2
    columns=[];beams=[];shears=[];roof=[]
    columns_plan=concrete_column_layout(p,c)
    floor_tops={1:p.storey_height-c.floor_slab_thickness,2:2*p.storey_height-c.attic_slab_thickness}
    for n in (1,2):
        bottom=c.foundation_top_z if n==1 else floor_tops[1]
        top=floor_tops[n]-c.beam_depth
        for post in columns_plan:
            columns.append(solid_box((post['x']-h,post['y']-h,bottom,post['x']+h,post['y']+h,top),
                                      f"structure:F{n}:column_{post['id']}","#B2B5B1"))
        ring=(('B01',(-projection,near-w/2,top,p.width+projection,near+w/2,floor_tops[n])),
              ('B02',(-projection,back-w/2,top,p.width+projection,back+w/2,floor_tops[n])),
              ('B03',(near-w/2,near+w/2,top,near+w/2,back-w/2,floor_tops[n])),
              ('B04',(far-w/2,near+w/2,top,far+w/2,back-w/2,floor_tops[n])))
        beams.extend(solid_box(b,f"structure:F{n}:beam_{label}","#9FA5A0") for label,b in ring)
        # Two candidate shear piers aligned across floors, in shared closed
        # exterior portions. Torsion/distribution and strength are unverified.
        for label,footprint in (("SW01",box(5000,p.depth-p.external_wall,p.width-p.external_wall,p.depth+projection)),
                                ("SW02",box(p.width-p.external_wall,p.external_wall,p.width+projection,1400))):
            # Carve the union of both floors' apertures from the candidate pier,
            # including its outward RC projection, before any native extrusion.
            holes=[]
            for floor in (floor_plan(1,p),floor_plan(2,p)):
                for axis,at,start,span in floor.windows:
                    if label=='SW01' and axis=='h' and at>p.depth/2:
                        holes.append(box(start,p.depth-p.external_wall-1,start+span,p.depth+projection+1))
                    elif label=='SW02' and axis=='v' and at>p.width/2:
                        holes.append(box(p.width-p.external_wall-1,start,p.width+projection+1,start+span))
            footprint=footprint.difference(unary_union(holes))
            shears.append(_profile_parts(footprint,bottom,top,f"structure:F{n}:shear_wall_{label}","#C0C4BE"))
    column_cuts=unary_union([box(post['x']-h,post['y']-h,post['x']+h,post['y']+h) for post in columns_plan])
    full=box(0,0,p.width,p.depth).difference(column_cuts)
    floor1=_profile_parts(full,-c.floor_slab_thickness,0,"structure:F1:slab_ground","#CAD0C8")
    stairs=next(room.shape for room in floor_plan(2,p).rooms if room.id=='stairs')
    # At the north-east stair core, the slab void continues through the outer
    # wall band to its independent perimeter beams. A hole touching the corner
    # column notch at just one point would be an invalid native solid.
    stair_void=box(stairs.bounds[0],stairs.bounds[1],p.width,p.depth)
    floor2=_profile_parts(full.difference(stair_void),p.storey_height-c.floor_slab_thickness,p.storey_height,
                         "structure:F2:slab_floor","#CAD0C8")
    hatch=box(A.hatch_x,A.hatch_y,A.hatch_x+A.hatch_length,A.hatch_y+A.hatch_width)
    attic=box((p.width-A.deck_width)/2,p.external_wall,(p.width+A.deck_width)/2,p.depth-p.external_wall).difference(hatch)
    attic_slab=_profile_parts(attic,2*p.storey_height-c.attic_slab_thickness,2*p.storey_height,
                             "structure:attic:slab_storage","#CAD0C8")
    beams.extend([floor1,floor2,attic_slab])
    slope=tan(radians(g.roof_pitch_degrees));ridge=p.width/2;zbase=2*p.storey_height
    top=lambda x:zbase+min(x,p.width-x)*slope
    for side,x1,x2 in (("west",-g.roof_overhang,ridge),("east",ridge,p.width+g.roof_overhang)):
        points=[(x1,top(x1)),(x2,top(x2)),(x2,top(x2)+c.roof_slab_vertical_thickness),(x1,top(x1)+c.roof_slab_vertical_thickness)]
        face=bd.Face(bd.Wire.make_polygon([(x,-g.roof_overhang,z) for x,z in points]))
        roof.append(named(bd.extrude(face,amount=p.depth+2*g.roof_overhang,dir=(0,1,0)),
                          f"structure:roof:slab_{side}","#ABB2AB"))
    gable_bottom=2*p.storey_height-c.attic_slab_thickness
    gable_points=[(0,gable_bottom),(p.width,gable_bottom),(p.width,zbase),
                  (ridge,top(ridge)),(0,zbase)]
    for side,y in (("south",-projection),("north",p.depth-p.external_wall)):
        face=bd.Face(bd.Wire.make_polygon([(x,y,z) for x,z in gable_points]))
        gable=bd.extrude(face,amount=c.column_width,dir=(0,1,0))
        if side=='north':
            from .attic_geometry import north_vent_bounds
            v=north_vent_bounds(p,g)
            gable=gable.cut(solid_box((v[0],y-1,v[2],v[3],y+c.column_width+1,v[5]),'vent_tool','#FFFFFF'))
        roof.append(named(gable,f"structure:roof:gable_shear_{side}","#B2B5B1"))
    frame=bd.Compound(children=[bd.Compound(children=items,label=f"structure:{category}") for category,items in
        (("columns",columns),("beams",beams),("bearing_walls",shears),("roof_framing",roof))],label="structure")
    return bd.Compound(children=[frame,_foundation(p,c.foundation_stem_width,c.foundation_raft_top_z,
                c.foundation_raft_thickness,c.foundation_top_z,projection)],label="variant_RC")


@orient_shape
def build_variant(system,p=P,g=G):
    return {"W":timber_variant,"S":steel_variant,"RC":concrete_variant}[system](p,g)


def _overlap(a,b):
    aa,bb=shape_bounds(a),shape_bounds(b)
    if not all(aa[i]<bb[i+3]-1e-6 and bb[i]<aa[i+3]-1e-6 for i in range(3)):return 0.
    return sum(overlap_volume(sa,sb) for sa in a.solids() for sb in b.solids())


def geometry_coordination(assembly,system,p=P,g=G,*,backend='auto'):
    members=list(leaves(assembly));collisions=[];apertures=[];intrusions=[]
    member_bounds=[shape_bounds(member) for member in members]
    floors={n:floor_plan(n,p) for n in (1,2)}
    opening_queries=[]
    for n in (1,2):
        floor=floors[n];z=(n-1)*p.storey_height
        for door in floor.doors:
            tool=opening_box(door.axis,door.at,door.start+.1,door.width-.2,
                p.external_wall if {'outside','balcony'} & {door.a,door.b} else p.internal_wall,z+.1,z+g.door_height-.1)
            opening_queries.append((n,f"F{n}:{door.id}",'door',tool))
        for index,window in enumerate(floor.windows,1):
            sill,height=window_vertical_range(window,g,p)
            tool=opening_box(*window,p.external_wall,z+sill+.1,z+sill+height-.1)
            opening_queries.append((n,f"F{n}:W{index:02d}",'window',tool))
    stair=next(r.shape for r in floors[2].rooms if r.id=='stairs')
    stair_tool=extruded_polygon(stair.buffer(-.1),.1,p.storey_height+200)
    hatch_bounds=(A.hatch_x+.1,A.hatch_y+.1,2*p.storey_height-450,
                 A.hatch_x+A.hatch_length-.1,A.hatch_y+A.hatch_width-.1,2*p.storey_height-.1)
    from .orientation import bounds
    if p.mirror_layout:hatch_bounds=bounds(hatch_bounds,p.width)
    hatch_tool=solid_box(hatch_bounds,"hatch","#FFFFFF")
    # Broad-phase candidates are ordered by the original member index. Exact
    # native solid intersections still decide every reported collision.
    tools=[query[3] for query in opening_queries]+[stair_tool,hatch_tool]
    candidates=aabb_candidates(member_bounds,[shape_bounds(tool) for tool in tools],backend=backend)
    def hits(tool,indices):
        return [{"member":members[index].label,"volume_mm3":round(v,4)} for index in indices
                if (v:=_overlap(members[index],tool))>.1]
    for n in (1,2):
        floor=floors[n]
        for query,indices in zip(opening_queries,candidates):
            query_floor,identifier,kind,tool=query
            if query_floor!=n:continue
            hit=hits(tool,indices)
            apertures.append({"id":identifier,"kind":kind,"overlaps":hit})
            collisions.extend(dict(item,aperture=identifier) for item in hit)
        for m,b in zip(members,member_bounds):
            if not m.label.startswith(f"structure:F{n}:") or not any(kind in m.label for kind in (':column_',':shear_wall_',':strap_brace_',':gusset_')):continue
            profile=box(b[0],b[1],b[3],b[4])
            for room in floor.rooms:
                area=profile.intersection(room.shape).area
                if area>.01:intrusions.append({"member":m.label,"floor":n,"room_id":room.id,"footprint_mm2":round(area,4)})
    stair_hits=hits(stair_tool,candidates[-2])
    hatch_hits=hits(hatch_tool,candidates[-1])
    envelope=[]
    for m,b in zip(members,member_bounds):
        if not m.label.startswith('structure:F') or ':slab_' in m.label:continue
        profile=box(b[0],b[1],b[3],b[4])
        area=profile.difference(box(0,0,p.width,p.depth)).area
        if area>.01:envelope.append({"member":m.label,"outside_original_outline_mm2":round(area,4),"bounds_mm":b})
    summary={
        "W":{"zh":"按 R14 镜像平面重排木结构演示架构；截面、节点与基础均未验算。","ja":"R14の左右反転間取りに合わせて木造概念架構を再配置。断面・接合部・基礎は未計算。","en":"Timber concept rearranged for the R14 mirrored layout; sections, connections and foundations are uncalculated."},
        "S":{"zh":"薄壁空心钢构件、交叉钢带及节点板为示意；制造等级、板厚适用性与连接承载力待核定。","ja":"薄肉中空鋼材・交差ストラップ・ガセットの概念案。製造等級、板厚適用性、接合耐力は未確定。","en":"Thin-wall hollow steel, crossed straps and gussets are conceptual; manufacturing grade, thickness suitability and connection capacities are pending."},
        "RC":{"zh":"300×300 mm 混凝土柱及300×400 mm梁保持原有室内边界，向原外轮廓各侧伸出 120 mm；外墙及建筑面积需重新协调。未绘制或验算配筋。","ja":"300×300 mmのRC柱と300×400 mmの梁は室内境界を保持し、元の外形から各面 120 mm 突出。外壁・建築面積の再調整が必要。配筋図・配筋計算は未実施。","en":"300×300 mm RC columns and 300×400 mm beams retain the interior perimeter faces but project 120 mm outside each original face; façade and building area need coordination. Reinforcement is neither drawn nor calculated."},
    }[system]
    return {"scope":"native solid aperture checks and column/pier footprints only; no strength or statutory assessment",
        "status":"architectural_coordination_pending" if envelope or collisions or stair_hits or hatch_hits or intrusions else "geometry_checks_passed_engineering_pending",
        "summary":summary,"apertures":apertures,"aperture_collisions":collisions,
        "main_stair_collisions":stair_hits,"attic_hatch_collisions":hatch_hits,
        "room_intrusions":intrusions,"exterior_outline_projections":envelope,
        "original_building_outline_mm":[0,0,p.width,p.depth],
        "actual_exterior_frame_outline_mm":[-120,-120,p.width+120,p.depth+120] if system=='RC' else [0,0,p.width,p.depth],
        "room_net_clearance_certification":None,"all_interior_fixtures_checked":False}


def variant_manifest(system,assembly,p=P,g=G):
    parameters=asdict(T if system=='W' else S if system=='S' else RC)
    names={"W":{"zh":"木结构（W造）","ja":"木造（W造）","en":"Timber (W)"},
        "S":{"zh":"轻钢结构（S造）","ja":"軽量鉄骨造（S造）","en":"Light-gauge steel (S)"},
        "RC":{"zh":"钢筋混凝土结构（RC造）","ja":"鉄筋コンクリート造（RC造）","en":"Reinforced concrete (RC)"}}
    assumptions=["Every section, plate thickness and foundation dimension is a demonstration input, not a calculation-selected size.",
        "City selection supplies research/checklist context; these geometries are shared by all four cities and do not assert site compliance.",
        "The 8190 x 7280 mm R14 architectural outline and 2800 mm storeys remain user-specified demonstration assumptions.",
        "Geotechnical data, actions, products, strengths, connection design and reinforcing schedules are absent.",
        "Architectural slabs/roof in the original house are display shells; the structural overlay replaces them for review, not construction."]
    if system=='S':assumptions.extend([
        "RHS members are genuinely hollow with assumed 2.3 mm column/joist and 3.2 mm beam walls; no manufacturing/product standard or approved light-steel system is selected.",
        "Large 8190/7280 mm overall spans and fabricated 180 x 300 x 3.2 mm transfer tubes require complete design; geometry alone does not establish light-gauge feasibility.",
        "Straps and gussets intentionally overlap to depict connections; bolts, screw layout, anchors and tested connection capacities are not specified."])
    if system=='RC':assumptions.extend([
        "300 mm perimeter columns/beam bands extend 120 mm outside each architectural face; structural perimeter is 8430 x 7520 mm and exterior/site/area coordination remains pending.",
        "180 mm floor and attic slabs, 120 mm vertical roof slabs, 300 mm columns and 300 x 400 mm beams are assumed drawing sizes only; beam depth was reduced from 450 to 400 mm solely to clear existing 2200 mm window tops, not as a strength calculation.",
        "RC self-weight, attic/storage loading, concrete/rebar strengths, reinforcing layout, punching shear, deflection and seismic detailing require an independent RC calculation, not timber load inheritance.",
        "The two shear piers are spatial candidates only; their quantity, distribution, ductility, diaphragm anchorage and torsional performance are unresolved.",
        "The sloped concrete roof/cantilever eaves and storage-attic slab require dedicated checks; hatch depth differs from the timber hatch hardware and product coordination is pending.",
        "The north-west stair slab void extends through the outer wall band to the separate perimeter beams, avoiding an invalid point-contact slab corner. The approved stair travel footprint remains clear; slab edges and beam/slab anchorage are unengineered.",
        "No reinforcing bars are rendered, avoiding an appearance of a designed reinforcing cage."])
    if system=='W':assumptions.extend(structure_manifest(p,g)['assumptions'])
    members=[{"name":item.label,"bounds_mm":shape_bounds(item),"volume_mm3":round(item.volume,6),"solid_count":len(item.solids())}
        for item in leaves(assembly)]
    return {"id":system,"system":system,"name":names[system],"status":"demonstration_candidate_not_engineered",
        "step_path":f"STEP/structure_{system}.step","glb_path":f"GLB/structure_{system}.glb",
        "units":"mm","glb_units":"m","glb_up_axis":"Y","native_up_axis":"Z",
        "parameters":parameters,"members":members,"member_count":len(members),
        "source_same_city_geometry":True,"city_specific_member_sizing":False,
        "material_grade":None,"manufacturing_specification":None,"reinforcement_schedule":None,
        "capacity_results":None,"statutory_compliance_result":None,"foundation_engineering_result":None,
        "self_weight_design_result":None,"assumptions":assumptions,
        "coordination":geometry_coordination(assembly,system,p,g),
        "required_calculations":["site_actions_and_material_specific_self_weight","floor_attic_roof_and_storage_loads",
            "seismic_wind_strength_and_torsion","member_bending_shear_axial_buckling_and_deflection",
            "diaphragms_connections_anchors_and_opening_load_transfer","foundation_soil_bearing_settlement_and_material_specific_reinforcement"]}
