"""Geometry-oracle and native-loader regressions; no CAD exports or writes."""
from pathlib import Path
import json
import os
import random
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from shapely import affinity
from shapely.geometry import LineString, MultiPolygon, Polygon, box
from lib import native_spatial as spatial


class AdapterFallbackTests(unittest.TestCase):
    def test_unavailable_native_falls_back_but_strict_rust_raises(self):
        with patch.object(spatial, "_load_native", return_value=(None, "injected unavailable")):
            shapes = [box(0, 0, 3, 3), box(1, 1, 4, 4)]
            self.assertEqual(spatial.polygon_metrics(shapes, [(0, 1)], [], backend="auto"), ([4.0], []))
            self.assertEqual(spatial.aabb_candidates([(0, 0, 0, 2, 2, 2)], [(1, 1, 1, 3, 3, 3)]), [[0]])
            with self.assertRaises(RuntimeError):
                spatial.polygon_metrics(shapes, [(0, 1)], [], backend="rust")
            with self.assertRaises(RuntimeError):
                spatial.aabb_candidates([], [], backend="rust")

    def test_failed_and_malformed_native_results_cannot_replace_the_oracle(self):
        class Broken:
            def aabb_candidates(self, *args): return [[1000]]
            def aabb_contact_candidates(self,*args): return [[1000]]
        with patch.object(spatial, "_load_native", return_value=(Broken(), None)):
            shapes = [box(0, 0, 3, 3), box(1, 1, 4, 4)]
            self.assertEqual(spatial.polygon_metrics(shapes, [(0, 1)], []), ([4.0], []))
            self.assertEqual(spatial.aabb_candidates([(0, 0, 0, 2, 2, 2)], [(1, 1, 1, 3, 3, 3)]), [[0]])
            with self.assertRaises(RuntimeError): spatial.polygon_metrics(shapes, [(0, 1)], [], backend="rust")
            with self.assertRaises(RuntimeError): spatial.aabb_candidates([], [(0, 0, 0, 1, 1, 1)], backend="rust")
            self.assertEqual(spatial.aabb_contact_candidates([(0,0,0,1,1,1)],[(1,0,0,2,1,1)]),[[0]])
            with self.assertRaises(RuntimeError): spatial.aabb_contact_candidates([],[(0,0,0,1,1,1)],backend="rust")

    def test_invalid_inputs_and_backend_are_rejected(self):
        for bounds in [[(0, 0)], [(0, 0, 0, -1, 1, 1)], [(0, 0, 0, float("nan"), 1, 1)]]:
            with self.assertRaises(ValueError): spatial.aabb_candidates(bounds, [], backend="python")
        for epsilon in [-1, float("nan"), float("inf")]:
            with self.assertRaises(ValueError): spatial.aabb_candidates([], [], epsilon, backend="python")
            with self.assertRaises(ValueError): spatial.aabb_contact_candidates([],[],epsilon,backend="python")
        for pairs in [[(-1, 0)], [(0, 1)], [(True, 0)]]:
            with self.assertRaises(ValueError): spatial.polygon_metrics([box(0, 0, 1, 1)], pairs, [], backend="python")
        with self.assertRaises(ValueError): spatial.polygon_metrics([], [], [], backend="unknown")

    def test_source_drift_rejects_stale_native_binary(self):
        spatial._load_native.cache_clear()
        try:
            with patch.object(spatial, "_source_hashes", return_value={"changed": "hash"}):
                module, reason = spatial._load_native()
                self.assertIsNone(module)
                self.assertIsInstance(reason, str)
        finally: spatial._load_native.cache_clear()

    def test_manifest_python_version_must_match_the_current_interpreter(self):
        spatial._load_native.cache_clear()
        manifest={"version":1,"api_version":3,"python_cache_tag":"different-python"}
        try:
            with patch.object(Path, "read_text", return_value=json.dumps(manifest)):
                module,reason=spatial._load_native()
                self.assertIsNone(module)
                self.assertIn("Python version changed",reason)
        finally: spatial._load_native.cache_clear()

    def test_python_backend_is_explicit_and_does_not_load_native(self):
        with patch.object(spatial, "_load_native", side_effect=AssertionError("should not import")):
            self.assertEqual(spatial.polygon_metrics([box(0, 0, 1, 1)], [(0, 0)], [(0, 0)], backend="python"), ([1.0], [True]))
            self.assertEqual(spatial.aabb_candidates([], [], backend="python"), [])
            self.assertEqual(spatial.aabb_contact_candidates([],[],backend="python"),[])

    def test_environment_selects_auto_calls_but_explicit_backend_overrides_it(self):
        with patch.object(spatial,"_load_native",return_value=(None,"unavailable")):
            with patch.dict(os.environ,{"TEXT_CAD_SPATIAL_BACKEND":"rust"}):
                with self.assertRaises(RuntimeError): spatial.aabb_candidates([],[])
                self.assertEqual(spatial.aabb_candidates([],[],backend="python"),[])
            with patch.dict(os.environ,{"TEXT_CAD_SPATIAL_BACKEND":"python"}):
                self.assertEqual(spatial.aabb_candidates([],[]),[])
                with self.assertRaises(RuntimeError): spatial.aabb_candidates([],[],backend="rust")


@unittest.skipUnless(spatial.backend_status()["available"], "Build the native extension to run Rust oracle tests")
class NativeOracleTests(unittest.TestCase):
    def test_contacts_retain_touching_faces_and_tolerance_boundaries(self):
        bounds=[(0,0,0,10,10,10),(30,0,0,30,10,10),(5,5,5,5,5,5)]
        queries=[(10,0,0,20,10,10),(10.001,0,0,20,10,10),
                 (10.002,0,0,20,10,10),(30,0,0,30,10,10),
                 (0,0,0,0,0,0)]
        expected=[[0],[0],[],[1],[0]]
        self.assertEqual(spatial.aabb_contact_candidates(bounds,queries,backend="python"),expected)
        self.assertEqual(spatial.aabb_contact_candidates(bounds,queries,backend="rust"),expected)
        self.assertEqual(spatial.aabb_contact_candidates(bounds,queries,0,backend="rust"),
                         spatial.aabb_contact_candidates(bounds,queries,0,backend="python"))

    def test_contact_bvh_matches_inclusive_full_scan_on_seeded_boxes(self):
        rng=random.Random(7107)
        bounds=[]
        for _ in range(1000):
            minimum=[rng.uniform(-8000,8000) for _ in range(3)]
            maximum=[v+(rng.uniform(0,1800) if rng.random()>.15 else 0) for v in minimum]
            bounds.append(tuple(minimum+maximum))
        queries=bounds[::31]+[(0,0,0,0,0,0)]
        for tolerance in (0,.001,1,100):
            self.assertEqual(spatial.aabb_contact_candidates(bounds,queries,tolerance,backend="rust"),
                             spatial.aabb_contact_candidates(bounds,queries,tolerance,backend="python"))

    def test_polygons_holes_islands_and_boundary_inclusive_coverage(self):
        shapes = [Polygon([(0, 0), (10, 0), (10, 10), (0, 10)], [[(2, 2), (2, 4), (4, 4), (4, 2)]]),
                  box(0, 0, 2, 2), box(2, 2, 4, 4), box(-1, 0, 1, 2),
                  MultiPolygon([box(0, 0, 1, 1), box(3, 0, 4, 1)]), box(1, 0, 3, 1), Polygon()]
        pairs = [(i, j) for i in range(len(shapes)) for j in range(len(shapes))]
        reference = spatial.polygon_metrics(shapes, pairs, pairs, backend="python")
        result = spatial.polygon_metrics(shapes, pairs, pairs, backend="rust")
        self.assertEqual(result[1], reference[1])
        for actual, expected in zip(result[0], reference[0]): self.assertAlmostEqual(actual, expected, places=7)

    def test_seeded_rotated_intersections_and_room_buffer(self):
        rng = random.Random(8107)
        shapes = [affinity.rotate(box(rng.uniform(-100, 100), rng.uniform(-100, 100), 250, 350),
                                  rng.uniform(-180, 180), origin=(0, 0)) for _ in range(35)]
        pairs = [(i, j) for i in range(len(shapes)) for j in range(i, len(shapes))]
        reference = spatial.polygon_metrics(shapes, pairs, pairs, backend="python")
        result = spatial.polygon_metrics(shapes, pairs, pairs, backend="rust")
        self.assertEqual(result[1], reference[1])
        self.assertEqual(result[0],reference[0])
        buffered = box(0, 0, 3000, 4000).buffer(.001)
        shapes = [buffered, box(-.0005, 0, 100, 100), box(-.002, 0, 100, 100)]
        self.assertEqual(spatial.polygon_metrics(shapes, [], [(0, 1), (0, 2)], backend="rust")[1], [True, False])

    def test_candidate_index_has_no_false_negatives_and_preserves_input_order(self):
        rng = random.Random(9107)
        bounds = []
        for _ in range(1200):
            minimum = [rng.uniform(-8000, 8000) for _ in range(3)]
            bounds.append(tuple(minimum + [v + rng.uniform(0, 1800) for v in minimum]))
        queries = [(-500, -600, -700, 500, 600, 700), bounds[10], (0, 0, 0, 0, 0, 0)] + bounds[::31]
        for epsilon in [0, 1e-6, .1, 100]:
            self.assertEqual(spatial.aabb_candidates(bounds, queries, epsilon, backend="rust"),
                             spatial.aabb_candidates(bounds, queries, epsilon, backend="python"))

    def test_native_unsupported_geometry_falls_back_without_changing_results(self):
        shapes = [box(0, 0, 10, 10), LineString([(0, 0), (10, 10)])]
        self.assertEqual(spatial.polygon_metrics(shapes, [(0, 1)], [(0, 1)]),
                         spatial.polygon_metrics(shapes, [(0, 1)], [(0, 1)], backend="python"))
        with self.assertRaises(RuntimeError): spatial.polygon_metrics(shapes, [], [(0, 1)], backend="rust")


if __name__ == "__main__": unittest.main()
