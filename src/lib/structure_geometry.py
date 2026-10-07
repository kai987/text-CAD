"""R06 timber structural *demonstration*, sharing the approved house plans.

The members show a candidate load path; section sizes are drawing inputs, not
calculated capacities. Conceptual architectural shells intentionally overlap
this optional frame. Hide shells to inspect it. No strength, seismic grade,
soil capacity, statutory exemption or construction fitness is asserted.
"""
from __future__ import annotations

from .orientation import orient_shape, orient_record

from dataclasses import asdict, dataclass
from math import ceil, radians, tan

from cadgen import build123d as bd, srgb
from shapely.geometry import box

from .house_plan import dimensions, floor_plan


@dataclass(frozen=True)
class StructureParameters:
    external_column_width: float = 120
    internal_column_width: float = 90
    perimeter_beam_width: float = 120
    internal_beam_width: float = 90
    transfer_beam_width: float = 180
    storey_beam_depth: float = 300
    sill_base_z: float = -200
    sill_depth: float = 120
    floor_board_allowance: float = 24
    attic_joist_width: float = 60
    attic_joist_depth: float = 180
    attic_joist_max_spacing: float = 455
    hatch_trimmer_width: float = 120
    hatch_header_width: float = 60
    bearing_panel_thickness: float = 9
    internal_bearing_panel_display_thickness: float = 5
    minimum_bearing_panel_length: float = 300
    roof_post_width: float = 90
    roof_purlin_width: float = 120
    roof_purlin_vertical_depth: float = 60
    roof_rafter_width: float = 60
    roof_rafter_vertical_depth: float = 90
    roof_rafter_max_spacing: float = 455
    ridge_beam_width: float = 120
    ridge_beam_depth: float = 60


T = StructureParameters()


def _attic():
    # The storage-attic revision is authored independently of this frame.
    from .attic_geometry import A
    return A


@orient_record
def foundation_support_segments(p):
    """R10 load-path axes, all uncalculated; no obsolete LDK pillar retained."""
    d=dimensions(p);e=p.external_wall/2;t=p.internal_wall
    return [
        {"id":"I01","axis":"h","at":d["south_top"]+t/2,"start":e,"end":p.width-e},
        {"id":"I02","axis":"h","at":d["sy"]-t/2,"start":e,"end":p.width-e},
        {"id":"I03","axis":"v","at":d["wcl"]-t/2,"start":d["sy"]-t/2,"end":p.depth-e},
        {"id":"I04","axis":"v","at":d["wcr"]+t/2,"start":d["sy"]-t/2,"end":p.depth-e},
        {"id":"I05","axis":"h","at":d["wetbottom"]-t/2,"start":d["wcl"]-t/2,"end":d["wcr"]+t/2},
        {"id":"I06","axis":"v","at":p.access_left-t/2,"start":e,"end":d["sy"]-t/2},
        {"id":"I07","axis":"v","at":d["ar"]+t/2,"start":e,"end":d["sy"]-t/2},
    ]


@orient_record
def _beam_segments(p, t=T):
    e = p.external_wall/2
    r = t.perimeter_beam_width/2
    # Ring corners are butt-jointed so their native volumes do not duplicate.
    segments = [
        {"id":"B01", "axis":"h", "at":e, "start":e-r, "end":p.width-e+r, "width":2*r},
        {"id":"B02", "axis":"h", "at":p.depth-e, "start":e-r, "end":p.width-e+r, "width":2*r},
        {"id":"B03", "axis":"v", "at":e, "start":e+r, "end":p.depth-e-r, "width":2*r},
        {"id":"B04", "axis":"v", "at":p.width-e, "start":e+r, "end":p.depth-e-r, "width":2*r},
    ]
    for i, support in enumerate(foundation_support_segments(p), 5):
        segment = dict(support, id=f"B{i:02d}", width=t.transfer_beam_width if i==5 else t.internal_beam_width)
        # Internal members finish at the inside face of the perimeter frame.
        limit = p.width if segment["axis"]=="h" else p.depth
        if abs(segment["start"]-e)<.01: segment["start"] += r
        if abs(segment["end"]-(limit-e))<.01: segment["end"] -= r
        segments.append(segment)
    return segments


@orient_record
def floor_beam_segments(number,p,t=T):
    """R10 attic opening transfer perimeter, with assumed connection details."""
    segments=_beam_segments(p,t)
    if number==2:
        a=_attic();d=dimensions(p);right=a.hatch_x+a.hatch_length
        width=t.internal_column_width
        left=p.access_left-p.internal_wall/2+width/2  # butt to western partition beam
        for key,y in [('B12',a.hatch_y-width/2),('B13',a.hatch_y+a.hatch_width+width/2)]:
            segments.append({'id':key,'axis':'h','at':y,'start':left,'end':right+width,'width':width})
        segments.append({'id':'B14','axis':'v','at':right+width/2,'start':a.hatch_y,
                         'end':a.hatch_y+a.hatch_width,'width':width})
    return segments


def attic_beam_opening(p,z1,z2):
    a=_attic()
    return _box((a.hatch_x,a.hatch_y,z1-1,a.hatch_x+a.hatch_length,
                 a.hatch_y+a.hatch_width,z2+1),'attic_beam_opening','#FFFFFF')


@orient_record
def column_layout(p,t=T):
    """Posts in shared closed wall segments, avoiding every R10 aperture.

    Grid candidates and door/window jamb candidates are filtered by complete
    footprint containment on BOTH floors. No free-standing F1 transfer pillar.
    Long spans still require engineering; filtering is geometry only.
    """
    from math import hypot
    d=dimensions(p);e=p.external_wall/2
    floors=[floor_plan(n,p) for n in (1,2)]
    common=floors[0].walls.intersection(floors[1].walls)
    records=[]
    axes=[('h',e,e,p.width-e,True),('h',p.depth-e,e,p.width-e,True),
          ('v',e,e,p.depth-e,True),('v',p.width-e,e,p.depth-e,True),
          ('v',d['wcl']-p.internal_wall/2,d['sy']+80,p.depth-e,False),
          ('v',d['wcr']+p.internal_wall/2,d['sy']+80,p.depth-e,False),
          ('h',d['sy']-p.internal_wall/2,d['sx']+p.stair_width+p.internal_wall/2,
               d['sx']+p.stair_width+p.internal_wall/2,False)]
    for axis,at,start,end,external in axes:
        width=t.external_column_width if external else t.internal_column_width
        positions=[start,end]+_positions(start,end,910)
        for floor in floors:
            apertures=[(door.axis,door.at,door.start,door.width) for door in floor.doors]+floor.windows
            for ax,pos,lo,span in apertures:
                if ax==axis and abs(at-pos)<1:
                    positions.extend([lo-width/2-5,lo+span+width/2+5])
        for pos in sorted(set(positions)):
            if pos<start or pos>end:continue
            x,y=(pos,at) if axis=='h' else (at,pos)
            width=t.external_column_width if min(abs(x-e),abs(x-(p.width-e)),abs(y-e),abs(y-(p.depth-e)))<.01 else t.internal_column_width
            footprint=box(x-width/2,y-width/2,x+width/2,y+width/2)
            if not common.covers(footprint):continue
            if any(hypot(x-c['x'],y-c['y'])<(width+c['width'])/2+10 for c in records):continue
            records.append({'id':f'C{len(records)+1:02d}','x':x,'y':y,'width':width,
                            'floors':[1,2],'support':'aligned_column_or_beam'})
    return records


@orient_record
def bearing_wall_candidates(p, t=T):
    """Closed wall spans with explicit posts; a geometry list, never wall credit."""
    d=dimensions(p); e=p.external_wall/2
    columns=column_layout(p,t)
    ys=d["sy"]-p.internal_wall/2
    xt=d["ldk_right"]+p.internal_wall/2
    xc=d["wcl"]-p.internal_wall/2
    axes=[("h",e,True),("h",p.depth-e,True),("v",e,True),("v",p.width-e,True),
          ("h",ys,False),("v",xt,False),("v",xc,False)]
    candidates=[]
    for axis,at,external in axes:
        normal="y" if axis=="h" else "x"; along="x" if axis=="h" else "y"
        posts=sorted([c for c in columns if c["floors"]==[1,2] and abs(c[normal]-at)<.01],key=lambda c:c[along])
        for c1,c2 in zip(posts,posts[1:]):
            clear_start,clear_end=c1[along]+c1["width"]/2,c2[along]-c2["width"]/2
            if clear_end-clear_start<t.minimum_bearing_panel_length:continue
            # Span across half of each post face, rather than touching only
            # two corners. The 100 mm internal presentation wall leaves 5 mm
            # beside its 90 mm post. This face marker is not a sheathing spec.
            start,end=c1[along],c2[along]
            thick=t.bearing_panel_thickness if external else t.internal_bearing_panel_display_thickness
            offset=t.external_column_width/2 if external else t.internal_column_width/2
            limit=p.depth if axis=="h" else p.width
            face=at+offset if (not external or at<limit/2) else at-offset-thick
            profile=box(start,face,end,face+thick) if axis=="h" else box(face,start,face+thick,end)
            if not all(profile.difference(floor_plan(n,p).walls).area<.001 for n in (1,2)):continue
            candidates.append({"id":f"BW{len(candidates)+1:02d}","axis":axis,"at":at,"start":start,"end":end,
                               "normal_start":face,"thickness":thick,"clear_span":clear_end-clear_start,"external":external,
                               "end_columns":[c1["id"],c2["id"]],"wall_multiplier":None,"connection_capacity":None})
    return candidates


def _bounds(segment,z1,z2):
    half=segment["width"]/2
    if segment["axis"]=="h":return (segment["start"],segment["at"]-half,z1,segment["end"],segment["at"]+half,z2)
    return (segment["at"]-half,segment["start"],z1,segment["at"]+half,segment["end"],z2)


def _box(bounds,label,color="#B98A55"):
    x1,y1,z1,x2,y2,z2=bounds
    shape=bd.Box(x2-x1,y2-y1,z2-z1,align=(bd.Align.MIN,)*3).moved(bd.Location((x1,y1,z1)))
    shape.label=label;shape.color=srgb(color)
    return shape


def _label(shape,label,color="#B98A55"):
    shape.label=label;shape.color=srgb(color);return shape


def _section(points_xz,y,depth,label,color="#B98A55"):
    face=bd.Face(bd.Wire.make_polygon([(x,y,z) for x,z in points_xz]))
    return _label(bd.extrude(face,amount=depth,dir=(0,1,0)),label,color)


def _overlapping(a,b):
    aa,bb=a.bounding_box(),b.bounding_box()
    return all(lo<hi-1e-7 and olo<ahi-1e-7 for lo,hi,olo,ahi in zip(tuple(aa.min),tuple(bb.max),tuple(bb.min),tuple(aa.max)))


def _butt_members(segments,z1,z2,prefix,kind,color,opening=None):
    shapes=[]
    for segment in segments:
        shape=_box(_bounds(segment,z1,z2),f"{prefix}:{kind}_{segment['id']}",color)
        if opening is not None and _overlapping(shape,opening):shape=_label(shape.cut(opening),shape.label,color)
        cutters=[prior for prior in shapes if _overlapping(shape,prior)]
        if cutters:shape=_label(shape.cut(*cutters),shape.label,color)
        shapes.append(shape)
    return shapes


def _positions(start,end,maximum):
    count=max(1,ceil((end-start)/maximum))
    return [start+(end-start)*i/count for i in range(count+1)]


@orient_record
def structure_dimensions(p,g,t=T):
    a=_attic()
    attic_top=2*p.storey_height-t.floor_board_allowance
    return {"sill_bottom_z":t.sill_base_z,"sill_top_z":t.sill_base_z+t.sill_depth,
            "F1_beam_top_z":p.storey_height-t.floor_board_allowance,
            "F1_beam_bottom_z":p.storey_height-t.floor_board_allowance-t.storey_beam_depth,
            "F2_beam_top_z":attic_top-t.attic_joist_depth,
            "F2_beam_bottom_z":attic_top-t.attic_joist_depth-t.storey_beam_depth,
            "attic_joist_bottom_z":attic_top-t.attic_joist_depth,"attic_joist_top_z":attic_top,
            "attic_subfloor_bottom_z":attic_top,"attic_subfloor_top_z":2*p.storey_height,
            "deck_left":(p.width-a.deck_width)/2,"deck_right":(p.width+a.deck_width)/2,
            "hatch":[a.hatch_x,a.hatch_y,a.hatch_x+a.hatch_length,a.hatch_y+a.hatch_width]}


def _roof(p,g,d,t=T):
    slope=tan(radians(g.roof_pitch_degrees));ridge=p.width/2
    under=lambda x:2*p.storey_height+min(x,p.width-x)*slope
    half=t.roof_purlin_width/2
    px={"west":d["deck_left"]-half,"east":d["deck_right"]+half}
    pieces=[];posts=[]
    yposts=[p.external_wall/2,dimensions(p)["sy"]-p.internal_wall/2,p.depth-p.external_wall/2]
    # Purlins and rafters occupy separate vertical bands of the retained roof
    # envelope. These deliberately small bands are visual coordination inputs;
    # an engineered roof may need a different build-up and larger sections.
    for side,x in px.items():
        x1,x2=x-half,x+half
        points=[(x1,under(x1)),(x2,under(x2)),(x2,under(x2)+t.roof_purlin_vertical_depth),(x1,under(x1)+t.roof_purlin_vertical_depth)]
        pieces.append(_section(points,-g.roof_overhang,p.depth+2*g.roof_overhang,f"structure:roof:purlin_{side}","#AC7545"))
        for i,y in enumerate(yposts,1):
            h=t.roof_post_width/2
            points=[(x-h,d["F2_beam_top_z"]),(x+h,d["F2_beam_top_z"]),
                    (x+h,under(x+h)),(x-h,under(x-h))]
            posts.append(_section(points,y-h,2*h,f"structure:roof:post_{side}_P{i:02d}","#AC7545"))
    peak=under(ridge)
    pieces.append(_box((ridge-t.ridge_beam_width/2,-g.roof_overhang,peak,
                        ridge+t.ridge_beam_width/2,p.depth+g.roof_overhang,peak+t.ridge_beam_depth),
                       "structure:roof:ridge_beam","#AC7545"))
    for i,y in enumerate((yposts[0],yposts[-1]),1):
        h=t.roof_post_width/2
        posts.append(_box((ridge-h,y-h,d["F2_beam_top_z"],ridge+h,y+h,peak),
                          f"structure:roof:post_ridge_P{i:02d}","#AC7545"))
    rafters=[]
    for i,y in enumerate(_positions(-g.roof_overhang+t.roof_rafter_width/2,
                                    p.depth+g.roof_overhang-t.roof_rafter_width/2,t.roof_rafter_max_spacing),1):
        for side,x1,x2 in (("west",-g.roof_overhang,ridge-t.ridge_beam_width/2),
                           ("east",ridge+t.ridge_beam_width/2,p.width+g.roof_overhang)):
            bottom=t.roof_purlin_vertical_depth;top=bottom+t.roof_rafter_vertical_depth
            pts=[(x1,under(x1)+bottom),(x2,under(x2)+bottom),(x2,under(x2)+top),(x1,under(x1)+top)]
            rafters.append(_section(pts,y-t.roof_rafter_width/2,t.roof_rafter_width,
                                    f"structure:roof:rafter_{side}_R{i:02d}","#C49B6A"))
    return pieces+posts+rafters,posts


def _attic_members(p,g,d,roof_posts,t=T):
    a=_attic();hatch=d["hatch"];half=t.attic_joist_width/2
    y1,y2=p.external_wall/2,p.depth-p.external_wall/2
    z1,z2=d["attic_joist_bottom_z"],d["attic_joist_top_z"]
    west=a.hatch_x-t.hatch_trimmer_width/2;east=hatch[2]+t.hatch_trimmer_width/2
    centers=sorted(set(_positions(d["deck_left"]+half,west,t.attic_joist_max_spacing)+
                       _positions(west,east,t.attic_joist_max_spacing)+
                       _positions(east,d["deck_right"]-half,t.attic_joist_max_spacing)))
    joists=[];headers=[]
    for index,x in enumerate(centers,1):
        if abs(x-west)<.01 or abs(x-east)<.01:continue
        ranges=[("",y1,y2)]
        if x+half>hatch[0] and x-half<hatch[2]:
            ranges=[("_south",y1,a.hatch_y-t.hatch_header_width),("_north",hatch[3]+t.hatch_header_width,y2)]
        for suffix,ya,yb in ranges:
            label=f"structure:attic:joist_J{index:02d}{suffix}"
            shape=_box((x-half,ya,z1,x+half,yb,z2),label,"#C49B6A")
            cutters=[post for post in roof_posts if _overlapping(shape,post)]
            if cutters:shape=_label(shape.cut(*cutters),label,"#C49B6A")
            joists.append(shape)
    for side,x1,x2 in (("west",a.hatch_x-t.hatch_trimmer_width,a.hatch_x),
                       ("east",hatch[2],hatch[2]+t.hatch_trimmer_width)):
        label=f"structure:attic:trimmer_{side}"
        shape=_box((x1,y1,z1,x2,y2,z2),label,"#AC7545")
        cutters=[post for post in roof_posts if _overlapping(shape,post)]
        if cutters:shape=_label(shape.cut(*cutters),label,"#AC7545")
        headers.append(shape)
    for side,ya,yb in (("south",a.hatch_y-t.hatch_header_width,a.hatch_y),
                       ("north",hatch[3],hatch[3]+t.hatch_header_width)):
        headers.append(_box((a.hatch_x,ya,z1,hatch[2],yb,z2),f"structure:attic:header_{side}","#AC7545"))
    return joists,headers


@orient_shape
def structure_group(p,g,t=T):
    d=structure_dimensions(p,g,t);segments=_beam_segments(p,t)
    columns=[];beams=[];panels=[]
    for n in (1,2):
        bottom=d["sill_top_z"] if n==1 else d["F1_beam_top_z"]
        top=d[f"F{n}_beam_bottom_z"]
        for c in column_layout(p,t):
            if n not in c["floors"]:continue
            h=c["width"]/2
            columns.append(_box((c["x"]-h,c["y"]-h,bottom,c["x"]+h,c["y"]+h,top),
                                f"structure:F{n}:column_{c['id']}","#B98A55"))
        beams.extend(_butt_members(floor_beam_segments(n,p,t),d[f"F{n}_beam_bottom_z"],d[f"F{n}_beam_top_z"],f"structure:F{n}","beam","#B98A55",
                     attic_beam_opening(p,d[f"F{n}_beam_bottom_z"],d[f"F{n}_beam_top_z"]) if n==2 else None))
        # Internal/end panels own corner contact with larger perimeter posts;
        # outer markers butt around them, so neither marker stops short of its
        # declared end post behind a perpendicular marker.
        for wall in sorted(bearing_wall_candidates(p,t),key=lambda item:item['external']):
            a,b=wall["start"],wall["end"];v=wall["normal_start"];thick=wall["thickness"]
            panel_top=d[f"F{n}_beam_top_z"]
            bounds=(a,v,bottom,b,v+thick,panel_top) if wall["axis"]=="h" else (v,a,bottom,v+thick,b,panel_top)
            label=f"structure:F{n}:bearing_wall_{wall['id']}"
            panel=_box(bounds,label,"#DBBA89")
            # Transverse beams and larger corner/end posts own their timber
            # volume. Trim the display panel around those, with a real face
            # contact, rather than stacking two solids in the same location.
            cutters=[shape for shape in columns+beams+panels if _overlapping(panel,shape)]
            if cutters:panel=_label(panel.cut(*cutters),label,"#DBBA89")
            panels.append(panel)
    sills=_butt_members(segments,d["sill_bottom_z"],d["sill_top_z"],"structure:F1","sill","#8D6845")
    roof,roof_posts=_roof(p,g,d,t)
    joists,headers=_attic_members(p,g,d,roof_posts,t)
    return bd.Compound(children=[bd.Compound(children=items,label=f"structure:{category}") for category,items in (
        ("columns",columns),("beams",beams),("sills",sills),("attic_joists",joists),
        ("attic_headers",headers),("roof_framing",roof),("bearing_walls",panels))],label="structure")


@orient_record
def structure_manifest(p,g,t=T):
    d=structure_dimensions(p,g,t)
    return {"revision":"R10-STRUCTURE","units":"mm","status":"demonstration_candidate_not_engineered",
            "scheme":"timber_post_and_beam_candidate","parameters":asdict(t),"dimensions":d,
            "columns":column_layout(p,t),"beam_axes":_beam_segments(p,t),
            "floor_beam_axes":{f"F{n}":floor_beam_segments(n,p,t) for n in (1,2)},
            "bearing_wall_candidates":bearing_wall_candidates(p,t),"foundation_support_axes":foundation_support_segments(p),
            "roof_posts":{"north_vent_transfer_frame":"R20 single centred north ridge post retained; vertical vents flank the post; uncalculated", "gable_y":[p.external_wall/2,p.depth-p.external_wall/2],
                          "purlin_x":[d["deck_left"]-t.roof_purlin_width/2,d["deck_right"]+t.roof_purlin_width/2],
                          "middle_y":dimensions(p)["sy"]-p.internal_wall/2},
            "capacity_results":None,"statutory_compliance_result":None,"material_grade":None,
            "assumptions":[
                "未提供实际建房地点、测量、地盘调查、木材等级或荷载条件，结构布置仅作为演示草案。",
                "木构件、胶合板和混凝土的全部截面尺寸都是演示输入，不是验算选型结果。",
                "柱位沿两层共同的封闭墙段上下对齐；不因二层隔墙而在LDK净空间内擅自增柱。",
                "原建筑墙体、楼板和屋顶保留为展示壳体，与独立结构方案层有意重叠；查看结构时应隐藏建筑壳体。",
                "检修口下的梁通过周边示意边梁换向支承；对接和避让切口仅用于几何协调，紧固件、抗拔件、节点及承载未计算。",
                "屋架布置在150 mm概念屋面带内以保持阁楼净空；实际屋面层次与结构截面仍待重新设计和验算。",
                "储物阁楼即使未来获准不计法规面积，储物荷载仍必须纳入整栋结构设计。",
                "一层原200 mm建筑楼板壳体不是已设计的木楼面或混凝土承重楼板。",
            ],
            "required_calculations":["dead_live_and_local_storage_loads","snow_wind_and_seismic_site_actions",
                "bearing_wall_quantity_distribution_and_torsion","floor_and_roof_diaphragms",
                "beam_bending_shear_deflection_and_transfer_reactions","column_axial_and_buckling",
                "ridge_purlin_and_rafter_spans_and_uplift","hatch_trimmer_and_header_reactions",
                "joints_anchors_and_hold_downs","foundation_soil_bearing_settlement_and_reinforcement"],
            "critical_unresolved_items":["8190 x 7280 mm outline creates long open-LDK/roof spans; no section adequacy is established.",
                "The hatch requires designed load transfer, connections and a coordinated attic ladder product.",
                "First-floor floor build-up, foundations, ventilation and moisture protection require engineering.",
                "Bearing panels have no certified wall multiplier; geometry does not prove seismic or wind resistance."]}
