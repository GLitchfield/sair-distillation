#!/usr/bin/env python3
"""
Check how many of the 179 coverable FALSE problems our existing
magma battery (A-L + linear Z/3Z) already catches.
"""

import json
import itertools
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# ── Parser ──
def parse(expr):
    expr = expr.strip()
    depth = 0
    for i in range(len(expr) - 1, -1, -1):
        if expr[i] == ')': depth += 1
        elif expr[i] == '(': depth -= 1
        elif expr[i] == '*' and depth == 0:
            left = expr[:i].rstrip()
            right = expr[i+1:].lstrip()
            if left and right:
                return ('*', parse(left), parse(right))
    if expr.startswith('(') and expr.endswith(')'):
        return parse(expr[1:-1])
    return expr

def eval_tree(tree, asgn, table):
    if isinstance(tree, str):
        return asgn[tree]
    _, l, r = tree
    return table[eval_tree(l, asgn, table)][eval_tree(r, asgn, table)]

def parse_eq(s):
    l, r = s.split('=', 1)
    return parse(l.strip()), parse(r.strip())

def get_vars(s):
    return sorted(set(re.findall(r'[a-z]', s)))


# ── Define existing battery ──
# 2-element magmas
def magma_A_zero(): return [[0,0],[0,0]]          # x*y=0
def magma_E_one(): return [[1,1],[1,1]]            # x*y=1
def magma_B_right(): return [[0,1],[0,1]]          # x*y=y
def magma_C_left(): return [[0,0],[1,1]]           # x*y=x
def magma_D_xor(): return [[0,1],[1,0]]            # x*y=(x+y)%2
def magma_G_add():
    # Addition is over integers but for tables we can represent mod N
    # For finite check, use mod 2 (which equals XOR)
    # Actually G is different from D — G requires same TOTAL count, not parity
    # On 2 elements with + mod something, it might coincide with XOR
    # Let me use Z/2 addition which is XOR
    return [[0,1],[1,0]]  # same as XOR
def magma_F_neg(): return [[1,1],[0,0]]            # x*y=1-y

# 3-element magmas
def magma_H_rshift():
    # x*y = (y+1) mod 3
    return [[(j+1)%3 for j in range(3)] for i in range(3)]
def magma_I_lshift():
    # x*y = (x+1) mod 3
    return [[(i+1)%3 for j in range(3)] for i in range(3)]
def magma_J_nullleft():
    # 0*y=0; x*y=x if x≠0,y≠0; x*y=(3-x) if x≠0,y=0
    t = [[0]*3 for _ in range(3)]
    for i in range(3):
        for j in range(3):
            if i == 0:
                t[i][j] = 0
            elif j == 0:
                t[i][j] = (3-i) % 3  # (3-i), but ensure valid {0,1,2}
            else:
                t[i][j] = i
    return t
def magma_K_swap():
    # x*y=y for x∈{0,1}; 2*0=1, 2*1=0, 2*2=2
    t = [[j for j in range(3)] for i in range(3)]  # row 0,1 = right projection
    t[2] = [1, 0, 2]
    return t
def magma_L_nearzero():
    # x*y=0 except 0*2=1
    t = [[0]*3 for _ in range(3)]
    t[0][2] = 1
    return t

# Linear 2x+y mod 3 (Step 3)
def magma_linear_2xy():
    return [[(2*i + j) % 3 for j in range(3)] for i in range(3)]


BATTERY = {
    'A (Zero 2-elem)': (2, magma_A_zero()),
    'E (Const-1 2-elem)': (2, magma_E_one()),
    'B (Right Proj)': (2, magma_B_right()),
    'C (Left Proj)': (2, magma_C_left()),
    'D (XOR)': (2, magma_D_xor()),
    'F (Neg-right)': (2, magma_F_neg()),
    'H (Right-shift +1 mod 3)': (3, magma_H_rshift()),
    'I (Left-shift +1 mod 3)': (3, magma_I_lshift()),
    'J (Null-left)': (3, magma_J_nullleft()),
    'K (Swap-row2)': (3, magma_K_swap()),
    'L (Near-zero)': (3, magma_L_nearzero()),
    'Linear 2x+y mod 3': (3, magma_linear_2xy()),
}


def is_ce(parsed, table, N):
    vars_, lhs1, rhs1, lhs2, rhs2 = parsed
    domain = list(range(N))
    # EQ1 holds everywhere
    for vals in itertools.product(domain, repeat=len(vars_)):
        asgn = dict(zip(vars_, vals))
        if eval_tree(lhs1, asgn, table) != eval_tree(rhs1, asgn, table):
            return False
    # EQ2 fails somewhere
    for vals in itertools.product(domain, repeat=len(vars_)):
        asgn = dict(zip(vars_, vals))
        if eval_tree(lhs2, asgn, table) != eval_tree(rhs2, asgn, table):
            return True
    return False


def main():
    # Load coverable problems from Phase 1
    phase1 = json.load(open(ROOT / 'results/phase1_all_false.json'))
    coverable = {pid: r for pid, r in phase1['results'].items() if r['ces_found']}
    print(f"Coverable problems from Phase 1: {len(coverable)}")

    # Check each against existing battery
    caught_by_existing = set()
    caught_by_magma = {name: set() for name in BATTERY}
    uncaught = set()

    for pid, r in coverable.items():
        vars_ = get_vars(r['equation1'] + r['equation2'])
        lhs1, rhs1 = parse_eq(r['equation1'])
        lhs2, rhs2 = parse_eq(r['equation2'])
        parsed = (vars_, lhs1, rhs1, lhs2, rhs2)

        caught = False
        for name, (N, table) in BATTERY.items():
            if is_ce(parsed, table, N):
                caught_by_magma[name].add(pid)
                caught = True
        if caught:
            caught_by_existing.add(pid)
        else:
            uncaught.add(pid)

    print(f"\nExisting battery (A-L + linear) on 179 coverable problems:")
    print(f"  Caught by existing battery: {len(caught_by_existing)} ({len(caught_by_existing)/len(coverable)*100:.0f}%)")
    print(f"  NOT caught (gap): {len(uncaught)} ({len(uncaught)/len(coverable)*100:.0f}%)")
    print()

    print("Per-magma coverage (of 179 coverable problems):")
    for name, pids in sorted(caught_by_magma.items(), key=lambda x: -len(x[1])):
        print(f"  {name:<30} {len(pids):>4}")

    # Save gap list
    with open(ROOT / 'results/phase2_gap_analysis.json', 'w') as f:
        json.dump({
            'total_coverable': len(coverable),
            'caught_by_existing': sorted(caught_by_existing),
            'gap_not_caught': sorted(uncaught),
            'per_magma_coverage': {name: sorted(pids) for name, pids in caught_by_magma.items()},
        }, f, indent=2)
    print(f"\nSaved gap analysis to results/phase2_gap_analysis.json")


if __name__ == '__main__':
    main()
