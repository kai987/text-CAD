"""Build named STEP and GLB outputs for the user-confirmed concept house."""
from pathlib import Path
import json
import struct

from cadgen import glb, read_scene, step

from lib.house_geometry import geometry_manifest, house_assembly
from lib.interior_materials import apply_interior_materials
from lib.exterior_materials import apply_exterior_materials
from lib.outdoor_lighting import apply_outdoor_lighting_materials
from lib.engineering_inputs import engineering_inputs
from lib.step_transport import compact_export
from lib.house_plan import P, floor_plan
from lib.house_geometry import G


MATERIALS = {
    "definitions": {
        "wall_finish": {"name": "Concept plaster", "roughness": 0.86},
        "wood": {"name": "Concept timber", "roughness": 0.65},
        "roof_finish": {"name": "Concept roof cladding", "roughness": 0.7, "metalness": 0.1},
        "glass": {"name": "Concept glazing", "roughness": 0.15, "opacity": 0.45},
    },
    "assignments": [
        {"targets": ["#F1:external_walls", "#F1:partition_walls", "#F2:external_walls", "#F2:partition_walls"], "material": "wall_finish"},
        {"targets": ["#F1:doors", "#F2:doors", "#stairs", "#F1:floor_slab", "#F2:floor_slab"], "material": "wood"},
        {"targets": ["#roof:west_plane", "#roof:east_plane"], "material": "roof_finish"},
        {"targets": [f"#F{n}:W{i:02d}:glass" for n in (1,2) for i in range(1,len(floor_plan(n).windows)+1)], "material": "glass"},
    ],
}

# CADgen's ordinary static GLB exporter batches leaves by material. Its
# supported animation exporter instead retains individual occurrences. This
# no-op clip is only an export adapter: no geometry moves and no animation
# channels are added to the finished GLB.
STATIC_PARTS = r"""
export const clips = {
  named_parts: {label: "Static named assembly export", duration: 1,
                loop: false, update(t, m) {}}
};
"""


def restore_glb_hierarchy(step_path, glb_path):
    """Restore exact STEP labels/groups without changing CADgen's mesh bytes.

    Mesh coordinates are already world-space metres and Y-up. All inserted
    grouping nodes have identity transforms. Original mesh bytes remain intact;
    UVs and embedded finish images are appended to the BIN chunk.
    """
    data = glb_path.read_bytes()
    magic, version, total = struct.unpack_from("<4sII", data)
    if magic != b"glTF" or version != 2 or total != len(data):
        raise ValueError("CADgen did not write a valid GLB 2.0 container")
    json_size, json_kind = struct.unpack_from("<II", data, 12)
    if json_kind != 0x4E4F534A:
        raise ValueError("GLB first chunk is not JSON")
    document = json.loads(data[20:20+json_size])
    native_nodes = document["nodes"]
    node_by_occurrence = {}
    for index, node in enumerate(native_nodes):
        occurrence = node.get("extras", {}).get("cadOccurrenceId")
        if not occurrence or occurrence in node_by_occurrence:
            raise ValueError("Named CADgen GLB must contain one node per STEP leaf")
        node_by_occurrence[occurrence] = index
    scene = read_scene(step_path)

    def insert(occurrence):
        occurrence_id = occurrence.ref.removeprefix("#")
        if not occurrence.children:
            index = node_by_occurrence[occurrence_id]
            native_nodes[index]["name"] = occurrence.label
            document["meshes"][native_nodes[index]["mesh"]]["name"] = occurrence.label
            return index
        children = [insert(child) for child in occurrence.children]
        index = len(native_nodes)
        native_nodes.append({"name": occurrence.label, "children": children,
                             "extras": {"cadOccurrenceId": occurrence_id,
                                        "cadUnits": "m", "cadUpAxis": "y"}})
        return index

    document["scenes"] = [{"name": "house_3d", "nodes": [insert(root) for root in scene.roots]}]
    document["scene"] = 0
    document["asset"]["extras"] = {"units": "metres", "upAxis": "Y",
                                    "source": "Named CADgen STEP assembly; R21 1000 mm cantilever balcony proposal with approved interiors"}
    apply_interior_materials(document)
    bin_offset = 20+json_size
    bin_size, bin_kind = struct.unpack_from("<II", data, bin_offset)
    if bin_kind != 0x004E4942:
        raise ValueError("CADgen GLB second chunk is not BIN")
    binary = apply_exterior_materials(document, data[bin_offset+8:bin_offset+8+bin_size])
    apply_outdoor_lighting_materials(document, P, G)
    from lib.indoor_lighting import apply_indoor_lighting_metadata
    apply_indoor_lighting_metadata(document,P,G)
    encoded = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    encoded += b" "*((-len(encoded)) % 4)
    remaining_chunks = struct.pack("<II", len(binary), bin_kind)+binary
    body = struct.pack("<II", len(encoded), json_kind)+encoded+remaining_chunks
    destination = glb_path.with_suffix(".glb.tmp")
    destination.write_bytes(struct.pack("<4sII", b"glTF", 2, 12+len(body))+body)
    destination.replace(glb_path)
    return {"named_mesh_nodes": len(node_by_occurrence), "all_nodes": len(native_nodes)}


@step(out="../STEP/house_3d.step", materials=MATERIALS, animation=STATIC_PARTS)
@glb(out="../GLB/house_3d.glb")
def house_3d():
    return house_assembly()


if __name__ == "__main__":
    house_3d()
    root = Path(__file__).resolve().parents[1]
    glb.build(root/"STEP"/"house_3d.step", root/"GLB"/"house_3d.glb",
              animation={"clip": "named_parts", "fps": 1, "seconds": 1}, force=True)
    glb_metadata = restore_glb_hierarchy(root/"STEP"/"house_3d.step", root/"GLB"/"house_3d.glb")
    destination = root/"output"/"review"/"house_3d_assumptions_R01.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    manifest = geometry_manifest()
    manifest["glb_export"] = glb_metadata
    destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (destination.parent/"engineering_inputs_R06.json").write_text(
        json.dumps(engineering_inputs(P, G), ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    compact_export(root/"STEP"/"house_3d.step")
