"""Check the saved 2LDK assets and their shared parametric plan.

Run: .venv/bin/python checks/validate_apartment.py
No CAD artifacts are regenerated. The JSON report is apartment-specific.
"""
from pathlib import Path
import hashlib
import json
import struct
import sys

import ezdxf
import fitz
from shapely.geometry import Point,box
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from cadgen import read_scene
from cadgen.geometry import overlap_volume
from lib.apartment_plan import P,apartment_plan,dimensions,manifest,window_specs
from lib.house_geometry import opening_box

results=[]
def check(name,condition,actual=None):
    results.append({'check':name,'pass':bool(condition),'actual':actual})
def close(name,actual,expected,tolerance=1e-4):
    check(name,abs(actual-expected)<tolerance,actual)

floor,raw=apartment_plan();d=dimensions();rooms={r.id:r for r in floor.rooms}
inside=[r for r in floor.rooms if r.id!='balcony']
check('rooms:all_valid',all(r.shape.is_valid and r.area>0 for r in floor.rooms))
for i,a in enumerate(inside):
    for b in inside[i+1:]:close(f'rooms:{a.id}:{b.id}:no_overlap',a.shape.intersection(b.shape).area,0)
close('area:rooms_plus_raw_walls_fill_envelope',sum(r.shape.area for r in inside)+raw.area,P.width*P.depth)
close('area:inside_net_excludes_balcony',sum(r.area for r in inside),56.54)
for name,bounds in floor.fixtures:
    fixture=box(*bounds)
    check(f'fixture:{name}:{bounds}:within_one_room',any(r.shape.covers(fixture) for r in inside))
    close(f'fixture:{name}:{bounds}:clear_of_walls',fixture.intersection(raw).area,0)
close('entry:clear_width_beyond_shoe_cabinet',P.hall_width-350,1050)
graph={name:set() for name in rooms};graph['outside']=set()
for door in floor.doors:
    graph[door.a].add(door.b);graph[door.b].add(door.a)
    thick=P.external_wall if door.a=='outside' else P.internal_wall
    close(f'{door.id}:clear_2d_wall_opening',floor.walls.intersection(door.opening(thick)).area,0)
    q=door.start+door.width/2; offset=thick/2+2
    points=[Point(q,door.at+s*offset) if door.axis=='h' else Point(door.at+s*offset,q) for s in (-1,1)]
    adjacent={r.id for r in floor.rooms if any(r.shape.contains(point) for point in points)}
    expected={door.a,door.b}-{'outside'}
    check(f'{door.id}:room_adjacency',adjacent==expected,sorted(adjacent))
    check(f'{door.id}:opening_clear_of_fixtures',all(door.opening(thick).intersection(box(*b)).area<1e-4 for _,b in floor.fixtures))
for a,b in manifest()['connections']:graph[a].add(b);graph[b].add(a)
seen={'outside'};todo=['outside']
while todo:
    for other in graph[todo.pop()]-seen:seen.add(other);todo.append(other)
check('circulation:every_room_reachable_from_entrance',set(rooms)<=seen,sorted(seen))
for w in window_specs():
    if w['id'] in ('W01','W02'):close(f"{w['id']}:level_balcony_access",w['sill'],0)

scene=read_scene(ROOT/'STEP/apartment_2ldk.step');native={}
for occurrence in scene.leaves():
    shape=occurrence.shape();native[occurrence.label]=shape
    check(f'{occurrence.label}:solid_present',len(shape.solids())>0)
    for i,solid in enumerate(shape.solids()):
        check(f'{occurrence.label}:{i}:valid_positive_solid',solid.is_valid and solid.volume>0)
walls=[s for label,s in native.items() if label.startswith('F1:wall_')]
def overlap(tool):
    return sum(overlap_volume(solid,cut) for wall in walls for solid in wall.solids() for cut in tool.solids())
for door in floor.doors:
    tool=opening_box(door.axis,door.at,door.start,door.width,
                     P.external_wall if door.a=='outside' else P.internal_wall,
                     0,P.clear_height if door.kind=='open' else P.door_height)
    close(f'{door.id}:saved_STEP_wall_opening',overlap(tool),0,.1)
for w in window_specs():
    tool=opening_box(w['axis'],w['at'],w['start'],w['width'],P.external_wall,w['sill'],w['sill']+w['height'])
    close(f"{w['id']}:saved_STEP_wall_opening",overlap(tool),0,.1)
close('STEP:ceiling_top',native['ceiling:slab'].bounding_box().max.Z,P.clear_height+P.slab_thickness)
close('STEP:balcony_area',native['balcony:slab'].volume/P.slab_thickness/1e6,11.7)

data=(ROOT/'GLB/apartment_2ldk.glb').read_bytes()
magic,version,total=struct.unpack_from('<4sII',data)
check('GLB:container',magic==b'glTF' and version==2 and total==len(data))
size,kind=struct.unpack_from('<II',data,12);document=json.loads(data[20:20+size])
nodes=document['nodes'];mesh_nodes=[n for n in nodes if 'mesh' in n]
check('GLB:STEP_names_retained',{n['name'] for n in mesh_nodes}==set(native),len(mesh_nodes))
check('GLB:semantic_groups',{'apartment_2ldk','F1','ceiling','balcony','F1:fixtures','F1:storage_fixtures'}<={n['name'] for n in nodes})
check('GLB:metres_Y_up',all(n.get('extras',{}).get('cadUnits')=='m' and n.get('extras',{}).get('cadUpAxis')=='y' for n in nodes))
check('GLB:static_scene',not document.get('animations') and document['scenes'][0]['name']=='apartment_2ldk')
positions=[document['accessors'][p['attributes']['POSITION']] for m in document['meshes'] for p in m['primitives']]
extent=[min(a['min'][i] for a in positions) for i in range(3)]+[max(a['max'][i] for a in positions) for i in range(3)]
for i,(actual,expected) in enumerate(zip(extent,[0,-.2,-8.4,7.8,2.7,1.5])):close(f'GLB:metre_bound_{i}',actual,expected,1e-5)
glass_nodes=[n for n in mesh_nodes if ':glass_' in n['name']]
check('GLB:8_glass_panes',len(glass_nodes)==8,len(glass_nodes))
check('GLB:transparent_glazing',all(document['materials'][p['material']].get('alphaMode')=='BLEND'
      for n in glass_nodes for p in document['meshes'][n['mesh']]['primitives']))

doc=ezdxf.readfile(ROOT/'DXF/apartment_2ldk_plan.dxf');msp=doc.modelspace()
check('DXF:millimetres',doc.units==4)
check('DXF:clean_audit',not doc.audit().has_errors)
check('DXF:editable_dimensions',len(msp.query('DIMENSION'))>=6,len(msp.query('DIMENSION')))
texts=[e.dxf.text for e in msp.query('TEXT')]
check('DXF:editable_room_labels',all(r.name in texts for r in floor.rooms))
check('DXF:A3_layout','JP_A3_APARTMENT_1_50' in doc.layouts.names())
check('DXF:adaptive_black_white_text',all(e.dxf.color in (7,256) for e in msp.query('TEXT')))

saved=json.loads((ROOT/'output/review/apartment_2ldk_manifest.json').read_text())
expected=manifest()
for key in ('parameters','areas','floors','assumptions'):
    check(f'manifest:{key}:matches_current_parameters',saved[key]==expected[key])
meta=json.loads((ROOT/'output/review/apartment_2ldk_preview.json').read_text())
pdfbytes=(ROOT/meta['source']['path']).read_bytes()
check('preview:PDF_hash',hashlib.sha256(pdfbytes).hexdigest()==meta['source']['sha256'])
pdf=fitz.open(stream=pdfbytes,filetype='pdf')
check('PDF:one_A3_landscape_page',len(pdf)==1 and abs(pdf[0].rect.width-420*72/25.4)<.01 and abs(pdf[0].rect.height-297*72/25.4)<.01)
for row in meta['floors']:
    svg=(ROOT/row['path']).read_bytes()
    check('preview:SVG_hash',len(svg)==row['bytes'] and hashlib.sha256(svg).hexdigest()==row['sha256'])
    check('preview:outlined_vector_only',b'<text' not in svg and b'<image' not in svg)
    for required in row['requiredLabels']:
        check(f'preview:label:{required}',any(required in a['text'] for a in row['annotations']))
summary={'checks':len(results),'passed':sum(r['pass'] for r in results),'failed':sum(not r['pass'] for r in results),
         'STEP_leaf_occurrences':len(native),'areas':expected['areas']}
(ROOT/'output/review/apartment_2ldk_validation.json').write_text(json.dumps({'summary':summary,'checks':results},ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False))
for row in results:
    if not row['pass']:print(json.dumps(row,ensure_ascii=False))
raise SystemExit(0 if summary['failed']==0 else 1)
