# Test 29: v33 — Adding J, K, L Back

## Purpose
Test adding 3-element table magmas J (null-left), K (swap-row2), L (near-zero) back to the battery. Cross-model error analysis showed these magmas catch 23 of 51 "both-wrong" FALSE problems from the v29 run.

## Cheatsheet
- cheatsheet_v33.txt (2,752 bytes) — v29 + J, K, L magma descriptions

## Results on hard3_100 @ 16k tokens

| Model | v29 (5 magmas) | v33 (8 magmas) | Delta |
|---|---|---|---|
| **GPT-OSS** | 74.7% | **88.9%** | **+14.2** |
| **Gemma** | 86.9% | **93.9%** | **+7.0** |

### GPT-OSS detail
| Metric | v29 | v33 |
|---|---|---|
| TP | 45 | 48 |
| FP | 22 | **10** |
| FN | 3 | **0** |
| TN | 29 | **40** |
| F1 | 0.783 | **0.906** |

### Gemma detail
| Metric | v29 | v33 |
|---|---|---|
| TP | 47 | 43 |
| FP | 9 | **1** |
| FN | 0 | 2 |
| TN | 39 | **50** |
| F1 | 0.913 | **0.966** |

## Key Finding
**The Haiku-era magma battery was always sound — the models just needed the capability to execute it.** Adding J, K, L back cut GPT-OSS FPs in half (22→10) and gave Gemma 97.7% precision with only 1 FP. The original v23 battery design is vindicated.

## Why These Were Cut
We dropped J, K, L during GPT-OSS compression (v28/v29) because:
1. GPT-OSS wasn't citing them as CEs in its visible output
2. Token budget concerns at 8k cap
With 16k tokens, both concerns are resolved.
