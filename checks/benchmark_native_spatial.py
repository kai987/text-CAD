"""Reproducible full-call benchmark; never exports or modifies CAD artifacts.

Run after building the local extension:
    .venv/bin/python checks/benchmark_native_spatial.py --output /tmp/spatial.json
Includes Python validation, marshaling, BVH construction and result checks.
Furniture timings also include footprint/room/route construction, but exclude
the floor plan prepared once and CAD solids/export/rendering. Synthetic BVH
timings are not whole-building generation or browser rendering speedups.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import platform
import random
from statistics import median
import sys
from time import perf_counter_ns

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'src'))

from checks.test_furniture_native import original_report
from lib.apartment_plan import P as APARTMENT,apartment_plan
from lib.house_plan import P as HOUSE,floor_plan
from lib.furniture_geometry import clearance_report
from lib.native_spatial import MANIFEST,aabb_candidates,backend_status


def measure(function,warmups,trials):
    for _ in range(warmups): function()
    samples=[]
    for _ in range(trials):
        start=perf_counter_ns();function();samples.append((perf_counter_ns()-start)/1e6)
    return {'median_ms':median(samples),'minimum_ms':min(samples),
            'maximum_ms':max(samples),'samples_ms':samples}


def source_hashes():
    paths=['src/lib/native_spatial.py','src/lib/furniture_geometry.py',
           'checks/test_furniture_native.py','checks/benchmark_native_spatial.py']
    return {path:sha256((ROOT/path).read_bytes()).hexdigest() for path in paths}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--warmups',type=int,default=5)
    parser.add_argument('--trials',type=int,default=30)
    parser.add_argument('--bounds',type=int,default=10000)
    parser.add_argument('--queries',type=int,default=100)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.warmups<0 or min(args.trials,args.bounds,args.queries)<1:
        parser.error('warmups must be nonnegative and other counts positive')
    status=backend_status()
    if not status['available']:
        raise RuntimeError(f'Build the native extension before benchmarking: {status}')
    hashes=source_hashes();manifest=MANIFEST.read_text()
    report={'platform':platform.platform(),'architecture':platform.machine(),
            'python':platform.python_version(),'warmups':args.warmups,'trials':args.trials,
            'backend_status':status,'source_sha256':hashes,'native_manifest':json.loads(manifest),
            'furniture':[]}
    layouts=[('house_f1','house',floor_plan(1),HOUSE),
             ('house_f2','house',floor_plan(2),HOUSE),
             ('apartment_f1','apartment',apartment_plan()[0],APARTMENT)]
    for name,model,floor,parameters in layouts:
        original=lambda:original_report(floor,model,parameters)
        python=lambda:clearance_report(floor,model,parameters,backend='python')
        rust=lambda:clearance_report(floor,model,parameters,backend='rust')
        expected=original()
        assert python()==rust()==expected,name
        result={'layout':name,'checks':len(expected),
                'original_shapely':measure(original,args.warmups,args.trials),
                'batched_python':measure(python,args.warmups,args.trials),
                'rust_filtered_geos':measure(rust,args.warmups,args.trials)}
        report['furniture'].append(result)
        print(name, {key:round(result[key]['median_ms'],4) for key in
                     ('original_shapely','batched_python','rust_filtered_geos')})
    rng=random.Random(41007)
    bounds=[]
    for _ in range(args.bounds):
        minimum=[rng.uniform(-10000,10000) for _ in range(3)]
        bounds.append(tuple(minimum+[value+rng.uniform(20,1200) for value in minimum]))
    queries=[]
    for _ in range(args.queries):
        minimum=[rng.uniform(-10000,10000) for _ in range(3)]
        queries.append(tuple(minimum+[value+rng.uniform(200,1600) for value in minimum]))
    python=lambda:aabb_candidates(bounds,queries,backend='python')
    rust=lambda:aabb_candidates(bounds,queries,backend='rust')
    expected=python()
    assert rust()==expected,'BVH results differ'
    report['synthetic_aabb']={'seed':41007,'bounds':len(bounds),'queries':len(queries),
                              'candidates':sum(map(len,expected)),
                              'python':measure(python,args.warmups,args.trials),
                              'rust':measure(rust,args.warmups,args.trials)}
    print('synthetic_aabb', {key:round(report['synthetic_aabb'][key]['median_ms'],4)
                             for key in ('python','rust')})
    if source_hashes()!=hashes or MANIFEST.read_text()!=manifest:
        raise RuntimeError('Sources or native binary changed during measurement; rerun benchmark')
    if args.output:
        args.output.expanduser().write_text(json.dumps(report,indent=2)+'\n')
        print(f'Recorded {args.output}')


if __name__=='__main__': main()
