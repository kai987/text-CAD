"""Generate independent named Tokyo Tower and Tokyo Skytree STEP/GLB files.

Run from the repository root:
    CADGEN_DAEMON=0 .venv/bin/python src/towers_3d.py

Importing the module does not write files. Geometry is original schematic CAD
from cited control dimensions, with every unverified detail marked assumed.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import struct

from cadgen import glb, read_scene, step
from lib.tower_geometry import (REVISION, TOWERS, GROUPS, component_specs,
                                geometry_manifest, geometry_source_paths, tower_assembly)
from lib.step_transport import compact_export

ROOT = Path(__file__).resolve().parents[1]
STATIC_PARTS = r'''
export const clips = {
  named_parts: {label: "Static named landmark assembly", duration: 1,
                loop: false, update(t, m) {}}
};
'''


@step(out='../STEP/tokyo_tower.step', animation=STATIC_PARTS)
def tokyo_tower():
    return tower_assembly('tokyo-tower')


@step(out='../STEP/tokyo_skytree.step', animation=STATIC_PARTS)
def tokyo_skytree():
    return tower_assembly('tokyo-skytree')


def restore_hierarchy(step_path, glb_path, tower_id):
    """Restore exact CAD occurrence names and groups; keep every mesh byte."""
    raw=glb_path.read_bytes()
    magic,version,total=struct.unpack_from('<4sII',raw)
    if (magic,version,total)!=(b'glTF',2,len(raw)):
        raise ValueError('Expected a complete GLB 2.0 container')
    size,kind=struct.unpack_from('<II',raw,12)
    if kind!=0x4E4F534A:
        raise ValueError('GLB first chunk must be JSON')
    doc=json.loads(raw[20:20+size]);nodes=doc['nodes'];indexed={}
    for index,node in enumerate(nodes):
        occurrence=node.get('extras',{}).get('cadOccurrenceId')
        if not occurrence or occurrence in indexed:
            raise ValueError('Named GLB needs exactly one unique occurrence per leaf')
        indexed[occurrence]=index
    scene=read_scene(step_path)
    material_cache={}
    specifications = {part['name']: part for part in component_specs(tower_id)}
    detailed = TOWERS[tower_id].get('revision',REVISION) in ('LANDMARK-R02','LANDMARK-R03','LANDMARK-R04','LANDMARK-R05','LANDMARK-R06','LANDMARK-R07')

    def insert(occurrence):
        occurrence_id=occurrence.ref.removeprefix('#')
        if not occurrence.children:
            index=indexed[occurrence_id];node=nodes[index];node['name']=occurrence.label
            mesh=doc['meshes'][node['mesh']];mesh['name']=occurrence.label
            group=occurrence.label.split(':',1)[0]
            if group not in GROUPS:
                raise ValueError(f'Unclassified exported leaf: {occurrence.label}')
            node.setdefault('extras',{}).update({'landmarkGroup':group,'sourceUnits':'mm'})
            specification = specifications[occurrence.label]
            role = specification.get('role', 'glazing' if 'glazing' in occurrence.label else 'structure')
            if tower_id=='tokyo-skytree' or TOWERS[tower_id].get('revision') in ('LANDMARK-R05','LANDMARK-R06','LANDMARK-R07'):
                node['extras']['landmarkPrimitive'] = specification['kind']
            if detailed:
                node['extras']['landmarkRole'] = role
                if 'flight' in specification:
                    node['extras']['landmarkFlight'] = specification['flight']
                node['extras']['landmarkDetail'] = role in ('connection_detail', 'light_lens', 'obstruction_light_lens')
                if specification.get('steel_node_id'):
                    node['extras']['steelNodeId'] = specification['steel_node_id']
                    node['extras']['steelDetailKind'] = specification['steel_detail_kind']
                    node['extras']['steelMicro'] = specification.get('detail_level') == 'steel_micro'
            for primitive in mesh['primitives']:
                old=primitive['material'];finish='glass' if role == 'glazing' or 'glazing' in occurrence.label else 'solid'
                key=(old,finish,role) if detailed else (old,finish)
                if key not in material_cache:
                    material=deepcopy(doc['materials'][old]);pbr=material.setdefault('pbrMetallicRoughness',{})
                    pbr['roughnessFactor']=.28 if finish=='glass' else .68
                    pbr['metallicFactor']=.25 if finish=='glass' else .12
                    material['name']=f'{"tokyo" if tower_id == "tokyo-tower" else "skytree"}_{old}_{finish}_{role}' if detailed else f'landmark_{old}_{finish}'
                    if finish=='glass':
                        material['emissiveFactor']=[.012,.018,.025]
                        if detailed:
                            # R02 uses separate thin panes rather than a solid
                            # transparent deck volume. Geometry stays in STEP.
                            pbr.setdefault('baseColorFactor',[.35,.54,.62,1])[3]=(float(TOWERS[tower_id].get('detail',{}).get('deck_appearance',{}).get('glass_alpha',.30)) if group=='decks' else .30)
                            pbr['roughnessFactor']=.16
                            pbr['metallicFactor']=.05
                            material['alphaMode']='BLEND'
                            material['doubleSided']=True
                    if detailed and role in ('light_lens', 'obstruction_light_lens'):
                        material['emissiveFactor']=[0,0,0]
                        pbr['roughnessFactor']=.2
                    material_cache[key]=len(doc['materials']);doc['materials'].append(material)
                primitive['material']=material_cache[key]
            return index
        children=[insert(child) for child in occurrence.children]
        index=len(nodes)
        node={'name':occurrence.label,'children':children,
              'extras':{'cadOccurrenceId':occurrence_id,'cadUnits':'m','cadUpAxis':'y'}}
        if occurrence.label in GROUPS:node['extras']['landmarkGroup']=occurrence.label
        nodes.append(node)
        return index

    doc['scenes']=[{'name':TOWERS[tower_id]['file_stem'],'nodes':[insert(root) for root in scene.roots]}]
    doc['scene']=0
    doc['asset']['extras']={'units':'metres','upAxis':'Y','revision':TOWERS[tower_id].get('revision',REVISION),
                            'landmarkId':tower_id,'status':'reference_concept_only',
                            'source':'Original named CADgen appearance model using cited control heights; unverified dimensions are schematic assumptions, not original-building CAD.'}
    if tower_id == 'tokyo-tower':
        doc['asset']['extras']['steelNodes'] = geometry_manifest(tower_id)['steel_nodes']
    encoded=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode()
    encoded+=b' '*(-len(encoded)%4)
    body=struct.pack('<II',len(encoded),kind)+encoded+raw[20+size:]
    temporary=glb_path.with_suffix('.glb.tmp')
    temporary.write_bytes(struct.pack('<4sII',b'glTF',2,len(body)+12)+body)
    temporary.replace(glb_path)
    # CADgen stores world-space meshes; newly inserted groups are identities.
    return {'named_mesh_nodes':len(indexed),'all_nodes':len(nodes),'groups':list(GROUPS),
            'mesh_coordinates':'world-space metres; Y-up','mapping_from_CAD':'(X,Z,-Y)/1000'}


def fingerprint(path):
    data=path.read_bytes()
    return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}


def generate(tower_ids=None,root=ROOT):
    root=Path(root)
    if root.resolve()!=ROOT.resolve():
        raise ValueError('CADgen source-relative output paths require this repository root')
    for directory in ['STEP','GLB','output/review']:(root/directory).mkdir(parents=True,exist_ok=True)
    manifests=[]
    generators={'tokyo-tower':tokyo_tower,'tokyo-skytree':tokyo_skytree}
    for tower_id in tower_ids or TOWERS:
        if tower_id not in TOWERS:raise ValueError(f'Unknown tower {tower_id}')
        p=TOWERS[tower_id];stem=p['file_stem']
        source_paths = [*geometry_source_paths(tower_id),'src/towers_3d.py']
        source_snapshot = {name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in source_paths}
        print(f'Generating {tower_id}: named reference-concept solids',flush=True)
        generators[tower_id]()
        step_path=root/f'STEP/{stem}.step';glb_path=root/f'GLB/{stem}.glb'
        glb.build(step_path,glb_path,animation={'clip':'named_parts','fps':1,'seconds':1},force=True)
        hierarchy=restore_hierarchy(step_path,glb_path,tower_id)
        compact_export(step_path)
        # Bounds and validity come from the actual saved STEP, not a second
        # in-memory generator, and remain independent of GLB presentation.
        from cadgen import build123d as bd
        saved=bd.import_step(step_path);bounds=saved.bounding_box()
        if not saved.is_valid:raise ValueError(f'Invalid saved STEP: {tower_id}')
        if abs(bounds.max.Z-p['height_mm'])>.05:
            raise ValueError(f'Wrong saved tip height {tower_id}: {bounds.max.Z}')
        manifest=geometry_manifest(tower_id)
        manifest['bbox']={'min':[bounds.min.X,bounds.min.Y,bounds.min.Z],
                          'max':[bounds.max.X,bounds.max.Y,bounds.max.Z]}
        manifest['saved_step']={'valid':bool(saved.is_valid),'solids':len(saved.solids()),'ground_datum_mm':0}
        manifest['glb_export']=hierarchy
        if any(hashlib.sha256((root/name).read_bytes()).hexdigest() != digest
               for name,digest in source_snapshot.items()):
            raise RuntimeError('Tower generation sources changed during export; regenerate from a stable source snapshot.')
        manifest['source_sha256']=source_snapshot
        manifest['artifacts']={name:fingerprint(root/name)
                               for name in (f'STEP/{stem}.step',f'GLB/{stem}.glb')}
        destination=root/f'output/review/{stem}_manifest.json'
        destination.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        manifests.append(manifest)
        print(json.dumps({'id':tower_id,'bbox':manifest['bbox'],'solids':manifest['saved_step']['solids'],
                          'named_nodes':hierarchy['named_mesh_nodes'],'artifacts':manifest['artifacts']},ensure_ascii=False),flush=True)
    return manifests


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tower',choices=list(TOWERS),action='append')
    args,cadgen_args=parser.parse_known_args()
    # The CADgen decorator parses process arguments when a generator runs.
    # Consume our catalog selector before handing its own flags to CADgen.
    import sys
    sys.argv=[sys.argv[0],*cadgen_args]
    generate(args.tower)
