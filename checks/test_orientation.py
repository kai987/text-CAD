"""World-space reflection contracts, including transformed CAD ancestors."""
import sys
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from cadgen import build123d as bd
from lib.orientation import shape,record,bounds,side_name
from lib.house_redesign_plan import P,floor_plan

class OrientationTests(unittest.TestCase):
    def test_nested_cad_transforms_are_preserved_before_reflection(self):
        leaf=bd.Box(10,20,30,align=(bd.Align.MIN,)*3);leaf.label='west_piece'
        group=bd.Compound(children=[leaf],label='group').rotate(bd.Axis.Z,90).moved(bd.Location((500,700,2800)))
        expected=group.bounding_box();reflected=shape(group,P.width);actual=reflected.bounding_box()
        self.assertAlmostEqual(actual.min.X,P.width-expected.max.X)
        self.assertAlmostEqual(actual.max.X,P.width-expected.min.X)
        self.assertAlmostEqual(actual.min.Y,expected.min.Y)
        self.assertAlmostEqual(actual.min.Z,2800)
        self.assertEqual(reflected.children[0].label,'east_piece')
        self.assertEqual(group.children[0].label,'west_piece')
    def test_empty_named_group_survives(self):
        empty=shape(bd.Compound(label='empty'),P.width)
        self.assertEqual(empty.label,'empty')
        self.assertFalse(empty)
    def test_explicit_world_records_and_directions(self):
        data={'axis':'h','at':90,'start':600,'end':1500,'vehicle_envelopes_mm':[[100,200,500,700]],'light_position_glb_m':[1,2,3]}
        mirrored=record(data,P.width)
        self.assertEqual((mirrored['start'],mirrored['end']),(6690,7590))
        self.assertEqual(mirrored['vehicle_envelopes_mm'],[[7690,200,8090,700]])
        self.assertAlmostEqual(mirrored['light_position_glb_m'][0],7.19)
        self.assertEqual(side_name('attic:storage:southwest_box:body'),'attic:storage:southeast_box:body')
        self.assertEqual(bounds(bounds([20,30,60,90],P.width),P.width),[20,30,60,90])
    def test_mirrored_swing_hinge_stays_at_reflected_original_hinge(self):
        d=next(d for d in floor_plan(1).doors if d.id=='D01')
        self.assertTrue(d.hinge_at_end)
        self.assertLess(d.start+d.width,P.width/2)

if __name__=='__main__':unittest.main()
