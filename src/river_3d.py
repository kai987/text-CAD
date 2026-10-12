"""Export the independent RIVER-R01 demonstration as named STEP and GLB.

Run from the repository root: CADGEN_DAEMON=0 .venv/bin/python src/river_3d.py
Importing this module never creates or overwrites an output file.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from math import cos, pi, sin
from pathlib import Path
from random import Random
import struct

import numpy as np
from cadgen import glb, read_scene, step

from lib.river_geometry import (R, REVISION, geometry_manifest, river_assembly,
                                tree_crown_lobes, tree_positions)
from lib.step_transport import compact_export

ROOT = Path(__file__).resolve().parents[1]
STATIC_PARTS = r"""
export const clips = {
  named_parts: {label: "Static named river assembly export", duration: 1,
                loop: false, update(t, m) {}}
};
"""
MATERIALS = {
    "definitions": {"water": {"name":"Demonstration river water", "roughness":.18, "opacity":.62}},
    "assignments": [{"targets":["#River:water"], "material":"water"}],
}


@step(out="../STEP/river_demo.step", materials=MATERIALS, animation=STATIC_PARTS)
def river_demo():
    return river_assembly()


def foliage_mesh(tree):
    """One deterministic, opaque leaf/flower mesh inside the CAD crown boxes.

    STEP stores planting volumes; GLB displays curved leaf surfaces and blossom
    sprays inside the same recorded crown boxes and planting radius. No
    external textures or per-leaf scene nodes are needed. Coordinates follow
    the existing world-space metre/Y-up export.
    """
    seed = int.from_bytes(hashlib.sha256(('foliage-v1:' + tree['id']).encode()).digest()[:8], 'little')
    rng = Random(seed)
    points, colors, triangles = [], [], []
    green = ((.32, .44, .24), (.43, .56, .29), (.54, .65, .36), (.25, .36, .19))
    pink = ((.96, .85, .87), (.91, .74, .79), (1, .93, .94), (.85, .60, .67))
    linear = lambda value: value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4

    def glyph(center, u, v, normal, local, faces, palette, flower=False):
        offset = len(points)
        base = tuple(linear(value) for value in palette)
        for index, (x, y, z) in enumerate(local):
            points.append(center + u * x + v * y + normal * z)
            tint = .91 + .09 * index / max(1, len(local) - 1)
            colors.append((.37, .23, .10) if flower and index == 0
                          else tuple(value * tint for value in base))
        triangles.extend(tuple(offset + index for index in face) for face in faces)

    for lobe in tree_crown_lobes(tree):
        start = len(points)
        centre, radii = np.asarray(lobe['centre']), np.asarray(lobe['radii'])
        count = 200 if tree['kind'] == 'green' else 145
        for index in range(count):
            direction = np.asarray([rng.gauss(0, 1) for _ in range(3)])
            direction /= np.linalg.norm(direction)
            radial = rng.uniform(.38, .94)
            anchor = centre + direction * radii * radial
            normal = direction + np.asarray([rng.uniform(-.8, .8) for _ in range(3)])
            normal /= np.linalg.norm(normal)
            reference = np.array((1., 0., 0.)) if abs(normal[2]) > .9 else np.array((0., 0., 1.))
            u = np.cross(normal, reference); u /= np.linalg.norm(u)
            v = np.cross(normal, u)
            if tree['kind'] == 'sakura' and index < 95:
                radius = rng.uniform(92, 142)
                turn = rng.uniform(0, 2 * pi)
                for petal in range(5):
                    angle = turn + petal * 2 * pi / 5
                    pu, pv = u * cos(angle) + v * sin(angle), -u * sin(angle) + v * cos(angle)
                    local = [(0, 0, 0), (-.27 * radius, .49 * radius, .08 * radius),
                             (-.10 * radius, radius, .14 * radius),
                             (.10 * radius, radius, .14 * radius),
                             (.27 * radius, .49 * radius, .08 * radius)]
                    glyph(anchor, pu, pv, normal, local, [(0, 1, 2), (0, 2, 3), (0, 3, 4)],
                          rng.choice(pink), flower=True)
            else:
                length = rng.uniform(205, 335)
                local = [(0, 0, 0), (-.26 * length, .22 * length, .02 * length),
                         (-.22 * length, .65 * length, .06 * length), (0, length, 0),
                         (.22 * length, .65 * length, .06 * length),
                         (.26 * length, .22 * length, .02 * length), (0, .45 * length, .11 * length)]
                glyph(anchor, u, v, normal, local,
                      [(6, 0, 1), (6, 1, 2), (6, 2, 3), (6, 3, 4), (6, 4, 5), (6, 5, 0)],
                      rng.choice(green))
        # The recorded CAD lobe AABB is also the presentation envelope. Fitting
        # the finite leaf vertices keeps native/download bounds consistent and
        # all horizontal box corners inside the original planting radius.
        values = np.asarray(points[start:])
        minimum, maximum = values.min(axis=0), values.max(axis=0)
        values = (values - minimum) / (maximum - minimum) * (2 * radii) + centre - radii
        points[start:] = list(values)
    cad = np.asarray(points)
    positions = np.column_stack((cad[:, 0], cad[:, 2], -cad[:, 1])) / 1000
    indices = np.asarray(triangles, dtype=np.uint32)
    face_normals = np.cross(positions[indices[:, 1]] - positions[indices[:, 0]],
                            positions[indices[:, 2]] - positions[indices[:, 0]])
    normals = np.zeros_like(positions)
    for column in range(3):
        np.add.at(normals, indices[:, column], face_normals)
    lengths = np.linalg.norm(normals, axis=1)
    if not np.all(lengths > 0):
        raise ValueError('Tree foliage contains an unused or degenerate vertex.')
    normals /= lengths[:, None]
    return {'positions': positions.astype('<f4'), 'normals': normals.astype('<f4'),
            'colors': np.asarray(colors, dtype='<f4'),
            'indices': indices.astype('<u2' if len(points) <= 65535 else '<u4').ravel()}


def compact_static_buffers(document, binary):
    """Remove superseded crown payloads, retaining every active byte unchanged."""
    if len(document['buffers']) != 1 or document.get('animations') or document.get('skins'):
        raise ValueError('River foliage packing requires the static single-buffer export.')
    used = set()
    for mesh in document['meshes']:
        for primitive in mesh['primitives']:
            used.update(primitive['attributes'].values())
            if 'indices' in primitive:
                used.add(primitive['indices'])
            for target in primitive.get('targets', []):
                used.update(target.values())
    accessors = document['accessors']
    if any(accessors[index].get('sparse') for index in used):
        raise ValueError('Sparse accessors are outside the river packing profile.')
    views = {accessors[index]['bufferView'] for index in used}
    views.update(image['bufferView'] for image in document.get('images', []) if 'bufferView' in image)
    packed, new_views, view_map = bytearray(), [], {}
    for old in sorted(views):
        record = deepcopy(document['bufferViews'][old])
        if record.get('buffer', 0) != 0:
            raise ValueError('External river buffers are unsupported.')
        offset, length = record.get('byteOffset', 0), record['byteLength']
        if offset + length > len(binary):
            raise ValueError('River buffer view exceeds its BIN payload.')
        packed.extend(b'\0' * (-len(packed) % 4))
        record['byteOffset'] = len(packed)
        packed.extend(binary[offset:offset + length])
        view_map[old] = len(new_views); new_views.append(record)
    accessor_map, new_accessors = {}, []
    for old in sorted(used):
        record = deepcopy(accessors[old]); record['bufferView'] = view_map[record['bufferView']]
        accessor_map[old] = len(new_accessors); new_accessors.append(record)
    for mesh in document['meshes']:
        for primitive in mesh['primitives']:
            primitive['attributes'] = {key: accessor_map[value] for key, value in primitive['attributes'].items()}
            if 'indices' in primitive:
                primitive['indices'] = accessor_map[primitive['indices']]
            for target in primitive.get('targets', []):
                for key, value in target.items():
                    target[key] = accessor_map[value]
    for image in document.get('images', []):
        if 'bufferView' in image:
            image['bufferView'] = view_map[image['bufferView']]
    document['bufferViews'], document['accessors'] = new_views, new_accessors
    document['buffers'][0]['byteLength'] = len(packed)
    return bytes(packed)


def apply_tree_foliage(document, binary):
    """Replace only crown presentation meshes; named CAD occurrences stay intact."""
    output = bytearray(binary)
    by_name = {f"Landscape:trees:{tree['id']}:crown": tree for tree in tree_positions()}
    mesh_users = {}
    targets = []
    for node in document['nodes']:
        if 'mesh' in node:
            mesh_users[node['mesh']] = mesh_users.get(node['mesh'], 0) + 1
            if node.get('name') in by_name:
                targets.append(node)
    if len(targets) != len(by_name) or {node['name'] for node in targets} != set(by_name):
        raise ValueError('River foliage requires every original named tree crown exactly once.')
    if any(mesh_users[node['mesh']] != 1 for node in targets):
        raise ValueError('River crown meshes must not be shared with other occurrences.')
    changed, totals = set(), {'crowns': 0, 'vertices': 0, 'triangles': 0}

    def attribute(values, kind, component, target):
        output.extend(b'\0' * (-len(output) % 4))
        view = len(document['bufferViews'])
        raw = values.tobytes()
        document['bufferViews'].append({'buffer': 0, 'byteOffset': len(output), 'byteLength': len(raw), 'target': target})
        output.extend(raw)
        record = {'bufferView': view, 'componentType': component, 'count': len(values), 'type': kind}
        if kind == 'VEC3':
            record.update(min=values.min(axis=0).tolist(), max=values.max(axis=0).tolist())
        index = len(document['accessors']); document['accessors'].append(record)
        return index

    for node in document['nodes']:
        name = node.get('name')
        if 'mesh' not in node or name not in by_name:
            continue
        if name in changed:
            raise ValueError('River contains a duplicate crown occurrence.')
        changed.add(name)
        generated = foliage_mesh(by_name[name])
        mesh = document['meshes'][node['mesh']]
        material = deepcopy(document['materials'][mesh['primitives'][0]['material']])
        material['name'] = name + ':foliage'; material['doubleSided'] = True; material['alphaMode'] = 'OPAQUE'
        material['pbrMetallicRoughness'] = {'baseColorFactor': [1, 1, 1, 1], 'roughnessFactor': .84, 'metallicFactor': 0}
        material_index = len(document['materials']); document['materials'].append(material)
        primitive = {'attributes': {key: attribute(generated[value], 'VEC3', 5126, 34962)
                                    for key, value in [('POSITION', 'positions'), ('NORMAL', 'normals'), ('COLOR_0', 'colors')]},
                     'indices': attribute(generated['indices'], 'SCALAR',
                                          5123 if generated['indices'].dtype.itemsize == 2 else 5125, 34963),
                     'material': material_index, 'mode': 4}
        mesh['primitives'] = [primitive]
        mesh['extras'] = {**mesh.get('extras', {}), 'vegetationStyle': 'natural_trees_v1',
                          'nativeRepresentation': 'planting crown envelope',
                          'displayRepresentation': 'curved leaf surfaces and blossom sprays'}
        totals['crowns'] += 1; totals['vertices'] += len(generated['positions'])
        totals['triangles'] += len(generated['indices']) // 3
    if changed != set(by_name):
        raise ValueError('River foliage requires every original named tree crown.')
    document['asset'].setdefault('extras', {})['vegetation'] = totals
    return compact_static_buffers(document, output), totals


def restore_hierarchy(step_path, glb_path):
    """Retain CADgen's world-coordinate meshes and restore named STEP groups."""
    raw = glb_path.read_bytes()
    magic, version, total = struct.unpack_from("<4sII",raw)
    if (magic,version,total)!=(b"glTF",2,len(raw)):
        raise ValueError("River export must be a GLB 2.0 container")
    size,kind=struct.unpack_from("<II",raw,12)
    if kind!=0x4E4F534A:
        raise ValueError("GLB first chunk must be JSON")
    doc=json.loads(raw[20:20+size])
    nodes=doc["nodes"]
    indexed={}
    for i,node in enumerate(nodes):
        occurrence=node.get("extras",{}).get("cadOccurrenceId")
        if not occurrence or occurrence in indexed:
            raise ValueError("Named GLB needs one unique occurrence per STEP leaf")
        indexed[occurrence]=i
    scene=read_scene(step_path)

    def insert(occurrence):
        occurrence_id=occurrence.ref.removeprefix("#")
        if not occurrence.children:
            index=indexed[occurrence_id]
            node=nodes[index]
            node["name"]=occurrence.label
            mesh=doc["meshes"][node["mesh"]]
            mesh["name"]=occurrence.label
            for primitive in mesh["primitives"]:
                source=doc["materials"][primitive["material"]]
                material=deepcopy(source)
                material["name"]=occurrence.label+":finish"
                pbr=material.setdefault("pbrMetallicRoughness",{})
                pbr["roughnessFactor"]=.82
                pbr["metallicFactor"]=.08 if occurrence.label.startswith("Bridge:rails") else 0
                if occurrence.label.startswith("River:water"):
                    pbr["roughnessFactor"]=.18
                    pbr.setdefault("baseColorFactor",[.25,.62,.72,1])[3]=.62
                    material["alphaMode"]="BLEND"
                    material["doubleSided"]=True
                if occurrence.label.startswith("Lighting:fixtures") and occurrence.label.endswith(":lens"):
                    material["emissiveFactor"]=[.28,.22,.11]
                primitive["material"]=len(doc["materials"])
                doc["materials"].append(material)
            return index
        child_indices=[insert(child) for child in occurrence.children]
        index=len(nodes)
        nodes.append({"name":occurrence.label,"children":child_indices,
                      "extras":{"cadOccurrenceId":occurrence_id,"cadUnits":"m","cadUpAxis":"y"}})
        return index

    doc["scenes"]=[{"name":"river_demo","nodes":[insert(root) for root in scene.roots]}]
    doc["scene"]=0
    doc["asset"]["extras"]={"units":"metres","upAxis":"Y","revision":REVISION,
                               "source":"Independent named CADgen STEP; invented suburban river demonstration, no hydraulic or structural calculation"}
    bin_offset = 20 + size
    bin_size, bin_kind = struct.unpack_from('<II', raw, bin_offset)
    if bin_kind != 0x004E4942:
        raise ValueError('River export must contain a BIN chunk.')
    binary, foliage = apply_tree_foliage(doc, raw[bin_offset + 8:bin_offset + 8 + bin_size])
    encoded=json.dumps(doc,ensure_ascii=False,separators=(",",":")).encode()
    encoded+=b" "*((-len(encoded))%4)
    binary += b'\0' * (-len(binary) % 4)
    remaining=struct.pack('<II',len(binary),bin_kind)+binary
    body=struct.pack("<II",len(encoded),kind)+encoded+remaining
    destination=glb_path.with_suffix(".glb.tmp")
    destination.write_bytes(struct.pack("<4sII",b"glTF",2,len(body)+12)+body)
    destination.replace(glb_path)
    return {"named_mesh_nodes":len(indexed),"all_nodes":len(nodes),"vegetation":foliage,
            "mesh_coordinates":"world-space metres, Y-up", "mapping_from_CAD":"(X,Z,-Y)/1000"}


def _fingerprint(path):
    raw=path.read_bytes()
    return {"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}


def generate(root=ROOT):
    root=Path(root)
    if root.resolve()!=ROOT.resolve():
        raise ValueError("CADgen's source-relative output decorator requires this repository root")
    for directory in ("STEP","GLB","output/review"):
        (root/directory).mkdir(parents=True,exist_ok=True)
    river_demo()
    step_path=root/"STEP/river_demo.step"
    glb_path=root/"GLB/river_demo.glb"
    glb.build(step_path,glb_path,animation={"clip":"named_parts","fps":1,"seconds":1},force=True)
    exported=restore_hierarchy(step_path,glb_path)
    compact_export(step_path)
    # Read the exact generated STEP for bounds/group counts: no second geometry build.
    from cadgen import build123d as bd
    assembly=bd.import_step(step_path)
    manifest=geometry_manifest(R,assembly)
    manifest["glb_export"]=exported
    manifest["source_sha256"]={name:hashlib.sha256((root/name).read_bytes()).hexdigest()
                                for name in ("src/lib/river_geometry.py","src/river_3d.py")}
    manifest["artifacts"]={name:_fingerprint(root/name)
                             for name in ("STEP/river_demo.step","GLB/river_demo.glb")}
    destination=root/"output/review/river_demo_manifest.json"
    destination.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"revision":REVISION,"manifest":str(destination),"artifacts":manifest["artifacts"],
                      "groups":manifest["groups"],"glb_export":exported},ensure_ascii=False))
    return manifest


if __name__=="__main__":
    generate()
