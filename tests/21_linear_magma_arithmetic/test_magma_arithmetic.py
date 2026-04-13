#!/usr/bin/env python3
"""
Test Haiku's ability to do arithmetic in new linear magmas.
For each problem, ask: does EQ1 hold universally in this magma?
Compare Haiku's answer to the known ground truth.
"""

import json
import os
import sys
import time
import datetime

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
    """Ask Haiku to verify if an equation holds in a linear magma."""
    # Build the operation table
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

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY"); sys.exit(1)

    # Test cases: (equation, a, b, p, expected_holds)
    # Ground truth computed by our polynomial coefficient method
    test_cases = [
        # (2,2) mod 3 tests
        ("x = y * (y * (x * x))", 2, 2, 3, True),   # EQ1 of hard3_0017 - should hold
        ("x = (x * (y * z)) * x", 2, 2, 3, False),   # EQ2 of hard3_0017 - should fail
        ("x = y * ((y * y) * x)", 2, 2, 3, True),     # EQ1 of hard3_0026 - should hold
        ("x = ((y * y) * z) * (y * x)", 2, 2, 3, False), # EQ2 of hard3_0026 - should fail

        # (3,3) mod 5 tests
        ("x = y * ((y * x) * x)", 3, 3, 5, True),     # EQ1 of hard3_0025 - should hold
        ("x = (y * z) * ((y * y) * x)", 3, 3, 5, False), # EQ2 of hard3_0025 - should fail
        ("x = (x * (y * x)) * y", 3, 3, 5, True),     # EQ1 of hard3_0039 - should hold
        ("x = (x * x) * (x * (y * z))", 3, 3, 5, False), # EQ2 of hard3_0039 - should fail

        # Control: known easy cases
        ("x * y = y", 0, 1, 2, True),                  # right projection in right projection
        ("x * y = x", 0, 1, 2, False),                 # left projection in right projection
    ]

    print(f"Testing {len(test_cases)} cases...")
    print()

    correct = 0
    total = 0
    for eq, a, b, p, expected in test_cases:
        prompt = build_prompt(eq, a, b, p)
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        try:
            resp = call_haiku(prompt, api_key)
            # Parse HOLDS: YES or NO
            if "HOLDS: YES" in resp.upper() or "HOLDS:YES" in resp.upper():
                got = True
            elif "HOLDS: NO" in resp.upper() or "HOLDS:NO" in resp.upper():
                got = False
            else:
                got = None

            is_correct = got == expected
            if is_correct:
                correct += 1
            total += 1
            tag = "✓" if is_correct else "✗"
            exp_str = "HOLDS" if expected else "FAILS"
            got_str = "HOLDS" if got else ("FAILS" if got is not None else "UNPARSED")
            print(f"  {ts} {tag} ({a},{b})mod{p} | {eq[:40]:<40} | exp={exp_str} got={got_str}")
            if not is_correct:
                # Show last 200 chars of response for debugging
                print(f"       Response tail: ...{resp[-200:]}")
        except Exception as e:
            print(f"  {ts} ERROR: {e}")
            total += 1

        time.sleep(1)

    print(f"\nAccuracy: {correct}/{total} = {100*correct/total:.0f}%")
    print(f"  mod 3 cases: check above")
    print(f"  mod 5 cases: check above")

if __name__ == '__main__':
    main()
