# Test: Gemini Flash Lite Baseline (No Cheatsheet)

## Purpose
Establish whether Gemini 3.1 Flash Lite has the same "always FALSE" baseline behavior as Haiku, or if it differs.

## Cheatsheets Used
None — no cheatsheet, standard competition prompt template only.

## Datasets
- normal: 60 problems (30 TRUE + 30 FALSE), same sample as Haiku baseline test (seed=42)

## Results

| Dataset | Model | TP | FP | FN | TN | Accuracy | TRUE Recall |
|---------|-------|----|----|----|----|----------|-------------|
| normal (60) | Gemini Flash Lite | 0 | 0 | 30 | 30 | 50% | 0% |
| normal (60) | Haiku (prior test) | 0 | 0 | 30 | 30 | 50% | 0% |

Gemini says FALSE on every single problem, identical to Haiku.

## Conclusions
- Both target models (Haiku and Gemini Flash Lite) have the same baseline behavior: always FALSE.
- 0% TRUE recall without a cheatsheet is consistent across models and datasets.
- The cheatsheet is solely responsible for TRUE identification in both models.
- No need to test harder datasets — if it fails 100% on TRUE for easy problems, it will fail on hard ones too.
