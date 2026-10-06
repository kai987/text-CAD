use crate::SpatialError;

/// XYZ minimum followed by XYZ maximum. Zero thickness is permitted.
pub type Bounds = [f64; 6];
const LEAF_SIZE: usize = 8;

/// Exact original strict overlap predicate. A degenerate query may match a
/// larger box, so it is never rejected solely for having zero thickness.
pub fn bounds_overlap(a: &Bounds, b: &Bounds, epsilon: f64) -> bool {
    (0..3).all(|i| a[i] < b[i + 3] - epsilon && b[i] < a[i + 3] - epsilon)
}

/// Inclusive contact predicate used by the exact original CAD contact scan.
pub fn bounds_contact(a: &Bounds, b: &Bounds, tolerance: f64) -> bool {
    !(0..3).any(|i| a[i] > b[i + 3] + tolerance || b[i] > a[i + 3] + tolerance)
}

#[derive(Clone, Copy)]
enum QueryMode {
    Strict(f64),
    Contact(f64),
}

impl QueryMode {
    fn matches(self, a: &Bounds, b: &Bounds) -> bool {
        match self {
            Self::Strict(epsilon) => bounds_overlap(a, b, epsilon),
            Self::Contact(tolerance) => bounds_contact(a, b, tolerance),
        }
    }
}

fn validate_bounds(bounds: &[Bounds], name: &str) -> Result<(), SpatialError> {
    for (index, item) in bounds.iter().enumerate() {
        if item.iter().any(|value| !value.is_finite()) {
            return Err(SpatialError(format!(
                "{name} {index} contains nonfinite coordinates"
            )));
        }
        if (0..3).any(|i| item[i] > item[i + 3]) {
            return Err(SpatialError(format!(
                "{name} {index} has reversed minimum/maximum"
            )));
        }
    }
    Ok(())
}

enum Children {
    Leaf(Vec<usize>),
    Branch(Box<Node>, Box<Node>),
}

struct Node {
    envelope: Bounds,
    children: Children,
}

impl Node {
    fn build(bounds: &[Bounds], indices: &mut [usize]) -> Self {
        let mut envelope = bounds[indices[0]];
        for &index in &indices[1..] {
            for i in 0..3 {
                envelope[i] = envelope[i].min(bounds[index][i]);
                envelope[i + 3] = envelope[i + 3].max(bounds[index][i + 3]);
            }
        }
        let children = if indices.len() <= LEAF_SIZE {
            Children::Leaf(indices.to_vec())
        } else {
            let axis = (0..3)
                .max_by(|&a, &b| {
                    (envelope[a + 3] - envelope[a]).total_cmp(&(envelope[b + 3] - envelope[b]))
                })
                .unwrap_or(0);
            // Halve first so finite extreme coordinates cannot overflow when
            // forming the sort center. Sorting affects speed, not correctness.
            indices.sort_unstable_by(|&a, &b| {
                let center_a = bounds[a][axis] / 2.0 + bounds[a][axis + 3] / 2.0;
                let center_b = bounds[b][axis] / 2.0 + bounds[b][axis + 3] / 2.0;
                center_a.total_cmp(&center_b).then(a.cmp(&b))
            });
            let middle = indices.len() / 2;
            let (left, right) = indices.split_at_mut(middle);
            Children::Branch(
                Box::new(Self::build(bounds, left)),
                Box::new(Self::build(bounds, right)),
            )
        };
        Self { envelope, children }
    }

    fn query(&self, bounds: &[Bounds], query: &Bounds, mode: QueryMode, output: &mut Vec<usize>) {
        if !mode.matches(&self.envelope, query) {
            return;
        }
        match &self.children {
            Children::Leaf(indices) => {
                output.extend(
                    indices
                        .iter()
                        .copied()
                        .filter(|&index| mode.matches(&bounds[index], query)),
                );
            }
            Children::Branch(left, right) => {
                left.query(bounds, query, mode, output);
                right.query(bounds, query, mode, output);
            }
        }
    }
}

/// Build one BVH and return exact strict-overlap candidate indices for each
/// query, sorted by original input order. Every finite epsilon is supported,
/// including negative values, following the unmodified predicate above.
pub fn aabb_candidates(
    bounds: &[Bounds],
    queries: &[Bounds],
    epsilon: f64,
) -> Result<Vec<Vec<usize>>, SpatialError> {
    if !epsilon.is_finite() {
        return Err(SpatialError("epsilon must be finite".into()));
    }
    query_candidates(bounds, queries, QueryMode::Strict(epsilon))
}

/// Inclusive contact candidates, preserving faces, edges, points and a gap
/// exactly equal to tolerance. Candidate IDs are sorted by original input.
pub fn aabb_contact_candidates(
    bounds: &[Bounds],
    queries: &[Bounds],
    tolerance: f64,
) -> Result<Vec<Vec<usize>>, SpatialError> {
    if !tolerance.is_finite() || tolerance < 0.0 {
        return Err(SpatialError(
            "contact tolerance must be finite and non-negative".into(),
        ));
    }
    query_candidates(bounds, queries, QueryMode::Contact(tolerance))
}

fn query_candidates(
    bounds: &[Bounds],
    queries: &[Bounds],
    mode: QueryMode,
) -> Result<Vec<Vec<usize>>, SpatialError> {
    validate_bounds(bounds, "bounds")?;
    validate_bounds(queries, "query")?;
    if bounds.is_empty() {
        return Ok(vec![Vec::new(); queries.len()]);
    }
    let mut indices: Vec<_> = (0..bounds.len()).collect();
    let tree = Node::build(bounds, &mut indices);
    Ok(queries
        .iter()
        .map(|query| {
            let mut result = Vec::new();
            tree.query(bounds, query, mode, &mut result);
            result.sort_unstable();
            result
        })
        .collect())
}
