"""Generate and validate the current CAD catalog before publishing (concept geometry only)."""
from __future__ import annotations
import argparse
from datetime import datetime
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from zoneinfo import ZoneInfo
from cad_release import ROOT, RELEASE, artifact_paths, digest, source_paths, verify

GENERATORS = ['src/generate_redesign_plans.py', 'src/generate_attic_plan.py',
              'src/generate_structure_plan.py', 'src/generate_site_plan.py',
              'src/house_3d.py', 'src/generate_structural_variants.py',
              'src/generate_structural_cases.py', 'src/apartment_2ldk.py',
              'web/scripts/generate-plan-svg.py']
VALIDATORS = ['checks/validate_redesign_plans.py', 'checks/validate_jp_drafting.py',
              'checks/validate_3d.py', 'checks/validate_site.py', 'checks/validate_structure.py',
              'checks/validate_structural_variants.py', 'checks/validate_structural_cases.py',
              'checks/validate_apartment.py', 'checks/validate_fixtures.py',
              'checks/validate_furniture.py', 'checks/validate_outdoor_lighting.py',
              'checks/validate_glb_native.py', 'checks/validate_indoor_lighting.py']
UNIT_TESTS = ['checks/test_cad_release.py', 'checks/test_orientation.py',
              'checks/test_step_transport.py', 'checks/test_attic_opening_rules.py',
              'checks/test_attic_layout.py', 'checks/test_upper_layout.py',
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


def run(paths: list[str]) -> None:
    for path in paths:
        print(f'CAD pipeline: {path}', flush=True)
        subprocess.run([sys.executable, path], cwd=ROOT, check=True,
                       env={**os.environ, 'CADGEN_DAEMON': '0'})


def run_unit_tests(snapshot: dict | None = None) -> None:
    print('CAD pipeline: Python unit tests', flush=True)
    if snapshot is None:
        command = [sys.executable, '-m', 'unittest', *UNIT_TESTS, '-v']
        kwargs = {}
    else:
        names = [path.removesuffix('.py').replace('/', '.') for path in UNIT_TESTS]
        command = [sys.executable, '-c', _CANDIDATE_TEST_RUNNER, *names]
        kwargs = {'input': json.dumps(snapshot), 'text': True}
    subprocess.run(command, cwd=ROOT, check=True,
                   env={**os.environ, 'CADGEN_DAEMON': '0'}, **kwargs)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--regenerate', action='store_true', help='Rebuild all current house/apartment outputs, validate, then record provenance.')
    parser.add_argument('--validate', action='store_true', help='Verify provenance first, then validate saved CAD; never bless modified inputs.')
    args = parser.parse_args()
    if args.regenerate == args.validate:
        parser.error('Choose exactly one of --regenerate or --validate.')
    if args.validate:
        print(json.dumps(verify(), ensure_ascii=False), flush=True)
        run(VALIDATORS)
        run_unit_tests()
        return
    # Invalidate the old gate before mutation; partial generation cannot be published.
    (ROOT/RELEASE).unlink(missing_ok=True)
    run(GENERATORS)
    run(VALIDATORS)
    font = Path(os.environ.get('TEXT_CAD_CJK_FONT', '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'))
    plan = json.loads((ROOT/'output/review/design_manifest.json').read_text())
    model = json.loads((ROOT/'output/review/house_3d_assumptions_R01.json').read_text())
    release = {
        'schema_version': 1, 'drawing_revision': plan['drawing_revision'], 'model_revision': model['revision'],
        'generated_at': datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(),
        'scope': 'Current house and apartment concept geometry/drawings. No engineering or regulatory approval.',
        'generation_commands': GENERATORS, 'validation_commands': VALIDATORS,
        'unit_test_commands': UNIT_TESTS,
        'toolchain': {'python': platform.python_version(), 'platform': platform.system(),
                     'packages': {name: importlib.metadata.version(name) for name in
                                  ['cadgen', 'build123d', 'ezdxf', 'shapely', 'reportlab', 'PyMuPDF']},
                     'font': {'name': font.name, 'sha256': digest(font)}},
        'sources': {path: digest(ROOT/path) for path in source_paths(ROOT)},
        'artifacts': {path: digest(ROOT/path) for path in artifact_paths(ROOT)},
    }
    run_unit_tests(release)
    (ROOT/RELEASE).write_text(json.dumps(release, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(verify(), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
