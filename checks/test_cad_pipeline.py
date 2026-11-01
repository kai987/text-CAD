"""Scoped dependency, isolated generation and rollback publication regressions.

No CAD runtime is required: small named files exercise the same staging and
publication paths as the expensive generators.
"""
from contextlib import ExitStack
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('cad_release', ROOT/'src/cad_release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)
spec = importlib.util.spec_from_file_location('cad_pipeline', ROOT/'src/cad_pipeline.py')
pipeline = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {'cad_release': release}):
    spec.loader.exec_module(pipeline)


class ScopedCadPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        files = {
            'src/cad_pipeline.py': '# pipeline\n',
            'src/cad_release.py': '# release\n',
            'src/towers_3d.py': 'from lib.tower_geometry import catalog\n',
            'src/generate_tower_plans.py': 'from lib.tower_geometry import catalog\n',
            'src/lib/tower_geometry.py': 'from .tokyo_tower_detail import tower\nfrom .skytree_detail import tree\n',
            'src/lib/tokyo_tower_detail.py': 'tower = 1\n',
            'src/lib/skytree_detail.py': 'tree = 1\n',
            'checks/check.py': '# verification\n',
            'requirements.txt': 'cadgen==test\n',
            'web/scripts/generate-plan-svg.py': '# preview\n',
            'GLB/tokyo_tower.glb': 'old tower',
            'GLB/tokyo_skytree.glb': 'old skytree',
            'output/review/design_manifest.json': '{"drawing_revision":"R22"}',
            'output/review/house_3d_assumptions_R01.json': '{"revision":"R22-3D"}',
        }
        for name, text in files.items():
            self.write(name, text)
        self.font = self.root/'test-font.ttf'
        self.font.write_bytes(b'font')
        self.baseline = {
            'schema_version': 1, 'drawing_revision': 'R22', 'model_revision': 'R22-3D',
            'validation_commands': ['checks/check.py'], 'scope': 'Concept only',
            'sources': pipeline._hashes(self.root, release.source_paths(self.root)),
            'artifacts': pipeline._hashes(self.root, release.artifact_paths(self.root)),
        }
        self.write(release.RELEASE, json.dumps(self.baseline))
        self.old_gate = (self.root/release.RELEASE).read_bytes()

    def write(self, name, text):
        path = self.root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def exercise(self, action=None, tests=None, *, refresh=False):
        def generate(commands, *, root):
            if commands != pipeline.VALIDATORS and commands:
                (root/'GLB/tokyo_tower.glb').write_bytes(b'new tower')
            if action:
                action(commands, root)

        with ExitStack() as stack:
            stack.enter_context(patch.object(pipeline, 'ROOT', self.root))
            stack.enter_context(patch.object(pipeline, 'run', side_effect=generate))
            stack.enter_context(patch.object(pipeline, 'run_unit_tests', side_effect=tests))
            stack.enter_context(patch.object(pipeline.importlib.metadata, 'version', return_value='test'))
            stack.enter_context(patch.dict(pipeline.os.environ, {'TEXT_CAD_CJK_FONT': str(self.font)}))
            stack.enter_context(patch.dict(sys.modules, {'cad_release': release}))
            pipeline.regenerate(tuple(pipeline.MODELS) if refresh else ('tokyo-tower',), refresh=refresh)

    def assert_unchanged(self):
        self.assertEqual((self.root/'GLB/tokyo_tower.glb').read_bytes(), b'old tower')
        self.assertEqual((self.root/'GLB/tokyo_skytree.glb').read_bytes(), b'old skytree')
        self.assertEqual((self.root/release.RELEASE).read_bytes(), self.old_gate)

    def test_selection_retains_full_default_and_scopes_tower_flags(self):
        self.assertEqual(pipeline.generation_commands(tuple(pipeline.MODELS)), pipeline.GENERATORS)
        self.assertEqual(pipeline.generation_commands(('tokyo-tower',)),
                         ['src/towers_3d.py --tower tokyo-tower',
                          'src/generate_tower_plans.py --model tokyo-tower'])
        self.assertEqual(pipeline.generation_commands(('river',)),
                         ['src/river_3d.py', 'src/generate_river_plans.py'])
        self.assertEqual(pipeline.generation_commands(('apartment',)), ['src/apartment_2ldk.py'])
        house = pipeline.generation_commands(('house',))
        self.assertEqual(len(house), 8)
        self.assertEqual(house[-1], 'web/scripts/generate-plan-svg.py')

    def test_own_tower_source_can_change_but_shared_catalog_requires_both(self):
        self.write('src/lib/tokyo_tower_detail.py', 'tower = 2\n')
        pipeline.check_scope(self.root, self.baseline, ('tokyo-tower',))
        self.write('src/lib/tower_geometry.py', 'from .tokyo_tower_detail import tower\nfrom .skytree_detail import tree\ncatalog = "changed for both towers"\n')
        with self.assertRaisesRegex(ValueError, 'tokyo-skytree'):
            pipeline.check_scope(self.root, self.baseline, ('tokyo-tower',))

    def test_unknown_new_and_removed_generation_sources_are_not_blessed(self):
        self.write('src/new_generator.py', 'new = 1\n')
        with self.assertRaisesRegex(ValueError, 'unknown dependency'):
            pipeline.check_scope(self.root, self.baseline, ('tokyo-tower',))
        (self.root/'src/new_generator.py').unlink()
        (self.root/'src/lib/skytree_detail.py').unlink()
        with self.assertRaises(ValueError):
            pipeline.check_scope(self.root, self.baseline, ('tokyo-tower',))

    def test_unselected_saved_cad_must_match_last_release(self):
        self.write('GLB/tokyo_skytree.glb', 'manual change')
        with self.assertRaisesRegex(ValueError, 'Unselected CAD artifact'):
            pipeline.check_scope(self.root, self.baseline, ('tokyo-tower',))

    def test_refresh_accepts_verification_only_sources(self):
        self.write('src/cad_pipeline.py', '# updated pipeline\n')
        self.write('checks/new_check.py', '# new check\n')
        pipeline.check_scope(self.root, self.baseline, tuple(pipeline.MODELS), refresh=True)
        self.write('src/lib/tokyo_tower_detail.py', 'tower = 2\n')
        with self.assertRaisesRegex(ValueError, 'Cannot refresh changed generation'):
            pipeline.check_scope(self.root, self.baseline, tuple(pipeline.MODELS), refresh=True)

    def test_refresh_rejects_modified_geometry_even_for_all_models(self):
        self.write('GLB/tokyo_tower.glb', 'changed')
        with self.assertRaisesRegex(ValueError, 'Unselected CAD artifact'):
            pipeline.check_scope(self.root, self.baseline, tuple(pipeline.MODELS), refresh=True)

    def test_generator_failure_preserves_live_preview_and_old_gate(self):
        def fail(commands, _root):
            if commands != pipeline.VALIDATORS:
                raise subprocess.CalledProcessError(1, ['generator'])
        with self.assertRaises(subprocess.CalledProcessError):
            self.exercise(action=fail)
        self.assert_unchanged()

    def test_saved_cad_validation_failure_preserves_live_outputs(self):
        def fail(commands, _root):
            if commands == pipeline.VALIDATORS:
                raise subprocess.CalledProcessError(1, ['validator'])
        with self.assertRaises(subprocess.CalledProcessError):
            self.exercise(action=fail)
        self.assert_unchanged()

    def test_shared_unit_failure_preserves_live_outputs(self):
        with self.assertRaises(subprocess.CalledProcessError):
            self.exercise(tests=subprocess.CalledProcessError(1, ['tests']))
        self.assert_unchanged()

    def test_complete_candidate_is_checked_before_gate_last_publication(self):
        def inspect(snapshot, *, root):
            self.assert_unchanged()
            self.assertFalse((root/release.RELEASE).exists())
            self.assertEqual((root/'GLB/tokyo_tower.glb').read_bytes(), b'new tower')
            self.assertEqual(release.verify_snapshot(root, snapshot)['revision'], 'R22')
        self.exercise(tests=inspect)
        self.assertEqual((self.root/'GLB/tokyo_tower.glb').read_bytes(), b'new tower')
        self.assertEqual((self.root/'GLB/tokyo_skytree.glb').read_bytes(), b'old skytree')
        self.assertEqual(release.verify(self.root)['revision'], 'R22')
        candidate = json.loads((self.root/release.RELEASE).read_text())
        self.assertEqual(candidate['selected_models'], ['tokyo-tower'])
        self.assertEqual(candidate['operation'], 'staged_regeneration')

    def test_generator_cannot_silently_change_unselected_output(self):
        def change(commands, root):
            if commands != pipeline.VALIDATORS:
                (root/'GLB/tokyo_skytree.glb').write_bytes(b'unrelated overwrite')
        with self.assertRaisesRegex(ValueError, 'unselected output'):
            self.exercise(action=change)
        self.assert_unchanged()

    def test_generator_cannot_remove_existing_output_from_live_catalog(self):
        def remove(commands, root):
            if commands != pipeline.VALIDATORS:
                (root/'GLB/tokyo_tower.glb').unlink()
        with self.assertRaisesRegex(ValueError, 'removed an existing CAD output'):
            self.exercise(action=remove)
        self.assert_unchanged()

    def test_concurrent_editor_change_aborts_promotion(self):
        def edit(_snapshot, *, root):
            self.write('src/cad_pipeline.py', '# edit while generating\n')
        with self.assertRaisesRegex(RuntimeError, 'changed during staging'):
            self.exercise(tests=edit)
        self.assert_unchanged()

    def test_refresh_runs_all_checks_without_changing_cad_bytes(self):
        self.write('checks/check.py', '# stronger verification\n')
        self.baseline.update(generated_at='2026-10-01T12:00:00+09:00',
                             generation_commands=['historic generator'], toolchain={'python': 'historic'})
        self.write(release.RELEASE, json.dumps(self.baseline))
        self.exercise(refresh=True)
        candidate = json.loads((self.root/release.RELEASE).read_text())
        self.assertEqual(candidate['operation'], 'validation_refresh')
        self.assertEqual(candidate['generation_commands'], ['historic generator'])
        self.assertEqual(candidate['generated_at'], self.baseline['generated_at'])
        self.assertEqual(candidate['toolchain'], {'python': 'historic'})
        self.assertEqual(candidate['validation_toolchain']['packages']['cadgen'], 'test')
        self.assertIn('validated_at', candidate)
        self.assertEqual(candidate['artifacts'], self.baseline['artifacts'])
        release.verify(self.root)

    def test_copy_failure_rolls_back_existing_and_new_files_and_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage = Path(temporary)
            for relative, data in [('GLB/tokyo_tower.glb', b'new'),
                                   ('GLB/tokyo_tower_new.glb', b'new file'),
                                   (release.RELEASE, b'new gate')]:
                path = stage/relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            replace = pipeline._replace_bytes
            failed = False
            def fail_once(path, source):
                nonlocal failed
                self.assertFalse((self.root/release.RELEASE).exists())
                if path.name == 'tokyo_tower_new.glb' and not failed:
                    failed = True
                    raise OSError('simulated disk failure')
                replace(path, source)
            with patch.object(pipeline, '_replace_bytes', side_effect=fail_once):
                with self.assertRaisesRegex(OSError, 'disk failure'):
                    pipeline.promote_outputs(self.root, stage, ['GLB/tokyo_tower.glb', 'GLB/tokyo_tower_new.glb'])
            self.assert_unchanged()
            self.assertFalse((self.root/'GLB/tokyo_tower_new.glb').exists())

    def test_publication_rejects_symlink_parent_outside_repository(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage = Path(temporary)
            (stage/'GLB').mkdir()
            (stage/'GLB/other.glb').write_bytes(b'new file')
            outside = self.root.parent/(self.root.name + '-outside')
            outside.mkdir()
            self.addCleanup(outside.rmdir)
            (self.root/'external').symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'inside the repository'):
                pipeline.promote_outputs(self.root, stage, ['external/other.glb'])
            self.assertFalse((outside/'other.glb').exists())
            self.assert_unchanged()

    def test_dry_run_never_stages_or_writes_outputs(self):
        with patch.object(sys, 'argv', ['cad_pipeline.py', '--regenerate', '--model', 'river', '--dry-run']), \
             patch.object(pipeline, 'regenerate') as generate:
            pipeline.main()
        generate.assert_not_called()
        self.assert_unchanged()


if __name__ == '__main__':
    unittest.main()
