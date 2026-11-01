"""Local shaft silhouette and unchanged-boundary checks for the R07 fit."""
from __future__ import annotations

from copy import deepcopy
from math import inf
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from lib.tower_geometry import TOWERS,_tower_paint
from lib.tokyo_tower_detail import (UPPER_SHAFT_OUTLINE_DEFAULTS,body_radius,profile_radius,
                                   component_specs,_square,_upper_frame_levels,_upper_frame_ring)
from lib.tokyo_tower_steel import refine_steel


class TokyoShaftOutlineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=deepcopy(TOWERS['tokyo-tower'])
        cls.p['detail']['upper_shaft_outline']=deepcopy(UPPER_SHAFT_OUTLINE_DEFAULTS)
        cls.c=cls.p['detail']['upper_shaft_outline']
        cls.off=deepcopy(cls.p);cls.off['detail']['upper_shaft_outline']['enabled']=False
        cls.ring=staticmethod(lambda z:_square(body_radius(cls.p,z)))
        old_ring=lambda z:_square(body_radius(cls.off,z))
        cls.parts=refine_steel(cls.p,component_specs(cls.p,cls.ring,_tower_paint))
        cls.old_parts=refine_steel(cls.off,component_specs(cls.off,old_ring,_tower_paint))
        cls.by={part['name']:part for part in cls.parts}
        cls.old_by={part['name']:part for part in cls.old_parts}

    def test_missing_or_disabled_fit_preserves_the_original_profile_exactly(self):
        missing=deepcopy(self.p);missing['detail'].pop('upper_shaft_outline')
        for z in [*range(0,333001,1000),223550,252650]:
            old=profile_radius(self.p['profile'],z)
            self.assertEqual(body_radius(missing,z),old)
            self.assertEqual(body_radius(self.off,z),old)

    def test_fit_preserves_both_endpoint_values_and_all_outside_samples_exactly(self):
        for z in [*range(0,130001,1000),*range(224000,333001,1000),223550,252650]:
            self.assertEqual(body_radius(self.p,z),profile_radius(self.p['profile'],z),z)
        self.assertEqual(body_radius(self.p,130000),9900.)
        self.assertEqual(body_radius(self.p,223550),3950.)
        for z,w in ((150000,8534.551769807),(190000,5838.619159208),
                    (210000,4617.862052294),(217000,4249.608716512)):
            self.assertAlmostEqual(body_radius(self.p,z),w,places=6)

    def test_boundary_tangents_match_the_unchanged_reference_on_both_sides(self):
        delta=.01
        for z,slope in ((self.c['start_mm'],self.c['start_slope_mm_per_mm']),
                        (self.c['end_mm'],self.c['end_slope_mm_per_mm'])):
            left=(body_radius(self.p,z)-body_radius(self.p,z-delta))/delta
            right=(body_radius(self.p,z+delta)-body_radius(self.p,z))/delta
            self.assertAlmostEqual(left,slope,delta=1e-6)
            self.assertAlmostEqual(right,slope,delta=1e-6)

    def test_active_fit_is_decreasing_convex_and_never_bulges_outside_endpoint_line(self):
        start,end=self.c['start_mm'],self.c['end_mm']
        zs=[start+(end-start)*i/1000 for i in range(1001)]
        radii=[body_radius(self.p,z) for z in zs]
        slopes=[(b-a)/(zb-za) for a,b,za,zb in zip(radii,radii[1:],zs,zs[1:])]
        self.assertTrue(all(slope<0 for slope in slopes))
        self.assertTrue(all(b>=a-1e-10 for a,b in zip(slopes,slopes[1:])))
        for z,radius in zip(zs,radii):
            t=(z-start)/(end-start)
            line=9900*(1-t)+3950*t
            self.assertLessEqual(radius,line+1e-7)

    def test_actual_straight_frame_stations_have_no_outward_knee(self):
        levels=[125000,*[z for z in _upper_frame_levels() if 130000<=z<=223550],231000]
        radii=[abs(_upper_frame_ring(self.ring,z)[0][0]) for z in levels]
        slopes=[(b-a)/(zb-za) for a,b,za,zb in zip(radii,radii[1:],levels,levels[1:])]
        self.assertTrue(all(slope<0 for slope in slopes))
        self.assertTrue(all(b>=a-1e-10 for a,b in zip(slopes,slopes[1:])))

    def test_only_local_frame_and_actual_top_deck_mounts_change(self):
        self.assertEqual(set(self.by),set(self.old_by))
        changed=[name for name in self.by if self.by[name]!=self.old_by[name]]
        self.assertTrue(changed)
        frame_prefixes=('structure:upper_chord_','structure:upper_diagonal_',
                        'structure:upper_return_','structure:upper_secondary_',
                        'structure:upper_secondary_return_','structure:upper_ring_')
        mounts=('decks:top_support_ring_','decks:top_underside_bracket_')
        for name in changed:
            part=self.by[name]
            if name.startswith(frame_prefixes):
                a,b=(part['axis_start'],part['axis_end']) if 'axis_start' in part else (part['start'],part['end'])
                self.assertGreaterEqual(min(a[2],b[2]),130000,name)
                self.assertLessEqual(max(a[2],b[2]),223550,name)
            else:self.assertTrue(name.startswith(mounts),name)
        for name,part in self.by.items():
            if part['group'] in ('base','core','antenna') or name.startswith('decks:top_service_'):
                self.assertEqual(part,self.old_by[name],name)

    def test_top_deck_mounts_use_the_real_straight_frame_not_an_envelope_point(self):
        z=216550.;ring=_upper_frame_ring(self.ring,z);half=abs(ring[0][0])
        for side in range(4):
            part=self.by[f'decks:top_support_ring_{side}']
            self.assertEqual(part['start'],[*ring[side],z])
            self.assertEqual(part['end'],[*ring[(side+1)%4],z])
        for i in range(8):
            part=self.by[f'decks:top_underside_bracket_{i}']
            self.assertEqual(part['start'][2],z)
            self.assertAlmostEqual(max(abs(v) for v in part['start'][:2]),half)
            self.assertEqual(part['end'],self.old_by[part['name']]['end'])
        self.assertNotEqual(half,body_radius(self.p,z))

    def test_invalid_or_discontinuous_fits_fail_before_export(self):
        for override in ({'start_mm':223550.},{'end_mm':inf},
                         {'start_half_width_mm':9901.},{'end_half_width_mm':0.},
                         {'start_slope_mm_per_mm':-.01},
                         {'start_slope_mm_per_mm':-.1,'end_slope_mm_per_mm':-.04},
                         {'method':'unsupported'}):
            p=deepcopy(self.p);p['detail']['upper_shaft_outline'].update(override)
            with self.subTest(override=override),self.assertRaises(ValueError):body_radius(p,175000.)


if __name__=='__main__':unittest.main()
