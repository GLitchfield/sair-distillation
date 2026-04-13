# Cohomological Fingerprinting for Magma Implication

## The Core Idea

For each equation E in the competition's problem set, we can precompute a **cohomological fingerprint** — a compact numerical summary of how E behaves under the magma cohomology construction. At inference time, comparing fingerprints of E1 and E2 gives a mechanical test for refuting implications (proving FALSE) that catches cases our small-magma testing misses.

## Why This Matters

Our current best strategy (test 6 specific magmas) achieves ~93% accuracy on the normal problem set. All 500 TRUE cases are correct, but 69 FALSE cases slip through — both equations happen to be satisfied by all 6 test magmas, so we can't find a counterexample.

Cohomology attacks exactly this gap. Even when every small magma you test satisfies both E1 and E2, the cohomology can detect that E1's "extension structure" is richer than E2's, which proves E1 cannot imply E2. The counterexample magma lives on F_p × F_p (size p²), which is typically too large for brute-force enumeration but falls right out of the linear algebra.

## Mathematical Setup

### Step 1: Linear Magma Satisfiability

For a linear magma on F_p with operation x ◇ y = ax + by, every magma expression w(x₁,...,xₙ) evaluates to a linear combination:

    w(x₁,...,xₙ) = Σᵢ Pᵢ(a,b) · xᵢ

where Pᵢ(a,b) are polynomials in a,b with natural number coefficients. These polynomials can be computed recursively:

- If w = xᵢ (a bare variable): P_i = 1, P_j = 0 for j ≠ i
- If w = w₁ ◇ w₂: P_{w,i}(a,b) = a · P_{w₁,i}(a,b) + b · P_{w₂,i}(a,b)

An equation E: w_L ≃ w_R holds in this linear magma iff P_{w_L,i}(a,b) = P_{w_R,i}(a,b) for all variables i.

**Implementation**: Write a function `satisfies_linear(equation, a, b, p) -> bool` that checks this.

### Step 2: Cocycle Space Computation

Fix (a, b, p) where both E1 and E2 are satisfied. The cocycle space Z²_E(G, M) for G = M = F_p with operation ax + by consists of all functions f: F_p × F_p → F_p satisfying:

    Σ_{w₁◇w₂ ≤ w_L} Q_{w_L, w₁◇w₂}(a,b) · f(w₁(x⃗), w₂(x⃗))
    = Σ_{w₁◇w₂ ≤ w_R} Q_{w_R, w₁◇w₂}(a,b) · f(w₁(x⃗), w₂(x⃗))

for ALL x⃗ ∈ F_p^n (where n is the number of variables in E).

Since f has p² unknowns (the values f(i,j) for i,j ∈ F_p), and we get one linear constraint per choice of x⃗, this is a system of p^n linear equations in p² unknowns over F_p.

**Implementation**: 
1. Represent f as a vector of p² unknowns
2. For each x⃗ ∈ F_p^n, evaluate all subexpressions w₁, w₂ in the linear magma to get concrete elements of F_p
3. The cocycle constraint becomes: Σ coefficients · f(concrete_val₁, concrete_val₂) = 0
4. This gives one row of the constraint matrix
5. After processing all x⃗, row-reduce to find dim(Z²_E)

### Step 3: Coboundary Space

The coboundary space B²(G, M) consists of functions f(x,y) = g(ax + by) - a·g(x) - b·g(y) for some g: F_p → F_p. This is the image of the map d¹: C¹ → C², which has p unknowns (the values of g) and produces p² values. 

dim(B²) = p - dim(ker(d¹))

where ker(d¹) = {g : g(ax+by) = ag(x) + bg(y) for all x,y} is the set of "linear" functions (magma homomorphisms from G to M).

**Implementation**: Build the p² × p matrix for d¹ and compute its rank.

### Step 4: The Fingerprint

For each equation E and each parameter choice (a, b, p):
- `sat(E, a, b, p)`: 1 if the linear magma satisfies E, 0 otherwise
- `z_dim(E, a, b, p)`: dimension of Z²_E if satisfiable, else N/A
- `h_dim(E, a, b, p)`: dimension of H²_E = z_dim - b_dim if satisfiable, else N/A

The **fingerprint** of E is the tuple of these values across all parameter choices.

### Step 5: The Decision Rule

Given equations E1 and E2, for each (a, b, p) where BOTH are satisfiable:

1. **Dimension test**: If z_dim(E1) > z_dim(E2), then Z²_E1 ⊄ Z²_E2, so E1 CANNOT imply E2 → **FALSE**

2. **Subspace test** (stronger): Actually check if the null space of the E1 cocycle matrix is contained in the null space of the E2 cocycle matrix. If not → **FALSE**

3. **Cohomology dimension test**: If h_dim(E1) > h_dim(E2) → **FALSE**

If none of these fire for any parameter choice → no information (fall back to other methods).

## Recommended Parameter Choices

We want (a, b, p) triples where many equations are simultaneously satisfiable, giving us the most discriminating power.

### p = 2 (4 unknowns for f — very cheap)
- (0, 0): constant-zero. Satisfies equations where both sides have order ≥ 1 with matching structure.
- (1, 0): left projection.
- (0, 1): right projection.  
- (1, 1): XOR.

### p = 3 (9 unknowns for f — moderate)
- (1, 2) mod 3: i.e., x ◇ y = x - y. 
- (2, 1) mod 3: i.e., x ◇ y = 2x + y = -x + y.
- (1, 1) mod 3: x ◇ y = x + y.
- (2, 2) mod 3: x ◇ y = 2x + 2y = -(x+y).

### p = 5 (25 unknowns — more expensive but richer)
- (3, 4) mod 5: golden ratio (3² = 9 ≡ 4 = 3+1 mod 5, so φ = 3).
- (2, 3) mod 5: another common satisfying pair.
- (1, 4) mod 5: x ◇ y = x - y mod 5.

### Why these?
- p=2 is the cheapest and catches many cases (our data shows 90% of FALSE refuted by 2-element magmas)
- p=3 catches cases where p=2 is too coarse (XOR over F_3 distinguishes more)
- p=5 is where the golden ratio lives, which is needed for equations like E1110
- The specific (a,b) choices are ones where many order-≤4 equations are satisfiable

## Encoding Strategy for the Cheat Sheet

### Option A: Encode Per-Equation Fingerprints (~3-6 KB)

For each equation appearing in the problem set (estimated ~500-600 unique equations), store a compact fingerprint. Example encoding:

```
# Format: EqNum:sat_bits|z_dims
# sat_bits = which of 12 parameter choices satisfy this equation (12 bits → 3 hex chars)
# z_dims = cocycle dimensions for satisfied params (1 digit each)
E43:F0A|443
E65:C38|5524
E1491:C30|4423
...
```

At ~15 chars per equation × 600 equations = ~9 KB. Tight but feasible.

The LLM's decision procedure:
1. Look up E1 and E2 fingerprints
2. Find parameter choices where both are satisfied (AND the sat_bits)
3. Compare z_dims at those positions
4. If any z_dim(E1) > z_dim(E2) → FALSE

### Option B: Encode Decision Boundaries (~1-2 KB)

Instead of raw fingerprints, precompute which equation-pair features predict FALSE and encode just the rules:

```
RULES FOR ADDITIONAL FALSE DETECTION:
If E1 satisfies XOR(F2) but E2 does not → FALSE
If E1 satisfies x◇y=x-y(F3) but E2 does not → FALSE  
If both satisfy x◇y=x+y(F3) and E1 has cocycle dim > E2 → FALSE
...
```

More compact but less general.

### Option C: Hybrid — Expand the Magma Battery + Cohomology Rules (~4-6 KB)

Add more test magmas (linear magmas over F_3 and F_5) to the existing 6-magma strategy, and add cohomology-based decision rules for when all magmas pass. This keeps the cheat sheet mostly procedural (which LLMs handle well) while adding the cohomological discrimination power.

## Precomputation Pipeline (for Claude Code to implement)

```python
# Pseudocode — actual implementation in Python with numpy

import numpy as np
from itertools import product

def parse_equation(eq_str):
    """Parse equation string into (lhs_tree, rhs_tree) with variable names."""
    ...

def poly_coefficients(tree, variables, a, b, p):
    """Compute P_{w,i}(a,b) mod p for each variable i."""
    if tree is a variable x_i:
        coeffs = {v: 0 for v in variables}
        coeffs[x_i] = 1
        return coeffs
    else:  # tree = left ◇ right
        left_coeffs = poly_coefficients(tree.left, variables, a, b, p)
        right_coeffs = poly_coefficients(tree.right, variables, a, b, p)
        return {v: (a * left_coeffs[v] + b * right_coeffs[v]) % p 
                for v in variables}

def satisfies_linear(eq, a, b, p):
    """Check if linear magma x◇y = ax+by mod p satisfies equation."""
    lhs_coeffs = poly_coefficients(eq.lhs, eq.variables, a, b, p)
    rhs_coeffs = poly_coefficients(eq.rhs, eq.variables, a, b, p)
    return all(lhs_coeffs[v] == rhs_coeffs[v] for v in eq.variables)

def eval_in_linear_magma(tree, assignment, a, b, p):
    """Evaluate expression tree with concrete variable assignments in F_p."""
    if tree is variable x_i:
        return assignment[x_i]
    else:
        left_val = eval_in_linear_magma(tree.left, assignment, a, b, p)
        right_val = eval_in_linear_magma(tree.right, assignment, a, b, p)
        return (a * left_val + b * right_val) % p

def subterms_diamond(tree):
    """Return list of (w1, w2) for each w1◇w2 subterm of tree, 
       with the Q coefficient (monomial in a,b applied above this node)."""
    ...

def cocycle_matrix(eq, a, b, p):
    """Build the constraint matrix for E-cocycles.
    
    f has p² unknowns: f(i,j) for i,j in F_p.
    For each assignment x⃗ in F_p^n, we get one constraint row.
    Returns matrix A where A @ f_vec = 0 defines Z²_E.
    """
    n_vars = len(eq.variables)
    n_unknowns = p * p
    rows = []
    
    for assignment_vals in product(range(p), repeat=n_vars):
        assignment = dict(zip(eq.variables, assignment_vals))
        row = [0] * n_unknowns
        
        # For each ◇-subterm in LHS, add its Q-coefficient times f(w1_val, w2_val)
        for (w1, w2, Q_coeff) in subterms_with_coefficients(eq.lhs, a, b, p):
            w1_val = eval_in_linear_magma(w1, assignment, a, b, p)
            w2_val = eval_in_linear_magma(w2, assignment, a, b, p)
            idx = w1_val * p + w2_val
            row[idx] = (row[idx] + Q_coeff) % p
        
        # Subtract contributions from RHS
        for (w1, w2, Q_coeff) in subterms_with_coefficients(eq.rhs, a, b, p):
            w1_val = eval_in_linear_magma(w1, assignment, a, b, p)
            w2_val = eval_in_linear_magma(w2, assignment, a, b, p)
            idx = w1_val * p + w2_val
            row[idx] = (row[idx] - Q_coeff) % p
        
        rows.append(row)
    
    return np.array(rows) % p

def coboundary_matrix(a, b, p):
    """Build the matrix for d¹: C¹ → C².
    
    g has p unknowns: g(0), g(1), ..., g(p-1).
    f(x,y) = g(ax+by) - a*g(x) - b*g(y) has p² outputs.
    Returns p² × p matrix.
    """
    mat = np.zeros((p*p, p), dtype=int)
    for x in range(p):
        for y in range(p):
            row_idx = x * p + y
            xy_val = (a * x + b * y) % p
            mat[row_idx, xy_val] = (mat[row_idx, xy_val] + 1) % p
            mat[row_idx, x] = (mat[row_idx, x] - a) % p
            mat[row_idx, y] = (mat[row_idx, y] - b) % p
    return mat % p

def rank_mod_p(matrix, p):
    """Compute rank of matrix over F_p using Gaussian elimination."""
    # Standard Gaussian elimination with modular arithmetic
    ...

def cocycle_dim(eq, a, b, p):
    """Dimension of Z²_E = p² - rank(cocycle_matrix)."""
    mat = cocycle_matrix(eq, a, b, p)
    return p*p - rank_mod_p(mat, p)

def coboundary_dim(a, b, p):
    """Dimension of B² = rank(coboundary_matrix)."""
    mat = coboundary_matrix(a, b, p)
    return rank_mod_p(mat, p)

def cohomology_dim(eq, a, b, p):
    """Dimension of H²_E = dim(Z²_E) - dim(B²)."""
    return cocycle_dim(eq, a, b, p) - coboundary_dim(a, b, p)

def check_implication_cohomology(eq1, eq2, params_list):
    """Check if cohomology refutes eq1 => eq2.
    
    Returns: 'FALSE' if refuted, 'UNKNOWN' otherwise.
    """
    for (a, b, p) in params_list:
        if satisfies_linear(eq1, a, b, p) and satisfies_linear(eq2, a, b, p):
            z1 = cocycle_dim(eq1, a, b, p)
            z2 = cocycle_dim(eq2, a, b, p)
            if z1 > z2:
                return 'FALSE'  # dim(Z²_E1) > dim(Z²_E2) → can't have containment
            
            # Stronger test: check actual subspace containment
            # (more expensive but catches more cases)
            mat1 = cocycle_matrix(eq1, a, b, p)
            mat2 = cocycle_matrix(eq2, a, b, p)
            null1 = null_space_mod_p(mat1, p)  # basis for Z²_E1
            null2 = null_space_mod_p(mat2, p)  # basis for Z²_E2
            if not subspace_contained(null1, null2, p):
                return 'FALSE'
    
    return 'UNKNOWN'

# Main pipeline
PARAMS = [
    # (a, b, p)
    (0, 0, 2), (1, 0, 2), (0, 1, 2), (1, 1, 2),  # F_2
    (1, 2, 3), (2, 1, 3), (1, 1, 3), (2, 2, 3),  # F_3
    (3, 4, 5), (1, 4, 5), (2, 3, 5),              # F_5
]

def compute_fingerprint(eq):
    """Compute full fingerprint for an equation."""
    fp = {}
    for (a, b, p) in PARAMS:
        sat = satisfies_linear(eq, a, b, p)
        fp[(a,b,p)] = {
            'satisfies': sat,
            'z_dim': cocycle_dim(eq, a, b, p) if sat else None,
            'h_dim': cohomology_dim(eq, a, b, p) if sat else None,
        }
    return fp

def evaluate_on_problems(problems, params=PARAMS):
    """Run cohomology check on all problems, report accuracy improvement."""
    results = {'correct': 0, 'incorrect': 0, 'unknown': 0}
    
    for prob in problems:
        eq1, eq2, true_answer = prob
        cohom_answer = check_implication_cohomology(eq1, eq2, params)
        
        if cohom_answer == 'FALSE':
            if true_answer == False:
                results['correct'] += 1
            else:
                results['incorrect'] += 1  # False positive! Cohomology should never give this
        else:
            results['unknown'] += 1
    
    return results
```

## Expected Impact

### What cohomology CAN catch:
- FALSE implications where both equations are satisfied by all small magmas (the 69 cases our current strategy misses)
- Cases where the equations have similar "shape" but different algebraic structure
- Austin-type implications (true for finite, false for infinite) — cohomology works over infinite fields too

### What cohomology CANNOT catch:
- TRUE implications (cohomology only proves FALSE, never TRUE)
- FALSE implications where the counterexample magma is non-linear or requires very specific structure

### Estimated accuracy improvement:
- Current: 93.1% (500 TP + 431 TN out of 1000)
- If cohomology catches even half the remaining 69 FALSE cases: ~96.5%
- If combined with expanded magma battery (linear magmas over F_3, F_5): potentially 97-98%

### Important: Zero false positives expected
The cohomology test is mathematically sound — if it says FALSE, it IS false. There's no accuracy tradeoff. It only adds true negatives, never introduces errors. This is the key advantage over heuristic approaches.

## Implementation Plan for Claude Code

1. **Phase 1**: Implement equation parser and linear magma satisfiability check
2. **Phase 2**: Implement cocycle matrix construction and Gaussian elimination over F_p
3. **Phase 3**: Run on the normal.jsonl problem set, measure how many of the 69 "missed" FALSE cases get caught
4. **Phase 4**: Determine encoding strategy based on results — fingerprints vs rules vs expanded magma battery
5. **Phase 5**: Integrate into cheat sheet

The hardest part is Phase 2 — correctly computing the Q coefficients (the monomials in a,b that appear above each ◇-subterm in the expression tree). This requires a careful recursive traversal of the expression tree that tracks both the evaluation AND the polynomial coefficients simultaneously.

## Appendix: Computing Q Coefficients

For a word w, each ◇-subterm w₁ ◇ w₂ has a coefficient Q_{w, w₁◇w₂}(a,b) that represents "what happens above this subterm in the expression tree." The recursion:

- Q_{w, w} = 1 (the whole expression is its own top-level subterm, coefficient 1)
- If w = w_L ◇ w_R, and w₁◇w₂ is a subterm of w_L:
  Q_{w, w₁◇w₂} = a · Q_{w_L, w₁◇w₂}
- If w = w_L ◇ w_R, and w₁◇w₂ is a subterm of w_R:
  Q_{w, w₁◇w₂} = b · Q_{w_R, w₁◇w₂}

So Q is literally the product of a's and b's along the path from the subterm up to the root, where you multiply by `a` when going up through a left branch and `b` when going up through a right branch.

Example: For w = x ◇ (y ◇ z):
- The top-level ◇ has Q = 1
- The subterm y ◇ z sits on the right of the root, so Q = b

For w = (x ◇ y) ◇ (y ◇ z):
- The top-level ◇ has Q = 1  
- x ◇ y sits on the left, so Q = a
- y ◇ z sits on the right, so Q = b
