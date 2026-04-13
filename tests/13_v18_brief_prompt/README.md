# Test: v18 with Brief Output Prompt

## Purpose
Test whether changing the output format to "brief" (inspired by SimonRJ's cheatsheet) reduces response length and unparsed responses without hurting accuracy.

## Cheatsheets Used
- cheatsheet_v18_briefPrompt.txt — v18 with output format changed to "REASONING: brief, PROOF: brief or empty, COUNTEREXAMPLE: brief or empty"

## Datasets
- hard3.jsonl (400 problems)

## Results

| Metric | v18 | v18_briefPrompt | v18_bailout |
|--------|-----|-----------------|-------------|
| Accuracy | 63.0% | 63.6% | 58.4% |
| F1 | 0.601 | 0.604 | 0.577 |
| TP | 106 | 106 | 113 |
| FP | 65 | 63 | 85 |
| FN | 76 | 76 | 81 |
| TN | 134 | 137 | 120 |
| Unparsed | 19 | 18 | 1 |

## Conclusions
- Slight improvement across the board compared to v18: fewer FPs, more TNs.
- Unparsed only dropped by 1 (19 → 18) — the "brief" format alone doesn't solve token exhaustion.
- Unlike the bailout instruction, the brief prompt didn't cause collateral damage to accuracy.
- The improvement is small and within run-to-run variance, but the direction is consistently positive.
