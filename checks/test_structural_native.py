"""Compare native broad-phase filtering with exact structural coordination.

Run after building the optional PyO3 extension:
    .venv/bin/python checks/test_structural_native.py

No STEP, GLB, drawing or review artifact is written by these tests.
"""
from __future__ import annotations

import gc
import json
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))

from cadgen import build123d as bd
from lib.attic_geometry import A
from lib.house_geometry import G, opening_box
from lib.house_plan import P, floor_plan, dimensions
from lib.native_spatial import aabb_candidates
from lib import structural_variants as variants


def full_scan_report(assembly,system):
    """Original all-member scan, retaining the real native narrow phase."""
    def all_members(bounds,queries,epsilon=1e-6,*,backend='auto'):
        return [list(range(len(bounds))) for _ in queries]
    with patch.object(variants,'aabb_candidates',all_members):
        return variants.geometry_coordination(assembly,system,backend='python')


class StructuralBroadPhaseTests(unittest.TestCase):
    def test_touching_and_epsilon_boundaries_use_the_original_strict_predicate(self):
        bounds=[[0.,0.,0.,10.,10.,10.],[30.,0.,0.,40.,10.,10.],
                [-20.,-20.,-20.,-10.,-10.,-10.]]
        queries=[[10.,0.,0.,20.,10.,10.],
                 [10.-.5e-6,0.,0.,20.,10.,10.],
                 [10.-1e-6,0.,0.,20.,10.,10.],
                 [10.-2e-6,0.,0.,20.,10.,10.],
                 [0.,10.,0.,10.,20.,10.],
                 [0.,0.,10.,10.,10.,20.],
                 [-10.,0.,0.,0.,10.,10.],
                 [0.,-10.,0.,10.,0.,10.],
                 [0.,0.,-10.,10.,10.,0.],
                 [-21.,-21.,-21.,-9.,-9.,-9.],
                 [-100.,-100.,-100.,100.,100.,100.]]
        expected=[[],[],[],[0],[],[],[],[],[],[2],[0,1,2]]
        self.assertEqual(aabb_candidates(bounds,queries,backend='python'),expected)
        self.assertEqual(aabb_candidates(bounds,queries,backend='rust'),expected)

    def test_hollow_member_candidate_is_rejected_by_native_solid_intersection(self):
        beam=variants._axis_tube((0,0,0,100,20,20),'h',2,'test:hollow')
        void=variants.solid_box((10,5,5,90,15,15),'test:void','#FFFFFF')
        material=variants.solid_box((10,.5,.5,90,1.5,1.5),'test:material','#FFFFFF')
        queries=[variants.shape_bounds(void),variants.shape_bounds(material)]
        for backend in ('python','rust'):
            self.assertEqual(aabb_candidates([variants.shape_bounds(beam)],queries,backend=backend),[[0],[0]])
        self.assertAlmostEqual(variants._overlap(beam,void),0.,places=6)
        self.assertGreater(variants._overlap(beam,material),1.)

    def test_positive_aperture_hits_keep_original_member_order_and_volumes(self):
        door=floor_plan(1,P).doors[0]
        tool=opening_box(door.axis,door.at,door.start+.1,door.width-.2,
            P.external_wall if door.a=='outside' else P.internal_wall,.1,G.door_height-.1)
        bounds=variants.shape_bounds(tool)
        assembly=bd.Compound(children=[
            variants.solid_box(bounds,'test:second','#FFFFFF'),
            variants.solid_box(bounds,'test:first','#FFFFFF'),
            variants.solid_box((bounds[3],bounds[1],bounds[2],bounds[3]+100,bounds[4],bounds[5]),
                               'test:touching','#FFFFFF')],label='test:apertures')
        python=variants.geometry_coordination(assembly,'W',backend='python')
        native=variants.geometry_coordination(assembly,'W',backend='rust')
        self.assertEqual(python,native)
        self.assertEqual(python,full_scan_report(assembly,'W'))
        hits=python['apertures'][0]['overlaps']
        self.assertEqual([hit['member'] for hit in hits],['test:second','test:first'])
        self.assertTrue(all(hit['volume_mm3']>.1 for hit in hits))


class ActualStructuralReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assemblies={}
        cls.reports={}
        cls.saved=json.loads((ROOT/'output/review/structural_variants_R07.json').read_text())['variants']
        for system in ('W','S','RC'):
            started=time.perf_counter()
            assembly=variants.build_variant(system)
            cls.assemblies[system]=assembly
            cls.reports[system]={
                'python':variants.geometry_coordination(assembly,system,backend='python'),
                'rust':variants.geometry_coordination(assembly,system,backend='rust'),
                'full_scan':full_scan_report(assembly,system),
            }
            print(f'{system}: built once; complete Python/native/full-scan reports in '
                  f'{time.perf_counter()-started:.2f}s',flush=True)

    @classmethod
    def tearDownClass(cls):
        cls.assemblies.clear()
        gc.collect()

    def test_all_three_complete_reports_match_python_and_original_full_scan(self):
        for system,reports in self.reports.items():
            with self.subTest(system=system):
                self.assertEqual(reports['python'],reports['rust'])
                self.assertEqual(reports['full_scan'],reports['rust'])
                self.assertEqual(self.saved[system]['coordination'],reports['rust'])

    def test_actual_member_bounds_match_all_indexed_queries(self):
        for system,assembly in self.assemblies.items():
            with self.subTest(system=system):
                bounds=[variants.shape_bounds(member) for member in variants.leaves(assembly)]
                python=aabb_candidates(bounds,bounds,backend='python')
                native=aabb_candidates(bounds,bounds,backend='rust')
                self.assertEqual(python,native)
                self.assertTrue(all(index in row for index,row in enumerate(native)))

    def test_actual_rc_stair_and_hatch_aabb_candidates_do_not_fill_real_voids(self):
        members={item.label:item for item in variants.leaves(self.assemblies['RC'])}
        slab=members['structure:F2:slab_floor']
        attic=members['structure:attic:slab_storage']
        sx,sy,xmax,ymax=next(room.shape.bounds for room in floor_plan(2).rooms if room.id=='stairs')
        stair_tool=variants.solid_box((sx+.1,sy+.1,2620.1,xmax-.1,ymax-.1,2799.9),
                                     'test:stair','#FFFFFF')
        hatch_x=P.width-A.hatch_x-A.hatch_length if P.mirror_layout else A.hatch_x
        hatch_tool=variants.solid_box((hatch_x+.1,A.hatch_y+.1,5420.1,
            hatch_x+A.hatch_length-.1,A.hatch_y+A.hatch_width-.1,5599.9),'test:hatch','#FFFFFF')
        for member,tool in ((slab,stair_tool),(attic,hatch_tool)):
            with self.subTest(member=member.label):
                bounds=[variants.shape_bounds(member)]
                queries=[variants.shape_bounds(tool)]
                self.assertEqual(aabb_candidates(bounds,queries,backend='rust'),[[0]])
                self.assertEqual(aabb_candidates(bounds,queries,backend='python'),[[0]])
                self.assertAlmostEqual(variants._overlap(member,tool),0.,places=6)


if __name__=='__main__':
    unittest.main(verbosity=2)
