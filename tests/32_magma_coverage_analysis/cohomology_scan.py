#!/usr/bin/env python3
"""
Cohomology-based FALSE detection for equational implications.

For each (a,b,p) where both EQ1 and EQ2 hold in the linear magma x*y=ax+by mod p,
compute the cocycle space dimension for each equation. If dim(Z²_E1) > dim(Z²_E2),
then E1 cannot imply E2 → FALSE.
"""

import json
import sys
import numpy as np
from itertools import product as iproduct
from collections import defaultdict

sys.path.insert(0, '.')
from linear_magma_scan import parse_equation, get_variables, satisfies_linear


def eval_in_linear(tree, assignment, a, b, p):
    """Evaluate expression tree with concrete assignments in linear magma."""
    if isinstance(tree, str):
        return assignment[tree]
    left = eval_in_linear(tree[1], assignment, a, b, p)
    right = eval_in_linear(tree[2], assignment, a, b, p)
    return (a * left + b * right) % p


def get_star_subterms(tree):
    """Return list of (left_subtree, right_subtree, path_coefficient_fn) for each * node.

    For each w1*w2 subterm in tree, the Q coefficient is the product of a/b along
    the path from this subterm up to the root:
    - multiply by a when going up through a left branch
    - multiply by b when going up through a right branch
    """
    results = []

    def recurse(node, coeff_fn):
        if isinstance(node, str):
            return  # leaf variable, no * subterms
        # node = ('*', left, right)
        # This node itself is a * subterm
        results.append((node[1], node[2], coeff_fn))
        # Recurse into children
        recurse(node[1], lambda a, b, p, cf=coeff_fn: (a * cf(a, b, p)) % p)
        recurse(node[2], lambda a, b, p, cf=coeff_fn: (b * cf(a, b, p)) % p)

    recurse(tree, lambda a, b, p: 1)
    return results


def cocycle_matrix(eq_str, a, b, p):
    """Build the cocycle constraint matrix for an equation at (a,b,p).

    f has p² unknowns: f(i,j) for i,j in {0,...,p-1}.
    For each assignment x⃗ in F_p^n, we get one constraint:
    sum of Q*f(w1_val, w2_val) for LHS subterms = same for RHS subterms.
    """
    lhs_tree, rhs_tree = parse_equation(eq_str)
    variables = sorted(get_variables(lhs_tree) | get_variables(rhs_tree))
    n_vars = len(variables)
    n_unknowns = p * p

    lhs_subterms = get_star_subterms(lhs_tree)
    rhs_subterms = get_star_subterms(rhs_tree)

    rows = []
    for vals in iproduct(range(p), repeat=n_vars):
        assignment = dict(zip(variables, vals))
        row = np.zeros(n_unknowns, dtype=int)

        # Add LHS contributions
        for left, right, coeff_fn in lhs_subterms:
            w1_val = eval_in_linear(left, assignment, a, b, p)
            w2_val = eval_in_linear(right, assignment, a, b, p)
            q = coeff_fn(a, b, p)
            idx = w1_val * p + w2_val
            row[idx] = (row[idx] + q) % p

        # Subtract RHS contributions
        for left, right, coeff_fn in rhs_subterms:
            w1_val = eval_in_linear(left, assignment, a, b, p)
            w2_val = eval_in_linear(right, assignment, a, b, p)
            q = coeff_fn(a, b, p)
            idx = w1_val * p + w2_val
            row[idx] = (row[idx] - q) % p

        rows.append(row)

    return np.array(rows) % p


def rank_mod_p(matrix, p):
    """Compute rank of matrix over F_p using Gaussian elimination."""
    if matrix.size == 0:
        return 0
    m = matrix.copy() % p
    rows, cols = m.shape
    rank = 0
    for col in range(cols):
        # Find pivot
        pivot = None
        for row in range(rank, rows):
            if m[row, col] % p != 0:
                pivot = row
                break
        if pivot is None:
            continue
        # Swap
        m[[rank, pivot]] = m[[pivot, rank]]
        # Eliminate
        inv = pow(int(m[rank, col]), p - 2, p)  # Fermat's little theorem
        m[rank] = (m[rank] * inv) % p
        for row in range(rows):
            if row != rank and m[row, col] % p != 0:
                factor = m[row, col]
                m[row] = (m[row] - factor * m[rank]) % p
        rank += 1
    return rank


def cocycle_dim(eq_str, a, b, p):
    """Dimension of Z²_E = p² - rank(cocycle_matrix)."""
    mat = cocycle_matrix(eq_str, a, b, p)
    return p * p - rank_mod_p(mat, p)


def check_cohomology(eq1_str, eq2_str, params_list):
    """Check if cohomology refutes eq1 => eq2.
    Returns 'FALSE' with details if refuted, 'UNKNOWN' otherwise.
    """
    for a, b, p in params_list:
        if not satisfies_linear(eq1_str, a, b, p):
            continue
        if not satisfies_linear(eq2_str, a, b, p):
            continue  # shouldn't happen if linear scan found no CE, but just in case

        z1 = cocycle_dim(eq1_str, a, b, p)
        z2 = cocycle_dim(eq2_str, a, b, p)

        if z1 > z2:
            return 'FALSE', f'({a},{b}) mod {p}: dim(Z²_E1)={z1} > dim(Z²_E2)={z2}'

    return 'UNKNOWN', None


def main():
    # Parameters to check
    PARAMS = [
        # p=2
        (0, 0, 2), (1, 0, 2), (0, 1, 2), (1, 1, 2),
        # p=3
        (0, 0, 3), (1, 0, 3), (0, 1, 3), (1, 1, 3),
        (2, 1, 3), (1, 2, 3), (2, 2, 3), (2, 0, 3), (0, 2, 3),
        # p=5
        (0, 0, 5), (1, 0, 5), (0, 1, 5), (1, 1, 5),
        (2, 1, 5), (1, 2, 5), (2, 2, 5), (3, 3, 5),
        (3, 4, 5), (4, 3, 5), (2, 3, 5), (3, 2, 5),
    ]

    # Load problems
    dataset = sys.argv[1] if len(sys.argv) > 1 else 'datasets/order5_half.jsonl'
    with open(dataset) as f:
        probs = [json.loads(l) for l in f]

    false_probs = [p for p in probs if not p['answer']]
    print(f'Checking {len(false_probs)} FALSE problems with cohomology...')
    print(f'Parameters: {len(PARAMS)} (a,b,p) triples')
    print()

    caught = 0
    for i, prob in enumerate(false_probs):
        result, detail = check_cohomology(prob['equation1'], prob['equation2'], PARAMS)
        if result == 'FALSE':
            caught += 1
            print(f'  ✓ {prob["id"]}: {detail}')

        if (i + 1) % 20 == 0:
            print(f'  ... {i+1}/{len(false_probs)} checked, {caught} caught so far')

    print(f'\nCohomology catches: {caught}/{len(false_probs)} FALSE problems')
    print(f'Remaining uncaught: {len(false_probs) - caught}')


if __name__ == '__main__':
    main()
