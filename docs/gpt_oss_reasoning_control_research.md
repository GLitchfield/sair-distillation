# Controlling gpt-oss-120b Reasoning Token Consumption
## Research Report for SAIR Distillation Challenge

## The Core Problem

20% of gpt-oss-120b responses are returning with zero visible output. The model is burning the entire 8192-token budget on internal reasoning before emitting anything to the `final` channel. This is happening despite `reasoning: low` in the official config.

## Why This Is Happening: Understanding the Model

### gpt-oss is math-native and trained for extreme chain-of-thought

From OpenAI's own model card (arXiv:2508.10925):

> "The gpt-oss models are strong at math in particular, which we believe is because they can use **very long CoTs effectively**, e.g., our gpt-oss-20b uses **over 20k CoT tokens per problem on average for AIME**."

This is the critical fact. The model was trained specifically to spend enormous amounts of reasoning tokens on math problems. You're giving it math problems. With an 8K hard cap. Of course it runs out.

Even at `reasoning: low`, the model retains its math-maximalist instincts. "Low" just means "less than high" — it doesn't mean "fast." For genuinely hard magma implication problems, even low-reasoning gpt-oss may want 4K-8K+ tokens of thinking.

### Harmony format and the channel architecture

gpt-oss outputs across three channels in the Harmony format:
- **analysis** — raw chain-of-thought, internal reasoning
- **commentary** — tool calls and visible preambles
- **final** — user-facing response

Token budget is shared across all channels. If `analysis` consumes 8000 tokens, `final` gets 192 tokens — not enough for VERDICT + REASONING + PROOF + COUNTEREXAMPLE + \boxed{}.

When the model runs out of budget mid-analysis and gets cut off before switching to the final channel, you get an empty response.

### Reasoning level is a "hint", not a hard cap

From community testing: `Reasoning: low` in the system message is a soft guidance. The model can and does ignore it when faced with a task it considers complex. Setting `Reasoning: disabled` sometimes works on gpt-oss-20b but is unreliable, and isn't an officially supported value.

## Why Your Current Cheat Sheet May Be Making It Worse

Looking at `cheatsheet_v29_gpt.txt`, I see several patterns that actively encourage more reasoning:

### 1. The CAUTION section creates reasoning loops

```
CAUTION: "EQ1 forces the operation to be projection X" is NOT sufficient for TRUE. 
Other operations may also satisfy EQ1 while failing EQ2. Before concluding TRUE 
based on a derived operation form, construct 2+ DIFFERENT operations (e.g., 
permutation cycles, 3-element tables) and verify all satisfy EQ2. If you cannot, 
lean FALSE.
```

This tells the model: "don't trust your first answer; construct additional examples; verify everything." That's an invitation to think more. You're explicitly asking for additional reasoning steps the model then has to execute internally. The `Reasoning: low` budget can't accommodate "construct 2+ different operations and verify each."

### 2. Contradictory instructions force reasoning to reconcile them

From OpenAI's GPT-5 guide (applies to all reasoning models):

> "Poorly-constructed prompts containing contradictory or vague instructions can be more damaging... as [the model] expends reasoning tokens searching for a way to reconcile the contradictions rather than picking one instruction at random."

Your cheat sheet has implicit contradictions:
- "QUICK CHECKS" suggests fast decisions
- "Test these 5 magmas" suggests thorough checking
- "attempt to derive EQ2 from EQ1 by substitution" is a third path
- CAUTION says don't trust derived forms
- APPROACH says test then derive

The model has to reason about which path to take. That reasoning is internal and expensive.

### 3. Five magmas is a lot of mental state

Each magma evaluation requires the model to:
1. Parse the magma definition
2. Evaluate EQ1 against it
3. Evaluate EQ2 against it
4. Compare results

Across 5 magmas, that's ~20 evaluation steps. Even compact, that's real reasoning token cost.

### 4. The output format requests multiple fields

```
VERDICT: TRUE or FALSE
REASONING: brief
PROOF: if TRUE
COUNTEREXAMPLE: if FALSE
End your response with \boxed{TRUE} or \boxed{FALSE}.
```

The model has to plan what goes in each field before emitting to the final channel. That planning happens in `analysis`. More fields = more planning = more reasoning tokens.

### 5. "REASONING: brief" is vague

"Brief" is ambiguous. Is that 1 sentence? 3 sentences? A paragraph? The model has to decide, which costs reasoning tokens. Specific word/sentence limits would be cheaper.

## What the Research Says to Do

### Principle 1: Binary-friendly output minimizes reasoning

From OpenAI's gpt-oss-safeguard guide (their own recommended practice for gpt-oss classification tasks):

> "Binary output limits gpt-oss-safeguard's reasoning to a simple yes/no decision. Use this when speed matters more than understanding why the decision was made."

Their recommended binary format:
```
Return exactly one character: 0 or 1. Do not include any explanation or punctuation.
0 = Content does NOT violate this policy.
1 = Content violates this policy.
```

Stripped of all extra output. The model has nothing to plan except the single answer character.

Your equivalent: `\boxed{TRUE}` or `\boxed{FALSE}` as the ONLY required output. Everything else optional.

### Principle 2: Reinforce the output instruction at top AND bottom

From the same guide:

> "Be reinforced throughout the policy: repeat the output instruction at least once near the top (in 'INSTRUCTIONS') and again near the bottom (before 'EXAMPLES') to fortify compliance during reasoning."

The model's reasoning tokens repeatedly see the output format, which anchors the planning. Without this, the model may reason about what format to use.

### Principle 3: Pre-compress your cheat sheet aggressively

From the safeguard guide:

> "If you have a longer policy with multiple categories, consider pre-compressing each policy to **300-600 tokens**."

Your current cheat sheet is ~1700 chars (~450 tokens). That's within the recommended range, but the *cognitive density* is high — lots of procedural instructions. Fewer instructions = less reasoning about which to apply.

### Principle 4: Add an explicit escape hatch

From community testing (HuggingFace discussion #28 on gpt-oss-20b):

> "The Reasoning directive is a hint for the model. To handle a case where your input is unclear/ambiguous (which elicits a lot of inference by the model) it is better to append a rule to your system prompt to avoid unwanted cycles, for example: 'If the user is ambiguous or unclear, respond with Please clarify instead of answering.'"

Translated to your task: give the model permission to guess when stuck. Something like:

> "If you cannot determine the answer within 3 magma tests, output \boxed{FALSE} immediately."

This gives the model a pre-approved exit from reasoning loops. Without this, it keeps trying until it runs out of budget.

### Principle 5: Avoid micromanaging steps

Together AI's prompting guide for gpt-oss specifically warns:

> "**Avoid over-prompting**: Micromanaging steps can limit its advanced reasoning capabilities. **Provide clear objectives**: Balance clarity with flexibility for optimal results."

> "Think of GPT-OSS as a senior problem-solver — provide high-level objectives and let it determine the methodology."

This is the opposite of what your cheat sheet does. You're providing very specific procedures. For gpt-oss, you might get better results by stating the problem clearly and letting the model choose its approach — but with strict output constraints to cap the visible output.

### Principle 6: Reduce the number of choices

From OpenAI's policy:

> "Additional policies lead to small but meaningful degradations in accuracy."

Each additional magma or rule in your cheat sheet is a choice point. Fewer choices means less reasoning about which to apply. The data from your earlier analysis showed that 4 magmas (Zero, Right, Left, XOR) cover 85% of FALSE cases. Dropping from 5 to 3 or 4 magmas is probably fine.

## Concrete Recommendations

### Recommendation 1: Rewrite the cheat sheet with ruthless compression

Draft structure (~300 tokens):

```
Determine if EQ1 implies EQ2 over all magmas. Output exactly one line: \boxed{TRUE} or \boxed{FALSE}.

Test these 3 magmas. If any satisfies EQ1 but fails EQ2, output \boxed{FALSE}.

R: x*y = y. Any expression → rightmost leaf.
L: x*y = x. Any expression → leftmost leaf.
Z: x*y = 0 on {0}. All expressions → 0. EQ holds iff both sides identical OR both contain *.

If all 3 magmas satisfy both equations, output \boxed{TRUE}.

If you cannot determine after testing all 3, output \boxed{FALSE}.

EQ1: {{equation1}}
EQ2: {{equation2}}

Output: \boxed{TRUE} or \boxed{FALSE}
```

Notes on this draft:
- No `REASONING`, `PROOF`, `COUNTEREXAMPLE` fields — just the verdict
- Output instruction appears at the top AND bottom
- Only 3 magmas instead of 5
- Explicit escape hatch ("If you cannot determine, output FALSE")
- No CAUTION section
- No contradictory guidance
- Default-FALSE bias matches the data (your earlier analysis showed most hard problems are FALSE)

### Recommendation 2: Put EQ1/EQ2 LAST in the prompt

Currently your prompt probably starts with the equations at the top. Move them to the bottom, right before the output instruction. The reasoning tokens then see the equations *after* the rules, which keeps the rules fresh in the model's planning. This is a pattern from OpenAI's prompting guides — instructions near the problem statement.

### Recommendation 3: Strip all "think about this" language

Every phrase like "consider", "verify", "check whether", "before concluding" is a trigger for more reasoning. Replace with imperative statements: "Test X. If Y, output Z."

### Recommendation 4: Add max_tokens headroom check

In your test harness, log `completion_tokens_details.reasoning_tokens` for every response. If the 20% failures are all at ~8000 reasoning tokens, confirmed — it's a budget issue. If reasoning tokens are low but output is still empty, something else is going on.

```python
response = client.chat.completions.create(...)
print(f"Reasoning: {response.usage.completion_tokens_details.reasoning_tokens}")
print(f"Completion: {response.usage.completion_tokens}")
print(f"Finish reason: {response.choices[0].finish_reason}")
```

If finish_reason is `length` with high reasoning_tokens → budget exhaustion. Confirmed diagnosis.

### Recommendation 5: Try `Reasoning: disabled` (experimental)

Some community reports indicate that setting `Reasoning: disabled` in the system message works on gpt-oss models even though it's not officially supported. Worth a 20-problem smoke test to see if it reduces reasoning token usage. If it works on OpenRouter → DeepInfra, you may be able to bypass the reasoning budget entirely.

Note: this likely won't work through OpenRouter's standard API since the `reasoning_effort: low` is set in the model config, not in your prompt. You'd need to either:
- Modify `evaluation_models.json` locally for dev testing (add `"reasoning": "disabled"`)
- Test direct against the provider with a custom system message

### Recommendation 6: Avoid adding worked examples back in

The current cheat sheet has two worked examples. These are useful for small models to pattern-match on, but for a reasoning model, each example is additional content the model has to "read" during its analysis phase. This costs reasoning tokens even though the examples are in the input.

For gpt-oss specifically, consider no worked examples. For llama-3.3-70b (no reasoning), examples are more valuable. This is another argument for **different cheat sheets per model**.

### Recommendation 7: Investigate the "pre-inject final channel" hack

From HuggingFace discussion #50 on gpt-oss-120b, a community-discovered workaround:

> "The most effective way to stop reasoning at present is to append the following to the end of the message:
> `<|end|><|start|>assistant<|channel|>analysis<|message|><|end|><|start|>assistant<|channel|>`"

This pre-closes the analysis channel and opens the final channel, forcing the model to start its answer immediately without reasoning. Reported to work well in LM Studio and llama.cpp.

**Caveat**: this requires raw token access, which OpenRouter's standard chat completions API doesn't give you. You'd need to use a provider that exposes raw Harmony formatting. Worth trying if you self-host via vLLM, but likely not viable through the official judge pipeline.

## The Meta-Recommendation: Different Prompts Per Model

Your cheat sheet currently targets all three eval models with one prompt. But:
- **gpt-oss-120b**: reasoning model, burns tokens on internal thought. Needs ULTRA compact, binary output, no extra fields.
- **llama-3.3-70b**: no reasoning, needs explicit scratchpad, benefits from worked examples and step-by-step procedures.
- **gemma-4-31b**: reasoning on low, somewhere in between.

The official judge uses the same prompt for all three, and grades equally. You cannot send different prompts per model in the actual eval. But your cheat sheet has to work well enough on each.

The question becomes: what prompt structure minimizes failures on the most-fragile model without destroying performance on the others?

**Hypothesis**: the gpt-oss-friendly version (compact, binary-first, no extra fields) might also work on llama and gemma, because:
- llama can still think externally in its output even without fields (it'll just produce less structured output, but the verdict extractor is format-tolerant)
- gemma at low reasoning is similar to gpt-oss in needing compression

**Alternative hypothesis**: the compact version hurts llama because it doesn't give it enough scratchpad.

**Test this**: run the proposed compact cheat sheet on the 20 smoke test problems across all three models. Compare accuracy to your current v29. If accuracy on llama drops significantly, add a note at the end that lets llama think in the final channel without requiring it:

> "You may optionally write brief reasoning before the final boxed answer. The last boxed answer in your output is your verdict."

Since the judge's extraction rules say "within the same marker type, the last occurrence wins", you can emit multiple boxed answers — the last one counts. llama can reason and then commit; gpt-oss can skip straight to the answer.

## Summary

The problem is that gpt-oss was trained to burn 20k+ tokens on math problems, and your current cheat sheet is structured in a way that invites extended reasoning (CAUTION clauses, multiple verification steps, multi-field output format, 5 magmas to check). At 8K max_tokens, this produces 20% empty responses.

The fix is to:
1. **Cut the cheat sheet down** to binary-output-only, 300-400 tokens
2. **Remove verification/caution language** that triggers reasoning loops
3. **Reduce from 5 magmas to 3** (Zero, Right, Left cover most cases)
4. **Provide an explicit escape hatch** ("if unsure, output FALSE")
5. **Reinforce the output format** at top and bottom of the prompt
6. **Log reasoning tokens** to confirm the diagnosis
7. **Test per-model prompts** if the unified compact version hurts llama accuracy

The philosophical shift: stop trying to teach gpt-oss the math. It already knows the math. Your job is to **prevent it from over-thinking**, not to guide its thinking. Give it the minimum scaffolding needed for a verdict and let the model's training handle the rest.

## Sources

- OpenAI gpt-oss Model Card: arXiv:2508.10925
- OpenAI Harmony Response Format: https://cookbook.openai.com/articles/openai-harmony
- gpt-oss-safeguard User Guide: https://cookbook.openai.com/articles/gpt-oss-safeguard-guide
- Together AI gpt-oss Quickstart: https://docs.together.ai/docs/gpt-oss
- HuggingFace discussion on disabling reasoning: https://huggingface.co/openai/gpt-oss-120b/discussions/50
- HuggingFace discussion on reducing unwanted reasoning: https://huggingface.co/openai/gpt-oss-20b/discussions/28
- GPT-5 Prompting Guide (reasoning model principles): https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide
