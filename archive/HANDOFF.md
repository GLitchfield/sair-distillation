# SAIR Math Distillation Challenge — Handoff Document

## What This Project Is

The SAIR Foundation (co-founded by Terence Tao) launched a competition called the "Mathematics Distillation Challenge — Equational Theories" on March 13, 2026. The task: write a ≤10KB text "cheat sheet" that, when injected into a prompt, helps cheap LLMs correctly determine whether one equational law implies another over magmas (algebraic structures with a single binary operation).

- Competition page: https://competition.sair.foundation/competitions/mathematics-distillation-challenge-equational-theories-stage1/overview
- Tao's announcement: https://terrytao.wordpress.com/2026/03/13/mathematics-distillation-challenge-equational-theories/
- Playground: https://playground.sair.foundation/playground/mathematics-distillation-challenge-equational-theories-stage1
- YouTube walkthrough: https://www.youtube.com/watch?v=H5u2wtUE7UQ
- Zulip discussion: https://zulip.sair.foundation/#narrow/channel/13-Math-Distillation-Challenge---equational-theories/topic/discussions/with/191
- Submission deadline: April 20, 2026
- Top 1000 advance to Stage 2 (harder: must provide proofs/counterexamples)

---

## The Mathematical Problem

A **magma** is a set with a single binary operation * (no associativity, commutativity, or identity assumed). Given two equational laws like:
- Equation 1: `x * (y * z) = (z * w) * w`
- Equation 2: `x * (y * x) = (x * y) * z`

Determine: does Equation 1 **imply** Equation 2? (i.e., does every magma satisfying Eq1 also satisfy Eq2?)

This comes from the Equational Theories Project (ETP) which resolved all 22 million implications between 4,694 equational laws of order ≤4.

---

## How the Competition Works

### Prompt Template (from evaluation.jinja2)
```
You are a mathematician specializing in equational theories of magmas.
Your task is to determine whether Equation 1 ({{ equation1 }}) implies Equation 2 ({{ equation2 }}) over all magmas.
{% if cheatsheet is defined and cheatsheet %}
{{ cheatsheet }}
{% endif %}
Output format (use exact headers without any additional text or formatting):
VERDICT: must be exactly TRUE or FALSE (in the same line).
REASONING: must be non-empty.
PROOF: required if VERDICT is TRUE, empty otherwise.
COUNTEREXAMPLE: required if VERDICT is FALSE, empty otherwise.
```

The cheat sheet goes between the problem statement and the output format instructions. Max 10KB (10,000 bytes).

### Target Models (from the playground dropdown)
- OpenAI: gpt-oss-120b
- Meta: Llama 3.3 70B Instruct
- Google: Gemini 3.1 Flash Lite Preview
- xAI: Grok 4.1 Fast

All are cheap/fast models. Without a cheat sheet they score ~50% (coin flip).

### Datasets on HuggingFace
- **Problem set**: https://huggingface.co/datasets/SAIRfoundation/equational-theories-selected-problems
  - `normal` subset: 1000 problems, exactly 50% true / 50% false
  - `hard` subset: 200 problems, ~32% true / 68% false (curated to resist heuristics)
  - Also `hard1` and `hard2` subsets added recently
  - Download: https://huggingface.co/datasets/SAIRfoundation/equational-theories-selected-problems/resolve/main/data/normal.jsonl
  - Download: https://huggingface.co/datasets/SAIRfoundation/equational-theories-selected-problems/resolve/main/data/hard.jsonl
  
- **Benchmark data (no-cheatsheet baselines)**: https://huggingface.co/datasets/SAIRfoundation/equational-theories-benchmark
  - Contains runs from 25 models, 3 repeats each, on 200 hard problems
  - Subsets: benchmarks, runs (30K rows with raw responses), cells, leaderboard, models, prompt_templates
  - The benchmark page with heatmaps: competition.sair.foundation (Competitions > Equational Theories Benchmark)

### Scoring
- VERDICT must be parseable as TRUE or FALSE
- F1 score with strict parse-failure penalty (unparsed = wrong)
- Evaluated against a **private** subset (different from the 1200 public problems)
- If public set becomes saturated, they'll make evaluation harder

---

## Key Literature

### 1. The ETP Paper (most important)
- **Paper**: https://teorth.github.io/equational_theories/paper.pdf (arXiv:2512.07087)
- **Blueprint** (detailed math): https://teorth.github.io/equational_theories/blueprint.pdf
- **GitHub**: https://github.com/teorth/equational_theories
- **Dashboard**: https://teorth.github.io/equational_theories/dashboard/
- **Equation Explorer**: https://teorth.github.io/equational_theories/

Key findings from the paper:
- ALL positive implications (TRUE) were provable by automated theorem provers via rewriting
- ALL the hard work was in constructing counterexamples for FALSE cases
- Techniques for FALSE (in order of how many they resolved):
  1. **Small finite magmas** (brute force 2-4 element operation tables) — resolved the majority
  2. **Linear magmas** (x◇y = ax+by on a field) — large class of counterexamples
  3. **Translation-invariant magmas** (x◇y = x+f(y-x) on abelian group)
  4. **Twisting semigroup** invariant
  5. **Greedy/extension methods**
  6. **Syntactic methods** including variable-count criterion (Theorem 3.8)
- 37.12% of all implications were TRUE
- Problem is **undecidable** in general but all order ≤4 laws were resolved

### 2. Honda, Murakami & Zhang — Cheat Sheet ICL (the direct inspiration)
- **Paper**: https://aclanthology.org/2025.findings-emnlp.930/ (EMNLP 2025 Findings)
- **PDF**: https://aclanthology.org/2025.findings-emnlp.930.pdf
- **Code**: https://github.com/CyberAgentAILab/cheat-sheet-icl
- Method: Give frontier LLM many examples → ask it to summarize patterns → use summary as context for cheap model
- Cheat sheets transfer across models (GPT-4.1 → Gemini 2.0 Flash worked)
- Matched or beat many-shot ICL on 7/8 BBH tasks with far fewer tokens
- Their creation prompt: "identify difficult examples, write cheat sheet for those, exclude easy stuff"

### 3. Vampire ATP Results
- **Paper**: https://arxiv.org/html/2508.15856
- Vampire proved ALL true implications
- Challenge is in refuting false ones (counterexample construction)
- 310 undecided implications require infinite models

### 4. SAIR Foundation
- Blog: https://blog.sair.foundation/scaling-the-science-of-intelligence/
- Main site: https://sair.foundation
- Competition site: https://competition.sair.foundation/

---

## Our Data Analysis Findings

### Dataset distributions
| Set | Total | True | False | True Rate |
|-----|-------|------|-------|-----------|
| Normal | 1000 | 500 | 500 | 50.0% |
| Hard | ~200 | ~64 | ~136 | ~32% |

### Structural signal: LHS Simplification → ALWAYS FALSE (on normal set)
If eq2's LHS has fewer * operations than eq1's LHS: **188 problems → 0 true (0.0%)**. Example: eq1 LHS is "x * y" and eq2 LHS is "x" → ALWAYS FALSE. Mathematical reason: constraint on a product doesn't force constraint on bare elements.

### Variable analysis (normal set)
- eq2 introduces new variables NOT in eq1: 298 problems → 86 true (28.9%) — lean FALSE
- eq2 uses strict subset of eq1 vars: 702 problems → 414 true (59.0%) — lean TRUE
- eq2 has 2+ fewer vars: ~77% true

### CRITICAL WARNING
The hard problems were **deliberately curated to break structural heuristics**. Simple structural rules that get 82% on hard get only 40% on normal (worse than random!) because the patterns reverse. The cheat sheet MUST teach genuine mathematical reasoning.

### The Killer Finding: 2-Element Magma Coverage
We tested all 16 possible 2-element magmas against the normal set's 500 FALSE problems:
- **90.4% of FALSE implications** can be refuted by a 2-element magma counterexample
- **0% false positives** — no TRUE implication has a 2-element counterexample (by definition)
- Just 4 magmas cover 85% of FALSE cases:

| Magma | Description | Operation | Cumulative Coverage |
|-------|-------------|-----------|-------------------|
| Zero | constant 0 | 0*0=0, 0*1=0, 1*0=0, 1*1=0 | 34.4% |
| Right proj | x*y = y | 0*0=0, 0*1=1, 1*0=0, 1*1=1 | 58.2% |
| Left proj | x*y = x | 0*0=0, 0*1=0, 1*0=1, 1*1=1 | 76.8% |
| XOR | x+y mod 2 | 0*0=0, 0*1=1, 1*0=1, 1*1=0 | 85.2% |

Each has a simple **mental evaluation shortcut**:
- **Constant-0**: every * expression → 0. Equation holds iff both sides contain * (both become 0), or both are the same bare variable.
- **Right projection**: compound expression → its rightmost leaf variable.
- **Left projection**: compound expression → its leftmost leaf variable.
- **XOR**: count variable occurrences on each side. Equation holds iff every variable has same parity (even/odd count) on both sides.

All four shortcuts were **verified correct** against the actual magma evaluator.

---

## Current State of the Project

### Files in this directory
- `run_test.py` — Test harness supporting Anthropic (Haiku 4.5) and Gemini APIs
- `cheatsheet_v1.txt` — First draft cheat sheet (6,882 bytes / 10,000 byte limit)
- `normal.jsonl` — 1000 normal problems from HuggingFace
- `hard.jsonl` — **needs to be downloaded**: https://huggingface.co/datasets/SAIRfoundation/equational-theories-selected-problems/resolve/main/data/hard.jsonl
- `reference_doc.md` — Detailed reference document from literature review

### Cheat sheet v1 strategy
The cheat sheet teaches a concrete algorithm:
1. Quick structural checks (singleton detection, LHS complexity)
2. Test 6 specific counterexample magmas with mental evaluation shortcuts
3. Try linear magmas over Z/3Z
4. Attempt algebraic proof via substitution/rewriting
5. Default heuristic judgment

### Python environment
```bash
cd /mnt/c/Users/gavin/distillation
source venv/bin/activate  # venv already created with anthropic installed
export ANTHROPIC_API_KEY=...  # user has a key
```

### What hasn't been done yet
1. **No tests have been run yet** — we were about to run:
   ```bash
   python run_test.py --limit 20 --no-cheatsheet --output baseline_20.json
   python run_test.py --limit 20 --output v1_20.json
   ```
2. **hard.jsonl not downloaded yet**
3. **Cheat sheet not iterated** — v1 is a first draft based on analysis, needs empirical testing and refinement
4. **Haven't explored**: packing actual equation pairs/answers into the cheat sheet (Tao mentioned some competitors use "static lists of laws"), though he seemed to prefer reasoning-based approaches
5. **3.1KB of budget remaining** in the cheat sheet (currently 6.8KB of 10KB)

---

## Suggested Next Steps

1. **Run baseline and v1 on 20 problems** to measure lift
2. **Read the error cases** — look at the JSON output to see if the model is actually following the magma-testing steps or just guessing
3. **Iterate the cheat sheet** based on what types of errors occur:
   - If it's not following instructions → simplify/restructure
   - If it's making arithmetic errors on the magma tests → add worked examples
   - If it's failing on TRUE cases → improve the proof-strategy section
   - If it's failing on hard-set-specific patterns → may need different tactics
4. **Test on larger samples** (50, 100, full 1000) once the cheat sheet stabilizes
5. **Test on hard set** separately (different distribution, different patterns)
6. **Try the actual competition models** via the playground or Gemini API to check transferability
7. **Consider hybrid approach**: use some of the remaining 3.1KB budget for a compact lookup table of known tricky cases alongside the reasoning instructions

---

## Key Mathematical Theorems to Know

1. **Birkhoff completeness**: E implies E' iff E' can be derived from E by finite substitution rewrites
2. **Variable-count necessary condition** (Theorem 3.8 from blueprint): If each variable appears the same number of times on both sides of E, and E implies E', then each variable must appear the same number of times on both sides of E'
3. **Singleton detection**: If E has form x = f(y,z,...) where x doesn't appear on RHS, then E forces singleton magma, which satisfies everything → TRUE
4. **Duality**: E1 |= E2 iff dual(E1) |= dual(E2) (swap left/right arguments)
5. **Finite pigeonhole**: On finite magmas, injective ⟺ surjective, giving extra implications that don't hold for infinite magmas
