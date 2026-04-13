# Test: v19_novac Full Hard3 Run

## Purpose
Check for regressions from the anti-vacuous fix on the full hard3 dataset. Test 17 showed the fix improved accuracy from 23% to 76% on 5 targeted vacuous-FP problems. This test checks whether the fix causes collateral damage (new FNs from the model being too hesitant to say TRUE).

## Cheatsheet
- cheatsheet_v19_novac.txt (8,329 bytes) — v19 with Step 5 rule 4 changed from "TRIVIAL MODELS SIGNAL → TRUE" to "battery failure does NOT mean unsatisfiable, lean FALSE instead"

## Dataset
- hard3.jsonl (400 problems)

## Results

| Metric | v19 20k (test 16) | v19_novac (this test) | Delta |
|---|---|---|---|
| Accuracy | 66.7% | 59.5% | **-7.2** |
| F1 | 0.643 | 0.460 | -0.183 |
| TP | 120 | 69 | -51 |
| FP | 59 | 36 | -23 |
| FN | 74 | 126 | +52 |
| TN | 146 | 169 | +23 |
| Unparsed | 1 | 0 | -1 |

## Analysis

**Significant regression.** The fix killed TRUE recall — 73 new FNs vs 42 FPs fixed. Net -28 correct.

The instruction "lean FALSE instead" was too broad. It discouraged not just vacuous reasoning but also the legitimate singleton/trivial-models signal that drives many correct TRUE verdicts.

## Next Step
Created `datasets/dial_in_test.jsonl` — 40 problems (20 broken TPs + 20 fixed FPs) to iterate on more surgical wording that blocks vacuous reasoning without killing the singleton signal.
