#!/usr/bin/env python3
"""
For each category-a FP (CE exists in battery, model said TRUE):
1. Did the model attempt to test the CE magma at all?
2. If yes — did it evaluate correctly or make an error?
3. If no — what reasoning led to early exit?
"""
import json, itertools, re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent

def parse_expr(s):
    s = s.strip()
    depth = 0
    for i in range(len(s)-1, -1, -1):
        if s[i] == ')': depth += 1
        elif s[i] == '(': depth -= 1
        elif depth == 0 and s[i] == '*' and i > 0 and s[i-1] == ' ':
            return ('*', parse_expr(s[:i-1]), parse_expr(s[i+2:]))
    if s.startswith('(') and s.endswith(')'): return parse_expr(s[1:-1])
    return s

def eval_expr(expr, env, table, n):
    if isinstance(expr, str): return env[expr]
    _, l, r = expr
    return table[eval_expr(l,env,table,n)*n + eval_expr(r,env,table,n)]

def get_vars(expr):
    if isinstance(expr, str): return {expr}
    return get_vars(expr[1]) | get_vars(expr[2])

def parse_eq(eq):
    lhs, rhs = eq.split(' = ', 1)
    return parse_expr(lhs.strip()), parse_expr(rhs.strip())

BATTERY = {
    'H3': (3, [1,2,0,1,2,0,1,2,0]),
    'I3': (3, [1,1,1,2,2,2,0,0,0]),
    'J3': (3, [0,0,0,2,1,1,1,2,2]),
    'K3': (3, [0,1,2,0,1,2,1,0,2]),
    'L3': (3, [0,0,1,0,0,0,0,0,0]),
    'F2': (2, [1,0,1,0]),
}

def find_ce_magma(eq1, eq2):
    """Return which battery magma has a CE, and the CE assignment."""
    lhs1,rhs1 = parse_eq(eq1)
    lhs2,rhs2 = parse_eq(eq2)
    all_vars = sorted(get_vars(lhs1)|get_vars(rhs1)|get_vars(lhs2)|get_vars(rhs2))
    for name, (n, table) in BATTERY.items():
        # Check EQ1 holds as law
        eq1_holds = all(
            eval_expr(lhs1,dict(zip(all_vars,v)),table,n)==eval_expr(rhs1,dict(zip(all_vars,v)),table,n)
            for v in itertools.product(range(n), repeat=len(all_vars))
        )
        if not eq1_holds: continue
        # Check EQ2 fails somewhere
        for v in itertools.product(range(n), repeat=len(all_vars)):
            env = dict(zip(all_vars,v))
            if eval_expr(lhs2,env,table,n) != eval_expr(rhs2,env,table,n):
                return name, env
    return None, None

# Detection patterns for each magma in response text
MAGMA_PATTERNS = {
    'H3': [r'magma h', r'right.?shift', r'right.?spine', r'\(y\+1\)\s*%\s*3', r'\(y\+1\)\s*mod\s*3'],
    'I3': [r'magma i', r'left.?shift', r'left.?spine', r'\(x\+1\)\s*%\s*3', r'\(x\+1\)\s*mod\s*3'],
    'J3': [r'magma j', r'null.?left', r'j3', r'1\*0\s*=\s*2'],
    'K3': [r'magma k', r'swap.?row', r'k3'],
    'L3': [r'magma l', r'near.?zero', r'l3', r'0\*2\s*=\s*1'],
    'F2': [r'magma f', r'negate.?right', r'1\s*-\s*y'],
}

def model_attempted_magma(response, magma_name):
    """Did the model's response mention/attempt this magma?"""
    resp_lower = response.lower()
    for pat in MAGMA_PATTERNS.get(magma_name, []):
        if re.search(pat, resp_lower):
            return True
    return False

def find_early_exit_reason(response):
    """What reasoning did the model use to conclude TRUE without finding a CE?"""
    resp_lower = response.lower()
    patterns = {
        'only_left_proj':   r'only (magma c|left proj|left.?projection)',
        'only_proj':        r'only (projection|proj) magmas? satisfy',
        'vacuous':          r'vacuously? true|vacuous implic',
        'singleton':        r'singleton',
        'trivial_models':   r'trivial model',
        'restrictive_eq1':  r'(highly|very|extremely) restrictive|so restrictive',
        'no_ce_default':    r'(no|not found|could not find|unable to find).{0,30}counterexample',
        'battery_complete': r'tested all magmas',
    }
    found = []
    for label, pat in patterns.items():
        if re.search(pat, resp_lower):
            found.append(label)
    return found if found else ['unknown']

# ── main ───────────────────────────────────────────────────────────────────────
d = json.load(open(ROOT / 'results/haiku_v13a_hard3.json'))
items = list(d['results'].values()) if isinstance(d['results'],dict) else d['results']
fps = [r for r in items if r.get('verdict')=='TRUE' and r['answer']==False]

# Find category-a FPs
cat_a = []
for r in fps:
    magma, ce = find_ce_magma(r['equation1'], r['equation2'])
    if magma is not None:
        cat_a.append((r, magma, ce))

print(f"Category-a FPs: {len(cat_a)}")
print()

# Classify each
skipped   = []   # model didn't attempt the CE magma
attempted = []   # model did attempt it

for r, magma, ce in cat_a:
    if model_attempted_magma(r['response'], magma):
        attempted.append((r, magma, ce))
    else:
        skipped.append((r, magma, ce))

print(f"Skipped CE magma entirely: {len(skipped)} ({len(skipped)/len(cat_a)*100:.0f}%)")
print(f"Attempted CE magma:        {len(attempted)} ({len(attempted)/len(cat_a)*100:.0f}%)")
print()

# Break down by magma
print("--- Skip/Attempt breakdown by magma ---")
by_magma = defaultdict(lambda: {'skip':0,'attempt':0})
for r,m,ce in skipped:   by_magma[m]['skip'] += 1
for r,m,ce in attempted: by_magma[m]['attempt'] += 1
for m in ['J3','K3','I3','L3','H3','F2']:
    s = by_magma[m]['skip']
    a = by_magma[m]['attempt']
    if s+a > 0:
        print(f"  {m}: {s+a} total  |  skipped={s}  attempted={a}")
print()

# For skipped: what reasoning led to early exit?
print("--- Early exit reasons (skipped cases) ---")
reason_counts = defaultdict(int)
for r, magma, ce in skipped:
    reasons = find_early_exit_reason(r['response'])
    for reason in reasons:
        reason_counts[reason] += 1
for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
    print(f"  {reason}: {count}")
print()

# For attempted: extract the section of response about that magma and show what happened
print("--- Attempted cases: sample responses around the CE magma ---")
for r, magma, ce in attempted[:8]:
    print(f"  {r['id']} | CE magma: {magma} | CE: {ce}")
    print(f"  EQ1: {r['equation1']}")
    print(f"  EQ2: {r['equation2']}")
    resp = r['response']
    # Find the magma section
    lines = resp.split('\n')
    magma_short = magma[0]  # H, I, J, K, L
    matches = [i for i,l in enumerate(lines) 
               if re.search(r'magma\s+'+magma_short+r'\b', l, re.IGNORECASE)
               or (magma=='J3' and re.search(r'null.?left', l, re.IGNORECASE))
               or (magma=='K3' and re.search(r'swap.?row', l, re.IGNORECASE))]
    if matches:
        start = matches[0]
        snippet = '\n'.join(lines[start:start+15])
    else:
        snippet = resp[-400:]
    print(f"  Response excerpt:\n{snippet}")
    print()
