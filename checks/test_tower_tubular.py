"""Native checks: published-style hollow sections must contain actual bores."""
from pathlib import Path
import math
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from lib.tower_geometry import _cad_shape

def intersection_volume(shape,other):
    result=shape.intersect(other)
    if result is None:return 0.
    if isinstance(result,(list,tuple)):return sum(s.volume for s in result)
    return result.volume

class HollowTowerSectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from cadgen import build123d as bd
        cls.bd=bd

    def test_oblique_pipe_volume_bore_and_circular_surface(self):
        bd=self.bd;a=[100,200,300];b=[700,1000,2300];d=[b[i]-a[i] for i in range(3)];length=math.dist(a,b)
        s=_cad_shape({'kind':'tube','start':a,'end':b,'radius':1150,'wall_thickness_mm':100},bd)
        self.assertTrue(s.is_valid);self.assertEqual(len(s.solids()),1)
        self.assertAlmostEqual(s.volume,math.pi*(1150**2-1050**2)*length,delta=.1)
        bore=bd.Solid.make_cylinder(1040,length,plane=bd.Plane(origin=a,z_dir=d))
        self.assertAlmostEqual(intersection_volume(s,bore),0,delta=.001)
        self.assertEqual(len([f for f in s.faces() if f.geom_type==bd.GeomType.CYLINDER]),2)

    def test_ruled_annular_loft_remains_hollow_at_intermediate_station(self):
        bd=self.bd;sections=[{'z':0,'center':[0,0],'radius':1150,'wall_thickness_mm':100},
            {'z':1000,'center':[100,50],'radius':1100,'wall_thickness_mm':90},
            {'z':2000,'center':[190,100],'radius':1050,'wall_thickness_mm':90}]
        s=_cad_shape({'kind':'tube_loft','sections':sections},bd)
        self.assertTrue(s.is_valid);self.assertEqual(len(s.solids()),1)
        centre=bd.Solid.make_cylinder(800,1800,plane=bd.Plane(origin=(100,50,100)))
        self.assertAlmostEqual(intersection_volume(s,centre),0,delta=.001)
        self.assertGreater(s.volume,0)

    def test_rectangular_tube_preserves_actual_wall_volume(self):
        bd=self.bd;a=[0,0,0];b=[400,200,1200]
        s=_cad_shape({'kind':'rhs','start':a,'end':b,'width_mm':400,'depth_mm':300,'wall_thickness_mm':12},bd)
        self.assertTrue(s.is_valid);self.assertEqual(len(s.solids()),1)
        self.assertAlmostEqual(s.volume,(400*300-376*276)*math.dist(a,b),delta=.001)

    def test_invalid_sections_are_rejected_before_export(self):
        for spec in [dict(kind='tube',start=[0,0,0],end=[0,0,100],radius=10,wall_thickness_mm=10),
                     dict(kind='rhs',start=[0,0,0],end=[0,0,100],width_mm=20,depth_mm=30,wall_thickness_mm=10)]:
            with self.assertRaises(ValueError):_cad_shape(spec,self.bd)

if __name__=='__main__':unittest.main()
