"""Four-column 80--120 m grid, with an independent pre-R11 R10 scope."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from math import dist, isfinite
from pathlib import Path
import re
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from checks.tokyo_tower_r10_baseline import R10_BASELINE, TOKYO_R10_PARAMETERS, TOKYO_R10_SPEC_SHA256_BY_NAME
from checks.test_tokyo_tower_r10 import r10_reference_specs,r10_reference_parameters,r10_reference_node_catalog
from checks.test_tokyo_tower_r09 import piece_vertices,polygon_area_3d,dot,sub
from checks.test_tokyo_tower_r08 import geometry_fingerprint
from lib.tower_geometry import TOWERS,component_specs,geometry_manifest,_cad_shape


REMOVED_NAMES=frozenset(R10_BASELINE['removed_grid_names'])
OLD_NAMES=frozenset(R10_BASELINE['tokyo_part_names'])
LEVELS=(80000.,93000.,106000.,120000.)
GRID_NAMES=frozenset(
    [f'structure:grid_panel_{direction}_{side}_{band}_{column}'
     for direction in ('a','b') for side in range(4) for band in range(3) for column in range(4)]
    +[f'structure:grid_vertical_{side}_{band}_{column}' for side in range(4) for band in range(3) for column in (1,2,3)]
    +[f'structure:grid_belt_{side}_{band}' for side in range(4) for band in range(3)])
CLIP_NAMES=frozenset(f'structure:grid_corner_link_{corner}_{level}' for corner in range(4) for level in range(4))
SUPPORT_NAMES=frozenset(f'structure:grid_support_link_{corner}' for corner in range(4))
NEW_NAMES=GRID_NAMES|CLIP_NAMES|SUPPORT_NAMES


def frozen_outer_corner(parts,corner,z):
    stem=f'structure:leg_{corner+1:02d}_chord_{corner:02d}_'
    matches=[]
    for part in parts:
        for name,axis in part.get('legacy_member_axes',{}).items():
            if name.startswith(stem) and axis['axis_start'][2]-.00001<=z<=axis['axis_end'][2]+.00001:
                matches.append((name,axis))
    if not matches:raise AssertionError((corner,z,'Missing independent R10 outer-leg axis'))
    _,axis=min(matches)
    a,b=axis['axis_start'],axis['axis_end'];t=(z-a[2])/(b[2]-a[2])
    return [a[i]+t*(b[i]-a[i]) for i in range(3)]


def frozen_grid_node(parts,side,level,column):
    a=frozen_outer_corner(parts,side,LEVELS[level]);b=frozen_outer_corner(parts,(side+1)%4,LEVELS[level])
    return [a[i]+column/4*(b[i]-a[i]) for i in range(3)]


class TokyoTowerR11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parts=component_specs('tokyo-tower')
        cls.by={part['name']:part for part in cls.parts}
        cls.old=r10_reference_specs()
        cls.old_by={part['name']:part for part in cls.old}

    def test_independent_full_r10_replay_is_the_frozen_pre_grid_model(self):
        self.assertEqual(len(self.old),5337)
        self.assertEqual(geometry_fingerprint(self.old),R10_BASELINE['tokyo_specs_sha256'])
        self.assertEqual(R10_BASELINE['tokyo_specs_sha256'],
                         '29db95d4ad44eb35042f2143a194a8a51eaae704114cbf428dd65e09820c5c0f')

    def test_exact_120_old_grid_members_are_removed_and_all_5217_other_specs_stay_exact(self):
        self.assertEqual(len(REMOVED_NAMES),120)
        self.assertTrue(all(re.fullmatch(r'structure:upper_(?:diagonal|return|secondary|secondary_return|vertical|ring)_[0-3]_[1-5]',name)
                            for name in REMOVED_NAMES))
        self.assertEqual(set(self.by)&OLD_NAMES,OLD_NAMES-REMOVED_NAMES)
        self.assertEqual(len(self.parts),len(self.by))
        protected=[self.by[part['name']] for part in self.old if part['name'] not in REMOVED_NAMES]
        self.assertEqual(len(protected),5217)
        self.assertEqual(geometry_fingerprint(protected),R10_BASELINE['protected_specs_sha256'])
        self.assertEqual(R10_BASELINE['protected_specs_sha256'],
                         'b8610f26cc719a5539f695323f93925a5b72b9909afc6a69ef847eede5f73cc1')
        for part in protected:
            self.assertEqual(geometry_fingerprint(part),TOKYO_R10_SPEC_SHA256_BY_NAME[part['name']],part['name'])

    def test_all_integrated_materials_chords_and_existing_controls_stay_unchanged(self):
        assemblies=[part for part in self.old if part.get('role') in ('leg_assembly','arch_assembly')]
        self.assertEqual(len(assemblies),116)
        for part in self.old:
            if part in assemblies or part['name'].startswith('structure:upper_chord_'):
                self.assertEqual(self.by[part['name']],part,part['name'])
        p=TOWERS['tokyo-tower']
        self.assertEqual(p['revision'],'LANDMARK-R11')
        self.assertEqual(p['profile'],TOKYO_R10_PARAMETERS['profile'])
        self.assertEqual({key:p['detail'][key] for key in TOKYO_R10_PARAMETERS['detail']},TOKYO_R10_PARAMETERS['detail'])

    def test_exact_164_new_materials_form_96_crosses_36_verticals_12_belts_and_20_real_connections(self):
        self.assertEqual((len(GRID_NAMES),len(CLIP_NAMES),len(SUPPORT_NAMES)),(144,16,4))
        self.assertEqual(set(self.by),(OLD_NAMES-REMOVED_NAMES)|NEW_NAMES)
        self.assertEqual(len(self.parts),5381)
        self.assertEqual(Counter(self.by[name]['role'] for name in NEW_NAMES),Counter(
            grid_panel_brace=96,grid_panel_vertical=36,grid_belt=12,grid_attachment=16,grid_support_link=4))
        for name in GRID_NAMES:self.assertEqual(self.by[name]['kind'],'built_up',name)
        for name in CLIP_NAMES|SUPPORT_NAMES:self.assertEqual(self.by[name]['kind'],'beam',name)

    def test_every_main_member_follows_adjacent_quarter_cells_of_the_frozen_outer_leg_frame(self):
        for side in range(4):
            for band in range(3):
                expected={}
                for col in range(4):
                    expected[f'structure:grid_panel_a_{side}_{band}_{col}']=(band,col,band+1,col+1)
                    expected[f'structure:grid_panel_b_{side}_{band}_{col}']=(band,col+1,band+1,col)
                for col in (1,2,3):expected[f'structure:grid_vertical_{side}_{band}_{col}']=(band,col,band+1,col)
                expected[f'structure:grid_belt_{side}_{band}']=(band+1,0,band+1,4)
                for name,(l0,c0,l1,c1) in expected.items():
                    part=self.by[name]
                    self.assertEqual((part['grid_side'],part['grid_band']),(side,band))
                    a=frozen_grid_node(self.old,side,l0,c0);b=frozen_grid_node(self.old,side,l1,c1)
                    self.assertLess(dist(part['axis_start'],a),.00001,(name,'start'))
                    self.assertLess(dist(part['axis_end'],b),.00001,(name,'end'))
                    self.assertGreater(dist(a,b),0.)
        # The 80 m boundary must join the existing four-column lower face;
        # the central chord plane is about a metre inward at this level.
        for side in range(4):
            belt=self.old_by[f'structure:lower_belt_{side}_2']
            self.assertLess(dist(belt['start'],frozen_grid_node(self.old,side,0,0)),.00001)
            self.assertLess(dist(belt['end'],frozen_grid_node(self.old,side,0,4)),.00001)

    def test_new_grid_material_uses_the_existing_lower_face_open_built_up_families(self):
        for name in sorted(GRID_NAMES):
            part=self.by[name]
            a=re.fullmatch(r'structure:grid_panel_([ab])_([0-3])_[0-2]_([0-3])',name)
            vertical=re.fullmatch(r'structure:grid_vertical_([0-3])_[0-2]_([1-3])',name)
            if a:old_name=f'structure:lower_panel_{a[1]}_{a[2]}_2_{a[3]}'
            elif vertical:old_name=f'structure:lower_panel_vertical_{vertical[1]}_2_{vertical[2]}'
            else:old_name=f"structure:lower_belt_{part['grid_side']}_2"
            reference=self.old_by[old_name]
            self.assertEqual(part['built_up_family'],reference['built_up_family'],name)
            for key in ('width_mm','depth_mm'):
                self.assertEqual(part['built_up_frame'][key],reference['built_up_frame'][key],(name,key))
            for key in ('cover_thickness_mm','web_thickness_mm','dimensions_status'):
                self.assertEqual(part['section_profile'][key],reference['section_profile'][key],(name,key))
            opened=[p for p in part['pieces'] if p['kind']=='perforated_plate' and p['holes']]
            self.assertEqual(len(opened),2,name)
            for piece in opened:
                self.assertTrue(all(len(hole) in (3,4) and polygon_area_3d(hole)>0 for hole in piece['holes']),name)
                self.assertTrue(all(isfinite(v) for v in piece['void_probe_mm']),name)

    def test_new_grid_records_all_removed_axes_and_resolves_both_endpoint_connections(self):
        holders=[part for part in self.parts if 'grid_replaced_names' in part]
        self.assertEqual(len(holders),1)
        holder=holders[0]
        self.assertEqual(set(holder['grid_replaced_names']),REMOVED_NAMES)
        self.assertEqual(len(holder['grid_replaced_names']),120)
        self.assertEqual(holder['grid_legacy_member_axes'],{name:{
            'axis_start':self.old_by[name].get('axis_start',self.old_by[name].get('start')),
            'axis_end':self.old_by[name].get('axis_end',self.old_by[name].get('end'))} for name in REMOVED_NAMES})
        for name in GRID_NAMES:
            part=self.by[name]
            self.assertEqual(part['grid_levels_mm'],list(LEVELS))
            self.assertEqual(part['grid_band_levels_mm'],list(LEVELS[part['grid_band']:part['grid_band']+2]))
            connections=part['endpoint_connection_names']
            self.assertEqual(len(connections),2,name)
            self.assertTrue(all(isinstance(row,list) and row for row in connections),name)
            for index,row in enumerate(connections):
                self.assertEqual(len(row),len(set(row)),name)
                for host in row:self.assertIn(host,self.by,(name,host))
                if part['role']!='grid_belt':
                    point=part['axis_start' if index==0 else 'axis_end']
                    level=min(range(4),key=lambda i:abs(LEVELS[i]-point[2]))
                    belt=(f"structure:lower_belt_{part['grid_side']}_2" if level==0 else
                          f"structure:grid_belt_{part['grid_side']}_{level-1}")
                    self.assertIn(belt,row,(name,index,'actual horizontal host'))
        for corner in range(4):
            for level in range(4):
                part=self.by[f'structure:grid_corner_link_{corner}_{level}']
                expected=frozen_outer_corner(self.old,corner,LEVELS[level])
                self.assertLess(dist(part['attachment_points'][0],expected),.00001)
                self.assertEqual(part['nominal_axis_start'],part['attachment_points'][0])
                self.assertEqual(part['nominal_axis_end'],part['attachment_points'][1])
                self.assertEqual(part['source_embedding_mm'],20.)
                self.assertAlmostEqual(dist(part['start'],expected),20.,places=5)
                delta=sub(part['end'],part['start']);fraction=dot(sub(expected,part['start']),delta)/dot(delta,delta)
                self.assertTrue(0.<fraction<1.)
                self.assertLess(dist(expected,[part['start'][i]+fraction*delta[i] for i in range(3)]),.00001)

    def test_grid_pass_is_opt_in_private_and_rejects_malformed_geometry_controls(self):
        from lib.tokyo_tower_grid import refine_grid
        p=r10_reference_parameters();before=geometry_fingerprint(self.old)
        self.assertEqual(geometry_fingerprint(refine_grid(p,self.old)),before)
        p['detail']['lower_grid_continuity']={'enabled':False}
        self.assertEqual(geometry_fingerprint(refine_grid(p,self.old)),before)
        self.assertEqual(geometry_fingerprint(refine_grid(TOWERS['tokyo-tower'],self.old)),geometry_fingerprint(self.parts))
        self.assertEqual(geometry_fingerprint(self.old),before)
        for override in ({'enabled':'yes'},{'columns':True},{'columns':4.0},
                         {'band_levels_mm':[80000.,106000.,93000.,120000.]},
                         {'primary_brace_radius_mm':0.},{'belt_radius_mm':float('inf')},
                         {'support_height_mm':120000.}):
            config=deepcopy(TOWERS['tokyo-tower']);config['detail']['lower_grid_continuity'].update(override)
            with self.subTest(override=override),self.assertRaises(ValueError):refine_grid(config,self.old)

    def test_upper_equipment_nodes_and_skytree_are_outside_the_grid_edit_scope(self):
        nodes=[p for p in self.parts if p.get('steel_node_id')]
        equipment=[p for p in self.parts if p['name'].startswith('structure:upper_equipment_')]
        self.assertEqual((len(nodes),len(equipment)),(296,111))
        for part in nodes+equipment:self.assertEqual(part,self.old_by[part['name']])
        sky=component_specs('tokyo-skytree')
        self.assertEqual(len(sky),7649)
        self.assertEqual(geometry_fingerprint(sky),R10_BASELINE['skytree_specs_sha256'])
        self.assertEqual(geometry_fingerprint(TOWERS['tokyo-skytree']),R10_BASELINE['skytree_parameters_sha256'])

    def test_the_20_node_catalogs_keep_dimensions_and_resolve_114m_references_to_the_correct_corner(self):
        old=r10_reference_node_catalog();current=geometry_manifest('tokyo-tower')['steel_nodes']
        self.assertEqual(len(current),20)
        for original,actual in zip(old,current):
            expected=deepcopy(original);members=[]
            primary=re.fullmatch(r'structure:upper_chord_([0-3])_5',original['member_names'][0])
            for name in original['member_names']:
                if name in REMOVED_NAMES:
                    ring=re.fullmatch(r'structure:upper_ring_([0-3])_4',name)
                    self.assertIsNotNone(ring,original['id'])
                    self.assertIsNotNone(primary,original['id'])
                    corner=int(primary[1]);self.assertIn(corner,(int(ring[1]),(int(ring[1])+1)%4))
                    name=f'structure:grid_support_link_{corner}'
                if name not in members:members.append(name)
            expected['member_names']=members
            self.assertEqual(actual,expected,original['id'])
            self.assertTrue(all(name in self.by for name in actual['member_names']))
        for corner in range(4):
            support=self.by[f'structure:grid_support_link_{corner}']
            self.assertAlmostEqual(support['start'][2],114000.,places=6)
            self.assertAlmostEqual(support['end'][2],114000.,places=6)


class TokyoTowerR11NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from cadgen import build123d as bd
        cls.bd=bd;cls.parts=component_specs('tokyo-tower');cls.by={p['name']:p for p in cls.parts};cls.cache={};cls.contacts=set()

    def shape(self,name):
        if name not in self.cache:
            shape=_cad_shape(self.by[name],self.bd)
            self.assertTrue(shape.is_valid,name)
            self.assertEqual(len(shape.solids()),1,name)
            self.assertGreater(shape.volume,0.,name)
            self.cache[name]=shape
        return self.cache[name]

    def contact(self,one,two):
        self.assertNotEqual(one,two,'Endpoint verification must not intersect a part with itself.')
        key=tuple(sorted((one,two)))
        if key in self.contacts:return
        a,b=self.shape(one),self.shape(two)
        common=a.intersect(b)
        self.assertIsNotNone(common,(one,two))
        volume=sum(p.volume for p in common.solids())
        # A positive-volume native intersection strictly implies contact;
        # avoid a second, expensive all-face nearest-distance search for
        # every successful pair. Keep distance as a failure diagnostic.
        self.assertGreater(volume,1.,(one,two,a.distance_to(b) if volume<=1. else 0.))
        self.contacts.add(key)

    def test_all_164_new_members_are_valid_single_solids(self):
        self.assertEqual(len(NEW_NAMES),164)
        for name in sorted(NEW_NAMES):
            with self.subTest(name=name):self.shape(name)

    def test_all_288_nominal_grid_ends_contact_every_declared_real_connection(self):
        endpoint_count=0
        for name in sorted(GRID_NAMES):
            part=self.by[name]
            self.assertEqual(len(part['endpoint_connection_names']),2,name)
            for index,row in enumerate(part['endpoint_connection_names']):
                self.assertTrue(row,name);endpoint_count+=1
                for host in row:
                    with self.subTest(part=name,host=host):self.contact(name,host)
                if part['role']!='grid_belt':
                    point=part['axis_start' if index==0 else 'axis_end']
                    level=min(range(4),key=lambda i:abs(LEVELS[i]-point[2]))
                    belt=(f"structure:lower_belt_{part['grid_side']}_2" if level==0 else
                          f"structure:grid_belt_{part['grid_side']}_{level-1}")
                    self.assertIn(belt,row,(name,index))
        self.assertEqual(endpoint_count,288)

    def test_all_16_corner_links_join_incident_grid_members_and_actual_gross_cover_material(self):
        for corner in range(4):
            for level in range(4):
                name=f'structure:grid_corner_link_{corner}_{level}';part=self.by[name]
                self.assertEqual(self.by[part['target_member']]['role'],'leg_assembly')
                expected_incident={grid for grid in GRID_NAMES if any(
                    dist(self.by[grid][endpoint],part['attachment_points'][0])<.00001
                    for endpoint in ('axis_start','axis_end'))}
                self.assertEqual(set(part['source_members']),expected_incident,name)
                self.assertTrue(expected_incident,name)
                self.assertEqual(part['nominal_axis_start'],part['attachment_points'][0])
                self.assertEqual(part['source_embedding_mm'],20.)
                self.assertAlmostEqual(dist(part['start'],part['attachment_points'][0]),20.,places=5)
                self.assertEqual(part['end'],part['attachment_points'][1])
                self.contact(name,part['target_member'])
                for member in part['source_members']:self.contact(name,member)
                if level==0:
                    self.contact(name,f'structure:lower_belt_{corner}_2')
                    self.contact(name,f'structure:lower_belt_{(corner-1)%4}_2')

    def test_all_four_114m_supports_keep_real_primary_chord_and_gross_leg_contacts(self):
        for corner in range(4):
            name=f'structure:grid_support_link_{corner}';part=self.by[name]
            self.assertEqual(self.by[part['target_member']]['role'],'leg_assembly')
            self.assertEqual(part['source_member'],f'structure:upper_chord_{corner}_5')
            self.assertAlmostEqual(part['start'][2],114000.,places=6)
            self.contact(name,part['source_member'])
            self.contact(name,part['target_member'])
            for member in part.get('attached_members',[]):self.contact(name,member)

    def test_both_sides_of_representative_grid_webs_have_real_empty_openings(self):
        for name in ('structure:grid_panel_a_0_0_0','structure:grid_panel_b_0_1_2',
                     'structure:grid_vertical_0_1_2','structure:grid_belt_0_0'):
            part=self.by[name];shape=self.shape(name)
            pieces=[p for p in part['pieces'] if p['kind']=='perforated_plate' and p['holes']]
            self.assertEqual(len(pieces),2,name)
            for piece in pieces:
                probe=self.bd.Solid.make_sphere(.5,self.bd.Plane(origin=tuple(piece['void_probe_mm'])))
                common=shape.intersect(probe)
                self.assertLess(sum(p.volume for p in common.solids()) if common is not None else 0.,.000001,(name,piece['piece_id']))


if __name__=='__main__':unittest.main()
