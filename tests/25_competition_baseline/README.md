# Test 25: Competition Model Baseline

## Purpose
First tests on the actual competition evaluation models after the judge repo was released (Apr 10). Discovered the competition uses GPT-OSS-120B, Llama 3.3 70B, and Gemma 4 31B — NOT Haiku.

## Key Discovery
The competition models are fundamentally different from Haiku:
- GPT-OSS and Gemma have internal reasoning (hidden CoT) that burns shared token budget
- Llama has no internal reasoning — any thinking happens in visible output
- Official token cap is 8192 (later assumed 16k based on community discussion)
- All models accessed via OpenRouter with pinned providers

## Cheatsheet
- cheatsheet_v23.txt (8,302 bytes) — our Haiku-era best with 12-magma battery

## Results (v23 on hard3_100 @ 8k tokens)

| Model | Accuracy | F1 | TP | FP | FN | TN | Unparsed | Errors |
|---|---|---|---|---|---|---|---|---|
| Llama 3.3 70B | 52.5% | 0.420 | 17 | 16 | 31 | 35 | 0 | 0 |
| GPT-OSS-120B | ~55% | — | — | — | — | — | 26 | 10 |
| Gemma 4 31B | ~58% | 0.261 | 6 | 6 | 28 | 42 | 0 | 17 |

## Key Observations
- GPT-OSS had 26 unparsed (token exhaustion) and 10 timeouts on DeepInfra
- Gemma had 17 errors from Novita rate limiting
- Llama was 100% parseable but low accuracy
- Each model fails in a completely different way
- The cheatsheet designed for Haiku needs significant adaptation

## Providers Tested
- OpenRouter (initial): rate-limited, slow
- DeepInfra (direct): GPT-OSS + Llama, faster
- Cerebras: GPT-OSS, 30x faster than DeepInfra
- Google AI Studio: Gemma native API, slow but works with parallelism
- Novita: Gemma, heavily rate-limited
