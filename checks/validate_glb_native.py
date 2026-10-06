"""Read-only dense GLB audit; optional report writing is explicit."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lib.native_glb import audit_glb_file

DEFAULT_FILES = ["house_3d.glb", "apartment_2ldk.glb", "structure_W.glb", "structure_S.glb", "structure_RC.glb"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="Defaults to the five saved house/apartment/structure GLBs")
    parser.add_argument("--backend", choices=("auto", "python", "rust"), default="auto")
    parser.add_argument("--report", type=Path, help="Write a JSON report only when explicitly requested")
    args = parser.parse_args(argv)
    files = args.paths or [ROOT / "GLB" / name for name in DEFAULT_FILES]
    results = []
    for path in files:
        try:
            audit = audit_glb_file(path, backend=args.backend)
            results.append({"path": str(path), "pass": True, "audit": audit})
        except (OSError, TypeError, ValueError, RuntimeError) as error:
            results.append({"path": str(path), "pass": False, "error": str(error)})
    report = {"version": 1, "pass": all(row["pass"] for row in results), "backend_requested": args.backend,
              "scope": "Dense triangle numeric data and decoded POSITION bounds; no topology or engineering certification",
              "files": results}
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text)
    sys.stdout.write(text)
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
