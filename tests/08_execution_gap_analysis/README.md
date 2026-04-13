# Test: Execution Gap Analysis

## Purpose

Understand why Haiku misses problems where our magma battery theoretically contains a counterexample. This analysis distinguishes between "coverage gaps" (we do not have the right magma) and "execution gaps" (we have the right magma but Haiku fails to use it correctly).

## Cheatsheets Used

- **cheatsheet_v17.txt** (primary analysis target)
- Brute-force search used external computation, not cheatsheet-based

## Datasets

- **hard3**: 400 problems (subset: 266 FALSE problems requiring counterexamples)
- **hard_order5**: 327 problems (subset: 266 FALSE problems requiring counterexamples)
- Combined: **532 FALSE problems** analyzed

## Results

### Phase 1: Coverage Analysis (Brute-Force Search)

Exhaustively searched all magmas of small order against 532 FALSE problems:
- All 16 magmas on 2 elements (order 2)
- All 19,683 magmas on 3 elements (order 3)
- Structured 4-element magmas (selected families)

| Category | Count | Percentage |
|----------|-------|------------|
| Have a small-order CE | 179 | 34% |
| Uncoverable (need larger magmas) | 353 | 66% |

Of the 179 coverable problems:
- Our existing battery catches **133** in theory
- Real gap for new magmas: **46 problems** that have small-order CEs not in our battery

### Phase 2: Execution Gap (v17 on hard3)

Of the 133 problems our battery covers in theory, v17 actually catches only **95**.

**Execution gap: 37 problems on hard3** where Haiku has the right magma but fails to use it.

### Execution Gap Breakdown

| Error Category | Count | Percentage |
|---------------|-------|------------|
| Singleton signal misfires (Magma D fires too early) | ~16 | 44% |
| Arithmetic errors on 3-element magmas | ~16 | 44% |
| EQ2 arithmetic errors | ~4 | 11% |

### Singleton Signal Tradeoff

The singleton signal (Magma D/left-projection forcing x=y) is a double-edged sword:
- **+68 true positives** gained from singleton signal
- **-45 false positives** caused by singleton signal misfires
- **Net: +23 problems** on hard3

This means the singleton signal is net positive but with a high error rate.

### Cognitive Load Finding

**Key finding**: Haiku correctly evaluates Magma H (right-shift on Z/3Z) in isolation but fails under the cognitive load of the full cheatsheet. When given just Magma H and a single problem, Haiku computes correctly. When running the full 12-magma battery, Haiku makes arithmetic errors on Magma H.

**This is a load problem, not a capability problem.** Haiku can do the math but loses accuracy when juggling 12 magmas, structural checks, and decision logic simultaneously.

### Phase 2: New Magma Candidates

Top new magmas identified from brute-force search:
- **Right-f permutation cycles**: Magmas where x*y applies a fixed permutation to y (ignoring x). These are generalizations of Magma H.
- **Left-f permutation cycles**: Magmas where x*y applies a fixed permutation to x (ignoring y). These are generalizations of Magma I.
- These are teachable patterns that follow the same evaluation logic as existing H/I magmas but with different permutations.

## Conclusions

1. **Two roughly equal improvement paths exist**:
   - **Fix execution of existing magmas (~37 problems)**: Reduce arithmetic errors and singleton misfires. This is a prompting/cognitive-load challenge.
   - **Add new magmas (~46 problems)**: Include additional small-order magmas that cover currently uncoverable problems. This is a content/budget challenge.

2. **Both paths are limited by the 10KB budget.** Adding new magmas requires bytes for their definitions and evaluation rules. Fixing execution may require simplifying existing content to reduce cognitive load.

3. **The 66% uncoverable rate is a hard ceiling** for small-magma approaches. Two-thirds of FALSE problems in hard3+hard_order5 require magmas larger than order 3-4.

4. **The cognitive load problem suggests a quality-over-quantity approach** may be better: fewer magmas executed more reliably could outperform more magmas executed with errors.

5. **The singleton signal tradeoff (+68 TP, -45 FP, net +23)** suggests it is worth keeping but could benefit from tighter triggering conditions.

6. **Right-f and left-f permutation cycles are the most promising new magma candidates**, as they follow patterns Haiku already knows how to evaluate (from Magma H and I).
