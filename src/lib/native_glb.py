"""Read-only numeric audit for this project's dense GLB triangle exports.

Rust decodes immutable BIN bytes; the independent Python backend uses struct.
The audit checks POSITION/NORMAL finiteness, indices, decoded position bounds
and byte spans. Degenerate triangles are diagnostics, not rejection criteria.
It does not certify manifold topology, normal directions, textures, world-space
transforms or construction suitability, and it never changes CAD or GLB files.

Container/alignment rules follow the Khronos glTF 2.0 specification:
https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html
Sparse/compressed accessors, external buffers and non-triangle primitives are
explicitly outside this bounded export profile.
"""
from __future__ import annotations

import json
from math import isfinite
from pathlib import Path
import struct

from . import native_spatial

_USIZE_MAX = (1 << (8 * struct.calcsize("P"))) - 1
_COMPONENT_SIZES = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
_COMPONENTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def _finite_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return isfinite(value)
    except OverflowError:
        return False


def _integer(value, name, *, minimum=0):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum or value > _USIZE_MAX:
        raise ValueError(f"{name} must be an addressable integer >= {minimum}")
    return value


def _layout(value, name, width, alignment, binary_length, *, minimum_count=0):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError(f"{name} requires (offset, stride, count)")
    offset, stride, count = (_integer(v, f"{name} {key}") for key, v in zip(("offset", "stride", "count"), value))
    if count < minimum_count or stride < width or offset % alignment or stride % alignment:
        raise ValueError(f"{name} has invalid count, stride or component alignment")
    end = offset + (count - 1) * stride + width if count else offset
    if end > _USIZE_MAX or end > binary_length:
        raise ValueError(f"{name} exceeds the BIN byte span")
    return offset, stride, count


def _layouts(binary, values):
    if not isinstance(binary, bytes):
        raise TypeError("Mesh audit requires immutable bytes")
    result = []
    for index, value in enumerate(values):
        if not isinstance(value, (list, tuple)) or len(value) != 3:
            raise ValueError(f"Mesh {index} requires position, optional indices and optional normals")
        position, indices, normals = value
        position = _layout(position, f"Mesh {index} POSITION", 12, 4, len(binary), minimum_count=1)
        if indices is not None:
            if not isinstance(indices, (list, tuple)) or len(indices) != 4:
                raise ValueError(f"Mesh {index} indices require (offset, stride, count, component_bytes)")
            component = _integer(indices[3], f"Mesh {index} index component bytes", minimum=1)
            if component not in (1, 2, 4):
                raise ValueError("Index component bytes must be 1, 2 or 4")
            indices = (*_layout(indices[:3], f"Mesh {index} indices", component, component, len(binary)), component)
            count = indices[2]
        else:
            count = position[2]
        if count % 3:
            raise ValueError(f"Mesh {index} triangle count is not divisible by three")
        if normals is not None:
            normals = _layout(normals, f"Mesh {index} NORMAL", 12, 4, len(binary))
            if normals[2] != position[2]:
                raise ValueError(f"Mesh {index} NORMAL count differs from POSITION")
        result.append((position, indices, normals))
    return result


def _python_audit(binary, layouts):
    results = []
    for mesh_index, (position, indices, normals) in enumerate(layouts):
        offset, stride, vertex_count = position
        vertices = []
        minimum = [float("inf")] * 3
        maximum = [float("-inf")] * 3
        for index in range(vertex_count):
            point = struct.unpack_from("<fff", binary, offset + index * stride)
            if not all(isfinite(value) for value in point):
                raise ValueError(f"Mesh {mesh_index} POSITION contains non-finite values")
            vertices.append(point)
            for axis, value in enumerate(point):
                minimum[axis] = min(minimum[axis], value)
                maximum[axis] = max(maximum[axis], value)
        if normals is not None:
            for index in range(normals[2]):
                normal = struct.unpack_from("<fff", binary, normals[0] + index * normals[1])
                if not all(isfinite(value) for value in normal):
                    raise ValueError(f"Mesh {mesh_index} NORMAL contains non-finite values")
        if indices is None:
            references = range(vertex_count)
            index_count = 0
        else:
            offset, stride, index_count, component = indices
            references = []
            format = {1: "<B", 2: "<H", 4: "<I"}[component]
            for index in range(index_count):
                value = struct.unpack_from(format, binary, offset + index * stride)[0]
                if value >= vertex_count or value == (1 << (component * 8)) - 1:
                    raise ValueError(f"Mesh {mesh_index} index is out of range or uses the prohibited primitive-restart value")
                references.append(value)
        degenerate_count = 0
        for index in range(0, len(references), 3):
            a, b, c = (vertices[references[index + part]] for part in range(3))
            u = tuple(b[axis] - a[axis] for axis in range(3))
            v = tuple(c[axis] - a[axis] for axis in range(3))
            cross = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
            if all(value == 0.0 for value in cross):
                degenerate_count += 1
        results.append((vertex_count, index_count, len(references) // 3,
                        None if normals is None else normals[2], tuple(minimum + maximum), degenerate_count))
    return results


def _checked_results(values, layouts):
    if not isinstance(values, (list, tuple)) or len(values) != len(layouts):
        raise RuntimeError("Invalid native mesh audit result count")
    result = []
    for value, (position, indices, normals) in zip(values, layouts):
        if not isinstance(value, (list, tuple)) or len(value) != 6:
            raise RuntimeError("Invalid native mesh audit result")
        vertices, index_count, triangles, normal_count, bounds, degenerates = value
        expected_indices = 0 if indices is None else indices[2]
        expected_triangles = (position[2] if indices is None else indices[2]) // 3
        expected_normals = None if normals is None else normals[2]
        if (any(isinstance(v, bool) or not isinstance(v, int) for v in (vertices, index_count, triangles, degenerates))
                or (vertices, index_count, triangles, normal_count) != (position[2], expected_indices, expected_triangles, expected_normals)
                or (normal_count is not None and (isinstance(normal_count, bool) or not isinstance(normal_count, int)))
                or not 0 <= degenerates <= triangles
                or not isinstance(bounds, (list, tuple)) or len(bounds) != 6
                or any(not _finite_number(v) for v in bounds)
                or any(bounds[axis] > bounds[axis + 3] for axis in range(3))):
            raise RuntimeError("Invalid native mesh audit counts or bounds")
        result.append((vertices, index_count, triangles, normal_count, tuple(float(v) for v in bounds), degenerates))
    return result


def audit_triangle_meshes(binary, layouts, *, backend="auto"):
    """Decode dense triangle layouts, with explicit Python/strict native backends.

    Layouts are (POSITION (offset,stride,count), optional indices
    (offset,stride,count,component_bytes), optional NORMAL (offset,stride,count)).
    All offsets are relative to immutable BIN bytes. Results preserve layout
    order: (vertices, indices, triangles, optional normals, six bounds, degenerates).
    """
    layouts = _layouts(binary, layouts)
    backend = native_spatial._backend(backend)
    module = native_spatial._native_for(backend)
    if module is not None:
        try:
            return _checked_results(module.audit_triangle_meshes(binary, layouts), layouts)
        except Exception as error:
            if backend == "rust":
                raise RuntimeError(f"Rust mesh audit failed: {error}") from error
    return _python_audit(binary, layouts)


def _json_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate GLB JSON key: {key}")
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError(f"Non-finite JSON constant: {value}")


def _container(raw):
    if not isinstance(raw, bytes):
        raise TypeError("GLB audit requires immutable bytes")
    if len(raw) < 20:
        raise ValueError("Truncated GLB header or first chunk")
    magic, version, total = struct.unpack_from("<4sII", raw)
    if magic != b"glTF" or version != 2 or total != len(raw):
        raise ValueError("GLB 2.0 magic, version or total length is invalid")
    chunks = []
    offset = 12
    while offset < len(raw):
        if offset + 8 > len(raw):
            raise ValueError("Truncated GLB chunk header")
        size, kind = struct.unpack_from("<II", raw, offset)
        end = offset + 8 + size
        if size % 4 or end > len(raw):
            raise ValueError("GLB chunk has an invalid length, alignment or byte span")
        chunks.append((kind, raw[offset + 8:end]))
        offset = end
    if len(chunks) != 2 or chunks[0][0] != 0x4E4F534A or chunks[1][0] != 0x004E4942:
        raise ValueError("Dense GLB audit requires a JSON chunk followed by one BIN chunk")
    try:
        document = json.loads(chunks[0][1].decode("utf-8"), object_pairs_hook=_json_pairs, parse_constant=_invalid_constant)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid GLB JSON: {error}") from error
    if not isinstance(document, dict) or not isinstance(document.get("asset"), dict) or document["asset"].get("version") != "2.0":
        raise ValueError("GLB asset must declare glTF 2.0")
    if document.get("extensionsRequired"):
        raise ValueError("Required glTF extensions are unsupported by the dense GLB audit")
    buffers = document.get("buffers")
    if not isinstance(buffers, list) or len(buffers) != 1 or not isinstance(buffers[0], dict):
        raise ValueError("Dense GLB audit requires one embedded buffer")
    if "uri" in buffers[0]:
        raise ValueError("External or URI buffers are unsupported by the dense GLB audit")
    if buffers[0].get("extensions"):
        raise ValueError("Buffer extensions are unsupported by the dense GLB audit")
    length = _integer(buffers[0].get("byteLength"), "Buffer byteLength", minimum=1)
    binary = chunks[1][1]
    if length > len(binary) or len(binary) - length > 3 or any(binary[length:]):
        raise ValueError("GLB BIN length or zero padding differs from its buffer declaration")
    return document, binary[:length]


def _table(document, name):
    table = document.get(name)
    if not isinstance(table, list) or not table:
        raise ValueError(f"GLB requires a nonempty {name} array")
    return table


def _reference(table, index, name):
    index = _integer(index, f"{name} reference")
    if index >= len(table) or not isinstance(table[index], dict):
        raise ValueError(f"Invalid {name} reference")
    return index, table[index]


def _number_bounds(value, count, name):
    if not isinstance(value, list) or len(value) != count or any(not _finite_number(v) for v in value):
        raise ValueError(f"{name} requires {count} finite bounds")
    return value


def _accessors(document, binary):
    views = _table(document, "bufferViews")
    for index, view in enumerate(views):
        if not isinstance(view, dict) or _integer(view.get("buffer"), f"bufferView {index} buffer") != 0:
            raise ValueError("bufferViews must refer to the embedded buffer")
        if view.get("extensions"):
            raise ValueError("bufferView extensions are unsupported by the dense GLB audit")
        start = _integer(view.get("byteOffset", 0), f"bufferView {index} byteOffset")
        size = _integer(view.get("byteLength"), f"bufferView {index} byteLength", minimum=1)
        if start + size > len(binary):
            raise ValueError(f"bufferView {index} exceeds the embedded buffer")
        if "byteStride" in view:
            stride = _integer(view["byteStride"], f"bufferView {index} byteStride", minimum=4)
            if stride > 252 or stride % 4:
                raise ValueError("glTF vertex byteStride must be a multiple of four between 4 and 252")
        if view.get("target") not in (None, 34962, 34963):
            raise ValueError("Invalid bufferView target")
    accessors = _table(document, "accessors")
    layouts = []
    for index, accessor in enumerate(accessors):
        if not isinstance(accessor, dict):
            raise ValueError("Invalid accessor object")
        if "sparse" in accessor:
            raise ValueError("Sparse accessors are unsupported by the dense GLB audit")
        if accessor.get("extensions"):
            raise ValueError("Accessor extensions are unsupported by the dense GLB audit")
        _, view = _reference(views, accessor.get("bufferView"), f"accessor {index} bufferView")
        component = accessor.get("componentType")
        kind = accessor.get("type")
        if (isinstance(component, bool) or not isinstance(component, int) or component not in _COMPONENT_SIZES
                or not isinstance(kind, str) or kind not in _COMPONENTS):
            raise ValueError("Unsupported accessor component or element type")
        if not isinstance(accessor.get("normalized", False), bool) or (accessor.get("normalized", False) and component in (5125, 5126)):
            raise ValueError("Accessor normalization is invalid for its component type")
        count = _integer(accessor.get("count"), f"accessor {index} count", minimum=1)
        start = _integer(accessor.get("byteOffset", 0), f"accessor {index} byteOffset")
        alignment = _COMPONENT_SIZES[component]
        width = alignment * _COMPONENTS[kind]
        stride = view.get("byteStride", width)
        absolute = view.get("byteOffset", 0) + start
        if start % alignment or absolute % alignment or stride < width or stride % alignment:
            raise ValueError(f"accessor {index} has invalid alignment or stride")
        if start + (count - 1) * stride + width > view["byteLength"]:
            raise ValueError(f"accessor {index} exceeds its bufferView byte span")
        for bound in ("min", "max"):
            if bound in accessor:
                _number_bounds(accessor[bound], _COMPONENTS[kind], f"accessor {index} {bound}")
        if "min" in accessor and "max" in accessor and any(a > b for a, b in zip(accessor["min"], accessor["max"])):
            raise ValueError(f"accessor {index} has reversed declared bounds")
        layouts.append((absolute, stride, count))
    return accessors, views, layouts


def _float32(value):
    try:
        result = struct.unpack("<f", struct.pack("<f", value))[0]
    except (OverflowError, struct.error) as error:
        raise ValueError("Declared POSITION bounds cannot be represented as float32") from error
    if not isfinite(result):
        raise ValueError("Declared POSITION bounds must remain finite as float32")
    return result


def audit_glb_bytes(raw, *, backend="auto"):
    """Return decoded primitive counts and mesh-space bounds, or reject input.

    Declared POSITION bounds are converted to their accessor's float32 type and
    must exactly match decoded extrema. This is a bounded numeric audit, not a
    complete glTF validator; ancillary attribute spans are checked but texture,
    animation, topology and unit-normal semantics are outside its scope.
    """
    document, binary = _container(raw)
    accessors, views, accessor_layouts = _accessors(document, binary)
    meshes = _table(document, "meshes")
    descriptors = []
    metadata = []
    for mesh_index, mesh in enumerate(meshes):
        if not isinstance(mesh, dict) or not isinstance(mesh.get("primitives"), list) or not mesh["primitives"]:
            raise ValueError("Each mesh must have nonempty primitives")
        for primitive_index, primitive in enumerate(mesh["primitives"]):
            if (not isinstance(primitive, dict) or not isinstance(primitive.get("mode", 4), int)
                    or primitive.get("mode", 4) != 4 or isinstance(primitive.get("mode"), bool)):
                raise ValueError("Only TRIANGLES primitives are supported by the dense GLB audit")
            if primitive.get("extensions") or primitive.get("targets"):
                raise ValueError("Primitive extensions and morph targets are unsupported by the dense GLB audit")
            attributes = primitive.get("attributes")
            if not isinstance(attributes, dict) or "POSITION" not in attributes:
                raise ValueError("Triangle primitive requires POSITION")
            position_index, position = _reference(accessors, attributes["POSITION"], "POSITION accessor")
            if position["type"] != "VEC3" or position["componentType"] != 5126 or position.get("normalized", False):
                raise ValueError("POSITION requires an unnormalized float32 VEC3 accessor")
            for bound in ("min", "max"):
                _number_bounds(position.get(bound), 3, f"POSITION {bound}")
            for semantic, reference in attributes.items():
                attribute_index, attribute = _reference(accessors, reference, f"{semantic} accessor")
                _, view = _reference(views, attribute["bufferView"], f"{semantic} bufferView")
                if attribute["count"] != position["count"]:
                    raise ValueError("Vertex attribute count differs from POSITION")
                if attribute.get("byteOffset", 0) % 4 or accessor_layouts[attribute_index][1] % 4 or view.get("target") not in (None, 34962):
                    raise ValueError("Vertex attributes require four-byte alignment and a vertex buffer target")
            normal_layout = None
            if "NORMAL" in attributes:
                normal_index, normal = _reference(accessors, attributes["NORMAL"], "NORMAL accessor")
                if normal["type"] != "VEC3" or normal["componentType"] != 5126 or normal.get("normalized", False):
                    raise ValueError("NORMAL requires an unnormalized float32 VEC3 accessor")
                normal_layout = accessor_layouts[normal_index]
            index_layout = None
            if "indices" in primitive:
                index, accessor = _reference(accessors, primitive["indices"], "indices accessor")
                _, view = _reference(views, accessor["bufferView"], "indices bufferView")
                if accessor["type"] != "SCALAR" or accessor["componentType"] not in (5121, 5123, 5125) or accessor.get("normalized", False):
                    raise ValueError("Indices require an unnormalized unsigned SCALAR accessor")
                if "byteStride" in view or view.get("target") not in (None, 34963):
                    raise ValueError("Indices must be tightly packed in an index bufferView")
                index_layout = (*accessor_layouts[index], _COMPONENT_SIZES[accessor["componentType"]])
            descriptors.append((accessor_layouts[position_index], index_layout, normal_layout))
            metadata.append((mesh_index, primitive_index, mesh.get("name"), position))
    results = audit_triangle_meshes(binary, descriptors, backend=backend)
    primitives = []
    for value, (mesh_index, primitive_index, mesh_name, position) in zip(results, metadata):
        vertices, indices, triangles, normals, bounds, degenerates = value
        declared = tuple(_float32(value) for value in position["min"] + position["max"])
        if declared != bounds:
            raise ValueError(f"Mesh {mesh_index} primitive {primitive_index} declared POSITION bounds differ from decoded bytes")
        primitives.append({"mesh_index": mesh_index, "primitive_index": primitive_index, "mesh_name": mesh_name,
                           "vertex_count": vertices, "index_count": indices, "triangle_count": triangles,
                           "normal_count": normals, "bounds": list(bounds), "degenerate_count": degenerates})
    bounds = [min(row["bounds"][axis] for row in primitives) for axis in range(3)] + [
        max(row["bounds"][axis + 3] for row in primitives) for axis in range(3)]
    return {"version": 1, "profile": "dense_float32_triangles", "mesh_count": len(meshes),
            "primitive_count": len(primitives), "vertex_count": sum(row["vertex_count"] for row in primitives),
            "index_count": sum(row["index_count"] for row in primitives),
            "triangle_count": sum(row["triangle_count"] for row in primitives),
            "normal_count": sum(row["normal_count"] or 0 for row in primitives),
            "degenerate_count": sum(row["degenerate_count"] for row in primitives),
            "bounds": bounds, "primitives": primitives}


def audit_glb_file(path, *, backend="auto"):
    return audit_glb_bytes(Path(path).read_bytes(), backend=backend)
