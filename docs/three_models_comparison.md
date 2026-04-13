# The Three Models: Profiles, Tensions, and Balance
## A Strategic Guide for the SAIR Distillation Challenge

## TL;DR

You're writing one prompt for three fundamentally different models that disagree about what good prompting looks like. The judge weights them equally, so your score is roughly the minimum performance across the three. The weakest model on your prompt determines your grade.

The three models sit at different points on a spectrum:
- **gpt-oss-120b**: reasoning-maximalist; wants you to get out of its way
- **llama-3.3-70b**: no internal reasoning; wants you to spell everything out
- **gemma-4-31b**: reasoning-on-low; somewhere in between but newest and least understood

What helps one hurts another. The challenge isn't finding the "best" prompt — it's finding the prompt that doesn't catastrophically fail on any of the three.

---

## Model Profiles

### gpt-oss-120b (OpenAI, via deepinfra/bf16)

**Architecture**: 117B total parameters with 5.1B active per token. Mixture-of-Experts with 128 experts, top-4 routing. 36 layers. MXFP4 quantization native. Uses OpenAI's o200k_harmony tokenizer (201K vocab).

**Training philosophy**: Reasoning-first. Post-trained with heavy reinforcement learning on verifiable tasks (similar to OpenAI's o3/o4-mini). The model was deliberately trained to use long chain-of-thought on math problems — OpenAI's model card explicitly notes that gpt-oss-20b uses over 20,000 CoT tokens per AIME problem on average. The 120B version is in the same regime.

**Harmony format**: Outputs across three channels — `analysis` (raw CoT, hidden by convention), `commentary` (tool calls), and `final` (user-facing answer). Token budget is shared across all channels. If the model burns 8K tokens in `analysis`, `final` gets nothing.

**Reasoning levels**: low / medium / high, set in system message (currently `low` in the official config). These are soft hints, not hard caps. Even at "low", the model can choose to burn significant budget on hard problems.

**Strengths**: Math, coding, scientific reasoning, multi-step logic, agentic tasks. Particularly strong on problems where long CoT pays off.

**Weaknesses**: 
- Burns reasoning tokens on any contradictions or vagueness in the prompt
- Can exceed token budgets on hard problems even at low effort
- The training creates a strong instinct to think extensively on math regardless of instructions
- Fragile to over-prompting; micromanagement hurts it

**What it wants from a prompt**:
- Clear objectives, not procedural micromanagement
- No contradictory instructions
- Minimal scaffolding — "trust the model"
- Binary output format (the safeguard guide explicitly recommends this)
- Escape hatches for ambiguous cases ("if unsure, output X")
- Instructions reinforced at top AND bottom of prompt

**Official guidance (OpenAI)**: 
> "Think of GPT-OSS as a senior problem-solver — provide high-level objectives and let it determine the methodology. Avoid over-prompting: micromanaging steps can limit its advanced reasoning capabilities."

**Judge config**: temp 0.0, max_tokens 8192, reasoning: low, seed 0, pinned to `deepinfra/bf16`.

---

### llama-3.3-70b-instruct (Meta, via deepinfra/fp8)

**Architecture**: 70B dense parameters. Decoder-only transformer, Grouped-Query Attention. 128K vocabulary (tiktoken-based). No mixture-of-experts.

**Training philosophy**: Standard instruction-tuned model. SFT + RLHF. Pretrained on ~15 trillion tokens. No reinforcement learning for reasoning specifically. **No internal chain-of-thought mechanism** — any reasoning it does happens in the visible output.

**No reasoning mode**: This is critical. Llama has no "thinking channel" separate from its output. If you want it to reason about a problem, it has to write the reasoning out loud. The official config has `reasoning: disabled` because there's nothing to enable.

**Strengths**: Instruction following, multilingual support, general knowledge, conversational responses. Strong performance on benchmarks when prompted with explicit chain-of-thought.

**Weaknesses**:
- Math performance significantly benefits from explicit CoT prompting — without a scratchpad, it makes arithmetic mistakes
- Can be verbose ("helpful assistant" training)
- Sometimes adds preamble/postamble that pollutes structured outputs
- Not as strong on pure reasoning as the specialized reasoning models

**What it wants from a prompt**:
- Explicit "think step by step" instructions
- Worked examples (few-shot prompting)
- Clear output format with explicit markers
- Room to reason in the visible output (scratchpad space)
- Specific procedural instructions it can follow literally

**Official guidance (Meta, from Llama prompt engineering docs)**:
> "Detailed, explicit instructions produce better results than open-ended prompts. Giving explicit instructions is like placing rules and restrictions on how the model responds to your prompt."

> "Adding specific examples of your desired output generally results in a more accurate, consistent output when compared with zero-shot prompting."

This is the **exact opposite** of the gpt-oss guidance. One model wants you to over-prompt, the other wants you to under-prompt.

**Judge config**: temp 0.0, max_tokens 8192, reasoning: disabled, seed 0, pinned to `deepinfra/fp8`.

---

### gemma-4-31b-it (Google, via novita/bf16)

**Architecture**: 30.7B dense parameters. Released April 2, 2026 — the youngest model in the eval set. Uses Google's SentencePiece tokenizer. 256K context window. Multimodal (text, image, video input). Hybrid attention mechanism with interleaved local sliding window and full global attention.

**Training philosophy**: Reasoning-capable with configurable thinking mode. Built from similar research to Gemini 3 but open-weight. All Gemma 4 models are "designed as highly capable reasoners with configurable thinking modes."

**Reasoning mode**: Has thinking/reasoning that can be controlled. The official judge config sets `reasoning: low`. Less is publicly documented about exactly how this works internally compared to gpt-oss's Harmony format.

**Strengths**: Strong intelligence-per-parameter ratio. Per Artificial Analysis, scores 39 on their Intelligence Index v4.0 — "well above average." Strong on reasoning, coding, math, and multimodal tasks.

**Weaknesses**:
- Artificial Analysis describes it as "notably slow" (36 t/s on first-party Google AI Studio)
- "Somewhat verbose" — uses more tokens than average to reach answers
- Brand new (days old as of April 10, 2026) — very little community knowledge about its quirks
- The reasoning behavior under "low" effort is not as well-documented as gpt-oss

**What it probably wants from a prompt** (extrapolating from sibling models and Google's Gemma/Gemini prompting patterns):
- Clear structure with headers or delimiters
- Explicit output format specifications
- Moderate amount of guidance — not as bare as gpt-oss, not as hand-held as llama
- Since it's verbose by default, needs explicit length constraints

**Key unknown**: Because it was released on April 2, 2026, there isn't enough community testing to know exactly how it responds to different prompt styles. You'll need to treat the smoke tests on gemma as your primary source of truth, not external docs.

**Judge config**: temp 0.0, max_tokens 8192, reasoning: low, seed 0, pinned to `novita/bf16`.

---

## Side-by-Side Comparison

| Attribute | gpt-oss-120b | llama-3.3-70b | gemma-4-31b |
|---|---|---|---|
| Architecture | MoE, 5.1B active | Dense 70B | Dense 31B |
| Reasoning mode | Yes (Harmony channels) | **No** | Yes (thinking mode) |
| Reasoning budget competes with output? | **Yes** | N/A | Yes |
| Training for long CoT on math | **Heavy RL** | None specifically | Moderate |
| Tokenizer | o200k_harmony (201K) | tiktoken (128K) | SentencePiece |
| Prefers procedural instructions? | **No** (hurts it) | **Yes** (helps it) | Moderate |
| Benefits from worked examples? | Neutral/negative | **Strong positive** | Likely positive |
| Tendency to be verbose | Low in final channel | Moderate | **High** |
| Max safe visible output at 8K cap | 2-8K depending on reasoning | Full 8K | 4-8K |
| Sensitivity to prompt contradictions | **Very high** | Low | Unknown |
| Native instinct on hard math problems | Think for 10K+ tokens | Answer directly | Think moderately |
| Release date | Aug 2025 | Dec 2024 | **Apr 2, 2026** |
| Community knowledge | High | Very high | **Very low** |

---

## The Fundamental Tensions

### Tension 1: Procedural specificity

- **llama wants**: "Test magma 1: x*y=y. Check if both equations hold. Then test magma 2: x*y=x..."
- **gpt-oss wants**: "Determine if EQ1 implies EQ2. Use counterexample magmas if helpful."

Llama follows instructions literally. Gpt-oss reasons about instructions and gets tangled in contradictions. The more specific you make the procedure, the better for llama and the worse for gpt-oss.

### Tension 2: Worked examples

- **llama wants**: 2-3 worked examples showing the full reasoning and output format
- **gpt-oss wants**: None — examples consume reasoning tokens and the model already knows the task

Each worked example is ~200-400 tokens of input. For gpt-oss, those tokens get "read" during analysis phase and contribute to its reasoning budget. For llama, the examples are pattern-matching templates it copies.

### Tension 3: Output format verbosity

- **llama wants**: Structured output with clear fields (`VERDICT:`, `REASONING:`, `PROOF:`, `\boxed{}`)
- **gpt-oss wants**: Just `\boxed{}` — any additional field is planning overhead in the analysis channel
- **gemma wants**: Probably moderate — structure helps anchor output but verbosity hurts throughput

### Tension 4: Scratchpad space

- **llama needs it**: Without visible reasoning, llama makes arithmetic errors on magma evaluations
- **gpt-oss doesn't**: It does all reasoning in the hidden analysis channel; visible scratchpad is wasted output tokens
- **gemma**: Probably does moderate reasoning internally but may still benefit from some visible scratchpad

### Tension 5: Escape hatches

- **gpt-oss wants**: Explicit permission to give up ("if unsure, output FALSE") — prevents reasoning loops
- **llama**: Doesn't need this — it doesn't have reasoning loops to fall into
- **gemma**: Probably benefits from it, similar to gpt-oss

---

## Your Most Powerful Tool: The Judge's Extraction Rules

From the official judge README, the verdict extraction rules are:

1. Case-insensitive
2. **Boxed answers beat labeled answers**
3. Labeled answers beat bare first/last-line answers
4. **Within the same marker type, the LAST occurrence wins**
5. Instruction patterns (like "VERDICT: TRUE or FALSE") are ignored

These rules give you a way to resolve the fundamental tensions. You can structure the prompt so that:

**Llama and gemma use the visible output as scratchpad**, emitting intermediate reasoning and potentially intermediate `\boxed{}` answers as they work through the problem.

**gpt-oss can skip straight to a final `\boxed{}`** because the prompt doesn't force it to write intermediate content.

**Both paths converge on a final `\boxed{}`** at the end, and the "last boxed wins" rule picks the right answer regardless of what came before.

### Worked illustration

Imagine the prompt tells the model: "You may optionally show your work. Your final answer must be a `\boxed{TRUE}` or `\boxed{FALSE}` at the end of your response."

**Llama's natural output**:
```
Let me test some magmas.
Magma R (x*y=y): EQ1 holds, EQ2 holds. \boxed{TRUE} so far.
Magma L (x*y=x): EQ1 holds, EQ2 fails. So actually \boxed{FALSE}.
Counterexample found.
\boxed{FALSE}
```

**gpt-oss's natural output** (after internal reasoning):
```
\boxed{FALSE}
```

Both get the right answer. Llama uses the scratchpad; gpt-oss uses its analysis channel. The judge sees the last `\boxed{}` in each case.

**Critical point**: the "last wins" rule is the only reason this trick works. Without it, llama's intermediate `\boxed{TRUE}` would cause problems. With it, you can let llama iterate freely and gpt-oss jump directly to the answer.

---

## Strategies for Finding Balance

### Strategy 1: The "Optional Scratchpad" unified prompt

Build one prompt that:
- States the task concisely at the top
- Gives the core method (test 3-4 magmas) without excessive procedural detail
- Explicitly marks reasoning as OPTIONAL
- Anchors the output format at both the top and bottom
- Has an escape hatch for ambiguous cases

This plays to all three models:
- gpt-oss can skip reasoning and go straight to the answer
- llama fills the scratchpad naturally and commits at the end
- gemma uses moderate reasoning and emits the verdict

Sketch:
```
Task: determine if EQ1 implies EQ2 over all magmas. 
Final answer must be \boxed{TRUE} or \boxed{FALSE} at the end.

Method: test these 3 magmas. If any satisfies EQ1 but fails EQ2, 
the answer is FALSE. Otherwise TRUE.

R (right projection): x*y = y. Expression → rightmost leaf.
L (left projection): x*y = x. Expression → leftmost leaf.  
Z (zero): x*y = 0 on {0}. All expressions → 0.

You may show your work if helpful. If you cannot determine after 
testing all 3, output \boxed{FALSE}.

EQ1: {{equation1}}
EQ2: {{equation2}}

Final answer: \boxed{TRUE} or \boxed{FALSE}
```

This is ~300 tokens, no contradictions, binary output, escape hatch, reinforced format.

### Strategy 2: Measure fragility to find the bottleneck

Run this prompt on the 20-problem smoke test across all three models. The one with the lowest accuracy is your bottleneck. Then:

- If **gpt-oss** is bottleneck → strip more content, add more escape hatches, check for contradictions
- If **llama** is bottleneck → add worked examples, more explicit procedures, structured format
- If **gemma** is bottleneck → this is harder since it's new; try both directions and see which helps

### Strategy 3: Asymmetric improvements

Because the three models have different failure modes, a change that improves one might not affect the others. Track accuracy per model separately and look for changes that:
- Fix one model's failures without degrading the others
- Have asymmetric impact (e.g., a worked example that helps llama by 10% and costs gpt-oss 2%)

### Strategy 4: Know when to give up on balance

If you find that gpt-oss is fundamentally incompatible with the prompt style llama needs — for instance, if llama requires detailed procedures that blow gpt-oss's reasoning budget — you may need to accept lower performance on one model. The question becomes: which is cheaper to sacrifice?

- If gpt-oss struggles because of format issues (empty responses), fix that first — format failures are worse than accuracy failures
- If llama struggles because of missing scratchpad, add more scratchpad — llama's ceiling is lower so it needs more help
- Gemma is the wildcard; treat it as a tiebreaker until you understand its quirks

### Strategy 5: Different output "lanes" for different models

Since you can't send different prompts, consider designing your prompt so different models naturally use different parts of it:

- **Fast lane**: Just the task + magma list + output format. Gpt-oss will take this path.
- **Scratchpad lane**: "You may show your work" invitation. Llama will use this.
- **Verification lane**: "If you are unsure after X steps" escape hatch. All models benefit.

The prompt serves all three but each model picks up what it needs. This is more structured than Strategy 1 but uses the same underlying principles.

---

## Testing Strategy

### Setup

For each iteration of your cheat sheet, run smoke tests on all three eval models separately. Log for each response:
- `correct` (verdict matches ground truth)
- `finish_reason` (stop/length/etc)
- `completion_tokens`
- `reasoning_tokens` where available (gpt-oss, gemma)
- Full response text for failure analysis

### Metrics per model

Track per-model:
- Accuracy on TRUE problems
- Accuracy on FALSE problems  
- Format compliance rate (was verdict parseable?)
- Truncation rate (finish_reason = length)
- Empty response rate (completion with no visible content)

### Decision rule

The cheat sheet is only as good as its worst model performance. Your iteration target should be:
1. **Minimum**: no model has >5% format failures
2. **Acceptable**: no model has >15% accuracy gap from the best model
3. **Goal**: all three models within a few percentage points of each other

### Red flags to watch for

- **gpt-oss empty responses** → budget exhaustion, cheat sheet is triggering too much reasoning
- **llama adds extra text after the verdict** → output format not anchored strongly enough
- **gemma responses are unusually long** → need explicit length constraint
- **Any model has huge TRUE-vs-FALSE asymmetry** → your heuristics are biased
- **All three disagree frequently** → the cheat sheet is teaching different methods to different models

---

## The Meta-Recommendation

Stop optimizing for "the best possible cheat sheet" and start optimizing for "the cheat sheet that doesn't catastrophically fail on any model." With equal weighting across three models, your score is roughly the average of three scores, but the models that perform worst drag the average down the most.

A cheat sheet that gets 90/80/60 across the three models scores 76.7 average. A cheat sheet that gets 75/75/75 scores 75. The second one is worse on average but probably more predictable and has less variance.

**For the final submission**, predictability matters. For iteration, you can afford to experiment. But your final submission should be the version that has been validated across all three models and doesn't have any known failure modes on any of them.

The competition doesn't reward the prompt that makes gpt-oss brilliant. It rewards the prompt that makes all three models perform adequately. Design for the weakest, not the strongest.

## Sources

- OpenAI gpt-oss Model Card: arXiv:2508.10925
- OpenAI Harmony Format: https://cookbook.openai.com/articles/openai-harmony
- Together AI gpt-oss Prompting: https://docs.together.ai/docs/gpt-oss
- Meta Llama 3.3 Model Card: https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct
- Llama Prompt Engineering: https://www.llama.com/docs/how-to-guides/prompting/
- Google Gemma 4 Announcement: https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/
- Gemma 4 31B Artificial Analysis: https://artificialanalysis.ai/models/gemma-4-31b
- SAIR Official Judge: https://github.com/SAIRcompetition/equational-theories-stage1-judge
