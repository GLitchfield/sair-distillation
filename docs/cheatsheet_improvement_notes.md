# Cheatsheet Improvement Notes

Observations from testing v17/v18 on hard3, to revisit when building the next version.

## Singleton Detection (Step 1a vs Step 2 signal)

- Step 1a check itself works correctly — Haiku properly rejects non-singleton equations at this step.
- The misfires (20 on v18 hard3, 50% accuracy) come from TWO other sources:
  1. **Step 2 singleton signal**: Haiku tests Magma D (left projection), finds EQ1 forces x=y in that magma, declares "singleton signal → TRUE." But x=y in left projection doesn't always mean EQ1 forces singleton globally.
  2. **Step 5 "EQ1 is restrictive" heuristic**: When all magmas fail EQ1, Haiku reasons "EQ1 forces singleton/trivial structure → vacuously TRUE."
- Options: tighten Step 2 singleton signal (require 2+ magmas), or remove it entirely and only keep Step 1a.
- Singleton detection is worth 243/1000 correct on normal (100% accurate when it truly applies), but only 1/400 on hard3 and 0/654 on order5.

## Balance Check (Step 1c)

- Valid rule — 100% correct when it applies.
- But rarely triggers: 7/1000 on normal, 0/400 on hard3, 0/654 on order5.
- First candidate to cut if we need bytes. Worth ~7 correct on normal, 0 elsewhere.

## Step 4 (Algebraic Proof)

- Produces 49 verdicts at 67% accuracy on v18 hard3.
- Step 5 runs at 64%, so Step 4 is marginally better (+~2 correct answers).
- BUT: Step 4 is the main cause of token exhaustion — Haiku spins on rewrite attempts.
- 19 unparsed responses in v18, most from Step 4 spinning.
- Net effect may be negative: +2 correct from proofs, -19 from unparsed.
- Consider removing or severely limiting (e.g., "try ONE substitution only").

## 3-Element Magma Worked Examples

- Decompose strategy (labeled sub-steps P, Q, R with table lookups) tested at 97-100% in isolation on H, I, J, K, L.
- But v18 (which added these examples) showed no improvement over v17 on hard3 (63.0% vs 63.5%).
- Possible cause: the extra content increased token usage, causing more unparsed (19 vs 11).
- The examples help with arithmetic but the token cost may offset the gain.

## Verdict Source Analysis (v18 hard3)

| Source | Count | Accuracy | Notes |
|--------|-------|----------|-------|
| Step 2 magma CE | 161 (40%) | 63% | Core of the sheet |
| Step 5 judgment | 70 (18%) | 64% | Heuristic fallback |
| Step 4 proof | 49 (12%) | 67% | Marginal gain, high token cost |
| Step 3 linear | 39 (10%) | 67% | Useful |
| Step 1 singleton | 19 (5%) | 47% | All misfires on hard3 |
| Unparsed | 19 (5%) | 0% | Token exhaustion |
| Step 2 singleton signal | 13 (3%) | 38% | Unreliable |
| Step 1 disjoint | 8 (2%) | 88% | Small but reliable |
| Step 1 balance | 2 (1%) | 50% | Misfires — rule never applies on hard3 |
