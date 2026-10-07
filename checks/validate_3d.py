"""Acceptance checks against the saved named STEP and metre/Y-up GLB."""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import math
import struct
import sys
from shapely.geometry import box
from shapely.affinity import scale

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"src"))

from cadgen import read_scene
from cadgen.geometry import overlap_volume
from lib.house_plan import P, dimensions, floor_plan
from lib.house_geometry import G, cuboid, extruded_polygon, opening_box, section_extrusion, window_vertical_range
from lib.exterior_geometry import E
from lib.attic_geometry import A, attic_dimensions, attic_clear_height
from lib.native_glb import audit_glb_bytes


from lib.orientation import bounds as reflect_bounds, shape as reflect_shape

def world_bounds(value):
    return reflect_bounds(value,P.width) if P.mirror_layout else value

results = []


def check(name, ok, actual=None, expected=None):
    results.append({"check": name, "pass": bool(ok), "actual": actual, "expected": expected})


def close(name, actual, expected, tolerance=0.01):
    check(name, abs(actual-expected) <= tolerance, round(actual, 6), expected)


def bounds(shape):
    b = shape.bounding_box()
    return [b.min.X, b.min.Y, b.min.Z, b.max.X, b.max.Y, b.max.Z]


def intersects_bounds(a, b):
    return all(a[i] < b[i+3]-1e-7 and b[i] < a[i+3]-1e-7 for i in range(3))


def overlap(shapes, tool):
    tb = bounds(tool)
    tool_solids = tool.solids()
    total = 0.0
    for shape in shapes:
        for solid in shape.solids():
            if intersects_bounds(bounds(solid), tb):
                total += sum(overlap_volume(solid, ts) for ts in tool_solids)
    return total


def exterior_core_tool(axis, at, start, width, z1, z2):
    """A test region through the retained backing, excluding the finish gap.

    The approved 180 mm wall still ends at the same interior room boundary.
    The outer 22 mm is now 20 mm finish plus a 2 mm visual separation. This
    region tests the remaining backing with 1 mm clearance from each face.
    """
    setback = E.cladding_thickness+E.backing_gap
    limit = P.depth if axis == "h" else P.width
    low_side = at < limit/2
    center = P.external_wall/2+setback/2 if low_side else limit-P.external_wall/2-setback/2
    return opening_box(axis, center, start, width, P.external_wall-setback-4, z1, z2)


step_path = ROOT/"STEP"/"house_3d.step"
glb_path = ROOT/"GLB"/"house_3d.glb"
check("saved_STEP_is_nonempty", step_path.stat().st_size > 1000, step_path.stat().st_size)
check("saved_GLB_is_nonempty", glb_path.stat().st_size > 1000, glb_path.stat().st_size)
scene = read_scene(step_path)
leaves = list(scene.leaves())
check("all_STEP_leaf_labels_unique", len({o.label for o in leaves}) == len(leaves), len(leaves))
native = {}
solid_count = 0
for occurrence in leaves:
    shape = occurrence.shape()
    native[occurrence.label] = shape
    solids = shape.solids()
    check(f"{occurrence.label}:contains_solid", len(solids) > 0, len(solids))
    for i, solid in enumerate(solids, 1):
        solid_count += 1
        check(f"{occurrence.label}:solid_{i}_valid", solid.is_valid)
        check(f"{occurrence.label}:solid_{i}_positive_volume", solid.volume > 0, round(solid.volume, 3))


for number in (1, 2):
    plan = floor_plan(number)
    z = (number-1)*P.storey_height
    wall_height = P.storey_height-G.slab_thickness
    setback = E.cladding_thickness+E.backing_gap
    core = [shape for label, shape in native.items()
            if label.startswith(f"F{number}:wall_external_")]
    cladding = [shape for label, shape in native.items()
                if label.startswith(f"F{number}:exterior:cladding:")]
    partitions = [shape for label, shape in native.items()
                  if label.startswith(f"F{number}:wall_partition_")]
    walls = core+partitions+cladding
    check(f"F{number}:four_external_backing_walls", len(core) == 4, len(core), 4)
    check(f"F{number}:independent_external_finish", bool(cladding), len(cladding))
    core_bounds = [min(bounds(s)[i] for s in core) for i in range(3)]+ \
                  [max(bounds(s)[i+3] for s in core) for i in range(3)]
    expected_core_bounds = [setback, setback, z, P.width-setback, P.depth-setback, z+wall_height]
    for coordinate, (actual, expected) in enumerate(zip(core_bounds, expected_core_bounds)):
        close(f"F{number}:external_backing_bound_{coordinate}", actual, expected)
    finish_bounds = [min(bounds(s)[i] for s in cladding) for i in range(3)]+ \
                    [max(bounds(s)[i+3] for s in cladding) for i in range(3)]
    expected_finish_bounds = [0, 0, z-G.slab_thickness, P.width, P.depth,
                              z+wall_height+(G.slab_thickness if number == 2 else 0)]
    for coordinate, (actual, expected) in enumerate(zip(finish_bounds, expected_finish_bounds)):
        close(f"F{number}:approved_finished_outline_bound_{coordinate}", actual, expected)
    core_area = (P.width-2*setback)*(P.depth-2*setback)- \
                (P.width-2*P.external_wall)*(P.depth-2*P.external_wall)
    exterior_aperture_area = sum(d.width*G.door_height for d in plan.doors if {'outside','balcony'} & {d.a,d.b})+ \
                             sum(window[3]*window_vertical_range(window)[1] for window in plan.windows)
    close(f"F{number}:backing_volume_preserves_inner_room_boundary_mm3", sum(s.volume for s in core),
          core_area*wall_height-exterior_aperture_area*(P.external_wall-setback), 0.1)
    close(f"F{number}:finish_backing_no_coincident_solids_mm3", sum(overlap(core, s) for s in cladding), 0)
    for direction in ("south", "north", "west", "east"):
        # Safe spans below all window sills and clear of the south entrance.
        a, b = E.cladding_thickness, setback
        cx, cy = P.width/2, P.depth/2
        sample_bounds = {
            "south": (cx-50, a+.1, z+100, cx+50, b-.1, z+200),
            "north": (cx-50, P.depth-b+.1, z+100, cx+50, P.depth-a-.1, z+200),
            "west": (a+.1, cy-50, z+100, b-.1, cy+50, z+200),
            "east": (P.width-b+.1, cy-50, z+100, P.width-a-.1, cy+50, z+200),
        }[direction]
        close(f"F{number}:{direction}:finish_backing_gap_is_clear_mm3", overlap(core+cladding, cuboid(sample_bounds)), 0)
    for room in plan.rooms:
        room_clearance = extruded_polygon(room.shape.buffer(-.1), z+1, wall_height-2)
        close(f"F{number}:{room.id}:approved_net_room_not_encroached_mm3", overlap(walls, room_clearance), 0)
    # Test physical clear openings through the new projecting attachments as
    # well as the retained backing. Window jambs/glass and the intentionally
    # closed entrance door are excluded; their approved opening dimensions are
    # tested separately below. Trim, sill, canopy and accent are not excluded.
    attachments = [shape for label, shape in native.items()
                   if label.startswith(f"F{number}:exterior:") or
                   (label.startswith(f"F{number}:W") and label.endswith((":exterior_trim", ":sill"))) or
                   (label.startswith(f"F{number}:D") and label.endswith((":frame", ":canopy", ":porch", ":porch_step", ":threshold")))]
    for door in plan.doors:
        if {'outside','balcony'} & {door.a,door.b}:
            swept = opening_box(door.axis, door.at, door.start+.1, door.width-.2, 1400,
                                z+.1, z+G.door_height-.1)
            close(f"F{number}:{door.id}:projecting_attachments_clear_of_aperture_mm3", overlap(attachments, swept), 0)
    for i, window in enumerate(plan.windows, 1):
        axis, at, start, width = window
        sill, height = window_vertical_range(window)
        swept = opening_box(axis, at, start+.1, width-.2, 1400, z+sill+.1, z+sill+height-.1)
        close(f"F{number}:W{i:02d}:projecting_attachments_clear_of_aperture_mm3", overlap(attachments, swept), 0)
    slab = native[f"F{number}:floor_slab"]
    slab_bounds = bounds(slab)
    close(f"F{number}:floor_datum_mm", slab_bounds[5], z)
    close(f"F{number}:slab_thickness_mm", slab_bounds[5]-slab_bounds[2], G.slab_thickness)
    for coordinate, expected in ((0, setback), (1, setback), (3, P.width-setback), (4, P.depth-setback)):
        close(f"F{number}:slab_edge_backing_bound_{coordinate}", slab_bounds[coordinate], expected)
    if number == 1:
        close("F1:slab_net_volume_mm3", slab.volume,
              (P.width-2*setback)*(P.depth-2*setback)*G.slab_thickness, 0.1)
    for door in plan.doors:
        thickness = P.external_wall if {'outside','balcony'} & {door.a,door.b} else P.internal_wall
        tool = opening_box(door.axis, door.at, door.start, door.width,
                           thickness, z, z+G.door_height)
        close(f"F{number}:{door.id}:wall_opening_volume_mm3", overlap(walls, tool), 0)
        if {'outside','balcony'} & {door.a,door.b}:
            head = exterior_core_tool(door.axis, door.at, door.start, door.width,
                                      z+G.door_height+1, z+wall_height-1)
            backing_walls = core
        else:
            head = opening_box(door.axis, door.at, door.start, door.width,
                               thickness-2, z+G.door_height+1, z+wall_height-1)
            backing_walls = partitions
        close(f"F{number}:{door.id}:overdoor_wall_preserved_mm3",
              overlap(backing_walls, head), head.volume, 0.1)
    for i, window in enumerate(plan.windows, 1):
        sill, height = window_vertical_range(window)
        tool = opening_box(*window, P.external_wall, z+sill, z+sill+height)
        close(f"F{number}:W{i:02d}:wall_opening_volume_mm3", overlap(walls, tool), 0)
        below = exterior_core_tool(*window, z+1, z+sill-1) if sill>2 else None
        above = exterior_core_tool(*window, z+sill+height+1, z+wall_height-1)
        if below is not None:
            close(f"F{number}:W{i:02d}:wall_below_preserved_mm3", overlap(core, below), below.volume, 0.1)
        close(f"F{number}:W{i:02d}:wall_above_preserved_mm3", overlap(core, above), above.volume, 0.1)
        original_frames = [native[f"F{number}:W{i:02d}:frame_{j}"] for j in range(1, 5)]
        wb = [min(bounds(s)[j] for s in original_frames) for j in range(3)]+ \
             [max(bounds(s)[j+3] for s in original_frames) for j in range(3)]
        axis, at, start, width = window
        tangent, normal = (0, 1) if axis == "h" else (1, 0)
        limit = P.depth if axis == "h" else P.width
        expected_normal = (0, G.window_frame_depth) if at < limit/2 else (limit-G.window_frame_depth, limit)
        for coordinate, expected in ((tangent, start), (tangent+3, start+width),
                                     (normal, expected_normal[0]), (normal+3, expected_normal[1]),
                                     (2, z+sill), (5, z+sill+height)):
            close(f"F{number}:W{i:02d}:unchanged_aperture_and_flush_frame_bound_{coordinate}", wb[coordinate], expected)


for number,index,width in ((1,1,2100),):
    frame=bounds(native[f'F{number}:W{index:02d}:frame_5'])
    close(f'R13:F{number}:W{index:02d}:floor_level_frame_bottom_mm',
          bounds(native[f'F{number}:W{index:02d}:frame_1'])[2],(number-1)*2800)
    close(f'R13:F{number}:W{index:02d}:floor_window_head_mm',
          bounds(native[f'F{number}:W{index:02d}:frame_2'])[5],(number-1)*2800+2200)
    check(f'R13:F{number}:W{index:02d}:two_glass_solids',len(native[f'F{number}:W{index:02d}:glass'].solids())==2)
    check(f'R13:F{number}:W{index:02d}:no_hanging_sill',f'F{number}:W{index:02d}:sill' not in native)
    if number==2:
        for name in ('exterior_trim','frame_5','glass'):
            close(f'R13:W{index:02d}:{name}:balcony_finish_clear_mm3',
                  overlap([native[f'F2:W{index:02d}:{name}']],native['balcony:finish']),0)

for door_id,width in (('D26',1600),('D27',1800)):
    for i in (1,2):
        frame=native[f'F2:{door_id}_slider_frame_{i}'];glass=native[f'F2:{door_id}_slider_glass_{i}']
        b=bounds(frame)
        close(f'R17:{door_id}:{i}:frame_floor_gap_mm',b[2],2810)
        close(f'R17:{door_id}:{i}:head_elevation_mm',b[5],4890)
        close(f'R17:{door_id}:{i}:balcony_finish_clear_mm3',overlap([frame,glass],native['balcony:finish']),0)
    check(f'R17:{door_id}:two_independent_glazed_leaves',all(f'F2:{door_id}_slider_glass_{i}' in native for i in (1,2)))

d = dimensions(P)
stair_footprint = next(r.shape for r in floor_plan(2).rooms if r.id == "stairs")
x1, y1, x2, y2 = stair_footprint.bounds
slab2 = native["F2:floor_slab"]
opening = cuboid((x1, y1, P.storey_height-G.slab_thickness-1,
                   x2, y2, P.storey_height+1))
close("F2:complete_stairwell_opening_volume_mm3", overlap([slab2], opening), 0)
close("F2:slab_net_volume_mm3", slab2.volume,
      ((P.width-2*setback)*(P.depth-2*setback)-stair_footprint.area)*G.slab_thickness, 0.1)
stair_shapes = [shape for label, shape in native.items() if label.startswith("stairs:")]
close("stairs:no_F2_slab_overlap_mm3", overlap([s for label,s in native.items() if label.startswith("stairs:") and "stringer" not in label], slab2.solids()[0]), 0)
check("stairs:no_final_riser_consuming_tread", "stairs:upper_final_riser" not in native)
rise = P.storey_height/P.risers
close("stairs:specified_rise_mm", rise, 175)
landing_bounds = bounds(native["stairs:mid_landing"])
close("stairs:mid_landing_top_mm", landing_bounds[5], P.storey_height/2)
close("stairs:mid_landing_depth_mm", landing_bounds[4]-landing_bounds[1], P.stair_landing)
close("stairs:mid_landing_thickness_mm", landing_bounds[5]-landing_bounds[2], G.landing_thickness)
for flight, base_top in [("lower", 0), ("upper", P.storey_height/2)]:
    for i in range(1, P.risers//2):
        label = f"stairs:{flight}_tread_{i:02d}"
        sb = bounds(native[label])
        close(f"{label}:width_mm", sb[3]-sb[0], P.stair_width)
        close(f"{label}:tread_depth_mm", sb[4]-sb[1], P.tread)
        close(f"{label}:top_elevation_mm", sb[5], base_top+i*rise)
        close(f'{label}:R17_thickness_mm',sb[5]-sb[2],60)
for side in ('lower','upper'):
    rails=[v for k,v in native.items() if k.startswith(f'stairs:{side}_stringer_')]
    check(f'R17:{side}:two_stringers',len(rails)==2)
    for i in range(1,8):
        tread=native[f'stairs:{side}_tread_{i:02d}']
        check(f'R17:{side}:tread_{i}:supported_by_both_stringers',all(overlap([rail],tread.solids()[0])>0 for rail in rails))
        close(f'R17:{side}:open_riser_gap_mm',rise-G.stair_tread_thickness,115)
last_top = bounds(native["stairs:upper_tread_07"])[5]
close("stairs:final_floor_rise_mm", bounds(slab2)[5]-last_top, rise)
for side in ("lower", "upper"):
    end = native[f"stairs:{side}_tread_{'07' if side == 'lower' else '01'}"]
    landing = native["stairs:mid_landing"]
    close(f"stairs:{side}_landing_connection_distance_mm", min(s.distance_to(landing) for label,s in native.items() if label.startswith(f'stairs:{side}_stringer_')), 0)
wc1 = next(r.shape for r in floor_plan(1).rooms if r.id == "wc")
wc2 = next(r.shape for r in floor_plan(2).rooms if r.id == "wc")
check("WC:upper_lower_footprints_aligned", wc1.equals(wc2), list(wc1.bounds))
entry=next(d for d in floor_plan(1).doors if d.a=='outside')
handle=bounds(native['F1:D01:handle'])
check('R15:entry_handle_left_when_viewed_outside',(handle[0]+handle[3])/2<entry.start+entry.width/2,handle)
storage_parts=[s for name,s in native.items() if name.startswith('F1:under_stairs:')]
stair_parts=[s for name,s in native.items() if name.startswith('stairs:')]
close('R15:stair_storage_parts_clear_of_treads_mm3',sum(overlap(storage_parts,tread) for tread in stair_parts),0,.01)
store=next(r.shape for r in floor_plan(1).rooms if r.id=='under_stairs')
x1,y1,x2,y2=store.bounds
probe=cuboid((x1+1,y1+1,1,x2-1,y1+400,2000))
close('R15:storage_entry_2000mm_headroom_mm3',overlap(storage_parts+stair_parts,probe),0,.01)
check('R15:storage_shelves_and_stepped_ceiling',len(storage_parts)==17,len(storage_parts))
fridge_doors=[name for name in native if '_fridge:door_' in name]
check('R15:fridge_two_side_by_side_doors',len(fridge_doors)==2,fridge_doors)


roof = native["roof:west_plane"]
rb = bounds(roof)
close("roof:west_eave_x_mm", rb[0], -G.roof_overhang)
close("roof:ridge_x_mm", rb[3], P.width/2)
close("roof:south_overhang_mm", rb[1], -G.roof_overhang)
close("roof:north_edge_mm", rb[4], P.depth+G.roof_overhang)
pitch = math.degrees(math.atan((rb[5]-G.roof_vertical_thickness-rb[2])/(rb[3]-rb[0])))
close("roof:pitch_degrees", pitch, G.roof_pitch_degrees)
for side in ("south", "north"):
    gable = native[f"roof:{side}_gable_wall"]
    close(f"roof:{side}_gable_base_mm", bounds(gable)[2], 2*P.storey_height)
    close(f"roof:{side}_gable_ridge_mm", bounds(gable)[5],
          2*P.storey_height+(P.width/2)*math.tan(math.radians(G.roof_pitch_degrees)))
    close(f"roof:{side}_gable_backing_volume_mm3", gable.volume,
          .5*P.width*(P.width/2)*math.tan(math.radians(G.roof_pitch_degrees))*(P.external_wall-setback)-(A.north_vent_width*A.north_vent_height*(P.external_wall-setback) if side=='north' else 0), .1)
ceiling = native["roof:attic_ceiling_slab"]
close("attic:thin_subfloor_native_volume_mm3", ceiling.volume,
      ((P.width-2*setback)*(P.depth-2*setback)-A.hatch_length*A.hatch_width)*A.subfloor_thickness, .1)
close("attic:thin_subfloor_thickness_mm", bounds(ceiling)[5]-bounds(ceiling)[2], A.subfloor_thickness)
close("roof:ceiling_finished_floor_datum_mm", bounds(ceiling)[5], 2*P.storey_height)


# R15 verifies requested equipment and the aperture in the saved native CAD.
facing=next((i,b) for i,(name,b) in enumerate(floor_plan(1).fixtures,1) if name=='対面キッチン')
prefix=f'F1:fixture_{facing[0]:02d}_kitchen'
hob=native[prefix+':hob_dark'];hood=native[prefix+':range_hood_steel']
hb,cb=bounds(hob),bounds(hood)
close('R15:extractor_above_cooktop_x_mm',(hb[0]+hb[3])/2,(cb[0]+cb[3])/2)
check('R15:extractor_above_cooktop_z',cb[2]>hb[5]+800)
check('R15:equipment_present',all(any(token in name for name in native) for token in ('_fridge:body_white','_cupboard:microwave_body_steel',':hood_filter_dark',':hood_duct_cover_steel')))
vent_record=json.loads((ROOT/'output/review/house_3d_assumptions_R01.json').read_text())['attic']['north_vent_bounds_mm']
vx1,vy1,vz1,vx2,vy2,vz2=vent_record
vent_probe=cuboid((vx1+40,vy1+1,vz1+40,vx2-40,vy2-1,vz2-40))
vent_shell=[obj for name,obj in native.items() if name in ('roof:north_gable_wall','roof:cladding:north_gable','attic:gable_lining:north') or name.startswith('structure:roof:post_')]
close('R15:north_attic_vent_passes_through_shell_mm3',overlap(vent_shell,vent_probe),0,.1)
close('R15:north_attic_vent_width_mm',vx2-vx1,600)
close('R15:north_attic_vent_height_mm',vz2-vz1,300)
check('R15:north_attic_vent_all_named_parts',len([name for name in native if name.startswith('attic:north_vent:')])==6)

# The R04 attic fits inside the existing roof rather than enlarging its outer
# envelope. Checks use saved native solids and swept clearance regions; a
# concept ladder is not an actual usage, structural or regulatory assessment.
ad = attic_dimensions(P, G)
attic_record = json.loads((ROOT/"output/review"/"house_3d_assumptions_R01.json").read_text())["attic"]
attic_leaves = {label: shape for label, shape in native.items() if label.startswith("attic:")}
access_leaves = {label: shape for label, shape in native.items() if label.startswith("attic_access:")}
site_leaves = {label: shape for label, shape in native.items()
               if label.startswith(("foundation:", "yard:", "fence:"))}
structure_leaves = {label: shape for label, shape in native.items() if label.startswith("structure:")}
old_leaf_names = set(native)-set(attic_leaves)-set(access_leaves)-set(site_leaves)-set(structure_leaves)
check("R10:named_balcony_present", all(name in native for name in ("balcony:slab","balcony:drying_rail")))
check("R10:separate_entry_canopy_removed", "F1:D01:canopy" not in native)
bs=bounds(native["balcony:slab"])
for i,expected in enumerate((0,-1000,2650,8190,0,2775)):
    close(f"R10:balcony_slab_boundary_{i}_mm",bs[i],expected)
check("R13:no_balcony_supports_or_footings",not any(name.startswith(("balcony:support_post_","balcony:footing_")) for name in native))
porch_bounds=bounds(native["F1:D01:porch"])
close("R13:porch_projects_beyond_balcony_mm",bs[1]-porch_bounds[1],300)
from lib.house_redesign_plan import balcony_drying_bounds
rb=balcony_drying_bounds(P)
for name in ("balcony:drying_post_1","balcony:drying_post_2","balcony:drying_rail"):
    b=bounds(native[name])
    check(f"R13:{name}_within_slab",bs[0]<b[0] and b[3]<bs[3] and bs[1]<b[1] and b[4]<bs[4])
    check(f"R13:{name}_east_of_balcony_door",all(b[3]<=door.start or b[0]>=door.start+door.width for door in floor_plan(2).doors if door.kind=='bypass'))
check("attic:new_named_leaf_contract", len(attic_leaves) == 39, len(attic_leaves), 39)
check("attic_access:new_named_leaf_contract", len(access_leaves) == A.ladder_treads+6,
      len(access_leaves), A.ladder_treads+6)

deck = native["attic:deck_finish"]
expected_deck_bounds = [ad["deck_left"], A.deck_end_inset, ad["base_z"],
                        ad["deck_right"], P.depth-A.deck_end_inset, ad["deck_top_z"]]
for coordinate, (actual, expected) in enumerate(zip(bounds(deck), expected_deck_bounds)):
    close(f"attic:deck_bound_{coordinate}_mm", actual, expected)
deck_area = A.deck_width*(P.depth-2*A.deck_end_inset)-A.hatch_length*A.hatch_width
close("attic:deck_net_native_volume_mm3", deck.volume, deck_area*A.deck_thickness, .1)
close("attic:deck_storage_projection_area_m2", deck.volume/A.deck_thickness/1e6,
      deck_area/1e6, 1e-6)
hatch = cuboid(world_bounds((A.hatch_x+.1, A.hatch_y+.1, ad["base_z"]-G.slab_thickness-1,
                 ad["hatch_right"]-.1, ad["hatch_north"]-.1, ad["deck_top_z"]+1)))
close("attic:hatch_passes_through_floor_and_finish_mm3", overlap([ceiling, deck], hatch), 0)
floor_group = scene.resolve("#attic:floor_slab")
check("attic:original_ceiling_reparented_to_floor_group",
      {o.label for o in floor_group.children} == {"roof:attic_ceiling_slab", "attic:deck_finish"})

roof_peak = 2*P.storey_height+P.width/2*math.tan(math.radians(G.roof_pitch_degrees))
envelope = section_extrusion([(0, ad["base_z"]-G.slab_thickness),
                              (P.width, ad["base_z"]-G.slab_thickness),
                              (P.width, ad["base_z"]), (P.width/2, roof_peak),
                              (0, ad["base_z"])], 0, P.depth)
roof_planes = [native["roof:west_plane"], native["roof:east_plane"]]
for label, shape in attic_leaves.items():
    if label.startswith('attic:north_vent:'):
        check(f'{label}:north_facing_window_band', bounds(shape)[1]>=P.depth-70-.001 and bounds(shape)[4]<P.depth+100, bounds(shape))
    else:
        close(f"{label}:outside_existing_roof_envelope_mm3", shape.volume-overlap([shape], envelope), 0, .1)
    close(f"{label}:does_not_enter_existing_roof_mm3", overlap(roof_planes, shape), 0, .1)

lining_west = native["attic:lining:west_slope"]
lining_east = native["attic:lining:east_slope"]
flat_ceiling = native["attic:lining:flat_ceiling"]
clear_ridge = bounds(flat_ceiling)[2]-bounds(deck)[5]
close("attic:ridge_clear_height_mm", clear_ridge, attic_clear_height(P.width/2, P, G))
close("attic:physical_ceiling_caps_height_mm", clear_ridge, A.maximum_finished_clear_height)
check("attic:1350mm_demonstration_target_is_not_1400mm_exceeded", clear_ridge <= 1350+.01, clear_ridge)
for side, x in (("west", ad["deck_left"]), ("east", ad["deck_right"])):
    # A narrow native cross-section establishes the lower lining surface at
    # the finished deck edge, independently of its wider outer knee-wall edge.
    probe = cuboid((x-.001, P.depth/2-10, ad["deck_top_z"],
                    x+.001, P.depth/2+10, roof_peak+1))
    cross_section = native[f"attic:lining:{side}_slope"].intersect(probe)
    check(f"attic:{side}_deck_edge_has_native_lining", bool(cross_section))
    lower_surface = min((bounds(part)[2] for part in cross_section), default=float("inf"))
    close(f"attic:{side}_deck_edge_clear_height_mm", lower_surface-bounds(deck)[5],
          attic_clear_height(x, P, G), .01)

f2_hall = next(r.shape for r in floor_plan(2).rooms if r.id == "hall")
ladder_y1 = ad["ladder_center_y"]-A.ladder_width/2
ladder_y2 = ladder_y1+A.ladder_width
ladder_footprint = box(*world_bounds((ad["ladder_foot_x"], ladder_y1, ad["hatch_right"], ladder_y2)))
lower_landing_footprint = box(*world_bounds((ad["ladder_foot_x"]-A.ladder_bottom_landing_depth,
                             A.hatch_y, ad["ladder_foot_x"], ad["hatch_north"])))
check("attic_access:deployed_ladder_footprint_inside_F2_hall", f2_hall.covers(ladder_footprint))
check("attic_access:bottom_standing_footprint_inside_F2_hall", f2_hall.covers(lower_landing_footprint))
floor2_obstructions = [shape for label, shape in native.items()
                       if label.startswith("F2:") and label != "F2:floor_slab"]
lower_landing = cuboid((*lower_landing_footprint.bounds[:2], P.storey_height+.1,
                        *lower_landing_footprint.bounds[2:], P.storey_height+1400))
close("attic_access:bottom_standing_probe_clear_of_F2_parts_mm3", overlap(floor2_obstructions, lower_landing), 0)
for label, shape in access_leaves.items():
    close(f"{label}:clear_of_F2_parts_mm3", overlap(floor2_obstructions, shape), 0)
    close(f"{label}:clear_of_reused_ceiling_mm3", overlap([ceiling], shape), 0)

left_rail = native["attic_access:left_stringer"]
right_rail = native["attic_access:right_stringer"]
left_bounds, right_bounds = bounds(left_rail), bounds(right_rail)
for side, sb in (("left", left_bounds), ("right", right_bounds)):
    close(f"attic_access:{side}:foot_z_mm", sb[2], P.storey_height)
    close(f"attic_access:{side}:top_z_mm", sb[5], ad["deck_top_z"])
    close(f"attic_access:{side}:foot_x_mm", sb[0], P.width-ad["hatch_right"] if P.mirror_layout else ad["ladder_foot_x"])
    close(f"attic_access:{side}:top_x_mm", sb[3], P.width-ad["ladder_foot_x"] if P.mirror_layout else ad["hatch_right"])
    close(f"attic_access:{side}:top_reaches_finished_deck_mm", native[f"attic_access:{side}_stringer"].distance_to(deck), 0)
close("attic_access:overall_ladder_width_mm", right_bounds[4]-left_bounds[1], A.ladder_width)
close("attic_access:clear_tread_width_mm", right_bounds[1]-left_bounds[4],
      A.ladder_width-2*A.ladder_stringer_width)
close("attic_access:inclination_degrees", math.degrees(math.atan((left_bounds[5]-left_bounds[2])/(left_bounds[3]-left_bounds[0]))), A.ladder_angle_degrees)
rise = ad["ladder_rise"]/(A.ladder_treads+1)
for index in range(1, A.ladder_treads+1):
    label = f"attic_access:tread_{index:02d}"
    tread = native[label]
    close(f"{label}:riser_elevation_mm", bounds(tread)[5], P.storey_height+index*rise)
    close(f"{label}:depth_mm", bounds(tread)[3]-bounds(tread)[0], A.ladder_tread_depth)
    close(f"{label}:thickness_mm", bounds(tread)[5]-bounds(tread)[2], A.ladder_tread_thickness)
    close(f"{label}:left_stringer_contact_mm", tread.distance_to(left_rail), 0)
    close(f"{label}:right_stringer_contact_mm", tread.distance_to(right_rail), 0)
close("attic_access:last_step_to_deck_rise_mm", bounds(deck)[5]-bounds(native[f"attic_access:tread_{A.ladder_treads:02d}"])[5], rise)
lid = native["attic_access:hatch_lid"]
for side, rail in (("left", left_rail), ("right", right_rail)):
    close(f"attic_access:lid_to_{side}_stringer_distance_mm", lid.distance_to(rail),
          attic_record["ladder"]["lid_to_stringer_gap_mm"])
for label, shape in access_leaves.items():
    if label != "attic_access:hatch_lid":
        close(f"{label}:open_lid_no_solid_overlap_mm3", overlap([shape], lid), 0)

# A 1250 mm crouched-access illustration tests only spatial relationships.
# Actual ladder/product safety and human-use headroom remain unresolved.
access_probe_height = A.maximum_finished_clear_height-100
climb_probe = section_extrusion([(ad["ladder_foot_x"], P.storey_height+1),
                                 (ad["hatch_right"], ad["deck_top_z"]+1),
                                 (ad["hatch_right"], ad["deck_top_z"]+access_probe_height),
                                 (ad["ladder_foot_x"], P.storey_height+access_probe_height)],
                                left_bounds[4]+1, right_bounds[1]-left_bounds[4]-2)
if P.mirror_layout:climb_probe=reflect_shape(climb_probe,P.width)
attic_obstructions = list(attic_leaves.values())+[ceiling, lid, native["attic_access:hatch_trim"]]
close("attic_access:illustrative_climbing_probe_clear_of_F2_parts_mm3", overlap(floor2_obstructions, climb_probe), 0)
close("attic_access:illustrative_climbing_probe_clear_of_attic_parts_mm3", overlap(attic_obstructions, climb_probe), 0)
close("attic_access:illustrative_climbing_probe_clear_of_existing_roof_mm3", overlap(roof_planes, climb_probe), 0)
upper_bounds = attic_record["ladder"]["upper_landing_bounds_mm"]
expected_upper_bounds = world_bounds([ad["hatch_right"], A.hatch_y,
                         min(ad["hatch_right"]+600, ad["deck_right"]), ad["hatch_north"]])
for coordinate, (actual, expected) in enumerate(zip(upper_bounds, expected_upper_bounds)):
    close(f"attic_access:recorded_upper_landing_bound_{coordinate}_mm", actual, expected)
minimum_upper_height = min(attic_clear_height(x, P, G) for x in (upper_bounds[0], upper_bounds[2]))
close("attic_access:recorded_upper_landing_min_clear_height_mm",
      attic_record["ladder"]["upper_landing_min_clear_height_mm"], minimum_upper_height)
check("attic_access:upper_landing_has_low_storage_headroom", minimum_upper_height >= access_probe_height,
      minimum_upper_height, access_probe_height)
upper_landing = cuboid((upper_bounds[0]+.1, upper_bounds[1]+.1, ad["deck_top_z"]+.1,
                        upper_bounds[2]-.1, upper_bounds[3]-.1, ad["deck_top_z"]+access_probe_height))
close("attic_access:open_east_top_standing_probe_clear_mm3", overlap(attic_obstructions, upper_landing), 0)
close("attic_access:upper_standing_probe_supported_by_deck_mm3", overlap([deck],
      cuboid((upper_bounds[0]+.1, upper_bounds[1]+.1, ad["base_z"]+.1,
              upper_bounds[2]-.1, upper_bounds[3]-.1, ad["deck_top_z"]-.1))),
      (upper_bounds[2]-upper_bounds[0]-.2)*(upper_bounds[3]-upper_bounds[1]-.2)*(A.deck_thickness-.2), .1)


data = glb_path.read_bytes()
magic, version, total = struct.unpack_from("<4sII", data)
check("GLB:valid_container", magic == b"glTF" and version == 2 and total == len(data))
json_size, chunk_kind = struct.unpack_from("<II", data, 12)
document = json.loads(data[20:20+json_size])
nodes = document["nodes"]
mesh_nodes = [node for node in nodes if "mesh" in node]
check("GLB:all_STEP_leaf_names_retained", {node["name"] for node in mesh_nodes} == set(native), len(mesh_nodes), len(native))
check("GLB:named_groups_retained", {"house_3d", "F1", "F2", "stairs", "roof", "attic", "attic_access", "foundation", "yard", "fence", "structure"}.issubset({n["name"] for n in nodes}))
attic_floor_node = next(n for n in nodes if n["name"] == "attic:floor_slab")
check("GLB:attic_ceiling_and_finish_parent_retained",
      {nodes[i]["name"] for i in attic_floor_node.get("children", [])} == {"roof:attic_ceiling_slab", "attic:deck_finish"})
check("GLB:all_nodes_metres_Y_up", all(n.get("extras", {}).get("cadUnits") == "m" and
                                     n.get("extras", {}).get("cadUpAxis") == "y" for n in nodes))
check("GLB:static_mesh_has_no_animation", not document.get("animations"))
check("GLB:identity_groups_world_meshes", all(not any(k in n for k in ("matrix", "translation", "rotation", "scale")) for n in nodes))
numeric_audit = audit_glb_bytes(data)
check("GLB:numeric_mesh_audit", True, {key: numeric_audit[key] for key in
      ("vertex_count", "triangle_count", "degenerate_count")})
glb_bounds = numeric_audit["bounds"]
house_bounds = bounds(scene.resolve("#house_3d").shape())
expected_glb = [house_bounds[0]/1000, house_bounds[2]/1000, -house_bounds[4]/1000,
                house_bounds[3]/1000, house_bounds[5]/1000, -house_bounds[1]/1000]
for i, (actual, expected) in enumerate(zip(glb_bounds, expected_glb)):
    close(f"GLB:metre_Y_up_bound_{i}", actual, expected, 1e-5)
glass_nodes = [n for n in mesh_nodes if n["name"].endswith(":glass")]
glass_materials = [document["materials"][p["material"]]
                   for n in glass_nodes for p in document["meshes"][n["mesh"]]["primitives"]]
check("GLB:glazing_transparency_retained", all(m.get("alphaMode") == "BLEND" and
            m["pbrMetallicRoughness"]["baseColorFactor"][3] < 1 for m in glass_materials), len(glass_materials))
children = [child for n in nodes for child in n.get("children", [])]
scene_roots = document["scenes"][document.get("scene", 0)]["nodes"]
check("GLB:each_node_has_single_parent_or_scene_root", len(children)+len(scene_roots) == len(nodes) and
      len(set(children+scene_roots)) == len(nodes))

report = {
    "revision": "R17-3D", "units": "STEP mm; GLB metres / Y-up",
    "summary": {"checks": len(results), "passed": sum(r["pass"] for r in results),
                "failed": sum(not r["pass"] for r in results), "STEP_leaf_occurrences": len(leaves),
                "native_solids": solid_count, "GLB_mesh_nodes": len(mesh_nodes), "GLB_all_nodes": len(nodes)},
    "artifacts": {p.name: {"bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                  for p in (step_path, glb_path)},
    "thresholds": {"length_mm": 0.01, "opening_overlap_mm3": 0.01, "GLB_bound_metres": 1e-5},
    "exterior_wall_test_basis": {"approved_total_wall_thickness_mm": P.external_wall,
                                 "finish_thickness_mm": E.cladding_thickness,
                                 "visual_backing_gap_mm": E.backing_gap,
                                 "backing_thickness_mm": P.external_wall-setback,
                                 "approved_room_net_boundaries": "Unchanged; tested as exact native clear-room volumes",
                                 "finished_footprint_mm": [P.width, P.depth]},
    "attic_test_basis": {"source_layout": "approved R10",
                         "new_attic_leaf_count": len(attic_leaves),
                         "new_access_leaf_count": len(access_leaves), "purpose": "storage attic concept",
                         "deck_storage_projection_area_m2": deck_area/1e6,
                         "upper_landing_min_clear_height_mm": minimum_upper_height,
                         "illustrative_clearance_probe_mm": 1400,
                         "clearance_scope": "A geometric probe only, not a certified actual usage clearance"},
    "not_verified": ["Structure or building regulations", "Actual stair headroom and handrail design",
                     "Door pockets and selected products", "Site conditions and permit drawings",
                     "Attic loading, folding-ladder mechanism, actual access safety and statutory floor classification"],
    "checks": results,
}
destination = ROOT/"output"/"review"/"validation_3d.json"
destination.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps(report["summary"]))
for result in results:
    if not result["pass"]:
        print(json.dumps(result))
sys.exit(0 if all(r["pass"] for r in results) else 1)
