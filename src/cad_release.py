"""Dependency-free source/artifact freshness gate; geometry checks are in cad_pipeline."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = 'output/review/cad_release.json'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_paths(root: Path) -> list[str]:
    paths = [*root.glob('src/**/*.py'), *root.glob('checks/**/*.py')]
    paths += [root/'requirements.txt', root/'web/scripts/generate-plan-svg.py']
    return sorted(str(p.relative_to(root)) for p in paths if p.is_file())


def artifact_paths(root: Path) -> list[str]:
    paths = [*root.glob('DXF/*'), *root.glob('STEP/*'), *root.glob('GLB/*'),
             *root.glob('output/pdf/*'), *root.glob('output/vector/*'),
             *root.glob('output/review/*.json'), *root.glob('output/review/cases/*.json')]
    paths += [root/'web/src/plan-preview-metadata.json']
    # Historical DXFs/PDFs are retained and tracked; optional screenshots are browser QA, not generated CAD.
    return sorted(str(p.relative_to(root)) for p in paths if p.is_file() and str(p.relative_to(root)) != RELEASE and 'validation' not in p.stem)


def verify(root: Path = ROOT) -> dict:
    release = json.loads((root/RELEASE).read_text())
    return verify_snapshot(root, release)


def verify_snapshot(root: Path, release: dict) -> dict:
    """Check an unpublished candidate with exactly the final release's rules."""
    if release.get('schema_version') != 1 or not release.get('validation_commands'):
        raise ValueError('CAD release has no completed validation provenance.')
    if sorted(release['sources']) != source_paths(root):
        raise ValueError('CAD source set changed; run src/cad_pipeline.py --regenerate.')
    for section in ('sources', 'artifacts'):
        for relative, expected in release[section].items():
            path = (root/relative).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file() or digest(path) != expected:
                raise ValueError(f'Stale CAD {section}: {relative}; run src/cad_pipeline.py --regenerate.')
    if sorted(release['artifacts']) != artifact_paths(root):
        raise ValueError('CAD artifact set changed; run src/cad_pipeline.py --regenerate.')
    return {'revision': release['drawing_revision'], 'sources': len(release['sources']),
            'artifacts': len(release['artifacts']), 'scope': release['scope']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(verify(args.root.resolve()), ensure_ascii=False))
