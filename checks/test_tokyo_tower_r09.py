"""Real lower-member openings, against the independent pre-R09 R08 snapshot.

The exact edit list is derived only from frozen R08 names. It never discovers
an allowed scope by inspecting the modified geometry. Historic R07/R08 hashes
continue to protect their original implementations through explicit replays.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from math import dist, isfinite, sqrt
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from checks.tokyo_tower_r08_baseline import (
    R08_BASELINE, TOKYO_R08_PARAMETERS, TOKYO_R08_PART_NAMES,
    TOKYO_R08_SPEC_SHA256_BY_NAME,
)
from checks.test_tokyo_tower_r08 import geometry_fingerprint, r08_reference_specs
from checks.tokyo_tower_r09_baseline import R09_BASELINE, R09_LOWER_BUILT_UP
from lib.tower_geometry import TOWERS, component_specs, _cad_shape


# All 1384 R08 member-size edits plus exactly 144 lower-shaft panel members.
# Ancillary anchors, continuation links, node plates and crown bridges stay
# protected, even though their source members receive the R09 construction.
R09_TARGET_NAMES = frozenset(R08_BASELINE['r08_mutable_framing_names']) | frozenset(
    name for name in TOKYO_R08_PART_NAMES if re.fullmatch(
        r'structure:lower_belt_[0-3]_[0-2]'
        r'|structure:lower_panel_[ab]_[0-3]_[0-2]_[0-3]'
        r'|structure:lower_panel_vertical_[0-3]_[0-2]_[1-3]', name))
MACRO_KEYS = (
    'name', 'group', 'color', 'role', 'start', 'end', 'axis_start', 'axis_end',
    'nominal_axis_start', 'nominal_axis_end', 'local_frame', 'arch_side',
    'arch_lane', 'arch_layer', 'arch_segment', 'arch_member_kind',
)


def macro_signature(part):
    return {key: part[key] for key in MACRO_KEYS if key in part}


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def sub(a, b):
    return [x-y for x, y in zip(a, b)]


def polygon_area_3d(points):
    # Newell's formula applies to the real planar XYZ ring, independent of
    # its orientation or the legacy member's source-section representation.
    area = [sum(a[(i+1) % 3]*b[(i+2) % 3] - a[(i+2) % 3]*b[(i+1) % 3]
                for a, b in zip(points, points[1:] + points[:1])) for i in range(3)]
    return sqrt(dot(area, area))/2


def piece_vertices(piece):
    if piece['kind'] == 'plate_loft':
        return [point for section in piece['sections'] for point in section]
    return [point for ring in [piece['outer'], *piece['holes']] for point in ring] + [
        [point[i] + piece['extrusion'][i] for i in range(3)]
        for ring in [piece['outer'], *piece['holes']] for point in ring]


def r09_reference_parameters():
    """Independent R08 controls plus the captured, explicit R09 opt-in."""
    p = deepcopy(TOKYO_R08_PARAMETERS)
    p['revision'] = 'LANDMARK-R09'
    p['detail']['lower_built_up'] = deepcopy(R09_LOWER_BUILT_UP)
    return p


def r09_reference_specs():
    from lib.tokyo_tower_builtup import refine_built_up
    return refine_built_up(r09_reference_parameters(), r08_reference_specs())


class TokyoTowerR09Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = r09_reference_parameters()
        cls.parts = r09_reference_specs()
        cls.by = {part['name']: part for part in cls.parts}
        cls.old = r08_reference_specs()
        cls.old_by = {part['name']: part for part in cls.old}

    def test_historical_r08_replay_matches_the_independently_captured_full_model(self):
        self.assertEqual(TOKYO_R08_PARAMETERS['revision'], 'LANDMARK-R08')
        self.assertEqual(len(self.old), 6485)
        self.assertEqual(geometry_fingerprint(self.old), R08_BASELINE['tokyo_specs_sha256'])
        self.assertEqual(R08_BASELINE['tokyo_specs_sha256'],
                         '312fa63c6e5d63d24c44b6b80558f84043e1572a0e9f1008c92604c9362cc85f')

    def test_historical_r09_replay_is_the_complete_independent_pre_r10_model(self):
        self.assertEqual(len(self.parts), 6485)
        self.assertEqual(geometry_fingerprint(self.parts), R09_BASELINE['tokyo_specs_sha256'])
        self.assertEqual(R09_BASELINE['tokyo_specs_sha256'],
                         'd6a80d6dd3d64f5e5e8fcaf0187d74100d7c86ebb1148972b617036caa93785f')

    def test_only_the_exact_1528_frozen_lower_member_names_can_change(self):
        self.assertEqual(len(R09_TARGET_NAMES), 1528)
        self.assertEqual(tuple(part['name'] for part in self.parts), TOKYO_R08_PART_NAMES)
        self.assertEqual(len(self.by), 6485)
        protected = [part for part in self.parts if part['name'] not in R09_TARGET_NAMES]
        self.assertEqual(len(protected), 4957)
        self.assertEqual(geometry_fingerprint(protected),
                         'cc238dc2baaa4fc93c23f1c7735c19eeb95b6796003569665b1c32c95ddb1229')
        for part in protected:
            self.assertEqual(geometry_fingerprint(part), TOKYO_R08_SPEC_SHA256_BY_NAME[part['name']], part['name'])

    def test_every_replaced_member_preserves_its_macro_axis_identity_and_orientation(self):
        targets = [part for part in self.parts if part['name'] in R09_TARGET_NAMES]
        self.assertEqual(len(targets), 1528)
        old_kinds = Counter(self.old_by[part['name']]['kind'] for part in targets)
        self.assertEqual(old_kinds, Counter(loft3d=464, beam=1064))
        for part in targets:
            self.assertEqual(part['kind'], 'built_up', part['name'])
            old = self.old_by[part['name']]
            expected = macro_signature(old)
            self.assertEqual(geometry_fingerprint({key: part[key] for key in expected}),
                             geometry_fingerprint(expected), part['name'])
            if old['kind'] == 'beam':
                self.assertEqual(part['axis_start'], old['start'], part['name'])
                self.assertEqual(part['axis_end'], old['end'], part['name'])

    def test_each_member_contains_bounded_real_plate_geometry_and_explicit_openings(self):
        families = set()
        hole_sides = Counter()
        for name in sorted(R09_TARGET_NAMES):
            part = self.by[name]
            self.assertEqual(part['kind'], 'built_up', name)
            families.add(part['built_up_family'])
            self.assertEqual(part['built_up_scope'], 'photo_guided_open_built_up_not_surveyed')
            frame = part['built_up_frame']
            for axis in ('u', 'v', 'normal'):
                self.assertAlmostEqual(dot(frame[axis], frame[axis]), 1., places=7, msg=name)
            for a, b in (('u', 'v'), ('u', 'normal'), ('v', 'normal')):
                self.assertAlmostEqual(dot(frame[a], frame[b]), 0., places=7, msg=name)
            old = self.old_by[name]
            axial_length = dist(part['axis_start'], part['axis_end'])
            self.assertGreaterEqual(frame['length_mm'] + .00001, axial_length, name)
            if old.get('steel_role') == 'arch_plate_chord':
                self.assertAlmostEqual(frame['length_mm'], axial_length + 80., places=5, msg=name)
            else:
                self.assertAlmostEqual(frame['length_mm'], axial_length, places=5, msg=name)
            self.assertGreater(frame['width_mm'], 0., name)
            self.assertGreater(frame['depth_mm'], 0., name)
            if old['kind'] == 'beam':
                self.assertEqual(frame['width_mm'], 2*old['radius'], name)
                self.assertEqual(frame['depth_mm'], min(1100., max(240., 4*old['radius'])), name)
            else:
                self.assertEqual(frame['width_mm'], old['section_profile']['width_mm'], name)
                self.assertEqual(frame['depth_mm'], old['section_profile']['depth_mm'], name)
            self.assertEqual(part['built_up_dimensions_status'], 'photo_guided_demonstration_assumption')
            self.assertTrue(4 <= len(part['pieces']) <= 24, name)
            self.assertEqual(len({piece['piece_id'] for piece in part['pieces']}), len(part['pieces']), name)
            pierced = []
            for piece in part['pieces']:
                self.assertIn(piece['kind'], ('perforated_plate', 'plate_loft'), (name, piece['piece_id']))
                if piece['kind'] == 'plate_loft':
                    self.assertEqual(len(piece['sections']), 2)
                    self.assertTrue(all(len(section) == 4 for section in piece['sections']))
                    self.assertTrue(all(polygon_area_3d(section) > 0 for section in piece['sections']))
                    continue
                outer = piece['outer']
                self.assertGreaterEqual(len(outer), 4)
                self.assertGreater(polygon_area_3d(outer), 0.)
                extrusion = piece['extrusion']
                thickness = sqrt(dot(extrusion, extrusion))
                self.assertGreater(thickness, 0.)
                self.assertLess(thickness, min(frame['width_mm'], frame['depth_mm'])/2)
                normal = [value/thickness for value in extrusion]
                for ring in [outer, *piece['holes']]:
                    self.assertTrue(all(len(point) == 3 and all(isfinite(value) for value in point) for point in ring))
                    self.assertTrue(all(abs(dot(sub(point, outer[0]), normal)) < .00001 for point in ring))
                self.assertLess(sum(polygon_area_3d(hole) for hole in piece['holes']), polygon_area_3d(outer))
                for hole in piece['holes']:
                    self.assertIn(len(hole), (3, 4))
                    self.assertGreater(polygon_area_3d(hole), 0.)
                    hole_sides[len(hole)] += 1
                if piece['holes']:
                    pierced.append(piece)
                    probe = piece['void_probe_mm']
                    self.assertEqual(len(probe), 3)
                    self.assertTrue(all(isfinite(value) for value in probe))
            self.assertGreaterEqual(len(pierced), 2, name)
        self.assertEqual(families, {'battened', 'laced'})
        self.assertGreater(hole_sides[3], 0)
        self.assertGreater(hole_sides[4], 0)

    def test_built_up_pass_requires_opt_in_and_keeps_its_inputs_private(self):
        from lib.tokyo_tower_builtup import refine_built_up
        source = deepcopy(self.old)
        self.assertEqual(refine_built_up(TOKYO_R08_PARAMETERS, source), self.old)
        for setting in ({'enabled': False},):
            p = deepcopy(TOKYO_R08_PARAMETERS)
            p['detail']['lower_built_up'] = setting
            self.assertEqual(refine_built_up(p, source), self.old)
        before = geometry_fingerprint(source)
        refined = refine_built_up(self.p, source)
        self.assertEqual(geometry_fingerprint(source), before)
        self.assertEqual(geometry_fingerprint(refined), geometry_fingerprint(self.parts))

    def test_actual_plate_vertices_keep_the_recorded_envelope_and_r08_primary_bounds(self):
        for name in sorted(R09_TARGET_NAMES):
            part = self.by[name]
            frame = part['built_up_frame']
            vertices = [point for piece in part['pieces'] for point in piece_vertices(piece)]
            limits = ((-frame['width_mm']/2, frame['width_mm']/2),
                      (-frame['depth_mm']/2, frame['depth_mm']/2), (0., frame['length_mm']))
            for key, expected in zip(('u', 'v', 'normal'), limits):
                projected = [dot(sub(point, frame['origin_mm']), frame[key]) for point in vertices]
                self.assertAlmostEqual(min(projected), expected[0], delta=.00001, msg=(name, key))
                self.assertAlmostEqual(max(projected), expected[1], delta=.00001, msg=(name, key))
            old = self.old_by[name]
            if old['kind'] == 'loft3d':
                original = [point for section in old['sections'] for point in section]
                for axis in range(3):
                    self.assertAlmostEqual(min(point[axis] for point in vertices), min(point[axis] for point in original),
                                           delta=.00001, msg=(name, axis, 'min'))
                    self.assertAlmostEqual(max(point[axis] for point in vertices), max(point[axis] for point in original),
                                           delta=.00001, msg=(name, axis, 'max'))

    def test_malformed_piece_controls_are_rejected_before_native_export(self):
        from lib.tokyo_tower_builtup import refine_built_up
        for override in ({'enabled': 'yes'}, {'cover_thickness_mm': True},
                         {'web_thickness_mm': 0}, {'pitch_depth_ratio': float('inf')},
                         {'min_cells': 2.5}, {'max_cells': 25}, {'max_pieces_per_member': 25}):
            p = deepcopy(self.p)
            p['detail']['lower_built_up'].update(override)
            with self.subTest(override=override), self.assertRaises(ValueError):
                refine_built_up(p, self.old)

    def test_all_twenty_selected_nodes_and_their_296_named_parts_stay_exact(self):
        nodes = [part for part in self.parts if part.get('steel_node_id')]
        self.assertEqual(len(nodes), 296)
        self.assertEqual({part['steel_node_id'] for part in nodes}, {f'TT-N{i:02d}' for i in range(1, 21)})
        self.assertEqual(geometry_fingerprint(nodes),
                         '5f4990ab9a04587b34d7bf2b7134e5a6a0adcfa00c265673cfaac2e6048d8842')

    def test_equipment_upper_frame_decks_core_and_antenna_keep_their_r08_specs(self):
        equipment = [self.by[name] for name in R08_BASELINE['equipment_names']]
        self.assertEqual(len(equipment), 111)
        self.assertEqual(geometry_fingerprint(equipment), R08_BASELINE['equipment_specs_sha256'])
        mounted = [self.by[name] for name in R08_BASELINE['equipment_mount_names']]
        self.assertEqual(len(mounted), 42)
        self.assertEqual(geometry_fingerprint(mounted), R08_BASELINE['equipment_mount_specs_sha256'])
        for part in self.parts:
            if part['group'] in ('decks', 'core', 'antenna') or part['name'].startswith('structure:upper_'):
                self.assertEqual(geometry_fingerprint(part), TOKYO_R08_SPEC_SHA256_BY_NAME[part['name']], part['name'])
        self.assertEqual(self.p['profile'], TOKYO_R08_PARAMETERS['profile'])
        self.assertEqual(self.p['detail']['upper_shaft_outline'], TOKYO_R08_PARAMETERS['detail']['upper_shaft_outline'])

    def test_skytree_parameters_and_every_spec_remain_the_same_control(self):
        sky = component_specs('tokyo-skytree')
        self.assertEqual(len(sky), 7649)
        self.assertEqual(geometry_fingerprint(sky), R08_BASELINE['skytree_specs_sha256'])
        self.assertEqual(geometry_fingerprint(TOWERS['tokyo-skytree']), R08_BASELINE['skytree_parameters_sha256'])


class TokyoTowerR09NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from cadgen import build123d as bd
        cls.bd = bd
        cls.parts = r09_reference_specs()
        cls.by = {part['name']: part for part in cls.parts}
        cls.cache = {}

    def shape(self, name):
        if name not in self.cache:
            shape = _cad_shape(self.by[name], self.bd)
            solids = list(shape.solids())
            self.assertTrue(solids, name)
            self.assertTrue(all(solid.is_valid and isfinite(solid.volume) and solid.volume > 0 for solid in solids), name)
            if name in R09_TARGET_NAMES:
                self.assertEqual(len(solids), 1, name)
            self.cache[name] = shape
        return self.cache[name]

    def contact(self, one, two):
        a, b = self.shape(one), self.shape(two)
        self.assertLess(a.distance_to(b), .01, (one, two))
        common = a.intersect(b)
        self.assertIsNotNone(common, (one, two))
        self.assertGreater(sum(solid.volume for solid in common.solids()), 1., (one, two))

    def test_real_plate_openings_remain_empty_in_representative_complete_members(self):
        names = (
            'structure:leg_01_chord_00_01',
            'structure:leg_01_chord_00_08',
            'structure:lower_arch_0_0_7',
            'structure:lower_arch_inner_0_0_0',
            'structure:leg_01_web_0_01',
            'structure:leg_01_tie_0_01',
            'structure:lower_belt_0_0',
            'structure:lower_panel_a_0_0_0',
            'structure:lower_panel_vertical_0_0_1',
            'structure:arch_spandrel_tie_0_-1_0',
            'structure:lower_arch_diagonal_0_0_7',
            'structure:lower_arch_inplane_tie_0_0_8',
            'structure:lower_arch_web_0_8',
        )
        kinds = set()
        families = set()
        for name in names:
            part = self.by[name]
            self.assertEqual(part['kind'], 'built_up', name)
            solid = self.shape(name)
            families.add(part['built_up_family'])
            pierced = [piece for piece in part['pieces'] if piece['kind'] == 'perforated_plate' and piece['holes']]
            self.assertGreaterEqual(len(pierced), 2, name)
            for piece in pierced:
                kinds.update(len(hole) for hole in piece['holes'])
                # Test the complete assembled member, not just the perforated
                # face; another plate must not silently fill the recorded void.
                probe = self.bd.Solid.make_sphere(.5, self.bd.Plane(origin=tuple(piece['void_probe_mm'])))
                common = solid.intersect(probe)
                volume = sum(item.volume for item in common.solids()) if common is not None else 0.
                self.assertLess(volume, .000001, (name, piece['piece_id']))
        self.assertEqual(families, {'battened', 'laced'})
        self.assertEqual(kinds, {3, 4})

    def test_cad_drawing_triangles_preserve_both_real_rectangle_and_triangle_openings(self):
        from lib.tokyo_tower_builtup import faces
        for name in ('structure:leg_01_chord_00_01', 'structure:lower_arch_0_0_7'):
            part = self.by[name]
            pierced = [piece for piece in part['pieces'] if piece['kind'] == 'perforated_plate' and piece['holes']]
            self.assertEqual(len(pierced), 2, name)
            for piece in pierced:
                scoped = deepcopy(part)
                scoped['pieces'] = [piece]
                triangles = faces(scoped)
                self.assertTrue(triangles)
                self.assertTrue(all(len(face) == 3 for face in triangles))
                extrusion = piece['extrusion']
                thickness = sqrt(dot(extrusion, extrusion))
                normal = [value/thickness for value in extrusion]
                expected = polygon_area_3d(piece['outer']) - sum(polygon_area_3d(hole) for hole in piece['holes'])
                for depth in (0., thickness):
                    caps = [triangle for triangle in triangles if all(
                        abs(dot(sub(point, piece['outer'][0]), normal) - depth) < .00001 for point in triangle)]
                    self.assertTrue(caps, (name, piece['piece_id'], depth))
                    self.assertAlmostEqual(sum(polygon_area_3d(triangle) for triangle in caps), expected,
                                           delta=max(.01, expected*.0000001), msg=(name, piece['piece_id'], depth))

    def test_all_sixteen_arch_anchors_and_four_crown_bridges_contact_both_hosts(self):
        anchors = [part for part in self.parts if part['name'].startswith('structure:lower_arch_anchor_')]
        bridges = [part for part in self.parts if part['name'].startswith('structure:arch_spandrel_crown_bridge_')]
        self.assertEqual(len(anchors), 16)
        self.assertEqual(len(bridges), 4)
        for part in anchors + bridges:
            for key in ('source_member', 'target_member'):
                with self.subTest(part=part['name'], host=part[key]):
                    self.contact(part['name'], part[key])

    def test_all_112_continuation_links_have_positive_contact_at_both_ends(self):
        links = [part for part in self.parts if part.get('role') == 'leg_transition_link']
        self.assertEqual(len(links), 112)
        for part in links:
            for key in ('source_member', 'target_member'):
                with self.subTest(part=part['name'], host=part[key]):
                    self.contact(part['name'], part[key])

    def test_all_twenty_lower_node_plate_contacts_survive_the_changed_member_construction(self):
        plates = [part for part in self.parts if part.get('steel_node_id')
                  and part.get('contact_with') in R09_TARGET_NAMES]
        self.assertEqual(len(plates), 20)
        self.assertEqual({part['steel_node_id'] for part in plates}, {f'TT-N{i:02d}' for i in range(1, 17)})
        for part in plates:
            with self.subTest(part=part['name'], host=part['contact_with']):
                self.contact(part['name'], part['contact_with'])

    def test_all_42_protected_upper_equipment_mounts_still_contact_their_hosts(self):
        parts = [self.by[name] for name in R08_BASELINE['equipment_mount_names']]
        self.assertEqual(len(parts), 42)
        for part in parts:
            for host in part['host_members']:
                with self.subTest(part=part['name'], host=host):
                    self.contact(part['name'], host)


if __name__ == '__main__':
    unittest.main()
