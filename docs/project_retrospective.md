# SAIR Mathematics Distillation Challenge — Project Retrospective

## What We Set Out To Do

The SAIR Mathematics Distillation Challenge asks competitors to write a ≤10,000 byte "cheatsheet" that gets injected into prompts sent to small LLMs. The LLM then determines whether one equational law implies another over all magmas — a problem from abstract algebra that requires both counterexample construction and proof derivation.

We started on April 3, 2026 with a blank slate and 17 days until the April 20 deadline. By April 13 we had built a system achieving 93.9% accuracy on our hardest test set with the best model. This document captures the journey.

---

## Phase 1: The Haiku Era (Apr 3–9)

### Starting Point

We inherited a codebase with 14 cheatsheet versions (v1–v14) and a test harness built for Claude Haiku 4.5. The best result was v13a at 65.2% on hard3 (400 problems), but it was over the 10KB byte limit. The submittable best was v17 at 63.5%.

We didn't know yet which models the competition would actually use.

### The Magma Battery Approach

The core of every cheatsheet version was the **magma battery** — a set of specific algebraic structures (magmas) the model tests each equation pair against. If EQ1 holds in a magma but EQ2 doesn't, that magma is a counterexample and the answer is FALSE.

The battery evolved from 6 simple magmas (v5) to 12 diverse ones (v13+):
- **A, B** — constant magmas (x*y=0, x*y=1)
- **C, D** — projections (x*y=y, x*y=x)
- **E** — XOR (x*y=x+y mod 2)
- **F** — addition (x*y=x+y)
- **G** — negate-right (x*y=1-y)
- **H, I** — shifts mod 3
- **J, K, L** — structured 3-element tables

This battery caught ~90% of FALSE cases on the "normal" difficulty dataset and ~65% on the harder "hard3" set.

### What We Tried on Haiku

**Token exhaustion (Tests 15-16).** Haiku was running out of tokens mid-response, producing unparseable output. We discovered the 4096 max_tokens setting was too low — raising to 20k eliminated unparsed responses and gained 3.4 accuracy points (63.3%→66.7%). This was our first "free lunch."

**Vacuous reasoning fix (Tests 17-19).** We identified 21 false positives caused by the model concluding "EQ1 fails in all battery magmas → unsatisfiable → vacuously true." We tried 5 different fixes:
- novac1: "lean FALSE instead" — too aggressive, killed TRUE recall (-7 points)
- novac2: "if EQ1 fails in ALL 13, lean FALSE" — still bled (-5 on TRUE)
- novac3: "EQ1 holds in a few AND EQ2 holds in ALL → lean TRUE; never say vacuously true" — best, within noise of baseline
- v20 "traps" section: advisory paragraphs about reasoning errors — completely ignored by the model
- v21 embedded traps: same ideas inside Step 5 rules — made things worse

**Key insight: rules at the point of decision beat advisory sections.** The model follows numbered rules in Step 5 but ignores freestanding advice. And more caveats in rules degrade each other (MOSAIC 2026 finding confirmed).

**Worked examples (Tests 11-13, 20-22).** We tried adding detailed worked examples for 3-element magma arithmetic. In isolation, the "decompose" strategy improved accuracy from 10-35% to 97-100%. But in the full cheatsheet, the extra content increased token usage without improving overall accuracy. The token cost offset the arithmetic benefit.

**Community cheatsheets (Tests 7, 14).** We benchmarked against community submissions:
- SimonRJ: 54.2% — theory-focused, very low TRUE recall (17.4%)
- AMEY: 52.0% — too brief
- Adam Betka: 55.0% — structural rules didn't help our framework

Our battery approach consistently outperformed all community sheets we tested.

**Linear magma expansion (Tests 21-23).** A computational scan of all linear magmas x*y=ax+by mod p found that x*y=2x+2y mod 3 catches 9 new hard3 FALSE problems with zero false positives. We proved Haiku computes mod-3 arithmetic at 100% accuracy (120/120 trials) but mod-5 at 0% on "holds" verification — a fundamental arithmetic barrier. The coefficient method (computing polynomial coefficients instead of brute-force table evaluation) later solved the mod-5 problem at 100% accuracy.

**Singleton signal analysis (Test 8).** The singleton detection — when testing EQ1 in left projection reveals x=y, suggesting EQ1 forces singleton magmas — was a double-edged sword. It correctly identified 68 TRUE cases but caused 45 false positives. Net +23, so removing it hurt overall, but it was responsible for 62% of all FPs.

### What We Learned in Phase 1

1. **The magma battery is the foundation.** Every cheatsheet variant that improved accuracy did so by improving the battery or its execution, not by adding reasoning rules.

2. **Haiku's arithmetic is unreliable.** 100% at finding EQ1 failures but only 10-35% at confirming EQ1 holds universally in 3-element magmas. This fundamental limitation capped our accuracy.

3. **Run-to-run variance is massive.** 37% of problems flipped verdicts between runs with the same cheatsheet at temperature=0. Single runs are unreliable for comparison.

4. **Less is more for instructions.** Every attempt to add advisory sections, traps, or caveats either had no effect or hurt performance. The model follows compact rules, not prose advice.

5. **Token budget matters more than cheatsheet quality.** Raising max_tokens from 4k to 20k gave more improvement than weeks of cheatsheet iteration.

---

## The Pivot: Competition Models Revealed (Apr 10)

On April 10, the official judge repository was released. The actual evaluation models were:
- **GPT-OSS-120B** (OpenAI) — reasoning model with hidden chain-of-thought
- **Llama 3.3 70B Instruct** (Meta) — standard instruction-tuned, no reasoning
- **Gemma 4 31B IT** (Google) — reasoning model, newest of the three

None of these were Haiku. Our weeks of Haiku optimization had been against the wrong target.

But the work wasn't wasted. The magma battery design, the structural checks, the error analysis methodology — all transferred directly. What changed was HOW the models used the cheatsheet, not WHETHER the cheatsheet content was valuable.

---

## Phase 2: Competition Model Optimization (Apr 10–13)

### The Three-Model Challenge

Each model had fundamentally different needs:

**GPT-OSS** wanted minimal prompting. As a reasoning model trained specifically for math, it burned 93% of its output tokens on hidden chain-of-thought before writing anything visible. Our 8KB cheatsheet gave it too much to think about. The model did its own theorem-proving and magma construction — far more sophisticated than our battery procedure.

**Llama** wanted maximum hand-holding. With no internal reasoning, it needed explicit procedures, worked examples, and structured output format. It followed our cheatsheet literally, testing each magma in order. But it capped at ~52% accuracy regardless of cheatsheet quality — it simply couldn't reason deeply enough for the hard problems.

**Gemma** was the strongest but slowest. Its reasoning mode consumed 8,000-17,000 tokens per problem, achieving 93.9% accuracy on hard3 when given enough tokens. But it was prone to timeouts at 2-15 minutes per call.

The competition required one cheatsheet for all three models. What helped GPT-OSS (compact) hurt Llama (needed verbose). What helped Gemma (more magmas) caused it to timeout.

### Provider Infrastructure

Testing efficiency required direct provider access:
- **Cerebras** for GPT-OSS: 30x faster than DeepInfra (~1-4s/call vs 2-3 min)
- **Google AI Studio** native API for Gemma: 32 parallel workers, visible reasoning tokens
- **DeepInfra** for Llama: reliable, no issues

We built `run_direct_test.py` — a unified test runner supporting all providers with retry logic, parallelism, and incremental result saving.

### The Compression Discovery (Tests 26-27)

Analyzing GPT-OSS responses revealed that **93% of output tokens were invisible reasoning**. Average visible output was only ~329 tokens out of ~4,861 total. On truncated responses, ALL 8,192 tokens went to hidden thinking with zero visible output.

This meant:
- Compact visible format barely mattered (only 7% of budget)
- Compact cheatsheet INPUT mattered enormously (less to reason about)
- Token cap was the binding constraint, not cheatsheet design

Testing confirmed: compact worked examples reduced average token usage by 8% and improved GPT-OSS accuracy from 46.5% to 59.6% by reducing truncations.

### The J, K, L Revelation (Test 29)

Cross-model error analysis on v29 (5 magmas) showed GPT-OSS and Gemma were complementary — they missed different problems. An oracle ensemble reached 99%. Of the 51 problems both got wrong, 23 were catchable by magmas we'd dropped during compression: J (null-left), K (swap-row2), and L (near-zero).

Adding them back as v33 produced the single biggest improvement of the project:
- GPT-OSS: 74.7% → **88.9%** (+14.2 points)
- Gemma: 86.9% → **93.9%** (+7.0 points)

The irony was acute. We'd spent days trying to shrink the cheatsheet, cutting these magmas because GPT-OSS "wasn't using them." But GPT-OSS was using them — just not in ways visible in its output. Its hidden reasoning was checking them, and removing them made the hidden reasoning less effective.

### Expanding to Hard2 (Test 30)

A new "hard2" test set proved much harder — v33 scored only 52.5% (GPT-OSS) and 64.5% (Gemma). Linear magma scanning found that x*y=4x+2y mod 5 and x*y=2x+4y mod 5 caught 25 new hard2 FALSE problems. Adding these as v34 gave:
- GPT-OSS hard2: 52.5% → **68.5%** (+16 points)
- Gemma hard2: 64.5% → **72.5%** (+8 points)

But v34 caused Gemma timeouts on hard3 (93.9% → 80.8%) because the extra magma evaluation added reasoning time. This created an unresolved tradeoff between hard2 and hard3 performance.

### The Verbose Regression (Test 31)

We hypothesized that combining v23's full verbose structure with v34's additions might give the best of both worlds, especially at a higher token cap (64k). The result was catastrophic:
- Gemma: 88-139 errors per dataset (most problems timed out)
- GPT-OSS: dropped 13-14 points across all datasets

**More content = more reasoning = worse performance.** This was the definitive proof that compact cheatsheets dominate for reasoning models.

### The Order-5 Wall (Test 32)

Order-5 equations (deeper nesting) proved completely resistant to all approaches:
- No linear counterexample exists at any prime ≤7
- No 3-element counterexample exists (all 19,683 searched)
- No 4-element counterexample found (52,000 searched)
- Cohomology dimension test: 0/163 caught
- Cohomology subspace containment: 0/163 caught

Both models scored ~49% on order5 (random chance) with 0 true negatives. The order-5 FALSE problems require counterexample magmas that are beyond any computationally feasible search space. This remains an open problem.

### The Llama Problem

Llama consistently capped at ~52% regardless of what we tried:
- v23 (verbose 12-magma battery): 51.5%
- v29 (compact 5-magma): 51.5% (but 0 TPs — pure FALSE)
- v31 (strict CE verification + TRUE default): 45.5% (over-predicted TRUE)
- v32 (holds-iff reformatted magmas): 50.5%
- Temperature 0.3 instead of 0.0: 53.5%

The fundamental issue: Llama has no internal reasoning mechanism, and these problems require multi-step logical deduction that Llama can't do in its visible output alone. With ~830 tokens of output per problem and no hidden scratchpad, it can't reason deeply enough to verify magma evaluations or construct proofs.

---

## What Worked

### The Magma Battery (High Impact)
The selection and refinement of test magmas was our highest-ROI activity. The battery approach is mathematically sound — if a counterexample exists among small magmas, the model will find it. The key was identifying WHICH magmas to include:
- C, D (projections) — universal, all models use them
- E (XOR) — GPT-OSS favorite, structural check
- H, I (shifts) — GPT-OSS uses effectively
- J, K, L (3-element tables) — critical for hard problems, adding them back was the biggest single win

### Compact Cheatsheet Design (High Impact)
For reasoning models, less is more. Our best sheets were 2.3-3.1KB, not 8-9KB. Each additional byte of instruction content adds to the model's internal reasoning burden without proportionally helping accuracy.

### Linear Magma Scanning (Medium Impact)
The computational analysis of all (a,b,p) parameter triples identified specific magmas that catch problems our battery misses. The mod-5 magmas added 16-27 points on hard2. The polynomial coefficient method made these magmas usable even when brute-force table evaluation was unreliable.

### Cross-Model Error Analysis (Medium Impact)
Comparing where GPT-OSS and Gemma fail revealed complementary error patterns and identified which magmas to add back. The oracle ensemble analysis (99% on hard3_100) showed the theoretical ceiling.

### Provider Optimization (Medium Impact)
Finding Cerebras for GPT-OSS (30x faster) and Google AI Studio native API for Gemma (parallelizable) transformed our iteration speed from hours to minutes per test cycle.

### CAUTION About Projection Over-generalization (Low-Medium Impact)
A single sentence warning GPT-OSS not to trust "EQ1 forces projection X → TRUE" reasoning added ~4 points by reducing false positives. But this kind of rule-based fix has diminishing returns.

---

## What Didn't Work

### Verbose Instructions for Reasoning Models
Every attempt to add more procedural detail, worked examples, verification steps, or advisory sections to the cheatsheet hurt reasoning model performance. The v36 experiment was the most dramatic failure — 9KB verbose at 64k tokens was catastrophic.

### Rule-Based Reasoning Fixes
Traps sections, embedded caveats, novac fixes, "lean FALSE/TRUE" defaults — these either had no effect or caused collateral damage. The models don't follow prose advice; they follow their training.

### Reformatting for Llama
Reordering magma descriptions (holds-iff first), strict CE verification requirements, default-TRUE flipping — none moved Llama past its ~52% ceiling. The problem is fundamental capability, not prompting.

### Cohomology Approach for Order-5
Mathematically elegant but computationally useless for order-5 problems. The equations have no linear models at any tested prime, so the cocycle space machinery has nothing to work with.

### Temperature Changes
Testing Llama at temperature 0.3 vs 0.0 showed no meaningful difference. The FALSE bias is structural, not sampling-related.

---

## Key Technical Insights

### 1. Token Budget is the Real Constraint
More important than cheatsheet content is how many tokens the model has to work with. Raising from 8k to 16k was worth more than any cheatsheet change. GPT-OSS at 64k unlimited scored 85.9% vs 59.6% at 8k — same cheatsheet.

### 2. Hidden Reasoning Dominates
For GPT-OSS and Gemma, 90%+ of output tokens are invisible chain-of-thought. You can't optimize what you can't see. The only lever is reducing input complexity so the model reasons less.

### 3. Magma Selection > Magma Count
Having the RIGHT magmas matters more than having MANY. v33 with 8 carefully chosen magmas outperformed v23 with 12. The 3-element table magmas (J, K, L) were disproportionately valuable.

### 4. Problems Have Tiers
- **Easy FALSE** (~65% of hard3): caught by 2-element magmas (projections, constants, XOR)
- **Medium FALSE** (~20% of hard3): caught by 3-element table magmas (J, K, L)
- **Hard FALSE** (~15% of hard3): need exotic magmas beyond any practical battery
- **Order-5 FALSE**: completely unsolvable by battery approach
- **TRUE problems**: require proof construction, which reasoning models handle well

### 5. Models Are Complementary
GPT-OSS and Gemma fail on different problems. An ensemble achieves 99%. A single cheatsheet can't capture both models' strengths, but it can avoid catastrophic failure on either.

### 6. Dataset Difficulty Varies Enormously
| Dataset | GPT-OSS (v34) | Gemma (v34) |
|---|---|---|
| hard3_100 | 87.9% | 80.8% |
| hard2 | 68.5% | 72.5% |
| hard1 | 49.3% | 37.7% |
| order5_half | 49.5% | 46.3% |

The same cheatsheet ranges from 88% to 38% depending on the dataset. Hard1 was curated to specifically resist our battery.

---

## Current State (Apr 13)

### Best Cheatsheets
- **v33** (2,752 bytes): Best on hard3 — GPT-OSS 88.9%, Gemma 93.9%
- **v34** (3,147 bytes): Best on hard2 — GPT-OSS 68.5%, Gemma 72.5%

### Open Problems
1. **Llama at 52%** — fundamental capability gap, no known fix
2. **hard1 performance** — needs larger magmas we can't search efficiently
3. **Order-5 problems** — completely resistant to battery approach
4. **v33 vs v34 tradeoff** — mod-5 magmas help hard2 but cause Gemma timeouts on hard3
5. **Token cap uncertainty** — official cap may be 8k, 16k, or higher

### Recommendation for Submission
Submit v33 as the primary candidate. It's compact (2,752 bytes), well under the 10KB limit, and achieves the highest accuracy on the hardest validated dataset. The mod-5 additions in v34 are valuable but the Gemma timeout risk makes them a gamble for the unknown test set.

---

## Lessons for Future Work

1. **Test on the actual evaluation setup as early as possible.** We spent a week optimizing for Haiku before discovering the real models. Even with incomplete rules, testing on the actual models would have saved days.

2. **Build computation tools early.** The linear magma scanner, 3-element brute force, and cohomology pipeline should have been built in the first few days. Computational analysis is more reliable than prompting intuition.

3. **Document as you go.** We documented well in Phase 1 (proper test folders) but fell behind in Phase 2 when iteration speed increased. This made it harder to trace decisions and avoid repeating experiments.

4. **Respect the "golden rule."** Never make claims without verification. Several times we stated conclusions ("all unparsed are max_tokens," "compact examples don't help") that turned out to be wrong when we actually checked the data.

5. **One change at a time.** When we made multiple changes simultaneously (v25's compressed examples + boxed format + output restructure), we couldn't attribute effects. Isolation testing is slower but produces reliable conclusions.

6. **The model knows more than you think.** GPT-OSS and Gemma are genuinely capable at this task — they construct proofs and invent magmas we didn't include. The cheatsheet's job isn't to teach them math; it's to give them the right tools (magmas) and get out of the way.
