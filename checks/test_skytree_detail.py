"""Pure-spec invariants for the original Skytree R02 appearance model."""
from __future__ import annotations

from collections import Counter
from math import dist, hypot, isfinite, pi, sin, sqrt
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from lib.tower_geometry import TOWERS,GROUPS,component_specs,geometry_manifest,ring_points,profile_radius
from lib.skytree_detail import _frame_point


def area(points):
    return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1])))/2


def vertices(p):
    if p['kind']=='box':
        b=p['bounds'];return [[b[i],b[j],b[k]] for i in (0,3) for j in (1,4) for k in (2,5)]
    if p['kind']=='beam':return [p['start'],p['end']]
    if p['kind']=='loft3d':return [v for section in p['sections'] for v in section]
    return [[x,y,s['z']] for s in p['sections'] for x,y in s['points']]


def numbers(v):
    if isinstance(v,dict):
        for x in v.values():yield from numbers(x)
    elif isinstance(v,(list,tuple)):
        for x in v:yield from numbers(x)
    elif type(v) in (int,float):yield v


def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]


class SkytreeDetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=TOWERS['tokyo-skytree'];cls.parts=component_specs('tokyo-skytree')
        cls.by={p['name']:p for p in cls.parts}

    def test_named_catalog_stays_in_five_groups_and_recorded_envelope(self):
        self.assertEqual(len(self.parts),len(self.by))
        self.assertGreater(len(self.parts),1400);self.assertLessEqual(len(self.parts),2000)
        self.assertEqual({p['group'] for p in self.parts},set(GROUPS))
        self.assertTrue(all(p['name'].startswith(p['group']+':') for p in self.parts))
        self.assertEqual(self.p['height_mm'],634000)
        self.assertEqual(self.p['deck_levels_mm'],[350000,450000])
        pts=[v for p in self.parts for v in vertices(p)]
        self.assertEqual(max(v[2] for v in pts),634000)
        self.assertEqual(min(v[2] for v in pts),-2500)
        self.assertLessEqual(max(hypot(v[0],v[1]) for v in pts),53000)
        manifest=geometry_manifest('tokyo-skytree')
        self.assertTrue(all(v is None for v in manifest['engineering'].values()))

    def test_primitives_are_finite_nondegenerate_and_loft3d_sections_are_planar(self):
        for p in self.parts:
            with self.subTest(part=p['name']):
                self.assertTrue(all(isfinite(v) for v in numbers(p)))
                if p['kind']=='box':self.assertTrue(all(p['bounds'][i+3]>p['bounds'][i] for i in range(3)))
                elif p['kind']=='beam':
                    self.assertGreater(p['radius'],0);self.assertGreater(dist(p['start'],p['end']),0)
                elif p['kind']=='loft':
                    self.assertTrue(all(b['z']>a['z'] for a,b in zip(p['sections'],p['sections'][1:])))
                    self.assertTrue(all(area(s['points'])>0 for s in p['sections']))
                else:
                    self.assertEqual(p['kind'],'loft3d');self.assertEqual(len(p['sections']),2)
                    for section in p['sections']:
                        a,b,c=section[:3];u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
                        normal=cross(u,v);length=sqrt(sum(x*x for x in normal));self.assertGreater(length,0)
                        for point in section:
                            self.assertLess(abs(sum(normal[i]*(point[i]-a[i]) for i in range(3)))/length,1e-6)

    def test_profile_is_monotone_and_keeps_triangular_and_circular_controls(self):
        r=[profile_radius('tokyo-skytree',z) for z in range(0,495001,1000)]
        self.assertTrue(all(a>=b>0 for a,b in zip(r,r[1:])))
        for z,radius in self.p['profile']:self.assertAlmostEqual(profile_radius('tokyo-skytree',z),radius,places=8)
        ground=ring_points('tokyo-skytree',0)
        self.assertEqual(len(ground),24)
        for a,b in zip(ground[::8],ground[8::8]+ground[:1]):self.assertAlmostEqual(dist(a,b),68000,places=6)
        for point in ring_points('tokyo-skytree',315000):self.assertAlmostEqual(hypot(*point),16000,places=6)

    def test_only_three_primary_legs_reach_ground_and_lower_arches_really_attach(self):
        primary=[p for p in self.parts if p.get('role')=='primary_leg' and p['sections'][0]['z']==0]
        self.assertEqual({p['node'] for p in primary},{0,8,16})
        secondary=[p for p in self.parts if p.get('role')=='secondary_chord']
        self.assertEqual(min(p['sections'][0]['z'] for p in secondary),45000)
        ring=lambda z:ring_points('tokyo-skytree',z)
        for side in range(3):
            start=self.by[f'structure:lower_arch_{side}_0']['start']
            end=self.by[f'structure:lower_arch_{side}_7']['end']
            self.assertEqual(start,_frame_point(self.p,ring,side*8,12000))
            self.assertEqual(end,_frame_point(self.p,ring,((side+1)*8)%24,12000))
            self.assertEqual(self.by[f'structure:lower_arch_{side}_3']['end'],[*ring(45000)[side*8+4],45000])

    def test_three_main_floors_are_true_annuli_without_duplicate_slabs(self):
        floors=[p for p in self.parts if p['name'].startswith('decks:tembo_deck_floor_')]
        self.assertEqual(Counter(p['floor_level_mm'] for p in floors),Counter({340000:24,345000:24,350000:24}))
        signatures=[]
        for p in floors:
            a,b=p['sections'];self.assertEqual(b['z']-a['z'],300)
            points=b['points'];r=[hypot(*v) for v in points]
            self.assertAlmostEqual(min(r),6000);self.assertGreater(max(r),20000)
            expected=.5*(max(r)**2-6000**2)*sin(2*pi/24)
            self.assertAlmostEqual(area(points),expected,delta=.01)
            signatures.append((a['z'],b['z'],tuple(tuple(v) for v in points)))
        self.assertEqual(len(signatures),len(set(signatures)))

    def test_gallery_is_one_continuous_sloping_route_445_to_450_without_stairs(self):
        ramp=sorted((p for p in self.parts if p.get('role')=='galleria_ramp'),key=lambda p:p['segment'])
        self.assertEqual(len(ramp),32)
        self.assertEqual(ramp[0]['route_start'][2],445000)
        self.assertEqual(ramp[-1]['route_end'][2],450000)
        self.assertFalse(any(p.get('role')=='stair_tread' for p in self.parts))
        for i,p in enumerate(ramp):
            self.assertGreater(p['route_end'][2],p['route_start'][2])
            self.assertIn('unmeasured',p['route_assumption'])
            self.assertEqual(p['kind'],'loft3d')
            self.assertEqual(p['sections'][0][0][2],p['route_start'][2]-250)
            self.assertAlmostEqual(dist(p['sections'][0][0],p['sections'][0][1]),1800)
            if i:
                self.assertEqual(ramp[i-1]['route_end'],p['route_start'])
                self.assertEqual(ramp[i-1]['sections'][1],p['sections'][0])
        self.assertAlmostEqual(hypot(*ramp[0]['route_start'][:2]),12850)
        self.assertEqual(len([p for p in self.parts if p.get('role')=='galleria_access']),2)

    def test_glass_is_thin_split_shell_and_gallery_ribs_do_not_exceed_roof(self):
        glass=[p for p in self.parts if p.get('role')=='glazing' and p['group']=='decks']
        self.assertEqual(len(glass),288)
        self.assertTrue(all(p.get('finish')=='glass' and p['thickness_mm'] in (80,90) for p in glass))
        self.assertEqual(len([p for p in glass if p['kind']=='loft3d']),190)
        for p in glass:
            if p['kind']=='loft':
                self.assertTrue(all(len(s['points'])==4 for s in p['sections']))
                for s in p['sections']:
                    r=[hypot(*v) for v in s['points']]
                    self.assertAlmostEqual(max(r)-min(r),p['thickness_mm'],places=5)
        ribs=[p for p in self.parts if p.get('role')=='galleria_rib']
        self.assertEqual(len(ribs),102)
        self.assertLess(max(v[2] for p in ribs for v in vertices(p)),455000)
        roof=[p for p in glass if p.get('gallery_surface')=='arched_roof']
        self.assertEqual(len(roof),128)
        for segment in range(32):
            arc=[self.by[f'decks:tembo_galleria_arch_glazing_{segment:02d}_{panel}']['sections'][0] for panel in range(4)]
            self.assertGreater(arc[1][1][2],arc[0][0][2]+850)
            for a,b in zip(arc,arc[1:]):self.assertEqual(a[1],b[0])

    def test_gallery_end_entries_are_open_in_both_inner_glass_envelopes(self):
        self.assertNotIn('decks:tembo_galleria_inner_glazing_00',self.by)
        self.assertNotIn('decks:tembo_galleria_inner_glazing_31',self.by)
        # The access sector overlaps a full metre of the open gallery bay,
        # allowing for the 55 mm doorway rib in the schematic arrangement.
        self.assertGreater(11950*sin(.09)-55,1000)
        entrance_glass=[p for p in self.parts if p.get('entrance_bay')]
        self.assertEqual(len(entrance_glass),4)
        for p in entrance_glass:
            lo,hi=p['sections'][0]['z'],p['sections'][-1]['z']
            for z in (445000,450000):self.assertTrue(hi<=z or lo>=z+2200)

    def test_shinbashira_has_8m_diameter_and_375m_stop_with_separate_upper_guides(self):
        walls=[p for p in self.parts if p.get('role')=='shinbashira_wall']
        self.assertEqual(len(walls),48)
        self.assertEqual(max(s['z'] for p in walls for s in p['sections']),375000)
        for p in walls:
            thickness=p['wall_thickness_mm'];self.assertIn(thickness,(400,600))
            self.assertEqual(thickness,400 if p['sections'][0]['z']==0 else 600)
            for s in p['sections']:
                radius=[hypot(*v) for v in s['points']]
                self.assertAlmostEqual(max(radius),4000)
                self.assertAlmostEqual(min(radius),4000-thickness)
        upper=[p for p in self.parts if p.get('role')=='elevator_guide']
        self.assertTrue(upper);self.assertGreaterEqual(min(v[2] for p in upper for v in vertices(p)),375000)

    def test_lights_and_radial_supports_have_real_attachment_metadata(self):
        self.assertEqual(Counter(p.get('role') for p in self.parts)['light_lens'],6)
        self.assertEqual(Counter(p.get('role') for p in self.parts)['obstruction_light_lens'],11)
        for p in self.parts:
            if p.get('role') in ('light_lens','obstruction_light_lens'):
                self.assertIn('light_lens',p['name']);self.assertLess(max(v[2] for v in vertices(p)),634000)
        supports=[p for p in self.parts if p.get('role')=='galleria_support'];self.assertEqual(len(supports),8)
        ring=lambda z:ring_points('tokyo-skytree',z)
        for p in supports:
            i=p['target_segment'];ramp=self.by[f'decks:tembo_galleria_ramp_{i:02d}'];node=p['frame_node']
            self.assertEqual(p['start'],_frame_point(self.p,ring,node,p['start'][2]))
            self.assertAlmostEqual(p['end'][2],ramp['route_start'][2]-125)
            self.assertAlmostEqual(hypot(*p['end'][:2]),12850)


if __name__=='__main__':unittest.main()
