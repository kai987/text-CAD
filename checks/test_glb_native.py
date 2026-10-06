"""Read-only GLB fixture, decoded-byte oracle and optional native regressions."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lib import native_glb as audit
from lib import native_spatial as spatial

FILES = ("house_3d.glb", "apartment_2ldk.glb", "structure_W.glb", "structure_S.glb", "structure_RC.glb")


def glb(document, binary, *, json_bytes=None):
    encoded = json.dumps(document, separators=(",", ":")).encode() if json_bytes is None else json_bytes
    encoded += b" " * (-len(encoded) % 4)
    binary += b"\0" * (-len(binary) % 4)
    chunks = struct.pack("<II", len(encoded), 0x4E4F534A) + encoded + struct.pack("<II", len(binary), 0x004E4942) + binary
    return struct.pack("<4sII", b"glTF", 2, 12 + len(chunks)) + chunks


def fixture(*, vertices=None, indices=(0, 1, 2), component=2, normals=True, interleaved=False):
    vertices = vertices or [(0, 0, 0), (0.1, 0, 0), (0, 2, 0)]
    binary = bytearray()
    if interleaved and not normals:
        raise ValueError("Fixture interleaving requires normals")
    for point in vertices:
        binary += struct.pack("<fff", *point)
        if interleaved:
            binary += struct.pack("<fff", 0, 0, 1)
    decoded = [struct.unpack("<fff", struct.pack("<fff", *point)) for point in vertices]
    minimum = [min(p[axis] for p in decoded) for axis in range(3)]
    maximum = [max(p[axis] for p in decoded) for axis in range(3)]
    views = [{"buffer": 0, "byteOffset": 0, "byteLength": len(binary), "target": 34962}]
    if interleaved:
        views[0]["byteStride"] = 24
    accessors = [{"bufferView": 0, "byteOffset": 0, "componentType": 5126, "type": "VEC3", "count": len(vertices),
                  "min": minimum, "max": maximum}]
    attributes = {"POSITION": 0}
    if normals:
        if interleaved:
            normal_view, normal_offset = 0, 12
        else:
            normal_view, normal_offset = len(views), 0
            views.append({"buffer": 0, "byteOffset": len(binary), "byteLength": len(vertices) * 12, "target": 34962})
            binary += struct.pack("<fff", 0, 0, 1) * len(vertices)
        attributes["NORMAL"] = len(accessors)
        accessors.append({"bufferView": normal_view, "byteOffset": normal_offset, "componentType": 5126,
                          "type": "VEC3", "count": len(vertices)})
    primitive = {"attributes": attributes, "mode": 4}
    if indices is not None:
        binary += b"\0" * (-len(binary) % 4)
        start = len(binary)
        format = {1: "B", 2: "H", 4: "I"}[component]
        binary += struct.pack("<" + format * len(indices), *indices)
        primitive["indices"] = len(accessors)
        accessors.append({"bufferView": len(views), "componentType": {1: 5121, 2: 5123, 4: 5125}[component],
                          "type": "SCALAR", "count": len(indices)})
        views.append({"buffer": 0, "byteOffset": start, "byteLength": len(indices) * component, "target": 34963})
    document = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(binary)}],
                "bufferViews": views, "accessors": accessors, "meshes": [{"name": "fixture", "primitives": [primitive]}]}
    return document, bytes(binary)


class PythonAuditTests(unittest.TestCase):
    def test_index_widths_and_nonindexed_interleaved_vertices(self):
        for component in (1, 2, 4):
            for interleaved in (False, True):
                with self.subTest(component=component, interleaved=interleaved):
                    document, binary = fixture(component=component, interleaved=interleaved)
                    result = audit.audit_glb_bytes(glb(document, binary), backend="python")
                    self.assertEqual((result["vertex_count"], result["index_count"], result["triangle_count"],
                                      result["normal_count"], result["degenerate_count"]), (3, 3, 1, 3, 0))
                    self.assertEqual(result["bounds"], [0, 0, 0, struct.unpack("<f", struct.pack("<f", .1))[0], 2, 0])
        document, binary = fixture(indices=None, normals=False)
        result = audit.audit_glb_bytes(glb(document, binary), backend="python")
        self.assertEqual(result["index_count"], 0)
        self.assertEqual(result["normal_count"], 0)
        self.assertIsNone(result["primitives"][0]["normal_count"])

    def test_shared_accessors_still_report_each_primitive(self):
        document, binary = fixture()
        document["meshes"].append({"name": "second", "primitives": deepcopy(document["meshes"][0]["primitives"])})
        result = audit.audit_glb_bytes(glb(document, binary), backend="python")
        self.assertEqual((result["mesh_count"], result["primitive_count"], result["triangle_count"]), (2, 2, 2))
        self.assertEqual([row["mesh_name"] for row in result["primitives"]], ["fixture", "second"])

    def test_degenerate_triangles_are_diagnostic_and_tiny_valid_triangle_is_not(self):
        for vertices, indices in [([(0, 0, 0), (1, 0, 0), (2, 0, 0)], (0, 1, 2)),
                                  ([(0, 0, 0), (1, 0, 0), (0, 1, 0)], (0, 0, 2))]:
            document, binary = fixture(vertices=vertices, indices=indices)
            self.assertEqual(audit.audit_glb_bytes(glb(document, binary), backend="python")["degenerate_count"], 1)
        tiny = struct.unpack("<f", struct.pack("<I", 1))[0]
        document, binary = fixture(vertices=[(0, 0, 0), (tiny, 0, 0), (0, tiny, 0)])
        self.assertEqual(audit.audit_glb_bytes(glb(document, binary), backend="python")["degenerate_count"], 0)

    def test_decoded_bounds_reject_forged_metadata_and_accept_float32_rounding(self):
        document, binary = fixture()
        document["accessors"][0]["max"][0] = .1  # legal double JSON spelling of the stored f32 extremum
        audit.audit_glb_bytes(glb(document, binary), backend="python")
        for bound, axis, value in (("max", 0, .2), ("min", 1, -1), ("min", 0, True),
                                  ("max", 0, 1 << 2000), ("max", 0, 1e100)):
            tampered = deepcopy(document)
            tampered["accessors"][0][bound][axis] = value
            with self.subTest(bound=bound, value=value), self.assertRaises(ValueError):
                audit.audit_glb_bytes(glb(tampered, binary), backend="python")

    def test_nonfinite_position_and_normal_bytes_are_rejected(self):
        document, binary = fixture()
        for offset in (0, document["bufferViews"][1]["byteOffset"]):
            for value in (float("nan"), float("inf"), float("-inf")):
                tampered = bytearray(binary)
                struct.pack_into("<f", tampered, offset, value)
                with self.subTest(offset=offset, value=value), self.assertRaisesRegex(ValueError, "non-finite"):
                    audit.audit_glb_bytes(glb(document, bytes(tampered)), backend="python")

    def test_out_of_range_and_restart_indices_are_rejected(self):
        document, binary = fixture(indices=(0, 1, 3))
        with self.assertRaisesRegex(ValueError, "index"):
            audit.audit_glb_bytes(glb(document, binary), backend="python")
        vertices = [(float(index), 0, 0) for index in range(256)]
        document, binary = fixture(vertices=vertices, indices=(0, 1, 255), component=1)
        with self.assertRaisesRegex(ValueError, "index"):
            audit.audit_glb_bytes(glb(document, binary), backend="python")

    def test_triangle_and_normal_counts_are_checked(self):
        document, binary = fixture(indices=(0, 1))
        with self.assertRaisesRegex(ValueError, "divisible"):
            audit.audit_glb_bytes(glb(document, binary), backend="python")
        document, binary = fixture(vertices=[(0, 0, 0)] * 4, indices=None)
        with self.assertRaisesRegex(ValueError, "divisible"):
            audit.audit_glb_bytes(glb(document, binary), backend="python")
        document, binary = fixture()
        document["accessors"][1]["count"] = 2
        with self.assertRaisesRegex(ValueError, "count"):
            audit.audit_glb_bytes(glb(document, binary), backend="python")

    def test_accessor_references_spans_and_unsupported_encodings_are_checked(self):
        source, binary = fixture()
        mutations = [
            (lambda d: d["accessors"][0].update(bufferView=99), "reference"),
            (lambda d: d["accessors"][0].update(count=100), "span"),
            (lambda d: d["accessors"][0].update(byteOffset=2), "alignment"),
            (lambda d: d["accessors"][0].update(count=-1), "integer"),
            (lambda d: d["accessors"][0].update(count=True), "integer"),
            (lambda d: d["accessors"][0].update(sparse={}), "Sparse"),
            (lambda d: d["accessors"][0].update(normalized=True), "normalization"),
            (lambda d: d["accessors"][0].update(componentType=[]), "component"),
            (lambda d: d["accessors"][0].update(type={}), "component"),
            (lambda d: d["accessors"][0].pop("min"), "bounds"),
            (lambda d: d["bufferViews"][0].update(byteLength=10), "span"),
            (lambda d: d["bufferViews"][0].update(byteStride=14), "byteStride"),
            (lambda d: d["bufferViews"][0].update(byteStride=256), "byteStride"),
            (lambda d: d["bufferViews"][-1].update(byteStride=4), "span|packed"),
            (lambda d: d["bufferViews"][0].update(extensions={"EXT_meshopt_compression": {}}), "extensions"),
            (lambda d: d["buffers"][0].update(uri="outside.bin"), "URI"),
            (lambda d: d["meshes"][0]["primitives"][0].update(mode=1), "TRIANGLES"),
            (lambda d: d["meshes"][0]["primitives"][0].update(mode=4.0), "TRIANGLES"),
            (lambda d: d["meshes"][0]["primitives"][0].update(targets=[{}]), "morph"),
        ]
        for mutate, reason in mutations:
            document = deepcopy(source)
            mutate(document)
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                audit.audit_glb_bytes(glb(document, binary), backend="python")

    def test_container_and_json_errors_do_not_reach_mesh_decoding(self):
        document, binary = fixture()
        raw = glb(document, binary)
        invalid = [b"", raw[:-1], b"bad!" + raw[4:], raw[:4] + struct.pack("<I", 1) + raw[8:]]
        bad_chunk = bytearray(raw)
        struct.pack_into("<I", bad_chunk, 12, 0xffffffff)
        invalid.append(bytes(bad_chunk))
        bad_kind = bytearray(raw)
        struct.pack_into("<I", bad_kind, 16, 0x004E4942)
        invalid.append(bytes(bad_kind))
        invalid += [glb(document, binary, json_bytes=b'{"asset":{"version":"2.0"},"asset":{}}'),
                    glb(document, binary, json_bytes=b'{"x":NaN}'),
                    glb(document, binary, json_bytes=b"\xff")]
        for value in invalid:
            with self.subTest(length=len(value)), self.assertRaises(ValueError):
                audit.audit_glb_bytes(value, backend="python")
        for length in (len(binary) + 4, len(binary) - 4):
            changed = deepcopy(document)
            changed["buffers"][0]["byteLength"] = length
            with self.assertRaisesRegex(ValueError, "BIN"):
                audit.audit_glb_bytes(glb(changed, binary), backend="python")
        changed, unpadded = fixture(component=1)
        changed["buffers"][0]["byteLength"] = len(unpadded) - 1
        with self.assertRaisesRegex(ValueError, "padding"):
            audit.audit_glb_bytes(glb(changed, unpadded), backend="python")

    def test_raw_layouts_reject_unsafe_spans_and_preserve_zero_index_count(self):
        binary = struct.pack("<fffffffff", 0, 0, 0, 1, 0, 0, 0, 1, 0)
        result = audit.audit_triangle_meshes(binary, [((0, 12, 3), (0, 2, 0, 2), None)], backend="python")
        self.assertEqual(result, [(3, 0, 0, None, (0, 0, 0, 1, 1, 0), 0)])
        invalid = [((0, 12, 0), None, None), ((0, 8, 3), None, None), ((2, 12, 3), None, None),
                   ((0, 12, 4), None, None), ((0, 12, 3), (0, 1, 3, 3), None),
                   ((0, 12, 3), None, (0, 12, 2)), ((1 << 100, 12, 3), None, None),
                   ((0, 1 << 63, 3), None, None), ((-1, 12, 3), None, None)]
        for layout in invalid:
            with self.subTest(layout=layout), self.assertRaises(ValueError):
                audit.audit_triangle_meshes(binary, [layout], backend="python")
        with self.assertRaises(TypeError):
            audit.audit_triangle_meshes(bytearray(binary), [], backend="python")
        with self.assertRaises(ValueError):
            audit.audit_triangle_meshes(binary, [], backend="unknown")


class BackendSafetyTests(unittest.TestCase):
    def test_missing_and_failed_native_falls_back_but_strict_raises(self):
        document, binary = fixture()
        raw = glb(document, binary)
        expected = audit.audit_glb_bytes(raw, backend="python")
        with patch.object(spatial, "_load_native", return_value=(None, "injected unavailable")):
            self.assertEqual(audit.audit_glb_bytes(raw), expected)
            with self.assertRaisesRegex(RuntimeError, "unavailable"):
                audit.audit_glb_bytes(raw, backend="rust")
        class Failed:
            def audit_triangle_meshes(self, *args): raise RuntimeError("injected runtime error")
        with patch.object(spatial, "_load_native", return_value=(Failed(), None)):
            self.assertEqual(audit.audit_glb_bytes(raw), expected)
            with self.assertRaisesRegex(RuntimeError, "runtime error"):
                audit.audit_glb_bytes(raw, backend="rust")

    def test_invalid_native_results_cannot_escape_result_validation(self):
        document, binary = fixture()
        raw = glb(document, binary)
        expected = audit.audit_glb_bytes(raw, backend="python")
        good = (3, 3, 1, 3, tuple(expected["bounds"]), 0)
        invalid = [[], [good + (0,)], [(*good[:3], 3.0, *good[4:])],
                   [(3, 3, 1, 3, (0, 0, 0, float("nan"), 2, 0), 0)],
                   [(3, 3, 1, 3, (0, 0, 0, 1, 2, 0), 2)], [(3, True, 1, 3, good[4], 0)]]
        for output in invalid:
            class Broken:
                def audit_triangle_meshes(self, *args): return output
            with self.subTest(output=output), patch.object(spatial, "_load_native", return_value=(Broken(), None)):
                self.assertEqual(audit.audit_glb_bytes(raw), expected)
                with self.assertRaisesRegex(RuntimeError, "Invalid native"):
                    audit.audit_glb_bytes(raw, backend="rust")

    def test_explicit_python_does_not_import_native(self):
        document, binary = fixture()
        with patch.object(spatial, "_load_native", side_effect=AssertionError("must not import")):
            audit.audit_glb_bytes(glb(document, binary), backend="python")


@unittest.skipUnless(spatial.backend_status()["available"], "Build the native extension for strict Rust GLB oracle tests")
class NativeOracleTests(unittest.TestCase):
    def test_all_saved_glb_full_decoded_summaries_match_python(self):
        for name in FILES:
            path = ROOT / "GLB" / name
            before = path.read_bytes()
            expected = audit.audit_glb_bytes(before, backend="python")
            actual = audit.audit_glb_bytes(before, backend="rust")
            with self.subTest(file=name):
                self.assertEqual(actual, expected)
                self.assertEqual(hashlib.sha256(path.read_bytes()).digest(), hashlib.sha256(before).digest())

    def test_native_layouts_match_oracle_across_index_widths_interleaving_and_tiny_area(self):
        tiny = struct.unpack("<f", struct.pack("<I", 1))[0]
        rng = random.Random(81007)
        for width in (1, 2, 4):
            for interleaved in (False, True):
                vertices = [(rng.uniform(-1e4, 1e4), rng.uniform(-1e4, 1e4), rng.uniform(-1e4, 1e4)) for _ in range(24)]
                document, binary = fixture(vertices=vertices, indices=tuple(range(24)), component=width, interleaved=interleaved)
                raw = glb(document, binary)
                self.assertEqual(audit.audit_glb_bytes(raw, backend="rust"), audit.audit_glb_bytes(raw, backend="python"))
        for vertices, indices in [([(0, 0, 0), (tiny, 0, 0), (0, tiny, 0)], None),
                                  ([(0, 0, 0), (1, 0, 0), (2, 0, 0)], (0, 1, 2))]:
            document, binary = fixture(vertices=vertices, indices=indices, normals=False)
            raw = glb(document, binary)
            self.assertEqual(audit.audit_glb_bytes(raw, backend="rust"), audit.audit_glb_bytes(raw, backend="python"))
        binary = struct.pack("<fffffffff", 0, 0, 0, 1, 0, 0, 0, 1, 0)
        layout = [((0, 12, 3), (0, 2, 0, 2), None)]
        self.assertEqual(audit.audit_triangle_meshes(binary, layout, backend="rust"), audit.audit_triangle_meshes(binary, layout, backend="python"))

    def test_native_rejects_corrupt_numeric_bytes_and_restart_sentinel(self):
        document, binary = fixture()
        mutations = []
        for offset in (0, document["bufferViews"][1]["byteOffset"]):
            for value in (float("nan"), float("inf")):
                changed = bytearray(binary)
                struct.pack_into("<f", changed, offset, value)
                mutations.append((document, bytes(changed)))
        mutations.append(fixture(indices=(0, 1, 3)))
        mutations.append(fixture(vertices=[(float(i), 0, 0) for i in range(256)], indices=(0, 1, 255), component=1))
        for document, binary in mutations:
            with self.subTest(length=len(binary)), self.assertRaises((ValueError, RuntimeError)):
                audit.audit_glb_bytes(glb(document, binary), backend="rust")


class CommandLineTests(unittest.TestCase):
    def test_cli_defaults_to_all_five_files_and_reports_errors_without_writes(self):
        command = [sys.executable, str(ROOT / "checks" / "validate_glb_native.py"), "--backend", "python"]
        before = {name: ((ROOT / "GLB" / name).stat().st_mtime_ns,
                         hashlib.sha256((ROOT / "GLB" / name).read_bytes()).digest()) for name in FILES}
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["pass"])
        self.assertEqual([Path(row["path"]).name for row in report["files"]], list(FILES))
        self.assertEqual(before, {name: ((ROOT / "GLB" / name).stat().st_mtime_ns,
                                        hashlib.sha256((ROOT / "GLB" / name).read_bytes()).digest()) for name in FILES})
        with tempfile.TemporaryDirectory() as folder:
            invalid = Path(folder) / "invalid.glb"
            invalid.write_bytes(b"invalid")
            destination = Path(folder) / "report.json"
            result = subprocess.run(command + [str(invalid), "--report", str(destination)], cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertFalse(json.loads(result.stdout)["pass"])
            self.assertEqual(json.loads(destination.read_text()), json.loads(result.stdout))


if __name__ == "__main__":
    unittest.main()
