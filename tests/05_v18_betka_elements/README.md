# Test: v18a-e -- Incorporating Betka's Structural Analysis Elements

## Purpose

Systematically test whether structural analysis elements from Adam Betka's cheatsheet (separator tests, contradiction motifs, source-collapse lemmas, FALSE guards) can improve our magma-testing framework when added incrementally to v17.

## Cheatsheets Used

All included in this folder:

- **v18a.txt** -- v17 + separator tests (LP, RP, SET). Adds Check 1d to Step 1.
- **v18b.txt** -- v17 + contradiction motifs (C1, C2, C4, C6). Adds Check 1d with bare-source contradiction motifs.
- **v18c.txt** -- v17 + source-collapse lemmas. Adds Step 0 before Step 1 with canonical form matching.
- **v18d.txt** -- v17 + FALSE guards (G1-G4). Adds Step 1.5 with feature-based FALSE guards.
- **v18e.txt** -- v17 + combined separator + collapse + guards. Adds separator tests (1d), source-collapse (Step 0), and FALSE guards (Step 1.5).

## Datasets

- **hard3_400**: 400 problems from the hard3 dataset (same set used for v16/v17 testing)

## Results

### Hard3 400 Comparison

| Version | Accuracy | F1 Score | Unparsed | Notes |
|---------|----------|----------|----------|-------|
| **v17 (baseline)** | **63.5%** | **0.628** | 11 | No Betka elements |
| v18a (+separators) | 58.1% | 0.540 | -- | LP, RP, SET tests |
| v18b (+contradiction motifs) | 56.8% | 0.538 | -- | C1, C2, C4, C6 |
| v18c (+source-collapse) | 58.1% | 0.600 | 28 | High unparsed count |
| v18d (+FALSE guards) | 51.5% | 0.510 | -- | G1-G4 guards |
| v18e (combined) | 55.5% | 0.582 | -- | Separators + collapse + guards |

### Key Observations

- **All v18 variants performed worse than v17** (63.5%)
- v18d (FALSE guards) was the worst at 51.5% -- the guards were too aggressive
- v18c had 28 unparsed responses -- the source-collapse lemmas added enough complexity to cause token exhaustion
- v18e (combined) did not recover -- combining multiple Betka elements did not produce synergy
- v18c had the best F1 among v18 variants (0.600) but still below v17

## Conclusions

1. **Betka's structural rules do not help when grafted onto our magma-testing framework.** Every variant regressed from v17's 63.5%.
2. **The approaches may be fundamentally incompatible for small models.** Betka's rules are designed for deterministic feature computation (separator tests, motif matching), while our approach relies on Haiku actually testing specific magmas. Adding both creates cognitive overload without synergy.
3. **FALSE guards were particularly harmful** (v18d at 51.5%). They fired too aggressively on hard3, producing false negatives.
4. **Source-collapse lemmas caused token exhaustion** (28 unparsed in v18c). The normalization and pattern matching steps are too complex for Haiku to execute reliably within token limits.
5. **Betka's approach is better suited to a deterministic solver** that can compute features exactly. Haiku makes errors in feature computation (especially variable counting and parity checks), which causes rule misfires.
6. **The 10KB budget is a real constraint.** Adding Betka elements consumes bytes that could be spent on additional magmas or better examples, which have proven more effective.
