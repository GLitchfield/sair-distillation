# Test: Community Example Sheets Benchmark

## Purpose

Benchmark community-submitted cheatsheets against our best versions to understand how different approaches compare. This tests whether alternative strategies (theory-heavy, structural/feature-based) can outperform our magma-testing approach.

## Cheatsheets Used

Both included in this folder:

- **AMEY.txt** (2,934 bytes) -- Theory-heavy approach. References specific ETP equation IDs, uses LaTeX notation, includes only 4 counterexample magmas. Focuses on abstract mathematical reasoning (Master Laws, Singleton Collapse, Parentheses Balance, Variable Displacement, Duality Principle).

- **Adam Betka.txt** (10,424 bytes) -- Purely structural/feature-based approach. No magma testing at all. Uses a complex rule cascade: source-collapse lemmas, bare-source contradiction motifs (C1-C14), separator tests (LP, RP, SET, XOR, AB), FALSE guards (G1-G4), structural rules (T1-T8, F1-F3), and extended rules (D3-D4). Entirely deterministic -- designed to be computed without any magma evaluation.

## Datasets

- **hard3_400**: 400 problems from the hard3 dataset

## Results

### Hard3 400 Comparison

| Cheatsheet | Size | Accuracy | F1 Score | Approach |
|-----------|------|----------|----------|----------|
| **Our best (v13a rerun)** | ~7KB | **63.2%** | **0.693** | Magma testing |
| Adam Betka | 10,424 bytes | 55.0% | 0.521 | Structural rules |
| AMEY | 2,934 bytes | 52.0% | 0.284 | Abstract theory |

### Analysis: AMEY (52.0%, F1=0.284)

- Very low F1 indicates severe class imbalance in predictions
- The abstract theory references (Master Laws, specific equation IDs like 1689, 1076, 3744) require knowledge Haiku does not have
- LaTeX notation adds parsing overhead without benefit for a text model
- Only 4 counterexample magmas (left-projection, right-projection, constant, fixed-point trap) -- far fewer than our 12-magma battery
- The "Benchmark Bottlenecks" section (equations 706, 1274, 1516) is too specific to help on random problems

### Analysis: Adam Betka (55.0%, F1=0.521)

- Sophisticated structural approach with many well-designed rules
- The contradiction motifs (C1-C14) capture genuine mathematical patterns
- However, Haiku makes frequent errors in feature computation (variable counting, parity checks, topShape determination)
- The rule cascade is fragile -- one wrong feature computation cascades into a wrong verdict
- At 10,424 bytes, it is over the 10KB soft limit
- The approach works better in theory than in practice with a small language model

## Conclusions

1. **Our magma-testing approach significantly outperforms both community sheets** (63.2% vs 55.0% vs 52.0%).
2. **AMEY's abstract theory does not translate to small model execution.** Haiku cannot leverage equation ID references or abstract mathematical principles it was not trained on. The approach assumes more mathematical knowledge than Haiku possesses.
3. **Betka's structural rules are mathematically interesting but less effective than actual magma testing.** The rules are correct in principle but Haiku's execution errors in feature computation undermine them.
4. **Magma testing is more robust to execution errors** than feature computation. When Haiku tests a magma, a single arithmetic error usually only affects one magma; with structural rules, one wrong feature can flip the entire verdict.
5. **Size does not determine quality.** AMEY at 2.9KB and Betka at 10.4KB both lose to our ~7KB v13a. Content and approach matter more than length.
