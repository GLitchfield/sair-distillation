#!/usr/bin/env python3
"""
Test Haiku's arithmetic reliability on new linear magmas.
Runs each test case N times to measure consistency.
"""

import json
import os
import sys
import time
import datetime
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed

def call_haiku(prompt, api_key):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key, timeout=120.0)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4000,
        temperature=0.0,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text

def build_prompt(equation, a, b, p):
    table_lines = []
    for x in range(p):
        for y in range(p):
            val = (a * x + b * y) % p
            table_lines.append(f"  {x}*{y} = {val}")
    table = "\n".join(table_lines)

    return f"""You are testing whether an equation holds UNIVERSALLY in a specific magma.

Magma: {{0,1,...,{p-1}}} with operation x*y = ({a}x + {b}y) mod {p}

Operation table:
{table}

Equation to test: {equation}

Test this equation for ALL possible assignments of variables to {{0,1,...,{p-1}}}.
For each assignment, compute both sides step by step using the operation table.

After testing ALL assignments, answer:
HOLDS: YES or NO
If NO, give one specific assignment where it fails."""

def run_one(args):
    eq, a, b, p, expected, run_idx, api_key = args
    prompt = build_prompt(eq, a, b, p)
    try:
        resp = call_haiku(prompt, api_key)
        if "HOLDS: YES" in resp.upper() or "HOLDS:YES" in resp.upper():
            got = True
        elif "HOLDS: NO" in resp.upper() or "HOLDS:NO" in resp.upper():
            got = False
        else:
            got = None
        return (eq, a, b, p, expected, got, got == expected)
    except Exception as e:
        return (eq, a, b, p, expected, None, False)

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY"); sys.exit(1)

    N = 30

    test_cases = [
        # (equation, a, b, p, expected_holds, label)
        # mod 3
        ("x = y * (y * (x * x))", 2, 2, 3, True, "mod3 EQ1 holds"),
        ("x = (x * (y * z)) * x", 2, 2, 3, False, "mod3 EQ2 fails"),
        ("x = y * ((y * y) * x)", 2, 2, 3, True, "mod3 EQ1 holds"),
        ("x = ((y * y) * z) * (y * x)", 2, 2, 3, False, "mod3 EQ2 fails"),
        # mod 5
        ("x = y * ((y * x) * x)", 3, 3, 5, True, "mod5 EQ1 holds"),
        ("x = (y * z) * ((y * y) * x)", 3, 3, 5, False, "mod5 EQ2 fails"),
        ("x = (x * (y * x)) * y", 3, 3, 5, True, "mod5 EQ1 holds"),
        ("x = (x * x) * (x * (y * z))", 3, 3, 5, False, "mod5 EQ2 fails"),
    ]

    # Build all jobs
    jobs = []
    for eq, a, b, p, expected, label in test_cases:
        for i in range(N):
            jobs.append((eq, a, b, p, expected, i, api_key))

    print(f"Running {len(jobs)} total calls ({len(test_cases)} cases x {N} runs)...")
    print(f"Using 6 parallel workers")
    print()

    results = defaultdict(lambda: {"correct": 0, "wrong": 0, "unparsed": 0})

    completed = 0
    with ProcessPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(run_one, job): job for job in jobs}
        for future in as_completed(futures):
            eq, a, b, p, expected, got, is_correct = future.result()
            key = (eq, a, b, p, expected)
            if got is None:
                results[key]["unparsed"] += 1
            elif is_correct:
                results[key]["correct"] += 1
            else:
                results[key]["wrong"] += 1
            completed += 1
            if completed % 20 == 0:
                print(f"  {completed}/{len(jobs)} done...")

    print(f"\n{'='*80}")
    print(f"RESULTS ({N} runs per case)")
    print(f"{'='*80}")

    for eq, a, b, p, expected, label in test_cases:
        key = (eq, a, b, p, expected)
        r = results[key]
        total = r["correct"] + r["wrong"] + r["unparsed"]
        acc = r["correct"] / total if total else 0
        exp_str = "HOLDS" if expected else "FAILS"
        print(f"  ({a},{b})mod{p} | {label:20s} | {eq[:35]:35s} | acc={acc:.0%} ({r['correct']}/{total}) wrong={r['wrong']} unparsed={r['unparsed']}")

    # Summary by magma
    print()
    for mag_label, mag_a, mag_b, mag_p in [("mod 3 (2,2)", 2, 2, 3), ("mod 5 (3,3)", 3, 3, 5)]:
        total_correct = 0
        total_all = 0
        holds_correct = 0
        holds_all = 0
        fails_correct = 0
        fails_all = 0
        for eq, a, b, p, expected, label in test_cases:
            if a == mag_a and b == mag_b and p == mag_p:
                key = (eq, a, b, p, expected)
                r = results[key]
                t = r["correct"] + r["wrong"] + r["unparsed"]
                total_correct += r["correct"]
                total_all += t
                if expected:
                    holds_correct += r["correct"]
                    holds_all += t
                else:
                    fails_correct += r["correct"]
                    fails_all += t
        print(f"  {mag_label}: overall={total_correct}/{total_all} ({100*total_correct/total_all:.0f}%)  holds={holds_correct}/{holds_all} ({100*holds_correct/holds_all:.0f}%)  fails={fails_correct}/{fails_all} ({100*fails_correct/fails_all:.0f}%)")

if __name__ == '__main__':
    main()
