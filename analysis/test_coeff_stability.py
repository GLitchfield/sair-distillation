#!/usr/bin/env python3
"""Test coefficient method reliability on mod-5 magma, 30 iterations."""

import os
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed

COEFF_PROMPT = """You are testing whether an equation holds UNIVERSALLY in a linear magma.

Magma: x*y = (3x + 3y) mod 5, on the set with elements 0,1,2,3,4.

SHORTCUT: In this magma, every expression evaluates to a linear combination of variables mod 5.
To check if an equation holds, compute the COEFFICIENT of each variable on both sides.

Rules for computing coefficients:
- A bare variable x has coefficient 1 for x, 0 for all others
- For an expression (A * B): coeff(x) = (3 * coeff_A(x) + 3 * coeff_B(x)) mod 5

WORKED EXAMPLE: Check x = y * (x * y)
  RHS inner: x * y -> coeff(x) = 3*1 + 3*0 = 3, coeff(y) = 3*0 + 3*1 = 3
  RHS outer: y * (x*y) -> coeff(x) = 3*0 + 3*3 = 9 mod 5 = 4, coeff(y) = 3*1 + 3*3 = 12 mod 5 = 2
  LHS: x -> coeff(x) = 1, coeff(y) = 0
  Compare: x: LHS=1 vs RHS=4 -> DIFFERENT -> equation FAILS.

Now check this equation: {eq}

Compute coefficients for each variable on LHS and RHS. Then answer:
HOLDS: YES or NO"""


def run_one(args):
    eq, expected, run_idx, api_key = args
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    prompt = COEFF_PROMPT.format(eq=eq)
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
        ).content[0].text
        if "HOLDS: YES" in resp.upper():
            got = True
        elif "HOLDS: NO" in resp.upper():
            got = False
        else:
            got = None
        return (eq, expected, got, got == expected)
    except Exception as e:
        return (eq, expected, None, False)


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY")
        sys.exit(1)

    test_cases = [
        ("x = y * ((y * x) * x)", True),
        ("x = (x * (y * x)) * y", True),
        ("x = (y * z) * ((y * y) * x)", False),
        ("x = (x * x) * (x * (y * z))", False),
    ]

    N = 30
    jobs = [(eq, exp, i, api_key) for eq, exp in test_cases for i in range(N)]

    print(f"Running {len(jobs)} calls (4 cases x {N} runs, 6 workers)...")

    results = defaultdict(lambda: {"correct": 0, "wrong": 0, "unparsed": 0})
    done = 0

    with ProcessPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(run_one, job): job for job in jobs}
        for future in as_completed(futures):
            eq, expected, got, is_correct = future.result()
            if got is None:
                results[(eq, expected)]["unparsed"] += 1
            elif is_correct:
                results[(eq, expected)]["correct"] += 1
            else:
                results[(eq, expected)]["wrong"] += 1
            done += 1
            if done % 20 == 0:
                print(f"  {done}/{len(jobs)}...")

    print()
    holds_correct = 0
    holds_total = 0
    fails_correct = 0
    fails_total = 0
    for eq, expected in test_cases:
        r = results[(eq, expected)]
        total = r["correct"] + r["wrong"] + r["unparsed"]
        acc = r["correct"] / total
        exp_s = "HOLDS" if expected else "FAILS"
        c = r["correct"]
        w = r["wrong"]
        u = r["unparsed"]
        print(f"  {exp_s:5s} | {eq:40s} | acc={acc:.0%} ({c}/{total}) wrong={w} unparsed={u}")
        if expected:
            holds_correct += r["correct"]
            holds_total += total
        else:
            fails_correct += r["correct"]
            fails_total += total

    print()
    total_c = holds_correct + fails_correct
    total_t = holds_total + fails_total
    print(f"HOLDS cases: {holds_correct}/{holds_total} ({100*holds_correct/holds_total:.0f}%)")
    print(f"FAILS cases: {fails_correct}/{fails_total} ({100*fails_correct/fails_total:.0f}%)")
    print(f"Overall: {total_c}/{total_t} ({100*total_c/total_t:.0f}%)")
    print()
    print("Compare to brute-force: HOLDS=0%, FAILS=100%")


if __name__ == "__main__":
    main()
