#!/usr/bin/env python3
"""
Diagnose FP errors from a results file by brute-force CE search.
For each FP (model said TRUE, answer is FALSE), search all 2- and 3-element
magmas for a counterexample, then categorize:
  (a) CE found in battery magma    -> model arithmetic error
  (b) CE found outside battery     -> coverage gap
  (c) No CE in 2- or 3-element     -> hard problem, needs bigger magma
"""
import json, itertools, sys
from collections import defaultdict

# ── expression parser ──────────────────────────────────────────────────────────
def parse_expr(s):
    """Parse 'x * (y * z)' into ('*', 'x', ('*', 'y', 'z'))"""
    s = s.strip()
    depth = 0
    for i in range(len(s)-1, -1, -1):
        if s[i] == ')': depth += 1
        elif s[i] == '(': depth -= 1
        elif depth == 0 and s[i] == '*' and i > 0 and s[i-1] == ' ':
            return ('*', parse_expr(s[:i-1]), parse_expr(s[i+2:]))
    if s.startswith('(') and s.endswith(')'):
        return parse_expr(s[1:-1])
    return s  # bare variable

def eval_expr(expr, env, table, n):
    if isinstance(expr, str):
        return env[expr]
    _, l, r = expr
    lv = eval_expr(l, env, table, n)
    rv = eval_expr(r, env, table, n)
    return table[lv * n + rv]

def parse_equation(eq):
    lhs, rhs = eq.split(' = ', 1)
    return parse_expr(lhs.strip()), parse_expr(rhs.strip())

def get_vars(expr):
    if isinstance(expr, str):
        return {expr}
    return get_vars(expr[1]) | get_vars(expr[2])

def equation_holds_as_law(lhs, rhs, table, n, variables):
    """Check if equation holds for ALL assignments."""
    for vals in itertools.product(range(n), repeat=len(variables)):
        env = dict(zip(variables, vals))
        if eval_expr(lhs, env, table, n) != eval_expr(rhs, env, table, n):
            return False
    return True

def equation_fails_somewhere(lhs, rhs, table, n, variables):
    """Return a failing assignment, or None if always holds."""
    for vals in itertools.product(range(n), repeat=len(variables)):
        env = dict(zip(variables, vals))
        if eval_expr(lhs, env, table, n) != eval_expr(rhs, env, table, n):
            return dict(zip(variables, vals))
    return None

def find_ce(eq1_lhs, eq1_rhs, eq2_lhs, eq2_rhs, table, n, all_vars):
    if not equation_holds_as_law(eq1_lhs, eq1_rhs, table, n, all_vars):
        return None  # EQ1 doesn't hold as law in this magma
    fail = equation_fails_somewhere(eq2_lhs, eq2_rhs, table, n, all_vars)
    return fail  # None if EQ2 also holds, else the failing assignment

# ── battery magmas ─────────────────────────────────────────────────────────────
def make_battery():
    battery = {}
    # 2-element (n=2)
    battery['A2'] = (2, [0,0,0,0])   # zero
    battery['B2'] = (2, [0,1,0,1])   # right proj
    battery['C2'] = (2, [0,0,1,1])   # left proj
    battery['D2'] = (2, [0,1,1,0])   # XOR
    battery['E2'] = (2, [1,1,1,1])   # constant 1
    battery['F2'] = (2, [1,0,1,0])   # negate-right
    battery['G2'] = (2, [0,1,1,0])   # addition mod 2 (same as XOR)
    # 3-element (n=3)
    battery['A3'] = (3, [0]*9)        # zero
    battery['B3'] = (3, [0,1,2]*3)    # right proj: x*y=y
    battery['C3'] = (3, [0,0,0,1,1,1,2,2,2])  # left proj: x*y=x
    battery['D3'] = (3, [0,1,2,1,2,0,2,0,1])  # x+y mod 3 (XOR-like)
    battery['E3'] = (3, [1]*9)        # constant 1
    battery['F3'] = (3, [2,1,0,2,1,0,2,1,0])  # negate-right: 2-y
    battery['G3'] = (3, [0,1,2,1,2,0,2,0,1])  # addition mod 3
    battery['H3'] = (3, [1,2,0,1,2,0,1,2,0])  # right-shift: (y+1)%3
    battery['I3'] = (3, [1,1,1,2,2,2,0,0,0])  # left-shift: (x+1)%3
    # Step 3: linear 2x+y mod 3
    battery['Step3'] = (3, [(2*x+y)%3 for x in range(3) for y in range(3)])
    # J: Null-left [[0,0,0],[2,1,1],[1,2,2]]
    battery['J3'] = (3, [0,0,0,2,1,1,1,2,2])
    # K: Swap-row2 [[0,1,2],[0,1,2],[1,0,2]]
    battery['K3'] = (3, [0,1,2,0,1,2,1,0,2])
    # L: Near-zero: 0*2=1, else 0
    battery['L3'] = (3, [0,0,1,0,0,0,0,0,0])
    return battery

BATTERY = make_battery()
BATTERY_NAMES = set(BATTERY.keys())

# ── main ───────────────────────────────────────────────────────────────────────
def diagnose(results_file):
    d = json.load(open(results_file))
    items = list(d['results'].values()) if isinstance(d['results'], dict) else d['results']
    fps = [r for r in items if r.get('verdict') == 'TRUE' and r['answer'] == False]
    print(f"Diagnosing {len(fps)} FPs from {results_file}")
    print()

    cat_a = []  # CE in battery
    cat_b = []  # CE outside battery (but in 2- or 3-element)
    cat_c = []  # No CE found in 2- or 3-element magmas
    b_magma_hits = defaultdict(int)
    new_magma_hits = defaultdict(int)

    for r in fps:
        eq1 = r['equation1']
        eq2 = r['equation2']
        try:
            eq1_lhs, eq1_rhs = parse_equation(eq1)
            eq2_lhs, eq2_rhs = parse_equation(eq2)
        except Exception as e:
            print(f"  Parse error on {r['id']}: {e}")
            cat_c.append((r, None, None))
            continue

        all_vars = sorted(get_vars(eq1_lhs) | get_vars(eq1_rhs) |
                          get_vars(eq2_lhs) | get_vars(eq2_rhs))

        found_in_battery = None
        found_outside = None

        # Check battery magmas first
        for name, (n, table) in BATTERY.items():
            ce = find_ce(eq1_lhs, eq1_rhs, eq2_lhs, eq2_rhs, table, n, all_vars)
            if ce is not None:
                found_in_battery = (name, n, table, ce)
                b_magma_hits[name] += 1
                break

        if found_in_battery:
            cat_a.append((r, found_in_battery))
            continue

        # Search all 2-element magmas
        for table in itertools.product(range(2), repeat=4):
            ce = find_ce(eq1_lhs, eq1_rhs, eq2_lhs, eq2_rhs, list(table), 2, all_vars)
            if ce is not None:
                found_outside = ('2-element', 2, list(table), ce)
                new_magma_hits[str(list(table))] += 1
                break

        if found_outside:
            cat_b.append((r, found_outside))
            continue

        # Search all 3-element magmas
        for table in itertools.product(range(3), repeat=9):
            ce = find_ce(eq1_lhs, eq1_rhs, eq2_lhs, eq2_rhs, list(table), 3, all_vars)
            if ce is not None:
                found_outside = ('3-element', 3, list(table), ce)
                new_magma_hits[str(list(table))] += 1
                break

        if found_outside:
            cat_b.append((r, found_outside))
        else:
            cat_c.append((r, None, None))

    print(f"=== RESULTS ===")
    print(f"(a) CE in battery magma (model arithmetic error): {len(cat_a)}")
    print(f"(b) CE outside battery (coverage gap):            {len(cat_b)}")
    print(f"(c) No CE in 2- or 3-element magmas:             {len(cat_c)}")
    print()

    if cat_a:
        print("--- Category (a): Battery magmas that SHOULD have been found ---")
        for name, cnt in sorted(b_magma_hits.items(), key=lambda x: -x[1]):
            print(f"  {name}: {cnt} problems")
        print()
        print("  Sample problems:")
        for r, (name, n, table, ce) in cat_a[:5]:
            print(f"  {r['id']}: EQ1={r['equation1']}  EQ2={r['equation2']}")
            print(f"    CE in {name}, assignment={ce}")

    if cat_b:
        print()
        print("--- Category (b): New magmas needed ---")
        # Find most common new magma tables
        from collections import Counter
        table_counts = Counter()
        for r, (name, n, table, ce) in cat_b:
            table_counts[str(table)] += 1
        print(f"  Distinct new magma tables: {len(table_counts)}")
        print(f"  Top tables by coverage:")
        for tbl, cnt in table_counts.most_common(10):
            print(f"    {tbl}: covers {cnt} problems")
        print()
        print("  Sample problems:")
        for r, (name, n, table, ce) in cat_b[:5]:
            print(f"  {r['id']}: EQ1={r['equation1']}  EQ2={r['equation2']}")
            print(f"    CE in new {n}-element magma {table}, assignment={ce}")

    if cat_c:
        print()
        print("--- Category (c): No CE in 2- or 3-element magmas ---")
        print("  Sample problems:")
        for r, _, _ in cat_c[:10]:
            print(f"  {r['id']}: EQ1={r['equation1']}  EQ2={r['equation2']}")

    return cat_a, cat_b, cat_c

if __name__ == '__main__':
    fname = sys.argv[1] if len(sys.argv) > 1 else 'results/haiku_v13a_hard3.json'
    diagnose(fname)
