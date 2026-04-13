"""
Exhaustive search for small non-linear counterexamples in the 112 FP cases
that have no linear magma CE.

For 3-element magmas: 3^9 = 19,683 tables — fully exhaustive.
For 4-element magmas: 4^16 = 4B — sample only.

Uses vectorized numpy evaluation: evaluates all magmas × all assignments
simultaneously, so the inner loop is fast.
"""

import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
from itertools import product as iproduct
from collections import defaultdict
import time

# ── Reuse parser from precompute_magmas.py ───────────────────────────────────

class Var:
    def __init__(self, name): self.name = name
    def __repr__(self): return self.name

class Op:
    def __init__(self, left, right): self.left = left; self.right = right
    def __repr__(self): return f"({self.left} * {self.right})"

def tokenize(s):
    tokens = []
    i = 0
    while i < len(s):
        if s[i].isspace(): i += 1
        elif s[i] in '()*=': tokens.append(s[i]); i += 1
        else:
            j = i
            while j < len(s) and s[j].isalpha(): j += 1
            tokens.append(s[i:j]); i = j
    return tokens

def parse_term(tokens, pos):
    if tokens[pos] == '(':
        pos += 1
        left, pos = parse_term(tokens, pos)
        assert tokens[pos] == '*'
        pos += 1
        right, pos = parse_term(tokens, pos)
        assert tokens[pos] == ')'
        pos += 1
        return Op(left, right), pos
    else:
        return Var(tokens[pos]), pos + 1

def parse_side(tokens, pos):
    left, pos = parse_term(tokens, pos)
    if pos < len(tokens) and tokens[pos] == '*':
        pos += 1
        right, pos = parse_term(tokens, pos)
        return Op(left, right), pos
    return left, pos

def parse_equation(eq_str):
    tokens = tokenize(eq_str)
    eq_pos = tokens.index('=')
    lhs, _ = parse_side(tokens[:eq_pos], 0)
    rhs, _ = parse_side(tokens[eq_pos+1:], 0)
    vars_ = set()
    def cv(node):
        if isinstance(node, Var): vars_.add(node.name)
        else: cv(node.left); cv(node.right)
    cv(lhs); cv(rhs)
    return lhs, rhs, sorted(vars_)


# ── Vectorized evaluation ─────────────────────────────────────────────────────
# tables: shape (N_magmas, n, n) — N_magmas multiplication tables on {0..n-1}
# assignments: shape (N_assign, n_vars) — all variable assignments
# eval returns shape (N_magmas, N_assign) — result element for each combo

def eval_vec(node, var_index, tables, assignments):
    """
    node: expression tree
    var_index: dict mapping variable name -> column index in assignments
    tables: (N_magmas, n, n)
    assignments: (N_assign, n_vars)
    returns: (N_magmas, N_assign) int array
    """
    if isinstance(node, Var):
        # assignments[:, var_index[node.name]] has shape (N_assign,)
        # broadcast to (1, N_assign) → (N_magmas, N_assign) via numpy broadcasting
        vals = assignments[:, var_index[node.name]]  # (N_assign,)
        return np.broadcast_to(vals[np.newaxis, :], (tables.shape[0], assignments.shape[0])).copy()
    else:
        left = eval_vec(node.left, var_index, tables, assignments)   # (N_magmas, N_assign)
        right = eval_vec(node.right, var_index, tables, assignments)  # (N_magmas, N_assign)
        # tables[magma_idx, left[magma_idx, assign_idx], right[magma_idx, assign_idx]]
        N_magmas = tables.shape[0]
        N_assign = assignments.shape[0]
        magma_idx = np.arange(N_magmas)[:, np.newaxis]  # (N_magmas, 1)
        return tables[magma_idx, left, right]  # (N_magmas, N_assign)


def check_implication_vec(lhs1, rhs1, lhs2, rhs2, variables, tables, n):
    """
    For each magma in tables, check if EQ1 holds universally AND EQ2 fails somewhere.
    Returns boolean array of shape (N_magmas,): True = this magma is a CE.
    """
    n_vars = len(variables)
    var_index = {v: i for i, v in enumerate(variables)}

    # All assignments
    assigns = np.array(list(iproduct(range(n), repeat=n_vars)), dtype=np.int32)  # (n^n_vars, n_vars)

    # Evaluate both equations
    l1 = eval_vec(lhs1, var_index, tables, assigns)  # (N_magmas, n^n_vars)
    r1 = eval_vec(rhs1, var_index, tables, assigns)
    l2 = eval_vec(lhs2, var_index, tables, assigns)
    r2 = eval_vec(rhs2, var_index, tables, assigns)

    eq1_holds = np.all(l1 == r1, axis=1)   # (N_magmas,): EQ1 universal
    eq2_fails = np.any(l2 != r2, axis=1)   # (N_magmas,): EQ2 not universal

    return eq1_holds & eq2_fails


# ── Generate all n-element magma tables ──────────────────────────────────────

def all_magma_tables(n):
    """Generate all n^(n^2) multiplication tables as array (N, n, n)."""
    N = n ** (n * n)
    tables_flat = np.array(list(iproduct(range(n), repeat=n*n)), dtype=np.int32)
    return tables_flat.reshape(N, n, n)


def sample_magma_tables(n, k, seed=42):
    """Sample k random n-element magma tables."""
    rng = np.random.default_rng(seed)
    tables = rng.integers(0, n, size=(k, n, n), dtype=np.int32)
    return tables


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Load hard3 results, find FP cases with no linear CE
    with open(ROOT / 'results/haiku_v8_hard3.json') as f:
        data = json.load(f)
    results = data['results']
    fp_cases = [r for r in results if r.get('answer') == False and r.get('verdict') == 'TRUE']

    # Re-run linear check to identify which FPs have no linear CE
    PARAMS = [(a, b, p) for p in [2, 3, 5] for a in range(p) for b in range(p)]

    def poly_coeffs(node, variables, a, b, p):
        if isinstance(node, Var):
            return {v: (1 if v == node.name else 0) for v in variables}
        lc = poly_coeffs(node.left, variables, a, b, p)
        rc = poly_coeffs(node.right, variables, a, b, p)
        return {v: (a * lc[v] + b * rc[v]) % p for v in variables}

    def satisfies_linear(lhs, rhs, variables, a, b, p):
        lc = poly_coeffs(lhs, variables, a, b, p)
        rc = poly_coeffs(rhs, variables, a, b, p)
        return all(lc[v] == rc[v] for v in variables)

    def has_linear_ce(lhs1, rhs1, lhs2, rhs2, variables):
        for (a, b, p) in PARAMS:
            if satisfies_linear(lhs1, rhs1, variables, a, b, p) and \
               not satisfies_linear(lhs2, rhs2, variables, a, b, p):
                return True
        return False

    no_linear_ce = []
    for r in fp_cases:
        lhs1, rhs1, v1 = parse_equation(r['equation1'])
        lhs2, rhs2, v2 = parse_equation(r['equation2'])
        variables = sorted(set(v1) | set(v2))
        lhs1, rhs1, _ = parse_equation(r['equation1'])
        lhs2, rhs2, _ = parse_equation(r['equation2'])
        if not has_linear_ce(lhs1, rhs1, lhs2, rhs2, variables):
            no_linear_ce.append({
                'id': r['id'], 'eq1': r['equation1'], 'eq2': r['equation2'],
                'variables': variables,
                'lhs1': lhs1, 'rhs1': rhs1, 'lhs2': lhs2, 'rhs2': rhs2,
            })

    print(f"FP cases with no linear CE: {len(no_linear_ce)}")
    print()

    # ── 3-element exhaustive search ───────────────────────────────────────────
    print("=== 3-element exhaustive search (3^9 = 19,683 magmas) ===")
    t0 = time.time()
    tables3 = all_magma_tables(3)
    print(f"  Generated {len(tables3)} tables in {time.time()-t0:.1f}s")

    ce3_counts = defaultdict(list)  # table_idx -> list of problem ids
    found3 = []

    for prob in no_linear_ce:
        variables = prob['variables']
        t1 = time.time()
        ce_mask = check_implication_vec(
            prob['lhs1'], prob['rhs1'], prob['lhs2'], prob['rhs2'],
            variables, tables3, 3
        )
        n_ces = ce_mask.sum()
        if n_ces > 0:
            found3.append({'id': prob['id'], 'eq1': prob['eq1'], 'eq2': prob['eq2'],
                          'n_ces': int(n_ces), 'ce_indices': np.where(ce_mask)[0][:5].tolist()})

    print(f"  Problems with 3-element CE: {len(found3)}/{len(no_linear_ce)}")
    print(f"  Time: {time.time()-t0:.1f}s")
    print()

    if found3:
        print("  Sample CEs found:")
        for p in found3[:5]:
            print(f"    {p['id']}: {p['eq1']} | {p['eq2']}")
            # Show one CE table
            idx = p['ce_indices'][0]
            tbl = tables3[idx]
            print(f"      CE table (3-element): {tbl.tolist()}")
        print()

    not_found3 = len(no_linear_ce) - len(found3)
    print(f"  Still no CE after 3-element search: {not_found3}")
    print()

    # ── 4-element sample search ───────────────────────────────────────────────
    remaining_after3 = [p for p in no_linear_ce
                        if p['id'] not in {f['id'] for f in found3}]

    if remaining_after3:
        print(f"=== 4-element sampled search ({len(remaining_after3)} remaining problems) ===")
        N_SAMPLE = 200_000
        t0 = time.time()
        tables4 = sample_magma_tables(4, N_SAMPLE)
        print(f"  Sampled {N_SAMPLE} 4-element tables in {time.time()-t0:.1f}s")

        found4 = []
        for prob in remaining_after3:
            variables = prob['variables']
            ce_mask = check_implication_vec(
                prob['lhs1'], prob['rhs1'], prob['lhs2'], prob['rhs2'],
                variables, tables4, 4
            )
            n_ces = ce_mask.sum()
            if n_ces > 0:
                found4.append({'id': prob['id'], 'eq1': prob['eq1'], 'eq2': prob['eq2'],
                               'n_ces': int(n_ces)})

        print(f"  Problems with 4-element CE found in sample: {len(found4)}/{len(remaining_after3)}")
        print(f"  Time: {time.time()-t0:.1f}s")
        print()

        not_found4 = len(remaining_after3) - len(found4)
        print(f"  Still no CE after 4-element sample: {not_found4}")
        print()

    # ── Summary ───────────────────────────────────────────────────────────────
    print("=== Summary ===")
    total_fp = len(fp_cases)
    covered_linear = total_fp - len(no_linear_ce)
    covered_3el = len(found3)
    covered_4el = len(found4) if remaining_after3 else 0
    uncovered = not_found4 if remaining_after3 else not_found3

    print(f"Total FP cases: {total_fp}")
    print(f"  Covered by linear magmas:      {covered_linear}")
    print(f"  Covered by 3-element magmas:   {covered_3el}")
    print(f"  Covered by 4-element (sample): {covered_4el}")
    print(f"  Not covered by any found:      {uncovered}")
    print()
    print(f"  Total reachable CEs found: {covered_linear + covered_3el + covered_4el}/{total_fp} ({100*(covered_linear+covered_3el+covered_4el)/total_fp:.1f}%)")


if __name__ == '__main__':
    main()
