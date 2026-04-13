#!/usr/bin/env python3
"""
Scan linear magmas over F_p to find counterexamples for hard3 FALSE problems.
For each (a, b, p), the magma operation is x*y = (a*x + b*y) mod p.
An equation holds if the polynomial coefficients match for all variables.
"""

import json
import re
from itertools import product
from collections import defaultdict

# --- Equation Parser ---

def tokenize(eq_str):
    """Tokenize an equation string into tokens."""
    tokens = []
    i = 0
    while i < len(eq_str):
        c = eq_str[i]
        if c.isspace():
            i += 1
        elif c in '()*=':
            tokens.append(c)
            i += 1
        elif c.isalpha():
            var = ''
            while i < len(eq_str) and eq_str[i].isalpha():
                var += eq_str[i]
                i += 1
            tokens.append(var)
        else:
            i += 1
    return tokens

def parse_expr(tokens, pos):
    """Parse an expression, return (tree, new_pos).
    tree is either a string (variable) or ('*', left, right)."""
    left, pos = parse_atom(tokens, pos)
    while pos < len(tokens) and tokens[pos] == '*':
        pos += 1  # skip *
        right, pos = parse_atom(tokens, pos)
        left = ('*', left, right)
    return left, pos

def parse_atom(tokens, pos):
    """Parse an atom: variable or parenthesized expression."""
    if tokens[pos] == '(':
        pos += 1  # skip (
        expr, pos = parse_expr(tokens, pos)
        pos += 1  # skip )
        return expr, pos
    else:
        return tokens[pos], pos + 1

def parse_equation(eq_str):
    """Parse 'LHS = RHS' into (lhs_tree, rhs_tree)."""
    tokens = tokenize(eq_str)
    eq_idx = tokens.index('=')
    lhs, _ = parse_expr(tokens, 0)
    rhs, _ = parse_expr(tokens, eq_idx + 1)
    return lhs, rhs

def get_variables(tree):
    """Get all variable names from a tree."""
    if isinstance(tree, str):
        return {tree}
    return get_variables(tree[1]) | get_variables(tree[2])

# --- Linear Magma Evaluation ---

def poly_coefficients(tree, variables, a, b, p):
    """Compute polynomial coefficients for each variable in F_p.
    In linear magma x*y = ax+by mod p, any expression evaluates to
    sum(coeff[v] * v for v in variables) mod p.
    Returns dict: variable -> coefficient mod p."""
    if isinstance(tree, str):
        # It's a variable
        coeffs = {v: 0 for v in variables}
        coeffs[tree] = 1
        return coeffs
    # tree = ('*', left, right)
    left_coeffs = poly_coefficients(tree[1], variables, a, b, p)
    right_coeffs = poly_coefficients(tree[2], variables, a, b, p)
    return {v: (a * left_coeffs[v] + b * right_coeffs[v]) % p for v in variables}

def satisfies_linear(eq_str, a, b, p):
    """Check if linear magma (a,b,p) satisfies equation universally."""
    lhs_tree, rhs_tree = parse_equation(eq_str)
    variables = sorted(get_variables(lhs_tree) | get_variables(rhs_tree))
    lhs_coeffs = poly_coefficients(lhs_tree, variables, a, b, p)
    rhs_coeffs = poly_coefficients(rhs_tree, variables, a, b, p)
    return all(lhs_coeffs[v] == rhs_coeffs[v] for v in variables)

# --- Main scan ---

def main():
    # Load hard3
    with open('datasets/hard3.jsonl') as f:
        problems = [json.loads(line) for line in f]

    false_problems = [p for p in problems if not p['answer']]
    true_problems = [p for p in problems if p['answer']]
    print(f"Loaded {len(problems)} problems ({len(true_problems)} TRUE, {len(false_problems)} FALSE)")

    # Existing battery linear magmas (a, b, p)
    existing = {
        'A (const 0)': [(0, 0, 2), (0, 0, 3), (0, 0, 5)],
        'C (right proj)': [(0, 1, 2), (0, 1, 3), (0, 1, 5)],
        'D (left proj)': [(1, 0, 2), (1, 0, 3), (1, 0, 5)],
        'E (XOR)': [(1, 1, 2)],
        'F (addition)': [(1, 1, 3), (1, 1, 5)],
        'Linear (2x+y)': [(2, 1, 3)],
    }
    existing_triples = set()
    for triples in existing.values():
        existing_triples.update(triples)

    # Generate all (a, b, p) triples
    all_triples = []
    for p in [2, 3, 5]:
        for a in range(p):
            for b in range(p):
                all_triples.append((a, b, p))

    print(f"\nScanning {len(all_triples)} (a,b,p) triples against {len(false_problems)} FALSE problems...")

    # For each triple, find which FALSE problems it catches
    triple_catches = {}  # (a,b,p) -> set of problem IDs
    problem_caught_by = defaultdict(set)  # problem_id -> set of (a,b,p) that catch it

    for a, b, p in all_triples:
        catches = set()
        for prob in false_problems:
            eq1_holds = satisfies_linear(prob['equation1'], a, b, p)
            eq2_holds = satisfies_linear(prob['equation2'], a, b, p)
            if eq1_holds and not eq2_holds:
                catches.add(prob['id'])
                problem_caught_by[prob['id']].add((a, b, p))
        triple_catches[(a, b, p)] = catches

    # Also check: does any triple falsely catch a TRUE problem?
    false_positives = defaultdict(set)
    for a, b, p in all_triples:
        for prob in true_problems:
            eq1_holds = satisfies_linear(prob['equation1'], a, b, p)
            eq2_holds = satisfies_linear(prob['equation2'], a, b, p)
            if eq1_holds and not eq2_holds:
                false_positives[(a, b, p)].add(prob['id'])

    # Report existing battery coverage
    existing_caught = set()
    for triple in existing_triples:
        existing_caught |= triple_catches.get(triple, set())

    print(f"\n=== EXISTING BATTERY (linear magmas only) ===")
    print(f"FALSE problems caught: {len(existing_caught)}/{len(false_problems)}")
    for name, triples in existing.items():
        caught = set()
        for t in triples:
            caught |= triple_catches.get(t, set())
        if caught:
            print(f"  {name}: {len(caught)} catches")

    # Find NEW catches
    all_caught = set()
    for triple, catches in triple_catches.items():
        all_caught |= catches

    new_catches = all_caught - existing_caught
    print(f"\n=== ALL LINEAR MAGMAS (p=2,3,5) ===")
    print(f"Total FALSE caught: {len(all_caught)}/{len(false_problems)}")
    print(f"New catches beyond existing battery: {len(new_catches)}")

    # Rank new triples by marginal new catches
    new_triple_catches = {}
    for triple in all_triples:
        if triple in existing_triples:
            continue
        new_only = triple_catches.get(triple, set()) - existing_caught
        if new_only:
            new_triple_catches[triple] = new_only

    print(f"\n=== TOP NEW (a,b,p) TRIPLES (by new catches) ===")
    ranked = sorted(new_triple_catches.items(), key=lambda x: -len(x[1]))
    for (a, b, p), catches in ranked[:15]:
        is_existing = "(EXISTING)" if (a, b, p) in existing_triples else ""
        fp_count = len(false_positives.get((a, b, p), set()))
        print(f"  ({a},{b}) mod {p}  [x*y = {a}x+{b}y mod {p}]:  {len(catches)} new catches, {fp_count} false positives {is_existing}")

    # Greedy selection: pick triples that maximize coverage
    print(f"\n=== GREEDY SELECTION (maximize new coverage) ===")
    covered = set(existing_caught)
    selected = []
    remaining = dict(new_triple_catches)
    for i in range(10):
        if not remaining:
            break
        best_triple = max(remaining, key=lambda t: len(remaining[t] - covered))
        marginal = remaining[best_triple] - covered
        if not marginal:
            break
        covered |= marginal
        fp_count = len(false_positives.get(best_triple, set()))
        a, b, p = best_triple
        selected.append(best_triple)
        print(f"  Pick {i+1}: ({a},{b}) mod {p}  [x*y = {a}x+{b}y mod {p}]  +{len(marginal)} new  (total: {len(covered)}/{len(false_problems)}, FP: {fp_count})")
        del remaining[best_triple]

    # Coverage gap
    uncaught = set(p['id'] for p in false_problems) - all_caught
    print(f"\n=== COVERAGE GAP ===")
    print(f"FALSE problems NOT caught by any linear magma (p≤5): {len(uncaught)}/{len(false_problems)}")
    if uncaught:
        for pid in sorted(uncaught)[:10]:
            prob = next(p for p in false_problems if p['id'] == pid)
            print(f"  {pid}: EQ1={prob['equation1'][:50]}")
        if len(uncaught) > 10:
            print(f"  ... and {len(uncaught)-10} more")

    # Verify: zero false positives on TRUE problems for all triples
    total_fp = sum(len(v) for v in false_positives.values())
    if total_fp > 0:
        print(f"\n⚠️  WARNING: {total_fp} false positive(s) detected!")
        for triple, fps in false_positives.items():
            if fps:
                print(f"  {triple}: {fps}")
    else:
        print(f"\n✓ Zero false positives across all triples on TRUE problems")

if __name__ == '__main__':
    main()
