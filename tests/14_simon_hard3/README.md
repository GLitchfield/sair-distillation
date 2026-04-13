# Test: Simon's Community Cheatsheet on hard3

## Purpose
Benchmark SimonRJ's community cheatsheet against hard3 to compare with our own cheatsheets. Simon's sheet takes a fundamentally different approach: theory-focused (proof derivations, strict prohibitions against common reasoning errors) rather than our magma-battery approach.

## Cheatsheet Used
- `SimonRJ.txt` (5,190 bytes) — community submission from SimonRJ

### Key differences from our approach
- **No magma battery.** Simon's sheet tells the model to "try to find a small counterexample magma (sizes 2, 3, 4)" but doesn't provide specific pre-computed magmas with mental shortcuts.
- **Heavy guardrails.** ~60% of the sheet is "strict prohibitions" — warnings against common reasoning errors (assuming associativity, surjectivity, hand-waving, etc.).
- **Proof-focused TRUE strategy.** Relies on direct specialization, singleton collapse, and short local derivations rather than singleton signals from battery magmas.
- **No XOR/parity check, no balance criterion (Theorem 3.8), no linear magmas.**

## Dataset
- hard3.jsonl (400 problems)

## Results

| Metric | Simon | v17 (best submittable) | v13a rerun |
|--------|-------|------------------------|------------|
| Accuracy | 54.2% | 63.5% | 63.2% |
| F1 | 0.274 | 0.628 | 0.693 |
| TP | 34 | 120 | 166 |
| FP | 19 | 73 | 118 |
| FN | 161 | 69 | 29 |
| TN | 183 | 127 | 87 |
| Unparsed | 6 | 11 | 0 |
| Bytes | 5,190 | 6,922 | 10,823 |

## Analysis

### Simon's sheet heavily defaults FALSE (17.4% TRUE recall)
- 161 false negatives vs only 19 false positives — the model almost never says TRUE.
- This is only slightly better than the no-cheatsheet baseline (which says FALSE on everything, getting 50% on balanced datasets).
- Without specific magmas to test, Haiku can't reliably construct counterexamples or proofs on its own.

### The guardrails may be counterproductive
- The extensive "strict prohibitions" section (surjectivity, hand-waving, etc.) appears to make the model overly cautious.
- When in doubt, it defaults FALSE rather than attempting a proof — the opposite of our cheatsheets which over-predict TRUE.
- The "MOST IMPORTANT" section alone (~400 bytes) is dedicated to preventing a single reasoning error.

### Confirms the value of the magma battery
- Our sheets provide specific magmas with mental shortcuts (e.g., "B: x*y=y means expr → rightmost leaf"). This concrete machinery is what drives TRUE recall.
- Simon's approach of "try small counterexample magmas" without specifying which ones leaves Haiku unable to find counterexamples or detect singleton signals.

### Low FP count is notable
- Only 19 FPs (vs 73 for v17, 118 for v13a). Simon's conservative approach avoids false positives.
- Precision is 64.2% — comparable to ours, but achieved by rarely saying TRUE at all.

## Execution Notes
- Initial run (6 workers) was interrupted by API connection errors at ~12:07 UTC on Apr 7.
- 355/400 problems completed in the initial run; remaining 45 finished in a followup sequential run.
- Results aggregated from 6 chunk files + 1 missing-problems file.

## Conclusions
1. **The magma battery is our key differentiator.** Without it, Haiku defaults to FALSE on nearly everything.
2. **Guardrails alone don't help.** Preventing reasoning errors is less valuable than providing concrete test machinery.
3. **Simon's approach could complement ours** — his strict prohibitions might reduce our FP rate if selectively incorporated, but at the cost of bytes and potentially TRUE recall.
