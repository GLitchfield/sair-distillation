# Test: Order-5 Baseline

## Purpose

Establish baseline performance on the harder order-5 community problem set. Order-5 problems involve magmas on 5-element carrier sets, which are significantly harder than the order-2/3 problems in the normal and hard3 datasets.

## Cheatsheets Used

- **cheatsheet_v13a** (not copied here -- see main cheatsheets folder)
- **cheatsheet_v17.txt** (see tests/04_v17_repackaged/)

## Datasets

- **hard_order5**: 327 random problems (164 TRUE, 163 FALSE)

## Results

### Hard Order-5 (327 problems)

| Version | Accuracy | F1 Score | FP Rate on FALSE Cases |
|---------|----------|----------|----------------------|
| v13a | **55.7%** | 0.667 | ~77% |
| v17 | 49.7% | 0.602 | ~77% |

### Error Profile

- Both sheets have approximately **77% false positive rate on FALSE cases** -- meaning they incorrectly say TRUE on roughly 3 out of 4 FALSE problems
- Only **37 true negatives** between both sheets on FALSE cases -- they perform nearly identically on identifying FALSE order-5 problems
- The magma battery (order-2 and order-3 magmas) is **largely ineffective** at finding counterexamples for order-5 problems, because the counterexamples require order-5 magmas

### Why Order-5 Is Harder

- Counterexamples for FALSE order-5 problems typically require magmas with 5+ elements
- Our magma battery only tests magmas up to order 3 (elements {0,1,2})
- The structural checks (singleton, balance) still work but cover fewer cases
- The "EQ1 restrictive -> TRUE" heuristic fires more often, increasing FPs

## Conclusions

1. **Order-5 is significantly harder than hard3.** v13a drops from 63.2% to 55.7%, v17 drops from 63.5% to 49.7%.
2. **The magma battery barely helps on order-5.** The ~77% FP rate means the battery almost never finds a counterexample for FALSE order-5 problems.
3. **v13a holds up better than v17** on order-5 (55.7% vs 49.7%), suggesting v13a's decision logic handles the ambiguous cases slightly better.
4. **Improving order-5 performance would require order-5 magmas in the battery**, but these are too large to encode within the 10KB cheatsheet budget (a 5-element magma table has 25 entries).
5. **The 50% accuracy floor** (from always guessing one class) is barely exceeded, indicating that order-5 is near the ceiling of what a small-magma-battery approach can achieve.
