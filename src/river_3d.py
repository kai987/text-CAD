"""Export the independent RIVER-R01 demonstration as named STEP and GLB.

Run from the repository root: CADGEN_DAEMON=0 .venv/bin/python src/river_3d.py
Importing this module never creates or overwrites an output file.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import struct

from cadgen import glb, read_scene, step

from lib.river_geometry import R, REVISION, geometry_manifest, river_assembly
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
    encoded=json.dumps(doc,ensure_ascii=False,separators=(",",":")).encode()
    encoded+=b" "*((-len(encoded))%4)
    remaining=raw[20+size:]
    body=struct.pack("<II",len(encoded),kind)+encoded+remaining
    destination=glb_path.with_suffix(".glb.tmp")
    destination.write_bytes(struct.pack("<4sII",b"glTF",2,len(body)+12)+body)
    destination.replace(glb_path)
    return {"named_mesh_nodes":len(indexed),"all_nodes":len(nodes),
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
