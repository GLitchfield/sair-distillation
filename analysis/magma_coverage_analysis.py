#!/usr/bin/env python3
"""
Phase 2: Coverage analysis on Phase 1 results.

Takes a phase1 output JSON and computes:
  1. Per-magma coverage: how many problems each found CE magma covers
  2. Greedy set cover: minimal magma battery to cover all coverable problems
  3. Categorization of selected magmas into teachable families

Usage:
  python analysis/magma_coverage_analysis.py --input results/phase1_hard3_fps_v13a.json
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def table_key(table):
    """Canonical key for a magma table."""
    return tuple(tuple(row) for row in table)


def table_to_str(table, N):
    """Human-readable magma table."""
    rows = [' '.join(str(x) for x in row) for row in table]
    return f"{N}-elem: [" + ' | '.join(rows) + "]"


def classify_magma(table, N, family_hint):
    """Try to identify a pattern in the magma table."""
    t = table
    # Right projection check
    if all(t[i][j] == j for i in range(N) for j in range(N)):
        return "RIGHT_PROJECTION"
    # Left projection
    if all(t[i][j] == i for i in range(N) for j in range(N)):
        return "LEFT_PROJECTION"
    # Constant
    c = t[0][0]
    if all(t[i][j] == c for i in range(N) for j in range(N)):
        return f"CONSTANT_{c}"
    # Right-f: x*y depends only on y
    if all(t[0][j] == t[i][j] for i in range(N) for j in range(N)):
        f_vals = [t[0][j] for j in range(N)]
        return f"RIGHT_F: y→{f_vals}"
    # Left-f: x*y depends only on x
    if all(t[i][0] == t[i][j] for i in range(N) for j in range(N)):
        f_vals = [t[i][0] for i in range(N)]
        return f"LEFT_F: x→{f_vals}"
    # Linear over Z/N: x*y = (ax + by) mod N
    for a in range(N):
        for b in range(N):
            if all(t[i][j] == (a*i + b*j) % N for i in range(N) for j in range(N)):
                return f"LINEAR({a}x+{b}y mod {N})"
    # Translation-invariant: x*y = (x + f(y-x)) mod N
    f_candidate = tuple(t[0][j] for j in range(N))
    is_trans = all(t[i][j] == (i + f_candidate[(j-i) % N]) % N for i in range(N) for j in range(N))
    if is_trans:
        return f"TRANS(f={list(f_candidate)} mod {N})"
    return f"STRUCTURED_{family_hint}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--top', type=int, default=20, help='Top N magmas to display')
    p.add_argument('--output', default=None, help='Optional path to save analysis JSON')
    args = p.parse_args()

    data = json.load(open(args.input))
    results = data['results']

    print(f"{'='*70}")
    print(f"PHASE 2: Coverage Analysis")
    print(f"{'='*70}")
    print(f"Input: {args.input}")
    print(f"Total problems: {len(results)}")

    # Basic stats
    with_ce = [pid for pid, r in results.items() if r['ces_found']]
    without_ce = [pid for pid, r in results.items() if not r['ces_found']]
    print(f"Problems with at least one CE found: {len(with_ce)}")
    print(f"Problems with NO CE in search space: {len(without_ce)}")
    print(f"Ceiling: {len(with_ce)/len(results)*100:.1f}%")

    # Build magma → set of problems mapping
    magma_coverage = defaultdict(set)  # key: (N, table_tuple) → set of problem ids
    magma_family = {}  # key → family hint

    for pid, r in results.items():
        for ce in r['ces_found']:
            N = ce['N']
            key = (N, table_key(ce['table']))
            magma_coverage[key].add(pid)
            magma_family[key] = ce['family']

    print(f"Unique CE magmas found: {len(magma_coverage)}")
    print()

    # Top magmas by coverage
    ranked = sorted(magma_coverage.items(), key=lambda x: -len(x[1]))

    print(f"TOP {args.top} MAGMAS BY COVERAGE:")
    print(f"{'Rank':<5} {'N':<3} {'Cover':<7} {'Family':<12} {'Pattern':<40}")
    print(f"{'-'*70}")
    for rank, (key, probs) in enumerate(ranked[:args.top]):
        N, table = key
        pattern = classify_magma([list(row) for row in table], N, magma_family[key])
        print(f"{rank+1:<5} {N:<3} {len(probs):<7} {magma_family[key]:<12} {pattern[:40]}")
    print()

    # Greedy set cover
    print(f"GREEDY SET COVER:")
    print(f"{'-'*70}")
    coverable = set()
    for probs in magma_coverage.values():
        coverable |= probs

    remaining = set(coverable)
    selected = []
    available = dict(magma_coverage)
    step = 0

    while remaining and available and step < 50:
        best_key = max(available, key=lambda k: len(available[k] & remaining))
        gain = available[best_key] & remaining
        if not gain:
            break
        N, table = best_key
        pattern = classify_magma([list(row) for row in table], N, magma_family[best_key])
        print(f"  #{step+1}: +{len(gain):3d} new  (cumulative: {len(coverable)-len(remaining)+len(gain)}/{len(coverable)}) "
              f"{pattern[:50]}")
        selected.append({
            'rank': step+1,
            'N': N,
            'table': [list(row) for row in table],
            'pattern': pattern,
            'family': magma_family[best_key],
            'new_coverage': len(gain),
            'problems': sorted(gain),
        })
        remaining -= gain
        del available[best_key]
        step += 1

    print()
    print(f"After greedy selection:")
    print(f"  {len(selected)} magmas selected")
    print(f"  {len(coverable)-len(remaining)}/{len(coverable)} coverable problems covered")
    if remaining:
        print(f"  {len(remaining)} coverable problems not yet covered (would need >{step} magmas)")
    print(f"  {len(without_ce)} problems UNCOVERABLE in any search space magma")

    # Marginal gain analysis
    print()
    print(f"MARGINAL GAIN PROFILE:")
    print(f"  First 5 magmas cover: {sum(s['new_coverage'] for s in selected[:5])} problems")
    print(f"  First 10 magmas cover: {sum(s['new_coverage'] for s in selected[:10])} problems")
    print(f"  First 20 magmas cover: {sum(s['new_coverage'] for s in selected[:20])} problems")

    # Save analysis
    if args.output:
        output = {
            'input': args.input,
            'total_problems': len(results),
            'with_ce': len(with_ce),
            'without_ce': len(without_ce),
            'without_ce_ids': sorted(without_ce),
            'unique_magmas': len(magma_coverage),
            'top_magmas': [
                {
                    'rank': i+1,
                    'N': key[0],
                    'table': [list(row) for row in key[1]],
                    'pattern': classify_magma([list(row) for row in key[1]], key[0], magma_family[key]),
                    'coverage': len(probs),
                }
                for i, (key, probs) in enumerate(ranked[:args.top])
            ],
            'greedy_cover': selected,
        }
        with open(args.output, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"\nSaved analysis to {args.output}")


if __name__ == '__main__':
    main()
