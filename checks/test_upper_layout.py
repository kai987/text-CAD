"""R22 upper-floor coordination: actual source solids, not engineering approval."""
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
    def test_bath_fills_clear_room_span_and_shower_is_at_east_south_corner(self):
        from lib.fixture_geometry import fixture_group
        floor=floor_plan(1);bath=next(r for r in floor.rooms if r.id=='bath')
        tub=next(b for name,b in floor.fixtures if name=='浴槽')
        self.assertEqual((tub[0],tub[2]),(bath.shape.bounds[0],bath.shape.bounds[2]))
        group=next(g for g in fixture_group(floor,P).children if g.label.endswith('_bath'))
        rim=next(s for s in group.children if s.label.endswith(':tub_rim_ceramic')).bounding_box()
        self.assertAlmostEqual(rim.min.X,tub[0],places=3)
        self.assertAlmostEqual(rim.max.X,tub[2],places=3)
        head=next(s for s in group.children if s.label.endswith(':shower_head_chrome')).bounding_box()
        self.assertGreater((head.min.X+head.max.X)/2,tub[2]-200)
        self.assertLess((head.min.Y+head.max.Y)/2,tub[1]+200)

    def test_first_and_second_floor_vanities_use_identical_parts(self):
        from lib.fixture_geometry import fixture_group
        layouts=[floor_plan(n) for n in (1,2)]
        groups=[next(g for g in fixture_group(f,P).children if g.label.endswith('_vanity')) for f in layouts]
        fixtures=[next(b for name,b in f.fixtures if name in ('洗面','手洗い')) for f in layouts]
        self.assertEqual(sorted((fixtures[0][2]-fixtures[0][0],fixtures[0][3]-fixtures[0][1])),[450,600])
        volumes=[{s.label.split(':')[-1]:s.volume for s in g.children} for g in groups]
        self.assertEqual(volumes[0].keys(),volumes[1].keys())
        for name in volumes[0]:self.assertAlmostEqual(volumes[0][name],volumes[1][name],places=3)
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

    def test_two_bedroom_sliders_are_closed_along_their_openings(self):
        floor=floor_plan(2);doors=door_group(floor,P,G)
        leaves={s.label:s for s in doors.children}
        for ident in ('D21','D23'):
            door=next(d for d in floor.doors if d.id==ident)
            self.assertEqual(door.kind,'slide')
            self.assertIn(f'F2:{ident}_slide_track',leaves)
            b=leaves[f'F2:{ident}_door_slide'].bounding_box()
            footprint=box(b.min.X,b.min.Y,b.max.X,b.max.Y)
            start,end=(b.min.X,b.max.X) if door.axis=='h' else (b.min.Y,b.max.Y)
            self.assertAlmostEqual(start,door.start+5)
            self.assertAlmostEqual(end,door.start+door.width-5)
            self.assertLess(footprint.intersection(door.opening(P.internal_wall)).area,.001,
                            'face-mounted door stays outside wall thickness')
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
