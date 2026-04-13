# Cheatsheet Versions

## Key Versions

| Version | Bytes | Era | Description |
|---|---|---|---|
| **v33** | 2,752 | Competition | **Best on hard3.** 8 magmas (C,D,E,H,I,J,K,L) + CAUTION. GPT 88.9%, Gemma 93.9% on hard3_100. |
| **v34** | 3,147 | Competition | **Best on hard2.** v33 + 3 mod-5 linear magmas (M1,M2,M3). GPT 68.5%, Gemma 72.5% on hard2. |
| v29_gpt | 2,300 | Competition | 5 magmas (C,D,E,H,I) + CAUTION. Pre-JKL addition. |
| v23 | 8,302 | Haiku | Full 12-magma battery with worked examples. Best for Haiku/Llama. |
| v23_compact | 7,528 | Transition | Compressed worked examples. First competition model test. |

## Version History

### Phase 1: Haiku (v1–v23)
- v1–v7: Initial magma battery development
- v8+: 5-step decision procedure established
- v13a: Peak Haiku accuracy (65.2%) but over 10KB limit
- v15–v19: Prompting improvements, token management, vacuous fix attempts
- v23: Added 2x+2y mod 3 linear magma

### Phase 2: Competition Models (v25–v36)
- v25: Added `\boxed{}` verdict format
- v27_minimal: Ultra-minimal (1.4KB) — proved GPT-OSS doesn't need hand-holding
- v28_gpt: 5-magma compact sheet optimized for GPT-OSS
- v29_gpt: Added CAUTION about projection over-generalization (+4% GPT)
- v30_binary: Research doc's ultra-compressed (579B) — 0 truncations but only 52.5%
- v31_llama: Strict CE verification for Llama — over-predicted TRUE
- v32_llama: Holds-iff reformatted magmas — no improvement
- **v33: Added J,K,L back — biggest single improvement (+14% GPT, +7% Gemma)**
- **v34: Added mod-5 linear magmas — +16% GPT on hard2**
- v35: Added near-zero-2 magma — marginal, Gemma regressed
- v36: Verbose 9KB version — catastrophic regression for reasoning models

### Key Lesson
Compact cheatsheets (~3KB) dramatically outperform verbose ones (~9KB) for reasoning models. The magma selection matters; the surrounding instructions should be minimal.
