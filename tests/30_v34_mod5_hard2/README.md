# Test 30: v34 — Mod-5 Linear Magmas for hard2

## Purpose
Test adding 3 mod-5 linear magmas to improve FALSE detection on the hard2 dataset, where v33 scored only 52.5% (GPT-OSS) and 64.5% (Gemma).

Linear magma scan found:
- M1: x*y = 4x+2y mod 5 — catches 13 new hard2 FALSE problems
- M2: x*y = 2x+4y mod 5 — catches 12 new
- M3: x*y = 3x+3y mod 5 — catches 4 new

## Cheatsheet
- cheatsheet_v34.txt (3,147 bytes) — v33 + M1, M2, M3 with coefficient method instructions

## Results @ 16k tokens

### hard2 (200 problems) — target dataset
| Model | v33 | v34 | Delta |
|---|---|---|---|
| GPT-OSS | 52.5% | **68.5%** | **+16.0** |
| Gemma | 64.5% | **72.5%** | **+8.0** |

GPT-OSS TN jumped from 13 to 40 (+27). Gemma TN from 35 to 56 (+21).

### hard3_100 (99 problems) — regression check
| Model | v33 | v34 | Delta |
|---|---|---|---|
| GPT-OSS | 88.9% | 87.9% | -1.0 (noise) |
| Gemma | 93.9% | 80.8% | **-13.1** (12 timeouts) |

### hard1 (69 problems)
| Model | v34 Accuracy | Notes |
|---|---|---|
| GPT-OSS | 49.3% | hard1 is very hard regardless |
| Gemma | 37.7% | 30 timeouts |

## Key Finding
The mod-5 magmas are a strong win for hard2 (+16/+8 points) with no GPT-OSS regression on hard3. However, the extra computation causes Gemma timeouts on hard3 (-13 points from 12 errors). This creates a tradeoff:

- **v33 is better for hard3-focused evaluation** (93.9% Gemma)
- **v34 is better for hard2-focused evaluation** (72.5% Gemma)

## Coefficient Method
The mod-5 magmas use the coefficient method rather than table lookups:
```
coeff(v) for (A*B) = (a*coeff_A(v) + b*coeff_B(v)) mod 5
```
This was validated at 100% accuracy over 120 trials in isolation testing (Test 21 extended).
