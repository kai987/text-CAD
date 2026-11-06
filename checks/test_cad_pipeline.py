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


class DevelopmentCadPipelineTests(unittest.TestCase):
    setUp = ScopedCadPipelineTests.setUp
    write = ScopedCadPipelineTests.write
    assert_unchanged = ScopedCadPipelineTests.assert_unchanged

    def exercise_development(self, *, validators=None, units=None, preflight=None):
        self.commands, self.selected_tests, self.stages = [], [], []
        def run(commands, *, root):
            self.commands.append(commands); self.stages.append(root)
            self.assert_unchanged()
            self.assertFalse((root/release.RELEASE).exists())
            if validators: validators(root)
        def tests(snapshot, *, root, tests):
            self.selected_tests.extend(tests)
            self.assertFalse((root/release.RELEASE).exists())
            self.assertEqual(snapshot['operation'], 'development_validation_context')
            release.verify_snapshot(root, snapshot)
            if units: units(root)
        with patch.object(pipeline, 'ROOT', self.root), \
             patch.object(pipeline, 'run', side_effect=run), \
             patch.object(pipeline, 'run_unit_tests', side_effect=tests), \
             patch.object(pipeline, 'run_model_preflight', side_effect=preflight):
            return pipeline.validate_development_models(('tokyo-tower',))

    def test_model_subset_omits_unrelated_heavy_native_tests(self):
        validators, tests = pipeline.development_commands(('seto-ohashi',))
        self.assertEqual(validators, ['checks/validate_seto_bridge.py'])
        self.assertIn('checks/test_seto_bridge.py', tests)
        self.assertTrue(set(pipeline.COMMON_DEVELOPMENT_TESTS).issubset(tests))
        self.assertFalse(any('tokyo_tower_r' in path for path in tests))
        self.assertNotIn('checks/validate_towers.py', validators)
        self.assertNotIn('analysis/test_house_review.py', tests)

    def test_development_catalog_covers_all_full_checks_and_deduplicates_shared_checks(self):
        validators, tests = pipeline.development_commands(tuple(pipeline.MODELS))
        self.assertEqual(validators, pipeline.VALIDATORS)
        self.assertEqual(tests, pipeline.UNIT_TESTS)
        validators, tests = pipeline.development_commands(('house', 'apartment', 'tokyo-tower', 'tokyo-skytree'))
        self.assertEqual(len(validators), len(set(validators)))
        self.assertEqual(len(tests), len(set(tests)))
        with patch.object(pipeline, 'VALIDATORS', [*pipeline.VALIDATORS, 'checks/new.py']):
            with self.assertRaisesRegex(ValueError, 'ownership catalog'):
                pipeline.development_commands(('seto-ohashi',))
        with patch.object(pipeline, 'UNIT_TESTS', [*pipeline.UNIT_TESTS, 'checks/test_new.py']):
            with self.assertRaisesRegex(ValueError, 'ownership catalog'):
                pipeline.development_commands(('seto-ohashi',))
        for models in ((), ('unknown',)):
            with self.subTest(models=models), self.assertRaisesRegex(ValueError, 'known'):
                pipeline.development_commands(models)

    def test_success_is_development_only_and_never_rewrites_gate_or_saved_cad(self):
        report = self.exercise_development()
        self.assertTrue(report['development_only'])
        self.assertFalse(report['release_ready'])
        self.assertFalse(report['production_gate_updated'])
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(self.commands, [['checks/validate_towers.py']])
        self.assertIn('checks/test_tokyo_tower_r11.py', self.selected_tests)
        self.assertTrue(all(not path.exists() for path in self.stages))
        self.assert_unchanged()
        # Redirecting this JSON over the release file cannot create a gate.
        with self.assertRaisesRegex(ValueError, 'completed validation provenance'):
            release.verify_snapshot(self.root, report)

    def test_selected_generation_change_can_be_checked_but_remains_unreleased(self):
        self.write('src/lib/tokyo_tower_detail.py', 'tower = 2\n')
        self.exercise_development()
        self.assert_unchanged()
        with self.assertRaisesRegex(ValueError, 'Stale CAD sources'):
            release.verify(self.root)

    def test_unselected_generation_and_artifact_drift_stop_before_running(self):
        for path, text in [('src/lib/skytree_detail.py', 'tree = 2\n'),
                           ('GLB/tokyo_skytree.glb', 'manual overwrite')]:
            original = (self.root/path).read_bytes()
            try:
                self.write(path, text)
                with patch.object(pipeline, 'run') as checks:
                    with self.subTest(path=path), self.assertRaises(ValueError):
                        pipeline.validate_development_models(('tokyo-tower',), root=self.root)
                    checks.assert_not_called()
                self.assertEqual((self.root/release.RELEASE).read_bytes(), self.old_gate)
            finally:
                (self.root/path).write_bytes(original)

    def test_shared_generation_dependency_requires_every_consumer(self):
        self.write('src/lib/tower_geometry.py',
                   'from .tokyo_tower_detail import tower\nfrom .skytree_detail import tree\nshared = 2\n')
        with self.assertRaisesRegex(ValueError, 'tokyo-skytree'):
            pipeline.validate_development_models(('tokyo-tower',), root=self.root)
        self.assert_unchanged()

    def test_verification_only_drift_does_not_bless_the_old_public_gate(self):
        self.write('checks/check.py', '# changed shared validator\n')
        self.write('src/cad_pipeline.py', '# changed pipeline\n')
        self.exercise_development()
        self.assert_unchanged()
        with self.assertRaisesRegex(ValueError, 'Stale CAD sources'):
            release.verify(self.root)

    def test_validator_or_unit_failures_leave_live_preview_and_gate_intact(self):
        def fail(_root):
            raise subprocess.CalledProcessError(1, ['failing development check'])
        for keyword in ('validators', 'units'):
            with self.subTest(keyword=keyword), self.assertRaises(subprocess.CalledProcessError):
                self.exercise_development(**{keyword: fail})
            self.assert_unchanged()
            self.assertTrue(all(not path.exists() for path in self.stages))

    def test_private_checks_cannot_mutate_inputs_or_create_a_release_gate(self):
        def mutate(root, path):
            destination = root/path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text('changed private input')
        paths = ['GLB/tokyo_tower.glb', 'GLB/new.glb', 'src/lib/tower_geometry.py', release.RELEASE]
        for path in paths:
            with self.subTest(path=path), self.assertRaisesRegex(RuntimeError, 'changed during development'):
                self.exercise_development(validators=lambda root: mutate(root, path))
            self.assert_unchanged()
        with self.assertRaisesRegex(RuntimeError, 'changed during development'):
            self.exercise_development(units=lambda root: mutate(root, 'GLB/tokyo_tower.glb'))
        self.assert_unchanged()

    def test_concurrent_live_edit_is_preserved_and_aborts_success(self):
        def edit(_root):
            self.write('src/cad_pipeline.py', '# concurrent editor change\n')
        with self.assertRaisesRegex(RuntimeError, 'changed during development'):
            self.exercise_development(validators=edit)
        self.assertEqual((self.root/'src/cad_pipeline.py').read_text(), '# concurrent editor change\n')
        self.assert_unchanged()

    def test_preflight_failure_stops_before_validators_or_generation(self):
        def fail(*_args, **_kwargs):
            raise ValueError('bad JSON metadata')
        with self.assertRaisesRegex(ValueError, 'bad JSON metadata'):
            self.exercise_development(preflight=fail)
        self.assertEqual(self.commands, [])
        self.assert_unchanged()
        with patch.object(pipeline, 'ROOT', self.root), \
             patch.object(pipeline, 'run_model_preflight', side_effect=fail), \
             patch.object(pipeline, 'run') as generation:
            with self.assertRaisesRegex(ValueError, 'bad JSON metadata'):
                pipeline.regenerate(('tokyo-tower',))
            generation.assert_not_called()
        self.assert_unchanged()

    def test_cli_requires_explicit_development_scope_and_rejects_mixed_operations(self):
        cases = [[], ['--model', 'all'], ['--model', 'river', '--regenerate'],
                 ['--model', 'river', '--validate'], ['--model', 'river', '--refresh-validation'],
                 ['--model', 'river', '--validation-group', 'core'], ['--model', 'river', '--drawings-only']]
        for args in cases:
            with self.subTest(args=args), patch.object(sys, 'argv', ['cad_pipeline.py', '--validate-model', *args]), \
                 patch('sys.stderr', new=io.StringIO()), self.assertRaises(SystemExit) as raised:
                pipeline.main()
            self.assertEqual(raised.exception.code, 2)
        with patch.object(sys, 'argv', ['cad_pipeline.py', '--validate-model', '--model', 'seto-ohashi', '--model', 'river']), \
             patch.object(pipeline, 'validate_development_models') as validate:
            pipeline.main()
        validate.assert_called_once_with(('river', 'seto-ohashi'))

    def test_development_dry_run_prints_exact_selection_and_does_not_stage(self):
        output = io.StringIO()
        with patch.object(sys, 'argv', ['cad_pipeline.py', '--validate-model', '--model', 'seto-ohashi', '--dry-run']), \
             patch('sys.stdout', new=output), patch.object(pipeline, 'staged_tree') as stage, \
             patch.object(pipeline, 'validate_development_models') as validate:
            pipeline.main()
        record = json.loads(output.getvalue())
        self.assertEqual(record['validation_commands'], ['checks/validate_seto_bridge.py'])
        self.assertEqual(record['generation_commands'], [])
        self.assertEqual(record['preflight_models'], ['seto-ohashi'])
        self.assertFalse(record['release_ready'])
        stage.assert_not_called(); validate.assert_not_called()
        self.assert_unchanged()


class SetoMetadataPreflightTests(unittest.TestCase):
    def metadata(self):
        return {'id': 'seto-ohashi', 'model_id': 'seto-ohashi', 'units': 'mm',
                'revision': 'BRIDGE-test', 'component_count': 1,
                'groups': [{'id': 'foundations', 'count': 1}],
                'components': [{'name': 'foundations:base', 'group': 'foundations',
                                'kind': 'box', 'bounds': [0,0,0,100,200,300]}]}

    def test_json_compatible_specification_passes_without_native_geometry(self):
        record = pipeline.preflight_seto_manifest(self.metadata())
        self.assertEqual(record['components'], 1)
        self.assertIn('no CAD kernel', record['check'])

    def test_json_round_trip_and_nonfinite_errors_are_rejected_before_export(self):
        cases = []
        for value in (float('nan'), float('inf'), float('-inf'), Path('not-json'), (1,2)):
            metadata = self.metadata(); metadata['parameters'] = {'value': value}; cases.append(metadata)
        for metadata in cases:
            with self.subTest(value=metadata['parameters']), self.assertRaisesRegex(ValueError, 'JSON'):
                pipeline.preflight_seto_manifest(metadata)

    def test_duplicate_names_groups_and_bad_shape_controls_are_rejected(self):
        cases = []
        metadata = self.metadata(); metadata['components'] *= 2; metadata['component_count'] = 2; cases.append(metadata)
        for field, value in [('name',''), ('group','other'), ('kind','unsupported'),
                             ('bounds',[0,0,0,0,20,30]), ('bounds',[0,0,0,True,20,30]),
                             ('clearance_cuts',[{'bounds':[1,1,1,0,3,4]}]),
                             ('surface_recesses',[{'outline':[[0,0,0]]*3,'extrusion':[0,0,0]}])]:
            metadata = self.metadata(); metadata['components'][0][field] = value; cases.append(metadata)
        metadata = self.metadata(); metadata['groups'][0]['count'] = 2; cases.append(metadata)
        for metadata in cases:
            with self.subTest(metadata=metadata), self.assertRaises(ValueError):
                pipeline.preflight_seto_manifest(metadata)

    def test_actual_seto_preflight_does_not_load_a_native_cad_kernel(self):
        code = pipeline._SETO_PREFLIGHT + '\nassert not any(name in sys.modules for name in ("cadgen", "build123d", "OCP"))\n'
        result = subprocess.run([sys.executable, '-c', code], cwd=ROOT, check=True, capture_output=True, text=True)
        record = json.loads(result.stdout)
        self.assertEqual(record['model_id'], 'seto-ohashi')
        self.assertGreater(record['components'], 1)


if __name__ == '__main__':
    unittest.main()
