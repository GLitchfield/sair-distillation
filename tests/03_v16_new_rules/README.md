# Test: v16 -- New Rules (EQ1-Restrictive and Singleton Stop)

## Purpose

Test two new rules designed to fix the dominant error modes found in v15:
1. "EQ1 fails everywhere -> TRUE" rule to fix the 62% of FNs caused by Haiku misinterpreting restrictive EQ1s
2. Stronger singleton stop logic to fix the 30% of FNs from singleton mishandling

## Cheatsheets Used

- **cheatsheet_v16.txt** -- Compact version (7,257 bytes). Included in this folder.
- **cheatsheet_v16b.txt** -- Extended version with more detail on Magma H/I evaluation (8,043 bytes). Included in this folder.

### Key Differences

- v16 is compact at 7,257 bytes
- v16b adds detailed bottom-up evaluation examples for Magma H (right-shift) and Magma I (left-shift), bringing it to 8,043 bytes
- Both add Step 5 rule 4: "EQ1 failed in ALL or nearly all tested magmas -> TRUE" with explanation
- Both add Step 5 rule 5: "No CE, no proof, but some magmas DID satisfy EQ1 -> FALSE"
- Both include a third worked example showing the "EQ1 very restrictive -> TRUE" pattern

## Datasets

- **Probe test**: 17 known failures from v15 (9 normal FNs + 8 hard3 FPs)
- **normal_100**: 100 problems from the normal difficulty set
- **hard3_400**: 400 problems from the hard3 dataset

## Results

### Probe Test (17 known failures)

| Version | Normal FNs Fixed (of 9) | Hard3 FPs Fixed (of 8) |
|---------|------------------------|----------------------|
| v16 | 9/9 (7 parsed + 2 unparsed but correct reasoning) | 1/8 |
| v16b | Similar to v16 | Similar to v16 |

The new "EQ1 restrictive -> TRUE" rule fixed all 9 normal FNs. Hard3 FPs were mostly unaffected.

### Normal 100

| Version | Accuracy | F1 Score |
|---------|----------|----------|
| v16 | **88%** | 0.893 |
| v16b | **89%** | 0.909 |
| v15 | 64% | -- |

Massive improvement over v15's 64%. The new rules dramatically helped on normal difficulty.

### Hard3 400

| Version | Accuracy | F1 Score |
|---------|----------|----------|
| v16 | 60.0% | 0.671 |
| v16b | 57.4% | 0.643 |
| v13a rerun | 63.2% | 0.693 |

Both v16 variants performed worse than v13a's rerun on hard3.

### Prompt Length Analysis

- v16b (longer, +H/I detail) was slightly better on normal (89% vs 88%) but slightly worse on hard3 (57.4% vs 60.0%)
- No strong evidence either way for prompt length effects within this range

### FP Analysis on Hard3

128 false positives were analyzed and split roughly 50/50:
- **~66 FPs**: Singleton signal misfires (Magma D triggering too early, etc.)
- **~62 FPs**: EQ1-restrictive rule misfires (the new "EQ1 fails everywhere -> TRUE" rule)

The new "EQ1 fails everywhere -> TRUE" rule, while fixing normal FNs, caused 62 of 128 FPs on hard3.

## Conclusions

1. **New rules dramatically helped normal accuracy** (88-89% vs 64%), confirming the error analysis from v15 was correct.
2. **The same rules hurt hard3** by increasing false positives. The hard3 dataset is specifically designed to defeat these heuristics.
3. **The "EQ1 fails everywhere -> TRUE" heuristic is a double-edged sword**: it correctly identifies restrictive EQ1s in normal problems but misfires on hard3 where EQ1 genuinely fails in small magmas but has counterexamples in larger ones.
4. **v16b's extra H/I detail provided no clear benefit** -- slightly better on normal, slightly worse on hard3.
5. The fundamental tension: rules that improve normal accuracy tend to hurt hard3, and vice versa. Hard3 is engineered to exploit exactly these heuristic shortcuts.
