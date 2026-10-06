"""Optional Rust spatial computations with explicit, compatible Python fallback.

This module handles geometry only, in the caller's units. It never interprets
building codes, sizes structural members, changes CAD solids or exports files.
Build the local extension with ``.venv/bin/python src/build_spatial_native.py``.
"""
from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
import importlib
import json
from math import isfinite
import os
from pathlib import Path
import sys
import sysconfig

ROOT = Path(__file__).resolve().parents[2]
CRATE = ROOT / "rust" / "spatial-core"
MANIFEST = Path(__file__).with_name("_spatial_native.manifest.json")


def _source_hashes():
    paths = [CRATE / "Cargo.toml", CRATE / "Cargo.lock", CRATE / "rust-toolchain.toml",
             *sorted((CRATE / "src").rglob("*.rs"))]
    return {path.relative_to(ROOT).as_posix(): sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)}


@lru_cache(maxsize=1)
def _load_native():
    try:
        binary = Path(__file__).with_name("_spatial_native" + sysconfig.get_config_var("EXT_SUFFIX"))
        manifest = json.loads(MANIFEST.read_text())
        if manifest.get("version") != 1 or manifest.get("api_version") != 3:
            raise RuntimeError("Unsupported native spatial manifest version")
        if manifest.get("python_cache_tag") != sys.implementation.cache_tag:
            raise RuntimeError("Native spatial Python version changed; rebuild the extension")
        if manifest.get("sources") != _source_hashes():
            raise RuntimeError("Native spatial sources changed; rebuild the extension")
        if manifest.get("binary_sha256") != sha256(binary.read_bytes()).hexdigest():
            raise RuntimeError("Native spatial binary differs from the build manifest")
        module = importlib.import_module("._spatial_native", __package__)
        if module.api_version() != 3:
            raise RuntimeError("Native spatial API mismatch")
        return module, None
    except (ImportError, OSError, ValueError, RuntimeError, AttributeError) as error:
        return None, str(error)


def _backend(value):
    selected = os.environ.get("TEXT_CAD_SPATIAL_BACKEND", "auto") if value == "auto" else value
    if selected not in ("auto", "python", "rust"):
        raise ValueError("Spatial backend must be auto, python or rust")
    return selected


def backend_status():
    module, reason = _load_native()
    requested = _backend("auto")
    return {"available": module is not None, "requested": requested,
            "selected": ("unavailable" if requested == "rust" and module is None else
                         "python" if requested == "python" or module is None else "rust"),
            "reason": reason}


def _native_for(backend):
    if backend == "python":
        return None
    module, reason = _load_native()
    if module is None and backend == "rust":
        raise RuntimeError(f"Rust spatial backend unavailable: {reason}")
    return module


def _pairs(pairs, count):
    result = []
    for pair in pairs:
        if len(pair) != 2 or any(isinstance(i, bool) or not isinstance(i, int) or i < 0 or i >= count for i in pair):
            raise ValueError("Spatial pair indices must refer to existing geometries")
        result.append(tuple(pair))
    return result


def _geometry_bounds(geometry):
    if geometry.is_empty:
        return None
    if not geometry.is_valid or geometry.has_z:
        raise ValueError("Rust polygon filtering requires valid, finite 2D polygons")
    if geometry.geom_type not in ("Polygon", "MultiPolygon"):
        raise ValueError("Rust polygon filtering supports Polygon and MultiPolygon")
    minx,miny,maxx,maxy=geometry.bounds
    if any(not isfinite(value) for value in (minx,miny,maxx,maxy)):
        raise ValueError("Polygon coordinates must be finite")
    # All nonempty valid polygons have positive planar area. Embedding their
    # bounds in a shared unit Z interval preserves strict 2D overlap exactly.
    return (minx,miny,0.0,maxx,maxy,1.0)


def polygon_metrics(geometries, area_pairs, cover_pairs, *, backend="auto"):
    """Rust candidate filtering followed by exact GEOS area/coverage predicates.

    Rust never approximates polygon intersections or their decision thresholds.
    Only strictly disjoint bounding boxes are excluded; holes, narrow overlaps,
    shared boundaries and rotated polygons are resolved by the original engine.
    """
    geometries = list(geometries)
    area_pairs = _pairs(area_pairs, len(geometries))
    cover_pairs = _pairs(cover_pairs, len(geometries))
    backend = _backend(backend)
    module = _native_for(backend)
    if module is not None:
        try:
            bounds=[];mapping={}
            for index,geometry in enumerate(geometries):
                bound=_geometry_bounds(geometry)
                if bound is not None:
                    mapping[index]=len(bounds);bounds.append(bound)
            sources=sorted({a for a,b in area_pairs+cover_pairs if a in mapping})
            queries=[bounds[mapping[index]] for index in sources]
            results=_checked_candidates(module,bounds,queries,0.0)
            candidates={index:set(row) for index,row in zip(sources,results)}
            def possible(a,b):
                return a in candidates and b in mapping and mapping[b] in candidates[a]
            areas=[geometries[a].intersection(geometries[b]).area if possible(a,b) else 0.0
                   for a,b in area_pairs]
            covers=[bool(geometries[a].covers(geometries[b])) if possible(a,b) else False
                    for a,b in cover_pairs]
            return areas,covers
        except Exception as error:
            if backend == "rust":
                raise RuntimeError(f"Rust polygon metrics failed: {error}") from error
    return ([geometries[a].intersection(geometries[b]).area for a, b in area_pairs],
            [bool(geometries[a].covers(geometries[b])) for a, b in cover_pairs])


def _bounds(values):
    result = []
    for value in values:
        if len(value) != 6:
            raise ValueError("AABB needs six coordinates")
        bounds = tuple(float(v) for v in value)
        if any(not isfinite(v) for v in bounds) or any(bounds[i] > bounds[i + 3] for i in range(3)):
            raise ValueError("AABB coordinates must be finite with minimum <= maximum")
        result.append(bounds)
    return result


def _overlapping(a, b, epsilon):
    return all(a[i] < b[i + 3] - epsilon and b[i] < a[i + 3] - epsilon for i in range(3))


def _contacting(a,b,tolerance):
    return all(a[i]<=b[i+3]+tolerance and b[i]<=a[i+3]+tolerance for i in range(3))


def _checked_candidates(module,bounds,queries,epsilon,*,contact=False):
    query=module.aabb_contact_candidates if contact else module.aabb_candidates
    predicate=_contacting if contact else _overlapping
    results=query(bounds,queries,epsilon)
    if (len(results)!=len(queries) or any(
            not isinstance(row,list) or row!=sorted(set(row))
            or any(isinstance(i,bool) or not isinstance(i,int) or i<0 or i>=len(bounds)
                   or not predicate(bounds[i],query,epsilon) for i in row)
            for query,row in zip(queries,results))):
        raise RuntimeError("Invalid native AABB candidate result")
    return results


def aabb_candidates(bounds, queries, epsilon=1e-6, *, backend="auto"):
    """Ordered candidates only; exact solid intersection remains in the CAD kernel."""
    bounds, queries = _bounds(bounds), _bounds(queries)
    epsilon = float(epsilon)
    if not isfinite(epsilon) or epsilon < 0:
        raise ValueError("AABB epsilon must be finite and non-negative")
    backend = _backend(backend)
    module = _native_for(backend)
    if module is not None:
        try:
            return _checked_candidates(module,bounds,queries,epsilon)
        except Exception as error:
            if backend == "rust":
                raise RuntimeError(f"Rust AABB query failed: {error}") from error
    return [[i for i, bound in enumerate(bounds) if _overlapping(bound, query, epsilon)] for query in queries]


def aabb_contact_candidates(bounds,queries,tolerance=.001,*,backend="auto"):
    """Inclusive contact candidates, retaining planar faces and touching bounds.

    The tolerance bounds each axis separately; boxes remain a conservative
    screen. The caller must retain the CAD distance and exact face intersection
    tests before reporting a physical contact. Units match the input bounds.
    """
    bounds,queries=_bounds(bounds),_bounds(queries)
    tolerance=float(tolerance)
    if not isfinite(tolerance) or tolerance<0:
        raise ValueError("Contact tolerance must be finite and non-negative")
    backend=_backend(backend)
    module=_native_for(backend)
    if module is not None:
        try:
            return _checked_candidates(module,bounds,queries,tolerance,contact=True)
        except Exception as error:
            if backend=="rust":
                raise RuntimeError(f"Rust contact query failed: {error}") from error
    return [[i for i,bound in enumerate(bounds) if _contacting(bound,query,tolerance)]
            for query in queries]
