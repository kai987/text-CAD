"""Export named Seto Ohashi Bisan pair STEP/GLB; no import-time writes.

CADGEN_DAEMON=0 .venv/bin/python src/seto_bridge_3d.py
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import struct

from cadgen import glb, read_scene, step
from lib.seto_bridge_geometry import MODEL_ID, REVISION, GROUPS, bridge_assembly, geometry_manifest
from lib.step_transport import compact_export

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ['src/lib/seto_bridge_geometry.py', 'src/lib/seto_bridge_activity.py', 'src/seto_bridge_3d.py', 'src/lib/step_transport.py']
STATIC_PARTS = '''export const clips = { named_parts: {label: "Static named Seto Ohashi assembly", duration: 1, loop: false, update(t,m) {}} };'''


@step(out='../STEP/seto_ohashi.step', animation=STATIC_PARTS)
def seto_ohashi():
    return bridge_assembly()


def fingerprint(path):
    raw = path.read_bytes()
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def restore_hierarchy(step_path, glb_path):
    """Restore STEP occurrence groups without changing a mesh coordinate."""
    raw=glb_path.read_bytes()
    if struct.unpack_from('<4sII',raw)!=(b'glTF',2,len(raw)):
        raise ValueError('Invalid GLB container')
    size,kind=struct.unpack_from('<II',raw,12)
    if kind!=0x4E4F534A: raise ValueError('Missing JSON chunk')
    doc=json.loads(raw[20:20+size]);nodes=doc['nodes'];indexed={}
    for index,node in enumerate(nodes):
        occurrence=node.get('extras',{}).get('cadOccurrenceId')
        if not occurrence or occurrence in indexed: raise ValueError('GLB requires unique CAD occurrence IDs')
        indexed[occurrence]=index
    scene=read_scene(step_path)
    def insert(occurrence):
        occurrence_id=occurrence.ref.removeprefix('#')
        if not occurrence.children:
            index=indexed[occurrence_id];node=nodes[index];node['name']=occurrence.label
            group=occurrence.label.split(':',1)[0]
            if group not in GROUPS: raise ValueError(f'Unclassified leaf: {occurrence.label}')
            node.setdefault('extras',{}).update({'bridgeGroup':group,'sourceUnits':'mm'})
            if group in ('traffic','vessels','trains'):
                node['extras']['actorId']=occurrence.label.split(':')[1]
            doc['meshes'][node['mesh']]['name']=occurrence.label
            return index
        children=[insert(child) for child in occurrence.children]
        node={'name':occurrence.label,'children':children,'extras':{'cadOccurrenceId':occurrence_id}}
        if occurrence.label in GROUPS: node['extras']['bridgeGroup']=occurrence.label
        index=len(nodes);nodes.append(node);return index
    doc['scenes']=[{'name':'SetoOhashiBisanPair','nodes':[insert(root) for root in scene.roots]}];doc['scene']=0
    for material in doc.get('materials',[]):
        pbr=material.setdefault('pbrMetallicRoughness',{})
        pbr['roughnessFactor']=.7;pbr['metallicFactor']=.12
    doc['asset']['extras']={'units':'metres','upAxis':'Y','revision':REVISION,'modelId':MODEL_ID,
        'status':'reference_concept_only','coordinateMapping':'(X,Z,-Y)/1000',
        'activity':geometry_manifest()['activity']}
    encoded=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();encoded+=b' '*(-len(encoded)%4)
    body=struct.pack('<II',len(encoded),kind)+encoded+raw[20+size:]
    glb_path.write_bytes(struct.pack('<4sII',b'glTF',2,len(body)+12)+body)
    return {'named_mesh_nodes':len(indexed),'all_nodes':len(nodes),'groups':list(GROUPS),
        'mesh_coordinates':'world-space metres; Y-up','mapping_from_CAD':'(X,Z,-Y)/1000'}


def generate(root=ROOT):
    root=Path(root)
    if root.resolve()!=ROOT.resolve(): raise ValueError('CADgen outputs are source-relative; generate inside the selected checkout')
    for directory in ('STEP','GLB','output/review'): (root/directory).mkdir(parents=True,exist_ok=True)
    sources={path:fingerprint(root/path)['sha256'] for path in SOURCES}
    print('Generating Seto Ohashi North/South Bisan pair',flush=True)
    seto_ohashi()
    step_path,glb_path=root/'STEP/seto_ohashi.step',root/'GLB/seto_ohashi.glb'
    glb.build(step_path,glb_path,animation={'clip':'named_parts','fps':1,'seconds':1},force=True)
    hierarchy=restore_hierarchy(step_path,glb_path)
    compact_export(step_path)
    from cadgen import build123d as bd
    saved=bd.import_step(step_path);bounds=saved.bounding_box()
    if not saved.is_valid: raise ValueError('Invalid saved bridge STEP')
    manifest=geometry_manifest()
    manifest['bbox']={'min':[bounds.min.X,bounds.min.Y,bounds.min.Z], 'max':[bounds.max.X,bounds.max.Y,bounds.max.Z]}
    manifest['saved_step']={'valid':True,'solids':len(saved.solids()),'datum':'T.P.; sea assumed at 0'}
    manifest['glb_export']=hierarchy
    if sources!={path:fingerprint(root/path)['sha256'] for path in SOURCES}:
        raise RuntimeError('Generation sources changed; regenerate from a stable snapshot')
    manifest['source_sha256']=sources
    manifest['artifacts']={path:fingerprint(root/path) for path in ['STEP/seto_ohashi.step','GLB/seto_ohashi.glb']}
    (root/'output/review/seto_ohashi_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'revision':REVISION,'solids':manifest['saved_step']['solids'],'bbox':manifest['bbox'],'artifacts':manifest['artifacts']}),flush=True)
    return manifest


if __name__=='__main__': generate()
