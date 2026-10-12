"""Independently read saved river CAD/3D and reject mismatched sources/drawings.

No assets are generated or provenance blessed here. This bounded geometry check
does not calculate flood capacity, bridge strength, foundations or code approval.
Run: .venv/bin/python checks/validate_river.py
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from math import isfinite
import os
from pathlib import Path
import struct
import sys
import xml.etree.ElementTree as ET

import ezdxf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
# The saved-shape audit is intentionally local. An old CADgen daemon can hold
# the input request indefinitely, while the pipeline also disables it globally.
os.environ.setdefault('CADGEN_DAEMON', '0')
from cadgen import read_scene
from lib.native_glb import audit_glb_bytes
from lib.river_geometry import (R, REVISION, GROUPS, geometry_manifest, bridge_dimensions,
                                section_offsets, tree_positions)


CENTRELINE_TOLERANCE_MM = 1e-8


def centreline_samples_match(actual, expected):
    """Allow libm rounding across platforms while preserving the sampled path.

    The absolute tolerance is in CAD millimetres, far below the saved-solid
    tolerance. Sample count, point shape and finite numeric coordinates remain
    mandatory; source bindings and all other manifest fields stay exact.
    """
    if not isinstance(actual, list) or len(actual) != len(expected):
        return False
    for saved, current in zip(actual, expected):
        if not isinstance(saved, list) or len(saved) != 2:
            return False
        for coordinate, reference in zip(saved, current):
            if (type(coordinate) not in (int, float) or not isfinite(coordinate)
                    or abs(coordinate - reference) > CENTRELINE_TOLERANCE_MM):
                return False
    return True


def validate(root=ROOT):
    results = []

    def check(name, condition, actual=None):
        results.append({'check': name, 'pass': bool(condition), 'actual': actual})

    def close(name, actual, expected, tolerance=1e-3):
        check(name, isfinite(actual) and abs(actual - expected) <= tolerance,
              {'actual': actual, 'expected': expected, 'tolerance': tolerance})

    def digest(path):
        return hashlib.sha256((root / path).read_bytes()).hexdigest()

    def bindings(metadata, sources, artifacts):
        saved_sources = metadata.get('source_sha256', {})
        check('provenance:exact_sources', set(saved_sources) == set(sources), list(saved_sources))
        for path in sources:
            check(f'provenance:source:{path}', saved_sources.get(path) == digest(path))
        saved_artifacts = metadata.get('artifacts', {})
        check('provenance:exact_artifacts', set(saved_artifacts) == set(artifacts), list(saved_artifacts))
        for path in artifacts:
            data = (root / path).read_bytes()
            expected = saved_artifacts.get(path, {})
            check(f'provenance:artifact:{path}', set(expected) == {'sha256', 'bytes'}
                  and expected.get('sha256') == hashlib.sha256(data).hexdigest()
                  and expected.get('bytes') == len(data))

    manifest = json.loads((root / 'output/review/river_demo_manifest.json').read_text())
    canonical = geometry_manifest()
    check('manifest:schema', manifest.get('schema_version') == 1)
    check('manifest:concept_only', manifest.get('status') == 'concept_demo_only')
    for key, expected in canonical.items():
        if key == 'centreline_samples':
            check(f'manifest:{key}:current_parameters',
                  centreline_samples_match(manifest.get(key), expected),
                  {'tolerance_mm': CENTRELINE_TOLERANCE_MM})
        else:
            check(f'manifest:{key}:current_parameters', manifest.get(key) == expected)
    check('manifest:demonstration_dimensions', manifest.get('parameters') == asdict(R))
    bindings(manifest, ['src/lib/river_geometry.py', 'src/river_3d.py'],
             ['STEP/river_demo.step', 'GLB/river_demo.glb'])

    scene = read_scene(root / 'STEP/river_demo.step')
    native = {}
    min_bound, max_bound = [float('inf')] * 3, [float('-inf')] * 3
    for occurrence in scene.leaves():
        label, shape = occurrence.label, occurrence.shape()
        check(f'STEP:{label}:unique_label', label not in native)
        native[label] = shape
        solids = list(shape.solids())
        check(f'STEP:{label}:positive_valid_solids', bool(solids)
              and all(solid.is_valid and isfinite(solid.volume) and solid.volume > 0 for solid in solids))
        bounds = shape.bounding_box()
        for axis, key in enumerate(('X', 'Y', 'Z')):
            min_bound[axis] = min(min_bound[axis], getattr(bounds.min, key))
            max_bound[axis] = max(max_bound[axis], getattr(bounds.max, key))
    check('STEP:nonempty_named_model', len(native) >= len(GROUPS), len(native))
    check('STEP:all_semantic_groups_have_geometry',
          all(any(name.startswith(group + ':') for name in native) for group in GROUPS))
    check('STEP:scene_name', any(root_occurrence.label == 'river_demo' for root_occurrence in scene.roots))
    for name, expected in [('min', min_bound), ('max', max_bound)]:
        values = manifest.get('bbox', {}).get(name, [])
        check(f'manifest:STEP_bbox_{name}_length', len(values) == 3)
        for axis, (actual, expected_value) in enumerate(zip(values, expected)):
            close(f'manifest:STEP_bbox_{name}_{axis}', actual, expected_value)
    for axis, expected in enumerate((R.width, R.length)):
        close(f'STEP:envelope_axis_{axis}', max_bound[axis] - min_bound[axis], expected)
    close('STEP:terrain_bottom', min_bound[2], R.base_bottom_z)
    bridge = bridge_dimensions()
    deck = native.get('Bridge:deck:slab')
    check('STEP:bridge_deck_named', deck is not None)
    if deck is not None:
        bbox = deck.bounding_box()
        close('STEP:bridge_span', bbox.max.X - bbox.min.X, bridge['span'])
        close('STEP:bridge_width', bbox.max.Y - bbox.min.Y, R.bridge_width)
        close('STEP:bridge_top_elevation', bbox.max.Z, R.bridge_top_z)
    water = native.get('River:water:surface_volume')
    check('STEP:water_named', water is not None)
    if water is not None:
        bbox = water.bounding_box()
        close('STEP:water_top_elevation', bbox.max.Z, R.water_z)
        close('STEP:water_bottom_elevation', bbox.min.Z, R.bed_z)
        offsets = section_offsets()
        expected_volume = (R.water_width + 2 * offsets['bed_inner']) / 2 * (R.water_z - R.bed_z) * R.length
        close('STEP:water_trapezoidal_volume', water.volume, expected_volume, max(.01, expected_volume * 1e-8))

    data = (root / 'GLB/river_demo.glb').read_bytes()
    audit = audit_glb_bytes(data)
    size, kind = struct.unpack_from('<II', data, 12)
    check('GLB:first_chunk_JSON', kind == 0x4E4F534A)
    document = json.loads(data[20:20 + size])
    nodes = document['nodes']
    mesh_nodes = [node for node in nodes if 'mesh' in node]
    check('GLB:exact_STEP_leaf_labels', len(mesh_nodes) == len(native)
          and {node.get('name') for node in mesh_nodes} == set(native), len(mesh_nodes))
    check('GLB:semantic_groups', set(GROUPS) <= {node.get('name') for node in nodes})
    check('GLB:metres_Y_up_metadata', all(node.get('extras', {}).get('cadUnits') == 'm'
          and node.get('extras', {}).get('cadUpAxis') == 'y' for node in nodes))
    identity = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
    check('GLB:identity_world_mesh_transforms', all(
        node.get('translation', [0, 0, 0]) == [0, 0, 0]
        and node.get('rotation', [0, 0, 0, 1]) == [0, 0, 0, 1]
        and node.get('scale', [1, 1, 1]) == [1, 1, 1]
        and node.get('matrix', identity) == identity for node in nodes))
    check('GLB:static_river_scene', not document.get('animations')
          and document.get('scenes', [{}])[0].get('name') == 'river_demo')
    vegetation = document.get('asset', {}).get('extras', {}).get('vegetation', {})
    check('GLB:natural_tree_crown_count', vegetation.get('crowns') == len(tree_positions()))
    for tree in tree_positions():
        prefix = f"Landscape:trees:{tree['id']}"
        check(f'STEP:{prefix}:named_tapered_tree', all(prefix + ':' + part in native
              for part in ('trunk', 'branches', 'crown')))
        crowns = [node for node in mesh_nodes if node.get('name') == prefix + ':crown']
        check(f'GLB:{prefix}:one_crown_mesh', len(crowns) == 1)
        for node in crowns:
            mesh = document['meshes'][node['mesh']]
            check(f'GLB:{prefix}:foliage_representation',
                  mesh.get('extras', {}).get('vegetationStyle') == 'natural_trees_v1')
            for primitive in mesh['primitives']:
                attributes = primitive['attributes']
                position = document['accessors'][attributes['POSITION']]
                color = document['accessors'][attributes['COLOR_0']] if 'COLOR_0' in attributes else {}
                check(f'GLB:{prefix}:finite_leaf_color_layout', color.get('type') == 'VEC3'
                      and color.get('componentType') == 5126 and color.get('count') == position['count'])
                material = document['materials'][primitive['material']]
                check(f'GLB:{prefix}:opaque_double_sided_leaves', material.get('doubleSided') is True
                      and material.get('alphaMode', 'OPAQUE') == 'OPAQUE')
                check(f'GLB:{prefix}:detailed_single_batch', len(mesh['primitives']) == 1
                      and position['count'] > 4000)
    water_nodes = [node for node in mesh_nodes if node.get('name') == 'River:water:surface_volume']
    check('GLB:one_named_water_mesh', len(water_nodes) == 1)
    water_materials = [document['materials'][primitive['material']] for node in water_nodes
                       for primitive in document['meshes'][node['mesh']]['primitives']]
    check('GLB:transparent_water_material', bool(water_materials) and all(
        material.get('alphaMode') == 'BLEND'
        and 0 < material.get('pbrMetallicRoughness', {}).get('baseColorFactor', [1, 1, 1, 1])[3] < 1
        for material in water_materials))
    expected = [min_bound[0]/1000, min_bound[2]/1000, -max_bound[1]/1000,
                max_bound[0]/1000, max_bound[2]/1000, -min_bound[1]/1000]
    for axis, (actual, target) in enumerate(zip(audit['bounds'], expected)):
        # A small tessellation tolerance covers the curved tree crowns only;
        # unit conversion, handedness and full reach extent are checked here.
        close(f'GLB:CAD_mm_to_m_Y_up_bound_{axis}', actual, target, .025)
    check('GLB:decoded_triangle_geometry', audit['triangle_count'] > 0,
          {key: audit[key] for key in ('vertex_count', 'triangle_count', 'degenerate_count')})
    mesh_bounds = {}
    for primitive in audit['primitives']:
        name, bounds = primitive['mesh_name'], primitive['bounds']
        previous = mesh_bounds.get(name, bounds)
        mesh_bounds[name] = [min(previous[i], bounds[i]) for i in range(3)] + [
            max(previous[i], bounds[i]) for i in range(3, 6)]
    for name, bounds in mesh_bounds.items():
        shape = native.get(name)
        check(f'GLB:{name}:STEP_correspondence', shape is not None)
        if shape is None:
            continue
        bb = shape.bounding_box()
        transformed = [bb.min.X/1000, bb.min.Z/1000, -bb.max.Y/1000,
                       bb.max.X/1000, bb.max.Z/1000, -bb.min.Y/1000]
        check(f'GLB:{name}:saved_STEP_bounds_converted', all(
            abs(actual-target) <= .025 for actual, target in zip(bounds, transformed)),
            {'actual': bounds, 'expected': transformed, 'tessellation_tolerance_m': .025})

    metadata = json.loads((root / 'output/review/river_demo_drawings.json').read_text())
    check('drawings:schema_concept_units_revision', metadata.get('schema_version') == 1
          and metadata.get('status') == 'concept_demo_only' and metadata.get('units') == 'mm'
          and metadata.get('revision') == REVISION and metadata.get('source_geometry_revision') == REVISION)
    paths = ['DXF/river_demo_plan.dxf', 'DXF/river_demo_section.dxf',
             'output/svg/river_demo_plan.svg', 'output/svg/river_demo_section.svg']
    bindings(metadata, ['src/lib/river_geometry.py', 'src/generate_river_plans.py'], paths)
    expected_dimensions = {
        'plan': [R.length, R.width, R.water_width, bridge['span'], R.bridge_width, R.path_width],
        'section': [R.width, R.water_width, bridge['span'], R.crest_z-R.water_z, R.water_z-R.bed_z],
    }
    rows = metadata.get('drawings', [])
    check('drawings:exact_two_views', len(rows) == 2 and {row.get('id') for row in rows} == {'plan', 'section'})
    for row in rows:
        id = row['id']
        dimensions = expected_dimensions[id]
        check(f'{id}:metadata_canonical_dimensions', row.get('dimensions_mm') == dimensions)
        check(f'{id}:metadata_paths', row.get('dxf') == f'DXF/river_demo_{id}.dxf'
              and row.get('svg') == f'output/svg/river_demo_{id}.svg')
        labels = row.get('required_labels', [])
        check(f'{id}:nonempty_required_labels', len(labels) >= 4
              and all(isinstance(label, str) and label.strip() for label in labels))
        doc = ezdxf.readfile(root / row['dxf'])
        check(f'{id}:DXF_millimetres', doc.units == 4 and doc.header.get('$MEASUREMENT') == 1)
        check(f'{id}:DXF_clean_audit', not doc.audit().has_errors)
        msp = doc.modelspace()
        native_dimensions = list(msp.query('DIMENSION'))
        check(f'{id}:DXF_editable_dimension_count', len(native_dimensions) == len(dimensions), len(native_dimensions))
        actual_dimensions = sorted(float(dimension.get_measurement()) for dimension in native_dimensions)
        check(f'{id}:DXF_canonical_geometric_dimensions', len(actual_dimensions) == len(dimensions)
              and all(abs(a-b) <= .01 for a, b in zip(actual_dimensions, sorted(dimensions))), actual_dimensions)
        check(f'{id}:DXF_dimension_text_no_override', all(dimension.dxf.text in ('', '<>') for dimension in native_dimensions))
        # The plotted title/assumption notes are editable paper-space TEXT;
        # feature labels and all true-size dimensions remain in model space.
        texts = [entity for layout in doc.layouts for entity in layout.query('TEXT')]
        native_text = '\n'.join(entity.dxf.text for entity in texts)
        check(f'{id}:DXF_editable_labels', bool(texts)
              and all(label in native_text for label in labels))
        check(f'{id}:DXF_adaptive_contrast_positive_text', all(entity.dxf.color in (7, 256)
              and entity.dxf.height > 0 for entity in texts))
        check(f'{id}:DXF_A3_layout', any('A3' in name for name in doc.layouts.names()))
        svg = ET.fromstring((root / row['svg']).read_bytes())
        check(f'{id}:SVG_units_revision', svg.attrib.get('data-units') == 'mm'
              and svg.attrib.get('data-revision') == REVISION)
        svg_dimensions = [float(element.attrib['data-dimension-mm']) for element in svg.iter()
                          if 'data-dimension-mm' in element.attrib]
        check(f'{id}:SVG_dimensions_match_native', sorted(svg_dimensions) == sorted(dimensions), svg_dimensions)
        visible_dimensions = []
        for element in svg.iter():
            if 'data-dimension-mm' not in element.attrib:
                continue
            text = ''.join(element.itertext()).strip().removesuffix('mm').strip().replace(',', '')
            try:
                visible = float(text)
            except ValueError:
                visible = float('nan')
            visible_dimensions.append(element.tag.split('}')[-1] == 'text'
                                      and visible == float(element.attrib['data-dimension-mm']))
        check(f'{id}:SVG_visible_dimension_numbers', bool(visible_dimensions) and all(visible_dimensions))
        svg_text = '\n'.join(svg.itertext())
        check(f'{id}:SVG_required_labels', all(label in svg_text for label in labels))
        check(f'{id}:SVG_safe_vector_profile', all(element.tag.split('}')[-1] not in
              ('script', 'image', 'foreignObject') for element in svg.iter()))
    summary = {'checks': len(results), 'passed': sum(row['pass'] for row in results),
               'failed': sum(not row['pass'] for row in results), 'revision': REVISION,
               'STEP_leaf_occurrences': len(native), 'GLB_meshes': len(mesh_nodes),
               'vegetation': vegetation,
               'scope': 'Saved concept geometry and source-bound editable drawings; engineering uncalculated.'}
    return {'summary': summary, 'checks': results}


def main():
    report = validate()
    (ROOT / 'output/review/river_demo_validation.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report['summary'], ensure_ascii=False))
    for row in report['checks']:
        if not row['pass']:
            print(json.dumps(row, ensure_ascii=False))
    raise SystemExit(0 if report['summary']['failed'] == 0 else 1)


if __name__ == '__main__':
    main()
