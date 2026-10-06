#!/usr/bin/env python3
"""Build optional Rust spatial checks for the running CPython interpreter.

Run with the CAD virtual environment's Python, for example:
    .venv/bin/python src/build_spatial_native.py

The extension and integrity manifest stay local and are gitignored. The default
CAD environment can still use its Shapely/Python fallback without this build.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    project = Path(__file__).resolve().parent.parent
    crate = project / "rust" / "spatial-core"
    target = crate / "target"
    suffix = sysconfig.get_config_var("EXT_SUFFIX")
    if not suffix:
        raise RuntimeError("The current interpreter has no native extension suffix")
    environment = os.environ.copy()
    environment["PYO3_PYTHON"] = sys.executable
    environment["CARGO_TARGET_DIR"] = str(target)
    environment["RUSTFLAGS"] = (
        environment.get("RUSTFLAGS", "") + f" --remap-path-prefix={project}=."
    ).strip()
    subprocess.run(
        ["cargo", "build", "--locked", "--release", "--features", "python"],
        cwd=crate,
        env=environment,
        check=True,
    )
    if sys.platform == "darwin":
        library = target / "release" / "libtext_cad_spatial_core.dylib"
    elif sys.platform == "win32":
        library = target / "release" / "text_cad_spatial_core.dll"
    else:
        library = target / "release" / "libtext_cad_spatial_core.so"
    output = project / "src" / "lib" / f"_spatial_native{suffix}"
    temporary = output.with_name(output.name + ".tmp")
    shutil.copy2(library, temporary)
    os.replace(temporary, output)
    sources = sorted([
        crate / "Cargo.toml",
        crate / "Cargo.lock",
        crate / "rust-toolchain.toml",
        *list((crate / "src").rglob("*.rs")),
    ])
    manifest = {
        "version": 1,
        "api_version": 3,
        "sources": {path.relative_to(project).as_posix(): sha256(path) for path in sources},
        "binary_sha256": sha256(output),
        "python_cache_tag": sys.implementation.cache_tag,
    }
    manifest_path = output.parent / "_spatial_native.manifest.json"
    temporary_manifest = manifest_path.with_name(manifest_path.name + ".tmp")
    temporary_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary_manifest, manifest_path)
    subprocess.run([
        sys.executable, "-c",
        "import sys; sys.path.insert(0, sys.argv[1]); "
        "from lib import _spatial_native; "
        "assert _spatial_native.api_version() == 3; "
        "assert not hasattr(_spatial_native, 'polygon_metrics'); "
        "assert _spatial_native.aabb_candidates([], [], 0.0) == []; "
        "assert _spatial_native.aabb_contact_candidates([], [], 0.0) == []; "
        "assert _spatial_native.audit_triangle_meshes(b'', []) == []; "
        "print('Verified Rust spatial native API', _spatial_native.api_version())",
        str(project / "src"),
    ], check=True)
    print(f"Built {output}")
    print(f"Recorded {manifest_path}")


if __name__ == "__main__":
    main()
