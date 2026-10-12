"""Occurrence hierarchy/metadata edits must preserve native GLB payloads."""
from contextlib import ExitStack
from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import house_3d


def container(document, binary):
    encoded = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode()
    encoded += b" " * (-len(encoded) % 4)
    chunks = struct.pack("<II", len(encoded), 0x4E4F534A) + encoded
    chunks += struct.pack("<II", len(binary), 0x004E4942) + binary
    return struct.pack("<4sII", b"glTF", 2, 12 + len(chunks)) + chunks


def decode(raw):
    size, _ = struct.unpack_from("<II", raw, 12)
    return json.loads(raw[20:20 + size]), raw[20 + size + 8:]


class NamedGlbMetadataTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "model.glb"
        # Deliberately nontrivial world-space coordinates, material fields,
        # accessors and node transforms expose accidental payload edits.
        self.binary = struct.pack("<fffffffff", 1, 2, -3, 4, 5, -6, 7, 8, -9)
        self.document = {
            "asset": {"version": "2.0", "generator": "CADgen"},
            "buffers": [{"byteLength": len(self.binary)}],
            "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(self.binary)}],
            "accessors": [{"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3"}],
            "materials": [{"name": "original", "pbrMetallicRoughness": {"roughnessFactor": .7}}],
            "meshes": [{"name": "old", "primitives": [{"attributes": {"POSITION": 0}, "material": 0}]}],
            "nodes": [{"mesh": 0, "name": "old", "translation": [1, 2, 3],
                       "extras": {"cadOccurrenceId": "leaf-1", "cadUnits": "m", "cadUpAxis": "y"}}],
            "scenes": [{"name": "original", "nodes": [0]}],
            "scene": 0,
        }
        self.raw = container(self.document, self.binary)
        self.path.write_bytes(self.raw)
        leaf = SimpleNamespace(ref="#leaf-1", label="卧室:床", children=[])
        group = SimpleNamespace(ref="#group-1", label="F1:furniture", children=[leaf])
        scene = SimpleNamespace(roots=[group])
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(house_3d, "read_scene", return_value=scene))
        self.stack.enter_context(patch.object(house_3d, "apply_interior_materials"))
        self.stack.enter_context(patch.object(house_3d, "apply_exterior_materials", side_effect=lambda doc, binary: binary))
        self.stack.enter_context(patch.object(house_3d, "apply_outdoor_lighting_materials"))
        self.stack.enter_context(patch("lib.indoor_lighting.apply_indoor_lighting_metadata"))

    def test_display_metadata_and_groups_do_not_modify_geometry_materials_or_transforms(self):
        details = house_3d.restore_glb_hierarchy(
            Path("model.step"), self.path, scene_name="apartment_2ldk", source="A01 参考計画",
        )
        document, binary = decode(self.path.read_bytes())
        self.assertEqual(binary, self.binary)
        for field in ("buffers", "bufferViews", "accessors", "materials"):
            self.assertEqual(document[field], self.document[field])
        self.assertEqual(document["meshes"][0]["primitives"], self.document["meshes"][0]["primitives"])
        expected_node = deepcopy(self.document["nodes"][0])
        expected_node["name"] = "卧室:床"
        self.assertEqual(document["nodes"][0], expected_node)
        self.assertEqual(document["meshes"][0]["name"], "卧室:床")
        self.assertEqual(document["nodes"][1], {
            "name": "F1:furniture", "children": [0],
            "extras": {"cadOccurrenceId": "group-1", "cadUnits": "m", "cadUpAxis": "y"},
        })
        self.assertEqual(document["scenes"], [{"name": "apartment_2ldk", "nodes": [1]}])
        self.assertEqual(document["asset"]["extras"], {"units": "metres", "upAxis": "Y", "source": "A01 参考計画"})
        self.assertEqual(details, {"named_mesh_nodes": 1, "all_nodes": 2})

    def test_single_metadata_pass_matches_legacy_apartment_second_write_byte_for_byte(self):
        house_3d.restore_glb_hierarchy(Path("model.step"), self.path)
        document, binary = decode(self.path.read_bytes())
        document["scenes"][0]["name"] = "apartment_2ldk"
        document["asset"]["extras"]["source"] = "Parametric Japanese 2LDK concept A01; demonstration dimensions"
        expected = container(document, binary)
        self.path.write_bytes(self.raw)
        house_3d.restore_glb_hierarchy(
            Path("model.step"), self.path, scene_name="apartment_2ldk",
            source="Parametric Japanese 2LDK concept A01; demonstration dimensions",
        )
        self.assertEqual(self.path.read_bytes(), expected)

    def test_ambiguous_occurrences_fail_before_overwriting_the_file(self):
        document = deepcopy(self.document)
        document["nodes"].append(deepcopy(document["nodes"][0]))
        raw = container(document, self.binary)
        self.path.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, "one node per STEP leaf"):
            house_3d.restore_glb_hierarchy(Path("model.step"), self.path)
        self.assertEqual(self.path.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
