"""Adversarial tests for publication freshness; no CAD runtime required."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('cad_release', Path(__file__).resolve().parents[1]/'src/cad_release.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


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


if __name__ == '__main__':
    unittest.main()
