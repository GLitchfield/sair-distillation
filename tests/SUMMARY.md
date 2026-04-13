# Test Summary

All results on hard3 (400 problems) unless noted. Dates are approximate.

## No-Cheatsheet Baseline

| Dataset | Sample | Accuracy | TP | FP | FN | TN | Notes |
|---------|--------|----------|----|----|----|----|-------|
| normal | 30T+30F | 50% | 0 | 0 | 30 | 30 | Says FALSE on everything |
| hard3 | 30 random | 60% | 0 | 0 | 12 | 18 | Says FALSE on everything |
| hard_order5 | 30T+30F | 50% | 0 | 0 | 30 | 30 | Says FALSE on everything |

Haiku has 0% TRUE recall without a cheatsheet. All TRUE identification comes from the cheatsheet.

## Cheatsheet Runs on hard3 (400 problems)

| Cheatsheet | Bytes | Accuracy | F1 | TP | FP | FN | TN | Unparsed | Test |
|------------|-------|----------|-----|----|----|----|----|----------|------|
| v5 | ? | 46.3% | 0.586 | - | - | - | - | - | early |
| v7 | ? | 54.5% | 0.667 | - | - | - | - | - | magma battery |
| v13a (original) | 10,823 | 65.2% | 0.714 | 130 | 65 | 131 | 74 | ? | over 10KB limit |
| v13a (rerun) | 10,823 | 63.2% | 0.693 | 166 | 118 | 29 | 87 | 0 | different error profile |
| v14 | 6,230 | 55.7% | 0.504 | - | - | - | - | - | regression |
| v16 | 7,257 | 60.0% | 0.671 | 163 | 128 | 32 | 77 | 0 | [03] |
| v16b | 8,043 | 57.4% | 0.643 | 153 | 128 | 42 | 76 | 1 | [03] |
| v17 | 6,922 | 63.5% | 0.628 | 120 | 73 | 69 | 127 | 11 | [04] |
| v18a (separators) | 6,782 | 58.1% | 0.540 | 95 | 72 | 90 | 130 | 13 | [05] |
| v18b (motifs) | 7,325 | 56.8% | 0.538 | 98 | 77 | 91 | 123 | 11 | [05] |
| v18c (collapse) | 7,449 | 58.1% | 0.600 | 117 | 94 | 62 | 99 | 28 | [05] |
| v18d (guards) | 7,126 | 51.5% | 0.510 | 99 | 98 | 92 | 103 | 8 | [05] |
| v18e (combined) | 7,534 | 55.5% | 0.582 | 124 | 107 | 71 | 98 | 0 | [05] |
| AMEY | 2,934 | 52.0% | 0.284 | 38 | 35 | 157 | 170 | 0 | [07] |
| Adam Betka | 10,424 | 55.0% | 0.521 | 98 | 83 | 97 | 122 | 0 | [07] |
| Simon | 5,190 | 54.2% | 0.274 | 34 | 19 | 161 | 183 | 6 | [14] |
| v19 (=v18_brief) | 8,271 | 63.3% | 0.602 | 103 | 60 | 76 | 132 | 29 | [15] |
| v19 (20k tokens) | 8,271 | 66.7% | 0.643 | 120 | 59 | 74 | 146 | 1 | [16] |
| v19_novac | 8,329 | 59.5% | 0.460 | 69 | 36 | 126 | 169 | 0 | [18] |

## Cheatsheet Runs on normal

| Cheatsheet | Sample | Accuracy | F1 | TP | FP | FN | TN | Test |
|------------|--------|----------|-----|----|----|----|----|------|
| v15 | 100 | 64.0% | 0.550 | 22 | 2 | 34 | 42 | [02] |
| v16 | 100 | 88.0% | 0.893 | 50 | 6 | 6 | 38 | [03] |
| v16b | 100 | 89.0% | 0.909 | 55 | 10 | 1 | 34 | [03] |

## Cheatsheet Runs on hard_order5

| Cheatsheet | Sample | Accuracy | F1 | TP | FP | FN | TN | Test |
|------------|--------|----------|-----|----|----|----|----|------|
| v13a | 327 (half) | 55.7% | 0.667 | 144 | 125 | 19 | 37 | [06] |
| v17 | 327 (half) | 49.7% | 0.602 | 121 | 122 | 38 | 37 | [06] |

## Targeted Tests

| Test | Cheatsheet | Dataset | Accuracy | Notes |
|------|------------|---------|----------|-------|
| v15 compliance | v15 | 42 v13a failures | 81.0% | Singleton/compliance fixes worked |
| v16 probe | v16 | 17 known failures | 47.1% | 9/9 normal FNs fixed, 1/8 hard3 FPs |
| v16b probe | v16b | 17 known failures | 52.9% | Similar to v16 |

## Key Findings (verified)

1. **Haiku always says FALSE without a cheatsheet.** 0% TRUE recall on all datasets.
2. **v13a is not reproducible.** 65.2% → 63.2% on rerun with very different error profile (65 vs 118 FPs).
3. **Prompting guide improvements help compliance** but Step 5 logic changes dominate accuracy.
4. **Longer cheatsheets don't clearly help or hurt.** v16 (7.3KB) vs v16b (8KB) was a wash.
5. **Betka's structural rules don't help** when added to our magma-testing framework.
6. **Execution gap is ~37 problems on hard3.** Split: 44% singleton signal misfires, 44% arithmetic errors, 11% EQ2 errors.
7. **Singleton signal nets +23 on hard3** (+68 TPs, -45 FPs) but causes 62% of all FPs.
8. **CORRECTED (twice): Haiku is 100% at finding EQ1 failures in 3-element magmas, but only 10-35% at confirming EQ1 holds.** Initial parser bug reversed the results. Real picture: Haiku's bias is toward "EQ1 fails" — it finds phantom failures due to arithmetic errors. The 3-element magmas are unreliable as CE tools because Haiku can't confirm EQ1 holds universally.
9. **Battery expansion ceiling is 46 new problems** — our existing battery already catches 133/179 coverable.
10. **Order-5 is much harder.** ~77% FP rate on FALSE cases. Magma battery largely ineffective.

---

## Phase 2: Competition Models (Apr 10-13)

On Apr 10, the official judge repo was released revealing the actual evaluation models:
- **gpt-oss-120b** (reasoning: low, via DeepInfra/Cerebras)
- **llama-3.3-70b-instruct** (reasoning: disabled, via DeepInfra)
- **gemma-4-31b-it** (reasoning: low, via Novita/Google AI Studio)

These are fundamentally different from Haiku — two have internal reasoning (hidden CoT), one has none. The competition uses one cheatsheet for all three, weighted equally.

### Key Discoveries

1. **GPT-OSS burns 93% of tokens on hidden reasoning.** Visible output is only ~7%. At 8192 max_tokens, 20% of responses are completely empty (zero visible chars). Raising to 16k eliminates unparsed.

2. **Compact cheatsheets beat verbose ones for reasoning models.** v23 (8.3KB full battery) performed worse than v33 (2.8KB compact) on GPT-OSS because more content = more reasoning tokens burned. v36 (9KB verbose at 64k) was catastrophic for Gemma (88-139 errors per dataset).

3. **Llama caps at ~52% regardless of cheatsheet.** No internal reasoning = can't solve the hard problems. Tested v23, v29, v31, v32 — all ~50-53%. Temperature changes (0.0 vs 0.3) don't help.

4. **Gemma is the strongest model** when given enough tokens (16k+). Reaches 93.9% on hard3_100 with v33. But very slow (~2-15 min/call) and prone to timeouts.

5. **J, K, L (3-element table magmas) are critical.** Adding them back (v29→v33) improved GPT-OSS from 74.7%→88.9% and Gemma from 86.9%→93.9% on hard3_100.

6. **Mod-5 linear magmas help on hard2.** Adding M1=(4,2), M2=(2,4), M3=(3,3) mod 5 (v33→v34) improved GPT-OSS from 52.5%→68.5% on hard2. But caused Gemma timeouts on hard3.

7. **CAUTION about projection over-generalization** helps GPT-OSS by ~4 points (v28→v29).

8. **Order-5 problems are unsolvable by battery approach.** No linear CE exists up to p=7, no 3-element CE exists (19,683 searched), no 4-element CE found (52K searched). Both models score ~49% (random).

9. **Oracle ensemble (GPT-OSS + Gemma) reaches 99%** on hard3_100 — the models are highly complementary.

### Competition Model Results

#### On hard3_100 (99 problems, stratified subset) @ 16k tokens

| Cheatsheet | Bytes | GPT-OSS | | Gemma | | Llama | |
|---|---|---|---|---|---|---|---|
| | | Acc | F1 | Acc | F1 | Acc | F1 |
| v29 (5 magmas) | 2,300 | 74.7% | 0.783 | 86.9% | 0.913 | 51.5% | 0.000 |
| v33 (8 magmas +J,K,L) | 2,752 | **88.9%** | **0.906** | **93.9%** | **0.966** | — | — |
| v34 (11 magmas +mod5) | 3,147 | 87.9% | 0.887 | 80.8% | 0.918 | — | — |
| v36 (9KB verbose @64k) | 9,048 | 75.8% | 0.793 | 9.1% | — | — | — |

#### On hard2 (200 problems) @ 16k tokens

| Cheatsheet | GPT-OSS | | Gemma | |
|---|---|---|---|---|
| | Acc | F1 | Acc | F1 |
| v33 (8 magmas) | 52.5% | 0.700 | 64.5% | 0.758 |
| v34 (11 magmas +mod5) | **68.5%** | **0.764** | **72.5%** | **0.844** |

#### On hard1 (69 problems) @ 16k tokens

| Cheatsheet | GPT-OSS | | Gemma | |
|---|---|---|---|---|
| | Acc | F1 | Acc | F1 |
| v34 (11 magmas) | 49.3% | 0.590 | 37.7% | 0.727 |

#### On hard3 full (400 problems) @ 16k tokens

| Cheatsheet | GPT-OSS | | Gemma | |
|---|---|---|---|---|
| | Acc | F1 | Acc | F1 |
| v29 (5 magmas) | 71.0% | 0.759 | 83.0% | 0.862 |

#### On order5_half (327 problems) @ 16k tokens

| Cheatsheet | GPT-OSS | | Gemma | |
|---|---|---|---|---|
| | Acc | F1 | Acc | F1 |
| v29 (5 magmas) | 49.5% | 0.663 | 46.3% | 0.638 |

Both models get 0 TN on order5. Battery approach completely fails.

### Cheatsheet Evolution (Phase 2)

| Version | Bytes | Key change | Status |
|---|---|---|---|
| v25 | 8,376 | v23 + \boxed{} format | Tested, minor effect |
| v27_minimal | 1,430 | Ultra-minimal, no magmas | 60.6% GPT, too many FPs |
| v28_gpt | 1,967 | 5 magmas GPT-OSS uses (C,D,E,H,I) | 67.7% GPT, broke Llama |
| v29_gpt | 2,300 | v28 + CAUTION | 71.7% GPT, best pre-JKL |
| v30_binary | 579 | Research doc's ultra-compressed | 52.5% GPT, 0 truncation |
| v31_llama | 8,682 | v23 + strict CE + TRUE default | Over-predicted TRUE |
| v32_llama | 8,514 | v23 + holds-iff reformat | Worse than v23 for Llama |
| **v33** | **2,752** | **v29 + J,K,L** | **Best on hard3: 88.9%/93.9%** |
| **v34** | **3,147** | **v33 + M1,M2,M3 mod-5** | **Best on hard2: 68.5%/72.5%** |
| v35 | 3,299 | v34 + near-zero-2 (N) | Marginal, Gemma regressed |
| v36 | 9,048 | v23 verbose + all additions | Regressed badly |

### Provider Setup

| Model | Provider | Speed | Notes |
|---|---|---|---|
| GPT-OSS | Cerebras | ~1-4s/call | 30x faster than DeepInfra |
| Gemma | Google AI Studio (native) | ~2-15min/call | 32 parallel, no thinking budget control |
| Llama | DeepInfra | ~20-30s/call | Fast, no issues |

---

## No-Cheatsheet Baseline (Both Models)

| Dataset | Model | TP | FP | FN | TN | Accuracy |
|---------|-------|----|----|----|----|----------|
| normal (30T+30F) | Haiku | 0 | 0 | 30 | 30 | 50% |
| normal (30T+30F) | Gemini Flash Lite | 0 | 0 | 30 | 30 | 50% |
| hard3 (30 random) | Haiku | 0 | 0 | 12 | 18 | 60% |
| hard_order5 (30T+30F) | Haiku | 0 | 0 | 30 | 30 | 50% |

Both models say FALSE on everything. 0% TRUE recall across all datasets and models.

## Test Index

| # | Folder | Description |
|---|--------|-------------|
| 01 | 01_baseline_no_cheatsheet | Haiku without cheatsheet on all datasets |
| 02 | 02_v15_prompting_guide | Prompting guide changes, compliance/regression tests |
| 03 | 03_v16_new_rules | EQ1-restrictive and singleton rules |
| 04 | 04_v17_repackaged | v13a content with prompting improvements |
| 05 | 05_v18_betka_elements | 5 variants incorporating Betka's structural rules |
| 06 | 06_order5_baseline | v13a and v17 on harder order-5 problems |
| 07 | 07_example_sheets | Community cheatsheets (AMEY, Betka) |
| 08 | 08_execution_gap_analysis | Why Haiku misses problems the battery should catch |
| 09 | 09_gemini_baseline | Gemini Flash Lite no-cheatsheet — same always-FALSE behavior as Haiku |
| 10 | 10_magma_arithmetic_isolation | Magma arithmetic: baseline accuracy, stability, and 8+ prompting strategies tested on H and J |
| 11 | 11_v18_worked_examples | v18 with decompose worked examples for all 3-element magmas — 63.0% on hard3, no improvement over v17 |
| 12 | 12_v18_bailout | Bailout instruction before Step 4 — unparsed 19→1 but accuracy dropped 63.0%→58.4%, more FPs |
| 13 | 13_v18_brief_prompt | Brief output format — 63.6% accuracy, slight improvement, unparsed 19→18 |
| 14 | 14_simon_hard3 | Simon's community cheatsheet — 54.2% accuracy, very low TRUE recall (17.4%) |
| 15 | 15_v19_retry_validation | v19 (=v18_brief rerun) 63.3% + retry logic validation; unparsed are max_tokens not end_turn |
| 16 | 16_v19_20k_tokens | v19 with 20k token limit — 66.7% accuracy, unparsed 29→1, new best on hard3 |
| 17 | 17_vacuous_fp_fix | Targeted A/B: anti-vacuous fix 23%→76% on 5 problems (20 runs each) |
| 18 | 18_v19_novac_full | Full hard3 with novac fix — 59.5%, regression (-7.2), fix too aggressive |
| 19 | 19_v19_novac3_full | novac3 (surgical fix) full hard3 — 63.7%, within noise of baseline |
| 20 | 20_v19_rerun | v19 rerun — 63.9%, confirms 66.7% was high-side variance |
| 21 | 21_linear_magma_arithmetic | Arithmetic isolation: mod-3 100%, mod-5 0% (30 runs each) |
| 22 | 22_v23_new_linear | v23 (v19 + 2x+2y mod 3) on hard3_100 — 68.7%/64.3% across 2 runs |
| 23 | 23_v24_coeff_method | v24 coefficient method for linear magmas — 59.6%, no improvement |
| 24 | 24_v23_competition_baseline | First tests on competition models via OpenRouter |
| 25 | 25_competition_baseline | Competition model baseline with v23, provider setup discovery |
| 26 | 26_gpt_token_analysis | GPT-OSS burns 93% tokens on hidden reasoning, TRUE problems 60% truncation |
| 27 | 27_compact_examples | Compact examples reduce token burn 8%, accuracy +13 on GPT-OSS |
| 28 | 28_v29_three_models | v29 on all 3 models @ 16k: Gemma 86.9%, GPT 74.7%, Llama 51.5% |
| 29 | 29_v33_jkl_improvement | Adding J,K,L: GPT 74.7→88.9%, Gemma 86.9→93.9% — biggest single win |
| 30 | 30_v34_mod5_hard2 | Mod-5 magmas: GPT +16% on hard2, Gemma +8%, but Gemma timeouts on hard3 |
| 31 | 31_v36_verbose_regression | v36 verbose 9KB @ 64k: catastrophic regression, Gemma 88-139 errors |
| 32 | 32_magma_coverage_analysis | Linear scan, 3-elem brute force, cohomology, 4-elem search. Order5 unsolvable. |
