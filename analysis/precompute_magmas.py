"""
Precomputation: find which linear magmas (x*y = ax+by mod p) act as
counterexamples for Haiku's false positives on hard3.

A CE for (EQ1, EQ2) is a magma where EQ1 holds as a universal law
but EQ2 does NOT hold as a universal law.

For a linear magma x*y = ax+by mod p, an equation holds iff the
polynomial coefficients of both sides match for every variable.
"""

import json
from itertools import product
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent


# ── Expression tree ──────────────────────────────────────────────────────────

class Var:
    def __init__(self, name): self.name = name
    def __repr__(self): return self.name

class Op:
    def __init__(self, left, right): self.left = left; self.right = right
    def __repr__(self): return f"({self.left} * {self.right})"


def parse_term(tokens, pos):
    """Parse a single term: variable or (term * term).
    Inside parens, only a single * is allowed (no naked top-level * inside parens).
    """
    if tokens[pos] == '(':
        pos += 1  # consume '('
        left, pos = parse_term(tokens, pos)
        assert tokens[pos] == '*', f"Expected *, got {tokens[pos]}"
        pos += 1  # consume '*'
        right, pos = parse_term(tokens, pos)
        assert tokens[pos] == ')', f"Expected ), got {tokens[pos]}"
        pos += 1  # consume ')'
        return Op(left, right), pos
    else:
        # bare variable
        return Var(tokens[pos]), pos + 1


def parse_side(tokens, pos):
    """Parse one side of an equation: term, or term * term (one naked top-level op allowed)."""
    left, pos = parse_term(tokens, pos)
    if pos < len(tokens) and tokens[pos] == '*':
        pos += 1  # consume '*'
        right, pos = parse_term(tokens, pos)
        return Op(left, right), pos
    return left, pos


def parse_expr(tokens, pos):
    return parse_side(tokens, pos)


def tokenize(s):
    tokens = []
    i = 0
    while i < len(s):
        if s[i].isspace():
            i += 1
        elif s[i] in '()*=':
            tokens.append(s[i])
            i += 1
        else:
            # variable name (one or more word chars)
            j = i
            while j < len(s) and s[j].isalpha():
                j += 1
            tokens.append(s[i:j])
            i = j
    return tokens


def parse_equation(eq_str):
    """Parse 'lhs = rhs' string into (lhs_tree, rhs_tree, variables)."""
    tokens = tokenize(eq_str)
    eq_pos = tokens.index('=')
    lhs_tokens = tokens[:eq_pos]
    rhs_tokens = tokens[eq_pos+1:]

    lhs, _ = parse_side(lhs_tokens, 0)
    rhs, _ = parse_side(rhs_tokens, 0)

    # collect variables
    def collect_vars(node, acc):
        if isinstance(node, Var):
            acc.add(node.name)
        else:
            collect_vars(node.left, acc)
            collect_vars(node.right, acc)

    vars_ = set()
    collect_vars(lhs, vars_)
    collect_vars(rhs, vars_)
    return lhs, rhs, sorted(vars_)


# ── Linear magma satisfiability ──────────────────────────────────────────────

def poly_coeffs(node, variables, a, b, p):
    """
    For a linear magma x*y = ax+by mod p, compute the coefficient vector
    of the expression: returns dict {var: coeff mod p}.
    """
    if isinstance(node, Var):
        return {v: (1 if v == node.name else 0) for v in variables}
    else:
        lc = poly_coeffs(node.left, variables, a, b, p)
        rc = poly_coeffs(node.right, variables, a, b, p)
        return {v: (a * lc[v] + b * rc[v]) % p for v in variables}


def satisfies_linear(lhs, rhs, variables, a, b, p):
    """True iff linear magma ax+by mod p satisfies the equation."""
    lc = poly_coeffs(lhs, variables, a, b, p)
    rc = poly_coeffs(rhs, variables, a, b, p)
    return all(lc[v] == rc[v] for v in variables)


# ── Exhaustive small-magma CE check ─────────────────────────────────────────

def eval_tree(node, assignment, table, n):
    """Evaluate expression tree with concrete assignment in an arbitrary n-element magma."""
    if isinstance(node, Var):
        return assignment[node.name]
    else:
        l = eval_tree(node.left, assignment, table, n)
        r = eval_tree(node.right, assignment, table, n)
        return table[l][r]


def check_equation_in_magma(lhs, rhs, variables, table, n):
    """True iff the magma (given by n×n table) satisfies the equation universally."""
    for vals in product(range(n), repeat=len(variables)):
        assignment = dict(zip(variables, vals))
        if eval_tree(lhs, assignment, table, n) != eval_tree(rhs, assignment, table, n):
            return False
    return True


def linear_magma_table(a, b, p):
    """Build multiplication table for x*y = ax+by mod p."""
    return [[(a*x + b*y) % p for y in range(p)] for x in range(p)]


# ── Parameter sweep ──────────────────────────────────────────────────────────

# All (a,b,p) linear magmas to test
PARAMS = []
for p in [2, 3, 5]:
    for a in range(p):
        for b in range(p):
            PARAMS.append((a, b, p))

# Also label the ones we already have in the cheatsheet
KNOWN_MAGMAS = {
    (0, 0, 2): "Zero(F2)",
    (1, 0, 2): "LeftProj(F2)",
    (0, 1, 2): "RightProj(F2)",
    (1, 1, 2): "XOR(F2)",
    (1, 0, 3): "LeftProj(F3)",
    (0, 1, 3): "RightProj(F3)",
    (1, 1, 3): "Add(F3)",
    (2, 1, 3): "Linear-2x+y(F3)",  # Step 3 in cheatsheet
}


def find_linear_ce(lhs1, rhs1, lhs2, rhs2, variables1, variables2):
    """
    For each linear magma (a,b,p), check if it's a CE:
    EQ1 holds (universally) AND EQ2 fails (at least one assignment).
    Returns list of (a,b,p) that are CEs.
    """
    ces = []
    for (a, b, p) in PARAMS:
        table = linear_magma_table(a, b, p)
        eq1_holds = satisfies_linear(lhs1, rhs1, variables1, a, b, p)
        if not eq1_holds:
            continue
        # EQ1 holds — now check if EQ2 fails
        eq2_holds = satisfies_linear(lhs2, rhs2, variables2, a, b, p)
        if not eq2_holds:
            ces.append((a, b, p))
    return ces


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    # Load hard3 results for Haiku v8
    with open(ROOT / 'results/haiku_v8_hard3.json') as f:
        data = json.load(f)

    results = data['results']
    fp_cases = [r for r in results if r.get('answer') == False and r.get('verdict') == 'TRUE']
    fn_cases = [r for r in results if r.get('answer') == True and r.get('verdict') == 'FALSE']
    tn_cases = [r for r in results if r.get('answer') == False and r.get('verdict') == 'FALSE']

    print(f"Haiku v8 FP cases (FALSE but predicted TRUE): {len(fp_cases)}")
    print(f"Haiku v8 FN cases (TRUE but predicted FALSE): {len(fn_cases)}")
    print(f"Haiku v8 TN cases (correctly predicted FALSE): {len(tn_cases)}")
    print()

    # For each FP case, find which linear magmas are CEs
    param_counts = defaultdict(int)   # how many FP cases each param catches
    param_new_counts = defaultdict(int)  # how many FP cases each param catches that aren't caught by known magmas
    fp_coverage = []  # per-case results

    for r in fp_cases:
        eq1_str = r['equation1']
        eq2_str = r['equation2']
        lhs1, rhs1, vars1 = parse_equation(eq1_str)
        lhs2, rhs2, vars2 = parse_equation(eq2_str)
        all_vars = sorted(set(vars1) | set(vars2))
        # Use union of variables for both equations
        lhs1, rhs1, _ = parse_equation(eq1_str)
        lhs2, rhs2, _ = parse_equation(eq2_str)

        ces = find_linear_ce(lhs1, rhs1, lhs2, rhs2, all_vars, all_vars)
        known_ces = [c for c in ces if c in KNOWN_MAGMAS]
        new_ces = [c for c in ces if c not in KNOWN_MAGMAS]

        fp_coverage.append({
            'id': r['id'],
            'eq1': eq1_str,
            'eq2': eq2_str,
            'ces': ces,
            'known_ces': known_ces,
            'new_ces': new_ces,
            'any_ce_found': len(ces) > 0,
        })

        for c in ces:
            param_counts[c] += 1
        for c in new_ces:
            param_new_counts[c] += 1

    # Summary stats
    found = sum(1 for c in fp_coverage if c['any_ce_found'])
    found_new_only = sum(1 for c in fp_coverage if c['new_ces'] and not c['known_ces'])
    found_known = sum(1 for c in fp_coverage if c['known_ces'])
    not_found = sum(1 for c in fp_coverage if not c['any_ce_found'])

    print(f"=== CE Coverage of {len(fp_cases)} FP cases ===")
    print(f"  CE found (any linear magma):     {found}/{len(fp_cases)}")
    print(f"  CE found by KNOWN magmas:         {found_known}/{len(fp_cases)}")
    print(f"  CE found only by NEW magmas:      {found_new_only}/{len(fp_cases)}")
    print(f"  No CE found in any linear magma:  {not_found}/{len(fp_cases)}")
    print()

    # Rank params by how many FP cases they catch (new cases only)
    print("=== Top linear magmas by FP cases caught (ALL) ===")
    for (a, b, p), count in sorted(param_counts.items(), key=lambda x: -x[1])[:20]:
        label = KNOWN_MAGMAS.get((a,b,p), "NEW")
        print(f"  x*y = {a}x+{b}y mod {p}  [{label}]: {count} FP cases")

    print()
    print("=== Top NEW linear magmas by FP cases caught ===")
    for (a, b, p), count in sorted(param_new_counts.items(), key=lambda x: -x[1])[:15]:
        print(f"  x*y = {a}x+{b}y mod {p}: {count} FP cases")

    print()

    # Greedy coverage: which minimal set of new params covers the most cases?
    print("=== Greedy coverage: minimal new params to cover FP cases ===")
    uncovered = set(i for i, c in enumerate(fp_coverage) if not c['known_ces'] and c['new_ces'])
    print(f"FP cases not covered by known magmas but coverable by new: {len(uncovered)}")

    selected = []
    remaining = set(uncovered)
    # Build reverse index: param -> set of case indices it covers (among uncovered)
    param_covers = defaultdict(set)
    for i in uncovered:
        for c in fp_coverage[i]['new_ces']:
            param_covers[c].add(i)

    for _ in range(10):  # pick up to 10 new magmas
        if not remaining:
            break
        best = max(param_covers.keys(), key=lambda c: len(param_covers[c] & remaining), default=None)
        if best is None or len(param_covers[best] & remaining) == 0:
            break
        covered_now = param_covers[best] & remaining
        a, b, p = best
        print(f"  Add x*y = {a}x+{b}y mod {p}: covers {len(covered_now)} new cases (cumulative: {len(uncovered)-len(remaining)+len(covered_now)}/{len(uncovered)})")
        selected.append(best)
        remaining -= covered_now

    if remaining:
        print(f"  Remaining uncoverable by selected: {len(remaining)}")

    print()

    # Check: how many FP cases have NO CE in any linear magma at all?
    print("=== Cases with NO linear magma CE (need non-linear approach) ===")
    no_ce = [c for c in fp_coverage if not c['any_ce_found']]
    print(f"  Count: {len(no_ce)}")
    for c in no_ce[:5]:
        print(f"  {c['id']}: EQ1={c['eq1']}  EQ2={c['eq2']}")

    # Verify: do TN cases stay unaffected? (make sure new magmas don't break TRUE cases)
    print()
    print("=== Sanity check: do new magmas misfire on TRUE cases? ===")
    # Check TP cases (answer=True, verdict=TRUE) — new magmas should never be CEs
    tp_cases = [r for r in results if r.get('answer') == True and r.get('verdict') == 'TRUE']
    fn_cases_list = [r for r in results if r.get('answer') == True and r.get('verdict') == 'FALSE']
    all_true_cases = tp_cases + fn_cases_list

    misfires = defaultdict(int)
    for r in all_true_cases:
        lhs1, rhs1, vars1 = parse_equation(r['equation1'])
        lhs2, rhs2, vars2 = parse_equation(r['equation2'])
        all_vars = sorted(set(vars1) | set(vars2))
        ces = find_linear_ce(lhs1, rhs1, lhs2, rhs2, all_vars, all_vars)
        for c in ces:
            misfires[c] += 1

    if misfires:
        print("  WARNING: These params fire on TRUE cases (false CEs):")
        for (a,b,p), count in sorted(misfires.items(), key=lambda x: -x[1])[:10]:
            label = KNOWN_MAGMAS.get((a,b,p), "NEW")
            print(f"    x*y={a}x+{b}y mod {p} [{label}]: {count} TRUE cases flagged WRONG")
    else:
        print("  All clear — no linear magma fires on TRUE cases.")


if __name__ == '__main__':
    main()
