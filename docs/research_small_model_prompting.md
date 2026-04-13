# Research: Getting the Most from Small Models
*Compiled 2026-03-28 for the SAIR Math Distillation project*

This document summarizes what is known about prompting small/cheap LLMs (Claude Haiku, Gemini Flash Lite) to reliably execute complex multi-step instructions and arithmetic. Findings are drawn from 2022–2026 papers plus Anthropic's own documentation. Each section ends with a **direct application** note for this project.

---

## 1. Instruction Following: Getting Models to Actually Comply

**The core finding:** Compliance is a distinct skill from task accuracy. A model can get the right answer while failing to follow the format or procedure you specified. The MOSAIC benchmark (Jan 2026) showed that compliance varies significantly by constraint *type*, *quantity*, and crucially *position* in the prompt — not just whether the instruction is clear.

**What works:**

- **Imperative present-tense commands outperform suggestions.** "Step 3: Evaluate Magma D" beats "In step 3, you should evaluate Magma D." Anthropic's own best practices document confirms this.
- **Explain *why* a rule exists, not just what it is.** "Never skip step 4 because the model often mistakes absence-of-proof for a TRUE answer" is more effective than just "Do not skip step 4." Models generalize from reasoning, not just pattern-match the rule.
- **Separate task description from constraints when optimizing prompts** (2601.03359). Treating "what to do" and "how to do it / what not to do" as separate optimization targets improved compliance on 8B models significantly.
- **Position matters: put the most critical instructions at the very end**, immediately before the problem. The "Lost in the Middle" paper (TACL 2024) showed a U-shaped attention curve — beginning and end are attended to much better than the middle. MOSAIC (Jan 2026) confirmed this: middle-of-prompt instructions are systematically under-followed.
- **Certain instruction combinations interact harmfully** (MOSAIC 2026): stacking many constraints in one step degrades each one. Atomic steps — one action, one output — are more reliably followed.

**Reliability caution:** IFEval++ (Dec 2025) showed models that appear to be near-ceiling on standard compliance benchmarks drop up to 61.8% when prompts are rephrased slightly. Compliance is fragile.

**Direct application:** The step procedure in the cheatsheet should go at the *very end*, immediately before the problem. The magma tables and background can live in the middle. Each step should be one action only. Add "why" explanations for non-obvious rules, especially the CE verification step.

---

## 2. Arithmetic and Symbolic Calculation Reliability

**The core finding:** Chain-of-thought is necessary but not sufficient. It doesn't fix the three main error types: (1) semantic misunderstanding, (2) calculation errors in individual steps, and (3) skipping required steps. Small models exhibit all three more than large ones.

**What works:**

- **Explicit intermediate values in scratchpad** (Nye et al., 2021, still the most-cited work). Requiring the model to write intermediate values — "LHS of EQ1 in Magma D: x appears odd times (1), y appears odd times (1) → fails" — dramatically reduces errors vs. computing in a single step. Crucially, blank filler tokens (just giving more space) provide *no benefit*. The reasoning content itself is what matters.
- **Explicit labeling by type.** "x-count-LHS=1, x-count-RHS=3" is more reliable than inline prose. Small nudges like naming intermediate values reduce compounding errors.
- **Fragile Thoughts (Mar 2026) quantified CoT error propagation.** If a wrong intermediate value enters the reasoning chain, small models lose 50–60% accuracy on the final answer. The most important intervention is preventing incorrect intermediate values, not adding more steps. Notably: extra redundant steps cause almost no harm (0–6% loss), so padding CoT with verification steps is safe.
- **Unit/type conversion errors don't scale away.** Fragile Thoughts found dimensional/unit reasoning errors persist even in very large models. For this project: the "left arg vs right arg" distinction for Magmas H and I is exactly this type of error. It will not be fixed by making the model reason longer.

**Direct application:** For Magmas H and I, the cheatsheet should require the model to write out each sub-expression evaluation *step by step* (e.g., "inner: z*x = (x+1)%3 = a; outer: y*a = (a+1)%3 = b") rather than trying to compute the full nested expression in one shot. This is exactly where the current FN errors live.

---

## 3. Self-Verification: What Works and What Doesn't

**The honest finding:** Generic self-correction largely doesn't work, especially for small models. The 2024 papers "Large Language Models Cannot Self-Correct Reasoning Yet" (ICLR) and "Small Language Models Need Strong Verifiers to Self-Correct Reasoning" (ACL) established this clearly: the model that made the error uses the same weights to check it, and tends to confirm its prior output (hallucinated compliance).

**What does work:**

- **Decomposed verification with forced computation output.** Rather than "check your answer," the Chain of Verification (CoVe) approach structures verification as answering specific questions about the output. For this project: "write out the LHS and RHS values separately for 3 distinct assignments before concluding" forces genuine computation rather than faked confirmation.
- **The v8/v11 CE verification step is sound in principle** — but it only works for Haiku because Haiku is above the capability threshold. The Gemini failure (ignored in 176/188 FN cases) is the predicted behavior for a model below that threshold.
- **Anthropic's 2026 reasoning faithfulness paper** (important new finding): CoT is *least faithful on harder tasks*. The cases where you most want reliable self-monitoring are exactly where it's least trustworthy. This means for the hard3 problems, we should not rely on Haiku's self-stated reasoning being accurate — only on the structured outputs it produces.
- **STaSC (Mar 2026):** small models CAN learn to self-correct through iterative self-generated data, without needing a strong external verifier. This is a meaningful update to the 2024 consensus. However, this is a fine-tuning technique, not a prompting technique — not directly applicable here.

**Direct application:** Don't rely on prose self-checks ("verify your work"). Instead, require explicit output of intermediate values that are hard to fake correctly without actually computing. E.g., "State the value of both sides for assignments (0,0,0), (1,0,0), (0,1,0)."

---

## 4. Format and Structure

**What works:**

- **XML tags for separating types of content** (instructions vs. data vs. examples), not for constraining the reasoning process itself.
- **"Let Me Speak Freely?" (2024, widely confirmed in 2026):** enforcing strict format *during reasoning* hurts performance. The right approach: allow free-form reasoning, then require a structured final answer. The current `VERDICT: TRUE/FALSE` format is correct.
- **Think Inside the JSON** (2502.14905): for tasks requiring structured output at the end, a two-step process (reason freely → then format) preserves accuracy vs. enforcing structure throughout.

**What doesn't work:**

- Long instruction lists where constraints interact. Each additional constraint competes with the others (MOSAIC 2026).
- Asking for structured XML or JSON *during* the reasoning steps — this constrains the very thing that needs to be free.

**Direct application:** Current design (free-form reasoning, final `VERDICT:` line) is correct. Do not add format requirements to intermediate steps.

---

## 5. Reasoning Length vs. Quality

**The "overthinking" problem is real.** For binary decision tasks, very long reasoning chains can become counterproductive: the model's attention to the original problem statement decays as the chain extends, and it starts reasoning about its most recent intermediate conclusion rather than the original constraints.

**Key nuance (Fragile Thoughts / ReBalance 2026):** The distinction is between *prose deliberation length* (bad to over-extend) and *computation step count* (safe to extend). Shorter prose is often fine; abbreviating explicit computation steps reliably increases errors.

**Distilled reasoning models are MORE sensitive to prompt-level suppression** (ReBalance, Mar 2026). Attempts to tell a distilled model (like DeepSeek-R1 distillations) to "think briefly" can cause large accuracy drops. This is a new finding — prior 2025 guidance said it was safe.

**CoT is often decorative on easy problems.** In most frontier model/task pairs, removing any single CoT step changed the final answer less than 17% of the time. The model on easy problems is not actually using its chain-of-thought to reach the answer — it's post-hoc rationalizing. This means monitoring CoT on easy cases tells you little; monitoring it on hard cases is where you need it most (but also where it's least faithful, per Anthropic 2026).

**Direct application:** Keep step prose short and directive. Invest words in explicit computation steps. Don't add prose "reflection" steps — they add length without helping.

---

## 6. Few-Shot Examples: The Highest-ROI Intervention

**Consistent finding across 2022–2026:** For complex multi-step procedures with a specific output format, few-shot examples are the single highest-leverage prompting intervention for small models. They outperform instruction improvements alone for tasks that involve novel procedure execution.

**How to do it right:**
- 3–5 examples minimum, wrapped in `<example>` tags
- Cover both TRUE and FALSE cases
- Show the full step-by-step reasoning with explicit intermediate values
- Ensure diversity — don't cluster examples around one magma type (anchoring bias)

**Anchoring bias is architectural, not fixable by prompting.** Models anchor disproportionately on concrete examples. CoT, reflection instructions, and explicit "ignore this anchor" hints all fail to eliminate it (ACL 2024 anchoring paper). This means: the examples you choose matter a lot, and the set must be diverse.

**Direct application:** Adding 2–3 worked examples with explicit magma evaluation tables to the cheatsheet is likely worth more than adding another magma to the battery. Current cheatsheet has no examples.

---

## 7. Known Systematic Failure Modes

| Failure Mode | Description | Mitigation |
|---|---|---|
| **Recency bias** | Last instruction in prompt dominates | Put decision procedure last; put warnings near the relevant step |
| **Anchoring** | Over-applies concrete examples to other cases | Use diverse examples; cover edge cases explicitly |
| **Hallucinated compliance** | Appears to follow instructions without computing | Force verbatim intermediate output that can't be faked |
| **Shortcutting to signal** | Detects surface patterns instead of executing procedure | Remove or reframe signals as "not sufficient alone"; require proof attempt |
| **Semantic interference** | Framing of question changes reasoning even on same math | Be consistent in how the implication direction is framed |
| **CoT error propagation** | Wrong intermediate value cascades to wrong answer | Force step-by-step with labeled values; prevent inline multi-step computation |

---

## 8. What is NEW in 2026 (vs. prior knowledge)

The following are genuine updates to 2025 understanding:

1. **CoT faithfulness degrades on hard tasks specifically** (Anthropic 2026). Harder problems → less faithful reasoning traces → can't rely on the stated reasoning being the actual reasoning.

2. **UnitConversion/type errors don't scale away** (Fragile Thoughts, Mar 2026). Left-arg vs. right-arg errors for Magmas H/I are exactly this type. No amount of larger model or more reasoning fixes this without explicit step-by-step scaffolding.

3. **Distilled reasoning models are more sensitive to prompt-level suppression** (ReBalance, Mar 2026). Not applicable to Haiku/Flash Lite directly, but relevant if we ever test a reasoning-distilled model.

4. **Middle-of-prompt instructions are significantly under-followed** (MOSAIC, Jan 2026). Quantified clearly for the first time. Actionable: move the most critical rules to the end of the prompt.

5. **Instruction position + combination interactions matter as much as content** (MOSAIC, Jan 2026). Stacking many constraints in one section degrades each one.

6. **Compliance drops up to 61.8% with prompt rephrasing** (IFEval++, Dec 2025, widely cited in 2026). Benchmark compliance scores are fragile — test on paraphrases, not just the original phrasing.

---

## Summary: Top Actionable Changes for This Project

Ordered by expected impact:

1. **Add 2–3 worked examples** (TRUE case + FALSE case + tricky case) with full step-by-step evaluation, including explicit intermediate values for magma evaluations. This is the biggest missing piece.

2. **Add step-by-step evaluation scaffolding for Magmas H and I specifically.** Require writing each sub-expression value before combining. This directly addresses the 14/18 FN errors.

3. **Move the step procedure to the very end of the cheatsheet**, immediately before the problem. Tables and background go in the middle.

4. **Add "why" explanations for the two most-violated rules:** (a) why failing to find a CE doesn't mean TRUE, (b) why EQ1 must hold for ALL assignments for a CE to be valid.

5. **Keep step prose atomic and short.** Each step = one action. Don't chain multiple actions in one step.

6. **Do not add more prose self-check steps** — they don't help and add length. Add forced intermediate computation outputs instead.

---

*Sources: Wei et al. 2022 (CoT); Nye et al. 2021 (Scratchpads); "Large LLMs Cannot Self-Correct" ICLR 2024; "Small LMs Need Strong Verifiers" ACL 2024; "Lost in the Middle" TACL 2024; "Let Me Speak Freely?" 2024; Anthropic Claude 4 Prompting Best Practices; MOSAIC 2601.18554 Jan 2026; Fragile Thoughts 2603.03332 Mar 2026; ReBalance 2603.12372 Mar 2026; Anthropic Reasoning Faithfulness 2026; IFEval++ 2512.14754 Dec 2025; Thinking Intervention 2503.24370 Mar 2026; STaSC 2503.08681 Mar 2026; HIPO 2603.16152 Mar 2026.*
