# Test: v18 with Bailout Instruction

## Purpose
Test whether adding "If at any point you are running low on space and not making progress, skip remaining steps and go directly to Step 5" before Step 4 reduces unparsed responses without hurting accuracy.

## Cheatsheets Used
- cheatsheet_v18_bailout.txt — v18 + bailout instruction before Step 4

## Datasets
- hard3.jsonl (400 problems)

## Results

| Metric | v18 | v18_bailout | Change |
|--------|-----|-------------|--------|
| Accuracy | 63.0% | 58.4% | -4.6% |
| F1 | 0.601 | 0.577 | -0.024 |
| TP | 106 | 113 | +7 |
| FP | 65 | 85 | +20 |
| FN | 76 | 81 | +5 |
| TN | 134 | 120 | -14 |
| Unparsed | 19 | 1 | -18 |

## Conclusions
- The bailout instruction nearly eliminated unparsed responses (19 → 1).
- But accuracy dropped 4.6% — the converted responses mostly became FPs (+20), not correct answers.
- Haiku is bailing out and defaulting to TRUE when uncertain, rather than making a good judgment.
- The instruction may be encouraging early exit even on problems where continued work would have reached the right answer.
- Net effect is negative: gaining 18 parsed responses but losing 20 TNs is a bad trade.
