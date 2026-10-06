#[cfg(feature = "python")]
fn main() {
    // CPython resolves these symbols when loading the extension. In
    // particular, macOS needs the linker to permit that dynamic lookup.
    pyo3_build_config::add_extension_module_link_args();
}

#[cfg(not(feature = "python"))]
fn main() {}
