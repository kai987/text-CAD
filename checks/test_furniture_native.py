"""Compare batched Rust clearance checks with the original Shapely report.

Run .venv/bin/python -m unittest discover -s checks -p test_furniture_native.py.
Only polygon checks run; these tests do not build solids or export CAD files.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from shapely import affinity
from shapely.geometry import MultiPolygon, Polygon, box

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))

from lib.apartment_plan import P as APARTMENT,apartment_plan
from lib.house_plan import P as HOUSE,floor_plan
from lib import furniture_geometry as furniture


def original_report(floor,model_id,p):
    """Frozen pre-batch reference: direct independent Shapely predicates."""
    placements=furniture.furniture_placements(floor,model_id,p)
    rooms={room.id:room for room in floor.rooms}
    rows=[]
    def add(name,ok,evidence=None):
        rows.append({'check':name,'pass':bool(ok),'evidence':evidence})
    for index,item in enumerate(placements):
        shape=item.footprint()
        add(f'{item.room}:{item.id}:inside_room',rooms[item.room].shape.buffer(.001).covers(shape),list(shape.bounds))
        add(f'{item.room}:{item.id}:clear_walls',floor.walls.intersection(shape).area<.001)
        for name,bounds in floor.fixtures:
            if name=='ベッド':continue
            add(f'{item.room}:{item.id}:clear_fixture:{name}:{bounds}',shape.intersection(box(*bounds)).area<.001)
        for name,zone in furniture.clearance_zones(floor,model_id,p):
            add(f'{item.room}:{item.id}:clear_zone:{name}',shape.intersection(zone).area<.001)
        for other in placements[index+1:]:
            add(f'{item.room}:{item.id}:separate_from:{other.room}:{other.id}',shape.intersection(other.footprint()).area<.001)
    return rows


def native_available():
    try:
        furniture.polygon_metrics([box(0,0,1,1)],[(0,0)],[(0,0)],backend='rust')
    except (ImportError,ModuleNotFoundError,RuntimeError):
        return False
    return True


HAS_NATIVE=native_available()


class FurnitureClearanceTests(unittest.TestCase):
    def assert_reports_equal(self,floor,model_id,p,*,expect_fail=None):
        expected=original_report(floor,model_id,p)
        if expect_fail is not None:
            selected=[row for row in expected if expect_fail in row['check']]
            self.assertTrue(selected,f'missing adversarial check: {expect_fail}')
            self.assertTrue(any(not row['pass'] for row in selected),expect_fail)
        for backend in ('python','auto',*(['rust'] if HAS_NATIVE else [])):
            with self.subTest(backend=backend,model=model_id,floor=floor.number):
                self.assertEqual(furniture.clearance_report(floor,model_id,p,backend=backend),expected)
        return expected

    def test_all_actual_layouts_keep_every_original_row_name_order_evidence_and_decision(self):
        layouts=[('house',floor_plan(1),HOUSE,111),('house',floor_plan(2),HOUSE,54),
                 ('apartment',apartment_plan()[0],APARTMENT,228)]
        for model,floor,p,count in layouts:
            rows=self.assert_reports_equal(floor,model,p)
            self.assertEqual(len(rows),count)
            self.assertTrue(all(row['pass'] for row in rows))

    def test_rust_is_available_for_the_native_acceptance_cases(self):
        if not HAS_NATIVE:
            self.skipTest('Native spatial extension is not installed; python/auto parity still runs.')
        self.assert_reports_equal(floor_plan(2),'house',HOUSE)

    def test_blocking_a_hinged_door_and_its_entry_approach_is_rejected(self):
        for zone_name in ('D21:door_sweep','D21:master:650mm_approach'):
            floor=floor_plan(2)
            zone=dict(furniture.clearance_zones(floor,'house',HOUSE))[zone_name]
            point=zone.representative_point()
            placements=furniture.furniture_placements(floor,'house',HOUSE)
            placements[0]=replace(placements[0],x=point.x-50,y=point.y-50,width=100,depth=100,rotation=0)
            with patch.object(furniture,'furniture_placements',return_value=placements):
                self.assert_reports_equal(floor,'house',HOUSE,expect_fail=f'clear_zone:{zone_name}')

    def test_wardrobe_kitchen_routes_and_balcony_landings_reject_obstructions(self):
        scenarios=[('house',2,HOUSE,'wardrobe_0:650mm_front','master'),
                   ('house',1,HOUSE,'kitchen:900mm_working_front','ldk'),
                   ('house',1,HOUSE,'ldk:route_1:650mm','ldk'),
                   ('apartment',1,APARTMENT,'balcony_slider_900:800mm_landing','ldk'),
                   ('apartment',1,APARTMENT,'ldk:route_4:650mm','ldk')]
        for model,number,p,zone_name,room_id in scenarios:
            floor=floor_plan(number) if model=='house' else apartment_plan()[0]
            zone=dict(furniture.clearance_zones(floor,model,p))[zone_name]
            point=zone.representative_point()
            placements=furniture.furniture_placements(floor,model,p)
            index=next(i for i,item in enumerate(placements) if item.room==room_id)
            placements[index]=replace(placements[index],x=point.x-50,y=point.y-50,width=100,depth=100,rotation=0)
            with self.subTest(model=model,zone=zone_name),patch.object(furniture,'furniture_placements',return_value=placements):
                self.assert_reports_equal(floor,model,p,expect_fail=f'clear_zone:{zone_name}')

    def test_furniture_collision_and_fixture_collision_are_reported(self):
        floor=floor_plan(1)
        placements=furniture.furniture_placements(floor,'house',HOUSE)
        placements[1]=replace(placements[1],x=placements[0].x,y=placements[0].y)
        floor.fixtures.append(('injected_obstacle',tuple(placements[0].footprint().bounds)))
        with patch.object(furniture,'furniture_placements',return_value=placements):
            rows=self.assert_reports_equal(floor,'house',HOUSE,expect_fail='ldk:sofa:separate_from:ldk:coffee_table')
            self.assertTrue(any(not row['pass'] and 'clear_fixture:injected_obstacle' in row['check'] for row in rows))

    def test_room_buffer_retains_the_original_point_zero_zero_one_mm_tolerance(self):
        for outside,expected in ((.0005,True),(.0015,False)):
            floor=floor_plan(2)
            placements=furniture.furniture_placements(floor,'house',HOUSE)
            placements[2]=replace(placements[2],x=180-outside,y=5500,width=100,depth=100,rotation=0)
            with patch.object(furniture,'furniture_placements',return_value=placements):
                rows=self.assert_reports_equal(floor,'house',HOUSE)
                row=next(row for row in rows if row['check']=='bed3:bed:inside_room')
                self.assertEqual(row['pass'],expected)

    def test_room_holes_and_gaps_between_multipolygon_components_are_not_covered(self):
        shapes=[Polygon([(180,180),(3550,180),(3550,3280),(180,3280)],
                        holes=[[(500,500),(1000,500),(1000,1000),(500,1000)]]),
                MultiPolygon([box(180,180,700,1200),box(900,180,3550,1200)])]
        for room_shape in shapes:
            floor=floor_plan(2)
            next(room for room in floor.rooms if room.id=='master').shape=room_shape
            placements=furniture.furniture_placements(floor,'house',HOUSE)
            placements[0]=replace(placements[0],x=650,y=650,width=400,depth=200,rotation=0)
            with patch.object(furniture,'furniture_placements',return_value=placements):
                self.assert_reports_equal(floor,'house',HOUSE,expect_fail='master:bed:inside_room')

    def test_overlap_decision_retains_the_strict_point_zero_zero_one_mm_squared_threshold(self):
        for overlap,expected in ((.0009,True),(.0011,False)):
            floor=floor_plan(2)
            placements=furniture.furniture_placements(floor,'house',HOUSE)
            placements[0]=replace(placements[0],x=500,y=500,width=1,depth=1,rotation=0)
            floor.fixtures.append(('threshold_probe',(500,500,501,500+overlap)))
            with patch.object(furniture,'furniture_placements',return_value=placements):
                rows=self.assert_reports_equal(floor,'house',HOUSE)
                row=next(row for row in rows if 'master:bed:clear_fixture:threshold_probe' in row['check'])
                self.assertEqual(row['pass'],expected)

    def test_rotated_thin_overlaps_keep_exact_areas_and_the_clearance_threshold(self):
        # Quantized polygon BooleanOps previously reduced the 0.002 mm² case
        # below the real 0.001 mm² clearance threshold. The broad phase must
        # leave the original Shapely area/decision authoritative.
        for intended_area in (.0009,.0011,.002,.01):
            width=1000
            shapes=[affinity.rotate(box(0,0,width,width),17,origin=(0,0)),
                    affinity.rotate(box(width-intended_area/width,0,2*width,width),
                                    17,origin=(0,0))]
            expected=shapes[0].intersection(shapes[1]).area
            if intended_area==.002:self.assertGreater(expected,.001)
            for backend in ('python','auto',*(['rust'] if HAS_NATIVE else [])):
                with self.subTest(area=intended_area,backend=backend):
                    areas,covers=furniture.polygon_metrics(shapes,[(0,1)],[],backend=backend)
                    self.assertEqual(covers,[])
                    self.assertEqual(areas,[expected])
                    self.assertEqual(areas[0]<.001,expected<.001)

    def test_rotated_shared_hole_boundary_keeps_boundary_inclusive_coverage(self):
        outer=Polygon(box(0,0,1000,1000).exterior.coords,
                      holes=[box(500,300,700,700).exterior.coords])
        inner=box(200,400,500,600)
        for angle,offset in ((76.84573498979813,0),(17,1000000)):
            shapes=[affinity.translate(affinity.rotate(shape,angle,origin=(0,0)),offset,offset)
                    for shape in (outer,inner)]
            expected=shapes[0].covers(shapes[1])
            self.assertTrue(expected)
            for backend in ('python','auto',*(['rust'] if HAS_NATIVE else [])):
                with self.subTest(angle=angle,offset=offset,backend=backend):
                    areas,covers=furniture.polygon_metrics(shapes,[],[(0,1)],backend=backend)
                    self.assertEqual(areas,[])
                    self.assertEqual(covers,[expected])

    def test_one_batch_reuses_zone_polygons_and_each_footprint_once(self):
        floor=floor_plan(1)
        placements=furniture.furniture_placements(floor,'house',HOUSE)
        expected=original_report(floor,'house',HOUSE)
        footprint_calls=[]
        original_footprint=furniture.Placement.footprint
        def counted_footprint(item):
            footprint_calls.append(item)
            return original_footprint(item)
        with patch.object(furniture,'clearance_zones',wraps=furniture.clearance_zones) as zones,\
             patch.object(furniture,'polygon_metrics',wraps=furniture.polygon_metrics) as metrics,\
             patch.object(furniture.Placement,'footprint',counted_footprint):
            actual=furniture.clearance_report(floor,'house',HOUSE,backend='python')
        self.assertEqual(actual,expected)
        self.assertEqual(zones.call_count,1)
        self.assertEqual(len(footprint_calls),len(placements))
        self.assertEqual(metrics.call_count,1)
        geometries,area_pairs,cover_pairs=metrics.call_args.args
        self.assertEqual(len({id(shape) for shape in geometries}),len(geometries))
        self.assertEqual(len(area_pairs)+len(cover_pairs),len(expected))
        self.assertLess(len(geometries),len(expected)//2)


if __name__=='__main__':
    unittest.main()
