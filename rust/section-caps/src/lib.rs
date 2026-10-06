//! Horizontal world-space caps for closed, manifold triangle meshes.
//!
//! The numerical behavior follows `web/src/section-caps.ts`: GLB coordinates
//! are metres, tessellation seams weld within two micrometres, and cuts at
//! vertex levels sample the retained lower side. Calculations use f64; the
//! packed result is f32, matching Three.js BufferGeometry attributes.

use std::collections::HashMap;
use wasm_bindgen::prelude::*;

mod cad_outlines;
pub use cad_outlines::cad_outline;

const WELD: f64 = 2e-6;
const AREA_EPSILON: f64 = WELD * WELD;

#[derive(Clone, Copy, Debug)]
struct Point {
    x: f64,
    z: f64,
}

#[derive(Clone, Copy)]
struct Vertex {
    x: f64,
    y: f64,
    z: f64,
}

struct Transform {
    matrix: [f64; 16],
    inverse: [[f64; 3]; 3],
    normal: [f64; 3],
}

impl Transform {
    fn new(matrix: &[f64]) -> Option<Self> {
        let matrix: [f64; 16] = matrix.try_into().ok()?;
        if !matrix.iter().all(|value| value.is_finite())
            || matrix[3] != 0.0
            || matrix[7] != 0.0
            || matrix[11] != 0.0
            || matrix[15] != 1.0
        {
            return None;
        }
        // Column-major Three.js matrix, written here as the 3x3 linear part.
        let [a, b, c] = [matrix[0], matrix[4], matrix[8]];
        let [d, e, f] = [matrix[1], matrix[5], matrix[9]];
        let [g, h, i] = [matrix[2], matrix[6], matrix[10]];
        let determinant = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g);
        if determinant == 0.0 || !determinant.is_finite() {
            return None;
        }
        let inverse = [
            [
                (e * i - f * h) / determinant,
                (c * h - b * i) / determinant,
                (b * f - c * e) / determinant,
            ],
            [
                (f * g - d * i) / determinant,
                (a * i - c * g) / determinant,
                (c * d - a * f) / determinant,
            ],
            [
                (d * h - e * g) / determinant,
                (b * g - a * h) / determinant,
                (a * e - b * d) / determinant,
            ],
        ];
        if !inverse.iter().flatten().all(|value| value.is_finite()) {
            return None;
        }
        // Local normal = A^T * world-up. The rendering normal matrix A^-T
        // consequently returns world-up, even with shear or a reflection.
        let normal_length = d.hypot(e).hypot(f);
        if normal_length == 0.0 || !normal_length.is_finite() {
            return None;
        }
        Some(Self {
            matrix,
            inverse,
            normal: [d / normal_length, e / normal_length, f / normal_length],
        })
    }

    fn world(&self, local: &[f64]) -> Option<Vertex> {
        let m = self.matrix;
        let point = Vertex {
            x: m[0] * local[0] + m[4] * local[1] + m[8] * local[2] + m[12],
            y: m[1] * local[0] + m[5] * local[1] + m[9] * local[2] + m[13],
            z: m[2] * local[0] + m[6] * local[1] + m[10] * local[2] + m[14],
        };
        (point.x.is_finite() && point.y.is_finite() && point.z.is_finite()).then_some(point)
    }

    fn local(&self, point: Point, height: f64) -> Option<[f32; 3]> {
        let translated = [
            point.x - self.matrix[12],
            height - self.matrix[13],
            point.z - self.matrix[14],
        ];
        let mut local = [0.0; 3];
        for (row, output) in self.inverse.iter().zip(local.iter_mut()) {
            let value = row[0] * translated[0] + row[1] * translated[1] + row[2] * translated[2];
            if !value.is_finite() || value.abs() > f32::MAX as f64 {
                return None;
            }
            *output = value as f32;
        }
        Some(local)
    }
}

fn area(points: &[Point]) -> f64 {
    points
        .iter()
        .zip(points.iter().cycle().skip(1))
        .take(points.len())
        .map(|(point, next)| point.x * next.z - next.x * point.z)
        .sum::<f64>()
        / 2.0
}

fn contains(point: Point, polygon: &[Point]) -> bool {
    let mut inside = false;
    let mut previous = polygon.len() - 1;
    for (index, a) in polygon.iter().enumerate() {
        let b = polygon[previous];
        if (a.z > point.z) != (b.z > point.z)
            && point.x < (b.x - a.x) * (point.z - a.z) / (b.z - a.z) + a.x
        {
            inside = !inside;
        }
        previous = index;
    }
    inside
}

fn simplify(mut points: Vec<Point>) -> Vec<Point> {
    while points.len() > 3 {
        let mut changed = false;
        let next: Vec<_> = points
            .iter()
            .enumerate()
            .filter_map(|(index, &b)| {
                let a = points[(index + points.len() - 1) % points.len()];
                let c = points[(index + 1) % points.len()];
                let length = (c.x - a.x).hypot(c.z - a.z);
                let cross = (b.x - a.x) * (c.z - a.z) - (b.z - a.z) * (c.x - a.x);
                let between = (b.x - a.x) * (b.x - c.x) + (b.z - a.z) * (b.z - c.z) <= AREA_EPSILON;
                if length > WELD && cross.abs() <= WELD * length && between {
                    changed = true;
                    None
                } else {
                    Some(b)
                }
            })
            .collect();
        // Retain the prior loop rather than creating a degenerate polygon.
        if !changed || next.len() < 3 {
            break;
        }
        points = next;
    }
    points
}

fn bucket_key(x: f64, z: f64) -> (u64, u64) {
    // Floored f64 values avoid integer-cast overflow for large translations.
    // Normalize negative zero so neighbouring zero buckets share one key.
    (
        (if x == 0.0 { 0.0 } else { x }).to_bits(),
        (if z == 0.0 { 0.0 } else { z }).to_bits(),
    )
}

fn weld(
    point: Point,
    points: &mut Vec<Point>,
    buckets: &mut HashMap<(u64, u64), Vec<usize>>,
) -> Option<usize> {
    let x = (point.x / WELD).floor();
    let z = (point.z / WELD).floor();
    if !x.is_finite() || !z.is_finite() {
        return None;
    }
    // Preserve the TypeScript bucket and insertion search order. HashMap
    // iteration never determines contour or triangulation ordering.
    for dx in -1..=1 {
        for dz in -1..=1 {
            if let Some(indices) = buckets.get(&bucket_key(x + dx as f64, z + dz as f64)) {
                for &index in indices {
                    if (points[index].x - point.x).hypot(points[index].z - point.z) <= WELD {
                        return Some(index);
                    }
                }
            }
        }
    }
    let index = points.len();
    points.push(point);
    buckets.entry(bucket_key(x, z)).or_default().push(index);
    Some(index)
}

fn add_edge(a: usize, b: usize, neighbors: &mut Vec<Vec<usize>>, insertion_order: &mut Vec<usize>) {
    if neighbors.len() <= a.max(b) {
        neighbors.resize_with(a.max(b) + 1, Vec::new);
    }
    for (from, to) in [(a, b), (b, a)] {
        if neighbors[from].is_empty() {
            insertion_order.push(from);
        }
        if !neighbors[from].contains(&to) {
            neighbors[from].push(to);
        }
    }
}

fn depth(index: usize, parents: &[Option<usize>]) -> Option<usize> {
    let mut current = index;
    let mut depth = 0;
    while let Some(parent) = parents[current] {
        depth += 1;
        if depth >= parents.len() {
            return None;
        }
        current = parent;
    }
    Some(depth)
}

/// The WASM/native entry point. `positions` are flattened mesh-local XYZ;
/// `indices` are triangle indices (empty means non-indexed triangles), and
/// `matrix` is a nonsingular, column-major affine world transform.
///
/// The returned array contains all XYZ positions followed by all XYZ normals
/// (equal-size halves, total length = 6 * vertex count). An empty array means
/// there is no cap, or the input is invalid/open/non-manifold. No JavaScript
/// objects, renderer state, network requests, or global geometry caches are used.
#[wasm_bindgen]
pub fn section_cap(
    positions: &[f64],
    indices: &[u32],
    matrix: &[f64],
    world_height: f64,
) -> Vec<f32> {
    create_section_cap(positions, indices, matrix, world_height).unwrap_or_default()
}

fn create_section_cap(
    positions: &[f64],
    indices: &[u32],
    matrix: &[f64],
    world_height: f64,
) -> Option<Vec<f32>> {
    if !world_height.is_finite()
        || positions.len() < 9
        || !positions.len().is_multiple_of(3)
        || !positions.iter().all(|value| value.is_finite())
        || (!indices.is_empty() && !indices.len().is_multiple_of(3))
        || (indices.is_empty() && !positions.len().is_multiple_of(9))
    {
        return None;
    }
    let transform = Transform::new(matrix)?;
    let vertices: Vec<_> = positions
        .chunks_exact(3)
        .map(|point| transform.world(point))
        .collect::<Option<_>>()?;
    if indices
        .iter()
        .any(|&index| index as usize >= vertices.len())
    {
        return None;
    }
    let min_y = vertices
        .iter()
        .map(|point| point.y)
        .fold(f64::INFINITY, f64::min);
    let max_y = vertices
        .iter()
        .map(|point| point.y)
        .fold(f64::NEG_INFINITY, f64::max);
    if world_height <= min_y + WELD || world_height >= max_y - WELD {
        return None;
    }
    let sample_height = world_height - WELD * 4.0;
    let mut points = Vec::new();
    let mut buckets = HashMap::new();
    let mut neighbors = Vec::new();
    let mut insertion_order = Vec::new();
    let count = if indices.is_empty() {
        vertices.len()
    } else {
        indices.len()
    };
    for start in (0..count).step_by(3) {
        let triangle: [Vertex; 3] = std::array::from_fn(|offset| {
            vertices[if indices.is_empty() {
                start + offset
            } else {
                indices[start + offset] as usize
            }]
        });
        let mut intersections = Vec::with_capacity(2);
        for edge in 0..3 {
            let a = triangle[edge];
            let b = triangle[(edge + 1) % 3];
            let da = a.y - sample_height;
            let db = b.y - sample_height;
            if (da > 0.0) == (db > 0.0) {
                continue;
            }
            let t = da / (da - db);
            let point = Point {
                x: a.x + (b.x - a.x) * t,
                z: a.z + (b.z - a.z) * t,
            };
            if !point.x.is_finite() || !point.z.is_finite() {
                return None;
            }
            intersections.push(point);
        }
        if intersections.len() != 2 {
            continue;
        }
        let a = weld(intersections[0], &mut points, &mut buckets)?;
        let b = weld(intersections[1], &mut points, &mut buckets)?;
        if a != b {
            add_edge(a, b, &mut neighbors, &mut insertion_order);
        }
    }
    if insertion_order.is_empty()
        || insertion_order
            .iter()
            .any(|&index| neighbors[index].len() != 2)
    {
        return None;
    }
    let mut visited = vec![false; points.len()];
    let mut loops = Vec::new();
    for start in insertion_order {
        if visited[start] {
            continue;
        }
        let mut polygon = Vec::new();
        let mut previous = None;
        let mut current = start;
        loop {
            if visited[current] {
                return None;
            }
            visited[current] = true;
            polygon.push(points[current]);
            let next = neighbors[current]
                .iter()
                .copied()
                .find(|&neighbor| Some(neighbor) != previous)?;
            previous = Some(current);
            current = next;
            if current == start {
                break;
            }
        }
        let polygon = simplify(polygon);
        let polygon_area = area(&polygon).abs();
        if !polygon_area.is_finite() {
            return None;
        }
        if polygon.len() >= 3 && polygon_area > AREA_EPSILON {
            loops.push(polygon);
        }
    }
    if loops.is_empty() {
        return None;
    }
    let areas: Vec<_> = loops.iter().map(|polygon| area(polygon).abs()).collect();
    let parents: Vec<_> = loops
        .iter()
        .enumerate()
        .map(|(index, polygon)| {
            let mut parent = None;
            for (candidate, enclosing) in loops.iter().enumerate() {
                if areas[candidate] > areas[index]
                    && contains(polygon[0], enclosing)
                    && parent.is_none_or(|parent| areas[candidate] < areas[parent])
                {
                    parent = Some(candidate);
                }
            }
            parent
        })
        .collect();
    let mut output = Vec::new();
    for (index, polygon) in loops.iter().enumerate() {
        if depth(index, &parents)? % 2 != 0 {
            continue;
        }
        let holes: Vec<_> = loops
            .iter()
            .enumerate()
            .filter_map(|(hole_index, polygon)| {
                (parents[hole_index] == Some(index)).then_some(polygon)
            })
            .collect();
        let mut flat = polygon.clone();
        let mut hole_indices = Vec::with_capacity(holes.len());
        for hole in holes {
            hole_indices.push(flat.len());
            flat.extend_from_slice(hole);
        }
        let coordinates: Vec<_> = flat.iter().flat_map(|point| [point.x, point.z]).collect();
        let triangles = earcutr::earcut(&coordinates, &hole_indices, 2).ok()?;
        if !triangles.len().is_multiple_of(3) {
            return None;
        }
        for triangle in triangles.chunks_exact(3) {
            let [a, b, c] = [
                *flat.get(triangle[0])?,
                *flat.get(triangle[1])?,
                *flat.get(triangle[2])?,
            ];
            let signed = (b.x - a.x) * (c.z - a.z) - (b.z - a.z) * (c.x - a.x);
            if !signed.is_finite() {
                return None;
            }
            if signed.abs() <= AREA_EPSILON {
                continue;
            }
            // The renderer uses f32 local positions. A thin f64 ear can
            // collapse or reverse after this conversion, so its final winding
            // must be measured from those actual positions in world space.
            let mut local = [
                transform.local(a, world_height)?,
                transform.local(b, world_height)?,
                transform.local(c, world_height)?,
            ];
            let [pa, pb, pc] = [
                transform.world(&local[0].map(f64::from))?,
                transform.world(&local[1].map(f64::from))?,
                transform.world(&local[2].map(f64::from))?,
            ];
            let cross_y = (pb.z - pa.z) * (pc.x - pa.x) - (pb.x - pa.x) * (pc.z - pa.z);
            if !cross_y.is_finite() {
                return None;
            }
            if cross_y == 0.0 {
                continue;
            }
            if cross_y < 0.0 {
                local.swap(1, 2);
            }
            output.extend(local.into_iter().flatten());
        }
    }
    if output.is_empty() {
        return None;
    }
    let position_length = output.len();
    output.reserve(position_length);
    for _ in 0..position_length / 3 {
        output.extend(transform.normal.map(|value| value as f32));
    }
    Some(output)
}
