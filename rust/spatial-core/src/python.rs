use std::panic::{catch_unwind, AssertUnwindSafe};

use pyo3::exceptions::{PyRuntimeError, PyValueError};
use pyo3::prelude::*;

use crate::{Bounds, MeshAudit, MeshLayout, SpatialError, API_VERSION};

fn result_to_python<T>(result: std::thread::Result<Result<T, SpatialError>>) -> PyResult<T> {
    match result {
        Ok(Ok(value)) => Ok(value),
        Ok(Err(error)) => Err(PyValueError::new_err(error.to_string())),
        Err(payload) => {
            let message = payload
                .downcast_ref::<String>()
                .map(String::as_str)
                .or_else(|| payload.downcast_ref::<&str>().copied())
                .unwrap_or("unknown Rust geometry panic");
            Err(PyRuntimeError::new_err(format!(
                "Rust spatial calculation failed: {message}"
            )))
        }
    }
}

#[pyfunction]
fn api_version() -> u32 {
    API_VERSION
}

#[pyfunction(name = "aabb_candidates")]
fn py_aabb_candidates(
    py: Python<'_>,
    bounds: Vec<Bounds>,
    queries: Vec<Bounds>,
    epsilon: f64,
) -> PyResult<Vec<Vec<usize>>> {
    result_to_python(py.detach(move || {
        catch_unwind(AssertUnwindSafe(|| {
            crate::aabb_candidates(&bounds, &queries, epsilon)
        }))
    }))
}

#[pyfunction(name = "aabb_contact_candidates")]
fn py_aabb_contact_candidates(
    py: Python<'_>,
    bounds: Vec<Bounds>,
    queries: Vec<Bounds>,
    tolerance: f64,
) -> PyResult<Vec<Vec<usize>>> {
    result_to_python(py.detach(move || {
        catch_unwind(AssertUnwindSafe(|| {
            crate::aabb_contact_candidates(&bounds, &queries, tolerance)
        }))
    }))
}

type SignedMeshLayout = ([i128; 3], Option<[i128; 4]>, Option<[i128; 3]>);

fn unsigned_descriptor<const N: usize>(
    descriptor: [i128; N],
    context: &str,
) -> Result<[usize; N], SpatialError> {
    let mut output = [0; N];
    for (i, value) in descriptor.into_iter().enumerate() {
        output[i] = usize::try_from(value).map_err(|_| {
            SpatialError(format!(
                "{context} field {i} must be a non-negative addressable integer"
            ))
        })?;
    }
    Ok(output)
}

#[pyfunction(name = "audit_triangle_meshes")]
fn py_audit_triangle_meshes(
    py: Python<'_>,
    binary: &[u8],
    layouts: Vec<SignedMeshLayout>,
) -> PyResult<Vec<MeshAudit>> {
    // &[u8] is extracted only from immutable Python bytes. Its owner remains
    // alive for this call, including while Python is detached from this thread.
    result_to_python(py.detach(move || {
        catch_unwind(AssertUnwindSafe(|| {
            let layouts: Vec<MeshLayout> = layouts
                .into_iter()
                .enumerate()
                .map(|(i, (position, index, normal))| {
                    Ok((
                        unsigned_descriptor(position, &format!("mesh {i} positions"))?,
                        index
                            .map(|descriptor| {
                                unsigned_descriptor(descriptor, &format!("mesh {i} indices"))
                            })
                            .transpose()?,
                        normal
                            .map(|descriptor| {
                                unsigned_descriptor(descriptor, &format!("mesh {i} normals"))
                            })
                            .transpose()?,
                    ))
                })
                .collect::<Result<_, SpatialError>>()?;
            crate::audit_triangle_meshes(binary, &layouts)
        }))
    }))
}

#[pymodule]
fn _spatial_native(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(api_version, module)?)?;
    module.add_function(wrap_pyfunction!(py_aabb_candidates, module)?)?;
    module.add_function(wrap_pyfunction!(py_aabb_contact_candidates, module)?)?;
    module.add_function(wrap_pyfunction!(py_audit_triangle_meshes, module)?)?;
    Ok(())
}
