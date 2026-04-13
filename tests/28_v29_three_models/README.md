# Test 28: v29 Baseline on All Three Models @ 16k

## Purpose
Establish a clean baseline for all three competition models on v29 with 16k token cap. This was our first proper three-model comparison.

## Cheatsheet
- cheatsheet_v29_gpt.txt (2,300 bytes) — compact 5 magmas (C,D,E,H,I) + CAUTION about projection over-generalization

## Results on hard3_100 @ 16k tokens

| Model | Accuracy | F1 | TP | FP | FN | TN | Errors |
|---|---|---|---|---|---|---|---|
| **Gemma 4 31B** | **86.9%** | **0.913** | 47 | 9 | 0 | 39 | 4 |
| GPT-OSS-120B | 74.7% | 0.783 | 45 | 22 | 3 | 29 | 0 |
| Llama 3.3 70B | 51.5% | 0.000 | 0 | 0 | 48 | 51 | 0 |

## Results on hard3 full (400) @ 16k tokens

| Model | Accuracy | F1 | TP | FP | FN | TN | Errors |
|---|---|---|---|---|---|---|---|
| **Gemma** | **83.0%** | **0.862** | 187 | 55 | 5 | 145 | 5 |
| GPT-OSS | 71.0% | 0.759 | 183 | 104 | 12 | 101 | 0 |

## Key Findings
1. **Gemma is the strongest model** at 86.9%/83.0% — much better than GPT-OSS
2. **Llama is completely broken on v29** — 0 TPs, says FALSE on everything. The compact 5-magma sheet doesn't give Llama enough procedure.
3. **GPT-OSS has high TRUE recall (93.8%)** but too many FPs (104 on full hard3)
4. **Oracle ensemble reaches 99%** on hard3_100 — models are highly complementary
5. Gemma uses 8,845 avg reasoning tokens — needs 16k+ cap
