#!/usr/bin/env python3
"""
Search structured 4-element magmas for counterexamples to order5 FALSE problems.
Since NO linear magma satisfies EQ1 for these problems, we need non-linear structures.
"""

import json
import sys
import random
from itertools import product as iproduct
from collections import Counter

sys.path.insert(0, '.')
from linear_magma_scan import parse_equation, get_variables


def check_magma(eq_str, table, size):
    """Check if equation holds universally in a table-based magma.
    Returns True (holds) or False (fails). Bails early on first failure."""
    lhs_tree, rhs_tree = parse_equation(eq_str)
    variables = sorted(get_variables(lhs_tree) | get_variables(rhs_tree))

    def eval_tree(tree, assignment):
        if isinstance(tree, str):
            return assignment[tree]
        left = eval_tree(tree[1], assignment)
        right = eval_tree(tree[2], assignment)
        return table[left * size + right]

    for vals in iproduct(range(size), repeat=len(variables)):
        assignment = dict(zip(variables, vals))
        if eval_tree(lhs_tree, assignment) != eval_tree(rhs_tree, assignment):
            return False
    return True


def generate_structured_4elem():
    """Generate structured 4-element magma tables."""
    size = 4
    tables = []

    # 1. Unary right: x*y = f(y) — 256 magmas
    for f in iproduct(range(4), repeat=4):
        table = []
        for x in range(4):
            for y in range(4):
                table.append(f[y])
        tables.append(('unary_right', tuple(table)))

    # 2. Unary left: x*y = f(x) — 256 magmas
    for f in iproduct(range(4), repeat=4):
        table = []
        for x in range(4):
            for y in range(4):
                table.append(f[x])
        tables.append(('unary_left', tuple(table)))

    # 3. Near right-projection: x*y=y with 1-2 entries changed
    base_rp = [y for x in range(4) for y in range(4)]
    for pos in range(16):
        for val in range(4):
            if val != base_rp[pos]:
                t = list(base_rp)
                t[pos] = val
                tables.append(('near_right_proj', tuple(t)))

    # 4. Near left-projection: x*y=x with 1-2 entries changed
    base_lp = [x for x in range(4) for y in range(4)]
    for pos in range(16):
        for val in range(4):
            if val != base_lp[pos]:
                t = list(base_lp)
                t[pos] = val
                tables.append(('near_left_proj', tuple(t)))

    # 5. Near constant-0: x*y=0 with 1-2 entries changed
    base_z = [0] * 16
    for pos in range(16):
        for val in range(1, 4):
            t = list(base_z)
            t[pos] = val
            tables.append(('near_zero', tuple(t)))
    # 2-entry perturbations of constant-0
    for p1 in range(16):
        for p2 in range(p1 + 1, 16):
            for v1 in range(1, 4):
                for v2 in range(1, 4):
                    t = list(base_z)
                    t[p1] = v1
                    t[p2] = v2
                    tables.append(('near_zero_2', tuple(t)))

    # 6. Cyclic permutation magmas: x*y = (x + f(y)) mod 4 or similar
    for shift in range(1, 4):
        for f in iproduct(range(4), repeat=4):
            table = []
            for x in range(4):
                for y in range(4):
                    table.append((x + f[y] * shift) % 4)
            tables.append(('cyclic', tuple(table)))

    # 7. Random 4-element magmas — sample 50,000
    random.seed(42)
    for _ in range(50000):
        table = tuple(random.randint(0, 3) for _ in range(16))
        tables.append(('random', table))

    # Deduplicate
    seen = set()
    unique = []
    for label, table in tables:
        if table not in seen:
            seen.add(table)
            unique.append((label, list(table)))
    return unique


def main():
    dataset = sys.argv[1] if len(sys.argv) > 1 else '../datasets/order5_half.jsonl'
    with open(dataset) as f:
        probs = [json.loads(l) for l in f]
    false_probs = [p for p in probs if not p['answer']]

    tables = generate_structured_4elem()
    print(f"Generated {len(tables)} unique 4-element magmas")
    print(f"Checking against {len(false_probs)} FALSE problems...")
    print()

    # For each magma, check which problems it catches
    problem_catches = Counter()
    magma_catches = {}

    for idx, (label, table) in enumerate(tables):
        catches = []
        for p in false_probs:
            if check_magma(p['equation1'], table, 4):
                if not check_magma(p['equation2'], table, 4):
                    catches.append(p['id'])
        if catches:
            magma_catches[(label, tuple(table))] = catches
            for pid in catches:
                problem_catches[pid] += 1

        if (idx + 1) % 5000 == 0:
            print(f"  {idx+1}/{len(tables)} magmas checked, {len(magma_catches)} useful found...")

    print(f"\nDone. {len(magma_catches)} magmas catch at least 1 problem.")
    caught_problems = set()
    for catches in magma_catches.values():
        caught_problems.update(catches)
    print(f"Total FALSE problems caught: {len(caught_problems)}/{len(false_probs)}")
    print()

    # Top magmas by catch count
    top = sorted(magma_catches.items(), key=lambda x: -len(x[1]))[:10]
    print("=== TOP 10 MAGMAS ===")
    for (label, table), catches in top:
        tbl_str = ','.join(str(x) for x in table)
        print(f"  {label}: [{tbl_str}] catches {len(catches)}")

    # Greedy selection
    print()
    print("=== GREEDY SELECTION ===")
    covered = set()
    remaining = dict(magma_catches)
    for i in range(10):
        if not remaining:
            break
        best_key = max(remaining, key=lambda k: len(set(remaining[k]) - covered))
        new = set(remaining[best_key]) - covered
        if not new:
            break
        covered |= new
        label, table = best_key
        tbl_str = ','.join(str(x) for x in table)
        print(f"  Pick {i+1}: {label} [{tbl_str}] +{len(new)} new (total: {len(covered)}/{len(false_probs)})")
        del remaining[best_key]


if __name__ == '__main__':
    main()
