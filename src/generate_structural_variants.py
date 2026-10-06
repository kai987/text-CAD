"""Export three separately named, unengineered R07 material alternatives.

CADGEN_DAEMON=0 .venv/bin/python src/generate_structural_variants.py
Native STEP is millimetres/Z-up; GLB is metres/Y-up like the existing house.
Existing house and plan artifacts are not modified.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import struct
import sys

from cadgen import glb, read_scene, step
from lib.house_plan import P
from lib.structural_variants import build_variant, variant_manifest

ROOT=Path(__file__).resolve().parents[1]
STATIC_PARTS=r'''export const clips = {named_parts: {label: "Named structural alternative", duration: 1, loop: false, update(t, m) {}}};'''


@step(out='../STEP/structure_W.step',animation=STATIC_PARTS)
def structure_W():
    return build_variant('W')


@step(out='../STEP/structure_S.step',animation=STATIC_PARTS)
def structure_S():
    return build_variant('S')


@step(out='../STEP/structure_RC.step',animation=STATIC_PARTS)
def structure_RC():
    return build_variant('RC')


def restore_named_hierarchy(step_path,glb_path,system):
    data=glb_path.read_bytes()
    magic,version,total=struct.unpack_from('<4sII',data)
    if magic!=b'glTF' or version!=2 or total!=len(data):raise ValueError('Invalid GLB container')
    size,kind=struct.unpack_from('<II',data,12)
    doc=json.loads(data[20:20+size]);nodes=doc['nodes']
    occurrence_map={node['extras']['cadOccurrenceId']:i for i,node in enumerate(nodes)}
    def insert(item):
        occurrence=item.ref.removeprefix('#')
        if not item.children:
            index=occurrence_map[occurrence];nodes[index]['name']=item.label
            doc['meshes'][nodes[index]['mesh']]['name']=item.label
            return index
        index=len(nodes)
        children=[insert(child) for child in item.children]
        index=len(nodes)
        nodes.append({'name':item.label,'children':children,'extras':{'cadOccurrenceId':occurrence,'cadUnits':'m','cadUpAxis':'y'}})
        return index
    scene=read_scene(step_path)
    doc['scenes']=[{'name':f'structure_{system}','nodes':[insert(root) for root in scene.roots]}]
    doc['scene']=0
    doc['asset']['extras']={'units':'metres','upAxis':'Y','revision':'R09-STRUCTURE-VARIANTS',
                          'scope':'Demonstration geometry; capacity and statutory compliance uncalculated'}
    for material in doc.get('materials',[]):
        pbr=material.setdefault('pbrMetallicRoughness',{})
        pbr['roughnessFactor']=.45 if system=='S' else .86
        pbr['metallicFactor']=.5 if system=='S' else 0
    encoded=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode()
    encoded+=b' '*((-len(encoded))%4)
    body=struct.pack('<II',len(encoded),kind)+encoded+data[20+size:]
    glb_path.write_bytes(struct.pack('<4sII',b'glTF',2,12+len(body))+body)
    return {'named_mesh_nodes':len(occurrence_map),'all_nodes':len(nodes)}


def export(system):
    step_path=ROOT/'STEP'/f'structure_{system}.step'
    glb_path=ROOT/'GLB'/f'structure_{system}.glb'
    {'W':structure_W,'S':structure_S,'RC':structure_RC}[system]()
    glb.build(step_path,glb_path,animation={'clip':'named_parts','fps':1,'seconds':1},force=True)
    assembly=build_variant(system)
    record=variant_manifest(system,assembly)
    record['glb_export']=restore_named_hierarchy(step_path,glb_path,system)
    print(json.dumps({'system':system,'members':record['member_count'],'step':str(step_path),'glb':str(glb_path),
        'coordination_status':record['coordination']['status'],'aperture_collisions':len(record['coordination']['aperture_collisions']),
        'stair_collisions':len(record['coordination']['main_stair_collisions']),'hatch_collisions':len(record['coordination']['attic_hatch_collisions'])}),flush=True)
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--systems',nargs='+',choices=['W','S','RC'],default=['W','S','RC'])
    args=parser.parse_args()
    # CADgen's callable decorator parses process arguments on export. Consume
    # this generator's own options before invoking it.
    sys.argv=[sys.argv[0],"--force"]
    path=ROOT/'output/review/structural_variants_R07.json'
    manifest=json.loads(path.read_text()) if path.exists() else {'schema_version':1,'revision':'R09-STRUCTURE-VARIANTS',
        'status':'demonstration_candidates_not_engineered','original_architectural_parameters':asdict(P),
        'source_same_city_geometry':True,'city_specific_member_sizing':False,'variants':{}}
    manifest['revision']='R09-STRUCTURE-VARIANTS'
    manifest['original_architectural_parameters']=asdict(P)
    for system in args.systems:manifest['variants'][system]=export(system)
    path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(str(path),flush=True)


if __name__=='__main__':main()
