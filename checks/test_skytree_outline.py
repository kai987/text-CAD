"""Independent geometric acceptance of the source-informed Skytree outline."""
from copy import deepcopy
from math import cos, dist, hypot, isfinite, pi, sin, sqrt
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from lib.skytree_outline import (SKYTREE_OUTLINE_DEFAULTS, outline_config,
                                principal_radii, profile_radius, ring_points)


PARAMETERS = {
    'base_triangle_side_mm': 68000,
    'transition_height_mm': 315000,
    'transition_diameter_mm': 32000,
    'ring_divisions': 24,
    'detail': {'outline': {}},
}


def width(points, angle):
    values = [x*cos(angle)+y*sin(angle) for x, y in points]
    return max(values)-min(values)


def circle_radius(points):
    a, b, c = points
    twice_area = abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
    return dist(a, b)*dist(b, c)*dist(c, a)/(2*twice_area)


class SkytreeOutlineTests(unittest.TestCase):
    def test_ground_triangle_has_equal_edge_samples_and_published_approximate_side(self):
        points = ring_points(PARAMETERS, 0)
        self.assertEqual(len(points), 24)
        vertices = points[::8]
        for a, b in zip(vertices, vertices[1:]+vertices[:1]):
            self.assertAlmostEqual(dist(a, b), 68000, places=7)
        for side in range(3):
            for i in range(8):
                self.assertAlmostEqual(dist(points[side*8+i], points[(side*8+i+1)%24]), 8500, places=7)
        self.assertAlmostEqual(points[0][0], 0, places=7)
        self.assertAlmostEqual(points[0][1], 68000/sqrt(3), places=7)
        self.assertEqual(ring_points(PARAMETERS, -100), points)

    def test_transition_and_upper_reference_have_regular_24_point_circular_sections(self):
        for z, radius in ((315000, 16000), (495000, 9000), (497000, 9000-2000*7/180)):
            points = ring_points(PARAMETERS, z)
            for i, point in enumerate(points):
                self.assertAlmostEqual(hypot(*point), radius, places=7)
                expected = (radius*cos(pi/2+i*pi/12), radius*sin(pi/2+i*pi/12))
                self.assertLess(dist(point, expected), 1e-8)
            lengths = [dist(a, b) for a, b in zip(points, points[1:]+points[:1])]
            self.assertLess(max(lengths)-min(lengths), 1e-8)

    def test_upper_cone_is_linear_instead_of_historical_arbitrary_profile_controls(self):
        for z in range(315000, 497001, 1000):
            expected = 16000-(z-315000)*7/180
            self.assertAlmostEqual(profile_radius(PARAMETERS, z), expected, places=8)
        self.assertGreater(profile_radius(PARAMETERS, 495000), 6100)

    def test_face_midpoint_has_the_published_mukuri_character(self):
        ground = principal_radii(PARAMETERS, 0)
        at50 = principal_radii(PARAMETERS, 50000)
        at100 = principal_radii(PARAMETERS, 100000)
        at150 = principal_radii(PARAMETERS, 150000)
        self.assertGreater(at50[1], ground[1])
        self.assertGreater(at100[1], at50[1])
        self.assertGreater(at100[1], at150[1])
        self.assertAlmostEqual(at100[1], 20344.245858709, places=5)
        self.assertAlmostEqual(at100[0], 29482.395543598, places=5)
        for z in range(0, 315001, 5000):
            corner, midpoint = principal_radii(PARAMETERS, z)
            points = ring_points(PARAMETERS, z)
            for i in (0, 8, 16):
                self.assertAlmostEqual(hypot(*points[i]), corner, places=7)
            for i in (4, 12, 20):
                self.assertAlmostEqual(hypot(*points[i]), midpoint, places=7)

    def test_principal_guides_are_circles_tangent_to_the_same_upper_cone(self):
        samples = [principal_radii(PARAMETERS, z) for z in (0, 157500, 315000)]
        fits = [circle_radius([(sample[k], z) for sample, z in zip(samples, (0, 157500, 315000))])
                for k in range(2)]
        self.assertAlmostEqual(fits[0], 4534199.75858, places=3)
        self.assertAlmostEqual(fits[1], 5760565.10655, places=3)
        # Rounded endpoints do not make the separately published radii
        # exact extra constraints, and their record never drives geometry.
        self.assertNotAlmostEqual(fits[0], SKYTREE_OUTLINE_DEFAULTS['published_sori_radius_mm'], delta=1000)
        changed = deepcopy(PARAMETERS)
        changed['detail']['outline']['published_sori_radius_mm'] = 1
        self.assertEqual(ring_points(changed, 100000), ring_points(PARAMETERS, 100000))
        step = 0.1
        for k in range(2):
            derivative = (principal_radii(PARAMETERS, 315000)[k]
                          -principal_radii(PARAMETERS, 315000-step)[k])/step
            self.assertAlmostEqual(derivative, -7/180, delta=2e-8)
        # All intermediate guides meet the radial cone tangent too.
        above, below = ring_points(PARAMETERS, 315000+step), ring_points(PARAMETERS, 315000-step)
        for i, (a, b) in enumerate(zip(above, below)):
            angle = pi/2+i*pi/12
            for k, direction in enumerate((cos(angle), sin(angle))):
                self.assertAlmostEqual((a[k]-b[k])/(2*step), -7/180*direction, delta=2e-8)

    def test_sections_stay_finite_convex_and_threefold_symmetric(self):
        for z in range(0, 497001, 5000):
            points = ring_points(PARAMETERS, z)
            self.assertTrue(all(isfinite(v) for p in points for v in p))
            for i in range(24):
                a, b, c = (points[(i+j)%24] for j in range(3))
                cross = (b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0])
                self.assertGreaterEqual(cross, -1e-6)
                angle = 2*pi/3
                rotated = (a[0]*cos(angle)-a[1]*sin(angle), a[0]*sin(angle)+a[1]*cos(angle))
                self.assertLess(dist(rotated, points[(i+8)%24]), 1e-7)

    def test_different_views_retain_a_direction_dependent_lower_silhouette(self):
        base, lower, upper = (ring_points(PARAMETERS, z) for z in (0, 100000, 315000))
        self.assertAlmostEqual(width(base, 0), 68000, places=7)
        self.assertAlmostEqual(width(base, pi/2), 68000*sqrt(3)/2, places=7)
        self.assertGreater(abs(width(lower, 0)-width(lower, pi/2)), 1000)
        for angle in (0, pi/12, pi/6, pi/3, pi/2):
            self.assertAlmostEqual(width(upper, angle), 32000, places=7)
            self.assertAlmostEqual(width(lower, angle), width(lower, angle+2*pi/3), places=7)

    def test_custom_controls_are_used_without_mutating_defaults_or_caller(self):
        changed = deepcopy(PARAMETERS)
        changed['detail']['outline']['cone_reference_diameter_mm'] = 20000
        saved = deepcopy(changed)
        self.assertAlmostEqual(profile_radius(changed, 495000), 10000)
        self.assertEqual(changed, saved)
        config = outline_config(changed)
        config['cone_reference_height_mm'] = 1
        self.assertEqual(outline_config(PARAMETERS)['cone_reference_height_mm'], 495000)

    def test_invalid_or_nonfinite_controls_fail_before_building_cad(self):
        for key, value in (('transition_height_mm', 0), ('transition_diameter_mm', -1),
                           ('base_triangle_side_mm', float('nan')), ('ring_divisions', 12)):
            changed = deepcopy(PARAMETERS)
            changed[key] = value
            with self.assertRaises(ValueError):
                ring_points(changed, 100000)
        changed = deepcopy(PARAMETERS)
        changed['detail']['outline']['cone_reference_height_mm'] = 315000
        with self.assertRaises(ValueError):
            profile_radius(changed, 100000)
        for z in (float('nan'), float('inf'), 1000000):
            with self.assertRaises(ValueError):
                ring_points(PARAMETERS, z)


if __name__ == '__main__':
    unittest.main()
