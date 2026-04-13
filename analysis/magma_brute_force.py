#!/usr/bin/env python3 -u
"""
Phase 1: Brute-force counterexample search.

For each FALSE problem we're currently missing, find ALL small-order magmas
that serve as counterexamples (EQ1 holds universally, EQ2 fails somewhere).

Search space:
  - All 2-element magmas (16)
  - All 3-element magmas (19,683)
  - Structured 4-element magmas (linear over Z/4, translation-invariant)

Output: results/phase1_ce_search.json with per-problem CE lists.
Incremental: resumes from existing output file.

Usage:
  python analysis/magma_brute_force.py --problems hard3_fps --output results/phase1_ce_search.json
  python analysis/magma_brute_force.py --problems hard3_all_false --output results/phase1_hard3_all.json
"""

import argparse, json, itertools, re, time, os
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent


# ── Equation parser ──────────────────────────────────────────────────────────

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
    lhs, rhs = s.split('=', 1)
    return parse(lhs.strip()), parse(rhs.strip())


def get_vars(s):
    return sorted(set(re.findall(r'[a-z]', s)))


# ── Magma enumeration ────────────────────────────────────────────────────────

def enumerate_magmas_2():
    """All 16 two-element magmas."""
    N = 2
    for flat in itertools.product(range(N), repeat=N*N):
        table = tuple(tuple(flat[i*N:(i+1)*N]) for i in range(N))
        yield ('2elem', table)


def enumerate_magmas_3():
    """All 19,683 three-element magmas."""
    N = 3
    for flat in itertools.product(range(N), repeat=N*N):
        table = tuple(tuple(flat[i*N:(i+1)*N]) for i in range(N))
        yield ('3elem', table)


def enumerate_magmas_4_structured():
    """Structured 4-element magmas: linear over Z/4, translation-invariant, simple permutation."""
    N = 4

    # Linear: x*y = (a*x + b*y) mod 4 for a,b in 0..3
    for a in range(N):
        for b in range(N):
            table = tuple(tuple((a*i + b*j) % N for j in range(N)) for i in range(N))
            yield ('4linear', table)

    # Translation-invariant: x*y = (x + f(y-x)) mod 4 for all functions f
    # This is 4^4 = 256 magmas
    for f in itertools.product(range(N), repeat=N):
        table = tuple(tuple((i + f[(j-i) % N]) % N for j in range(N)) for i in range(N))
        yield ('4trans', table)

    # Right-f: x*y = f(y) for all functions f
    for f in itertools.product(range(N), repeat=N):
        table = tuple(tuple(f[j] for j in range(N)) for i in range(N))
        yield ('4rightf', table)

    # Left-f: x*y = f(x)
    for f in itertools.product(range(N), repeat=N):
        table = tuple(tuple(f[i] for j in range(N)) for i in range(N))
        yield ('4leftf', table)


# ── Counterexample check ─────────────────────────────────────────────────────

def is_counterexample(parsed_problem, table, N):
    """Check if this magma is a CE: EQ1 holds universally AND EQ2 fails somewhere."""
    vars_, lhs1, rhs1, lhs2, rhs2 = parsed_problem
    domain = list(range(N))

    # EQ1 must hold for every assignment
    for vals in itertools.product(domain, repeat=len(vars_)):
        asgn = dict(zip(vars_, vals))
        if eval_tree(lhs1, asgn, table) != eval_tree(rhs1, asgn, table):
            return False

    # EQ2 must fail for some assignment
    for vals in itertools.product(domain, repeat=len(vars_)):
        asgn = dict(zip(vars_, vals))
        if eval_tree(lhs2, asgn, table) != eval_tree(rhs2, asgn, table):
            return True  # CE found

    return False  # EQ1 and EQ2 both hold, not a CE


# ── Problem source loaders ───────────────────────────────────────────────────

def load_problems(source):
    """Returns list of (id, eq1, eq2, answer) tuples."""
    if source == 'hard3_fps_v13a':
        # Problems where v13a said TRUE but answer is FALSE
        with open(ROOT / 'datasets/hard3.jsonl') as f:
            dataset = {json.loads(l)['id']: json.loads(l) for l in f}
        d = json.load(open(ROOT / 'results/v13a_hard3_rerun.json'))
        ids = [r['id'] for r in d['results'] if r.get('verdict')=='TRUE' and r['answer']==False]
        return [(pid, dataset[pid]['equation1'], dataset[pid]['equation2'], False) for pid in ids]

    if source == 'hard3_all_false':
        with open(ROOT / 'datasets/hard3.jsonl') as f:
            problems = [json.loads(l) for l in f if not json.loads(l)['answer']]
        return [(p['id'], p['equation1'], p['equation2'], False) for p in problems]

    if source == 'order5_all_false':
        with open(ROOT / 'datasets/hard_order5.jsonl') as f:
            problems = [json.loads(l) for l in f if not json.loads(l)['answer']]
        return [(p['id'], p['equation1'], p['equation2'], False) for p in problems]

    if source == 'hard3_order5_all_false':
        out = []
        for path in ['datasets/hard3.jsonl', 'datasets/hard_order5.jsonl']:
            with open(ROOT / path) as f:
                for line in f:
                    p = json.loads(line)
                    if not p['answer']:
                        out.append((p['id'], p['equation1'], p['equation2'], False))
        return out

    raise ValueError(f"Unknown source: {source}")


# ── Main search ──────────────────────────────────────────────────────────────

def run_search(problems, output_path, max_ces_per_problem=20):
    """For each problem, find CEs. Save incrementally."""
    # Load existing results if any
    if os.path.exists(output_path):
        existing = json.load(open(output_path))
        print(f"Resuming from {output_path}: {len(existing['results'])} problems already done")
    else:
        existing = {'results': {}, 'metadata': {}}

    # Pre-parse all problems
    parsed_problems = {}
    for pid, eq1, eq2, ans in problems:
        vars_ = get_vars(eq1 + eq2)
        lhs1, rhs1 = parse_eq(eq1)
        lhs2, rhs2 = parse_eq(eq2)
        parsed_problems[pid] = (vars_, lhs1, rhs1, lhs2, rhs2)

    # Decide which to process
    todo = [p for p in problems if p[0] not in existing['results']]
    print(f"Total: {len(problems)}, already done: {len(existing['results'])}, to do: {len(todo)}")

    # Magma generators with sizes
    magma_sources = [
        ('2elem', 2, enumerate_magmas_2, 16),
        ('3elem', 3, enumerate_magmas_3, 19683),
        ('4struct', 4, enumerate_magmas_4_structured, 4*16 + 256*3),
    ]

    # Process each problem
    for idx, (pid, eq1, eq2, ans) in enumerate(todo):
        start = time.time()
        parsed = parsed_problems[pid]
        nvars = len(parsed[0])

        ces_found = []  # list of (family, table) tuples
        stats = {'2elem': 0, '3elem': 0, '4struct': 0}

        for family_label, N, gen_func, total in magma_sources:
            for label, table in gen_func():
                if is_counterexample(parsed, table, N):
                    ces_found.append({'family': label, 'N': N, 'table': list(list(row) for row in table)})
                    stats[family_label] += 1
                    if len(ces_found) >= max_ces_per_problem:
                        break
            if len(ces_found) >= max_ces_per_problem:
                break

        elapsed = time.time() - start
        existing['results'][pid] = {
            'equation1': eq1,
            'equation2': eq2,
            'nvars': nvars,
            'ces_found': ces_found,
            'stats': stats,
            'elapsed_sec': round(elapsed, 2),
        }

        # Save after each problem
        with open(output_path, 'w') as f:
            json.dump(existing, f, indent=2)

        ce_count = len(ces_found)
        print(f"  [{idx+1}/{len(todo)}] {pid}: {ce_count} CEs found "
              f"(2elem:{stats['2elem']} 3elem:{stats['3elem']} 4struct:{stats['4struct']}) "
              f"in {elapsed:.1f}s", flush=True)

    # Final summary
    total_with_ce = sum(1 for r in existing['results'].values() if r['ces_found'])
    print(f"\nDone. {total_with_ce}/{len(existing['results'])} problems have at least one CE.")
    return existing


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--problems', required=True,
                   choices=['hard3_fps_v13a', 'hard3_all_false', 'order5_all_false', 'hard3_order5_all_false'])
    p.add_argument('--output', required=True)
    p.add_argument('--max-ces', type=int, default=100,
                   help='Stop searching a problem after finding this many CEs')
    args = p.parse_args()

    problems = load_problems(args.problems)
    print(f"Loaded {len(problems)} problems from {args.problems}")

    run_search(problems, args.output, max_ces_per_problem=args.max_ces)


if __name__ == '__main__':
    main()
