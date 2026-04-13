"""
Enumerate all 3-element magmas and find which ones serve as counterexamples
for the 128 FP cases in v11. Report coverage — how many FP cases each magma explains.
"""
import json
import re
import itertools
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent

# ── load FP cases ──────────────────────────────────────────────────────────────
with open(ROOT / 'results/haiku_v11_hard3.json') as f:
    data = json.load(f)
with open(ROOT / 'datasets/hard3.jsonl') as f:
    dataset = {json.loads(l)['id']: json.loads(l) for l in f}

results = data['results']
fp_cases = [
    dataset[r['id']]
    for r in results
    if r['verdict'] == 'TRUE' and not dataset[r['id']]['answer']
]
print(f"FP cases to cover: {len(fp_cases)}")

# ── equation parser ────────────────────────────────────────────────────────────
def parse(expr):
    """Parse 'a * (b * c)' into a nested tuple tree ('*', a, b)."""
    expr = expr.strip()
    # find lowest-precedence * (outside all parens)
    depth = 0
    for i in range(len(expr) - 1, -1, -1):
        if expr[i] == ')': depth += 1
        elif expr[i] == '(': depth -= 1
        elif expr[i] == '*' and depth == 0:
            # check it's the operator, not part of a variable
            left  = expr[:i].rstrip()
            right = expr[i+1:].lstrip()
            if left and right:
                return ('*', parse(left), parse(right))
    # no operator found at top level — strip outer parens or return variable
    if expr.startswith('(') and expr.endswith(')'):
        return parse(expr[1:-1])
    return expr  # bare variable

def eval_tree(tree, assignment, table):
    if isinstance(tree, str):
        return assignment[tree]
    _, left, right = tree
    l = eval_tree(left,  assignment, table)
    r = eval_tree(right, assignment, table)
    return table[l][r]

def parse_equation(eq_str):
    lhs_s, rhs_s = eq_str.split('=', 1)
    return parse(lhs_s.strip()), parse(rhs_s.strip())

def get_vars(eq_str):
    return sorted(set(re.findall(r'[a-z]', eq_str)))

# pre-parse all FP cases
parsed = []
for case in fp_cases:
    vars_all = get_vars(case['equation1'] + case['equation2'])
    lhs1, rhs1 = parse_equation(case['equation1'])
    lhs2, rhs2 = parse_equation(case['equation2'])
    parsed.append((vars_all, lhs1, rhs1, lhs2, rhs2, case['id']))

# ── check one magma against all FP cases ──────────────────────────────────────
N = 3
domain = list(range(N))

def check_magma(table):
    """Return list of FP case IDs this magma can explain (EQ1 holds all, EQ2 fails some)."""
    covered = []
    for vars_all, lhs1, rhs1, lhs2, rhs2, cid in parsed:
        # check EQ1 holds for ALL assignments
        eq1_holds = True
        for vals in itertools.product(domain, repeat=len(vars_all)):
            asgn = dict(zip(vars_all, vals))
            if eval_tree(lhs1, asgn, table) != eval_tree(rhs1, asgn, table):
                eq1_holds = False
                break
        if not eq1_holds:
            continue
        # check EQ2 fails for SOME assignment
        eq2_fails = False
        for vals in itertools.product(domain, repeat=len(vars_all)):
            asgn = dict(zip(vars_all, vals))
            if eval_tree(lhs2, asgn, table) != eval_tree(rhs2, asgn, table):
                eq2_fails = True
                break
        if eq2_fails:
            covered.append(cid)
    return covered

# ── enumerate all 3-element magmas ────────────────────────────────────────────
# table[i][j] ∈ {0,1,2} for i,j ∈ {0,1,2} — 3^9 = 19683 magmas
coverage = {}  # table_key -> list of covered FP ids

total = 3**9
print(f"Enumerating {total} magmas...")

best_so_far = 0
for idx, flat in enumerate(itertools.product(range(N), repeat=N*N)):
    if idx % 2000 == 0:
        print(f"  {idx}/{total}  best coverage so far: {best_so_far}", flush=True)
    table = [list(flat[i*N:(i+1)*N]) for i in range(N)]
    covered = check_magma(table)
    if covered:
        coverage[flat] = covered
        if len(covered) > best_so_far:
            best_so_far = len(covered)

# ── report top magmas by coverage ─────────────────────────────────────────────
ranked = sorted(coverage.items(), key=lambda x: len(x[1]), reverse=True)

print(f"\nFound {len(coverage)} magmas that cover at least 1 FP case")
print(f"\nTop 20 by coverage:")
for flat, covered in ranked[:20]:
    table = [list(flat[i*N:(i+1)*N]) for i in range(N)]
    print(f"  {len(covered):3d} cases  table={table}")

# ── greedy set cover ──────────────────────────────────────────────────────────
print(f"\nGreedy set cover (how many magmas needed to cover all FP cases):")
all_fp_ids = set(c['id'] for c in fp_cases)
remaining = set(all_fp_ids)
selected = []
available = dict(ranked)

while remaining and available:
    best_flat = max(available, key=lambda f: len(set(available[f]) & remaining))
    gain = set(available[best_flat]) & remaining
    if not gain:
        break
    table = [list(best_flat[i*N:(i+1)*N]) for i in range(N)]
    print(f"  Magma {len(selected)+1}: covers {len(gain)} new cases  table={table}")
    selected.append((best_flat, gain))
    remaining -= gain
    del available[best_flat]

print(f"\nAfter greedy cover: {len(all_fp_ids)-len(remaining)}/{len(all_fp_ids)} FP cases covered")
print(f"Uncoverable by any 3-element magma: {len(remaining)} cases")
if remaining:
    print("Uncovered IDs:", sorted(remaining))
