"""STEP transport compaction must preserve lexical content and appearance."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from lib.step_transport import compact_text, compact_export


class StepTransportTests(unittest.TestCase):
    def test_quoted_names_escaped_quotes_binary_and_numbers_are_unchanged(self):
        text = "#1 = PRODUCT('room A; B', 'O''Brien', \"0 AB\", (1.234567890123E-9, -0.));\n"
        self.assertEqual(compact_text(text), "#1=PRODUCT('room A; B','O''Brien',\"0 AB\",(1.234567890123E-9,-0.));\n")

    def test_whitespace_does_not_merge_tokens_or_change_comments(self):
        self.assertEqual(compact_text('FOO \n BAR(1  2); /* quote \' and spacing */'),
                         "FOO BAR(1 2);/* quote ' and spacing */\n")

    def test_sidecar_hash_is_updated_without_changing_appearance(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'test.step'
            raw = b"ISO-10303-21;\nDATA;\n#1 = PRODUCT('west cabinet', '', '', ());\nENDSEC;\nEND-ISO-10303-21;\n"
            path.write_bytes(raw)
            sidecar = path.with_suffix('.step.json')
            metadata = {'documentHash':hashlib.sha256(raw).hexdigest(), 'appearance':{'color':'#ABCDEF'}, 'animation':None, 'schemaVersion':1}
            sidecar.write_text(json.dumps(metadata))
            compact_export(path)
            updated = json.loads(sidecar.read_text())
            self.assertEqual(updated['documentHash'], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertLess(path.stat().st_size, len(raw))
            self.assertEqual({k:v for k,v in updated.items() if k!='documentHash'},
                             {k:v for k,v in metadata.items() if k!='documentHash'})


if __name__ == '__main__':
    unittest.main()
