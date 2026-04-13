#!/usr/bin/env python3
"""
Counterexample Gap Analysis
===========================
Finds 3-element magmas that can serve as counterexamples for hard3 FALSE
problems missed by our current 7-magma battery.

Two phases:
  1. Test a curated list of named 3-element magmas with simple formulas
  2. Systematic search over structured families (linear, projection-variants)
     then full exhaustive search if time permits

Usage: python analyze_ce_gap.py
"""

import json, itertools, time
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).resolve().parent.parent

# ── Expression evaluator ──────────────────────────────────────────────────────

def eval_expr(expr, op, assignment):
    """Recursively evaluate a magma expression tree.
    op is a list-of-lists: op[a][b] = a*b in the magma.
    assignment is a dict: variable -> element index.
    """
    expr = expr.strip()
    # Base: single variable
    if len(expr) == 1 and expr.isalpha():
        return assignment[expr]
    # Find top-level * (leftmost at depth 0)
    depth = 0
    for i, c in enumerate(expr):
        if c == '(':   depth += 1
        elif c == ')': depth -= 1
        elif c == '*' and depth == 0:
            lv = eval_expr(expr[:i], op, assignment)
            rv = eval_expr(expr[i+1:], op, assignment)
            return op[lv][rv]
    # Whole expression wrapped in parens
    if expr[0] == '(' and expr[-1] == ')':
        return eval_expr(expr[1:-1], op, assignment)
    raise ValueError(f"Cannot parse: {repr(expr)}")


def eq_vars(eq_str):
    return sorted(set(c for c in eq_str if c.isalpha()))


def satisfies(eq_str, op, n):
    """True if magma satisfies equation as a universal law."""
    lhs, rhs = eq_str.split(' = ', 1)
    vs = eq_vars(eq_str)
    for vals in itertools.product(range(n), repeat=len(vs)):
        asgn = dict(zip(vs, vals))
        if eval_expr(lhs, op, asgn) != eval_expr(rhs, op, asgn):
            return False
    return True


def violates(eq_str, op, n):
    """True if magma violates equation for some assignment."""
    lhs, rhs = eq_str.split(' = ', 1)
    vs = eq_vars(eq_str)
    for vals in itertools.product(range(n), repeat=len(vs)):
        asgn = dict(zip(vs, vals))
        if eval_expr(lhs, op, asgn) != eval_expr(rhs, op, asgn):
            return True
    return False


def is_ce(eq1, eq2, op, n=3):
    """True if magma is a valid counterexample: satisfies EQ1 but violates EQ2."""
    return satisfies(eq1, op, n) and violates(eq2, op, n)


# ── Load missed FALSE problems ────────────────────────────────────────────────

def load_missed_false():
    """Problems where answer=FALSE and at least one model said TRUE."""
    haiku_results  = {r['id']: r for r in json.load(open(BASE/'results/haiku_v5_hard3.json'))['results']}
    gemini_results = {r['id']: r for r in json.load(open(BASE/'results/gemini_v5_hard3.json'))['results']}

    missed, both_wrong = [], []
    for pid, row in haiku_results.items():
        if row['answer']:           # skip TRUE problems
            continue
        h_wrong = row.get('verdict') == 'TRUE'
        g_wrong = gemini_results.get(pid, {}).get('verdict') == 'TRUE'
        if h_wrong or g_wrong:
            entry = {
                'id': pid,
                'eq1': row['equation1'],
                'eq2': row['equation2'],
                'haiku_wrong': h_wrong,
                'gemini_wrong': g_wrong,
            }
            missed.append(entry)
            if h_wrong and g_wrong:
                both_wrong.append(entry)
    return missed, both_wrong


# ── Named candidate magmas ────────────────────────────────────────────────────

def op(fn, n=3):
    return [[fn(i, j) for j in range(n)] for i in range(n)]

NAMED = {
    # Simple order-based
    'min':               op(lambda x, y: min(x, y)),
    'max':               op(lambda x, y: max(x, y)),
    # Modular arithmetic
    'add_mod3':          op(lambda x, y: (x + y) % 3),
    'sub_mod3':          op(lambda x, y: (x - y) % 3),
    'mul_mod3':          op(lambda x, y: (x * y) % 3),
    'neg_right_mod3':    op(lambda x, y: (2 - y) % 3),       # Negate-right analogue
    'neg_left_mod3':     op(lambda x, y: (2 - x) % 3),
    # Linear (ax+by mod 3)
    'linear_1_2':        op(lambda x, y: (x + 2*y) % 3),     # complement to Step 3's (2x+y)
    'linear_2_2':        op(lambda x, y: (2*x + 2*y) % 3),
    # Conditional projections
    'left_nonzero':      op(lambda x, y: x if x > 0 else y), # left arg unless it's 0
    'right_nonzero':     op(lambda x, y: y if y > 0 else x), # right arg unless it's 0
    'left_if_larger':    op(lambda x, y: x if x >= y else y),
    'left_if_smaller':   op(lambda x, y: x if x <= y else y),
    # Difference / absolute
    'abs_diff':          op(lambda x, y: abs(x - y)),
    # Mixed zero-and-projection
    'zero_if_eq':        op(lambda x, y: 0 if x == y else y),  # 0 on diagonal, right-proj elsewhere
    'zero_if_neq':       op(lambda x, y: x if x == y else 0),  # x on diagonal, 0 elsewhere
    'right_cap1':        op(lambda x, y: min(y, 1)),            # right-proj capped at 1
    'left_cap1':         op(lambda x, y: min(x, 1)),
}


# ── Structured family search ──────────────────────────────────────────────────

def all_linear_mod3():
    """All linear magmas x*y = (a*x + b*y + c) % 3 for a,b,c in {0,1,2}."""
    magmas = {}
    for a, b, c in itertools.product(range(3), repeat=3):
        name = f'linear({a},{b},{c})'
        magmas[name] = op(lambda x, y, a=a, b=b, c=c: (a*x + b*y + c) % 3)
    return magmas


def all_projection_variants():
    """Right/left projection with one element behaving differently."""
    magmas = {}
    for override_x in range(3):
        for override_val in range(3):
            # Right projection everywhere, except row override_x → constant override_val
            table = [[j for j in range(3)] for _ in range(3)]  # right proj
            table[override_x] = [override_val] * 3
            magmas[f'rproj_override_row{override_x}={override_val}'] = table

            # Left projection everywhere, except col override_x → constant override_val
            table2 = [[i for j in range(3)] for i in range(3)]  # left proj
            for i in range(3):
                table2[i][override_x] = override_val
            magmas[f'lproj_override_col{override_x}={override_val}'] = table2
    return magmas


# ── Exhaustive search ─────────────────────────────────────────────────────────

def exhaustive_search(problems, n=3, time_limit_secs=120, top_k=20):
    """Try all n^(n^2) operation tables. Returns top_k by coverage."""
    total = n ** (n * n)
    print(f"\nExhaustive search: {total:,} possible {n}-element magmas "
          f"(time limit: {time_limit_secs}s)...")
    t0 = time.time()
    best = []   # list of (coverage_count, op_table, covered_ids)
    min_best = 0

    for idx, flat in enumerate(itertools.product(range(n), repeat=n*n)):
        if idx % 5000 == 0:
            elapsed = time.time() - t0
            pct = 100 * idx / total
            print(f"  {idx:>7,}/{total:,} ({pct:5.1f}%)  elapsed={elapsed:.0f}s  "
                  f"best_so_far={min_best}", end='\r')
            if elapsed > time_limit_secs:
                print(f"\n  Time limit reached at {idx:,}/{total:,} ({pct:.1f}%)")
                break

        table = [list(flat[i*n:(i+1)*n]) for i in range(n)]
        covered = [p['id'] for p in problems if is_ce(p['eq1'], p['eq2'], table)]
        count = len(covered)

        if count > min_best or len(best) < top_k:
            best.append((count, [row[:] for row in table], covered))
            best.sort(key=lambda x: -x[0])
            if len(best) > top_k:
                best = best[:top_k]
            min_best = best[-1][0] if best else 0

    print()
    return best


# ── Helpers ───────────────────────────────────────────────────────────────────

def describe_table(table):
    rows = ['  '.join(str(v) for v in row) for row in table]
    return ' | '.join(rows)


def check_named_match(table):
    for name, t in {**NAMED, **all_linear_mod3()}.items():
        if table == t:
            return name
    return None


def test_magma_set(name, magmas, problems):
    print(f"\n{'─'*60}")
    print(f"  {name}")
    print(f"{'─'*60}")
    results = []
    for mname, table in magmas.items():
        covered = [p['id'] for p in problems if is_ce(p['eq1'], p['eq2'], table)]
        results.append((len(covered), mname, table, covered))
    results.sort(reverse=True)
    shown = 0
    for count, mname, table, covered in results:
        if count == 0 and shown >= 5:
            break
        pct = 100 * count / len(problems) if problems else 0
        flag = ' ◄◄ BEST' if count == results[0][0] and count > 0 else ''
        print(f"  {mname:40s} {count:3d}/{len(problems)} ({pct:5.1f}%){flag}")
        shown += 1
    return results


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Loading missed FALSE problems...")
    missed, both_wrong = load_missed_false()
    print(f"  Total missed FALSE (at least one model wrong): {len(missed)}")
    print(f"  Both models wrong:  {len(both_wrong)}")
    print(f"  Haiku-only wrong:   {sum(p['haiku_wrong'] and not p['gemini_wrong'] for p in missed)}")
    print(f"  Gemini-only wrong:  {sum(p['gemini_wrong'] and not p['haiku_wrong'] for p in missed)}")

    # ── Phase 1: Named magmas ────────────────────────────────────────────────
    named_results = test_magma_set("PHASE 1: Named candidate magmas", NAMED, missed)

    # ── Phase 2: All linear magmas over Z/3Z ────────────────────────────────
    linear_results = test_magma_set(
        "PHASE 2: All linear magmas (ax+by+c) mod 3",
        all_linear_mod3(), missed)

    # ── Phase 3: Projection variants ────────────────────────────────────────
    proj_results = test_magma_set(
        "PHASE 3: Projection variants (one row/col overridden)",
        all_projection_variants(), missed)

    # Summary of best so far before exhaustive search
    all_phase1_3 = named_results + linear_results + proj_results
    all_phase1_3.sort(reverse=True)
    print(f"\n{'='*60}")
    print(f"  Best coverage before exhaustive search:")
    for count, mname, table, covered in all_phase1_3[:5]:
        pct = 100 * count / len(missed) if missed else 0
        print(f"  {mname:40s} {count}/{len(missed)} ({pct:.1f}%)")
        print(f"    Table: {describe_table(table)}")

    # ── Phase 4: Full exhaustive search ─────────────────────────────────────
    top = exhaustive_search(missed, n=3, time_limit_secs=180, top_k=20)

    print(f"\n{'='*60}")
    print(f"  TOP MAGMAS FROM EXHAUSTIVE SEARCH")
    print(f"{'='*60}")
    for i, (count, table, covered) in enumerate(top):
        pct = 100 * count / len(missed) if missed else 0
        match = check_named_match(table)
        match_str = f"  → matches: {match}" if match else ""
        print(f"\n#{i+1}: covers {count}/{len(missed)} ({pct:.1f}%){match_str}")
        print(f"  Table (row=left arg, col=right arg):")
        print(f"       y=0  y=1  y=2")
        for r, row in enumerate(table):
            print(f"  x={r}:  {row[0]}    {row[1]}    {row[2]}")
        # Check if it has a simple formula
        is_comm = all(table[i][j] == table[j][i] for i in range(3) for j in range(3))
        is_left_proj  = all(table[i][j] == i for i in range(3) for j in range(3))
        is_right_proj = all(table[i][j] == j for i in range(3) for j in range(3))
        props = []
        if is_comm:      props.append("commutative")
        if is_left_proj: props.append("= left-projection")
        if is_right_proj: props.append("= right-projection")
        if props:
            print(f"  Properties: {', '.join(props)}")
        print(f"  Covers: {covered}")

    # Both-wrong subset analysis
    print(f"\n{'='*60}")
    print(f"  COVERAGE ON 'BOTH MODELS WRONG' SUBSET ({len(both_wrong)} problems)")
    print(f"{'='*60}")
    for count, table, covered in top[:10]:
        both_covered = [pid for pid in covered if any(p['id'] == pid for p in both_wrong)]
        pct_both = 100 * len(both_covered) / len(both_wrong) if both_wrong else 0
        print(f"  Table {describe_table(table)} | both-wrong: {len(both_covered)}/{len(both_wrong)} ({pct_both:.1f}%)")

    print("\nDone.")


if __name__ == '__main__':
    main()
