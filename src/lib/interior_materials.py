"""PBR finishes for original interior parts; geometry and CAD labels are unchanged."""
from copy import deepcopy


def apply_interior_materials(document):
    """Assign by semantic leaf name and keep a separate finish per original colour."""
    variants = {}
    for node in document['nodes']:
        name = node.get('name', '').lower()
        if 'mesh' not in node or not (':furniture:' in name or ':fixture_' in name):
            continue
        if any(word in name for word in ('chrome', 'metal', 'steel', 'drain', 'tap', 'faucet')):
            finish, roughness, metalness = 'brushed metal', .23, .78
        elif 'mirror' in name:
            finish, roughness, metalness = 'mirror finish', .08, .85
        elif any(word in name for word in ('screen', 'glass', 'hob', 'display')):
            finish, roughness, metalness = 'dark glass', .16, .22
        elif any(word in name for word in ('ceramic', 'basin', 'tub', 'toilet')):
            finish, roughness, metalness = 'glazed ceramic', .22, 0
        elif any(word in name for word in ('pillow', 'blanket', 'duvet', 'mattress', 'cushion', 'upholstery')) or ('sofa' in name and 'leg_' not in name):
            finish, roughness, metalness = 'woven fabric', .93, 0
        elif any(word in name for word in ('wood', 'frame', 'table', 'console', 'cabinet')):
            finish, roughness, metalness = 'satin wood', .56, 0
        else:
            finish, roughness, metalness = 'satin finish', .48, 0
        for primitive in document['meshes'][node['mesh']]['primitives']:
            original = primitive.get('material')
            if original is None:
                continue
            key = (original, finish)
            if key not in variants:
                material = deepcopy(document['materials'][original])
                material['name'] = f'{material.get("name", "interior")} / {finish}'
                pbr = material.setdefault('pbrMetallicRoughness', {})
                pbr.update(roughnessFactor=roughness, metallicFactor=metalness)
                variants[key] = len(document['materials'])
                document['materials'].append(material)
            primitive['material'] = variants[key]
