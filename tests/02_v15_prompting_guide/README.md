# Test: v15 -- Prompting Guide Improvements

## Purpose

Test changes inspired by the prompting strategy guide. Key improvements over earlier versions: full output format examples (both TRUE and FALSE worked examples), flat Step 5 decision rules, format reminder at end of prompt, and tighter singleton detection wording.

## Cheatsheets Used

- **cheatsheet_v15.txt** (included in this folder)

### Key Change in v15

Step 5 rule: "no proof + no CE -> FALSE" -- This was intended to prevent Haiku from guessing TRUE without evidence. The rule states that passing all magma tests is not proof, and when in doubt, say FALSE.

## Datasets

- **Compliance subset**: 42 problems specifically selected to test format compliance and singleton detection
- **normal_100**: 100 problems from the normal difficulty set
- **Stability benchmark**: 10 problems run 30 times each to measure consistency

## Results

### Compliance Subset (42 problems)

- **34/42 correct (81%)**
- This was a major improvement from 0% on these same problems with v13a (which had format/compliance issues)
- The full output examples and format reminder successfully fixed compliance

### Normal 100

- **64/100 (64%)**
- This was a significant regression from ~85% with earlier versions
- **34 false negatives (FNs)** -- problems that should be TRUE but Haiku said FALSE

### Stability Benchmark (10 problems x 30 runs)

- Average consistency: **82%**
- Perfect consistency (same answer all 30 runs): **0/10 problems**
- No problem achieved 100% consistency across 30 runs

### Error Analysis of 34 FNs

| Error Category | Count | Percentage |
|---------------|-------|------------|
| "EQ1 fails in all magmas -> says FALSE" | 21 | 62% |
| Singleton signal mishandling | 10 | 30% |
| Actual Step 5 default-to-FALSE | 3 | 9% |

The dominant FN cause was **NOT** the Step 5 default-FALSE rule as originally assumed. Instead, 62% of FNs came from Haiku misunderstanding what "EQ1 fails in all magmas" means -- Haiku would correctly observe that EQ1 fails in all tested magmas but then conclude FALSE instead of recognizing this as evidence for TRUE (highly restrictive EQ1).

## Conclusions

1. **Prompting guide improvements worked for compliance.** Full output examples and format reminders fixed the formatting problems that plagued v13a.
2. **The "default FALSE" Step 5 rule caused massive FN regression** (64% vs ~85% accuracy). However, the mechanism was subtler than expected.
3. **The real problem was Haiku's interpretation of "EQ1 fails in all magmas."** Haiku treated this as evidence against TRUE, when in fact it is strong evidence FOR TRUE (EQ1 is so restrictive that only exotic magmas satisfy it).
4. Singleton mishandling remained a significant issue (30% of FNs).
5. The stability benchmark revealed that Haiku's answers are not deterministic -- 82% average consistency means roughly 1 in 5 runs flip answers.
