"""R08 appearance changes against an independent, frozen R07 control set."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from math import dist, inf, isfinite, nextafter
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from checks.tokyo_tower_r07_baseline import R07_BASELINE, TOKYO_R07_PARAMETERS
from checks.tokyo_tower_r08_baseline import R08_BASELINE, TOKYO_R08_PARAMETERS
from lib.tower_geometry import TOWERS, _tower_paint, component_specs
from lib.tokyo_tower_detail import (_base_config, _leg_cage_half, _leg_frame_levels,
                                   _square, body_radius, component_specs as appearance_specs)
from lib.tokyo_tower_steel import refine_steel

MUTABLE_FRAMING_NAMES = frozenset(R07_BASELINE['mutable_framing_names'])
MUTABLE_NODE_NAMES = frozenset(R07_BASELINE['mutable_node_part_names'])
EQUIPMENT_ROLES = frozenset('upper_equipment_' + name for name in
                          ('outrigger', 'stay', 'crossbar', 'service_floor', 'guard', 'radome', 'mount', 'feed'))


def geometry_fingerprint(value):
    """10 nm grid: retain identifiers/metadata exactly, tolerate libm tails."""
    def canonical(item):
        if isinstance(item, float):
            if not isfinite(item):
                raise ValueError('Nonfinite R08 reference geometry.')
            return round(item, 5) or 0.
        if isinstance(item, dict):
            return {key: canonical(v) for key, v in item.items()}
        if isinstance(item, (list, tuple)):
            return [canonical(v) for v in item]
        return item
    return hashlib.sha256(json.dumps(canonical(value), sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def r07_reference_specs():
    """Replay archived controls; a fixed full hash below validates the replay."""
    p = deepcopy(TOKYO_R07_PARAMETERS)
    return refine_steel(p, appearance_specs(p, lambda z: _square(body_radius(p, z)), _tower_paint))


def r08_reference_specs():
    """Replay pre-R09 controls, independently bound to all 6485 frozen specs.

    The later built-up-member pass is opt-in. These captured R08 controls do
    not enable it; the full digest test prevents a changed legacy default
    from silently redefining the historical H/I and secondary-member guards.
    """
    p = deepcopy(TOKYO_R08_PARAMETERS)
    return refine_steel(p, appearance_specs(p, lambda z: _square(body_radius(p, z)), _tower_paint))


def r08_mutable_framing(part):
    return part['name'] in MUTABLE_FRAMING_NAMES


def r08_hosted_steel_detail(part):
    return part['name'] in MUTABLE_NODE_NAMES


def r08_new_equipment(part):
    return (part['group'] == 'structure' and part['name'].startswith('structure:upper_equipment_')
            and part.get('role') in EQUIPMENT_ROLES)


def r08_protected_specs(specs):
    return [part for part in specs if not (r08_mutable_framing(part)
                                          or r08_hosted_steel_detail(part)
                                          or r08_new_equipment(part))]


def projection(parts, keys):
    return [{key: part[key] for key in keys if key in part} for part in parts]


def axis_distance(point, a, b):
    delta = [b[k] - a[k] for k in range(3)]
    t = max(0., min(1., sum((point[k] - a[k]) * delta[k] for k in range(3)) / sum(v*v for v in delta)))
    return dist(point, [a[k] + t * delta[k] for k in range(3)])


def bounds_z(part):
    if part['kind'] == 'beam':
        return min(part['start'][2], part['end'][2]) - part['radius'], max(part['start'][2], part['end'][2]) + part['radius']
    if part['kind'] == 'box':
        return part['bounds'][2], part['bounds'][5]
    if part['kind'] == 'loft3d':
        values = [q[2] for section in part['sections'] for q in section]
    else:
        values = [section['z'] for section in part['sections']]
    return min(values), max(values)


class TokyoTowerR08Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = TOWERS['tokyo-tower']
        cls.parts = r08_reference_specs()
        cls.by = {part['name']: part for part in cls.parts}
        cls.current_parts = component_specs('tokyo-tower')
        cls.current_by = {part['name']: part for part in cls.current_parts}
        cls.old = r07_reference_specs()
        cls.old_by = {part['name']: part for part in cls.old}

    def test_archived_replay_is_the_frozen_independent_r07_not_current_geometry(self):
        self.assertEqual(R07_BASELINE['source_commit'], 'fa20614b5b4ceb3d37b0e60f08ae2c553c04b90c')
        self.assertEqual(len(self.old), 6374)
        self.assertEqual(geometry_fingerprint(self.old), R07_BASELINE['tokyo_specs_sha256'])
        self.assertEqual(R07_BASELINE['tokyo_specs_sha256'], '955b957cdc20dbdebc2773f5197853bd454b6e421972d71ab41c5a2665b6f2bc')

    def test_archived_r08_replay_remains_the_complete_pre_r09_control_set(self):
        self.assertEqual(TOKYO_R08_PARAMETERS['revision'], 'LANDMARK-R08')
        self.assertEqual(len(self.parts), 6485)
        self.assertEqual(geometry_fingerprint(self.parts), R08_BASELINE['tokyo_specs_sha256'])
        self.assertEqual(R08_BASELINE['tokyo_specs_sha256'], '312fa63c6e5d63d24c44b6b80558f84043e1572a0e9f1008c92604c9362cc85f')

    def test_only_explicit_framing_hosts_and_separate_fittings_can_change(self):
        legacy = [part for part in self.parts if not r08_new_equipment(part)]
        self.assertEqual(len(legacy), 6374)
        self.assertEqual(geometry_fingerprint([part['name'] for part in legacy]), R07_BASELINE['tokyo_name_sha256'])
        protected = r08_protected_specs(self.parts)
        self.assertEqual(len(protected), 4814)
        self.assertEqual(geometry_fingerprint(protected), R07_BASELINE['protected_specs_sha256'])
        self.assertEqual(R07_BASELINE['protected_specs_sha256'], '833fbb9b8853dcc1e93608f5deed69b83c5da4e3840c78f90ee5360ff75a1dcb')
        framing = [part for part in self.parts if r08_mutable_framing(part)]
        self.assertEqual(len(framing), 1384)
        self.assertEqual(geometry_fingerprint(projection(framing, R07_BASELINE['framing_axis_keys'])), R07_BASELINE['framing_axes_sha256'])

    def test_only_twelve_hosted_node_families_follow_the_smaller_sections(self):
        details = [part for part in self.parts if r08_hosted_steel_detail(part)]
        self.assertEqual(len(details), 176)
        self.assertEqual({part['steel_node_id'] for part in details}, {f'TT-N{i:02d}' for i in range(5, 17)})
        self.assertEqual(geometry_fingerprint(projection(details, R07_BASELINE['node_identity_keys'])), R07_BASELINE['mutable_node_identity_sha256'])
        for part in self.parts:
            if part.get('steel_node_id') in R07_BASELINE['protected_base_node_ids']:
                self.assertEqual(part, self.old_by[part['name']])

    def test_leg_and_arch_sections_shrink_without_moving_their_axes(self):
        legs = [part for part in self.parts if r08_mutable_framing(part) and part.get('role') == 'primary_chord']
        self.assertEqual(len(legs), 208)
        for part in legs:
            profile = part['section_profile']; old = self.old_by[part['name']]['section_profile']
            for key in ('width_mm', 'depth_mm'):
                self.assertAlmostEqual(profile[key], old[key] * .70, places=6, msg=part['name'])
                self.assertGreater(profile[key], 0)
            self.assertLess(profile['web_thickness_mm'], profile['width_mm'])
            self.assertLess(2 * profile['flange_thickness_mm'], profile['depth_mm'])
        arches = [part for part in self.parts if part.get('steel_role') == 'arch_plate_chord']
        self.assertEqual(len(arches), 256)
        for part in arches:
            self.assertEqual(part['section_profile'], {'type': 'H', 'width_mm': 320., 'depth_mm': 420.,
                                                      'web_thickness_mm': 16., 'flange_thickness_mm': 20.})

    def test_secondary_braces_keep_a_finer_section_hierarchy(self):
        for part in self.parts:
            if not r08_mutable_framing(part) or part['kind'] != 'beam':
                continue
            name = part['name']
            if part.get('role') == 'leg_brace':
                expected = 95.
            elif part.get('role') == 'leg_tie':
                expected = 110.
            elif name.startswith('structure:arch_spandrel_tie_'):
                expected = 90.
            elif name.startswith('structure:arch_spandrel_diagonal_'):
                expected = 75.
            elif name.startswith('structure:lower_arch_diagonal_'):
                expected = 60.
            elif name.startswith('structure:lower_arch_inplane_tie_'):
                expected = 48.
            else:
                expected = 55.
            self.assertEqual(part['radius'], expected, name)
            self.assertLess(part['radius'], self.old_by[name]['radius'], name)

    def test_foot_axes_crown_and_smooth_main_shaft_controls_are_retained(self):
        c = _base_config(self.p)
        self.assertEqual(_leg_frame_levels(self.p), _leg_frame_levels(TOKYO_R07_PARAMETERS))
        for z in range(0, 125001, 250):
            self.assertEqual(_leg_cage_half(self.p, z), _leg_cage_half(TOKYO_R07_PARAMETERS, z))
        self.assertEqual(self.p['profile'], TOKYO_R07_PARAMETERS['profile'])
        self.assertEqual(self.p['detail']['upper_shaft_outline'], TOKYO_R07_PARAMETERS['detail']['upper_shaft_outline'])
        self.assertEqual((self.p['detail']['arch_crown_mm'], c['arch_rib_depth_mm'], c['arch_plane_half_depth_mm'], c['arch_panel_count']),
                         (40000., 1800., 650., 16))

    def test_skytree_parameters_and_every_named_spec_remain_exact(self):
        parts = component_specs('tokyo-skytree')
        self.assertEqual(len(parts), R07_BASELINE['skytree_part_count'])
        self.assertEqual(geometry_fingerprint(parts), R07_BASELINE['skytree_specs_sha256'])
        self.assertEqual(geometry_fingerprint(TOWERS['tokyo-skytree']), R07_BASELINE['skytree_parameters_sha256'])

    def test_new_fittings_have_a_bounded_inventory_and_photo_fit_scope(self):
        new = [part for part in self.current_parts if r08_new_equipment(part)]
        self.assertEqual(len(new), 111)
        self.assertEqual([part['name'] for part in new], R08_BASELINE['equipment_names'])
        self.assertEqual(geometry_fingerprint(new), R08_BASELINE['equipment_specs_sha256'])
        self.assertEqual(Counter(part['role'] for part in new), Counter({
            'upper_equipment_stay': 23, 'upper_equipment_service_floor': 20,
            'upper_equipment_outrigger': 19, 'upper_equipment_mount': 19,
            'upper_equipment_crossbar': 16, 'upper_equipment_guard': 8,
            'upper_equipment_radome': 3, 'upper_equipment_feed': 3}))
        decks = {deck['id']: deck for deck in self.p['deck_specs']}
        for part in new:
            self.assertEqual(part['dimensions_status'], 'photo_guided_appearance_assumption')
            self.assertEqual(part['equipment_inventory_status'], 'operator_photo_reference_date_and_current_inventory_unverified')
            self.assertEqual(part['source_reference'], 'https://www.tokyotower.co.jp/plan/towerpedia/')
            self.assertEqual(part['source_photo'], 'https://www.tokyotower.co.jp/plan/towerpedia/img/img_006.jpg')
            self.assertIn('not measured', part['scope'])
            self.assertFalse(any(key in part for key in ('broadcaster', 'channel', 'frequency_mhz')))
            low, high = bounds_z(part)
            self.assertGreater(low, decks['main']['top_mm'])
            self.assertLess(high, decks['top']['bottom_mm'])

    def test_direct_mounts_follow_actual_named_straight_chords(self):
        mounted = [part for part in self.current_parts if r08_new_equipment(part) and part.get('host_members')]
        self.assertEqual(len(mounted), 42)
        for part in mounted:
            self.assertEqual(len(part['host_members']), len(part['attachment_points']))
            self.assertEqual(part['mount_overlap_mm'], 180.)
            for name, point in zip(part['host_members'], part['attachment_points']):
                host = self.current_by[name]
                self.assertTrue(name.startswith('structure:upper_chord_'))
                self.assertLess(axis_distance(point, host['axis_start'], host['axis_end']), .00001, part['name'])
                self.assertEqual(host, self.old_by[name])
            host_r = max(abs(v) for v in part['attachment_points'][0][:2])
            self.assertGreater(max(abs(v) for v in part['end'][:2]), host_r + 500, part['name'])

    def test_equipment_requires_opt_in_and_rejects_invalid_fitted_controls(self):
        from lib.tokyo_tower_equipment import UPPER_EQUIPMENT_DEFAULTS, upper_equipment_specs
        radius = lambda z: 5000.
        self.assertEqual(upper_equipment_specs(TOKYO_R07_PARAMETERS, radius), [])
        for override in ({'enabled': False},):
            p = deepcopy(TOKYO_R07_PARAMETERS); p['detail']['upper_equipment'] = override
            self.assertEqual(upper_equipment_specs(p, radius), [])
        for override in ({'enabled': 'yes'}, {'tiers_mm': [180000., 170000.]},
                         {'projections_mm': [6000.] * 4}, {'gallery_height_mm': 230000.},
                         {'radomes': [{'height_mm': 146000., 'face': 4, 'corner': -1, 'diameter_mm': 1600., 'projection_mm': 1500.}]}):
            p = deepcopy(TOKYO_R07_PARAMETERS); p['detail']['upper_equipment'] = {**deepcopy(UPPER_EQUIPMENT_DEFAULTS), **override}
            with self.subTest(override=override), self.assertRaises(ValueError):
                upper_equipment_specs(p, radius)

    def test_frozen_checks_tolerate_machine_tails_but_reject_meaningful_axis_changes(self):
        def perturb(item, direction):
            if isinstance(item, float):
                for _ in range(8):
                    item = nextafter(item, direction)
                return item
            if isinstance(item, dict):
                return {key: perturb(value, direction) for key, value in item.items()}
            if isinstance(item, (list, tuple)):
                return [perturb(value, direction) for value in item]
            return item
        for reference in (self.old, r08_protected_specs(self.old),
                          projection([part for part in self.old if r08_mutable_framing(part)], R07_BASELINE['framing_axis_keys'])):
            expected = geometry_fingerprint(reference)
            for direction in (inf, -inf):
                self.assertEqual(geometry_fingerprint(perturb(reference, direction)), expected)
        point = {'name': 'structure:reference', 'axis_start': [1000.123456, 0., 180000.]}
        expected = geometry_fingerprint(point)
        for direction in (inf, -inf):
            changed = deepcopy(point)
            for _ in range(8):
                changed['axis_start'][0] = nextafter(changed['axis_start'][0], direction)
            self.assertEqual(geometry_fingerprint(changed), expected)
        changed = deepcopy(point); changed['axis_start'][0] += .001
        self.assertNotEqual(geometry_fingerprint(changed), expected)


class TokyoTowerR08NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from cadgen import build123d as bd
        from lib.tower_geometry import _cad_shape
        cls.bd = bd; cls.make = staticmethod(_cad_shape)
        cls.by = {part['name']: part for part in component_specs('tokyo-tower')}
        cls.cache = {}

    def shape(self, name):
        if name not in self.cache:
            shape = self.make(self.by[name], self.bd)
            self.assertTrue(shape.is_valid, name)
            self.assertGreater(shape.volume, 0, name)
            self.cache[name] = shape
        return self.cache[name]

    def contact(self, one, two):
        a, b = self.shape(one), self.shape(two)
        self.assertLess(a.distance_to(b), .01, (one, two))
        common = a.intersect(b)
        self.assertIsNotNone(common, (one, two))
        self.assertGreater(sum(s.volume for s in common.solids()), 1., (one, two))

    def test_all_forty_two_new_direct_mounts_have_positive_host_contact(self):
        mounted = [part for part in self.by.values() if r08_new_equipment(part) and part.get('host_members')]
        self.assertEqual(len(mounted), 42)
        for part in mounted:
            for host in part['host_members']:
                with self.subTest(part=part['name'], host=host):
                    self.contact(part['name'], host)

    def test_circular_covers_are_valid_and_connected_to_their_short_mounts(self):
        covers = [part for part in self.by.values() if part.get('role') == 'upper_equipment_radome']
        self.assertEqual(len(covers), 3)
        for part in covers:
            self.contact(part['name'], part['name'].replace('_cover', '_feed'))
            self.contact(part['name'], part['name'].replace('_cover', '_post'))


if __name__ == '__main__':
    unittest.main()
