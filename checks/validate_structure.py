"""Geometric acceptance for R06 saved structural demonstration and supplements.

No calculation of member strength, wall rating or statutory compliance occurs.
Use --source for a lightweight frame check before whole-house exports exist.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import struct
import sys

import ezdxf
from ezdxf.lldxf import const
import fitz
from shapely.geometry import box

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from cadgen import read_scene
from cadgen.geometry import overlap_volume
from lib.house_plan import P,floor_plan
from lib.house_geometry import G,cuboid,opening_box,window_vertical_range,extruded_polygon
from lib.structure_geometry import T,structure_group,structure_manifest,structure_dimensions
from lib.engineering_inputs import engineering_inputs
from lib.contact_geometry import ContactGeometry

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',action='store_true',help='Validate a lightweight frame before whole-house export')
parser.add_argument('--report',type=Path,help='Write acceptance JSON to this path instead of the default review report')
args=parser.parse_args()
results=[]
contacts=ContactGeometry()


def check(name,condition,actual=None,expected=None):
    results.append({'check':name,'pass':bool(condition),'actual':actual,'expected':expected})


def close(name,actual,expected,tolerance=.01):
    check(name,abs(actual-expected)<=tolerance,round(actual,6),expected)


def bounds(shape):
    b=shape.bounding_box();return [b.min.X,b.min.Y,b.min.Z,b.max.X,b.max.Y,b.max.Z]


def broad_overlap(a,b):return all(a[i]<b[i+3]-1e-7 and b[i]<a[i+3]-1e-7 for i in range(3))


def overlap(a,b):
    if not broad_overlap(bounds(a),bounds(b)):return 0.
    return sum(overlap_volume(sa,sb) for sa in a.solids() for sb in b.solids())


def shared_face_area(a,b):
    """Actual common planar face area, not mere bounding-box coincidence."""
    return contacts.shared_face_area(a,b)


record=structure_manifest(P,G)
d=structure_dimensions(P,G)
if args.source:
    group=structure_group(P,G)
    native={shape.label:shape for child in group.children for shape in child.children}
    all_native=native
else:
    all_native={occurrence.label:occurrence.shape() for occurrence in read_scene(ROOT/'STEP/house_3d.step').leaves()}
    native={label:shape for label,shape in all_native.items() if label.startswith('structure:')}
    saved=json.loads((ROOT/'output/review/house_3d_assumptions_R01.json').read_text())
    check('saved:structure_manifest_matches_parameters',saved['structure']==record)
    check('saved:revision_R06',saved['revision']=='R09-3D',saved['revision'],'R09-3D')
    raw=(ROOT/'GLB/house_3d.glb').read_bytes()
    magic,version,size=struct.unpack_from('<4sII',raw)
    check('GLB:valid_container',magic==b'glTF' and version==2 and size==len(raw))
    length,kind=struct.unpack_from('<II',raw,12)
    check('GLB:JSON_chunk',kind==0x4E4F534A)
    glb=json.loads(raw[20:20+length])
    meshes=[node.get('name') for node in glb['nodes'] if 'mesh' in node and node.get('name','').startswith('structure:')]
    check('GLB:all_saved_structure_names_preserved',set(meshes)==set(native) and len(meshes)==len(native),len(meshes),len(native))
    groups={node.get('name') for node in glb['nodes'] if 'children' in node}
    check('GLB:independent_structure_categories',all(name in groups for name in (
        'structure','structure:columns','structure:beams','structure:sills','structure:attic_joists',
        'structure:attic_headers','structure:roof_framing','structure:bearing_walls')))

expected_columns={f"structure:F{n}:column_{c['id']}" for c in record['columns'] for n in c['floors']}
check('structure:all_recorded_named_columns',expected_columns=={name for name in native if ':column_' in name},len(expected_columns),len(expected_columns))
check('structure:all_leaf_names_unique',len(native)==len(set(native)))
for label,shape in native.items():
    check(f'{label}:valid_positive_solid',shape.is_valid and all(s.volume>0 for s in shape.solids()) and bool(shape.solids()))

for c in record['columns']:
    for n in c['floors']:
        label=f"structure:F{n}:column_{c['id']}";shape=native[label];b=bounds(shape)
        profile=box(b[0],b[1],b[3],b[4])
        close(f'{label}:inside_approved_closed_wall_mm2',profile.difference(floor_plan(n).walls).area,0,.01)
        close(f'{label}:column_top_reaches_beam_bottom_mm',b[5],d[f'F{n}_beam_bottom_z'])
        beams=[s for name,s in native.items() if name.startswith(f'structure:F{n}:beam_')]
        actual_contacts=sum(shared_face_area(shape,beam) for beam in contacts.candidates(shape,beams) if abs(shape.distance_to(beam))<.001)
        check(f'{label}:positive_face_to_upper_beam',actual_contacts>1,round(actual_contacts,3))
        supports=[s for name,s in native.items() if name.startswith('structure:F1:sill_' if n==1 else 'structure:F1:beam_')]
        actual_contacts=sum(shared_face_area(shape,support) for support in contacts.candidates(shape,supports) if abs(shape.distance_to(support))<.001)
        check(f'{label}:positive_face_to_lower_support',actual_contacts>1,round(actual_contacts,3))
    if c['floors']==[1,2]:
        a,b=bounds(native[f"structure:F1:column_{c['id']}"]),bounds(native[f"structure:F2:column_{c['id']}"])
        check(f"{c['id']}:upper_lower_column_plan_alignment",a[:2]+a[3:5]==b[:2]+b[3:5])

for n in (1,2):
    f=floor_plan(n);z=(n-1)*P.storey_height
    members=[shape for name,shape in native.items() if name.startswith(f'structure:F{n}:')]
    for door in f.doors:
        thickness=P.external_wall if {'outside','balcony'} & {door.a,door.b} else P.internal_wall
        tool=opening_box(door.axis,door.at,door.start+.1,door.width-.2,thickness,z+.1,z+G.door_height-.1)
        close(f'F{n}:{door.id}:structure_keeps_actual_door_opening_clear_mm3',sum(overlap(s,tool) for s in members),0,.1)
    for index,window in enumerate(f.windows,1):
        sill,height=window_vertical_range(window)
        axis,at,start,width=window
        tool=opening_box(axis,at,start+.1,width-.2,P.external_wall,z+sill+.1,z+sill+height-.1)
        close(f'F{n}:W{index:02d}:structure_keeps_actual_window_opening_clear_mm3',sum(overlap(s,tool) for s in members),0,.1)
    for wall in record['bearing_wall_candidates']:
        panel=native[f"structure:F{n}:bearing_wall_{wall['id']}"]
        for end in wall['end_columns']:
            post=native[f'structure:F{n}:column_{end}']
            area=shared_face_area(panel,post)
            check(f"F{n}:{wall['id']}:{end}:actual_positive_panel_post_face",area>1,round(area,3))
        check(f"F{n}:{wall['id']}:wall_multiplier_and_connection_capacity_unassigned",wall['wall_multiplier'] is None and wall['connection_capacity'] is None)

stair=next(room.shape for room in floor_plan(2).rooms if room.id=='stairs')
tool=extruded_polygon(stair.buffer(-.1),.1,P.storey_height+200)
close('stairs:frame_keeps_main_stair_travel_volume_clear_mm3',sum(overlap(shape,tool) for shape in native.values()),0,.1)
h=d['hatch']
tool=cuboid((h[0]+.1,h[1]+.1,d['attic_joist_bottom_z']+.1,h[2]-.1,h[3]-.1,d['attic_subfloor_top_z']-.1))
close('hatch:actual1200x650_aperture_unobstructed_by_structure_mm3',sum(overlap(shape,tool) for shape in native.values()),0,.1)
for name in ('structure:attic:header_south','structure:attic:header_north'):
    b=bounds(native[name]);close(f'{name}:clear_span_between_trimmers_mm',b[3]-b[0],1200)
    for side in ('west','east'):
        area=shared_face_area(native[name],native[f'structure:attic:trimmer_{side}'])
        check(f'{name}:positive_face_to_{side}_trimmer',area>1,round(area,3))

for label,shape in native.items():
    if ':joist_' in label or ':trimmer_' in label:
        b=bounds(shape);close(f'{label}:top_matches_real_subfloor_bottom_mm',b[5],d['attic_subfloor_bottom_z'])
        beams=[s for name,s in native.items() if name.startswith('structure:F2:beam_')]
        area=sum(shared_face_area(shape,beam) for beam in contacts.candidates(shape,beams) if shape.distance_to(beam)<.001)
        check(f'{label}:positive_face_to_attic_support_beam',area>1,round(area,3))
    if ':roof:post_' in label:
        beams=[s for name,s in native.items() if name.startswith('structure:F2:beam_')]
        area=sum(shared_face_area(shape,s) for s in contacts.candidates(shape,beams) if shape.distance_to(s)<.001)
        check(f'{label}:positive_face_to_lower_beam',area>1,round(area,3))
        roof_members=[s for name,s in native.items() if ':roof:purlin_' in name or name=='structure:roof:ridge_beam']
        area=sum(shared_face_area(shape,s) for s in contacts.candidates(shape,roof_members) if shape.distance_to(s)<.001)
        check(f'{label}:positive_face_to_roof_beam',area>1,round(area,3))

items=sorted(native.items())
for index,(label,shape) in enumerate(items):
    for other_label,other in items[index+1:]:
        if broad_overlap(bounds(shape),bounds(other)):
            close(f'{label}:{other_label}:no_duplicate_structural_volume_mm3',overlap(shape,other),0,.1)

if not args.source:
    foundation=[s for name,s in all_native.items() if name.startswith(('foundation:','F1:exterior:foundation:'))]
    for label,sill in native.items():
        if ':sill_' not in label:continue
        close(f'{label}:bottom_at_foundation_top_mm',bounds(sill)[2],-200)
        area=sum(shared_face_area(sill,s) for s in contacts.candidates(sill,foundation) if sill.distance_to(s)<.001)
        check(f'{label}:positive_face_to_actual_foundation',area>1,round(area,3))
    inputs=json.loads((ROOT/'output/review/engineering_inputs_R06.json').read_text())
    check('engineering_inputs:saved_record_matches_unfilled_brief',inputs==engineering_inputs(P,G))
else:inputs=engineering_inputs(P,G)
for section in ('site_inputs','material_inputs','load_inputs'):
    check(f'engineering_inputs:{section}:not_fabricated',all(value is None for value in inputs[section].values()))
check('engineering_inputs:no_structural_or_statutory_result',inputs['capacity_results'] is None and inputs['statutory_compliance_result'] is None)
check('manifest:unverified_geometry_is_not_engineering_result',record['capacity_results'] is None and record['statutory_compliance_result'] is None and record['material_grade'] is None)

# Lightweight parameter checks inspect a changed subassembly dimension rather
# than building the whole house or mirroring an implementation line-by-line.
for depth in (160,200):
    changed=replace(T,attic_joist_depth=depth)
    dd=structure_dimensions(P,G,changed)
    close(f'parameter:joist_depth_{depth}:beam_and_joist_meet_mm',dd['F2_beam_top_z'],dd['attic_joist_bottom_z'])
    close(f'parameter:joist_depth_{depth}:subfloor_datum_preserved_mm',dd['attic_joist_top_z'],5576)
    check(f'parameter:joist_depth_{depth}:F2_beam_keeps2100_headroom',dd['F2_beam_bottom_z']-P.storey_height>=2100)

dxf=ezdxf.readfile(ROOT/'DXF/house_structural_scheme.dxf')
check('DXF:mm_units_and_clean_audit',dxf.units==4 and not dxf.audit().has_errors)
dims=list(dxf.modelspace().query('DIMENSION'))
check('DXF:editable_structural_dimensions',len(dims)>=8,len(dims))
measurements=[round(dim.get_measurement()) for dim in dims]
check('DXF:house_hatch_and_deck_measurements_present',all(value in measurements for value in (P.width,1200,650,3680)),measurements)
dimension_paper_heights=[]
for dimension in dims:
    scale=75 if dimension.dxf.defpoint.y>=18000 else 50
    dimension_paper_heights.extend(entity.dxf.char_height/scale for entity in
        dxf.blocks.get(dimension.dxf.geometry).query('MTEXT'))
check('DXF:dimension_char_height2_5mm_on_each_scale',len(dimension_paper_heights)==len(dims) and
      all(abs(height-2.5)<.001 for height in dimension_paper_heights),dimension_paper_heights)
check('DXF:annotations_are_adaptive_black_white',all(e.dxf.color in (7,256) for e in dxf.modelspace().query('TEXT MTEXT DIMENSION')))
for name,scale in (('STRUCTURE_01_A3_1_50',50),('STRUCTURE_02_A3_1_75',75)):
    viewports=[v for v in dxf.layouts.get(name).query('VIEWPORT') if v.dxf.id>1]
    check(f'DXF:{name}:single_locked_exact_scale_viewport',len(viewports)==1 and bool(viewports[0].dxf.flags&const.VSF_LOCK_ZOOM) and abs(viewports[0].dxf.view_height/viewports[0].dxf.height-scale)<.001)
pdf=fitz.open(ROOT/'output/pdf/house_structural_scheme_R06_JP.pdf')
check('PDF:two_A3_landscape_sheets',len(pdf)==2 and all(abs(page.rect.width-420*72/25.4)<.01 and abs(page.rect.height-297*72/25.4)<.01 for page in pdf))
text='\n'.join(page.get_text() for page in pdf)
check('PDF:structural_pending_scope_and_geometry_legends',all(word in text for word in ('構造計算未実施','断面未計算','検修口','1350','耐震等級','1:25','工程入力')) or all(word in text for word in ('構造計算未実施','断面未計算','検修口','1350','耐震等級','1:25','未設定項目')))
for number,page in enumerate(pdf,1):
    spans=[span for block in page.get_text('dict')['blocks'] if 'lines' in block for line in block['lines'] for span in line['spans']]
    check(f'PDF:page{number}:all_text_inside_paper',all(span['bbox'][0]>=0 and span['bbox'][1]>=0 and span['bbox'][2]<=page.rect.width+.01 and span['bbox'][3]<=page.rect.height+.01 for span in spans))

out=args.report if args.report is not None else ROOT/'output/review'/('structure_source_validation_R06.json' if args.source else 'structure_validation_R06.json')
out.write_text(json.dumps({'scope':'Geometry and record acceptance only; no structural calculations or legal determination','pass':all(r['pass'] for r in results),'checks':results},ensure_ascii=False,indent=2)+'\n')
failures=[r for r in results if not r['pass']]
print(json.dumps({'mode':'source' if args.source else 'saved','checks':len(results),'failures':failures,'report':str(out)},ensure_ascii=False,indent=2))
raise SystemExit(bool(failures))
