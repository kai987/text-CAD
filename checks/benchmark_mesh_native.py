"""Compare full GLB numeric audits against the independent Python decoder.

Run after building native API 3:
    .venv/bin/python checks/benchmark_mesh_native.py --output /tmp/mesh-audit.json
Input files are read once outside timing. Measurements include JSON parsing,
layout/bounds validation and numeric auditing; they exclude CAD generation,
disk reads, browser rendering and GPU work. No CAD artifact is modified.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import platform
from statistics import median
import sys
from time import perf_counter_ns

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))

from lib.native_glb import audit_glb_bytes
from lib.native_spatial import MANIFEST,backend_status

DEFAULT_FILES=['house_3d.glb','apartment_2ldk.glb','structure_W.glb','structure_S.glb','structure_RC.glb']


def source_hashes():
    paths=['src/lib/native_spatial.py','src/lib/native_glb.py','checks/benchmark_mesh_native.py']
    return {path:sha256((ROOT/path).read_bytes()).hexdigest() for path in paths}


def measure(function,warmups,trials):
    for _ in range(warmups): function()
    samples=[]
    for _ in range(trials):
        start=perf_counter_ns();function();samples.append((perf_counter_ns()-start)/1e6)
    return {'median_ms':median(samples),'minimum_ms':min(samples),
            'maximum_ms':max(samples),'samples_ms':samples}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths',nargs='*',type=Path)
    parser.add_argument('--warmups',type=int,default=3)
    parser.add_argument('--trials',type=int,default=10)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.warmups<0 or args.trials<1:
        parser.error('warmups must be nonnegative and trials positive')
    status=backend_status()
    if not status['available']:
        raise RuntimeError(f'Build the native extension before benchmarking: {status}')
    hashes=source_hashes();manifest=MANIFEST.read_text()
    report={'platform':platform.platform(),'architecture':platform.machine(),
            'python':platform.python_version(),'warmups':args.warmups,'trials':args.trials,
            'source_sha256':hashes,'native_manifest':json.loads(manifest),'files':[]}
    for path in args.paths or [ROOT/'GLB'/name for name in DEFAULT_FILES]:
        raw=path.read_bytes()
        python=lambda:audit_glb_bytes(raw,backend='python')
        rust=lambda:audit_glb_bytes(raw,backend='rust')
        expected=python()
        assert rust()==expected,f'Native and reference summaries differ: {path}'
        result={'path':str(path),'bytes':len(raw),'sha256':sha256(raw).hexdigest(),
                'mesh_count':expected['mesh_count'],'vertex_count':expected['vertex_count'],
                'triangle_count':expected['triangle_count'],'degenerate_count':expected['degenerate_count'],
                'python':measure(python,args.warmups,args.trials),
                'rust':measure(rust,args.warmups,args.trials)}
        report['files'].append(result)
        print(path.name,{key:round(result[key]['median_ms'],4) for key in ('python','rust')},flush=True)
    if source_hashes()!=hashes or MANIFEST.read_text()!=manifest:
        raise RuntimeError('Sources or native binary changed during measurement; rerun')
    if args.output:
        args.output.expanduser().write_text(json.dumps(report,indent=2)+'\n')
        print(f'Recorded {args.output}')


if __name__=='__main__': main()
