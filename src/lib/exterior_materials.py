"""Original, embedded exterior finishes; no remote or manufacturer textures.

UVs use world-space metre coordinates already emitted by CADgen. Texture tiles
have explicit physical repeat sizes, so scale is stable in other GLB viewers.
The STEP retains the named solids and their source colours.
"""
from copy import deepcopy
from io import BytesIO
from math import sin, pi
import struct

from PIL import Image


def _texture_png(kind):
    size = 256
    image = Image.new("RGB", (size, size))
    pixels = []
    for y in range(size):
        for x in range(size):
            # Deterministic, tileable grain. Neutral tones tint the source CAD
            # colour, rather than replacing it with a downloaded photograph.
            if kind == "siding":
                grain = 2*sin(2*pi*x/16)*sin(2*pi*y/8)
                relief = 2.5*sin(2*pi*y/16)
                shade = 246 + grain + relief
                if y < 2:
                    shade = 204  # 3.6 mm horizontal board joint / 455 mm tile.
            else:
                grain = 4*sin(2*pi*x/32 + .65*sin(2*pi*y/256))
                shade = 239 + grain + 2*sin(2*pi*x/8)
                if x < 2:
                    shade = 205  # narrow vertical timber-board joint.
            value = max(0, min(255, round(shade)))
            pixels.append((value, value, value))
    image.putdata(pixels)
    stream = BytesIO()
    image.save(stream, format="PNG", optimize=True)
    return stream.getvalue()


def apply_exterior_materials(document, binary):
    """Return BIN bytes with aligned UV and PNG buffer views appended.

    Existing geometry, accessors and CAD occurrence IDs are kept. Every texture
    is embedded in the GLB, and every textured primitive gets its own UV data.
    """
    output = bytearray(binary)
    variants, textures = {}, {}

    def append_view(data, target=None):
        output.extend(b"\0"*((-len(output)) % 4))
        index = len(document["bufferViews"])
        view = {"buffer": 0, "byteOffset": len(output), "byteLength": len(data)}
        if target is not None:
            view["target"] = target
        document["bufferViews"].append(view)
        output.extend(data)
        return index

    def texture(kind):
        if kind not in textures:
            sampler = len(document.setdefault("samplers", []))
            document["samplers"].append({"magFilter": 9729, "minFilter": 9987,
                                         "wrapS": 10497, "wrapT": 10497})
            image = len(document.setdefault("images", []))
            document["images"].append({"name": f"Original procedural {kind}",
                "mimeType": "image/png", "bufferView": append_view(_texture_png(kind))})
            index = len(document.setdefault("textures", []))
            document["textures"].append({"sampler": sampler, "source": image})
            textures[kind] = index
        return textures[kind]

    def add_uv(primitive, name, kind):
        accessor = document["accessors"][primitive["attributes"]["POSITION"]]
        view = document["bufferViews"][accessor["bufferView"]]
        if accessor["componentType"] != 5126 or accessor["type"] != "VEC3":
            raise ValueError("Expected CADgen float32 world-space positions")
        offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        stride = view.get("byteStride", 12)
        side = name.rsplit(":", 1)[-1]
        width, height = (1.82, .455) if kind == "siding" else (.15, 2.8)
        coords = []
        for i in range(accessor["count"]):
            x, up, north = struct.unpack_from("<fff", binary, offset+i*stride)
            horizontal = -north if side in ("west", "east") else x
            coords.extend((horizontal/width, up/height))
        uv_view = append_view(struct.pack(f"<{len(coords)}f", *coords), 34962)
        uv_index = len(document["accessors"])
        document["accessors"].append({"bufferView": uv_view, "componentType": 5126,
                                    "count": accessor["count"], "type": "VEC2"})
        primitive["attributes"]["TEXCOORD_0"] = uv_index

    for node in document["nodes"]:
        name = node.get("name", "")
        if "mesh" not in node:
            continue
        kind = "siding" if ":cladding:" in name else "wood" if name == "F1:D01_door_swing" else None
        if not (kind or ":exterior:" in name or name.startswith("roof:") or ":W" in name or name.startswith("F1:D01:")):
            continue
        if ":glass" in name:
            continue
        metal = any(term in name for term in ("standing_seam", "ridge_cap", "fascia", "gutter", "downpipe", "exterior_trim", ":sill", ":frame", ":handle", ":canopy", ":threshold")) or name in ("roof:west_plane", "roof:east_plane")
        roughness, metalness = (.42, .48) if metal else (.6, 0) if kind == "wood" else (.88, 0)
        for primitive in document["meshes"][node["mesh"]]["primitives"]:
            original = primitive.get("material")
            if original is None:
                continue
            key = (original, kind, metal)
            if key not in variants:
                material = deepcopy(document["materials"][original])
                material["name"] = f"Japanese house / {kind or ('coated metal' if metal else 'matte exterior')}"
                pbr = material.setdefault("pbrMetallicRoughness", {})
                pbr.update(roughnessFactor=roughness, metallicFactor=metalness)
                if kind:
                    pbr["baseColorTexture"] = {"index": texture(kind)}
                variants[key] = len(document["materials"])
                document["materials"].append(material)
            primitive["material"] = variants[key]
            if kind:
                add_uv(primitive, name, kind)

    document["buffers"][0]["byteLength"] = len(output)
    output.extend(b"\0"*((-len(output)) % 4))
    document["asset"].setdefault("extras", {})["exteriorFinishes"] = {
        "source": "Original deterministic procedural textures; no external images",
        "sidingTileMetres": [1.82, .455], "timberTileMetres": [.15, 2.8],
        "status": "Demonstration finish, not a selected manufacturer product",
    }
    return bytes(output)
