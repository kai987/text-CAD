"""Lossless STEP text compaction for hosts with a 25 MiB file limit."""
import hashlib
import json
from pathlib import Path
import re

TOKENS = re.compile(r"'(?:[^']|'')*'|/\*.*?\*/|\"[^\"]*\"|\s+|[^\s'\"/]+|/", re.S)


def compact_text(text: str) -> str:
    """Keep quoted strings, comments and lexical token boundaries unchanged.

    No number is parsed or rounded. Only insignificant whitespace is removed;
    occasional record breaks keep the resulting text readable by STEP parsers.
    """
    result = []
    records = 0
    def record_break(match):
        nonlocal records
        records += 1
        return ';\n' if records % 128 == 0 else ';'
    for match in TOKENS.finditer(text):
        token = match[0]
        if token.isspace():
            before = text[match.start()-1] if match.start() else ''
            after = text[match.end()] if match.end() < len(text) else ''
            if before and after and (before.isalnum() or before == '_') and (after.isalnum() or after == '_'):
                result.append(' ')
        elif token.startswith(("'", '"', '/*')):
            result.append(token)
        else:
            result.append(re.sub(';', record_break, token))
    return ''.join(result).rstrip()+'\n'


def compact_export(path: Path) -> None:
    sidecar = path.with_suffix(path.suffix+'.json')
    original = path.read_bytes()
    metadata = json.loads(sidecar.read_text())
    if metadata['documentHash'] != hashlib.sha256(original).hexdigest():
        raise ValueError('STEP appearance metadata does not match the exported document.')
    compact = compact_text(original.decode('utf-8')).encode('utf-8')
    if len(compact) > 25 * 1024 * 1024:
        raise ValueError('Compacted STEP still exceeds the Sites 25 MiB file limit.')
    metadata['documentHash'] = hashlib.sha256(compact).hexdigest()
    path.write_bytes(compact)
    sidecar.write_text(json.dumps(metadata, separators=(',', ':'))+'\n')
    print(f'Lossless STEP text compaction: {len(original)} -> {len(compact)} bytes')
