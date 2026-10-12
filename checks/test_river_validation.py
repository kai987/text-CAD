"""Cross-platform roundoff must not weaken saved river path validation."""
from copy import deepcopy
import json
from math import nextafter
from pathlib import Path
import unittest

from checks.validate_river import CENTRELINE_TOLERANCE_MM, centreline_samples_match
from lib.river_geometry import geometry_manifest


class RiverCentrelineValidationTests(unittest.TestCase):
    def setUp(self):
        self.expected = geometry_manifest()['centreline_samples']

    def test_saved_path_and_one_ulp_platform_variation_are_accepted(self):
        root = Path(__file__).resolve().parents[1]
        saved = json.loads((root / 'output/review/river_demo_manifest.json').read_text())
        self.assertTrue(centreline_samples_match(saved['centreline_samples'], self.expected))
        rounded = [[nextafter(value, float('inf')) for value in point] for point in self.expected]
        self.assertNotEqual(rounded, self.expected)
        self.assertTrue(centreline_samples_match(rounded, self.expected))

    def test_changed_geometry_is_rejected_on_each_axis(self):
        for axis in (0, 1):
            with self.subTest(axis=axis):
                changed = deepcopy(self.expected)
                changed[3][axis] += CENTRELINE_TOLERANCE_MM * 10
                self.assertFalse(centreline_samples_match(changed, self.expected))

    def test_missing_extra_and_reordered_samples_are_rejected(self):
        for actual in (None, {}, self.expected[:-1], self.expected + [[0, 0]],
                       list(reversed(self.expected))):
            self.assertFalse(centreline_samples_match(actual, self.expected))

    def test_malformed_points_and_nonfinite_or_nonnumeric_values_are_rejected(self):
        for point in ([0], [0, 0, 0], None, 'point', [True, 0], ['0', 0],
                      [float('nan'), 0], [float('inf'), 0], [0, -float('inf')]):
            with self.subTest(point=point):
                actual = deepcopy(self.expected)
                actual[0] = point
                self.assertFalse(centreline_samples_match(actual, self.expected))


if __name__ == '__main__':
    unittest.main()
