import sys
import unittest
from dataclasses import replace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from lib.attic_geometry import A, attic_dimensions, attic_manifest, attic_access_group, north_vent_openings, _north_vent_group
from lib.house_geometry import G
from lib.house_plan import P
from lib.orientation import canonical
from lib.house_redesign_plan import floor_plan
from shapely.geometry import box

class AtticLayoutTests(unittest.TestCase):
    def test_single_and_pair_keep_total_area_and_avoid_ridge_axis(self):
        p=canonical(P)
        for count in (1,2):
            a=replace(A,north_vent_count=count)
            windows=north_vent_openings(p,G,a)
            self.assertEqual(len(windows),count)
            self.assertAlmostEqual(sum(w['gross_area_m2'] for w in windows),.18)
            self.assertEqual(len(_north_vent_group(p,G,a).children),11*count)
            for w in windows:
                b=w['bounds_mm'];self.assertGreater(w['height_mm'],w['width_mm'])
                self.assertFalse(b[0]<=p.width/2<=b[3])
        with self.assertRaises(ValueError):north_vent_openings(p,G,replace(A,north_vent_count=3))

    def test_access_reflects_about_hatch_without_moving_its_aperture(self):
        p=canonical(P);old=replace(A,ladder_mirrored=False)
        d0=attic_dimensions(p,G,old);d1=attic_dimensions(p,G,A)
        twice_center=2*A.hatch_x+A.hatch_length
        for key in ('ladder_top_x','ladder_foot_x'):
            self.assertAlmostEqual(d0[key]+d1[key],twice_center)
        before=attic_access_group(p,G,old);after=attic_access_group(p,G,A)
        self.assertAlmostEqual(before.volume,after.volume,places=5)
        for b,a in zip(before.children,after.children):
            bb,ab=b.bounding_box(),a.bounding_box()
            self.assertAlmostEqual(bb.min.X+ab.max.X,twice_center,places=5)
            self.assertAlmostEqual(bb.max.X+ab.min.X,twice_center,places=5)

    def test_mirrored_hall_landings_and_east_guardrail_entry(self):
        record=attic_manifest(P,G)
        hall=next(r.shape for r in floor_plan(2).rooms if r.id=='hall')
        self.assertEqual(record['ladder']['entry_side'],'east')
        self.assertEqual(record['hatch_bounds_mm'][0],P.width-A.hatch_x-A.hatch_length)
        for key in ('deployed_plan_bounds_mm','bottom_landing_bounds_mm'):
            self.assertTrue(hall.covers(box(*record['ladder'][key])))
        self.assertLess(record['ladder']['foot_mm'][0],record['ladder']['top_mm'][0])

if __name__=='__main__':unittest.main()
