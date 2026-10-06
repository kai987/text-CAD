use text_cad_spatial_core::{
    aabb_candidates, aabb_contact_candidates, bounds_contact, bounds_overlap, Bounds,
};

#[test]
fn strict_aabb_boundary_and_epsilon_semantics_match_the_original_predicate() {
    let boxes = [
        [0.0, 0.0, 0.0, 2.0, 2.0, 2.0],
        [2.0, 0.0, 0.0, 3.0, 2.0, 2.0],
        [1.999, 0.0, 0.0, 3.0, 2.0, 2.0],
        [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
    ];
    assert_eq!(
        aabb_candidates(&boxes, &[boxes[0]], 0.0).unwrap(),
        [vec![0, 2, 3]]
    );
    assert_eq!(
        aabb_candidates(&boxes, &[boxes[0]], 0.01).unwrap(),
        [vec![0, 3]]
    );
    assert_eq!(
        aabb_candidates(&boxes, &[boxes[3]], 0.0).unwrap(),
        [vec![0]]
    );
    assert_eq!(
        aabb_candidates(&boxes, &[boxes[0]], -0.01).unwrap(),
        [vec![0, 1, 2, 3]]
    );
}

struct Random(u64);

impl Random {
    fn next(&mut self) -> f64 {
        self.0 = self
            .0
            .wrapping_mul(6364136223846793005)
            .wrapping_add(1442695040888963407);
        ((self.0 >> 11) as f64) / ((1_u64 << 53) as f64)
    }

    fn bounds(&mut self, index: usize) -> Bounds {
        let minimum: [f64; 3] = std::array::from_fn(|_| self.next() * 2000.0 - 1000.0);
        let size: [f64; 3] = std::array::from_fn(|axis| {
            if (index + axis).is_multiple_of(17) {
                0.0
            } else {
                self.next() * 400.0
            }
        });
        [
            minimum[0],
            minimum[1],
            minimum[2],
            minimum[0] + size[0],
            minimum[1] + size[1],
            minimum[2] + size[2],
        ]
    }
}

#[test]
fn indexed_aabb_matches_exhaustive_scan_for_randomized_and_degenerate_queries() {
    let mut random = Random(0x56a1_88bb_e17a_0123);
    let boxes: Vec<_> = (0..512).map(|i| random.bounds(i)).collect();
    let mut queries: Vec<_> = (0..96).map(|i| random.bounds(i + 21)).collect();
    queries.extend_from_slice(&boxes[..30]);
    queries.extend([
        [0.0; 6],
        [-5000.0, -5000.0, -5000.0, 5000.0, 5000.0, 5000.0],
    ]);
    for epsilon in [0.0, 0.001, 0.01, 1.0, 100.0, -0.01, -10.0] {
        let reference: Vec<Vec<_>> = queries
            .iter()
            .map(|query| {
                boxes
                    .iter()
                    .enumerate()
                    .filter_map(|(i, bounds)| bounds_overlap(bounds, query, epsilon).then_some(i))
                    .collect()
            })
            .collect();
        assert_eq!(
            aabb_candidates(&boxes, &queries, epsilon).unwrap(),
            reference
        );
    }
}

#[test]
fn aabb_extreme_finite_coordinates_and_empty_batches_are_safe() {
    let bounds = vec![[-f64::MAX, -1.0, -1.0, f64::MAX, 1.0, 1.0]; 32];
    let queries = [[0.0; 6], [f64::MAX / 2.0, -0.5, -0.5, f64::MAX, 0.5, 0.5]];
    let result = aabb_candidates(&bounds, &queries, 0.0).unwrap();
    assert_eq!(result, vec![(0..32).collect::<Vec<_>>(); 2]);
    assert_eq!(
        aabb_candidates(&[], &queries, 0.0).unwrap(),
        [Vec::<usize>::new(), Vec::new()]
    );
    assert!(aabb_candidates(&bounds, &[], 0.0).unwrap().is_empty());
}

#[test]
fn aabb_rejects_malformed_ranges_and_nonfinite_values() {
    let reversed = [1.0, 0.0, 0.0, 0.0, 1.0, 1.0];
    let mut nonfinite = [0.0, 0.0, 0.0, 1.0, 1.0, 1.0];
    nonfinite[3] = f64::INFINITY;
    assert!(aabb_candidates(&[reversed], &[], 0.0).is_err());
    assert!(aabb_candidates(&[], &[reversed], 0.0).is_err());
    assert!(aabb_candidates(&[nonfinite], &[], 0.0).is_err());
    assert!(aabb_candidates(&[], &[], f64::NAN).is_err());
}

#[test]
fn contact_preserves_faces_points_and_the_exact_tolerance_gap() {
    let query = [0.0, 0.0, 0.0, 1.0, 1.0, 1.0];
    let bounds = [
        query,
        [1.0, 0.0, 0.0, 2.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        [1.25, 0.0, 0.0, 2.0, 1.0, 1.0],
        [1.250001, 0.0, 0.0, 2.0, 1.0, 1.0],
    ];
    assert_eq!(
        aabb_contact_candidates(&bounds, &[query], 0.0).unwrap(),
        [vec![0, 1, 2]]
    );
    assert_eq!(
        aabb_contact_candidates(&bounds, &[query], 0.25).unwrap(),
        [vec![0, 1, 2, 3]]
    );
    assert_eq!(
        aabb_candidates(&bounds, &[query], 0.0).unwrap(),
        [vec![0]],
        "strict query semantics remain unchanged"
    );
    assert_eq!(
        aabb_contact_candidates(&bounds, &[bounds[2]], 0.0).unwrap(),
        [vec![0, 1, 2]]
    );
}

#[test]
fn contact_bvh_matches_randomized_exhaustive_inclusive_scans() {
    let mut random = Random(0x881c_17aa_2921_5752);
    let bounds: Vec<_> = (0..512).map(|i| random.bounds(i)).collect();
    let mut queries: Vec<_> = (0..96).map(|i| random.bounds(i + 9)).collect();
    queries.extend_from_slice(&bounds[..30]);
    queries.extend([
        [0.0; 6],
        [-5000.0, -5000.0, -5000.0, 5000.0, 5000.0, 5000.0],
    ]);
    for tolerance in [0.0, 1e-6, 0.1, 2.0, 400.0, 1e9] {
        let expected: Vec<Vec<_>> = queries
            .iter()
            .map(|query| {
                bounds
                    .iter()
                    .enumerate()
                    .filter_map(|(i, bound)| bounds_contact(bound, query, tolerance).then_some(i))
                    .collect()
            })
            .collect();
        assert_eq!(
            aabb_contact_candidates(&bounds, &queries, tolerance).unwrap(),
            expected
        );
    }
}

#[test]
fn contact_handles_extreme_finite_values_and_rejects_invalid_tolerance() {
    let bounds = [[f64::MAX, -1.0, -1.0, f64::MAX, 1.0, 1.0]; 32];
    assert_eq!(
        aabb_contact_candidates(&bounds, &[bounds[0]], 0.0).unwrap(),
        [vec![
            0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,
            24, 25, 26, 27, 28, 29, 30, 31
        ]]
    );
    for tolerance in [-0.1, f64::NAN, f64::INFINITY] {
        assert!(aabb_contact_candidates(&[], &[], tolerance).is_err());
    }
    assert_eq!(
        aabb_contact_candidates(&[], &[[0.0; 6]], 0.0).unwrap(),
        [Vec::<usize>::new()]
    );
}
