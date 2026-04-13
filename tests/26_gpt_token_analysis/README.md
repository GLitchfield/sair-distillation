# Test 26: GPT-OSS Token Analysis

## Purpose
Understand why GPT-OSS produces so many unparsed/empty responses. Analyzed token usage patterns to discover the hidden reasoning budget problem.

## Key Discovery
**93% of GPT-OSS's output tokens are hidden reasoning.** Average breakdown:
- Total tokens: 4,861
- Visible output: ~329 tokens (7%)
- Hidden reasoning: ~4,532 tokens (93%)

For truncated responses: ALL 8,192 tokens go to hidden reasoning with ZERO visible output. The model thinks until the budget runs out and never writes anything.

## Analysis Details

### Token distribution by outcome
| Category | Avg tokens | Visible chars |
|---|---|---|
| Parsed correct | 4,686 | ~1,200 |
| Parsed wrong | 4,862 | ~1,200 |
| Truncated (unparsed) | 8,192 | **0** |

### TRUE vs FALSE asymmetry
| Answer type | Avg tokens | Truncation rate |
|---|---|---|
| TRUE problems | 7,264 | 60% |
| FALSE problems | 5,156 | 25% |

TRUE problems burn way more tokens because the model tries to construct proofs (harder than finding CEs).

## Implications
- Compact visible format doesn't help much (only 7% of budget is visible)
- Compact cheatsheet input helps by giving less to reason about
- The 8192 cap is the main bottleneck; raising to 16k eliminates unparsed
- Compact examples reduce hidden reasoning by ~8% (tested v23 vs v23_compact)
