"""Audit saved landmark STEP/GLB/DXF/SVG/PDF; never generate or bless assets.

This checks numerical geometry, named-part correspondence and source bindings.
It does not validate the geometry against a survey or certify real structures.
"""
from __future__ import annotations

import hashlib
import json
from math import isfinite, pi, dist
import os
from pathlib import Path
import struct
import sys
import xml.etree.ElementTree as ET

import ezdxf
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
os.environ.setdefault('CADGEN_DAEMON', '0')
from cadgen import read_scene
from lib.native_glb import audit_glb_bytes
from lib.tower_geometry import TOWERS, REVISION, GROUPS, component_specs, geometry_manifest, geometry_source_paths


def close(actual, expected, tolerance=1e-3):
    return isfinite(actual) and abs(actual - expected) <= tolerance


def validate(root=ROOT):
    root = Path(root)
    checks = []

    def check(name, condition, actual=None):
        checks.append({'check': name, 'pass': bool(condition), 'actual': actual})

    def bindings(label, metadata, sources, artifacts):
        check(label + ':source_catalog', set(metadata.get('source_sha256', {})) == set(sources))
        for path in sources:
            check(label + ':source:' + path,
                  metadata.get('source_sha256', {}).get(path) == hashlib.sha256((root / path).read_bytes()).hexdigest())
        check(label + ':artifact_catalog', set(metadata.get('artifacts', {})) == set(artifacts))
        for path in artifacts:
            raw = (root / path).read_bytes()
            record = metadata.get('artifacts', {}).get(path, {})
            check(label + ':artifact:' + path, record == {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})

    for tower_id, parameters in TOWERS.items():
        prefix = tower_id + ':'
        stem = parameters['file_stem']
        revision = parameters.get('revision', REVISION)
        try:
            model_paths = [f'STEP/{stem}.step', f'GLB/{stem}.glb']
            drawing_paths = [f'DXF/{stem}_{view}.dxf' for view in ('plan', 'elevation')]
            svg_paths = [f'output/svg/{stem}_{view}.svg' for view in ('plan', 'elevation')]
            if tower_id == 'tokyo-tower':
                drawing_paths.append(f'DXF/{stem}_steel_nodes.dxf')
                svg_paths.append(f'output/svg/{stem}_steel_nodes.svg')
            else:
                drawing_paths.append(f'DXF/{stem}_structure_zones.dxf')
                svg_paths.append(f'output/svg/{stem}_structure_zones.svg')
            pdf_path = f'output/pdf/{stem}_sheets.pdf'
            manifest = json.loads((root / f'output/review/{stem}_manifest.json').read_text())
            drawings = json.loads((root / f'output/review/{stem}_drawings.json').read_text())
            expected = geometry_manifest(tower_id)
            for key in ('id', 'names', 'revision', 'units', 'height_mm', 'parameters',
                        'groups', 'assumptions', 'source_references', 'engineering', 'files', *(['steel_nodes'] if tower_id == 'tokyo-tower' else [])):
                check(prefix + 'manifest:' + key, manifest.get(key) == expected.get(key))
            check(prefix + 'reference_scope', manifest.get('status') == 'reference_concept_only')
            bindings(prefix + 'model', manifest,
                     [*geometry_source_paths(tower_id), 'src/towers_3d.py'], model_paths)
            bindings(prefix + 'drawings', drawings,
                     [*geometry_source_paths(tower_id), 'src/generate_tower_plans.py'],
                     [*drawing_paths, *svg_paths, pdf_path])
            check(prefix + 'drawing_revision', drawings.get('revision') == revision
                  and drawings.get('source_geometry_revision') == revision
                  and drawings.get('units') == 'mm' and drawings.get('status') == 'reference_concept_only')

            scene = read_scene(root / model_paths[0])
            native = {}
            native_bounds = {}
            native_volumes = {}
            low, high = [float('inf')] * 3, [float('-inf')] * 3
            for occurrence in scene.leaves():
                label, shape = occurrence.label, occurrence.shape()
                check(prefix + label + ':unique_name', label not in native)
                native[label] = shape
                solids = list(shape.solids())
                volumes=[solid.volume for solid in solids]
                native_volumes[label]=sum(volumes)
                check(prefix + label + ':valid_solid', bool(solids)
                      and all(solid.is_valid for solid in solids) and all(isfinite(v) and v>0 for v in volumes))
                bounds = shape.bounding_box()
                native_bounds[label] = [bounds.min.X,bounds.min.Y,bounds.min.Z,bounds.max.X,bounds.max.Y,bounds.max.Z]
                for axis, key in enumerate(('X', 'Y', 'Z')):
                    low[axis] = min(low[axis], getattr(bounds.min, key))
                    high[axis] = max(high[axis], getattr(bounds.max, key))
            check(prefix + 'named_component_count', len(native) == len(component_specs(tower_id)), len(native))
            for group in GROUPS:
                check(prefix + 'saved_group:' + group, any(group in name.split(':') for name in native))
            check(prefix + 'STEP_reference_height', close(high[2], parameters['height_mm']), high[2])
            check(prefix + 'STEP_base_depth', close(low[2], -parameters['base_slab_thickness_mm']), low[2])

            raw = (root / model_paths[1]).read_bytes()
            audit = audit_glb_bytes(raw)
            check(prefix + 'GLB_mesh_count', audit['mesh_count'] == len(native), audit['mesh_count'])
            check(prefix + 'GLB_height_metres', close(audit['bounds'][4], parameters['height_mm'] / 1000, .001), audit['bounds'])
            json_length = struct.unpack_from('<I', raw, 12)[0]
            document = json.loads(raw[20:20 + json_length])
            extras = document.get('asset', {}).get('extras', {})
            check(prefix + 'GLB_declared_units', extras.get('units') == 'metres' and extras.get('upAxis') == 'Y')
            check(prefix + 'GLB_revision', extras.get('revision') == revision)
            for primitive in audit['primitives']:
                name = primitive['mesh_name']
                shape = native.get(name)
                check(prefix + name + ':GLB_STEP_name', shape is not None)
                if shape is None:
                    continue
                bbox = shape.bounding_box()
                target = [bbox.min.X/1000, bbox.min.Z/1000, -bbox.max.Y/1000,
                          bbox.max.X/1000, bbox.max.Z/1000, -bbox.min.Y/1000]
                check(prefix + name + ':GLB_STEP_bounds', all(close(a, b, .03)
                      for a, b in zip(primitive['bounds'], target)))
            materials = document.get('materials', [])
            check(prefix + 'visible_materials', bool(materials))
            if revision in ('LANDMARK-R02','LANDMARK-R03','LANDMARK-R04','LANDMARK-R05','LANDMARK-R06','LANDMARK-R07','LANDMARK-R08','LANDMARK-R09','LANDMARK-R10','LANDMARK-R11'):
                specs = {part['name']: part for part in component_specs(tower_id)}
                saved_meshes = {mesh['name']: mesh for mesh in document['meshes']}
                saved_nodes = {node.get('name'): node for node in document['nodes'] if 'mesh' in node}
                panes, lenses, treads = 0, 0, 0
                for name, spec in specs.items():
                    role = spec.get('role')
                    if role is not None:
                        check(prefix + name + ':saved_role', saved_nodes.get(name, {}).get('extras', {}).get('landmarkRole') == role)
                    if tower_id=='tokyo-skytree' or revision in ('LANDMARK-R05','LANDMARK-R06','LANDMARK-R07','LANDMARK-R08','LANDMARK-R09','LANDMARK-R10','LANDMARK-R11'):
                        check(prefix+name+':saved_primitive',saved_nodes.get(name,{}).get('extras',{}).get('landmarkPrimitive')==spec['kind'])
                        expected_volume=None
                        if spec['kind']=='tube':
                            r=spec['radius'];t=spec['wall_thickness_mm']
                            expected_volume=pi*(r*r-(r-t)**2)*dist(spec['start'],spec['end'])
                        elif spec['kind']=='rhs':
                            w,h,t=spec['width_mm'],spec['depth_mm'],spec['wall_thickness_mm']
                            expected_volume=(w*h-(w-2*t)*(h-2*t))*dist(spec['start'],spec['end'])
                        elif spec['kind']=='tube_loft':
                            expected_volume=0.
                            for a,b in zip(spec['sections'],spec['sections'][1:]):
                                ro,so=a['radius'],b['radius'];ri,si=ro-a['wall_thickness_mm'],so-b['wall_thickness_mm']
                                expected_volume+=pi*(b['z']-a['z'])*(ro*ro+ro*so+so*so-ri*ri-ri*si-si*si)/3
                        if expected_volume is not None:
                            check(prefix+name+':saved_hollow_volume',abs(native_volumes[name]-expected_volume)<=max(1.,expected_volume*1e-6),native_volumes[name])
                    if role == 'stair_tread':
                        treads += 1
                        check(prefix + name + ':saved_flight', saved_nodes.get(name, {}).get('extras', {}).get('landmarkFlight') == spec['flight'])
                    if role not in ('glazing', 'light_lens', 'obstruction_light_lens'):
                        continue
                    for primitive in saved_meshes.get(name, {}).get('primitives', []):
                        material = materials[primitive['material']]
                        if role == 'glazing':
                            panes += 1
                            alpha = material.get('pbrMetallicRoughness', {}).get('baseColorFactor', [0,0,0,1])[3]
                            check(prefix + name + ':transparent_pane', material.get('alphaMode') == 'BLEND' and 0 < alpha < 1)
                        else:
                            lenses += 1
                            check(prefix + name + ':daylight_lens_unlit', material.get('emissiveFactor', [0,0,0]) == [0,0,0])
                expected_panes = sum(part.get('role') == 'glazing' for part in specs.values())
                expected_lenses = sum(part.get('role') in ('light_lens','obstruction_light_lens') for part in specs.values())
                check(prefix + 'split_glass_and_lenses', panes == expected_panes and panes >= 50
                      and lenses == expected_lenses and lenses >= 6,
                      {'panes':panes, 'lenses':lenses})
                if tower_id == 'tokyo-tower':
                    check(prefix + 'all_named_treads_retained', treads == 600, treads)
                    catalog=manifest.get('steel_nodes',[])
                    check(prefix+'twenty_steel_nodes',len(catalog)==20 and len({n['id'] for n in catalog})==20)
                    check(prefix+'GLB_steel_catalog',extras.get('steelNodes')==catalog)
                    for row in catalog:
                        parts=[specs.get(name) for name in row['part_names']]
                        check(prefix+row['id']+':registered_parts',bool(parts) and all(parts))
                        if all(name in native_bounds for name in row['part_names']):
                            node_bounds = [min(native_bounds[name][axis] for name in row['part_names']) for axis in range(3)] + [
                                max(native_bounds[name][axis+3] for name in row['part_names']) for axis in range(3)]
                            check(prefix+row['id']+':native_catalog_bounds',all(close(a,b,.1)
                                  for a,b in zip(node_bounds,row['bounds_mm'])),node_bounds)
                        for name in row['part_names']:
                            spec=specs.get(name,{})
                            saved=saved_nodes.get(name,{}).get('extras',{})
                            check(prefix+name+':steel_node',saved.get('steelNodeId')==row['id']
                                  and saved.get('steelDetailKind')==spec.get('steel_detail_kind')
                                  and saved.get('steelMicro')==(spec.get('detail_level')=='steel_micro'))
                else:
                    ramps = [part for part in specs.values() if part.get('role') == 'galleria_ramp']
                    check(prefix + 'sloping_named_gallery', len(ramps) >= 24
                          and all(part['kind'] == 'loft3d' for part in ramps), len(ramps))

            for view, dxf_path, svg_path in zip(('plan', 'elevation', 'steel-nodes' if tower_id=='tokyo-tower' else 'structure-zones'), drawing_paths, svg_paths):
                row = next((value for value in drawings.get('drawings', []) if value.get('id') == view), {})
                doc = ezdxf.readfile(root / dxf_path)
                check(prefix + view + ':DXF_audit', not doc.audit().errors)
                check(prefix + view + ':DXF_units_mm', doc.units == 4)
                msp = doc.modelspace()
                text_layouts = doc.layouts if view in ('steel-nodes','structure-zones') else [msp]
                texts = [entity.dxf.text for layout in text_layouts for entity in layout.query('TEXT')]
                check(prefix + view + ':editable_text', len(texts) >= 2)
                if view == 'steel-nodes':
                    check(prefix + view + ':editable_node_index', all(any(node['id'] in value for value in texts)
                          for node in manifest['steel_nodes']))
                measured = sorted(float(entity.get_measurement()) for entity in msp.query('DIMENSION'))
                declared = sorted(row.get('dimensions_mm', []))
                check(prefix + view + ':native_DIMENSION', bool(measured) and len(measured) == len(declared)
                      and all(close(a, b, .01) for a, b in zip(measured, declared)), measured)
                check(prefix + view + ':readable_layers', all(layer.color == 7 for layer in doc.layers if layer.dxf.name != 'Defpoints'))
                svg = ET.parse(root / svg_path).getroot()
                check(prefix + view + ':SVG_units_revision', svg.attrib.get('data-units') == 'mm'
                      and svg.attrib.get('data-revision') == revision)
                check(prefix + view + ':SVG_safe', not any(node.tag.split('}')[-1].lower() in
                      ('script', 'image', 'foreignobject') for node in svg.iter()))
                values = sorted(float(node.attrib['data-dimension-mm']) for node in svg.iter()
                                if 'data-dimension-mm' in node.attrib)
                check(prefix + view + ':SVG_DXF_dimensions', len(values) == len(declared)
                      and all(close(a,b,1e-6) for a,b in zip(values,declared)))
                if view == 'plan':
                    check(prefix + 'plan_reference_width', any(close(value, parameters['base_width_mm'], .01)
                          for value in measured), measured)
                if view == 'elevation':
                    check(prefix + 'official_height_dimensions', all(any(close(value, target, .01) for value in measured)
                          for target in [parameters['height_mm'], *parameters['deck_levels_mm']]))
            pdf = PdfReader(root / pdf_path)
            check(prefix + 'PDF_page_count', len(pdf.pages) == 3)
            for index, page in enumerate(pdf.pages):
                width, height = float(page.mediabox.width), float(page.mediabox.height)
                check(prefix + f'PDF_A3_{index}', close(width, 420*72/25.4, .1) and close(height, 297*72/25.4, .1))
        except Exception as error:
            check(prefix + 'read_saved_assets', False, f'{type(error).__name__}: {error}')
    return {'revision': 'LANDMARK-CATALOG',
            'revisions': {key: value.get('revision', REVISION) for key,value in TOWERS.items()},
            'pass': all(row['pass'] for row in checks),
            'scope': 'Source-bound reference geometry and drawing consistency; not survey or engineering validation.',
            'checks': checks}


def main():
    report = validate()
    destination = ROOT / 'output/review/validation_towers.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    failures = [row for row in report['checks'] if not row['pass']]
    print(json.dumps({'pass': report['pass'], 'checks': len(report['checks']),
                      'failures': failures, 'report': str(destination)}, ensure_ascii=False))
    return 0 if report['pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
