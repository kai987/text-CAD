use text_cad_spatial_core::{audit_triangle_meshes, MeshLayout};

const TRIANGLE: [[f32; 3]; 3] = [[0.0, 0.0, 0.0], [2.0, 0.0, 0.0], [0.0, 3.0, 0.0]];

fn vectors(points: &[[f32; 3]]) -> Vec<u8> {
    points
        .iter()
        .flatten()
        .flat_map(|value| value.to_le_bytes())
        .collect()
}

fn put_indices(binary: &mut Vec<u8>, values: &[u32], component_bytes: usize) {
    for &value in values {
        binary.extend_from_slice(&value.to_le_bytes()[..component_bytes]);
    }
}

fn rejects(binary: &[u8], layout: MeshLayout, phrase: &str) {
    let error = audit_triangle_meshes(binary, &[layout]).unwrap_err();
    assert!(
        error.0.contains(phrase),
        "{} does not contain {phrase}",
        error.0
    );
}

#[test]
fn nonindexed_triangle_stats_and_bounds_are_read_without_changing_bytes() {
    let binary = vectors(&TRIANGLE);
    let before = binary.clone();
    let result = audit_triangle_meshes(&binary, &[([0, 12, 3], None, None)]).unwrap();
    assert_eq!(result, [(3, 0, 1, None, [0.0, 0.0, 0.0, 2.0, 3.0, 0.0], 0)]);
    assert_eq!(binary, before);
    assert!(audit_triangle_meshes(&[], &[]).unwrap().is_empty());
}

#[test]
fn indexed_unsigned_byte_short_and_int_triangles_have_identical_diagnostics() {
    let points = [
        [0.0, 0.0, 0.0],
        [2.0, 0.0, 0.0],
        [2.0, 3.0, 0.0],
        [0.0, 3.0, 0.0],
    ];
    for component_bytes in [1, 2, 4] {
        let mut binary = vectors(&points);
        put_indices(&mut binary, &[0, 1, 2, 0, 2, 3], component_bytes);
        let layout = (
            [0, 12, 4],
            Some([48, component_bytes, 6, component_bytes]),
            None,
        );
        assert_eq!(
            audit_triangle_meshes(&binary, &[layout]).unwrap(),
            [(4, 6, 2, None, [0.0, 0.0, 0.0, 2.0, 3.0, 0.0], 0)]
        );
    }
}

#[test]
fn interleaved_position_normal_and_padded_index_rows_are_supported() {
    let mut binary = vec![0; 4];
    for point in TRIANGLE {
        let mut row = vec![0; 32];
        row[..12].copy_from_slice(&vectors(&[point]));
        row[12..24].copy_from_slice(&vectors(&[[0.0, 0.0, 0.0]]));
        binary.extend(row);
    }
    for value in [0_u16, 1, 2] {
        binary.extend_from_slice(&value.to_le_bytes());
        binary.extend_from_slice(&[0, 0]);
    }
    let layout = ([4, 32, 3], Some([100, 4, 3, 2]), Some([16, 32, 3]));
    assert_eq!(
        audit_triangle_meshes(&binary, &[layout, layout]).unwrap(),
        vec![(3, 3, 1, Some(3), [0.0, 0.0, 0.0, 2.0, 3.0, 0.0], 0); 2]
    );
}

#[test]
fn repeated_indices_collinear_points_and_duplicate_positions_are_diagnostics() {
    let mut binary = vectors(&TRIANGLE);
    put_indices(&mut binary, &[0, 0, 2, 0, 1, 2], 1);
    let result =
        audit_triangle_meshes(&binary, &[([0, 12, 3], Some([36, 1, 6, 1]), None)]).unwrap();
    assert_eq!(result[0].5, 1);
    for points in [
        [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [2.0, 2.0, 2.0]],
        [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [1.0, 1.0, 1.0]],
    ] {
        assert_eq!(
            audit_triangle_meshes(&vectors(&points), &[([0, 12, 3], None, None)]).unwrap()[0].5,
            1
        );
    }
    let subnormal = [
        [0.0, 0.0, 0.0],
        [f32::from_bits(1), 0.0, 0.0],
        [0.0, f32::from_bits(1), 0.0],
    ];
    assert_eq!(
        audit_triangle_meshes(&vectors(&subnormal), &[([0, 12, 3], None, None)]).unwrap()[0].5,
        0,
        "Float32 subnormals remain nonzero when cross products use Float64"
    );
}

#[test]
fn invalid_position_shapes_alignment_truncation_and_overflow_are_rejected() {
    let binary = vectors(&TRIANGLE);
    rejects(&binary, ([0, 12, 0], None, None), "count must be positive");
    rejects(&binary, ([0, 12, 2], None, None), "divisible by three");
    rejects(&binary, ([0, 0, 3], None, None), "stride");
    rejects(&binary, ([2, 12, 3], None, None), "alignment");
    rejects(&binary, ([0, 14, 3], None, None), "alignment");
    rejects(
        &binary[..35],
        ([0, 12, 3], None, None),
        "beyond binary length",
    );
    rejects(&binary, ([usize::MAX - 3, 12, 3], None, None), "overflows");
    rejects(&binary, ([0, 12, usize::MAX], None, None), "overflows");
    rejects(&binary, ([0, usize::MAX - 3, 3], None, None), "overflows");
}

#[test]
fn malformed_index_types_counts_bounds_and_truncation_are_rejected() {
    let mut binary = vectors(&TRIANGLE);
    put_indices(&mut binary, &[0, 1, 3], 4);
    rejects(
        &binary,
        ([0, 12, 3], Some([36, 3, 3, 3]), None),
        "component bytes",
    );
    rejects(
        &binary,
        ([0, 12, 3], Some([36, 4, 2, 4]), None),
        "divisible by three",
    );
    rejects(
        &binary,
        ([0, 12, 3], Some([36, 4, 3, 4]), None),
        "outside vertex count",
    );
    rejects(
        &binary,
        ([0, 12, 3], Some([37, 4, 3, 4]), None),
        "alignment",
    );
    rejects(
        &binary[..47],
        ([0, 12, 3], Some([36, 4, 3, 4]), None),
        "beyond binary length",
    );
    let result =
        audit_triangle_meshes(&binary, &[([0, 12, 3], Some([36, 4, 0, 4]), None)]).unwrap();
    assert_eq!(
        result[0].2, 0,
        "explicit empty indices describe zero triangles"
    );
}

#[test]
fn reserved_primitive_restart_indices_are_rejected_even_with_enough_vertices() {
    let mut binary = vectors(&[[0.0, 0.0, 0.0]; 256]);
    put_indices(&mut binary, &[0, 1, 255], 1);
    rejects(
        &binary,
        ([0, 12, 256], Some([256 * 12, 1, 3, 1]), None),
        "reserved primitive restart value 255",
    );
    // The maximum valid uint8 index still works when extra vertices exist.
    *binary.last_mut().unwrap() = 254;
    assert_eq!(
        audit_triangle_meshes(&binary, &[([0, 12, 256], Some([256 * 12, 1, 3, 1]), None)]).unwrap()
            [0]
        .5,
        1,
    );
    for (component_bytes, maximum) in [(2, u16::MAX as u32), (4, u32::MAX)] {
        let mut binary = vectors(&TRIANGLE);
        put_indices(&mut binary, &[0, 1, maximum], component_bytes);
        rejects(
            &binary,
            (
                [0, 12, 3],
                Some([36, component_bytes, 3, component_bytes]),
                None,
            ),
            &format!("reserved primitive restart value {maximum}"),
        );
    }
}

#[test]
fn nonfinite_positions_and_normals_reject_the_complete_batch() {
    for invalid in [f32::NAN, f32::INFINITY, f32::NEG_INFINITY] {
        let mut points = TRIANGLE;
        points[1][2] = invalid;
        rejects(&vectors(&points), ([0, 12, 3], None, None), "position 1");
        let mut binary = vectors(&TRIANGLE);
        let normals = [[0.0, 0.0, 1.0], [0.0, invalid, 1.0], [0.0, 0.0, 1.0]];
        binary.extend(vectors(&normals));
        rejects(&binary, ([0, 12, 3], None, Some([36, 12, 3])), "normal 1");
    }
    let mut binary = vectors(&TRIANGLE);
    binary.extend(vectors(&[[0.0, 0.0, 0.0]; 3]));
    rejects(
        &binary,
        ([0, 12, 3], None, Some([36, 12, 2])),
        "normal count",
    );
    rejects(
        &binary[..71],
        ([0, 12, 3], None, Some([36, 12, 3])),
        "beyond binary length",
    );
    assert_eq!(
        audit_triangle_meshes(&binary, &[([0, 12, 3], None, Some([36, 12, 3]))]).unwrap()[0].3,
        Some(3),
        "finite zero normals are allowed"
    );
}
