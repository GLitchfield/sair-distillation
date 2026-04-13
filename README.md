# SAIR Mathematics Distillation Challenge — Equational Theories

A competition to write a ≤10,000 byte cheatsheet that helps small LLMs determine whether one equational law implies another over all magmas.

## Key Results

Our best cheatsheets on the hard3 test set (400 problems, order ≤4 equations) at 16k token budget:

| Model | v33 (2.8KB) | v34 (3.1KB) |
|---|---|---|
| **Gemma 4 31B** | **93.9%** (F1=0.966) | 80.8% |
| **GPT-OSS 120B** | **88.9%** (F1=0.906) | 87.9% |
| Llama 3.3 70B | ~52% | ~52% |

On the hard2 test set (200 problems, harder curated):

| Model | v33 | v34 |
|---|---|---|
| Gemma | 64.5% | **72.5%** |
| GPT-OSS | 52.5% | **68.5%** |

Best cheatsheets: [`cheatsheets/cheatsheet_v33.txt`](cheatsheets/cheatsheet_v33.txt) and [`cheatsheets/cheatsheet_v34.txt`](cheatsheets/cheatsheet_v34.txt).

## The Problem

A **magma** is a set with a single binary operation `*` (no other axioms). Given two equations like `x*(y*z) = z*x` and `x*y = y*x`, determine if every magma satisfying the first also satisfies the second.

- **TRUE** implications are provable by algebraic rewriting (Birkhoff completeness)
- **FALSE** implications require constructing a counterexample magma
- Based on the [Equational Theories Project](https://teorth.github.io/equational_theories/) which resolved all 22M implications between 4,694 laws

## Approach

The cheatsheet teaches models a **magma battery** — specific algebraic structures to test each equation pair against. If EQ1 holds in a magma but EQ2 doesn't, that magma is a counterexample proving FALSE.

The battery evolved through 36 versions, from 6 simple 2-element magmas to a curated set of 8-11 magmas spanning projections, XOR, modular shifts, and structured 3-element tables. Key additions include mod-5 linear magmas evaluated via a polynomial coefficient method.

For TRUE detection, the cheatsheet includes structural checks (singleton detection, variable balance) and lets the reasoning models construct their own proofs.

## Project Structure

```
CLAUDE.md                    ← Project context for Claude Code sessions
AGENT.md                     ← Research assistant methodology guidelines
README.md                    ← This file

cheatsheets/                 ← All 36+ cheatsheet versions
  cheatsheet_v33.txt         ← Best for hard3 (2,752 bytes)
  cheatsheet_v34.txt         ← Best for hard2 (3,147 bytes)

datasets/                    ← Problem sets (JSONL)
  normal.jsonl               ← 1,000 problems, baseline difficulty
  hard3.jsonl                ← 400 problems, harder curated
  hard2.jsonl                ← 200 problems, even harder
  hard1.jsonl                ← 69 problems, hardest
  hard_order5.jsonl           ← 654 problems, order-5 equations
  hard3_100.jsonl            ← 99-problem stratified subset for iteration

results/                     ← All test run outputs
tests/                       ← Documented test folders with writeups
docs/                        ← Research notes and analysis
  project_retrospective.md   ← Full project narrative
  three_models_comparison.md ← Competition model analysis
  gpt_oss_reasoning_control_research.md
  cohomology_precomputation_proposal.md
  prompting_strategy_guide.md
  research_small_model_prompting.md

analysis/                    ← Computational analysis scripts
  linear_magma_scan.py       ← Scan linear magmas for counterexamples
  cohomology_scan.py         ← Cocycle space dimension testing
  magma4_search.py           ← 4-element magma brute force search

run_test.py                  ← Haiku/Gemini test harness
run_direct_test.py           ← Competition model test runner (multi-provider)
parallel_test.py             ← Parallel test runner for Haiku
run_stability_test.py        ← Repeated-run consistency testing

equational-theories-stage1-judge/  ← Official competition judge (submodule)
```

## Running Tests

### Competition models (GPT-OSS, Llama, Gemma)

```bash
# GPT-OSS via Cerebras
python run_direct_test.py --provider cerebras --model gpt-oss-120b \
  --api-key $CEREBRAS_API_KEY \
  --cheatsheet cheatsheets/cheatsheet_v33.txt \
  --problems datasets/hard3_100.jsonl \
  --max-tokens 16384 --output results/test.jsonl

# Gemma via Google AI Studio (native API, parallelized)
python run_direct_test.py --provider gemini_native --model gemma-4-31b \
  --api-key $GOOGLE_API_KEY \
  --cheatsheet cheatsheets/cheatsheet_v33.txt \
  --problems datasets/hard3_100.jsonl \
  --max-tokens 16384 --parallel 32 --output results/test.jsonl

# Llama via DeepInfra
python run_direct_test.py --provider deepinfra --model llama-3.3-70b \
  --api-key $DEEPINFRA_API_KEY \
  --cheatsheet cheatsheets/cheatsheet_v33.txt \
  --problems datasets/hard3_100.jsonl \
  --max-tokens 16384 --output results/test.jsonl
```

### Haiku (legacy)

```bash
export ANTHROPIC_API_KEY=...
python parallel_test.py --cheatsheet cheatsheets/cheatsheet_v23.txt \
  --subset hard3 --output results/test.json --workers 6
```

### Analysis tools

```bash
# Scan linear magmas for counterexamples
python analysis/linear_magma_scan.py

# Run cohomology analysis on order-5 problems
python analysis/cohomology_scan.py datasets/order5_half.jsonl
```

## Key Findings

1. **Compact cheatsheets win for reasoning models.** 3KB outperforms 9KB because less content = less hidden reasoning = fewer timeouts.

2. **The magma battery is the foundation.** Selecting the right counterexample magmas matters more than any prompting technique.

3. **Token budget is the binding constraint.** Raising from 8k to 16k tokens was worth more than weeks of cheatsheet iteration.

4. **Models are complementary.** GPT-OSS and Gemma fail on different problems — an oracle ensemble reaches 99%.

5. **Order-5 equations are unsolvable by battery approach.** No counterexample exists in any 3-element magma, 4-element structured search, or cohomological analysis.

See [`docs/project_retrospective.md`](docs/project_retrospective.md) for the full narrative of what we tried and learned.

## Competition

- [SAIR Mathematics Distillation Challenge](https://competition.sair.foundation/competitions/mathematics-distillation-challenge-equational-theories-stage1/overview)
- [Equational Theories Project](https://teorth.github.io/equational_theories/)
- [Official Judge Repository](https://github.com/SAIRcompetition/equational-theories-stage1-judge)
