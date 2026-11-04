"""Whole-leg and whole-arch assemblies against the independent R09 snapshot."""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from math import dist, isfinite
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from checks.tokyo_tower_r09_baseline import R09_BASELINE, TOKYO_R09_SPEC_SHA256_BY_NAME
from checks.tokyo_tower_r10_baseline import R10_BASELINE, R10_INTEGRATED_LOWER
from checks.test_tokyo_tower_r09 import r09_reference_specs, r09_reference_parameters, piece_vertices, dot, sub
from checks.test_tokyo_tower_r08 import geometry_fingerprint
from lib.tower_geometry import TOWERS, component_specs, geometry_manifest, _cad_shape


REPLACED_NAMES = frozenset(R09_BASELINE['replaced_names'])
REFERENCE_KEYS = ('contact_with', 'source_member', 'target_member', 'member_names')


def expected_aliases():
    """Only pre-R10 frozen names determine the allowed material replacement."""
    result = {}
    for name in sorted(REPLACED_NAMES):
        leg = re.fullmatch(r'structure:leg_(0[1-4])_(?:chord_0[0-3]|web_[0-3]|tie_[0-3])_(\d{2})', name)
        if leg:
            result[name] = f'structure:leg_{leg[1]}_assembly_{leg[2]}'
            continue
        segment = re.fullmatch(r'structure:lower_arch_(?:inner_)?([0-3])_[01]_(\d+)', name)
        if not segment:
            segment = re.fullmatch(r'structure:lower_arch_(?:diagonal|inplane_tie)_([0-3])_[01]_(\d+)', name)
        if not segment:
            segment = re.fullmatch(r'structure:lower_arch_(?:inner_)?web_([0-3])_(\d+)', name)
        if not segment:
            raise AssertionError(f'Unrecognised frozen R09 material: {name}')
        result[name] = f'structure:arch_assembly_{segment[1]}_{min(int(segment[2]),15):02d}'
    return result


ALIASES = expected_aliases()
NEW_NAMES = frozenset(ALIASES.values())


def remap_references(part):
    expected = deepcopy(part)
    for key in REFERENCE_KEYS:
        value = expected.get(key)
        if isinstance(value, str):
            expected[key] = ALIASES.get(value, value)
        elif isinstance(value, list):
            expected[key] = list(dict.fromkeys(ALIASES.get(name, name) for name in value)) if key=='member_names' else [ALIASES.get(name, name) for name in value]
    return expected


def rotated_cloud(points, quarter_turns):
    result=[]
    for point in points:
        x,y,z=point
        for _ in range(quarter_turns):x,y=-y,x
        result.append(tuple(round(v,4) or 0. for v in (x,y,z)))
    return tuple(sorted(result))


def material_surfaces(part, quarter_turns=0, *, holes=False):
    surfaces=[]
    for piece in part['pieces']:
        function=piece.get('member_function')
        if function=='gross_continuous_cover':
            points=[p for section in piece['sections'] for p in section]
            surfaces.append(('cover',rotated_cloud(points,quarter_turns)))
        elif function=='gross_open_side_web':
            loops=piece['holes'] if holes else [piece['outer']]
            for loop in loops:
                surfaces.append(('web',rotated_cloud(loop+[
                    [point[i]+piece['extrusion'][i] for i in range(3)] for point in loop],quarter_turns)))
    return sorted(surfaces)


def r10_reference_parameters():
    p=r09_reference_parameters()
    p['revision']='LANDMARK-R10'
    p['detail']['integrated_lower']=deepcopy(R10_INTEGRATED_LOWER)
    return p


def r10_reference_specs():
    from lib.tokyo_tower_integrated import refine_integrated
    return refine_integrated(r10_reference_parameters(),r09_reference_specs())


def r10_reference_node_catalog():
    from lib.tokyo_tower_integrated import remap_node_catalog
    from lib.tokyo_tower_steel import node_catalog
    from lib.tokyo_tower_detail import component_specs as appearance_specs,_square,body_radius
    from lib.tower_geometry import _tower_paint
    p=r10_reference_parameters()
    return remap_node_catalog(node_catalog(p,appearance_specs(p,lambda z:_square(body_radius(p,z)),_tower_paint)),r10_reference_specs())


class TokyoTowerR10Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = r10_reference_parameters()
        cls.parts = r10_reference_specs()
        cls.by = {part['name']: part for part in cls.parts}
        cls.old = r09_reference_specs()
        cls.old_by = {part['name']: part for part in cls.old}

    def test_historical_r10_replay_is_the_complete_independent_pre_r11_model(self):
        self.assertEqual(len(self.parts),5337)
        self.assertEqual(geometry_fingerprint(self.parts),R10_BASELINE['tokyo_specs_sha256'])
        self.assertEqual(R10_BASELINE['tokyo_specs_sha256'],'29db95d4ad44eb35042f2143a194a8a51eaae704114cbf428dd65e09820c5c0f')

    def test_independent_r09_replay_is_not_redefined_by_current_r10_controls(self):
        self.assertEqual(len(self.old), 6485)
        self.assertEqual(geometry_fingerprint(self.old), R09_BASELINE['tokyo_specs_sha256'])
        self.assertEqual(R09_BASELINE['tokyo_specs_sha256'],
                         'd6a80d6dd3d64f5e5e8fcaf0187d74100d7c86ebb1148972b617036caa93785f')

    def test_exact_material_replacement_has_52_legs_64_arches_and_no_duplicate_old_members(self):
        self.assertEqual(len(REPLACED_NAMES), 1264)
        self.assertEqual(len(NEW_NAMES), 116)
        expected_names = (set(R09_BASELINE['tokyo_part_names']) - REPLACED_NAMES) | NEW_NAMES
        self.assertEqual(set(self.by), expected_names)
        self.assertEqual(len(self.parts), 5337)
        self.assertEqual(len(self.parts), len(self.by))
        assemblies = [self.by[name] for name in sorted(NEW_NAMES)]
        self.assertEqual(Counter(part['role'] for part in assemblies), Counter(leg_assembly=52, arch_assembly=64))
        consumed = []
        for part in assemblies:
            expected = {name for name, target in ALIASES.items() if target == part['name']}
            self.assertEqual(set(part['replaces_names']), expected, part['name'])
            self.assertEqual(len(part['replaces_names']), len(expected), part['name'])
            consumed.extend(part['replaces_names'])
            self.assertEqual(part['legacy_aliases'], {name: part['name'] for name in expected}, part['name'])
        self.assertEqual(Counter(consumed), Counter(REPLACED_NAMES))
        self.assertFalse(REPLACED_NAMES & set(self.by))

    def test_all_5221_retained_specs_only_change_explicit_alias_references(self):
        protected = [part for part in self.old if part['name'] not in REPLACED_NAMES]
        self.assertEqual(len(protected), 5221)
        self.assertEqual(geometry_fingerprint(protected), R09_BASELINE['protected_specs_sha256'])
        for part in protected:
            self.assertEqual(geometry_fingerprint(part), TOKYO_R09_SPEC_SHA256_BY_NAME[part['name']])
            self.assertEqual(geometry_fingerprint(self.by[part['name']]), geometry_fingerprint(remap_references(part)), part['name'])

    def test_every_legacy_axis_and_attachment_remains_traceable_to_real_integrated_material(self):
        for name in sorted(NEW_NAMES):
            part = self.by[name]
            self.assertEqual(part['kind'], 'built_up', name)
            expected = {}
            for old_name in part['replaces_names']:
                old = self.old_by[old_name]
                expected[old_name] = {'axis_start': old.get('axis_start', old.get('start')),
                                      'axis_end': old.get('axis_end', old.get('end'))}
            self.assertEqual(part['legacy_member_axes'], expected, name)
        for part in self.parts:
            for key in REFERENCE_KEYS:
                value = part.get(key)
                for referenced in value if isinstance(value, list) else [value] if isinstance(value, str) else []:
                    self.assertIn(referenced, self.by, (part['name'], key, referenced))

    def test_new_assemblies_have_gross_width_webs_not_four_repeated_small_girders(self):
        for name in sorted(NEW_NAMES):
            part = self.by[name]
            self.assertTrue(part['pieces'], name)
            self.assertGreater(dist(part['axis_start'], part['axis_end']), 0., name)
            old_chords = [self.old_by[old] for old in part['replaces_names']
                          if self.old_by[old].get('role') == 'primary_chord'
                          or self.old_by[old].get('steel_role') == 'arch_plate_chord']
            self.assertEqual(len(old_chords), 4, name)
            individual_width = max(max(old['built_up_frame'][key] for key in ('width_mm','depth_mm')) for old in old_chords)
            axis = sub(part['axis_end'],part['axis_start'])
            length = dist(part['axis_start'],part['axis_end'])
            normal = [value/length for value in axis]
            required_span=2*individual_width
            if part['role']=='arch_assembly':
                # The inherited outer/inner curves meet at the arch foot.
                # A fixed mid-arch width would reject that genuine taper;
                # bind width instead to the independent R09 curve separation.
                separations=[]
                for endpoint in ('axis_start','axis_end'):
                    outer=[old[endpoint] for old in old_chords if old['arch_layer']=='outer']
                    inner=[old[endpoint] for old in old_chords if old['arch_layer']=='inner']
                    delta=[sum(p[i] for p in outer)/2-sum(p[i] for p in inner)/2 for i in range(3)]
                    projected=[delta[i]-normal[i]*dot(delta,normal) for i in range(3)]
                    separations.append(dot(projected,projected)**.5)
                required_span=max(1.1*individual_width,.7*max(separations)+individual_width/2)
            def transverse_span(piece):
                distances = []
                for a in piece['outer']:
                    for b in piece['outer']:
                        delta = sub(a,b)
                        projected = [delta[i]-normal[i]*dot(delta,normal) for i in range(3)]
                        distances.append(dot(projected,projected)**.5)
                return max(distances)
            broad = [piece for piece in part['pieces'] if piece['kind'] == 'perforated_plate' and piece['holes']
                     and transverse_span(piece) > required_span]
            self.assertGreaterEqual(len(broad), 2, name)
            self.assertTrue(all(piece.get('void_probe_mm') for piece in broad), name)
            self.assertEqual(len({piece['piece_id'] for piece in part['pieces']}), len(part['pieces']), name)

    def test_gross_axes_and_actual_material_bounds_follow_the_four_frozen_corner_members(self):
        for name in sorted(NEW_NAMES):
            part=self.by[name]
            old_chords=[self.old_by[n] for n in part['replaces_names'] if
                        self.old_by[n].get('role')=='primary_chord' or self.old_by[n].get('steel_role')=='arch_plate_chord']
            for endpoint in ('axis_start','axis_end'):
                centre=[sum(old[endpoint][i] for old in old_chords)/4 for i in range(3)]
                self.assertLess(dist(part[endpoint],centre),.00001,(name,endpoint))
            source=part['gross_source_sections'];actual=part['gross_sections']
            self.assertEqual([len(ring) for ring in source],[4,4])
            normal=sub(part['axis_end'],part['axis_start']);length=dist(part['axis_start'],part['axis_end'])
            normal=[value/length for value in normal]
            for end,sign in ((0,-1),(1,1)):
                old_points=[point for old in old_chords for point in old['sections'][end]]
                for point,original in zip(actual[end],source[end]):
                    self.assertLess(dist(point,[original[i]+normal[i]*sign*40. for i in range(3)]),.00001,name)
                for axis in range(3):
                    low,high=min(p[axis] for p in source[end]),max(p[axis] for p in source[end])
                    old_low,old_high=min(p[axis] for p in old_points),max(p[axis] for p in old_points)
                    if part['role']=='leg_assembly' and axis<2:
                        self.assertAlmostEqual(low,old_low,delta=.00001,msg=(name,end,axis))
                        self.assertAlmostEqual(high,old_high,delta=.00001,msg=(name,end,axis))
                    else:
                        margin=max(max(old['built_up_frame'][key] for key in ('width_mm','depth_mm')) for old in old_chords)
                        self.assertLessEqual(abs(low-old_low),margin+.00001,(name,end,axis))
                        self.assertLessEqual(abs(high-old_high),margin+.00001,(name,end,axis))
            # Only the explicitly fitted 120 mm diagonal seam may locally
            # project outside the gross surface, never a second macro cage.
            vertices=[p for piece in part['pieces'] for p in piece_vertices(piece)]
            legacy_vertices=[p for old in old_chords for piece in old['pieces'] for p in piece_vertices(piece)]
            for axis in range(3):
                lo=min(p[axis] for ring in actual for p in ring);hi=max(p[axis] for ring in actual for p in ring)
                self.assertGreaterEqual(min(p[axis] for p in vertices),lo-100.00001,(name,axis))
                self.assertLessEqual(max(p[axis] for p in vertices),hi+100.00001,(name,axis))
                self.assertAlmostEqual(min(p[axis] for p in vertices),min(p[axis] for p in legacy_vertices),
                                       delta=100.00001,msg=(name,axis,'R09 lower bound'))
                self.assertAlmostEqual(max(p[axis] for p in vertices),max(p[axis] for p in legacy_vertices),
                                       delta=100.00001,msg=(name,axis,'R09 upper bound'))

    def test_integration_is_explicit_private_and_rejects_malformed_controls(self):
        from lib.tokyo_tower_integrated import refine_integrated
        p=r09_reference_parameters()
        before=geometry_fingerprint(self.old)
        self.assertEqual(geometry_fingerprint(refine_integrated(p,self.old)),before)
        p['detail']['integrated_lower']={'enabled':False}
        self.assertEqual(geometry_fingerprint(refine_integrated(p,self.old)),before)
        self.assertEqual(geometry_fingerprint(refine_integrated(self.p,self.old)),geometry_fingerprint(self.parts))
        self.assertEqual(geometry_fingerprint(self.old),before)
        for override in ({'enabled':'yes'},{'cover_thickness_mm':True},{'web_thickness_mm':0.},
                         {'end_overlap_mm':float('inf')},{'max_cells':17},{'min_cells':2.5},
                         {'diaphragm_edge_clearance_mm':20.}):
            config=deepcopy(self.p)
            config['detail']['integrated_lower'].update(override)
            with self.subTest(override=override),self.assertRaises(ValueError):refine_integrated(config,self.old)

    def test_actual_cover_and_open_web_surfaces_rotate_consistently_between_all_four_legs(self):
        for index in range(1,14):
            source=self.by[f'structure:leg_01_assembly_{index:02d}']
            for leg in range(2,5):
                target=self.by[f'structure:leg_{leg:02d}_assembly_{index:02d}']
                self.assertEqual(material_surfaces(source,leg-1),material_surfaces(target),
                                 (index,leg,'actual material surfaces'))
        # Node anchors predate the R10 fit and are not perfectly rotational.
        # Isolate only that known source of local diaphragm/void truncation;
        # compare the actual broad faces and hole loops generated without it.
        from lib.tokyo_tower_integrated import refine_integrated
        unanchored=deepcopy(self.old)
        for part in unanchored:
            for key in REFERENCE_KEYS:part.pop(key,None)
        intrinsic={p['name']:p for p in refine_integrated(self.p,unanchored)}
        for index in range(1,14):
            source=intrinsic[f'structure:leg_01_assembly_{index:02d}']
            for leg in range(2,5):
                target=intrinsic[f'structure:leg_{leg:02d}_assembly_{index:02d}']
                self.assertEqual(material_surfaces(source,leg-1,holes=True),material_surfaces(target,holes=True),
                                 (index,leg,'intrinsic actual hole layout'))

    def test_upper_equipment_nodes_visitor_decks_and_skytree_remain_protected(self):
        for part in self.old:
            if part['group'] in ('base','core','decks','antenna') or part['name'].startswith('structure:upper_'):
                self.assertEqual(self.by[part['name']], remap_references(part), part['name'])
        nodes = [part for part in self.parts if part.get('steel_node_id')]
        self.assertEqual(len(nodes), 296)
        self.assertEqual({part['steel_node_id'] for part in nodes}, {f'TT-N{i:02d}' for i in range(1,21)})
        for part in nodes:
            self.assertEqual(part, remap_references(self.old_by[part['name']]))
        sky = component_specs('tokyo-skytree')
        self.assertEqual(len(sky), 7649)
        self.assertEqual(geometry_fingerprint(sky), R09_BASELINE['skytree_specs_sha256'])
        self.assertEqual(geometry_fingerprint(TOWERS['tokyo-skytree']), R09_BASELINE['skytree_parameters_sha256'])

    def test_node_catalog_preserves_all_real_feature_dimensions_and_resolves_material_aliases(self):
        from lib.tokyo_tower_steel import node_catalog
        from lib.tokyo_tower_detail import component_specs as appearance_specs, _square, body_radius
        from lib.tower_geometry import _tower_paint
        p=r09_reference_parameters()
        old=node_catalog(p,appearance_specs(p,lambda z:_square(body_radius(p,z)),_tower_paint))
        current=r10_reference_node_catalog()
        self.assertEqual(len(current),20)
        self.assertEqual(current,[remap_references(row) for row in old])
        for row in current:
            self.assertTrue(all(name in self.by for name in row['member_names']))
            self.assertTrue(all(name in self.by for name in row['part_names']))


class TokyoTowerR10NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from cadgen import build123d as bd
        cls.bd = bd
        cls.parts = r10_reference_specs()
        cls.by = {part['name']:part for part in cls.parts}
        cls.cache = {}

    def shape(self, name):
        name = ALIASES.get(name, name)
        if name not in self.cache:
            shape = _cad_shape(self.by[name], self.bd)
            self.assertTrue(shape.is_valid, name)
            self.assertEqual(len(shape.solids()), 1, name)
            self.assertGreater(shape.volume, 0., name)
            self.cache[name] = shape
        return self.cache[name]

    def contact(self, one, two):
        one, two = ALIASES.get(one,one), ALIASES.get(two,two)
        self.assertNotEqual(one,two,'An alias must not turn a connection test into self-intersection.')
        a,b = self.shape(one),self.shape(two)
        self.assertLess(a.distance_to(b),.01,(one,two))
        common = a.intersect(b)
        self.assertIsNotNone(common,(one,two))
        self.assertGreater(sum(solid.volume for solid in common.solids()),1.,(one,two))

    def test_all_116_integrated_materials_are_single_connected_solids(self):
        self.assertEqual(len(NEW_NAMES),116)
        for name in sorted(NEW_NAMES):
            with self.subTest(name=name):self.shape(name)

    def test_adjacent_leg_and_arch_stations_have_positive_native_connections(self):
        for leg in range(1,5):
            for index in range(1,13):
                self.contact(f'structure:leg_{leg:02d}_assembly_{index:02d}',f'structure:leg_{leg:02d}_assembly_{index+1:02d}')
        for side in range(4):
            for index in range(15):
                self.contact(f'structure:arch_assembly_{side}_{index:02d}',f'structure:arch_assembly_{side}_{index+1:02d}')

    def test_all_legacy_external_attachments_still_contact_actual_new_hosts(self):
        contacts = []
        links = [p for p in self.parts if p.get('role') == 'leg_transition_link']
        anchors = [p for p in self.parts if p['name'].startswith('structure:lower_arch_anchor_')]
        bridges = [p for p in self.parts if p['name'].startswith('structure:arch_spandrel_crown_bridge_')]
        self.assertEqual((len(links),len(anchors),len(bridges)),(112,16,4))
        for part in links+anchors+bridges:
            contacts.extend((part['name'],part[key]) for key in ('source_member','target_member'))
        plates = [p for p in self.parts if p.get('steel_node_id') and p.get('contact_with') in NEW_NAMES]
        self.assertEqual(len(plates),20)
        contacts.extend((p['name'],p['contact_with']) for p in plates)
        mounts = [p for p in self.parts if p['name'].startswith('structure:upper_equipment_') and p.get('host_members')]
        self.assertEqual(len(mounts),42)
        contacts.extend((p['name'],host) for p in mounts for host in p['host_members'])
        self.assertEqual(len(contacts),326)
        for one,two in contacts:
            with self.subTest(part=one,host=two):self.contact(one,two)

    def test_whole_assemblies_keep_gross_openings_and_clear_arch_passage(self):
        for name in ('structure:leg_01_assembly_01','structure:leg_01_assembly_08',
                     'structure:arch_assembly_0_00','structure:arch_assembly_0_07'):
            part=self.by[name];shape=self.shape(name)
            pierced=[piece for piece in part['pieces'] if piece['kind']=='perforated_plate' and piece['holes']]
            self.assertGreaterEqual(len(pierced),2,name)
            for piece in pierced:
                probe=self.bd.Solid.make_sphere(.5,self.bd.Plane(origin=tuple(piece['void_probe_mm'])))
                common=shape.intersect(probe)
                self.assertLess(sum(s.volume for s in common.solids()) if common is not None else 0.,.000001,(name,piece['piece_id']))
        # The full deep arch must not become a filled curtain across its void.
        for z in (5000.,15000.,25000.,34000.,37000.):
            probe=self.bd.Solid.make_sphere(100.,self.bd.Plane(origin=(0.,-25000.,z)))
            for i in range(16):
                common=self.shape(f'structure:arch_assembly_0_{i:02d}').intersect(probe)
                self.assertLess(sum(s.volume for s in common.solids()) if common is not None else 0.,.000001,(z,i))


if __name__ == '__main__':unittest.main()
