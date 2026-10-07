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


def run(paths: list[str]) -> None:
    for path in paths:
        print(f'CAD pipeline: {path}', flush=True)
        subprocess.run([sys.executable, path], cwd=ROOT, check=True,
                       env={**os.environ, 'CADGEN_DAEMON': '0'})


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
        return
    # Invalidate the old gate before mutation; partial generation cannot be published.
    (ROOT/RELEASE).unlink(missing_ok=True)
    run(GENERATORS)
    run(VALIDATORS)
    subprocess.run([sys.executable, '-m', 'unittest', 'checks/test_cad_release.py', 'checks/test_orientation.py', 'checks/test_step_transport.py', 'checks/test_attic_opening_rules.py', 'checks/test_attic_layout.py', 'checks/test_upper_layout.py', '-v'], cwd=ROOT, check=True)
    font = Path(os.environ.get('TEXT_CAD_CJK_FONT', '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'))
    plan = json.loads((ROOT/'output/review/design_manifest.json').read_text())
    model = json.loads((ROOT/'output/review/house_3d_assumptions_R01.json').read_text())
    release = {
        'schema_version': 1, 'drawing_revision': plan['drawing_revision'], 'model_revision': model['revision'],
        'generated_at': datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(),
        'scope': 'Current house and apartment concept geometry/drawings. No engineering or regulatory approval.',
        'generation_commands': GENERATORS, 'validation_commands': VALIDATORS,
        'toolchain': {'python': platform.python_version(), 'platform': platform.system(),
                     'packages': {name: importlib.metadata.version(name) for name in
                                  ['cadgen', 'build123d', 'ezdxf', 'shapely', 'reportlab', 'PyMuPDF']},
                     'font': {'name': font.name, 'sha256': digest(font)}},
        'sources': {path: digest(ROOT/path) for path in source_paths(ROOT)},
        'artifacts': {path: digest(ROOT/path) for path in artifact_paths(ROOT)},
    }
    (ROOT/RELEASE).write_text(json.dumps(release, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(verify(), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
