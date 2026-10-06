"""Compare contact candidates with the original native CAD calculations.

Run after building the optional Rust extension:
    .venv/bin/python checks/test_contact_native.py

The actual W/S/RC STEP scenes are read once. No CAD or review file is written.
"""
from __future__ import annotations

import gc
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))

from cadgen import build123d as bd, read_scene
from lib import contact_geometry
from lib.contact_geometry import ContactGeometry
from lib.native_spatial import aabb_contact_candidates
from lib.structural_variants import _axis_tube, shape_bounds, solid_box


def original_shared_face_area(a, b):
    """Frozen original nested-face algorithm, including its exact screen."""
    total = 0.
    for fa in a.faces():
        aa = shape_bounds(fa)
        for fb in b.faces():
            bb = shape_bounds(fb)
            if any(aa[i] > bb[i+3]+.001 or bb[i] > aa[i+3]+.001
                   for i in range(3)):
                continue
            common = fa.intersect(fb)
            if common is not None:
                total += (sum(part.area for part in common)
                          if isinstance(common, list) else common.area)
    return total


def box(bounds, label="test:box"):
    return solid_box(bounds, label, '#FFFFFF')


def support_queries(native, system):
    """Original saved-validator base and column support traversal order."""
    foundation = [shape for name, shape in native.items()
                  if name.startswith('foundation:')]
    base = [(name, shape) for name, shape in native.items()
            if ':sill_' in name and system == 'W'
            or ':base_plate_' in name and system == 'S'
            or name.startswith('structure:F1:column_') and system == 'RC']
    queries = [(f'{system}:{name}:positive_native_face_to_foundation', shape,
                foundation) for name, shape in base]
    for name, post in native.items():
        if ':column_' not in name:
            continue
        floor = 1 if name.startswith('structure:F1:') else 2
        upper = [shape for label, shape in native.items()
                 if label.startswith(f'structure:F{floor}:beam_')]
        if floor == 2:
            lower = [shape for label, shape in native.items()
                     if label.startswith('structure:F1:beam_')]
        elif system == 'RC':
            lower = foundation
        else:
            lower = [shape for label, shape in native.items()
                     if label.startswith('structure:F1:sill_')]
        queries.extend([
            (f'{system}:{name}:positive_native_face_to_upper_beam', post, upper),
            (f'{system}:{name}:positive_native_face_to_lower_support', post, lower),
        ])
    return queries


def support_report(queries, context=None):
    """No-filter reference or filtered scan; exact distance gate unchanged."""
    report = []
    for name, shape, supports in queries:
        candidates = supports if context is None else context.candidates(shape, supports)
        area = sum((original_shared_face_area(shape, support) if context is None
                    else context.shared_face_area(shape, support))
                   for support in candidates if shape.distance_to(support) < .001)
        report.append({'check': name, 'pass': area > 1, 'actual': round(area, 4),
                       'expected': None})
    return report


class ContactCandidateTests(unittest.TestCase):
    def test_inclusive_contact_all_axes_and_degenerate_faces(self):
        bounds = [[0., 0., 0., 10., 10., 10.],
                  [10., 0., 0., 10., 10., 10.],
                  [10., 10., 10., 10., 10., 10.]]
        queries = [[10., 0., 0., 20., 10., 10.],
                   [0., 10., 0., 10., 20., 10.],
                   [0., 0., 10., 10., 10., 20.],
                   [-10., 0., 0., 0., 10., 10.],
                   [0., -10., 0., 10., 0., 10.],
                   [0., 0., -10., 10., 10., 0.],
                   [10.001, 10.001, 10.001, 20., 20., 20.],
                   [10.001001, 0., 0., 20., 10., 10.]]
        expected = [[0, 1, 2], [0, 1, 2], [0, 1, 2], [0], [0, 1], [0, 1],
                    [0, 1, 2], []]
        for backend in ('python', 'rust', 'auto'):
            with self.subTest(backend=backend):
                self.assertEqual(aabb_contact_candidates(bounds, queries,
                                                         backend=backend), expected)
                self.assertEqual(aabb_contact_candidates([], queries,
                                                         backend=backend), [[] for _ in queries])
                self.assertEqual(aabb_contact_candidates(bounds, [],
                                                         backend=backend), [])

    def test_cached_immutable_shapes_and_forced_backend_are_forwarded(self):
        class CountedShape:
            def __init__(self, bound):
                self.bound = bound
                self.bound_calls = self.face_calls = 0

            def bounding_box(self):
                self.bound_calls += 1
                a = self.bound
                return SimpleNamespace(min=SimpleNamespace(X=a[0], Y=a[1], Z=a[2]),
                                       max=SimpleNamespace(X=a[3], Y=a[4], Z=a[5]))

            def faces(self):
                self.face_calls += 1
                return []

        query = CountedShape((0, 0, 0, 10, 10, 10))
        far = CountedShape((100, 100, 100, 110, 110, 110))
        touching = CountedShape((10, 0, 0, 20, 10, 10))
        context = ContactGeometry(backend='rust')
        with patch.object(contact_geometry, 'aabb_contact_candidates',
                          wraps=aabb_contact_candidates) as native:
            self.assertEqual(context.candidates(query, [far, touching]), (touching,))
            self.assertEqual(context.candidates(query, [far, touching]), (touching,))
            self.assertEqual(context.shared_face_area(query, touching), 0.)
            self.assertEqual(context.shared_face_area(query, touching), 0.)
        self.assertTrue(all(call.kwargs['backend'] == 'rust'
                            and call.args[2] == .001 for call in native.call_args_list))
        self.assertEqual([q.bound_calls for q in (query, far, touching)], [1, 1, 1])
        self.assertEqual([q.face_calls for q in (query, touching)], [1, 1])

    def test_native_faces_keep_face_edge_corner_and_small_gap_results(self):
        first = box((0, 0, 0, 100, 100, 100))
        touching = box((100, 0, 0, 200, 100, 100))
        tilted_a = first.rotate(bd.Axis.Z, 17)
        tilted_b = touching.rotate(bd.Axis.Z, 17)
        lower_cylinder = bd.Solid.make_cylinder(10, 20)
        upper_cylinder = bd.Solid.make_cylinder(10, 20,
                                                bd.Plane(origin=(0, 0, 20)))
        cases = [
            ('face', first, touching),
            ('edge', first, box((100, 100, 0, 200, 200, 100))),
            ('corner', first, box((100, 100, 100, 200, 200, 200))),
            ('near_gap', first, box((100.0005, 0, 0, 200, 100, 100))),
            ('threshold_gap', first, box((100.001, 0, 0, 200, 100, 100))),
            ('outside_gap', first, box((100.001001, 0, 0, 200, 100, 100))),
            ('tilted_face', tilted_a, tilted_b),
            ('cylinder_cap', lower_cylinder, upper_cylinder),
        ]
        for name, a, b in cases:
            original = original_shared_face_area(a, b)
            for backend in ('python', 'rust', 'auto'):
                with self.subTest(case=name, backend=backend):
                    context = ContactGeometry(backend=backend)
                    self.assertEqual(context.shared_face_area(a, b), original)
                    expected = original if a.distance_to(b) < .001 else 0.
                    actual = sum(context.shared_face_area(a, candidate)
                                 for candidate in context.candidates(a, [b])
                                 if a.distance_to(candidate) < .001)
                    self.assertEqual(actual, expected)
        self.assertEqual(original_shared_face_area(first, touching), 10000.)
        self.assertEqual(original_shared_face_area(first, cases[1][2]), 0.)
        self.assertEqual(original_shared_face_area(first, cases[2][2]), 0.)

    def test_hollow_member_bounding_overlap_never_becomes_contact_area(self):
        tube = _axis_tube((0, 0, 0, 100, 20, 20), 'h', 2, 'test:hollow')
        void = box((10, 5, 5, 90, 15, 15))
        end = box((-10, 0, 0, 0, 20, 20))
        for backend in ('python', 'rust', 'auto'):
            with self.subTest(backend=backend):
                context = ContactGeometry(backend=backend)
                self.assertEqual(context.candidates(tube, [void, end]), (void, end))
                self.assertGreater(tube.distance_to(void), .001)
                self.assertEqual(context.shared_face_area(tube, void), 0.)
                self.assertEqual(context.shared_face_area(tube, end),
                                 original_shared_face_area(tube, end))
                self.assertAlmostEqual(context.shared_face_area(tube, end), 144.)


class ActualSavedContactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = json.loads((ROOT/'output/review/structural_variants_R07.json').read_text())
        cls.native = {system: {item.label: item.shape()
                              for item in read_scene(ROOT/record['step_path']).leaves()}
                      for system, record in manifest['variants'].items()}
        cls.queries = {system: support_queries(native, system)
                       for system, native in cls.native.items()}
        cls.original = {system: support_report(queries)
                        for system, queries in cls.queries.items()}

    @classmethod
    def tearDownClass(cls):
        cls.native.clear()
        cls.queries.clear()
        gc.collect()

    def test_saved_w_s_rc_exact_support_reports_match_unfiltered_original(self):
        for system, queries in self.queries.items():
            for backend in ('python', 'rust', 'auto'):
                with self.subTest(system=system, backend=backend):
                    actual = support_report(queries, ContactGeometry(backend=backend))
                    self.assertEqual(actual, self.original[system])
                    self.assertTrue(all(row['pass'] for row in actual))

    def test_saved_contact_candidates_do_not_omit_exact_distance_hits(self):
        for system, queries in self.queries.items():
            context = ContactGeometry(backend='rust')
            checked = kept = 0
            for name, shape, supports in queries:
                candidates = context.candidates(shape, supports)
                checked += len(supports)
                kept += len(candidates)
                candidate_ids = {id(q) for q in candidates}
                with self.subTest(system=system, contact=name):
                    self.assertEqual([q for q in supports if id(q) in candidate_ids],
                                     list(candidates))
                    for support in supports:
                        if shape.distance_to(support) < .001:
                            self.assertIn(id(support), candidate_ids)
            self.assertLess(kept, checked*.4, system)


if __name__ == '__main__':
    unittest.main(verbosity=2)
