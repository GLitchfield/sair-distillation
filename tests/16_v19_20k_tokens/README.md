# Test: v19 with 20k Token Output Limit

## Purpose
Test whether raising max_tokens from 4,096 to 20,000 reduces unparsed responses and improves accuracy. Test 15 showed 29/400 unparsed, with 45% running out of tokens in Step 4 (proof attempts) and 14% in Step 5 (about to output a verdict). All persistent unparsed were `max_tokens` — genuine token exhaustion, not model-side bugs.

## Hypothesis
- Unparsed count should drop significantly (from ~29 to near 0)
- The 4 Step 5 cases that were about to output a verdict should now complete
- Accuracy may improve slightly from recovered responses, or stay flat if the extra space just lets the model ramble without reaching better conclusions

## Cheatsheet
- cheatsheet_v19.txt (8,271 bytes) — identical to v18_briefPrompt and test 15

## Code Change
- `run_test.py`: max_tokens raised from 4,096 to 20,000 for all providers

## Dataset
- hard3.jsonl (400 problems)

## Results

| Metric | v19 4k (test 15) | v19 20k (this test) | v17 | v13a rerun |
|--------|------------------|---------------------|-----|------------|
| Accuracy | 63.3% | **66.7%** | 63.5% | 63.2% |
| F1 | 0.602 | **0.643** | 0.628 | 0.693 |
| TP | 103 | 120 | 120 | 166 |
| FP | 60 | 59 | 73 | 118 |
| FN | 76 | 74 | 69 | 29 |
| TN | 132 | 146 | 127 | 87 |
| Unparsed | 29 | **1** | 11 | 0 |

## Analysis

### Unparsed virtually eliminated
Unparsed dropped from 29 to 1. The 4,096 token limit was the sole cause of the unparsed problem — with headroom, the model completes its reasoning and outputs a verdict.

### Accuracy jumped +3.4 points
66.7% is our best hard3 result on a submittable cheatsheet (<10KB). Net +31 correct vs test 15 (86 fixed, 55 broken — the broken are run-to-run variance, not caused by the token change).

### Run-to-run variance is massive
Only 62.8% of problems got the same verdict across the two runs (same cheatsheet, same model, temperature=0). 37.2% flipped. This means ~37% of problems are in an "unstable zone" where the model's answer depends on random factors. Of the 55 regressions, 31 flipped TRUE→FALSE and 24 flipped FALSE→TRUE — no directional bias.

### Error analysis: 133 wrong answers (59 FP + 74 FN)

#### False Positives (59): Model says TRUE when answer is FALSE

| Root cause | Count | % |
|---|---|---|
| All battery magmas satisfying EQ1 also satisfy EQ2 → infers TRUE | 31 | 53% |
| Vacuous: no battery magma satisfies EQ1 → "vacuously true" | 21 | 36% |
| Singleton signal from Magma D (left projection forces x=y) | 4 | 7% |
| Singleton signal from other source | 3 | 5% |

**The dominant FP pattern (89%):** The model tests EQ1 against the battery, finds it holds in only a few magmas (or none), observes EQ2 also holds in those same magmas, and concludes "every magma satisfying EQ1 also satisfies EQ2 → TRUE." This is logically wrong because the battery is finite — there exist magmas outside the battery where EQ1 holds but EQ2 doesn't. The model is generalizing from incomplete evidence.

The 21 "vacuous" FPs are a special case: EQ1 fails in all 12 battery magmas + linear magma, so the model concludes "no magma satisfies EQ1, so the implication is vacuously true." But EQ1 *does* have models — just not in our battery.

#### False Negatives (74): Model says FALSE when answer is TRUE

| Root cause | Count | % |
|---|---|---|
| Bogus counterexample (claims CE that isn't valid) | 60 | 81% |
| Step 5 default FALSE (no proof, no CE, defaults FALSE) | 6 | 8% |
| Other (knows no CE but still says FALSE) | 5 | 7% |
| EQ1 fails in all battery → FALSE | 3 | 4% |

**The dominant FN pattern (81%):** The model presents a counterexample magma, but the CE is invalid. Breakdown of the 60 bogus CEs:

| Bogus CE type | Count | % |
|---|---|---|
| Battery magma (H/I/J/K/L/G) — arithmetic error | 17 | 28% |
| Projection magma (C or D) — wrong evaluation | 14 | 23% |
| Custom/invented magma — wrong | 9 | 15% |
| Admits no valid CE found, still says FALSE | 8 | 13% |
| Balance criterion misapplied as CE | 6 | 10% |
| Linear magma — arithmetic error | 3 | 5% |
| Constant magma (A/B) — wrong | 3 | 5% |

26 of the 60 bogus CE cases (43%) had a singleton signal detected earlier in the response but the model overrode it with the bogus CE.

### Key insights

1. **FPs and FNs are mirror images of the same problem.** The model can't reliably distinguish "EQ1 holds in this magma" from "EQ1 fails in this magma" for the 3-element magmas. When it gets the arithmetic wrong, it either (a) misses a valid CE → FP, or (b) claims a bogus CE → FN.

2. **The singleton signal is double-edged.** It correctly fires on many TRUE cases, but 26 FNs had singleton detected then overridden by a bogus CE. The model doesn't trust its own singleton finding.

3. **The "vacuous" FPs (21) reveal a coverage gap.** These are problems where EQ1 is genuinely restrictive — it only holds in magmas not in our battery. No amount of battery testing can help here; only algebraic proof can.

4. **Run-to-run variance (~37%) dwarfs the cheatsheet effect.** Most version comparisons show <4% accuracy differences, but 37% of problems flip between runs. This means we need multiple runs or majority voting to get reliable measurements.

## Files
- `cheatsheet_v19.txt` — cheatsheet used
- `v19_20k_hard3.json` — full 400-problem results
