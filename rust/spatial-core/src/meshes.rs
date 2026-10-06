//! Numeric audits for already-described GLB triangle buffer layouts.
//!
//! The GLB/JSON parser stays outside this module. Bytes remain immutable, and
//! vertex/index rows are read directly rather than allocating decoded meshes.

use crate::{Bounds, SpatialError};

/// Position (offset, stride, count), optional unsigned index descriptor
/// (offset, stride, count, component bytes), optional normal descriptor.
pub type MeshLayout = ([usize; 3], Option<[usize; 4]>, Option<[usize; 3]>);
/// Vertex count, index count, triangle count, optional normal count, XYZ bounds,
/// and count of degenerate triangles (a diagnostic rather than an error).
pub type MeshAudit = (usize, usize, usize, Option<usize>, Bounds, usize);

#[derive(Clone, Copy)]
struct Accessor {
    offset: usize,
    stride: usize,
    count: usize,
}

impl Accessor {
    fn checked(
        layout: [usize; 3],
        packed_width: usize,
        alignment: usize,
        binary_length: usize,
        context: &str,
    ) -> Result<Self, SpatialError> {
        let [offset, stride, count] = layout;
        if stride < packed_width {
            return Err(SpatialError(format!(
                "{context} stride {stride} is smaller than packed width {packed_width}"
            )));
        }
        if !offset.is_multiple_of(alignment) || !stride.is_multiple_of(alignment) {
            return Err(SpatialError(format!(
                "{context} offset and stride need {alignment}-byte alignment"
            )));
        }
        let end = if count == 0 {
            Some(offset)
        } else {
            (count - 1)
                .checked_mul(stride)
                .and_then(|span| offset.checked_add(span))
                .and_then(|last| last.checked_add(packed_width))
        }
        .ok_or_else(|| SpatialError(format!("{context} byte span overflows addressable memory")))?;
        if end > binary_length {
            return Err(SpatialError(format!(
                "{context} byte span ends at {end}, beyond binary length {binary_length}"
            )));
        }
        Ok(Self {
            offset,
            stride,
            count,
        })
    }

    fn vector(self, binary: &[u8], index: usize) -> [f64; 3] {
        let row = self.offset + index * self.stride;
        std::array::from_fn(|axis| {
            let at = row + axis * 4;
            f32::from_le_bytes([binary[at], binary[at + 1], binary[at + 2], binary[at + 3]]) as f64
        })
    }

    fn index(self, binary: &[u8], index: usize, component_bytes: usize) -> usize {
        let row = self.offset + index * self.stride;
        match component_bytes {
            1 => binary[row] as usize,
            2 => u16::from_le_bytes([binary[row], binary[row + 1]]) as usize,
            4 => u32::from_le_bytes([
                binary[row],
                binary[row + 1],
                binary[row + 2],
                binary[row + 3],
            ]) as usize,
            _ => unreachable!("component bytes were validated before decoding"),
        }
    }
}

/// Validate numeric triangle buffers and calculate their diagnostic counts.
/// Strides must include the complete packed row and meet component alignment.
/// All positions and supplied normals are finite; normals need not be unit
/// vectors. Repeated-index or exactly collinear triangles are counted, because
/// legitimate CAD tessellation can include them.
pub fn audit_triangle_meshes(
    binary: &[u8],
    layouts: &[MeshLayout],
) -> Result<Vec<MeshAudit>, SpatialError> {
    layouts
        .iter()
        .enumerate()
        .map(|(mesh, &(position_layout, index_layout, normal_layout))| {
            if position_layout[2] == 0 {
                return Err(SpatialError(format!(
                    "mesh {mesh} position count must be positive"
                )));
            }
            let position = Accessor::checked(
                position_layout,
                12,
                4,
                binary.len(),
                &format!("mesh {mesh} positions"),
            )?;
            let index = if let Some([offset, stride, count, component_bytes]) = index_layout {
                if ![1, 2, 4].contains(&component_bytes) {
                    return Err(SpatialError(format!(
                        "mesh {mesh} index component bytes must be 1, 2 or 4"
                    )));
                }
                if !count.is_multiple_of(3) {
                    return Err(SpatialError(format!(
                        "mesh {mesh} index count must be divisible by three"
                    )));
                }
                let accessor = Accessor::checked(
                    [offset, stride, count],
                    component_bytes,
                    component_bytes,
                    binary.len(),
                    &format!("mesh {mesh} indices"),
                )?;
                Some((accessor, component_bytes))
            } else {
                if !position.count.is_multiple_of(3) {
                    return Err(SpatialError(format!(
                        "mesh {mesh} non-indexed vertex count must be divisible by three"
                    )));
                }
                None
            };
            let normal = if let Some(layout) = normal_layout {
                if layout[2] != position.count {
                    return Err(SpatialError(format!(
                        "mesh {mesh} normal count must equal vertex count"
                    )));
                }
                Some(Accessor::checked(
                    layout,
                    12,
                    4,
                    binary.len(),
                    &format!("mesh {mesh} normals"),
                )?)
            } else {
                None
            };

            let mut bounds = [
                f64::INFINITY,
                f64::INFINITY,
                f64::INFINITY,
                f64::NEG_INFINITY,
                f64::NEG_INFINITY,
                f64::NEG_INFINITY,
            ];
            for vertex in 0..position.count {
                let point = position.vector(binary, vertex);
                if point.iter().any(|coordinate| !coordinate.is_finite()) {
                    return Err(SpatialError(format!(
                        "mesh {mesh} position {vertex} contains a nonfinite coordinate"
                    )));
                }
                for axis in 0..3 {
                    bounds[axis] = bounds[axis].min(point[axis]);
                    bounds[axis + 3] = bounds[axis + 3].max(point[axis]);
                }
                if let Some(normal) = normal {
                    if normal
                        .vector(binary, vertex)
                        .iter()
                        .any(|coordinate| !coordinate.is_finite())
                    {
                        return Err(SpatialError(format!(
                            "mesh {mesh} normal {vertex} contains a nonfinite coordinate"
                        )));
                    }
                }
            }
            let index_count = index.map_or(0, |(accessor, _)| accessor.count);
            // glTF 2.0 mesh indices cannot contain the component maximum,
            // which graphics APIs reserve for primitive restart. This remains
            // forbidden even when that number is below the vertex count.
            let restart_index = index.map(|(_, component_bytes)| match component_bytes {
                1 => u8::MAX as usize,
                2 => u16::MAX as usize,
                4 => u32::MAX as usize,
                _ => unreachable!("component bytes were validated before decoding"),
            });
            let element_count = index.map_or(position.count, |(accessor, _)| accessor.count);
            let mut degenerate_count = 0;
            for element in (0..element_count).step_by(3) {
                let mut vertex_indices = [0; 3];
                for (corner, vertex_index) in vertex_indices.iter_mut().enumerate() {
                    *vertex_index =
                        index.map_or(element + corner, |(accessor, component_bytes)| {
                            accessor.index(binary, element + corner, component_bytes)
                        });
                    if restart_index == Some(*vertex_index) {
                        return Err(SpatialError(format!(
                            "mesh {mesh} index {} uses reserved primitive restart value {}",
                            element + corner,
                            vertex_index
                        )));
                    }
                    if *vertex_index >= position.count {
                        return Err(SpatialError(format!(
                            "mesh {mesh} index {} references vertex {}, outside vertex count {}",
                            element + corner,
                            vertex_index,
                            position.count
                        )));
                    }
                }
                if vertex_indices[0] == vertex_indices[1]
                    || vertex_indices[1] == vertex_indices[2]
                    || vertex_indices[0] == vertex_indices[2]
                {
                    degenerate_count += 1;
                    continue;
                }
                let [a, b, c] = vertex_indices.map(|i| position.vector(binary, i));
                let u: [f64; 3] = std::array::from_fn(|axis| b[axis] - a[axis]);
                let v: [f64; 3] = std::array::from_fn(|axis| c[axis] - a[axis]);
                let cross = [
                    u[1] * v[2] - u[2] * v[1],
                    u[2] * v[0] - u[0] * v[2],
                    u[0] * v[1] - u[1] * v[0],
                ];
                if cross.iter().all(|&coordinate| coordinate == 0.0) {
                    degenerate_count += 1;
                }
            }
            Ok((
                position.count,
                index_count,
                element_count / 3,
                normal.map(|accessor| accessor.count),
                bounds,
                degenerate_count,
            ))
        })
        .collect()
}
