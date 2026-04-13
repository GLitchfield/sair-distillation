# Prompting Strategy for Small LLMs in the Distillation Challenge

## The Real Problem

The bottleneck in this competition is not mathematical — it's compliance. Small models (~70B parameters) like Llama 3.3 70B, Gemini Flash Lite, and Grok Fast don't reliably follow multi-step procedural instructions. A cheat sheet with perfect mathematical content but poor prompting design will underperform one with simpler math but better formatting.

This document covers what actually works for getting small LLMs to execute instructions consistently, with specific examples for the magma implication task.

---

## 1. Worked Examples Beat Abstract Rules

### The Research

Honda et al. (EMNLP 2025, "Distilling Many-Shot In-Context Learning into a Cheat Sheet") found that distilling many-shot examples into a concise textual summary outperformed both zero-shot instructions and retrieval-based ICL, while using far fewer tokens. The key finding: the cheat sheet works best when it combines compressed rules WITH representative examples.

Chain-of-thought research consistently shows that small models learn reasoning patterns primarily by mimicking demonstrated reasoning, not by following abstract instructions. Models under ~100B parameters often produce "illogical chains of thought" when given only instructions without examples (Wei et al., 2022).

### What This Means for Us

Don't write:
```
Step 3: Evaluate both equations in the constant-zero magma (x◇y = 0 for all x, y).
If both sides of the equation contain at least one ◇ operation, the equation is satisfied.
If one side is a bare variable and the other contains ◇, the equation is NOT satisfied.
```

Instead, write:
```
EXAMPLE — Testing the Zero Magma (every product = 0):

Problem: Does x ◇ (y ◇ z) = y ◇ x imply x = y ◇ (x ◇ x)?

Test E1 in Zero Magma: LHS = x ◇ (y ◇ z) = x ◇ 0 = 0. RHS = y ◇ x = 0. Both sides = 0. ✓ E1 holds.
Test E2 in Zero Magma: LHS = x. RHS = y ◇ (x ◇ x) = y ◇ 0 = 0. LHS = x ≠ 0 when x ≠ 0. ✗ E2 fails.

The Zero Magma satisfies E1 but not E2 → E1 does NOT imply E2.
VERDICT: FALSE
COUNTEREXAMPLE: {0,1} with x◇y = 0 for all x,y. E1 holds (both sides always 0). E2 fails: set x=1, then LHS=1 but RHS=0.
```

The second version costs more bytes but the LLM will actually do the right thing.

### Budget Allocation

For a 10KB cheat sheet, aim for roughly:
- 2-3 KB: Worked examples (2-3 complete problem solutions showing the full reasoning chain)
- 2-3 KB: Decision procedure (the steps to follow, kept linear)
- 2-3 KB: Reference tables (magma evaluation shortcuts, common patterns)
- 1-2 KB: Output format instructions and edge case rules

---

## 2. Linear Procedures Over Decision Trees

### The Problem with Branching

Every "if/then/else" is a point where the model can take the wrong branch, skip a branch, or hallucinate a condition. Small models are particularly bad at nested conditionals.

### Bad: Decision Tree
```
First, check if E1 forces a singleton magma:
  - If yes, E1 implies everything → TRUE
  - If no, check if E2's LHS is simpler than E1's LHS:
    - If yes, lean toward FALSE
    - If no, check if both equations have matching variable counts:
      - If yes, try algebraic rewriting...
      - If no, ...
```

### Good: Linear Checklist
```
Follow ALL steps in order. Stop as soon as you reach a VERDICT.

STEP 1 — Singleton Check
Look at E1. Does one side have a bare variable that doesn't appear on the other side?
Example: "x = y ◇ z" has x alone on the left but x doesn't appear in y ◇ z.
If YES → E1 forces singleton → VERDICT: TRUE (E1 implies everything).
If no → continue to Step 2.

STEP 2 — Zero Magma Test
In the zero magma, every ◇ expression equals 0. Bare variables keep their value.
• E1 holds if: both sides have ◇ (both become 0), OR both are the same bare variable.
• E2 holds if: same rule.
• If E1 holds but E2 does NOT hold → VERDICT: FALSE.
  COUNTEREXAMPLE: {0,1}, x◇y = 0 for all x,y.
If both hold or E1 doesn't hold → continue to Step 3.

STEP 3 — Right Projection Test
...

STEP 4 — Left Projection Test
...

STEP 5 — XOR Test
...

STEP 6 — If you reach here, all magma tests passed. Attempt to derive E2 from E1.
...

STEP 7 — Default judgment based on structural comparison.
...
```

Each step is self-contained. The model does one thing, checks one condition, and either stops or moves on. No nesting.

---

## 3. Show the Output Format Immediately

### The Principle

Small models are autocomplete engines. They will pattern-match the structure of what they've seen. If the first thing in your cheat sheet is a complete worked example in the exact output format, the model will slot into that format naturally.

### Recommended: Start With a Complete Example

```
You are classifying whether Equation 1 implies Equation 2 over all magmas.
Here is a complete worked example:

---
Equation 1: x ◇ y = y ◇ x
Equation 2: x ◇ (y ◇ z) = (x ◇ y) ◇ z

STEP 1 — Singleton check: E1 LHS = x◇y (not bare variable). Skip.
STEP 2 — Zero magma: E1: 0 = 0 ✓. E2: 0 = 0 ✓. Both hold. Continue.
STEP 3 — Right projection (x◇y = y): E1: y = x. Only true if x=y. E1 fails in general. Skip.
STEP 4 — Left projection (x◇y = x): E1: x = y. Only true if x=y. E1 fails in general. Skip.
STEP 5 — XOR (x◇y = x+y mod 2): 
  E1: x+y mod 2 = y+x mod 2. ✓ (addition is commutative).
  E2: x+(y+z) mod 2 = (x+y)+z mod 2. ✓ (addition is associative).
  Both hold. Continue.
STEP 6 — Derivation attempt: Commutativity does NOT imply associativity. 
  There exist commutative non-associative magmas.
STEP 7 — Default: E1 and E2 have different structural character. Lean FALSE.

VERDICT: FALSE
REASONING: Commutativity (E1) does not force associativity (E2). The five test magmas all happen to satisfy both, but non-associative commutative magmas exist.
PROOF:
COUNTEREXAMPLE: Consider {0,1,2} with x◇y = y◇x = (x+y) mod 3 if x≠y, and x◇x = x. This is commutative but not associative.
---

Now solve the actual problem using the same steps:
```

### Why This Works

The model sees the exact format (VERDICT/REASONING/PROOF/COUNTEREXAMPLE) in action before it needs to produce it. It sees the step-by-step pattern. It sees what "skip" looks like vs. what "VERDICT: FALSE" looks like. This is dramatically more effective than putting the output format instructions at the end.

---

## 4. Magma Evaluation — Make It Mechanical

### The Key Insight

The most reliable thing a small LLM can do is simple arithmetic and pattern matching. Frame each magma test as a mechanical procedure with no mathematical judgment required.

### Constant-Zero Magma (x ◇ y = 0 always)

```
ZERO MAGMA RULE: Replace every expression containing ◇ with 0. Leave bare variables alone.

Examples:
  x ◇ y → 0
  x ◇ (y ◇ z) → 0 (it contains ◇)
  (x ◇ y) ◇ z → 0
  x → x (bare variable, no ◇)
  y → y

An equation HOLDS in the zero magma if:
  • Both sides contain ◇ (both become 0, so 0 = 0 ✓)
  • Both sides are the SAME bare variable (e.g., x = x ✓)
An equation FAILS if:
  • One side is a bare variable and the other contains ◇ (e.g., x = 0 ✗ for x=1)
  • The two sides are different bare variables (e.g., x = y ✗)
```

### Right Projection (x ◇ y = y)

```
RIGHT PROJECTION RULE: Every ◇ expression evaluates to its RIGHTMOST LEAF variable.
Walk to the rightmost variable in the expression tree.

Examples:
  x ◇ y → y
  x ◇ (y ◇ z) → z (rightmost leaf)
  (x ◇ y) ◇ z → z
  (x ◇ y) ◇ (z ◇ w) → w
  x ◇ (y ◇ (z ◇ w)) → w
  x → x (bare variable)

An equation HOLDS if both sides have the same rightmost leaf variable.
```

### Left Projection (x ◇ y = x)

```
LEFT PROJECTION RULE: Every ◇ expression evaluates to its LEFTMOST LEAF variable.

Examples:
  x ◇ y → x
  x ◇ (y ◇ z) → x
  (x ◇ y) ◇ z → x (leftmost leaf of leftmost subtree)
  ((x ◇ y) ◇ z) ◇ w → x
  y → y (bare variable)

An equation HOLDS if both sides have the same leftmost leaf variable.
```

### XOR Magma ({0,1} with x ◇ y = x + y mod 2)

```
XOR RULE: Count how many times each variable appears on each side.
If every variable appears an EVEN number of times, the side evaluates to 0.
If every variable appears an ODD number of times, the side evaluates to that variable.
More precisely: the side evaluates to the XOR of all variable occurrences.

SHORTCUT: An equation holds in the XOR magma if and only if, for EVERY variable,
the number of times it appears on the LHS and the number of times it appears on the 
RHS have the SAME PARITY (both even or both odd).

Examples:
  x ◇ (y ◇ x) = y  → LHS: x appears 2×, y appears 1×. RHS: y appears 1×.
  Parity check: x: 2 vs 0 (both even ✓), y: 1 vs 1 (both odd ✓). HOLDS.

  x ◇ y = y ◇ (x ◇ x)  → LHS: x 1×, y 1×. RHS: x 2×, y 1×.
  Parity: x: 1 vs 2 (odd vs even ✗). FAILS.
```

---

## 5. Structural Signals to Encode

These are cheap checks that the LLM can do before attempting any magma evaluation.

### Singleton Detection (yields TRUE immediately)

```
SINGLETON RULE: If E1's LHS is a bare variable x, and x does NOT appear anywhere 
in E1's RHS, then E1 forces the magma to have only one element.
A singleton magma satisfies EVERY equation → VERDICT: TRUE.

Similarly if E1's RHS is a bare variable x not appearing in the LHS.

Example: E1 is "x = y ◇ z". The variable x appears on the left but not in y ◇ z.
This means for ANY y, z, the result y ◇ z must equal x — but x is arbitrary.
So y ◇ z must equal everything simultaneously → only possible with one element.
```

### LHS Complexity Check (yields FALSE signal)

```
COMPLEXITY RULE: If E2's LHS has FEWER ◇ operations than E1's LHS, lean strongly 
toward FALSE. In our test data, this pattern was FALSE 100% of the time (188/188 cases).

Count the ◇ symbols in just the left-hand side of each equation.
If count(E2_LHS) < count(E1_LHS) → strong FALSE signal.
```

---

## 6. The Default Heuristic

After all mechanical tests, the LLM needs a tiebreaker for cases where no test was conclusive. This should be simple and biased toward the base rate of the problem set.

```
DEFAULT RULE: If you have completed all magma tests and none found a counterexample,
and you were unable to find a derivation of E2 from E1, use this heuristic:

• If E1 and E2 have very similar structure (same shape, similar variable positions) → TRUE
• If E1 and E2 look structurally different → FALSE
• When in doubt → TRUE (because reaching this point means all magma tests passed,
  which is a positive signal)
```

Note: the optimal default depends on the true/false ratio. The normal set is 50/50, so the default bias matters less. The hard set is ~32% true, so a FALSE default would be better there. Test both.

---

## 7. Token Efficiency Tricks

### Use symbols, not words
- "✓" instead of "is satisfied"
- "✗" instead of "is not satisfied"  
- "→" instead of "therefore" or "this means"
- "LHS" / "RHS" instead of "left-hand side" / "right-hand side"

### Use tables for reference data
Tables are denser than prose and small models parse them well:
```
| Magma         | Rule              | Eq holds when                    |
|---------------|-------------------|----------------------------------|
| Zero (x◇y=0)  | ◇ expr → 0       | Both sides have ◇, or same var   |
| Right (x◇y=y) | expr → rightmost  | Same rightmost leaf both sides   |
| Left (x◇y=x)  | expr → leftmost   | Same leftmost leaf both sides    |
| XOR           | count vars mod 2  | Same parity each var both sides  |
```

### Front-load critical content
Place the most important instructions in the first 30% of the cheat sheet. LLM attention degrades over long contexts, especially for small models. Put worked examples and the linear procedure FIRST. Put reference tables and edge cases LAST.

---

## 8. Testing and Iteration Strategy

### Measure compliance, not just accuracy

When reviewing test results, categorize errors as:
1. **Wrong magma evaluation** — the model attempted the procedure but made an arithmetic mistake
2. **Skipped steps** — the model jumped to a verdict without doing the tests
3. **Format error** — the model didn't output VERDICT/REASONING/PROOF/COUNTEREXAMPLE correctly
4. **Wrong heuristic** — the model did all tests correctly but made the wrong default judgment

Each error type has a different fix:
- (1) → Better/simpler evaluation rules, more examples
- (2) → Reorder cheat sheet, make steps more prominent, add "you MUST do each step"
- (3) → Put output format example earlier, make it more prominent
- (4) → Adjust default bias, improve structural heuristics

### A/B test specific phrasings

Run the same 50 problems with two cheat sheet variants that differ in ONE thing. Examples of things to test:
- Worked example first vs. rules first
- "You MUST follow each step" vs. no such instruction
- 2 worked examples vs. 3 worked examples
- Table format vs. prose format for magma rules
- "Think step by step" vs. no such instruction (research is mixed on whether this helps small models)

### Track byte budget

Every iteration, check: `wc -c cheatsheet.txt`. You have 10,000 bytes. Use them wisely. A rough guide:
- Each worked example: ~500-800 bytes
- Each magma evaluation rule with examples: ~300-500 bytes
- The linear procedure skeleton: ~500-800 bytes
- Output format template: ~200-300 bytes

---

## 9. Complete Cheat Sheet Skeleton

Here's a structural template. Fill in with your best current content:

```
[WORKED EXAMPLE — FALSE case, ~600 bytes]
Show a complete problem solved correctly, ending with VERDICT: FALSE and a counterexample.

[WORKED EXAMPLE — TRUE case, ~500 bytes]  
Show a complete problem solved correctly, ending with VERDICT: TRUE and a proof sketch.

[PROCEDURE — ~800 bytes]
Step 1: Singleton check → TRUE
Step 2: Zero magma test → FALSE  
Step 3: Right projection test → FALSE
Step 4: Left projection test → FALSE
Step 5: XOR parity test → FALSE
Step 6: [Optional: Linear magma over F3] → FALSE
Step 7: Attempt algebraic derivation → TRUE
Step 8: Default heuristic → TRUE or FALSE

[MAGMA REFERENCE TABLE — ~600 bytes]
Compact rules for evaluating each test magma.

[STRUCTURAL SHORTCUTS — ~400 bytes]
LHS complexity rule, variable count criterion, etc.

[OUTPUT FORMAT REMINDER — ~200 bytes]
Reiterate the exact format expected.
```

Total: ~3100 bytes of structure + content to fill ≈ 6-8 KB working cheat sheet.

---

## 10. What NOT to Include

- **Long mathematical proofs or theory** — Haiku won't use them. It will skip over dense math and go straight to a guess.
- **Conditional logic deeper than one level** — "If X and Y but not Z, then..." will be misinterpreted.
- **Exhaustive lists of equation properties** — The model won't look things up in a table of 4694 entries. Only include patterns it can check mechanically.
- **Instructions to "be creative" or "think carefully"** — These are wasted bytes. Small models respond to structure, not encouragement.
- **Negative instructions** ("do NOT...") — Small models often fail to process negation. Phrase everything as what TO do, not what to avoid.

---

## References

- Honda, Murakami, Zhang. "Distilling Many-Shot In-Context Learning into a Cheat Sheet." EMNLP 2025 Findings. https://aclanthology.org/2025.findings-emnlp.930/
- Wei et al. "Chain of Thought Prompting Elicits Reasoning in Large Language Models." NeurIPS 2022. (CoT only helps models >100B; smaller models produce illogical chains)
- Competition playground for testing: https://playground.sair.foundation/playground/mathematics-distillation-challenge-equational-theories-stage1
- Prompt template (evaluation.jinja2): The output must have VERDICT, REASONING, PROOF, COUNTEREXAMPLE sections.
