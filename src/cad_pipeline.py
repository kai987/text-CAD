"""Generate and validate the current CAD catalog before publishing (concept geometry only)."""
from __future__ import annotations
import argparse
import ast
from contextlib import contextmanager
from datetime import datetime
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys
import tempfile
from zoneinfo import ZoneInfo
from cad_release import ROOT, RELEASE, artifact_paths, digest, source_paths, verify

GENERATORS = ['src/generate_redesign_plans.py', 'src/generate_attic_plan.py',
              'src/generate_structure_plan.py', 'src/generate_site_plan.py',
              'src/house_3d.py', 'src/generate_structural_variants.py',
              'src/generate_structural_cases.py', 'src/apartment_2ldk.py',
              'src/river_3d.py', 'src/generate_river_plans.py',
              'src/towers_3d.py', 'src/generate_tower_plans.py',
              'web/scripts/generate-plan-svg.py']
VALIDATORS = ['checks/validate_redesign_plans.py', 'checks/validate_jp_drafting.py',
              'checks/validate_3d.py', 'checks/validate_site.py', 'checks/validate_structure.py',
              'checks/validate_structural_variants.py', 'checks/validate_structural_cases.py',
              'checks/validate_apartment.py', 'checks/validate_fixtures.py',
              'checks/validate_furniture.py', 'checks/validate_outdoor_lighting.py',
              'checks/validate_glb_native.py', 'checks/validate_indoor_lighting.py',
              'checks/validate_river.py', 'checks/validate_towers.py']
UNIT_TESTS = ['checks/test_cad_release.py', 'checks/test_cad_pipeline.py', 'checks/test_orientation.py',
              'checks/test_step_transport.py', 'checks/test_attic_opening_rules.py',
              'checks/test_glb_export.py',
              'checks/test_attic_layout.py', 'checks/test_upper_layout.py',
              'checks/test_river_geometry.py',
              'checks/test_river_validation.py', 'checks/test_tower_drawings.py',
              'checks/test_tokyo_tower_detail.py', 'checks/test_tokyo_tower_steel.py', 'checks/test_tokyo_tower_base.py', 'checks/test_tokyo_tower_outline.py', 'checks/test_skytree_detail.py', 'checks/test_skytree_outline.py', 'checks/test_tower_tubular.py',
              'analysis/test_house_review.py']

# The analysis tests call the freshness gate. Verify their inputs against the
# unpublished candidate in an isolated process, without creating a usable gate
# before every test has passed. The public --validate path always uses verify().
_CANDIDATE_TEST_RUNNER = '''
import json
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, 'src')
from cad_release import verify_snapshot
snapshot = json.load(sys.stdin)
with patch('analysis.house_review.verify', lambda root: verify_snapshot(root, snapshot)):
    suite = unittest.defaultTestLoader.loadTestsFromNames(sys.argv[1:])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
'''


MODELS = ('house', 'apartment', 'river', 'tokyo-tower', 'tokyo-skytree')
_OUTPUT_ROOTS = ('DXF', 'STEP', 'GLB', 'output/pdf', 'output/svg',
                 'output/vector', 'output/review')
_VALIDATION_ONLY = {'src/cad_pipeline.py', 'src/cad_release.py'}


def generation_commands(models: tuple[str, ...]) -> list[str]:
    """Select complete model outputs; shared validators always run afterward."""
    selected = set(models)
    commands = []
    for path in GENERATORS:
        if path in GENERATORS[:7] or path == 'web/scripts/generate-plan-svg.py':
            if 'house' in selected:
                commands.append(path)
        elif path == 'src/apartment_2ldk.py':
            if 'apartment' in selected:
                commands.append(path)
        elif path in ('src/river_3d.py', 'src/generate_river_plans.py'):
            if 'river' in selected:
                commands.append(path)
        else:
            towers = [model for model in MODELS[-2:] if model in selected]
            if len(towers) == 2:
                commands.append(path)
            elif towers:
                flag = '--tower' if path == 'src/towers_3d.py' else '--model'
                commands.append(f'{path} {flag} {towers[0]}')
    return commands


def artifact_model(path: str) -> str:
    """Catalog ownership, including retained historical house supplements."""
    name = Path(path).name
    for prefix, model in [('apartment_2ldk', 'apartment'), ('river_demo', 'river'),
                          ('tokyo_tower', 'tokyo-tower'), ('tokyo_skytree', 'tokyo-skytree')]:
        if name.startswith(prefix):
            return model
    return 'house'


def _verification_source(path: str) -> bool:
    return path in _VALIDATION_ONLY or path.startswith('checks/')


def dependency_sources(root: Path, model: str) -> set[str]:
    """Conservative local-import closure, including imports inside functions.

    The two landmark generators intentionally import both catalogs, but their
    selectors execute one catalog. Their explicit per-tower source lists in
    tower_geometry remain authoritative for that conditional branch.
    """
    all_sources = set(source_paths(root))
    pending = [shlex.split(command)[0] for command in generation_commands((model,))]
    excluded = ({'src/lib/skytree_detail.py', 'src/lib/skytree_outline.py'} if model == 'tokyo-tower'
                else {'src/lib/tokyo_tower_detail.py', 'src/lib/tokyo_tower_steel.py'} if model == 'tokyo-skytree'
                else set())
    result = set()
    while pending:
        path = pending.pop()
        if path in result or path in excluded or path not in all_sources:
            continue
        result.add(path)
        module_parts = Path(path).relative_to('src').with_suffix('').parts if path.startswith('src/') else ()
        for node in ast.walk(ast.parse((root/path).read_text(), filename=path)):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = list(module_parts[:-node.level]) if node.level else []
                if node.module:
                    base += node.module.split('.')
                names = ['.'.join(base), *['.'.join([*base, alias.name]) for alias in node.names]]
            for name in names:
                candidate = 'src/' + name.replace('.', '/') + '.py'
                if candidate in all_sources:
                    pending.append(candidate)
    return result


def _hashes(root: Path, paths: list[str]) -> dict[str, str]:
    for relative in paths:
        path = root/relative
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f'CAD input must be a regular file inside the repository: {relative}')
    return {path: digest(root/path) for path in paths}


def check_scope(root: Path, previous: dict, models: tuple[str, ...], *, refresh: bool = False) -> None:
    """Never rebind a source change whose generated consumers were not selected."""
    if previous.get('schema_version') != 1 or not previous.get('validation_commands'):
        raise ValueError('A completed previous CAD release is required for a scoped operation.')
    sources = _hashes(root, source_paths(root))
    changed = {path for path in sources.keys() | previous['sources'].keys()
               if sources.get(path) != previous['sources'].get(path)}
    for path in sorted(changed):
        if _verification_source(path):
            continue
        if refresh:
            raise ValueError(f'Cannot refresh changed generation or analysis source: {path}; regenerate its models.')
        consumers = {model for model in MODELS if path in dependency_sources(root, model)}
        if not consumers or not consumers.issubset(models):
            detail = ', '.join(sorted(consumers - set(models))) or 'unknown dependency'
            raise ValueError(f'Source {path} also requires regeneration of {detail}; select the affected models or --model all.')
    current = set(artifact_paths(root))
    for path in sorted(current | previous['artifacts'].keys()):
        if not refresh and artifact_model(path) in models:
            continue
        if path not in current or previous['artifacts'].get(path) != digest(root/path):
            raise ValueError(f'Unselected CAD artifact changed: {path}; restore it or regenerate its model.')


def _output_paths(root: Path) -> list[str]:
    result = []
    for directory in _OUTPUT_ROOTS:
        for path in (root/directory).glob('**/*'):
            if path.is_file() and 'validation' not in path.stem and path.name != Path(RELEASE).name:
                if path.is_symlink():
                    raise ValueError(f'CAD output must not be a symlink: {path}')
                result.append(path.relative_to(root).as_posix())
    if (root/'web/src/plan-preview-metadata.json').is_file():
        result.append('web/src/plan-preview-metadata.json')
    return sorted(result)


@contextmanager
def staged_tree(root: Path):
    """Copy inputs, never hard-link writable CAD files into the live preview."""
    with tempfile.TemporaryDirectory(prefix='text-cad-stage-') as temporary:
        stage = Path(temporary)
        for name in ('src', 'checks', 'analysis', 'references', 'rust', 'docs',
                     'DXF', 'STEP', 'GLB', 'output', 'web/scripts', 'web/src'):
            source = root/name
            if source.is_dir():
                shutil.copytree(source, stage/name,
                                ignore=shutil.ignore_patterns('__pycache__', 'target', '*.pyc'))
        for name in ('requirements.txt', 'README.md', 'README.ja.md', 'README.en.md'):
            if (root/name).is_file():
                shutil.copy2(root/name, stage/name)
        yield stage


def _replace_bytes(path: Path, source: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=f'.{path.name}.cad-', dir=path.parent, delete=False) as pending:
        temporary = Path(pending.name)
    try:
        shutil.copy2(source, temporary)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def promote_outputs(root: Path, stage: Path, paths: list[str]) -> None:
    """Publish the gate last; rollback all replaced files on a caught failure.

    Multi-file replacement cannot be one filesystem rename. While promotion is
    in progress no valid gate exists, so concurrent builds fail closed.
    """
    destinations = [*paths, RELEASE]
    with tempfile.TemporaryDirectory(prefix='text-cad-rollback-', dir=root.parent) as temporary:
        backup = Path(temporary)
        existed = set()
        for relative in destinations:
            target = root/relative
            if target.is_symlink() or not target.resolve().is_relative_to(root.resolve()):
                raise ValueError(f'CAD destination must be inside the repository and not a symlink: {relative}')
            if target.is_file():
                existed.add(relative)
                (backup/relative).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup/relative)
        (root/RELEASE).unlink(missing_ok=True)
        replaced = []
        try:
            for relative in destinations:
                replaced.append(relative)
                _replace_bytes(root/relative, stage/relative)
        except BaseException:
            # Restore the previous gate only after its full artifact set.
            for relative in [*reversed([p for p in replaced if p != RELEASE]), RELEASE]:
                if relative in existed:
                    _replace_bytes(root/relative, backup/relative)
                else:
                    (root/relative).unlink(missing_ok=True)
            raise


def run(paths: list[str], *, root: Path | None = None) -> None:
    root = ROOT if root is None else root
    for path in paths:
        print(f'CAD pipeline: {path}', flush=True)
        subprocess.run([sys.executable, *shlex.split(path)], cwd=root, check=True,
                       env={**os.environ, 'CADGEN_DAEMON': '0'})


def run_unit_tests(snapshot: dict | None = None, *, root: Path | None = None) -> None:
    root = ROOT if root is None else root
    print('CAD pipeline: Python unit tests', flush=True)
    if snapshot is None:
        command = [sys.executable, '-m', 'unittest', *UNIT_TESTS, '-v']
        kwargs = {}
    else:
        names = [path.removesuffix('.py').replace('/', '.') for path in UNIT_TESTS]
        command = [sys.executable, '-c', _CANDIDATE_TEST_RUNNER, *names]
        kwargs = {'input': json.dumps(snapshot), 'text': True}
    subprocess.run(command, cwd=root, check=True,
                   env={**os.environ, 'CADGEN_DAEMON': '0'}, **kwargs)


def build_release(root: Path, commands: list[str], models: tuple[str, ...], *, refresh: bool = False) -> dict:
    font = Path(os.environ.get('TEXT_CAD_CJK_FONT', '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'))
    plan = json.loads((root/'output/review/design_manifest.json').read_text())
    model = json.loads((root/'output/review/house_3d_assumptions_R01.json').read_text())
    return {
        'schema_version': 1, 'drawing_revision': plan['drawing_revision'], 'model_revision': model['revision'],
        'generated_at': datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(),
        'scope': 'Current house, apartment, river and Tokyo landmark reference geometry/drawings. No survey, engineering or regulatory approval.',
        'generation_commands': commands, 'validation_commands': VALIDATORS,
        'unit_test_commands': UNIT_TESTS, 'selected_models': list(models),
        'operation': 'validation_refresh' if refresh else 'staged_regeneration',
        'toolchain': {'python': platform.python_version(), 'platform': platform.system(),
                     'packages': {name: importlib.metadata.version(name) for name in
                                  ['cadgen', 'build123d', 'ezdxf', 'shapely', 'reportlab', 'PyMuPDF']},
                     'font': {'name': font.name, 'sha256': digest(font)}},
        'sources': _hashes(root, source_paths(root)),
        'artifacts': _hashes(root, artifact_paths(root)),
    }


def regenerate(models: tuple[str, ...], *, refresh: bool = False) -> None:
    root = ROOT
    previous = json.loads((root/RELEASE).read_text()) if (root/RELEASE).is_file() else None
    if refresh or set(models) != set(MODELS):
        check_scope(root, previous or {}, models, refresh=refresh)
    source_snapshot = _hashes(root, source_paths(root))
    output_snapshot = _hashes(root, _output_paths(root))
    gate_snapshot = (root/RELEASE).read_bytes() if (root/RELEASE).is_file() else None
    commands = [] if refresh else generation_commands(models)
    with staged_tree(root) as stage:
        (stage/RELEASE).unlink(missing_ok=True)
        run(commands, root=stage)
        run(VALIDATORS, root=stage)
        candidate = build_release(stage, commands, models, refresh=refresh)
        if refresh:
            # These bytes were authored previously. Retain their generation
            # timestamp/toolchain/commands; record this runner as validation.
            validation = candidate
            candidate = {**previous, 'operation': 'validation_refresh',
                         'validated_at': validation['generated_at'],
                         'validation_toolchain': validation['toolchain'],
                         **{key: validation[key] for key in ('validation_commands', 'unit_test_commands',
                                                            'selected_models', 'sources', 'artifacts')}}
            candidate.setdefault('generation_commands', [])
        run_unit_tests(candidate, root=stage)
        from cad_release import verify_snapshot
        verify_snapshot(stage, candidate)
        # Editors may keep working while an expensive export runs. Never
        # overwrite their changed sources, outputs or previous release gate.
        if source_snapshot != _hashes(root, source_paths(root)) or output_snapshot != _hashes(root, _output_paths(root)):
            raise RuntimeError('CAD sources or outputs changed during staging; live files were not replaced.')
        if gate_snapshot != ((root/RELEASE).read_bytes() if (root/RELEASE).is_file() else None):
            raise RuntimeError('CAD release changed during staging; live files were not replaced.')
        stage_outputs = _output_paths(stage)
        removed = set(output_snapshot) - set(stage_outputs)
        if removed:
            raise ValueError(f'Staged generation removed an existing CAD output: {sorted(removed)[0]}')
        changed = [path for path in stage_outputs
                   if output_snapshot.get(path) != digest(stage/path)]
        if refresh and changed:
            raise ValueError(f'Validation refresh changed CAD output: {changed[0]}')
        if not refresh:
            for path in changed:
                if artifact_model(path) not in models:
                    raise ValueError(f'Scoped generation changed an unselected output: {path}')
        (stage/RELEASE).write_text(json.dumps(candidate, ensure_ascii=False, indent=2)+'\n')
        promote_outputs(root, stage, changed)
    print(json.dumps(verify(root), ensure_ascii=False), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--regenerate', action='store_true', help='Rebuild house, apartment, river and landmark outputs, validate, then record provenance.')
    parser.add_argument('--validate', action='store_true', help='Verify provenance first, then validate saved CAD; never bless modified inputs.')
    parser.add_argument('--refresh-validation', action='store_true', help='Revalidate unchanged saved CAD after pipeline/check-only changes; generation and analysis changes are rejected.')
    parser.add_argument('--model', choices=['all', *MODELS], action='append', help='Model to regenerate; repeat for shared dependencies. Default: all.')
    parser.add_argument('--dry-run', action='store_true', help='Print selected generation commands without changing any files.')
    args = parser.parse_args()
    if sum((args.regenerate, args.validate, args.refresh_validation)) != 1:
        parser.error('Choose exactly one of --regenerate, --validate or --refresh-validation.')
    if (args.model or args.dry_run) and not args.regenerate:
        parser.error('--model and --dry-run apply only to --regenerate.')
    models = tuple(MODELS if not args.model or 'all' in args.model else [model for model in MODELS if model in args.model])
    if args.dry_run:
        print(json.dumps({'models': models, 'generation_commands': generation_commands(models),
                          'validation_commands': VALIDATORS, 'staged': True}, ensure_ascii=False, indent=2))
        return
    if args.validate:
        print(json.dumps(verify(), ensure_ascii=False), flush=True)
        run(VALIDATORS)
        run_unit_tests()
        return
    regenerate(models, refresh=args.refresh_validation)


if __name__ == '__main__':
    main()
