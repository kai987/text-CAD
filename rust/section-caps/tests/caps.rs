use text_cad_section_caps::section_cap;

const IDENTITY: [f64; 16] = [
    1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0,
];

fn rectangular_shell(min: [f64; 3], max: [f64; 3]) -> (Vec<f64>, Vec<u32>) {
    let [x0, y0, z0] = min;
    let [x1, y1, z1] = max;
    (
        vec![
            x0, y0, z0, x1, y0, z0, x1, y1, z0, x0, y1, z0, x0, y0, z1, x1, y0, z1, x1, y1, z1, x0,
            y1, z1,
        ],
        vec![
            0, 3, 2, 0, 2, 1, 4, 5, 6, 4, 6, 7, 0, 4, 7, 0, 7, 3, 1, 2, 6, 1, 6, 5, 0, 1, 5, 0, 5,
            4, 3, 7, 6, 3, 6, 2,
        ],
    )
}

fn cube() -> (Vec<f64>, Vec<u32>) {
    rectangular_shell([-1.0; 3], [1.0; 3])
}

fn append_mesh(target: &mut (Vec<f64>, Vec<u32>), mesh: (Vec<f64>, Vec<u32>)) {
    let offset = (target.0.len() / 3) as u32;
    target.0.extend(mesh.0);
    target
        .1
        .extend(mesh.1.into_iter().map(|index| index + offset));
}

fn near(actual: f64, expected: f64, tolerance: f64) {
    assert!(
        (actual - expected).abs() <= tolerance,
        "{actual} differs from {expected}"
    );
}

fn world(point: &[f32], m: &[f64; 16]) -> [f64; 3] {
    let [x, y, z] = [point[0] as f64, point[1] as f64, point[2] as f64];
    [
        m[0] * x + m[4] * y + m[8] * z + m[12],
        m[1] * x + m[5] * y + m[9] * z + m[13],
        m[2] * x + m[6] * y + m[10] * z + m[14],
    ]
}

fn inspect(cap: &[f32], m: &[f64; 16], height: f64) -> (f64, Vec<[[f64; 3]; 3]>) {
    assert!(!cap.is_empty());
    assert_eq!(
        cap.len() % 18,
        0,
        "positions and normals must contain complete triangles"
    );
    assert!(cap.iter().all(|value| value.is_finite()));
    let (positions, normals) = cap.split_at(cap.len() / 2);
    let mut area = 0.0;
    let mut triangles = Vec::new();
    // A^T n_world = n_local. For expected world-up, compare the normalized
    // local result to A^T (0,1,0); this also covers reflected/sheared matrices.
    let normal_length = m[1].hypot(m[5]).hypot(m[9]);
    for normal in normals.chunks_exact(3) {
        for (actual, expected) in normal.iter().zip([m[1], m[5], m[9]]) {
            near(*actual as f64, expected / normal_length, 1e-6);
        }
    }
    for triangle in positions.chunks_exact(9) {
        let points = [
            world(&triangle[0..3], m),
            world(&triangle[3..6], m),
            world(&triangle[6..9], m),
        ];
        for point in points {
            near(point[1], height, 1e-6);
        }
        let [a, b, c] = points;
        let cross_y = (b[2] - a[2]) * (c[0] - a[0]) - (b[0] - a[0]) * (c[2] - a[2]);
        assert!(cross_y > 0.0, "cap triangle winding must face world-up");
        area += cross_y / 2.0;
        triangles.push(points);
    }
    (area, triangles)
}

#[test]
fn indexed_and_unindexed_cube_sections_match() {
    let (positions, indices) = cube();
    let indexed = section_cap(&positions, &indices, &IDENTITY, 0.0);
    let unindexed_positions: Vec<_> = indices
        .iter()
        .flat_map(|&index| {
            positions[index as usize * 3..index as usize * 3 + 3]
                .iter()
                .copied()
        })
        .collect();
    let unindexed = section_cap(&unindexed_positions, &[], &IDENTITY, 0.0);
    assert_eq!(indexed, unindexed);
    near(inspect(&indexed, &IDENTITY, 0.0).0, 4.0, 2e-5);
}

#[test]
fn tangencies_near_boundaries_and_outside_cuts_are_empty() {
    let (positions, indices) = cube();
    for height in [
        -2.0,
        -1.0,
        -1.0 + 1e-6,
        1.0 - 1e-6,
        1.0,
        2.0,
        f64::NAN,
        f64::INFINITY,
    ] {
        assert!(
            section_cap(&positions, &indices, &IDENTITY, height).is_empty(),
            "height {height}"
        );
    }
    assert!(!section_cap(&positions, &indices, &IDENTITY, 0.0).is_empty());
}

#[test]
fn exact_vertex_plane_samples_the_retained_lower_side() {
    let (positions, indices) = cube();
    let angle = std::f64::consts::FRAC_PI_4;
    let mut matrix = IDENTITY;
    matrix[0] = angle.cos();
    matrix[1] = angle.sin();
    matrix[4] = -angle.sin();
    matrix[5] = angle.cos();
    let cap = section_cap(&positions, &indices, &matrix, 0.0);
    near(inspect(&cap, &matrix, 0.0).0, 4.0 * 2.0_f64.sqrt(), 4e-5);
}

#[test]
fn vertex_level_uses_the_lower_cross_section_when_outline_changes() {
    let mut mesh = rectangular_shell([-1.0, -1.0, -1.0], [1.0, 0.0, 1.0]);
    append_mesh(
        &mut mesh,
        rectangular_shell([-0.5, 0.0, -0.5], [0.5, 1.0, 0.5]),
    );
    let at_vertex = section_cap(&mesh.0, &mesh.1, &IDENTITY, 0.0);
    near(inspect(&at_vertex, &IDENTITY, 0.0).0, 4.0, 2e-5);
    let above_vertex = section_cap(&mesh.0, &mesh.1, &IDENTITY, 1e-4);
    near(inspect(&above_vertex, &IDENTITY, 1e-4).0, 1.0, 2e-5);
}

#[test]
fn submicrometre_tessellation_seams_weld_into_a_closed_contour() {
    let (positions, indices) = cube();
    let mut unindexed: Vec<_> = indices
        .iter()
        .flat_map(|&index| {
            positions[index as usize * 3..index as usize * 3 + 3]
                .iter()
                .copied()
        })
        .collect();
    for (index, point) in unindexed.chunks_exact_mut(3).enumerate() {
        point[0] += (index % 3) as f64 * 0.2e-6;
        point[2] += (index % 5) as f64 * 0.2e-6;
    }
    let cap = section_cap(&unindexed, &[], &IDENTITY, 0.0);
    near(inspect(&cap, &IDENTITY, 0.0).0, 4.0, 2e-5);
}

#[test]
fn shear_rotation_translation_scale_and_reflection_keep_world_up_winding() {
    let (positions, indices) = cube();
    // General affine transform, including shear and a negative determinant.
    let matrix = [
        -1.4, 0.3, 0.2, 0.0, 0.4, 0.8, -0.1, 0.0, 0.2, -0.2, 1.1, 0.0, 4.0, 3.0, -2.0, 1.0,
    ];
    let cap = section_cap(&positions, &indices, &matrix, 3.0);
    assert!(inspect(&cap, &matrix, 3.0).0 > 0.0);
}

#[test]
fn nested_contours_preserve_holes_and_disconnected_solid_islands() {
    let mut mesh = rectangular_shell([0.0, 0.0, 0.0], [4.0, 2.0, 3.0]);
    append_mesh(
        &mut mesh,
        rectangular_shell([1.0, 0.0, 1.0], [3.0, 2.0, 2.0]),
    );
    append_mesh(
        &mut mesh,
        rectangular_shell([1.5, 0.0, 1.25], [2.5, 2.0, 1.75]),
    );
    let cap = section_cap(&mesh.0, &mesh.1, &IDENTITY, 1.0);
    let (area, triangles) = inspect(&cap, &IDENTITY, 1.0);
    near(area, 12.0 - 2.0 + 0.5, 2e-5);
    for triangle in triangles {
        let x = triangle.iter().map(|point| point[0]).sum::<f64>() / 3.0;
        let z = triangle.iter().map(|point| point[2]).sum::<f64>() / 3.0;
        let in_hole = x > 1.0 && x < 3.0 && z > 1.0 && z < 2.0;
        let in_island = (1.5..=2.5).contains(&x) && (1.25..=1.75).contains(&z);
        assert!(
            !in_hole || in_island,
            "triangulation must not fill the empty hole"
        );
    }
}

#[test]
fn open_and_nonmanifold_contours_do_not_create_invented_caps() {
    let plane = [
        -1.0, -1.0, 0.0, 1.0, -1.0, 0.0, 1.0, 1.0, 0.0, -1.0, 1.0, 0.0,
    ];
    assert!(section_cap(&plane, &[0, 1, 2, 0, 2, 3], &IDENTITY, 0.0).is_empty());
    let mut mesh = cube();
    let start = (mesh.0.len() / 3) as u32;
    mesh.0
        .extend([1.0, -1.0, -1.0, 1.0, 1.0, -1.0, 2.0, 0.0, -1.0]);
    mesh.1.extend([start, start + 1, start + 2]);
    assert!(section_cap(&mesh.0, &mesh.1, &IDENTITY, 0.0).is_empty());
}

#[test]
fn malformed_nonfinite_singular_and_projective_inputs_return_empty() {
    let (positions, indices) = cube();
    assert!(section_cap(&[], &[], &IDENTITY, 0.0).is_empty());
    assert!(section_cap(&positions[..positions.len() - 1], &indices, &IDENTITY, 0.0).is_empty());
    assert!(section_cap(&positions, &indices[..indices.len() - 1], &IDENTITY, 0.0).is_empty());
    assert!(section_cap(&positions, &[0, 1, u32::MAX], &IDENTITY, 0.0).is_empty());
    assert!(section_cap(&positions, &indices, &IDENTITY[..15], 0.0).is_empty());
    let mut nonfinite = positions.clone();
    nonfinite[0] = f64::NAN;
    assert!(section_cap(&nonfinite, &indices, &IDENTITY, 0.0).is_empty());
    nonfinite[0] = f64::INFINITY;
    assert!(section_cap(&nonfinite, &indices, &IDENTITY, 0.0).is_empty());
    let mut matrix = IDENTITY;
    matrix[0] = 0.0;
    assert!(section_cap(&positions, &indices, &matrix, 0.0).is_empty());
    matrix = IDENTITY;
    matrix[12] = f64::NAN;
    assert!(section_cap(&positions, &indices, &matrix, 0.0).is_empty());
    matrix = IDENTITY;
    matrix[3] = 0.1;
    assert!(section_cap(&positions, &indices, &matrix, 0.0).is_empty());
    matrix = IDENTITY;
    matrix[15] = 2.0;
    assert!(section_cap(&positions, &indices, &matrix, 0.0).is_empty());
    let mut overflow = positions;
    overflow[0] = f64::MAX;
    matrix = IDENTITY;
    matrix[0] = 2.0;
    assert!(section_cap(&overflow, &indices, &matrix, 0.0).is_empty());
}

#[test]
fn repeated_execution_is_deterministic() {
    let (positions, indices) = cube();
    let expected = section_cap(&positions, &indices, &IDENTITY, 0.375);
    for _ in 0..25 {
        assert_eq!(
            section_cap(&positions, &indices, &IDENTITY, 0.375),
            expected
        );
    }
}
