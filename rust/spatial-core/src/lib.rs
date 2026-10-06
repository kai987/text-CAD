//! Pure numeric indexed bounding-box candidate queries and triangle audits.
//!
//! These routines screen potential overlaps; exact polygon metrics remain in
//! GEOS and solid intersections remain in the CAD BRep kernel. They do not
//! infer structural capacity.
//! The optional `python` feature exposes the same operations to CPython while
//! releasing the interpreter during Rust calculations.

mod aabb;
mod meshes;

#[cfg(feature = "python")]
mod python;

pub use aabb::{aabb_candidates, aabb_contact_candidates, bounds_contact, bounds_overlap, Bounds};
pub use meshes::{audit_triangle_meshes, MeshAudit, MeshLayout};

use std::fmt;

pub const API_VERSION: u32 = 3;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SpatialError(pub String);

impl fmt::Display for SpatialError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(f)
    }
}

impl std::error::Error for SpatialError {}
