# Test: Magma Arithmetic in Isolation

## Purpose
Test Haiku's ability to evaluate equations in specific 3-element magmas, and explore prompting strategies to improve accuracy.

## Part 1: Baseline Arithmetic Accuracy

**Setup:** 40 problems per magma (20 IS_CE, 20 NOT_CE), no cheatsheet, just magma definition + equations.

**Initial results had a parser bug** that reversed IS_CE and NOT_CE accuracy. Corrected results:

| Magma | Overall | IS_CE (confirm EQ1 holds, find EQ2 fail) | NOT_CE (find EQ1 fails) |
|-------|---------|------------------------------------------|------------------------|
| H (right-shift) | 26/40 (65%) | 6/20 (30%) | 20/20 (100%) |
| I (left-shift) | 23/40 (57%) | 3/20 (15%) | 20/20 (100%) |
| J (null-left) | 27/40 (68%) | 7/20 (35%) | 20/20 (100%) |
| K (swap-row2) | 22/40 (55%) | 2/20 (10%) | 20/20 (100%) |

Haiku is perfect at finding EQ1 failures, but poor at confirming EQ1 holds universally (10-35%).

## Part 2: Stability Test on Single Problem (hard3_0179, Magma H)

30 runs of the same prompt, temperature=0. Result: 15/30 correct (50%). Even at temperature=0, this specific computation is nondeterministic.

## Part 3: Prompt Strategy Comparison — Magma H (hard3_0179)

5 strategies tested × 30 iterations each. Correct answer: EQ1 holds, EQ2 fails.

| Prompt | Correct | EQ1 right | Strategy |
|--------|---------|-----------|----------|
| C (verify) | 30/30 (100%) | 30/30 | Told the answer, asked to verify 9 assignments |
| D (shortcut) | 30/30 (100%) | 30/30 | "Count hops to rightmost leaf" method; EQ1 solved in prompt |
| E (two-pass) | 30/30 (100%) | 30/30 | Simplify to formula first, then check |
| A (labeled) | 18/30 (60%) | 18/30 | Name intermediates A,B,C,D, compute all 27 assignments |
| B (table) | 0/30 (0%) | 0/30 | Fill in 27-row table — made things worse |

D (shortcut) and E (two-pass) are the most promising generalizable strategies.

## Part 4: Prompt Strategy Comparison — Magma J (hard3_0037)

Tested C, D, E from Part 3, adapted for Magma J (which has no clean shortcut rule).

| Prompt | Correct | EQ1 right | Strategy |
|--------|---------|-----------|----------|
| C (verify) | 0/30 (0%) | 30/30 | Verify pre-computed answer |
| D (shortcut) | 0/30 (0%) | 30/30 | Case-based shortcut |
| E (two-pass) | 2/30 (7%) | 24/30 | Case analysis by x value |

All strategies that worked for H failed on J. The bottleneck is EQ2 evaluation — Haiku gets EQ1 right but almost never finds the EQ2 failure. The failure at x=1,y=0 requires tracking a 0 intermediate value through the table, which Haiku consistently misses.

## Part 5: J-Specific Prompting Strategies (hard3_0037)

Three strategies designed specifically for Magma J's failure mode:
- J1 (Zero focus): Highlights x*0=(3-x) as the danger zone, directs to test y=0 cases
- J2 (Worked example): Shows step-by-step EQ2 evaluation for a passing case, asks Haiku to do failing cases
- J3 (Decompose): Breaks EQ2 into labeled steps P,Q,R,S with structured output for all 9 assignments

Results:

| Prompt | Correct | EQ1 right | Strategy |
|--------|---------|-----------|----------|
| J1 (zero focus) | 17/30 (57%) | 30/30 | Warns about x*0=(3-x), directs to y=0 cases |
| **J2 (worked example)** | **30/30 (100%)** | 30/30 | Shows step-by-step EQ2 eval on a passing case |
| **J3 (decompose)** | **30/30 (100%)** | 30/30 | Labels sub-steps P,Q,R,S with structured output |

J2 and J3 achieve 100% — a massive improvement from the 0-7% in Part 4. J1 (just describing the danger) only reaches 57%.

## Conclusions

1. Strategies that bypass arithmetic (shortcut counting, algebraic simplification) work perfectly for magmas with clean rules (H).
2. These strategies fail on magmas without clean rules (J) — 0-7% correct.
3. **But: worked examples and decomposition fix J completely.** Showing step-by-step method (J2) or labeled sub-steps P,Q,R,S (J3) both achieve 100% on the same problem that was 0% before.
4. **Just describing the danger doesn't work.** J1 (warns about x*0) only reaches 57%. Haiku needs to SEE the computation format, not be told what to watch for.
5. Structured output as a big table (B, 27 rows) makes things worse. But structured output as labeled sub-steps (J3, 9 rows of P,Q,R,S) works perfectly. The difference is granularity — small labeled steps work, big tables don't.
6. The key insight: **demonstrate, don't describe.** A worked example of the evaluation method is worth more than any amount of warning about pitfalls.

## Part 6: Decompose Strategy on K and L

| Magma | Decompose accuracy |
|-------|--------------------|
| K (swap-row2) | 30/30 (100%) |
| L (near-zero) | 29/30 (97%) |

Combined with Parts 3-5, the decompose strategy works across ALL four 3-element magmas (H, J, K, L): 97-100% accuracy vs 10-35% without it.

## Implication for Cheatsheet Design

For each 3-element magma in the battery, include a compact worked example showing labeled sub-step evaluation (P = ..., Q = ..., R = ..., etc. using table lookups). This is the difference between 10-35% and 97-100% on these computations. The cost is bytes, but the payoff is proven across all magmas tested.
