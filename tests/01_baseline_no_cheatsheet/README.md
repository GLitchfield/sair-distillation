# Test: Baseline -- No Cheatsheet

## Purpose

Establish what Haiku does without any cheatsheet. This test answers the fundamental question: how much of Haiku's performance on the ETP implication task is due to the cheatsheet vs. Haiku's own capabilities?

## Cheatsheets Used

None. Haiku was given only a minimal prompt: "Does EQ1 imply EQ2 over all magmas?"

## Datasets

- **normal**: 30 TRUE + 30 FALSE problems (balanced)
- **hard3**: 30 random problems
- **hard_order5**: 30 TRUE + 30 FALSE problems (balanced)
- **Isolated knowledge questions**: Asked Haiku about magma definitions, magma arithmetic, and the ETP project directly

## Results

### Implication Task Results

| Dataset | Accuracy | TRUE Recall | FALSE Recall |
|---------|----------|-------------|--------------|
| normal (30T+30F) | 50% | 0% | 100% |
| hard3 (30 random) | varies | 0% | 100% |
| hard_order5 (30T+30F) | 50% | 0% | 100% |

Haiku answered **FALSE on every single problem** across all datasets. This means:
- 0% TRUE recall (never identifies a true implication)
- 100% FALSE recall (trivially, by always saying FALSE)
- 50% overall accuracy on balanced sets (by chance)

### Knowledge Probes

- **Magma definition**: Haiku knows what magmas are (a set with a binary operation, no axioms required). PASS.
- **Magma arithmetic**: Haiku can correctly compute products in specific magmas (e.g., left projection, XOR) when given the operation table in isolation. PASS.
- **ETP project knowledge**: Haiku does NOT know about the Equational Theories Project, the 4694 equations, or the implication problem space. FAIL.

## Conclusions

1. **The cheatsheet is entirely responsible for Haiku's ability to identify TRUE cases.** Without it, Haiku has zero TRUE recall.
2. Haiku's default behavior is to say FALSE on every implication problem. This is a safe but uninformative strategy.
3. Haiku has the prerequisite knowledge (magma definitions, arithmetic) but cannot synthesize it into implication judgments without explicit guidance.
4. Any TRUE recall we observe in cheatsheet-assisted runs is directly attributable to the cheatsheet's instructions and heuristics.
5. This baseline makes the cheatsheet's contribution measurable: every percentage point of TRUE recall above 0% is the cheatsheet's doing.
