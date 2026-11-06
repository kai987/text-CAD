"""Adversarial tests for publication freshness; no CAD runtime required."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('cad_release', Path(__file__).resolve().parents[1]/'src/cad_release.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
pipeline_spec = importlib.util.spec_from_file_location('cad_pipeline', Path(__file__).resolve().parents[1]/'src/cad_pipeline.py')
pipeline = importlib.util.module_from_spec(pipeline_spec)
with patch.dict(sys.modules, {'cad_release': module}):
    pipeline_spec.loader.exec_module(pipeline)


class CadReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ['src/model.py', 'checks/check.py', 'requirements.txt', 'web/scripts/generate-plan-svg.py', 'GLB/house.glb']:
            path = self.root/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'original')
        (self.root/'output/review').mkdir(parents=True)
        self.release = {'schema_version': 1, 'drawing_revision': 'R13', 'scope': 'Concept only',
                        'validation_commands': ['check.py'],
                        'sources': {name: module.digest(self.root/name) for name in module.source_paths(self.root)},
                        'artifacts': {'GLB/house.glb': module.digest(self.root/'GLB/house.glb')}}
        self.save()

    def save(self):
        (self.root/module.RELEASE).write_text(json.dumps(self.release))

    def test_verified_snapshot_and_ephemeral_reports(self):
        self.assertEqual(module.verify(self.root)['artifacts'], 1)
        for name in ['validation_3d.json', 'apartment_2ldk_validation.json', 'outdoor_lighting_validation_R08.json']:
            report = self.root/'output/review'/name
            report.write_text('new timestamp or runner path')
            self.assertNotIn(str(report.relative_to(self.root)), module.artifact_paths(self.root))
        module.verify(self.root)

    def test_parameter_change_or_new_source_is_blocked(self):
        (self.root/'src/model.py').write_text('changed parameters')
        with self.assertRaisesRegex(ValueError, 'Stale CAD sources'):
            module.verify(self.root)
        (self.root/'src/model.py').write_bytes(b'original')
        (self.root/'src/new.py').write_text('new generator')
        with self.assertRaisesRegex(ValueError, 'source set changed'):
            module.verify(self.root)

    def test_analysis_algorithm_and_source_set_changes_are_blocked(self):
        # Python glob treats a missing analysis directory as an empty source set.
        module.verify(self.root)
        path = self.root/'analysis/house_review.py'
        path.parent.mkdir()
        path.write_bytes(b'original analysis')
        with self.assertRaisesRegex(ValueError, 'source set changed'):
            module.verify(self.root)
        self.release['sources']['analysis/house_review.py'] = module.digest(path)
        self.save()
        module.verify(self.root)
        path.write_bytes(b'changed area or load calculation')
        with self.assertRaisesRegex(ValueError, 'Stale CAD sources: analysis/house_review.py'):
            module.verify(self.root)
        path.write_bytes(b'original analysis')
        nested = self.root/'analysis/rules/areas.py'
        nested.parent.mkdir()
        nested.write_bytes(b'new analysis rule')
        self.assertIn('analysis/rules/areas.py', module.source_paths(self.root))
        with self.assertRaisesRegex(ValueError, 'source set changed'):
            module.verify(self.root)
        nested.unlink()
        path.unlink()
        with self.assertRaisesRegex(ValueError, 'source set changed'):
            module.verify(self.root)

    def test_modified_missing_or_unsafe_artifact_is_blocked(self):
        (self.root/'GLB/house.glb').write_bytes(b'outdated export')
        with self.assertRaisesRegex(ValueError, 'Stale CAD artifacts'):
            module.verify(self.root)
        (self.root/'GLB/house.glb').unlink()
        with self.assertRaisesRegex(ValueError, 'Stale CAD artifacts'):
            module.verify(self.root)
        self.release['artifacts'] = {'../secret': 'unknown'}
        self.save()
        with self.assertRaisesRegex(ValueError, 'Stale CAD artifacts'):
            module.verify(self.root)

    def test_unregistered_artifact_is_blocked_in_each_catalog_directory(self):
        for name in ['DXF/new.dxf', 'STEP/new.step', 'GLB/new.glb',
                     'output/pdf/new.pdf', 'output/vector/new.svg',
                     'output/review/new.json', 'output/review/cases/new.json',
                     'web/src/plan-preview-metadata.json']:
            with self.subTest(name=name):
                path = self.root/name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'unregistered export')
                with self.assertRaisesRegex(ValueError, 'artifact set changed'):
                    module.verify(self.root)
                path.unlink()
        module.verify(self.root)

    def test_candidate_check_does_not_replace_the_published_gate(self):
        candidate = json.loads(json.dumps(self.release))
        candidate['drawing_revision'] = 'candidate'
        self.assertEqual(module.verify_snapshot(self.root, candidate)['revision'], 'candidate')
        self.assertEqual(module.verify(self.root)['revision'], 'R13')
        (self.root/'GLB/new.glb').write_bytes(b'unregistered export')
        with self.assertRaisesRegex(ValueError, 'artifact set changed'):
            module.verify_snapshot(self.root, candidate)


class CadPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.gate = self.root/module.RELEASE
        self.gate.parent.mkdir(parents=True)
        self.gate.write_text('previous gate')
        (self.gate.parent/'design_manifest.json').write_text(json.dumps({'drawing_revision': 'R22'}))
        (self.gate.parent/'house_3d_assumptions_R01.json').write_text(json.dumps({'revision': 'R22'}))
        self.font = self.root/'test-font.ttf'
        self.font.write_bytes(b'test font')

    def run_main(self, mode, unit_action):
        with patch.object(pipeline, 'ROOT', self.root), \
             patch.object(pipeline, 'run') as saved_checks, \
             patch.object(pipeline, 'verify', return_value={'revision': 'R22'}) as gate_check, \
             patch.object(pipeline, 'run_unit_tests', side_effect=unit_action), \
             patch.object(pipeline.importlib.metadata, 'version', return_value='test'), \
             patch.dict(pipeline.os.environ, {'TEXT_CAD_CJK_FONT': str(self.font)}), \
             patch.object(sys, 'argv', ['cad_pipeline.py', mode]):
            pipeline.main()
            return saved_checks, gate_check

    def test_cli_dispatches_selected_models_to_staged_regeneration(self):
        with patch.object(pipeline, 'regenerate') as regenerate, \
             patch.object(sys, 'argv', ['cad_pipeline.py', '--regenerate', '--model', 'tokyo-tower']):
            pipeline.main()
        regenerate.assert_called_once_with(('tokyo-tower',), refresh=False, drawings_only=False)

    def test_validate_runs_tests_and_never_rewrites_gate(self):
        original = self.gate.read_bytes()
        saved_checks, gate_check = self.run_main('--validate', lambda: None)
        gate_check.assert_called_once_with()
        saved_checks.assert_called_once_with(pipeline.VALIDATORS)
        self.assertEqual(self.gate.read_bytes(), original)

    def test_failed_validation_test_never_rewrites_gate(self):
        original = self.gate.read_bytes()
        with self.assertRaises(subprocess.CalledProcessError):
            self.run_main('--validate', subprocess.CalledProcessError(1, ['unit tests']))
        self.assertEqual(self.gate.read_bytes(), original)

    def test_stale_inputs_stop_validation_before_checks_and_tests(self):
        with patch.object(pipeline, 'verify', side_effect=ValueError('Stale CAD sources')), \
             patch.object(pipeline, 'run') as saved_checks, \
             patch.object(pipeline, 'run_unit_tests') as unit_tests, \
             patch.object(sys, 'argv', ['cad_pipeline.py', '--validate']):
            with self.assertRaisesRegex(ValueError, 'Stale CAD sources'):
                pipeline.main()
        saved_checks.assert_not_called()
        unit_tests.assert_not_called()

    def test_validate_and_candidate_use_one_unit_catalog(self):
        self.assertIn('checks/test_upper_layout.py', pipeline.UNIT_TESTS)
        self.assertIn('analysis/test_house_review.py', pipeline.UNIT_TESTS)
        self.assertEqual(len(pipeline.UNIT_TESTS), len(set(pipeline.UNIT_TESTS)))
        groups = [[p for p in pipeline.UNIT_TESTS if not p.startswith('analysis/')],
                  [p for p in pipeline.UNIT_TESTS if p.startswith('analysis/')]]
        with patch.object(pipeline.subprocess, 'run') as command, \
             patch.object(pipeline, 'verify_snapshot') as guard:
            pipeline.run_unit_tests()
            self.assertEqual([call.args[0] for call in command.call_args_list],
                             [[sys.executable, '-m', 'unittest', *group, '-v'] for group in groups])
            command.reset_mock()
            pipeline.run_unit_tests({'candidate': 'snapshot'})
            self.assertEqual([call.args[0][3:] for call in command.call_args_list],
                             [[path.removesuffix('.py').replace('/', '.') for path in group] for group in groups])
            for call in command.call_args_list:
                self.assertEqual(json.loads(call.kwargs['input']), {'candidate': 'snapshot'})
            self.assertEqual(guard.call_count, 4)

    def test_ci_groups_exactly_partition_all_validators_and_unit_modules(self):
        validators, tests = [], []
        for name in pipeline.VALIDATION_GROUPS:
            group_validators, group_tests = pipeline.validation_group(name)
            validators.extend(group_validators)
            tests.extend(group_tests)
        self.assertCountEqual(validators, pipeline.VALIDATORS)
        self.assertCountEqual(tests, pipeline.UNIT_TESTS)
        self.assertEqual(len(validators), len(set(validators)))
        self.assertEqual(len(tests), len(set(tests)))
        with self.assertRaisesRegex(ValueError, 'Unknown CAD validation group'):
            pipeline.validation_group('unknown')

    def test_grouped_cli_is_read_only_and_dispatches_only_with_validate(self):
        with patch.object(pipeline, 'run_validation_group') as grouped, \
             patch.object(sys, 'argv', ['cad_pipeline.py', '--validate', '--validation-group', 'tokyo-r11']):
            pipeline.main()
        grouped.assert_called_once_with('tokyo-r11')
        for mode in ('--regenerate', '--refresh-validation'):
            with patch.object(sys, 'argv', ['cad_pipeline.py', mode, '--validation-group', 'core']), \
                 patch('sys.stderr'):
                with self.assertRaises(SystemExit):
                    pipeline.main()

    def test_grouped_units_verify_inputs_before_and_after_without_rewriting_gate(self):
        gate = json.dumps({'candidate': 'snapshot'}).encode()
        self.gate.write_bytes(gate)
        with patch.object(pipeline, 'verify_snapshot', return_value={'revision': 'R22'}) as guard, \
             patch.object(pipeline, 'run_unit_tests') as units, \
             patch.object(pipeline, 'run') as validators:
            pipeline.run_validation_group('tokyo-r11', root=self.root)
        units.assert_called_once_with(root=self.root, tests=['checks/test_tokyo_tower_r11.py'])
        validators.assert_not_called()
        self.assertEqual(guard.call_count, 2)
        self.assertEqual(self.gate.read_bytes(), gate)

    def test_grouped_failure_still_checks_the_same_snapshot_and_gate(self):
        gate = json.dumps({'candidate': 'snapshot'}).encode()
        self.gate.write_bytes(gate)
        with patch.object(pipeline, 'verify_snapshot', return_value={'revision': 'R22'}) as guard, \
             patch.object(pipeline, 'run', side_effect=subprocess.CalledProcessError(1, ['validator'])):
            with self.assertRaises(subprocess.CalledProcessError):
                pipeline.run_validation_group('artifacts', root=self.root)
        self.assertEqual(guard.call_count, 2)
        self.assertEqual(self.gate.read_bytes(), gate)
        with patch.object(pipeline, 'verify_snapshot', return_value={'revision': 'R22'}), \
             patch.object(pipeline, 'run', side_effect=lambda *_args, **_kwargs: self.gate.write_bytes(b'changed gate')):
            with self.assertRaisesRegex(RuntimeError, 'release changed'):
                pipeline.run_validation_group('artifacts', root=self.root)


if __name__ == '__main__':
    unittest.main()
