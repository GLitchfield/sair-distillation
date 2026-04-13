# Test 32: Magma Coverage Analysis

## Purpose
Systematic analysis of what magmas can and cannot catch across all datasets. Includes linear magma scanning, 3-element brute force, cohomology testing, and 4-element structured search.

## Methods

### Linear magma scan (analysis/linear_magma_scan.py)
Scanned all (a,b,p) triples for p in {2,3,5,7} against FALSE problems. Uses polynomial coefficient method for efficient verification.

### 3-element brute force
Enumerated all 19,683 possible 3-element magma tables and tested each against FALSE problems.

### Cohomology scan (analysis/cohomology_scan.py)
Implemented cocycle space dimension comparison and subspace containment tests from the cohomology precomputation proposal.

### 4-element structured search (analysis/magma4_search.py)
Searched 52,000 structured and random 4-element magmas: unary, near-projection, near-zero, cyclic permutation, and 50K random tables.

## Results by Dataset

### hard3 (400 problems, 205 FALSE)
| Method | FALSE caught |
|---|---|
| v33 battery (C,D,E,H,I,J,K,L) | ~133/205 |
| All linear p≤5 | 38/205 |
| All 3-element (19,683) | ~179/205 |
| **Uncatchable by 3-element** | **~26/205** |

### hard2 (200 problems, 100 FALSE)
| Method | FALSE caught |
|---|---|
| v33 battery | 5/100 |
| All linear p≤7 | 33/100 |
| All 3-element (19,683) | 52/100 |
| **Uncatchable by 3-element** | **48/100** |

hard2 is much harder — our battery catches only 5% vs ~65% on hard3.

### hard1 (69 problems, 45 FALSE)
| Method | FALSE caught |
|---|---|
| v34 battery | 0/45 |
| All linear p≤7 | 10/45 |
| All 3-element (19,683) | 21/45 |
| **Uncatchable by 3-element** | **24/45** |

### order5_half (327 problems, 163 FALSE)
| Method | FALSE caught |
|---|---|
| All linear p≤7 | **0/163** |
| All 3-element (19,683) | **0/163** |
| Cohomology dimension test (p≤7) | **0/163** |
| Cohomology subspace test (p≤5) | **0/163** |
| 4-element structured (52K) | **0/163** |

Order5 is completely resistant to all battery approaches.

## Key Findings

1. **Our v33 battery catches the "easy" FALSE problems** — the ones with small magma CEs. The uncaught problems need exotic or large magmas.

2. **Linear magmas at higher primes (p=5,7) add significant coverage on hard2** — this led to v34's mod-5 additions which gave +16% on hard2.

3. **Order5 problems have NO small counterexamples.** Not linear (any p≤7), not 3-element (all 19,683), not 4-element (52K sampled), not cohomological. The CEs likely require 5+ elements with very specific non-linear structure.

4. **Top new magma from greedy search:** Near-zero-2 (x*y=0 except 2*1=1, 2*2=1) catches 3 hard1 + 10 hard2 problems. Added as v35 but caused Gemma regressions from reasoning overhead.

5. **Cohomology approach was a dead end for order5.** Both dimension test and subspace containment test found zero catches, because the order5 EQ1 equations have zero linear models at any tested prime.

## Tools Created
- `analysis/linear_magma_scan.py` — polynomial coefficient scan across (a,b,p) triples
- `analysis/cohomology_scan.py` — cocycle space dimension and subspace containment
- `analysis/magma4_search.py` — structured 4-element magma search
- `analysis/test_magma_arithmetic.py` — model arithmetic accuracy testing
- `analysis/test_coeff_stability.py` — coefficient method reliability testing
