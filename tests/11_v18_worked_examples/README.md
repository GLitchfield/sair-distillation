# Test: v18 — Worked Examples for 3-Element Magmas

## Purpose
Test whether adding decompose-style worked examples (labeled sub-steps with table lookups) for all 3-element magmas (H, I, J, K, L) improves accuracy on hard3. This approach was proven to improve isolated magma arithmetic from 10-35% to 97-100% in Test 10.

## Cheatsheets Used
- cheatsheet_v18.txt (8,290 bytes) — v17 base + full operation tables and worked examples for H/I/J/K/L + role prime + Step 4 attempt limit

## Datasets
- hard3.jsonl (400 problems)

## Results

| Metric | v13a rerun | v17 | v18 |
|--------|-----------|-----|-----|
| Accuracy | 63.2% | 63.5% | 63.0% |
| F1 | 0.693 | 0.628 | 0.601 |
| TP | 166 | 120 | 106 |
| FP | 118 | 73 | 65 |
| FN | 29 | 69 | 76 |
| TN | 87 | 127 | 134 |
| Unparsed | 0 | 11 | 19 |

## Observations
- Accuracy is essentially unchanged from v17 (63.0% vs 63.5%)
- FPs decreased slightly (65 vs 73) — possible improvement in counterexample detection
- FNs increased slightly (76 vs 69)
- Unparsed nearly doubled (19 vs 11) — the additional worked examples add token load, causing more responses to hit the token limit before producing a verdict
- F1 dropped (0.601 vs 0.628) partly due to the unparsed responses counting as wrong

## Conclusions
The worked examples that were 97-100% effective in isolation (Test 10) did not translate to measurable improvement on the full hard3 test. Possible reasons:
- The added content increases token usage, causing more unparsed responses (19 vs 11)
- The worked examples help with arithmetic but may be displacing attention from other parts of the procedure
- The isolated test measured one specific computation per prompt; the full test requires managing 12+ magmas plus structural checks
- This is a single run — given the variance we've seen (v13a: 65.2% → 63.2%), the difference between v17 and v18 may not be meaningful
