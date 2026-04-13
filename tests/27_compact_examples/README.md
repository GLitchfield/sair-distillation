# Test 27: Compact Examples Experiment

## Purpose
Test whether compressing worked examples reduces GPT-OSS hidden reasoning token burn. The hypothesis: if compact examples reduce total tokens, hidden reasoning mimics the style of the prompt.

## Cheatsheet
- cheatsheet_v23_compact.txt (7,528 bytes) — v23 with compressed worked examples only, everything else identical

## Results on Cerebras GPT-OSS hard3_100 @ 8k tokens

| Version | Accuracy | F1 | Avg tokens | Truncated | Unparsed |
|---|---|---|---|---|---|
| v23 (verbose) | 46.5% | 0.846 | 6,695 | 55 | 45 |
| v23_compact | **59.6%** | **0.941** | 6,178 | 42 | 37 |

## Key Finding
Compact examples reduced average token usage by ~8% (6,695→6,178) and improved accuracy by 13 points. The improvement came from fewer truncations (55→42) recovering parseable responses.

When parseable, v23_compact had exceptional accuracy: F1=0.941, 0 FN, only 3 FP.

## Conclusion
Compact examples DO influence hidden reasoning — the model reasons more concisely when shown concise examples. This validated the approach of using compact cheatsheets for reasoning models.
