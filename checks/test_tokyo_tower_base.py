"""R07 base appearance: deep arches, retained leg axes and source-bound massing."""
from __future__ import annotations

import hashlib
import json
import re
from math import dist, isfinite
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from lib.tower_geometry import TOWERS,component_specs,_cad_shape
from lib.tokyo_tower_detail import _base_config,_leg_frame_levels,_leg_cage_half


def fingerprint(value):
    def canonical(v):
        if isinstance(v,float):
            if not isfinite(v):raise ValueError('Nonfinite appearance specification.')
            return round(v,6) or 0.
        if isinstance(v,dict):return {k:canonical(x) for k,x in v.items()}
        if isinstance(v,(list,tuple)):return [canonical(x) for x in v]
        return v
    return hashlib.sha256(json.dumps(canonical(value),sort_keys=True,separators=(',',':')).encode()).hexdigest()


def segment_distance(point,a,b):
    d=[b[k]-a[k] for k in range(3)]
    t=max(0,min(1,sum((point[k]-a[k])*d[k] for k in range(3))/sum(v*v for v in d)))
    return dist(point,[a[k]+t*d[k] for k in range(3)])


class TokyoTowerBaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=TOWERS['tokyo-tower'];cls.c=_base_config(cls.p)
        cls.parts=component_specs('tokyo-tower');cls.by={p['name']:p for p in cls.parts}

    def test_original_leg_members_below80m_remain_exact_r06_source_geometry(self):
        def legacy(part):
            name=part['name']
            if re.fullmatch(r'structure:leg_\d+_shoe_plate',name):return True
            match=re.fullmatch(r'structure:leg_\d+_(?:chord_\d+|web_\d+|tie_\d+)_(\d+)',name)
            return bool(match and int(match[1])<=7)
        legs=[p for p in self.parts if legacy(p)]
        self.assertEqual(len(legs),340)
        # Independent6bbcb73/R06 baseline, with six-decimal-mm libm tolerance.
        # Only the four old80m head plates move into the Main Deck; all other
        # legacy leg members retain their original fields and order.
        self.assertEqual(fingerprint(legs),'8cdea4e6f618c3d83d10a5cd1943a4af96a4386f12edd0270fd936db207dca73')
        self.assertEqual(self.p['base_width_mm'],80000)

    def test_four_member_legs_continue_smoothly_to_the_main_deck(self):
        levels=_leg_frame_levels(self.p)
        self.assertEqual(levels[-7:],[80000,88000,98000,106000,114000,120000,125000])
        widths=[_leg_cage_half(self.p,z) for z in range(80000,125001,250)]
        self.assertEqual((widths[0],widths[-1]),(1000,450))
        self.assertTrue(all(a>b for a,b in zip(widths,widths[1:])))
        ribs=[p for p in self.parts if p.get('leg_continuation')]
        self.assertEqual(len(ribs),4*4*6)
        self.assertTrue(all(p['kind']=='loft3d' and p['role']=='primary_chord' for p in ribs))
        self.assertTrue(all(abs(p['section_profile']['width_mm']-525)<1e-7 for p in ribs))
        for leg in range(1,5):
            for chord in range(4):
                old=self.by[f'structure:leg_{leg:02d}_chord_{chord:02d}_07']
                first=self.by[f'structure:leg_{leg:02d}_chord_{chord:02d}_08']
                last=self.by[f'structure:leg_{leg:02d}_chord_{chord:02d}_13']
                self.assertLess(dist(old['axis_end'],first['nominal_axis_start']),1e-7)
                self.assertAlmostEqual(old['section_profile']['width_mm'],first['section_profile']['width_mm'],delta=1e-7)
                self.assertLess(first['axis_start'][2],80000)
                self.assertGreater(last['axis_end'][2],125000)
            plate=self.by[f'structure:leg_{leg:02d}_head_plate']['bounds']
            self.assertEqual((plate[2]+plate[5])/2,125000)
            self.assertLess(max(abs(x) for x in (plate[0],plate[1],plate[3],plate[4])),14000)

    def test_continuation_links_land_on_both_actual_host_axes(self):
        links=[p for p in self.parts if p.get('role')=='leg_transition_link']
        self.assertEqual(len(links),4*4*7)
        for level in [80000,88000,98000,106000,114000,120000,125000]:
            members=[p for p in links if p['level_mm']==level]
            self.assertEqual({(p['leg_group'],p['leg_chord']) for p in members},
                             {(leg,chord) for leg in range(1,5) for chord in range(4)})
        for part in links:
            for endpoint,host_key in (('start','source_member'),('end','target_member')):
                host=self.by[part[host_key]];a,b=host['axis_start'],host['axis_end']
                self.assertEqual(host['kind'],'loft3d')
                self.assertLess(segment_distance(part[endpoint],a,b),1e-7,part['name'])
            self.assertIn('visual assumptions',part['scope'])

    def test_arch_has_real_in_plane_depth_and_retains_h3_reference_crown(self):
        ribs=[p for p in self.parts if p.get('steel_role')=='arch_plate_chord']
        self.assertEqual(len(ribs),4*2*2*self.c['arch_panel_count'])
        self.assertEqual({p['arch_layer'] for p in ribs},{'inner','outer'})
        self.assertTrue(all(p['kind']=='loft3d' and p['role']=='open_cross_frame' for p in ribs))
        self.assertTrue(all(len(section)==12 for p in ribs for section in p['sections']))
        middle=self.c['arch_panel_count']//2-1
        for side in range(4):
            for lane in range(2):
                outer=self.by[f'structure:lower_arch_{side}_{lane}_{middle}']
                inner=self.by[f'structure:lower_arch_inner_{side}_{lane}_{middle}']
                self.assertEqual(outer['end'][2],40000)
                self.assertEqual(inner['end'][2],40000-self.c['arch_rib_depth_mm'])
                self.assertEqual(outer['end'][2]-inner['end'][2],1800)
                self.assertEqual(outer['axis_end'],outer['end'])
                first=self.by[f'structure:lower_arch_{side}_{lane}_0']
                first_inner=self.by[f'structure:lower_arch_inner_{side}_{lane}_0']
                self.assertEqual(first['start'],first_inner['start'])
                self.assertEqual(first['start'][2],1300)

    def test_arch_face_geometry_is_fourfold_symmetric(self):
        ribs={(p['arch_side'],p['arch_lane'],p['arch_layer'],p['arch_segment']):p
              for p in self.parts if p.get('steel_role')=='arch_plate_chord'}
        for (side,lane,layer,segment),part in ribs.items():
            other=ribs[((side+1)%4,lane,layer,segment)]
            for key in ('start','end'):
                x,y,z=part[key]
                self.assertLess(dist([-y,x,z],other[key]),1e-7)

    def test_deep_truss_leaves_the_central_passage_open(self):
        arches=[p for p in self.parts if p.get('arch_side')==0 and p['group']=='structure']
        self.assertTrue(arches)
        # The building is a separate mass; the steel arch must not add a low
        # lintel or diagonal through the centre of its own open span.
        for z in (5000,15000,25000,34000,37000):
            point=[0,-25000,z]
            for part in arches:
                self.assertGreater(segment_distance(point,part['start'],part['end']),500,part['name'])

    def test_h3_bridge_targets_the_existing_lower_panel_axis(self):
        bridges=[p for p in self.parts if p['name'].startswith('structure:arch_spandrel_crown_bridge_')]
        self.assertEqual(len(bridges),4)
        for part in bridges:
            source=self.by[part['source_member']];target=self.by[part['target_member']]
            self.assertEqual(part['start'],source['end'])
            self.assertEqual(part['end'],target['start'])
            self.assertEqual(part['start'][2],40000)
            self.assertGreater(dist(part['start'],part['end']),500)

    def test_foot_town_has_opaque_upper_mass_and_retains_roof_stair_datum(self):
        c=self.c;roof=self.by['base:foot_town_roof']['bounds']
        self.assertEqual(c['foot_town_width_mm'],48000)
        self.assertEqual(c['foot_town_depth_mm'],44000)
        self.assertEqual(c['foot_town_floor_levels_mm'],[0,3600,7200,10800,14400,18300])
        self.assertEqual(roof[5],self.p['detail']['foot_town_roof_mm'])
        self.assertEqual(roof[5],18300)
        self.assertEqual(roof[0],-c['foot_town_width_mm']/2-c['foot_town_roof_overhang_mm'])
        self.assertEqual(roof[1],-c['foot_town_depth_mm']/2-c['foot_town_roof_overhang_mm'])
        self.assertTrue(any(p['name'].startswith('base:foot_town_upper_cladding_') for p in self.parts))
        panes=[p for p in self.parts if p['name'].startswith('base:foot_town_glazing_')]
        self.assertTrue(panes)
        self.assertTrue(all(max(s['z'] for s in p['sections'])<7200 for p in panes))
        housing=self.by['base:foot_town_rooftop_housing']['bounds']
        self.assertEqual(housing[2],roof[5])
        self.assertGreater(housing[1],self.p['detail']['external_stair_bounds_mm'][4])

    def test_front_entrance_and_lamps_follow_expanded_front_face(self):
        c=self.c;front=-c['foot_town_depth_mm']/2;pitch=c['foot_town_width_mm']/c['foot_town_bays_per_face']
        for index,x in enumerate((-pitch,pitch),1):
            lamp=self.by[f'base:entry_wall_light_housing_{index}']['bounds']
            lens=self.by[f'base:entry_wall_light_lens_{index}']['bounds']
            self.assertAlmostEqual((lamp[0]+lamp[3])/2,x)
            self.assertLess(lamp[1],front);self.assertGreater(lamp[4],front)
            self.assertLess(lens[1],lamp[1]);self.assertGreater(lens[4],lamp[1])
        for index in (0,1):
            door=self.by[f'base:entry_door_glazing_{index}']['bounds']
            self.assertTrue(front<door[1]<door[4]<front+150)
        canopy=self.by['base:foot_town_entry_canopy']['bounds']
        self.assertEqual(canopy[1],front-c['foot_town_canopy_projection_mm'])


class TokyoTowerBaseNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from cadgen import build123d as bd
        cls.bd=bd;cls.by={p['name']:p for p in component_specs('tokyo-tower')};cls.cache={}

    def shape(self,name):
        if name not in self.cache:self.cache[name]=_cad_shape(self.by[name],self.bd)
        result=self.cache[name]
        self.assertTrue(result.is_valid,name);self.assertGreater(result.volume,0,name)
        return result

    def contact(self,a,b):
        aa,bb=self.shape(a),self.shape(b)
        self.assertLess(aa.distance_to(bb),.01,(a,b))
        common=aa.intersect(bb)
        self.assertIsNotNone(common,(a,b))
        self.assertGreater(sum(s.volume for s in common.solids()),1.,(a,b))

    def test_arch_bends_webs_anchors_and_h3_bridge_have_real_contact(self):
        for a,b in (
            ('structure:lower_arch_0_0_0','structure:lower_arch_0_0_1'),
            ('structure:lower_arch_inner_0_0_7','structure:lower_arch_inner_0_0_8'),
            ('structure:lower_arch_diagonal_0_0_7','structure:lower_arch_0_0_7'),
            ('structure:lower_arch_inplane_tie_0_0_8','structure:lower_arch_inner_0_0_7'),
            ('structure:lower_arch_web_0_8','structure:lower_arch_0_0_7'),
        ):self.contact(a,b)
        for name in ('structure:lower_arch_anchor_0_0_0','structure:lower_arch_anchor_0_1_1',
                     'structure:arch_spandrel_crown_bridge_0'):
            part=self.by[name]
            self.contact(name,part['source_member']);self.contact(name,part['target_member'])

    def test_expanded_front_lamps_are_attached_to_piers_and_lenses(self):
        for index,bay in ((1,3),(2,5)):
            housing=f'base:entry_wall_light_housing_{index}'
            self.contact(housing,f'base:foot_town_pier_0_{bay}')
            self.contact(housing,f'base:entry_wall_light_lens_{index}')

    def test_continuing_cage_and_links_have_positive_native_connections(self):
        for a,b in (
            ('structure:leg_01_chord_00_07','structure:leg_01_chord_00_08'),
            ('structure:leg_01_chord_03_08','structure:leg_01_chord_03_09'),
            ('structure:leg_01_chord_00_13','structure:leg_01_head_plate'),
        ):self.contact(a,b)
        for station in (0,2,6):
            for chord in (0,3):
                name=f'structure:leg_01_continuation_link_{station}_{chord}'
                part=self.by[name]
                self.contact(name,part['source_member']);self.contact(name,part['target_member'])
        plate=self.by['structure:leg_01_head_plate']['bounds']
        centre=[(plate[i]+plate[i+3])/2 for i in range(3)]
        floor=next(p for p in self.by.values() if p.get('role')=='deck_floor' and p['kind']=='box'
                   and p['bounds'][5]==125000 and all(p['bounds'][i]<centre[i]<p['bounds'][i+3] for i in range(2)))
        self.contact('structure:leg_01_head_plate',floor['name'])


if __name__=='__main__':unittest.main()
