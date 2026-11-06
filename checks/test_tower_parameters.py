"""Per-model input isolation and validation against pre-split parameter hashes."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from lib.skytree_parameters import parameters as skytree_parameters
from lib.tokyo_tower_parameters import parameters as tokyo_tower_parameters
from lib.tower_geometry import TOWERS, geometry_source_paths
from lib.tower_parameters import validate_tower_parameters


FACTORIES = {'tokyo-tower': tokyo_tower_parameters, 'tokyo-skytree': skytree_parameters}
# Captured from the complete live R11/R05 parameter dictionaries before moving
# either literal. Independent historical geometry fixtures remain unchanged.
PRE_SPLIT_HASHES = {
    'tokyo-tower': 'b58a95b13cfd87f55d1c76ce2b43eee244cf42d5a0f6c16087d1a6a4625b9e12',
    'tokyo-skytree': 'cb521c71ba13f01438977d47c0371b74375e5dbf74112f33225968771e1e2e33',
}


class TowerParameterTests(unittest.TestCase):
    def test_complete_defaults_match_independent_pre_split_values(self):
        for tower_id, factory in FACTORIES.items():
            with self.subTest(tower=tower_id):
                parameters = factory()
                encoded = json.dumps(parameters, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':'), allow_nan=False).encode()
                self.assertEqual(sha256(encoded).hexdigest(), PRE_SPLIT_HASHES[tower_id])
                self.assertEqual(TOWERS[tower_id], parameters)
                self.assertIs(validate_tower_parameters(tower_id, parameters), parameters)

    def test_returned_defaults_have_no_shared_mutable_objects(self):
        for tower_id, factory in FACTORIES.items():
            with self.subTest(tower=tower_id):
                first = factory()
                saved = deepcopy(factory())
                first['profile'][0][1] += 1
                first['names']['ja'] = 'edited'
                first['detail'].clear()
                self.assertEqual(factory(), saved)
                self.assertEqual(TOWERS[tower_id], saved)

    def test_sources_bind_only_the_selected_model_defaults_and_shared_schema(self):
        for tower_id, own, other in [
            ('tokyo-tower', 'tokyo_tower_parameters', 'skytree_parameters'),
            ('tokyo-skytree', 'skytree_parameters', 'tokyo_tower_parameters'),
        ]:
            with self.subTest(tower=tower_id):
                sources = geometry_source_paths(tower_id)
                self.assertIn(f'src/lib/{own}.py', sources)
                self.assertNotIn(f'src/lib/{other}.py', sources)
                self.assertIn('src/lib/tower_parameters.py', sources)
                self.assertEqual(len(sources), len(set(sources)))
                self.assertTrue(all((ROOT / source).is_file() for source in sources))

    def test_identity_names_and_provenance_are_required(self):
        for field, value in [('file_stem', 'wrong_model'), ('profile_kind', 'wrong_kind'),
                             ('revision', 'LANDMARK-R0'), ('revision', 'future'),
                             ('names', {'ja': '東京タワー'}), ('source_references', []),
                             ('source_references', [{'url': 'file:///local'}]), ('detail', [])]:
            with self.subTest(field=field, value=value):
                parameters = tokyo_tower_parameters()
                parameters[field] = value
                with self.assertRaises(ValueError):
                    validate_tower_parameters('tokyo-tower', parameters)
        with self.assertRaisesRegex(ValueError, 'Unknown landmark'):
            validate_tower_parameters('other', tokyo_tower_parameters())
        with self.assertRaisesRegex(ValueError, 'dictionary'):
            validate_tower_parameters('tokyo-tower', [])

    def test_nonfinite_or_nonpositive_dimensions_are_rejected(self):
        for field in ('height_mm', 'base_width_mm', 'base_slab_thickness_mm', 'antenna_start_mm'):
            for value in (0, -1, float('inf'), float('nan'), True, '100'):
                with self.subTest(field=field, value=value):
                    parameters = tokyo_tower_parameters()
                    parameters[field] = value
                    with self.assertRaises(ValueError):
                        validate_tower_parameters('tokyo-tower', parameters)
        parameters = tokyo_tower_parameters()
        parameters['detail']['lower_grid_continuity']['primary_brace_radius_mm'] = float('nan')
        with self.assertRaisesRegex(ValueError, 'finite'):
            validate_tower_parameters('tokyo-tower', parameters)

    def test_decks_profile_and_antenna_stay_ordered_within_the_height(self):
        mutations = [
            ('deck_levels_mm', [223550, 125000]), ('deck_levels_mm', [125000, 125000]),
            ('deck_levels_mm', [333000]), ('nominal_deck_levels_mm', [0]),
            ('antenna_start_mm', 333000), ('profile', [[0, 1], [0, 2]]),
            ('profile', [[1, 40000], [25000, 30000]]), ('profile', [[0, 0], [100, 1]]),
            ('profile', [[0, 1], [333000, 2]]), ('profile', [[0, 1], [1]]),
            ('deck_specs', [{'id': 'main', 'bottom_mm': 10, 'glass_bottom_mm': 10, 'top_mm': 20}]),
        ]
        for field, value in mutations:
            with self.subTest(field=field, value=value):
                parameters = tokyo_tower_parameters()
                parameters[field] = value
                with self.assertRaises(ValueError):
                    validate_tower_parameters('tokyo-tower', parameters)


if __name__ == '__main__':
    unittest.main()
