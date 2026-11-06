"""Read-only source, saved-solid, GLB and editable-drawing checks for BRIDGE-R03.

This audits saved geometry, not structural capacity, geotechnical conditions,
navigation clearance or construction conformity. It never blesses stale files.
"""
import hashlib
import json
from math import isfinite
import os
from pathlib import Path
import struct
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT))
os.environ.setdefault('CADGEN_DAEMON','0')
import ezdxf
from pypdf import PdfReader
from cadgen import read_scene
from lib.native_glb import audit_glb_bytes
from lib.seto_bridge_geometry import MODEL_ID, REVISION, GROUPS, geometry_manifest, component_specs, parameters
from lib.seto_bridge_activity import activity_manifest
from checks.seto_bridge_clearance import physical_clearance_checks
from checks.seto_r02_baseline import ANCHOR_NAMES, FLOORBEAM_NAMES

GEOMETRY_SOURCES=['src/lib/seto_bridge_geometry.py','src/lib/seto_bridge_activity.py','src/seto_bridge_3d.py','src/lib/step_transport.py']
DRAWING_SOURCES=['src/lib/seto_bridge_geometry.py','src/lib/seto_bridge_activity.py','src/generate_seto_bridge_plans.py']
NATIVE_PATHS=['STEP/seto_ohashi.step','GLB/seto_ohashi.glb']
DRAWING_PATHS=[f'{folder}/seto_ohashi_{view}.{extension}' for view in ('plan','elevation','section')
               for folder,extension in [('DXF','dxf'),('output/svg','svg')]]+['output/pdf/seto_ohashi_sheets.pdf']


def validate(root=ROOT):
    root=Path(root);results=[]
    def check(name,condition,actual=None):
        row={'check':name,'pass':bool(condition)}
        if actual is not None: row['actual']=actual
        results.append(row)
    def digest(path): return hashlib.sha256((root/path).read_bytes()).hexdigest()
    def bindings(label,metadata,sources,paths):
        check(label+':exact_sources',set(metadata.get('source_sha256',{}))==set(sources))
        for path in sources: check(label+':source:'+path,metadata.get('source_sha256',{}).get(path)==digest(path))
        check(label+':exact_artifacts',set(metadata.get('artifacts',{}))==set(paths))
        for path in paths:
            value=metadata.get('artifacts',{}).get(path,{})
            check(label+':artifact:'+path,value=={'sha256':digest(path),'bytes':(root/path).stat().st_size})
    manifest=json.loads((root/'output/review/seto_ohashi_manifest.json').read_text())
    for key,value in geometry_manifest().items(): check('manifest:'+key,manifest.get(key)==value)
    bindings('geometry',manifest,GEOMETRY_SOURCES,NATIVE_PATHS)
    sidecar=json.loads((root/'STEP/seto_ohashi.step.json').read_text())
    check('STEP:appearance_sidecar_hash',sidecar.get('documentHash')==digest('STEP/seto_ohashi.step'))
    specs={p['name']:p for p in component_specs()};native={};clearance_shapes={}
    bounds_min=[float('inf')]*3;bounds_max=[float('-inf')]*3
    scene=read_scene(root/'STEP/seto_ohashi.step')
    for occurrence in scene.leaves():
        name=occurrence.label;shape=occurrence.shape();solids=list(shape.solids())
        check('STEP:unique:'+name,name not in native)
        check('STEP:valid_positive:'+name,bool(solids) and shape.is_valid and all(s.is_valid and isfinite(s.volume) and s.volume>0 for s in solids))
        bb=shape.bounding_box();minimum=[bb.min.X,bb.min.Y,bb.min.Z];maximum=[bb.max.X,bb.max.Y,bb.max.Z]
        native[name]={'min':minimum,'max':maximum}
        if specs.get(name,{}).get('group') in ('foundations','towers','truss','road','railway'):
            clearance_shapes[name]=shape
        for axis in range(3):
            bounds_min[axis]=min(bounds_min[axis],minimum[axis]);bounds_max[axis]=max(bounds_max[axis],maximum[axis])
    check('STEP:exact_component_names',set(native)==set(specs),len(native))
    for kind,values in [('min',bounds_min),('max',bounds_max)]:
        saved=manifest.get('bbox',{}).get(kind,[])
        check('STEP:manifest_bbox:'+kind,len(saved)==3 and all(abs(a-b)<.001 for a,b in zip(saved,values)))
    check('STEP:four_portal_towers',len([name for name in native if name.startswith('towers:') and ':leg_' in name])==8)
    check('STEP:single_shared_anchor',len([name for name in native if name=='foundations:BB4A_shared:V_notched_body'])==1)
    activity=activity_manifest(parameters())
    # Reopen and intersect saved anchorage/floorbeam solids. The perforated
    # shape cannot be validated from metadata or outer bounds alone.
    for row in physical_clearance_checks(list(specs.values()),parameters(),activity,clearance_shapes):
        check('STEP:'+row['check'],row['pass'],row['actual'])
    road=lambda x:parameters()['road_deck_z_mm']-.01*max(abs(x),parameters()['shared_anchor_half_length_mm'])
    traffic_bounds=[bounds for name,bounds in native.items() if name.startswith('traffic:')]
    max_vehicle_height=max(bounds['max'][2]-min(road(bounds['min'][0]),road(bounds['max'][0])) for bounds in traffic_bounds)
    for bridge in ('north','south'):
        for number in (1,2):
            name=f'towers:{bridge}:tower_{number}:crossbeam_2'
            bounds=native[name]
            beam_center=(bounds['min'][0]+bounds['max'][0])/2
            clearance=bounds['min'][2]-road(beam_center)
            check('STEP:actual_vehicle_clearance:'+name,clearance>=max_vehicle_height+1000,
                  {'clearance_mm':clearance,'conservative_vehicle_height_mm':max_vehicle_height})
    check('STEP:TP_maximum',abs(bounds_max[2]-194000)<50,bounds_max[2])
    raw=(root/'GLB/seto_ohashi.glb').read_bytes();audit=audit_glb_bytes(raw)
    length,kind=struct.unpack_from('<II',raw,12)
    document=json.loads(raw[20:20+length]);nodes=document['nodes'];leaves=[n for n in nodes if 'mesh' in n]
    check('GLB:exact_STEP_names',len(leaves)==len(native) and {n.get('name') for n in leaves}==set(native))
    check('GLB:parent_groups',set(GROUPS)<={n.get('name') for n in nodes})
    meta=document.get('asset',{}).get('extras',{})
    check('GLB:identity_units',meta.get('units')=='metres' and meta.get('upAxis')=='Y' and meta.get('modelId')==MODEL_ID and meta.get('revision')==REVISION)
    check('GLB:motion_metadata',meta.get('activity')==activity)
    check('actors:generic_routes_v2',activity.get('schema_version')==2 and all(
        set(a['route'])=={'axis','min_mm','max_mm','fixed_mm'} and a['route']['axis'] in ('x','y') and
        a['route']['min_mm']<a['route']['max_mm'] for a in activity['actors']))
    actor_names={name:actor['id'] for actor in activity['actors'] for name in actor['part_names']}
    check('actors:exact_named_saved_parts',all(name in native for name in actor_names))
    check('actors:leaf_identity',all(node.get('extras',{}).get('actorId')==actor_names[node['name']]
        for node in leaves if node.get('name') in actor_names))
    check('actors:24_vehicles',sum(actor['group']=='traffic' for actor in activity['actors'])==24)
    check('actors:4_vessels',sum(actor['group']=='vessels' for actor in activity['actors'])==4)
    check('actors:8_train_carriages',sum(actor['group']=='trains' for actor in activity['actors'])==8)
    check('actors:2_four_car_consists',len({a['train_id'] for a in activity['actors'] if a['group']=='trains'})==2 and all(
        sum(a.get('train_id')==ident for a in activity['actors'])==4
        for ident in {a['train_id'] for a in activity['actors'] if a['group']=='trains'}))
    check('GLB:numeric_finite_triangles',audit['triangle_count']>0,audit['triangle_count'])
    identity=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
    check('GLB:identity_world_transforms',all(n.get('translation',[0,0,0])==[0,0,0] and n.get('scale',[1,1,1])==[1,1,1]
        and n.get('rotation',[0,0,0,1])==[0,0,0,1] and n.get('matrix',identity)==identity for n in nodes))
    by_mesh={row['mesh_index']:row['bounds'] for row in audit['primitives']}
    for node in leaves:
        cad=native.get(node.get('name'));gl=by_mesh.get(node['mesh'])
        if cad is None or gl is None: continue
        lo,hi=cad['min'],cad['max']
        expected=[lo[0]/1000,lo[2]/1000,-hi[1]/1000,hi[0]/1000,hi[2]/1000,-lo[1]/1000]
        check('GLB:STEP_bounds:'+node['name'],all(abs(a-b)<=.0006 for a,b in zip(gl,expected)))
    drawings=json.loads((root/'output/review/seto_ohashi_drawings.json').read_text())
    check('drawings:identity',drawings.get('id',drawings.get('model_id'))==MODEL_ID and drawings.get('revision')==REVISION
        and drawings.get('status')=='reference_concept_only' and drawings.get('source_geometry_revision')==REVISION)
    bindings('drawings',drawings,DRAWING_SOURCES,DRAWING_PATHS)
    for view in ('plan','elevation','section'):
        row=next((r for r in drawings.get('drawings',[]) if r.get('id')==view),{})
        doc=ezdxf.readfile(root/f'DXF/seto_ohashi_{view}.dxf');msp=doc.modelspace()
        check(view+':DXF_audit',not doc.audit().errors)
        check(view+':DXF_mm',doc.units==4)
        texts=[e.dxf.text for layout in doc.layouts for e in layout.query('TEXT')]
        check(view+':editable_labels',len(texts)>3)
        measured=sorted(float(e.get_measurement()) for e in msp.query('DIMENSION'))
        declared=sorted(row.get('dimensions_mm',[]))
        check(view+':native_dimensions',bool(measured) and len(measured)==len(declared) and all(abs(a-b)<.01 for a,b in zip(measured,declared)),measured)
        svg=ET.parse(root/f'output/svg/seto_ohashi_{view}.svg').getroot()
        check(view+':SVG_metadata',svg.get('data-revision')==REVISION and svg.get('data-units')=='mm')
        values=sorted(float(e.get('data-dimension-mm')) for e in svg.iter() if e.get('data-dimension-mm') is not None)
        check(view+':SVG_dimensions',len(values)==len(declared) and all(abs(a-b)<.001 for a,b in zip(values,declared)))
        check(view+':SVG_safe',all(e.tag.split('}')[-1].lower() not in ('script','image','foreignobject') for e in svg.iter()))
        visible='\n'.join(svg.itertext())
        check(view+':required_labels',all(t in visible and any(t in text for text in texts) for t in row.get('required_labels',[])))
        check(view+':natural_clearance_term','通行純空' not in visible and all('通行純空' not in text for text in texts))
        if view=='elevation': check(view+':published_spans',all(any(abs(n-target)<.01 for n in measured) for target in [1538000,1648000,990000,1100000]))
        if view=='section':
            check(view+':published_north_section',all(any(abs(n-target)<.01 for n in measured) for target in [30000,13000,35000]))
            check(view+':rail_crest_and_emu_height',all(any(abs(n-target)<.01 for n in measured) for target in [420,5300]))
            check(view+':editable_transport_passage','通行有効高さ' in visible and 'BB4A' in visible and
                any('通行有効高さ' in text for text in texts))
    pdf=PdfReader(root/'output/pdf/seto_ohashi_sheets.pdf')
    check('PDF:three_pages',len(pdf.pages)==3)
    check('PDF:A3_landscape',all(abs(float(page.mediabox.width)-420*72/25.4)<.1 and abs(float(page.mediabox.height)-297*72/25.4)<.1 for page in pdf.pages))
    summary={'revision':REVISION,'checks':len(results),'passed':sum(r['pass'] for r in results),'failed':sum(not r['pass'] for r in results),
        'STEP_leaf_occurrences':len(native),'GLB_meshes':len(leaves),'triangles':audit['triangle_count'],
        'scope':'Saved source-bound appearance geometry and editable drawings; engineering uncalculated.'}
    return {'summary':summary,'checks':results}


def main():
    report=validate()
    (ROOT/'output/review/seto_ohashi_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report['summary'],ensure_ascii=False))
    for row in report['checks']:
        if not row['pass']: print(json.dumps(row,ensure_ascii=False))
    raise SystemExit(0 if report['summary']['failed']==0 else 1)


if __name__=='__main__': main()
