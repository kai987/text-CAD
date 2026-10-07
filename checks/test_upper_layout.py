"""R21 upper-floor coordination: actual source solids, not engineering approval."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from lib.house_plan import P, floor_plan
from lib.house_geometry import G, door_group, wall_groups
from lib.house_redesign_plan import dimensions, hall_basin_bounds
from lib.orientation import canonical
from lib.attic_geometry import A, attic_manifest, attic_access_group
from lib.indoor_lighting import indoor_fixture_layout, indoor_lighting_group
from shapely.geometry import box


class UpperLayoutTests(unittest.TestCase):
    def test_relocated_trimmers_do_not_duplicate_regular_joists(self):
        from lib.structure_geometry import _attic_members, structure_dimensions, T
        q=canonical(P)
        joists,headers=_attic_members(q,G,structure_dimensions(q,G,T),[],T)
        for joist in joists:
            for header in headers:
                overlap=joist.intersect(header)
                self.assertLess(overlap.volume if overlap else 0,.01,
                                f'{joist.label} / {header.label}')

    def test_basin_centred_between_niche_ends(self):
        q=canonical(P);d=dimensions(q);b=hall_basin_bounds(q)
        self.assertAlmostEqual(b[1]-d['sy'],100)
        self.assertAlmostEqual(d['ym']-q.toilet_depth-q.internal_wall-b[3],100)
        self.assertEqual(b[3]-b[1],600)

    def test_two_bedroom_sliders_are_retracted_clear_of_openings(self):
        floor=floor_plan(2);doors=door_group(floor,P,G)
        leaves={s.label:s for s in doors.children}
        for ident in ('D21','D23'):
            door=next(d for d in floor.doors if d.id==ident)
            self.assertEqual(door.kind,'slide')
            self.assertIn(f'F2:{ident}_slide_track',leaves)
            b=leaves[f'F2:{ident}_door_slide'].bounding_box()
            footprint=box(b.min.X,b.min.Y,b.max.X,b.max.Y)
            self.assertLess(footprint.intersection(door.opening(P.internal_wall)).area,.001)
            self.assertTrue(any(r.shape.covers(footprint) for r in floor.rooms if r.id in (door.a,door.b)))

    def test_hatch_west_wall_gap_and_hall_lamp_clearance(self):
        record=attic_manifest(P,G);deck=record['deck_bounds_mm'];hatch=record['hatch_bounds_mm']
        self.assertAlmostEqual(hatch[0]-deck[0],100)
        hall=next(r.shape for r in floor_plan(2).rooms if r.id=='hall')
        for key in ('deployed_plan_bounds_mm','bottom_landing_bounds_mm'):
            self.assertTrue(hall.covers(box(*record['ladder'][key])))
        access=attic_access_group(P,G)
        light_group=indoor_lighting_group(2,P,G)
        lamp=next(g for g in light_group.children if g.label=='F2:indoor_light:hall')
        overlap=access.intersect(lamp)
        self.assertLess(overlap.volume if overlap else 0,.01)

    def test_wall_light_on_basin_wall_and_named_power_metadata(self):
        lights=indoor_fixture_layout(P,G)
        f=next(f for f in lights if f['id']=='indoor_F2_hall_vanity')
        self.assertEqual(f['style'],'wall_vanity')
        basin=next(b for name,b in floor_plan(2).fixtures if name=='手洗い')
        self.assertAlmostEqual(f['mount_center_mm'][1],(basin[1]+basin[3])/2)
        self.assertAlmostEqual(f['mount_center_mm'][0],basin[2])
        self.assertEqual(len(lights),16)


if __name__=='__main__':unittest.main()
