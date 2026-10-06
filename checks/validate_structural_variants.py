"""Accept R07 saved geometry only; never certify structure or local compliance."""
from __future__ import annotations

import argparse
import json
from math import isfinite
from pathlib import Path
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from cadgen import build123d as bd, read_scene
from lib.attic_geometry import A
from lib.house_geometry import G
from lib.house_plan import P, dimensions
from lib.structural_variants import _overlap, geometry_coordination, shape_bounds, solid_box
from lib.contact_geometry import ContactGeometry

results=[]
contacts=ContactGeometry()


def check(name,condition,actual=None,expected=None):
    results.append({'check':name,'pass':bool(condition),'actual':actual,'expected':expected})


def close(name,actual,expected,tolerance=.01):
    check(name,abs(actual-expected)<=tolerance,round(actual,6),expected)


def shared_face_area(a,b):
    """Native planar contact area, as opposed to a bounding-box touching test."""
    return contacts.shared_face_area(a,b)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,help='Write acceptance JSON to this path instead of the default review report')
    args=parser.parse_args()
    manifest=json.loads((ROOT/'output/review/structural_variants_R07.json').read_text())
    check('manifest:three_distinct_material_systems',set(manifest['variants'])=={'W','S','RC'})
    check('manifest:city_selection_does_not_invent_member_sizes',manifest['source_same_city_geometry'] is True and manifest['city_specific_member_sizing'] is False)
    counts={};geometries={}
    for system,record in manifest['variants'].items():
        native={item.label:item.shape() for item in read_scene(ROOT/record['step_path']).leaves()}
        counts[system]=len(native)
        check(f'{system}:native_named_members_match_manifest',set(native)=={item['name'] for item in record['members']} and len(native)==record['member_count'])
        check(f'{system}:no_unintended_architectural_or_site_shell',all(name.startswith(('structure:','foundation:')) for name in native))
        for item in record['members']:
            name=item['name'];shape=native[name];bounds=shape_bounds(shape)
            check(f'{system}:{name}:finite_valid_positive_native_solids',shape.is_valid and bool(shape.solids()) and all(s.volume>0 and isfinite(s.volume) for s in shape.solids()) and all(isfinite(x) for x in bounds))
            close(f'{system}:{name}:native_volume_matches_saved_record',shape.volume,item['volume_mm3'],.1)
            check(f'{system}:{name}:native_bounds_match_saved_record',all(abs(a-b)<.001 for a,b in zip(bounds,item['bounds_mm'])))
        for key in ('capacity_results','statutory_compliance_result','foundation_engineering_result','material_grade','manufacturing_specification','reinforcement_schedule','self_weight_design_result'):
            check(f'{system}:{key}:not_fabricated',record[key] is None)
        check(f'{system}:not_sized_separately_for_cities',record['source_same_city_geometry'] is True and record['city_specific_member_sizing'] is False)
        raw=(ROOT/record['glb_path']).read_bytes();magic,version,size=struct.unpack_from('<4sII',raw)
        check(f'{system}:GLB_valid_container',magic==b'glTF' and version==2 and size==len(raw))
        length,kind=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+length])
        check(f'{system}:GLB_JSON_chunk',kind==0x4E4F534A)
        glb_names=[node.get('name') for node in doc['nodes'] if 'mesh' in node]
        check(f'{system}:GLB_exact_native_member_names',set(glb_names)==set(native) and len(glb_names)==len(native))
        check(f'{system}:GLB_shared_world_coordinates',doc['asset']['extras']['upAxis']=='Y' and doc['asset']['extras']['units']=='metres' and all('matrix' not in node and 'translation' not in node and 'rotation' not in node and 'scale' not in node for node in doc['nodes']))
        for node in doc['nodes']:
            if 'mesh' not in node:continue
            n=shape_bounds(native[node['name']]);primitives=doc['meshes'][node['mesh']]['primitives']
            positions=[doc['accessors'][primitive['attributes']['POSITION']] for primitive in primitives]
            expected=[n[0]/1000,n[2]/1000,-n[4]/1000,n[3]/1000,n[5]/1000,-n[1]/1000]
            actual=[min(pos['min'][i] for pos in positions) for i in range(3)]+[max(pos['max'][i] for pos in positions) for i in range(3)]
            check(f"{system}:{node['name']}:GLB_mm_to_Yup_metres_preserves_location",all(abs(a-b)<.001 for a,b in zip(actual,expected)),actual,expected)
        # Recheck native exported solids, independently of the source assembly
        # and of the saved collision report. Reconstruct only the grouping.
        assembly=bd.Compound(children=list(native.values()),label=f'validation_{system}')
        coordination=geometry_coordination(assembly,system,P,G)
        for key in ('aperture_collisions','main_stair_collisions','attic_hatch_collisions','room_intrusions','exterior_outline_projections'):
            check(f'{system}:{key}:saved_report_matches_actual_export',coordination[key]==record['coordination'][key])
        check(f'{system}:actual_door_and_window_apertures_clear',not coordination['aperture_collisions'],coordination['aperture_collisions'])
        check(f'{system}:actual_main_stair_clear',not coordination['main_stair_collisions'],coordination['main_stair_collisions'])
        check(f'{system}:actual_attic_hatch_clear',not coordination['attic_hatch_collisions'],coordination['attic_hatch_collisions'])
        check(f'{system}:no_unreported_room_intrusion',not coordination['room_intrusions'] or (system=='RC' and all(item['room_id']=='balcony' for item in coordination['room_intrusions']) and coordination['status']=='architectural_coordination_pending'),coordination['room_intrusions'])
        foundation=[shape for name,shape in native.items() if name.startswith('foundation:')]
        base=[(name,shape) for name,shape in native.items() if ':sill_' in name and system=='W' or ':base_plate_' in name and system=='S' or name.startswith('structure:F1:column_') and system=='RC']
        for name,shape in base:
            close(f'{system}:{name}:bottom_at_foundation_top_mm',shape_bounds(shape)[2],-200)
            area=sum(shared_face_area(shape,support) for support in contacts.candidates(shape,foundation) if shape.distance_to(support)<.001)
            check(f'{system}:{name}:positive_native_face_to_foundation',area>1,round(area,4))
        for name,post in native.items():
            if ':column_' not in name:continue
            floor=1 if name.startswith('structure:F1:') else 2
            upper=[shape for label,shape in native.items() if label.startswith(f'structure:F{floor}:beam_')]
            upper_area=sum(shared_face_area(post,beam) for beam in contacts.candidates(post,upper) if post.distance_to(beam)<.001)
            check(f'{system}:{name}:positive_native_face_to_upper_beam',upper_area>1,round(upper_area,4))
            if floor==2:
                lower=[shape for label,shape in native.items() if label.startswith('structure:F1:beam_')]
            elif system=='RC':lower=foundation
            else:lower=[shape for label,shape in native.items() if label.startswith('structure:F1:sill_')]
            lower_area=sum(shared_face_area(post,support) for support in contacts.candidates(post,lower) if post.distance_to(support)<.001)
            check(f'{system}:{name}:positive_native_face_to_lower_support',lower_area>1,round(lower_area,4))
        if system=='S':
            post=native['structure:F1:column_C01'];p=record['parameters'];b=shape_bounds(post)
            width=p['exterior_column_width'];t=p['column_wall_thickness']
            close('S:hollow_column_true_material_volume',post.volume,(width*width-(width-2*t)**2)*(b[5]-b[2]),.1)
            check('S:hollow_column_centre_is_void',not post.is_inside((90,90,1000)))
            check('S:hollow_column_2_3mm_wall_is_material',post.is_inside((149,90,1000)))
            check('S:has_actual_straps_gussets_and_baseplates',all(any(kind in name for name in native) for kind in (':strap_brace_',':gusset_',':base_plate_')))
            check('S:sloped_purlins_are_connected_hollow_sections',all(len(shape.solids())==1 for name,shape in native.items() if ':purlin_' in name))
        if system=='RC':
            slab=native['structure:F2:slab_floor'];attic=native['structure:attic:slab_storage']
            stair_tool=solid_box((dimensions(P)['sx']+.1,dimensions(P)['sy']+.1,2620.1,dimensions(P)['xmax']-.1,dimensions(P)['ymax']-.1,2799.9),'stair_tool','#FFFFFF')
            hatch_tool=solid_box((A.hatch_x+.1,A.hatch_y+.1,5420.1,A.hatch_x+A.hatch_length-.1,A.hatch_y+A.hatch_width-.1,5599.9),'hatch_tool','#FFFFFF')
            close('RC:stair_is_true_slab_void_mm3',_overlap(slab,stair_tool),0,.1)
            close('RC:attic_hatch_is_true_slab_void_mm3',_overlap(attic,hatch_tool),0,.1)
            check('RC:floor_and_attic_material_exist_beside_holes',slab.is_inside((3600,3600,2700)) and attic.is_inside((2500,3800,5500)))
            check('RC:outward_projection_explicitly_pending',coordination['status']=='architectural_coordination_pending' and coordination['actual_exterior_frame_outline_mm']==[-120,-120,P.width+120,P.depth+120] and bool(coordination['exterior_outline_projections']))
            check('RC:reinforcing_bars_not_invented',not any('rebar' in name for name in native))
        geometries[system]=sorted((name,round(shape.volume,3),tuple(round(v,3) for v in shape_bounds(shape))) for name,shape in native.items())
    check('variants:distinct_geometry_not_recolouring',len({json.dumps(value) for value in geometries.values()})==3,counts)
    # R10 intentionally replaces architectural assets. Historical apartment files remain separate.
    check('R10:approved_architectural_parameters',manifest['original_architectural_parameters']['width']==P.width and manifest['original_architectural_parameters']['depth']==P.depth)
    failures=[result for result in results if not result['pass']]
    report={'scope':'Native geometry, shared coordinates and uncalculated status only; no safety or compliance conclusion',
        'pass':not failures,'member_counts':counts,'checks':results}
    destination=args.report if args.report is not None else ROOT/'output/review/structural_variants_validation_R07.json'
    destination.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'checks':len(results),'member_counts':counts,'failures':failures,'report':str(destination)},ensure_ascii=False,indent=2))
    raise SystemExit(bool(failures))


if __name__=='__main__':main()
