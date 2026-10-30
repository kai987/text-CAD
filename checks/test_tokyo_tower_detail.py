"""Independent control/route checks for the original Tokyo appearance detail."""
from __future__ import annotations

from collections import Counter
from math import dist, isfinite
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from lib.tower_geometry import (TOWERS, GROUPS, component_specs, geometry_manifest,
                                geometry_source_paths, profile_radius, revision_for)


def polygon_area(points):
    return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1]))) / 2


def horizontal_bounds(spec):
    if spec['kind'] == 'box':
        return spec['bounds'][:2] + spec['bounds'][3:5]
    if spec['kind'] == 'beam':
        return [min(spec['start'][i],spec['end'][i])-spec['radius'] for i in range(2)] + [
            max(spec['start'][i],spec['end'][i])+spec['radius'] for i in range(2)]
    points=[point for section in spec['sections'] for point in (section if spec['kind']=='loft3d' else section['points'])]
    return [min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)]


def maximum_z(spec):
    if spec['kind']=='box':return spec['bounds'][5]
    if spec['kind']=='beam':return max(spec['start'][2],spec['end'][2])+spec['radius']
    if spec['kind']=='loft3d':return max(p[2] for section in spec['sections'] for p in section)
    return max(section['z'] for section in spec['sections'])


class TokyoTowerDetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parameters=TOWERS['tokyo-tower']
        cls.specs=component_specs('tokyo-tower')

    def test_catalog_is_named_bounded_and_separate_from_skytree(self):
        names=[part['name'] for part in self.specs]
        self.assertEqual(len(set(names)),len(names))
        self.assertGreater(len(names),1000)
        self.assertLessEqual(len(names),3500)
        self.assertEqual(set(part['group'] for part in self.specs),set(GROUPS))
        self.assertTrue(all(name.startswith(part['group']+':') for name,part in zip(names,self.specs)))
        self.assertEqual(revision_for('tokyo-tower'),'LANDMARK-R04')
        self.assertEqual(revision_for('tokyo-skytree'),'LANDMARK-R02')
        self.assertNotEqual(component_specs('tokyo-skytree'), self.specs)
        self.assertEqual(geometry_source_paths('tokyo-skytree'),['src/lib/tower_geometry.py','src/lib/skytree_detail.py'])
        self.assertIn('src/lib/tokyo_tower_detail.py',geometry_source_paths('tokyo-tower'))

    def test_all_primitives_are_finite_and_have_nonzero_sections(self):
        def numbers(value):
            if isinstance(value,dict):
                for item in value.values():yield from numbers(item)
            elif isinstance(value,(list,tuple)):
                for item in value:yield from numbers(item)
            elif type(value) in (int,float):yield value
        for part in self.specs:
            with self.subTest(part=part['name']):
                self.assertTrue(all(isfinite(number) for number in numbers(part)))
                if part['kind']=='box':
                    self.assertTrue(all(part['bounds'][i+3]>part['bounds'][i] for i in range(3)))
                elif part['kind']=='beam':
                    self.assertGreater(part['radius'],0)
                    self.assertGreater(dist(part['start'],part['end']),0)
                elif part['kind']=='loft3d':
                    self.assertGreater(len(part['sections']),1)
                    for section in part['sections']:
                        area=[sum(a[(i+1)%3]*b[(i+2)%3]-a[(i+2)%3]*b[(i+1)%3]
                                  for a,b in zip(section,section[1:]+section[:1])) for i in range(3)]
                        self.assertGreater(sum(v*v for v in area),0)
                else:
                    self.assertEqual(part['kind'],'loft')
                    self.assertGreater(len(part['sections']),1)
                    self.assertTrue(all(b['z']>a['z'] for a,b in zip(part['sections'],part['sections'][1:])))
                    self.assertTrue(all(polygon_area(section['points'])>0 for section in part['sections']))

    def test_smoother_leg_controls_are_monotone_and_keep_reference_heights(self):
        radii=[profile_radius('tokyo-tower',z) for z in range(0,252651,1000)]
        self.assertTrue(all(a>=b>0 for a,b in zip(radii,radii[1:])))
        for z,radius in self.parameters['profile']:
            self.assertAlmostEqual(profile_radius('tokyo-tower',z),radius,places=8)
        self.assertEqual(self.parameters['height_mm'],333000)
        self.assertEqual(self.parameters['deck_levels_mm'],[125000,223550])
        self.assertAlmostEqual(max(maximum_z(part) for part in self.specs),333000)

    def test_lower_frame_keeps_the_base_building_approach_open(self):
        lower=[part for part in self.specs if part['group']=='structure' and maximum_z(part)<=20000]
        self.assertGreater(len(lower),12)
        for part in lower:
            x1,y1,x2,y2=horizontal_bounds(part)
            self.assertTrue(x2 < -18500 or x1 > 18500 or y2 < -18500 or y1 > 18500,part['name'])
        self.assertTrue(any(part.get('role')=='open_cross_frame' for part in self.specs))
        self.assertFalse(any(part['name'].startswith('structure:cross_a_') for part in lower))

    def test_six_hundred_rises_and_landings_connect_roof_to_main_deck(self):
        treads=sorted((p for p in self.specs if p.get('role')=='stair_tread'),key=lambda p:p['riser_index'])
        landings=sorted((p for p in self.specs if p.get('role')=='stair_landing'),key=lambda p:p['flight'])
        self.assertEqual(len(treads),600)
        self.assertEqual([part['riser_index'] for part in treads],list(range(1,601)))
        self.assertEqual(Counter(part['flight'] for part in treads),Counter({flight:25 for flight in range(1,25)}))
        self.assertEqual(len(landings),24)
        start=self.parameters['detail']['foot_town_roof_mm'];rise=(125000-start)/600
        self.assertAlmostEqual(rise,106700/600)
        self.assertAlmostEqual(treads[0]['bounds'][5]-rise,start)
        self.assertAlmostEqual(treads[-1]['bounds'][5],125000)
        for number,tread in enumerate(treads,1):
            self.assertAlmostEqual(tread['bounds'][5],start+number*rise)
            self.assertAlmostEqual(tread['bounds'][4]-tread['bounds'][1],260)
            # The entire route stays east of the guide-frame core and within
            # the tightest model frame below the main observation deck.
            self.assertGreaterEqual(tread['bounds'][0],5000)
            self.assertLessEqual(tread['bounds'][3],8750)
            self.assertGreaterEqual(tread['bounds'][1],-6500)
            self.assertLessEqual(tread['bounds'][4],0)
        for flight,landing in enumerate(landings,1):
            final=treads[flight*25-1]
            self.assertAlmostEqual(landing['bounds'][5],final['bounds'][5])
            if flight%2:self.assertAlmostEqual(final['bounds'][4],landing['bounds'][1])
            else:self.assertAlmostEqual(final['bounds'][1],landing['bounds'][4])
            if flight<24:self.assertAlmostEqual(treads[flight*25]['bounds'][5]-landing['bounds'][5],rise)
        self.assertEqual(landings[-1]['bounds'][:2],[4700,-8000])
        self.assertEqual(landings[-1]['bounds'][3:5],[9300,-6500])

    def test_main_deck_has_two_floor_levels_with_real_stair_openings(self):
        floors=[p for p in self.specs if p.get('role')=='deck_floor' and ':main_' in p['name']]
        self.assertEqual(len(floors),12)
        self.assertEqual(sorted({maximum_z(part) for part in floors}),[120000,125000])
        half=self.parameters['deck_specs'][0]['half_width_mm']*.95
        chamfer=half*.18
        expected=4*half*half-2*chamfer*chamfer-(9300-4700)*(1800+8000)
        for level in (120000,125000):
            area=0
            for part in floors:
                if maximum_z(part)!=level:continue
                if part['kind']=='box':
                    x1,y1,_,x2,y2,_=part['bounds'];area+=(x2-x1)*(y2-y1)
                else:area+=polygon_area(part['sections'][-1]['points'])
            self.assertAlmostEqual(area,expected,places=3)

    def test_glazing_is_split_into_thin_panels_instead_of_full_deck_volumes(self):
        panels=[p for p in self.specs if p.get('role')=='glazing']
        self.assertGreater(len(panels),100)
        self.assertTrue(all('glazing' in p['name'] and p.get('finish')=='glass' for p in panels))
        for panel in panels:
            x1,y1,x2,y2=horizontal_bounds(panel)
            if panel['kind']=='loft':
                self.assertEqual(len(panel['sections'][0]['points']),4)
                self.assertLess(polygon_area(panel['sections'][0]['points']),2e6)
        self.assertGreater(len([p for p in panels if ':main_glazing_' in p['name']]),16)

    def test_named_light_lenses_have_separate_roles_and_remain_below_tip(self):
        warm=[p for p in self.specs if p.get('role')=='light_lens']
        warning=[p for p in self.specs if p.get('role')=='obstruction_light_lens']
        self.assertEqual(len(warm),6)
        self.assertEqual(len(warning),11)
        for part in warm+warning:
            self.assertIn(part['role'],part['name'])
            self.assertEqual(part['detail_level'],'micro')
            self.assertLess(maximum_z(part),333000)
        manifest=geometry_manifest('tokyo-tower')
        self.assertTrue(all(value is None for value in manifest['engineering'].values()))
        self.assertGreaterEqual(len(manifest['assumptions']),2)

    def test_reference_controls_are_separate_from_visitor_deck_names(self):
        p=self.parameters
        self.assertEqual(p['nominal_deck_levels_mm'],[150000,250000])
        self.assertEqual(p['detail']['arch_crown_mm'],40000)
        self.assertEqual(p['antenna_start_mm'],252650)
        self.assertEqual(p['antenna_lattice_top_mm'],312600)
        arches=[part for part in self.specs if part['name'].startswith('structure:lower_arch_') and part.get('role')=='open_cross_frame']
        self.assertAlmostEqual(max(max(part['start'][2],part['end'][2]) for part in arches),40000)
        self.assertLess(min(min(part['start'][2],part['end'][2]) for part in arches),2000)
        panels=[p for p in self.specs if p.get('role')=='lower_panel_brace']
        self.assertGreaterEqual(len(panels),96)
        self.assertTrue(all(40000<=p['start'][2]<=80000 and 40000<=p['end'][2]<=80000 for p in panels))
        self.assertGreater(len([p for p in self.specs if p.get('role')=='antenna_support_lacing']),40)

    def test_arch_end_plates_bridge_actual_chords_and_deck_supports_meet_aprons(self):
        by_name={part['name']:part for part in self.specs}
        connectors=[p for p in self.specs if p['name'].startswith('structure:lower_arch_anchor_')]
        self.assertEqual(len(connectors),16)
        for connector in connectors:
            source=by_name[connector['source_member']]
            target=by_name[connector['target_member']]
            a,b=connector['attachment_points']
            self.assertTrue(a==source['start'] or a==source['end'])
            if target['kind']=='loft3d':
                centre_a,centre_b=target['axis_start'],target['axis_end']
            else:
                section_a,section_b=target['sections']
                centre_a=[sum(p[k] for p in section_a['points'])/4 for k in range(2)]+[section_a['z']]
                centre_b=[sum(p[k] for p in section_b['points'])/4 for k in range(2)]+[section_b['z']]
            t=(b[2]-centre_a[2])/(centre_b[2]-centre_a[2])
            self.assertTrue(0<=t<=1)
            for axis in range(2):
                self.assertAlmostEqual(b[axis],centre_a[axis]*(1-t)+centre_b[axis]*t)
            self.assertLess(connector['sections'][0]['z'],a[2])
            self.assertGreater(connector['sections'][1]['z'],a[2])
        brackets=[p for p in self.specs if p.get('role')=='deck_bracket']
        self.assertEqual(len(brackets),16)
        for bracket in brackets:
            apron=by_name[bracket['target_member']]
            edge=apron['sections'][0]
            expected=[(edge['points'][0][axis]+edge['points'][1][axis])/2 for axis in range(2)]+[edge['z']]
            self.assertEqual(bracket['end'],expected)
            level=115000 if ':main_' in bracket['name'] else 216550
            self.assertEqual(bracket['start'][2],level)
        self.assertEqual(len([p for p in self.specs if p.get('role')=='deck_support_ring']),4)


if __name__=='__main__':unittest.main()
