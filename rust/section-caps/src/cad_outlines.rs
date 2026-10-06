//! CAD outline intervals, matching `web/src/cad-outlines.ts`.
//!
//! Opposite coplanar triangle edges cancel even when one face splits the edge
//! into several shorter intervals. The coordinate-relative tolerance follows
//! Float32 mesh precision; same-directed duplicate borders and sharp creases
//! remain visible. All intermediate operations use f64 and preserve input
//! traversal order; only the returned Three.js endpoints are converted to f32.

use std::cmp::Ordering;
use wasm_bindgen::prelude::*;

#[derive(Clone, Copy, Debug, Default)]
struct Vector([f64; 3]);

impl Vector {
    fn sub(self, other: Self) -> Self {
        Self(std::array::from_fn(|i| self.0[i] - other.0[i]))
    }

    fn dot(self, other: Self) -> f64 {
        self.0[0] * other.0[0] + self.0[1] * other.0[1] + self.0[2] * other.0[2]
    }

    fn cross(self, other: Self) -> Self {
        let [x, y, z] = self.0;
        let [ox, oy, oz] = other.0;
        Self([y * oz - z * oy, z * ox - x * oz, x * oy - y * ox])
    }

    fn length_squared(self) -> f64 {
        self.dot(self)
    }

    fn scale(self, factor: f64) -> Self {
        Self(self.0.map(|value| value * factor))
    }

    fn triangle_normal(a: Self, b: Self, c: Self) -> Self {
        // Use Three.js Triangle.getNormal's exact subtraction/cross order.
        let normal = c.sub(b).cross(a.sub(b));
        let length_squared = normal.length_squared();
        if length_squared > 0.0 {
            normal.scale(1.0 / length_squared.sqrt())
        } else {
            Self::default()
        }
    }

    fn is_valid_vertex(self) -> bool {
        (self.0[0] + self.0[1] + self.0[2]).is_finite()
    }
}

struct Interval {
    start: f64,
    end: f64,
    forward: bool,
    normal: Vector,
}

struct Line {
    origin: Vector,
    direction: Vector,
    intervals: Vec<Interval>,
}

impl Line {
    fn contains(&self, point: Vector, tolerance_squared: f64) -> bool {
        point
            .sub(self.origin)
            .cross(self.direction)
            .length_squared()
            <= tolerance_squared
    }

    fn emit(&self, start: f64, end: f64, output: &mut Vec<f32>) {
        for distance in [start, end] {
            for i in 0..3 {
                output.push((self.direction.0[i] * distance + self.origin.0[i]) as f32);
            }
        }
    }
}

/// Flattened mesh-local XYZ positions, optional triangle indices (empty means
/// non-indexed), and crease threshold in degrees. Returns flattened XYZ line
/// endpoints in input traversal order. Incomplete or invalid triangles are
/// skipped, preserving valid borders elsewhere in the mesh.
#[wasm_bindgen]
pub fn cad_outline(positions: &[f64], indices: &[u32], threshold_angle: f64) -> Vec<f32> {
    let vertex_count = positions.len() / 3;
    let count = if indices.is_empty() {
        vertex_count
    } else {
        indices.len()
    };
    let coordinate_scale = positions
        .chunks_exact(3)
        .flatten()
        .filter(|value| value.is_finite())
        .fold(1.0_f64, |scale, value| scale.max(value.abs()));
    let tolerance = coordinate_scale * 1e-7;
    let tolerance_squared = tolerance * tolerance;
    let threshold_dot = (threshold_angle * std::f64::consts::PI / 180.0).cos();
    let mut lines: Vec<Line> = Vec::new();

    let vertex_at = |offset: usize| -> Option<Vector> {
        let index = if indices.is_empty() {
            offset
        } else {
            indices[offset] as usize
        };
        if index >= vertex_count {
            return None;
        }
        Some(Vector([
            positions[index * 3],
            positions[index * 3 + 1],
            positions[index * 3 + 2],
        ]))
    };

    for i in (0..count.saturating_sub(2)).step_by(3) {
        let (Some(a), Some(b), Some(c)) = (vertex_at(i), vertex_at(i + 1), vertex_at(i + 2)) else {
            continue;
        };
        let vertices = [a, b, c];
        if !vertices.iter().all(|vertex| vertex.is_valid_vertex()) {
            continue;
        }
        let normal = Vector::triangle_normal(a, b, c);
        if normal.length_squared() == 0.0 {
            continue;
        }
        for j in 0..3 {
            let start = vertices[j];
            let end = vertices[(j + 1) % 3];
            let delta = end.sub(start);
            let length_squared = delta.length_squared();
            if length_squared <= tolerance_squared {
                continue;
            }
            let direction = delta.scale(1.0 / length_squared.sqrt());
            let matching = lines.iter().position(|line| {
                direction.cross(line.direction).length_squared() <= 1e-12
                    && line.contains(start, tolerance_squared)
                    && line.contains(end, tolerance_squared)
            });
            let line_index = matching.unwrap_or_else(|| {
                lines.push(Line {
                    origin: start,
                    direction,
                    intervals: Vec::new(),
                });
                lines.len() - 1
            });
            let line = &mut lines[line_index];
            let t0 = start.sub(line.origin).dot(line.direction);
            let t1 = end.sub(line.origin).dot(line.direction);
            line.intervals.push(Interval {
                start: t0.min(t1),
                end: t0.max(t1),
                forward: t1 > t0,
                normal,
            });
        }
    }

    let mut output = Vec::new();
    for line in lines {
        let mut endpoints: Vec<_> = line
            .intervals
            .iter()
            .flat_map(|interval| [interval.start, interval.end])
            .collect();
        endpoints.sort_by(|a, b| a.partial_cmp(b).unwrap_or(Ordering::Equal));
        let mut breaks = Vec::new();
        for endpoint in endpoints {
            if breaks.last().is_none_or(|last| endpoint - last > tolerance) {
                breaks.push(endpoint);
            }
        }
        let mut visible_start = None;
        for pair in breaks.windows(2) {
            let [start, end] = [pair[0], pair[1]];
            let midpoint = (start + end) / 2.0;
            let active: Vec<_> = line
                .intervals
                .iter()
                .filter(|interval| interval.start < midpoint && interval.end > midpoint)
                .collect();
            let shared = active.iter().any(|interval| interval.forward)
                && active.iter().any(|interval| !interval.forward);
            let visible = !active.is_empty()
                && (!shared
                    || active.iter().enumerate().any(|(j, a)| {
                        active[j + 1..]
                            .iter()
                            .any(|b| a.normal.dot(b.normal) <= threshold_dot)
                    }));
            if visible && visible_start.is_none() {
                visible_start = Some(start);
            }
            if !visible {
                if let Some(first) = visible_start.take() {
                    line.emit(first, start, &mut output);
                }
            }
        }
        if let (Some(first), Some(last)) = (visible_start, breaks.last()) {
            line.emit(first, *last, &mut output);
        }
    }
    output
}

#[cfg(test)]
mod tests {
    use super::*;

    const UPPER: [[f64; 3]; 3] = [[0.0, 0.0, 0.0], [4.0, 0.0, 0.0], [0.0, 2.0, 0.0]];
    const LOWER: [[[f64; 3]; 3]; 2] = [
        [[2.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, -2.0, 0.0]],
        [[4.0, 0.0, 0.0], [2.0, 0.0, 0.0], [4.0, -2.0, 0.0]],
    ];

    fn outline(triangles: &[[[f64; 3]; 3]], indexed: bool, threshold: f64) -> Vec<f32> {
        let positions: Vec<_> = triangles.iter().flatten().flatten().copied().collect();
        let indices: Vec<_> = if indexed {
            (0..positions.len() as u32 / 3).collect()
        } else {
            Vec::new()
        };
        cad_outline(&positions, &indices, threshold)
    }

    fn covers(output: &[f32], point: [f64; 3], tolerance: f64) -> bool {
        let point = Vector(point);
        output.chunks_exact(6).any(|segment| {
            let a = Vector(std::array::from_fn(|i| segment[i] as f64));
            let b = Vector(std::array::from_fn(|i| segment[i + 3] as f64));
            let delta = b.sub(a);
            let t = point.sub(a).dot(delta) / delta.length_squared();
            let nearest = Vector(std::array::from_fn(|i| a.0[i] + delta.0[i] * t));
            t >= -tolerance
                && t <= 1.0 + tolerance
                && nearest.sub(point).length_squared() <= tolerance * tolerance
        })
    }

    #[test]
    fn split_coplanar_edges_cancel_and_perimeters_survive() {
        for indexed in [false, true] {
            let output = outline(&[UPPER, LOWER[0], LOWER[1]], indexed, 28.0);
            for x in [0.5, 1.5, 2.5, 3.5] {
                assert!(!covers(&output, [x, 0.0, 0.0], 1e-6));
            }
            assert!(covers(&output, [0.0, 1.0, 0.0], 1e-6));
            assert!(covers(&output, [2.0, 1.0, 0.0], 1e-6));
        }
    }

    #[test]
    fn only_partial_shared_interval_disappears() {
        let output = outline(
            &[UPPER, [[3.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, -2.0, 0.0]]],
            false,
            28.0,
        );
        assert!(covers(&output, [0.5, 0.0, 0.0], 1e-6));
        assert!(!covers(&output, [2.0, 0.0, 0.0], 1e-6));
        assert!(covers(&output, [3.5, 0.0, 0.0], 1e-6));
    }

    #[test]
    fn sharp_creases_use_signed_normals_and_configured_threshold() {
        let folded = [UPPER, [[4.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 2.0]]];
        assert!(covers(
            &outline(&folded, false, 28.0),
            [2.0, 0.0, 0.0],
            1e-6
        ));
        assert!(!covers(
            &outline(&folded, false, 91.0),
            [2.0, 0.0, 0.0],
            1e-6
        ));
        let opposite = [UPPER, [UPPER[2], UPPER[1], UPPER[0]]];
        assert!(covers(
            &outline(&opposite, false, 28.0),
            [2.0, 0.0, 0.0],
            1e-6
        ));
    }

    #[test]
    fn nearby_distinct_and_slightly_angled_borders_remain_separate() {
        for (left_y, right_y) in [(0.00002, 0.00002), (0.00001, 0.00003)] {
            let output = outline(
                &[
                    UPPER,
                    [[3.0, right_y, 0.0], [1.0, left_y, 0.0], [1.0, -2.0, 0.0]],
                ],
                false,
                28.0,
            );
            assert!(covers(&output, [2.0, 0.0, 0.0], 1e-8));
            assert!(covers(&output, [2.0, (left_y + right_y) / 2.0, 0.0], 1e-8));
        }
    }

    #[test]
    fn duplicate_degenerate_and_invalid_faces_do_not_consume_borders() {
        let invalid = [[f64::NAN, 0.0, 0.0], [1.0, 0.0, 0.0], [2.0, 0.0, 0.0]];
        let degenerate = [[0.0, 0.0, 0.0], [2.0, 0.0, 0.0], [4.0, 0.0, 0.0]];
        let output = outline(&[UPPER, UPPER, degenerate, invalid], false, 28.0);
        assert!(covers(&output, [2.0, 0.0, 0.0], 1e-6));
        assert!(output.iter().all(|value| value.is_finite()));
        let positions: Vec<_> = UPPER.into_iter().flatten().collect();
        assert_eq!(
            cad_outline(&positions, &[0, 1, 2, 0, u32::MAX, 2], 28.0),
            cad_outline(&positions, &[], 28.0)
        );
        assert!(cad_outline(&[], &[], 28.0).is_empty());
    }

    #[test]
    fn coplanar_pairs_with_a_third_creased_face_remain_visible() {
        let output = outline(
            &[
                UPPER,
                LOWER[0],
                LOWER[1],
                [[4.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 2.0]],
            ],
            false,
            28.0,
        );
        assert!(covers(&output, [2.0, 0.0, 0.0], 1e-6));
    }
}
