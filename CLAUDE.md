# SAIR Math Distillation Challenge — Project Context

## Competition
- **Goal:** Write a ≤10,000 byte cheatsheet injected into LLM prompts to help models determine if one equational law implies another over all magmas
- **Deadline:** April 20, 2026
- **Scoring:** F1 score on a private test set; unparsed responses count as wrong
- **Evaluation models:** gpt-oss-120b (reasoning:low), Llama 3.3 70B (no reasoning), Gemma 4 31B (reasoning:low)
- **Token cap:** 8192 official, likely increasing to 16k+
- **One cheatsheet for all three models**, weighted equally
- **Judge repo:** `equational-theories-stage1-judge/` — uses `\boxed{}` > `VERDICT:` > bare line priority for verdict extraction

## The Math Problem
A **magma** is a set with a single binary operation `*` (no other properties assumed). Given two equational laws, determine if every magma satisfying Law 1 also satisfies Law 2.

- TRUE implications are provable by term rewriting (Birkhoff completeness)
- FALSE implications require constructing a counterexample magma
- Based on the Equational Theories Project (ETP) — all 22M implications between 4,694 laws of order ≤4 resolved
- Order-5 equations are significantly harder; battery approach fails completely

## Current Best Cheatsheets

| Version | Bytes | Description | Best for |
|---|---|---|---|
| **v33** | 2,752 | 8 magmas (C,D,E,H,I,J,K,L) + CAUTION | hard3 (GPT 88.9%, Gemma 93.9%) |
| **v34** | 3,147 | v33 + 3 mod-5 linear magmas | hard2 (GPT 68.5%, Gemma 72.5%) |

Llama caps at ~52% on all cheatsheets — fundamental capability limit.

## File Structure
```
CLAUDE.md                    ← this file
AGENT.md                     ← research assistant methodology
README.md                    ← GitHub-facing project overview

run_test.py                  ← Haiku/Gemini test harness (legacy)
run_direct_test.py           ← competition model test runner (multi-provider, parallel)
parallel_test.py             ← parallel test runner for Haiku
run_stability_test.py        ← repeated-run consistency testing
run_judge_test.py            ← OpenRouter-based judge harness

cheatsheets/                 ← all cheatsheet versions (v1–v36)
datasets/                    ← problem sets (JSONL) + test subsets
results/                     ← test run outputs (JSONL/JSON)
tests/                       ← documented test folders (1-32)
analysis/                    ← computational analysis scripts
docs/                        ← reference documents and research notes
archive/                     ← old files kept for reference
trash/                       ← files moved here instead of deleting
equational-theories-stage1-judge/ ← official competition judge
```

**Key datasets:**
| File | Problems | TRUE | FALSE | Notes |
|------|----------|------|-------|-------|
| `normal.jsonl` | 1000 | 500 | 500 | Baseline difficulty |
| `hard3.jsonl` | 400 | 195 | 205 | Primary hard test set |
| `hard3_100.jsonl` | 99 | 48 | 51 | Stratified iteration subset |
| `hard2.jsonl` | 200 | 100 | 100 | Harder curated set |
| `hard1.jsonl` | 69 | 24 | 45 | Hardest curated set |
| `hard_order5.jsonl` | 654 | 327 | 327 | Order-5 equations (unsolvable by battery) |

## Cheatsheet Architecture (v33/v34)

The cheatsheet is compact (~3KB) with:

**Quick checks** — structural patterns that give immediate verdicts:
- Singleton detection (EQ1 forces singleton → TRUE)
- Variable balance (balanced EQ1 + unbalanced EQ2 → FALSE)
- Disjoint variables (constant law detection)

**Magma battery** — 8-11 specific magmas to test:
- C (right projection), D (left projection) — formula-based, universally useful
- E (XOR mod 2) — parity check per variable
- H (right-shift mod 3), I (left-shift mod 3) — formula-based
- J (null-left), K (swap-row2), L (near-zero) — 3-element table magmas, critical for hard problems
- M1, M2, M3 (mod-5 linear) — coefficient method, help on hard2

**CAUTION** — warning against "EQ1 forces projection X → TRUE" over-generalization

**Output format** — VERDICT/REASONING/PROOF/COUNTEREXAMPLE + `\boxed{TRUE/FALSE}`

## Provider Setup

| Model | Provider | Speed | API |
|---|---|---|---|
| GPT-OSS-120B | Cerebras | ~1-4s/call | OpenAI-compat |
| Gemma 4 31B | Google AI Studio | ~2-15min/call, 32 parallel | Native Gemini API |
| Llama 3.3 70B | DeepInfra | ~20-30s/call | OpenAI-compat |

`run_direct_test.py` supports all providers with `--provider` flag. Supports `--parallel N` for concurrent requests and `--temperature` override.

## Key Technical Findings

### Model Behavior
- **GPT-OSS** burns 93% of output tokens on hidden reasoning. Compact cheatsheets (~3KB) work best. More content = more reasoning = more timeouts.
- **Gemma** is strongest (93.9% on hard3) but needs 8-17k reasoning tokens per problem and 16k+ token cap.
- **Llama** has no internal reasoning and caps at ~52% regardless of cheatsheet. The task requires reasoning Llama can't do.
- **Oracle ensemble** (GPT+Gemma) reaches 99% — models are highly complementary.

### Magma Battery
- J, K, L (3-element table magmas) are disproportionately valuable — adding them gave +14% GPT, +7% Gemma.
- Mod-5 linear magmas help on hard2 (+16% GPT, +8% Gemma) but cause Gemma timeouts on hard3.
- On hard3, our battery catches ~65% of FALSE problems. The rest need exotic magmas.
- On order-5, NO counterexample exists in any 3-element magma (all 19,683 searched), 4-element (52K searched), or linear magma (p≤7).

### Prompting
- Verbose cheatsheets (9KB) are catastrophic for reasoning models — v36 caused 88-139 Gemma errors per dataset.
- Advisory sections ("traps," "cautions") are largely ignored unless embedded in decision rules.
- Worked examples influence hidden reasoning style — compact examples reduce token burn ~8%.
- `\boxed{}` format has highest priority in the judge's verdict extraction.

## Running Tests

```bash
# GPT-OSS on hard3_100
python run_direct_test.py --provider cerebras --model gpt-oss-120b \
  --api-key $CEREBRAS_KEY --cheatsheet cheatsheets/cheatsheet_v33.txt \
  --problems datasets/hard3_100.jsonl --max-tokens 16384 --output results/test.jsonl

# Gemma on hard3_100 (parallelized)
python run_direct_test.py --provider gemini_native --model gemma-4-31b \
  --api-key $GOOGLE_KEY --cheatsheet cheatsheets/cheatsheet_v33.txt \
  --problems datasets/hard3_100.jsonl --max-tokens 16384 --parallel 32 --output results/test.jsonl

# Llama on hard3_100
python run_direct_test.py --provider deepinfra --model llama-3.3-70b \
  --api-key $DEEPINFRA_KEY --cheatsheet cheatsheets/cheatsheet_v23.txt \
  --problems datasets/hard3_100.jsonl --max-tokens 16384 --output results/test.jsonl
```

### Important Notes
- Never delete files — move to `trash/` instead
- Always check `wc -c` on cheatsheets — hard limit is 10,000 bytes
- Get explicit approval before running any test that costs tokens
- Document every test in `tests/` with README, cheatsheet copy, and results
- Use `hard3_100.jsonl` for iteration; full datasets for validation only

## Full History
- Phase 1 (Haiku, tests 1-22): see `tests/SUMMARY.md`
- Phase 2 (Competition models, tests 25-32): see `tests/SUMMARY.md`
- Full narrative: see `docs/project_retrospective.md`
