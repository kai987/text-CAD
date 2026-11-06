"""Scoped dependency, isolated generation and rollback publication regressions.

No CAD runtime is required: small named files exercise the same staging and
publication paths as the expensive generators.
"""
from contextlib import ExitStack
from copy import deepcopy
import io
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

    def prepare_native_baseline(self):
        """Completed release fixture with independently bound native inputs."""
        self.native_contracts = {}
        for model, stem, detail in (
            ('tokyo-tower', 'tokyo_tower', 'src/lib/tokyo_tower_detail.py'),
            ('tokyo-skytree', 'tokyo_skytree', 'src/lib/skytree_detail.py'),
        ):
            step, glb = f'STEP/{stem}.step', f'GLB/{stem}.glb'
            contract = {'manifest': f'output/review/{stem}_manifest.json',
                        'artifacts': [step, step + '.json', glb],
                        'model_artifacts': [step, glb],
                        'sources': ['src/lib/tower_geometry.py', detail, 'src/towers_3d.py']}
            self.native_contracts[model] = contract
            self.write(step, 'original STEP for ' + model)
            self.write(step + '.json', json.dumps({'occurrences': [model]}))
            manifest = {'id': model,
                        'source_sha256': pipeline._hashes(self.root, contract['sources']),
                        'artifacts': {path: {'bytes': (self.root/path).stat().st_size,
                                             'sha256': release.digest(self.root/path)}
                                      for path in contract['model_artifacts']}}
            self.write(contract['manifest'], json.dumps(manifest))
        self.baseline['unit_test_commands'] = ['checks/check.py']
        self.baseline['artifacts'] = pipeline._hashes(self.root, release.artifact_paths(self.root))
        self.write(release.RELEASE, json.dumps(self.baseline))
        self.old_gate = (self.root/release.RELEASE).read_bytes()

    def native_snapshot(self, previous=None, models=('tokyo-tower',)):
        with patch.object(pipeline, 'native_model_contract', side_effect=self.native_contracts.__getitem__):
            return pipeline.verify_reusable_native_inputs(self.root, self.baseline if previous is None else previous, models)

    def exercise(self, action=None, tests=None, *, refresh=False, drawings_only=False, models=None):
        def generate(commands, *, root):
            if commands != pipeline.VALIDATORS and commands:
                if drawings_only:
                    path = root/'DXF/tokyo_tower_plan.dxf'
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(b'new drawing')
                else:
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
            if drawings_only:
                stack.enter_context(patch.object(pipeline, 'native_model_contract', side_effect=self.native_contracts.__getitem__))
            selected = models if models is not None else tuple(pipeline.MODELS) if refresh else ('tokyo-tower',)
            pipeline.regenerate(selected, refresh=refresh, drawings_only=drawings_only)

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
        self.assertEqual(pipeline.generation_commands(('seto-ohashi',)),
                         ['src/seto_bridge_3d.py', 'src/generate_seto_bridge_plans.py'])
        self.assertEqual(pipeline.artifact_model('GLB/seto_ohashi.glb'), 'seto-ohashi')
        house = pipeline.generation_commands(('house',))
        self.assertEqual(len(house), 8)
        self.assertEqual(house[-1], 'web/scripts/generate-plan-svg.py')

    def test_own_tower_source_can_change_but_shared_catalog_requires_both(self):
        self.write('src/lib/tokyo_tower_detail.py', 'tower = 2\n')
        pipeline.check_scope(self.root, self.baseline, ('tokyo-tower',))
        self.write('src/lib/tower_geometry.py', 'from .tokyo_tower_detail import tower\nfrom .skytree_detail import tree\ncatalog = "changed for both towers"\n')
        with self.assertRaisesRegex(ValueError, 'tokyo-skytree'):
            pipeline.check_scope(self.root, self.baseline, ('tokyo-tower',))

    def test_model_parameter_defaults_have_independent_pipeline_dependencies(self):
        self.write('src/lib/tower_geometry.py',
                   'from .tokyo_tower_parameters import tower\n'
                   'from .skytree_parameters import tree\n'
                   'from .tower_parameters import validate\n')
        self.write('src/lib/tokyo_tower_parameters.py', 'tower = 1\n')
        self.write('src/lib/skytree_parameters.py', 'tree = 1\n')
        self.write('src/lib/tower_parameters.py', 'validate = True\n')
        self.baseline['sources'] = pipeline._hashes(self.root, release.source_paths(self.root))
        self.write('src/lib/tokyo_tower_parameters.py', 'tower = 2\n')
        pipeline.check_scope(self.root, self.baseline, ('tokyo-tower',))
        with self.assertRaisesRegex(ValueError, 'tokyo-tower'):
            pipeline.check_scope(self.root, self.baseline, ('tokyo-skytree',))
        self.write('src/lib/tokyo_tower_parameters.py', 'tower = 1\n')
        self.write('src/lib/skytree_parameters.py', 'tree = 2\n')
        pipeline.check_scope(self.root, self.baseline, ('tokyo-skytree',))
        self.write('src/lib/tower_parameters.py', 'validate = False\n')
        with self.assertRaisesRegex(ValueError, 'tokyo-tower'):
            pipeline.check_scope(self.root, self.baseline, ('tokyo-skytree',))

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

    def test_drawings_only_selects_only_landmark_drawing_generators(self):
        self.assertEqual(pipeline.generation_commands(('tokyo-tower',), drawings_only=True),
                         ['src/generate_tower_plans.py --model tokyo-tower'])
        self.assertEqual(pipeline.generation_commands(('tokyo-skytree',), drawings_only=True),
                         ['src/generate_tower_plans.py --model tokyo-skytree'])
        self.assertEqual(pipeline.generation_commands(('tokyo-tower', 'tokyo-skytree'), drawings_only=True),
                         ['src/generate_tower_plans.py'])
        self.assertEqual(pipeline.generation_commands(tuple(pipeline.MODELS), drawings_only=False), pipeline.GENERATORS)
        for models in ((), ('river',), tuple(pipeline.MODELS), ('tokyo-tower', 'house')):
            with self.subTest(models=models), self.assertRaisesRegex(ValueError, 'nonempty selection'):
                pipeline.generation_commands(models, drawings_only=True)

    def test_drawings_only_preserves_native_bytes_and_runs_all_candidate_checks(self):
        self.prepare_native_baseline()
        original = self.native_snapshot()
        commands_run, candidates = [], []
        def inspect(snapshot, *, root):
            self.assert_unchanged()
            self.assertFalse((root/release.RELEASE).exists())
            self.assertEqual(snapshot['reused_native_artifacts'], original['artifacts'])
            pipeline.guard_reused_native_inputs(root, original)
            release.verify_snapshot(root, snapshot)
            candidates.append(snapshot)
        self.exercise(action=lambda commands, root: commands_run.append(commands), tests=inspect, drawings_only=True)
        self.assertEqual(commands_run, [['src/generate_tower_plans.py --model tokyo-tower'], pipeline.VALIDATORS])
        self.assertEqual(len(candidates), 1)
        candidate = json.loads((self.root/release.RELEASE).read_text())
        self.assertEqual(candidate['operation'], 'staged_drawings_regeneration')
        self.assertIs(candidate['drawings_only'], True)
        self.assertEqual(candidate['reused_native_sources'], original['sources'])
        self.assertEqual(candidate['reused_native_artifacts'], original['artifacts'])
        self.assertEqual((self.root/'DXF/tokyo_tower_plan.dxf').read_bytes(), b'new drawing')
        for path, expected in original['artifacts'].items():
            self.assertEqual(release.digest(self.root/path), expected, path)
        release.verify(self.root)

    def test_drawings_only_can_reuse_both_native_models_for_a_shared_drawing_fix(self):
        self.prepare_native_baseline()
        self.write('src/generate_tower_plans.py', '# shared drawing fix\nfrom lib.tower_geometry import catalog\n')
        models = ('tokyo-tower', 'tokyo-skytree')
        snapshot = self.native_snapshot(models=models)
        self.assertEqual(len(snapshot['artifacts']), 8)
        self.exercise(drawings_only=True, models=models)
        candidate = json.loads((self.root/release.RELEASE).read_text())
        self.assertEqual(candidate['generation_commands'], ['src/generate_tower_plans.py'])
        self.assertEqual(candidate['reused_native_artifacts'], snapshot['artifacts'])

    def test_drawings_only_rejects_geometry_and_native_exporter_source_drift(self):
        self.prepare_native_baseline()
        for name in self.native_contracts['tokyo-tower']['sources']:
            original = (self.root/name).read_bytes()
            try:
                (self.root/name).write_bytes(original + b'\n# modified native source\n')
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Native source differs'):
                    self.native_snapshot()
            finally:
                (self.root/name).write_bytes(original)
        self.assert_unchanged()

    def test_drawings_only_rejects_native_step_glb_sidecar_and_manifest_drift(self):
        self.prepare_native_baseline()
        snapshot = self.native_snapshot()
        for name in snapshot['artifacts']:
            original = (self.root/name).read_bytes()
            try:
                (self.root/name).write_bytes(original + b'\nchanged\n')
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Native artifact differs'):
                    self.native_snapshot()
            finally:
                (self.root/name).write_bytes(original)
        self.assert_unchanged()

    def test_drawings_only_rejects_missing_sidecars_and_incomplete_previous_release(self):
        self.prepare_native_baseline()
        previous = deepcopy(self.baseline)
        previous.pop('unit_test_commands')
        with self.assertRaisesRegex(ValueError, 'completed previous CAD release'):
            self.native_snapshot(previous)
        (self.root/'STEP/tokyo_tower.step.json').unlink()
        with self.assertRaisesRegex(ValueError, 'Cannot reuse native inputs'):
            self.native_snapshot()

    def test_drawings_only_requires_exact_cached_source_and_artifact_bindings(self):
        self.prepare_native_baseline()
        path = self.native_contracts['tokyo-tower']['manifest']
        original = json.loads((self.root/path).read_text())
        cases = []
        for mutation in ('extra_source', 'missing_source', 'wrong_source_hash', 'extra_artifact',
                         'missing_artifact', 'wrong_artifact_hash', 'wrong_artifact_bytes', 'wrong_id'):
            manifest = deepcopy(original)
            if mutation == 'extra_source': manifest['source_sha256']['src/extra.py'] = '0'*64
            elif mutation == 'missing_source': manifest['source_sha256'].pop('src/towers_3d.py')
            elif mutation == 'wrong_source_hash': manifest['source_sha256']['src/towers_3d.py'] = '0'*64
            elif mutation == 'extra_artifact': manifest['artifacts']['STEP/other.step'] = {}
            elif mutation == 'missing_artifact': manifest['artifacts'].pop('GLB/tokyo_tower.glb')
            elif mutation == 'wrong_artifact_hash': manifest['artifacts']['GLB/tokyo_tower.glb']['sha256'] = '0'*64
            elif mutation == 'wrong_artifact_bytes': manifest['artifacts']['GLB/tokyo_tower.glb']['bytes'] += 1
            elif mutation == 'wrong_id': manifest['id'] = 'tokyo-skytree'
            cases.append((mutation, manifest))
        for mutation, manifest in cases:
            # A trusted release hash alone must not bypass inconsistent cached
            # model bindings. Construct that prior-release fixture explicitly.
            self.write(path, json.dumps(manifest))
            previous = deepcopy(self.baseline)
            previous['artifacts'][path] = release.digest(self.root/path)
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'Native model'):
                self.native_snapshot(previous)

    def test_drawings_only_stage_guard_rejects_all_reused_input_mutations(self):
        self.prepare_native_baseline()
        snapshot = self.native_snapshot()
        with pipeline.staged_tree(self.root) as stage:
            pipeline.guard_reused_native_inputs(stage, snapshot)
            for name in [*snapshot['artifacts'], *snapshot['sources']]:
                original = (stage/name).read_bytes()
                try:
                    (stage/name).write_bytes(original + b'\nstaged mutation\n')
                    with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'changed during staging'):
                        pipeline.guard_reused_native_inputs(stage, snapshot)
                finally:
                    (stage/name).write_bytes(original)
        self.assert_unchanged()

    def test_drawings_only_generator_cannot_modify_reused_native_artifacts(self):
        self.prepare_native_baseline()
        def mutate(commands, root):
            if commands != pipeline.VALIDATORS:
                (root/'STEP/tokyo_tower.step.json').write_bytes(b'new sidecar')
        with self.assertRaisesRegex(ValueError, 'changed during staging'):
            self.exercise(action=mutate, drawings_only=True)
        self.assert_unchanged()
        self.assertFalse((self.root/'DXF/tokyo_tower_plan.dxf').exists())

    def test_drawings_only_validator_and_shared_unit_cannot_mutate_reused_native(self):
        self.prepare_native_baseline()
        def mutate_validator(commands, root):
            if commands == pipeline.VALIDATORS:
                (root/'GLB/tokyo_tower.glb').write_bytes(b'changed after drawing generation')
        with self.assertRaisesRegex(ValueError, 'changed during staging'):
            self.exercise(action=mutate_validator, drawings_only=True)
        self.assert_unchanged()
        def mutate_unit(_snapshot, *, root):
            (root/'output/review/tokyo_tower_manifest.json').write_bytes(b'changed by test')
        with self.assertRaisesRegex(ValueError, 'changed during staging'):
            self.exercise(tests=mutate_unit, drawings_only=True)
        self.assert_unchanged()

    def test_drawings_only_cannot_add_an_unbound_native_output(self):
        self.prepare_native_baseline()
        def add_native(commands, root):
            if commands != pipeline.VALIDATORS:
                (root/'STEP/tokyo_tower_extra.step').write_bytes(b'unexpected native output')
        with self.assertRaisesRegex(ValueError, 'changed a native output'):
            self.exercise(action=add_native, drawings_only=True)
        self.assert_unchanged()
        self.assertFalse((self.root/'STEP/tokyo_tower_extra.step').exists())

    def test_drawings_only_cli_rejects_other_operations_and_nonlandmark_selections(self):
        for args in (['--validate', '--drawings-only'], ['--refresh-validation', '--drawings-only'],
                     ['--regenerate', '--drawings-only'], ['--regenerate', '--drawings-only', '--model', 'all'],
                     ['--regenerate', '--drawings-only', '--model', 'river']):
            with self.subTest(args=args), patch.object(sys, 'argv', ['cad_pipeline.py', *args]), \
                 patch('sys.stderr', new=io.StringIO()), self.assertRaises(SystemExit) as raised:
                pipeline.main()
            self.assertEqual(raised.exception.code, 2)

    def test_drawings_only_dry_run_skips_reuse_and_generation(self):
        output = io.StringIO()
        with patch.object(sys, 'argv', ['cad_pipeline.py', '--regenerate', '--drawings-only',
                                        '--model', 'tokyo-tower', '--dry-run']), \
             patch.object(pipeline, 'regenerate') as generate, patch('sys.stdout', new=output):
            pipeline.main()
        generate.assert_not_called()
        record = json.loads(output.getvalue())
        self.assertEqual(record['generation_commands'], ['src/generate_tower_plans.py --model tokyo-tower'])
        self.assert_unchanged()


if __name__ == '__main__':
    unittest.main()
