"""Cache immutable CAD geometry while filtering possible contact pairs.

Bounding boxes only identify candidates. Callers must retain their exact CAD
distance predicates, and contact area is always computed with face booleans.
One context belongs to one validation run; do not mutate cached shapes.
"""
from __future__ import annotations

from .native_spatial import aabb_contact_candidates


class ContactGeometry:
    """Reuse bounds and faces without changing exact contact calculations."""

    def __init__(self, *, backend="auto", tolerance=.001):
        self.backend = backend
        self.tolerance = tolerance
        # Hold the objects as well as their ids so temporary face wrappers
        # cannot be collected and have their ids reused during this run.
        self._bounds = {}
        self._faces = {}

    def bounds(self, shape):
        key = id(shape)
        if key not in self._bounds:
            box = shape.bounding_box()
            self._bounds[key] = (shape, (box.min.X, box.min.Y, box.min.Z,
                                        box.max.X, box.max.Y, box.max.Z))
        return self._bounds[key][1]

    def faces(self, shape):
        key = id(shape)
        if key not in self._faces:
            self._faces[key] = (shape, tuple(shape.faces()))
        return self._faces[key][1]

    def candidate_rows(self, supports, queries):
        """Return original-order supports for each query, including touching.

        Per-axis separation up to the tolerance is conservative for Euclidean
        CAD distance. Degenerate face bounds are valid contact candidates.
        """
        supports, queries = tuple(supports), tuple(queries)
        rows = aabb_contact_candidates(
            [self.bounds(shape) for shape in supports],
            [self.bounds(shape) for shape in queries],
            self.tolerance, backend=self.backend)
        return [tuple(supports[index] for index in row) for row in rows]

    def candidates(self, query, supports):
        return self.candidate_rows(supports, (query,))[0]

    def shared_face_area(self, a, b):
        """Sum original ordered native face intersections, never box area."""
        faces_a, faces_b = self.faces(a), self.faces(b)
        candidates = self.candidate_rows(faces_b, faces_a)
        total = 0.
        for face, supports in zip(faces_a, candidates):
            for support in supports:
                common = face.intersect(support)
                if common is not None:
                    total += (sum(part.area for part in common)
                              if isinstance(common, list) else common.area)
        return total
