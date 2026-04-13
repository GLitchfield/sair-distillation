# Test 31: v36 Verbose Regression

## Purpose
Test whether combining v23's full verbose structure (9KB) with v34's additions (CAUTION, mod-5 magmas, boxed output) improves results. Hypothesis: with 64k token budget, the verbose battery might help models execute magma tests more accurately.

## Cheatsheet
- cheatsheet_v36.txt (9,048 bytes) — v23 full 12-magma battery with worked examples + CAUTION + M1/M2/M3 + boxed output

## Results @ 64k tokens

| Dataset | GPT-OSS | Gemma |
|---|---|---|
| hard3_100 | 75.8% | **9.1%** (88 errors) |
| hard2 | 54.5% | **21.5%** (139 errors) |
| hard1 | 47.8% | **2.9%** (65 errors) |

## Comparison to v33/v34 @ 16k

| Dataset | v33/v34 GPT | v36 GPT | v33/v34 Gemma | v36 Gemma |
|---|---|---|---|---|
| hard3_100 | 88.9% | **75.8% (-13)** | 93.9% | **9.1% (-85)** |
| hard2 | 68.5% | **54.5% (-14)** | 72.5% | **21.5% (-51)** |

## Key Finding
**Verbose cheatsheets are catastrophic for reasoning models.**

- GPT-OSS dropped 13-14 points across all datasets
- Gemma was effectively unusable — 88-139 errors per dataset at 64k tokens
- The 9KB cheatsheet caused Gemma to reason indefinitely on most problems

The failure mechanism: more cheatsheet content = more for the model to "read" during internal reasoning = more reasoning tokens burned = more timeouts. Even with 64k budget, the reasoning loops never terminate on hard problems.

## Conclusion
**Compact cheatsheets (~3KB) are definitively better than verbose ones (~9KB) for reasoning models.** The Haiku-era assumption that more instructions help was wrong for GPT-OSS and Gemma. The magma battery design was sound, but the verbose descriptions, worked examples, and procedural instructions actively hurt performance.
