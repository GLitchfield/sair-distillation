# v5 Cheatsheet Test Observations — hard3 Dataset

**Date:** 2026-03-26
**Test:** cheatsheet_v5.txt on the hard3 dataset (400 problems)
**Models tested:** Claude Haiku 4.5, Gemini Flash Lite
**Dataset:** 195 TRUE (48.8%), 205 FALSE (51.2%)

---

## 1. Summary Statistics

| Metric | Haiku v5 | Gemini v5 |
|--------|----------|-----------|
| Total problems | 400 | 400 |
| Correct | 185 (46.2%) | 212 (53.0%) |
| TP | 152 | 42 |
| FP | **172** | 35 |
| FN | 43 | **153** |
| TN | 33 | 170 |
| Precision | 0.469 | 0.546 |
| Recall | 0.779 | 0.215 |
| F1 | **0.586** | **0.309** |

**Per-class accuracy:**

| Class | Haiku | Gemini |
|-------|-------|--------|
| TRUE (195 problems) | 77.9% | 21.5% |
| FALSE (205 problems) | 16.1% | 82.9% |

**The models are mirror images of each other's failure modes.** Haiku massively over-predicts TRUE (recall=78%, but FALSE detection is only 16%). Gemini massively over-predicts FALSE (82.9% FALSE accuracy, but TRUE detection is only 21.5%).

**Error overlap:**
- Both wrong: **68** problems (32 where both said TRUE/answer FALSE, 36 where both said FALSE/answer TRUE)
- Haiku right, Gemini wrong: 120
- Gemini right, Haiku wrong: 147
- Both right: 65

---

## 2. The 68 Problems Both Models Got Wrong

### 2a. Both said TRUE, answer is FALSE (32 cases)

These are hard FALSE cases where both models failed to find a counterexample. All require 3-element (or larger) counterexamples not covered by the 7 standard magmas in v5.

```
hard3_0012: x = x*(y*(x*x))           => x*x = (x*y)*(x*x)
hard3_0016: x = y*(x*(x*x))           => x*y = (y*y)*(y*y)
hard3_0029: x = y*((z*y)*x)           => x*y = ((y*z)*z)*y
hard3_0037: x = (x*(x*y))*x           => x*x = x*((y*y)*x)
hard3_0056: x*x = (y*x)*z             => x*(x*y) = x*(z*z)
hard3_0059: x*x = (y*z)*w             => x*(x*y) = (z*x)*y
hard3_0062: x = x*(x*(y*(y*x)))       => x = x*((y*y)*(x*x))
hard3_0065: x = x*(y*(x*(x*z)))       => x*x = (x*x)*y
hard3_0070: x = y*(x*(z*(y*x)))       => x = y*((x*x)*x)
hard3_0075: x = y*(z*(x*(z*x)))       => x = ((x*x)*y)*(y*x)
hard3_0083: x = x*(x*((y*z)*y))       => x*y = (x*z)*(w*y)
hard3_0096: x = y*(z*((x*w)*x))       => x = (x*(x*x))*x
hard3_0102: x = y*(z*((w*w)*x))       => x = ((x*(y*x))*z)*x
hard3_0105: x = x*((x*y)*(z*z))       => x*y = x*(z*(x*z))
hard3_0112: x = y*((y*x)*(x*x))       => x = x*(((x*y)*y)*x)
hard3_0132: x = x*((y*(y*y))*z)       => x*y = x*(y*(y*z))
hard3_0141: x = y*((x*(y*y))*x)       => x*x = ((y*y)*y)*x
hard3_0172: x = (y*y)*(x*(z*x))       => x = y*(x*(z*(x*x)))
hard3_0178: x = (y*z)*(y*(y*x))       => x*(y*x) = (y*y)*x
hard3_0201: x = (x*(y*x))*(y*z)       => x = (((x*y)*z)*y)*x
hard3_0229: x = ((y*x)*x)*(z*x)       => x = (y*(x*x))*(z*x)
hard3_0242: x = ((y*z)*x)*(x*w)       => x = ((x*x)*y)*(y*y)
hard3_0248: x = (x*(y*(x*y)))*y       => (x*x)*x = (x*x)*y
hard3_0254: x = (y*(z*(x*x)))*x       => x*x = (y*z)*(x*x)
hard3_0300: x = ((x*(x*x))*x)*y       => x = x*((y*(z*z))*x)
hard3_0304: x = ((x*(x*y))*z)*y       => x = (x*y)*((x*y)*x)
hard3_0322: x = ((y*(z*y))*z)*x       => x*x = (x*(y*y))*x
hard3_0356: x*y = z*(x*(x*y))         => x*y = ((y*y)*z)*y
hard3_0368: x*x = (x*y)*(y*z)         => x*y = x*(z*(z*x))
hard3_0370: x*x = (y*x)*(z*w)         => x*y = z*((x*z)*w)
hard3_0371: x*x = (y*z)*(z*w)         => x*(y*z) = y*(x*z)
hard3_0394: x*(y*z) = (y*y)*x         => x*y = z*(w*(y*u))
```

**Pattern:** Many of these have EQ1 that forces very restricted structure (often only right-projection and/or constant magmas satisfy it among the 7 standard ones). Both models then conclude TRUE by default. The actual counterexamples are 3-element magmas with careful construction. For example, `hard3_0029` (answer FALSE) has the 3-element magma `op=[[0,1,2],[0,1,2],[1,0,2]]` as counterexample (verified computationally); `hard3_0012` (answer FALSE) has `op=[[0,0,0],[1,1,0],[2,0,2]]`.

### 2b. Both said FALSE, answer is TRUE (36 cases)

These are hard TRUE cases where both models incorrectly found or fabricated a counterexample, or defaulted to FALSE via flawed heuristics.

```
hard3_0003: x = y*(x*x)               => x = y*(z*(z*(w*x)))
hard3_0014: x = x*(y*(z*y))           => x = (((x*y)*z)*x)*y
hard3_0024: x = x*((y*z)*z)           => x = (x*(y*(z*y)))*x
hard3_0028: x = y*((z*x)*x)           => x = ((y*z)*w)*(z*x)
hard3_0030: x = (x*x)*(y*z)           => x*y = x*((x*x)*y)
hard3_0049: x = ((y*z)*w)*x           => x = y*(z*(x*(w*x)))
hard3_0068: x = x*(y*(z*(z*z)))       => x = x*((y*(y*z))*x)
hard3_0124: x = y*((z*w)*(u*x))       => x = (y*z)*(y*(z*x))
hard3_0144: x = y*((y*(y*z))*x)       => x = (y*(z*w))*(y*x)
hard3_0145: x = y*((z*(z*x))*y)       => x = y*(((x*y)*y)*y)
hard3_0176: x = (y*z)*(y*(x*z))       => x = (y*((y*y)*x))*y
hard3_0183: x = (x*x)*((y*z)*z)       => x = (x*x)*(y*(x*y))
hard3_0204: x = (y*(x*x))*(z*x)       => x = y*(((x*z)*z)*x)
hard3_0209: x = (y*(z*x))*(z*x)       => x = ((y*z)*z)*(w*x)
hard3_0231: x = ((y*x)*y)*(z*z)       => x = (y*(x*(y*x)))*x
hard3_0249: x = (x*(y*(x*z)))*w       => x = (x*(y*x))*(y*y)
hard3_0256: x = (y*(z*(z*w)))*x       => x = (x*((y*x)*x))*x
hard3_0257: x = (y*(z*(w*w)))*x       => x = ((y*y)*(y*y))*x
hard3_0259: x = (x*((y*x)*z))*z       => x = (x*(y*(z*x)))*x
hard3_0262: x = (x*((y*z)*w))*u       => x*y = ((x*z)*w)*x
hard3_0265: x = (y*((x*z)*y))*z       => x*(x*y) = (y*x)*x
hard3_0271: x = (y*((z*x)*z))*x       => x = ((y*z)*w)*(w*x)
hard3_0283: x = ((x*y)*(y*z))*w       => x = ((x*x)*x)*(y*z)
hard3_0295: x = ((y*z)*(z*w))*x       => x = (y*(y*z))*(w*x)
hard3_0297: x = ((y*z)*(w*z))*x       => x = ((x*y)*y)*(x*x)
hard3_0313: x = ((y*(x*x))*z)*x       => x*(y*z) = (w*y)*z
hard3_0314: x = ((y*(x*z))*y)*x       => x = (y*z)*(w*(u*x))
hard3_0317: x = ((y*(x*z))*z)*x       => (x*x)*y = (y*z)*y
hard3_0318: x = ((y*(x*z))*w)*x       => x = (x*((y*z)*z))*x
hard3_0323: x = ((y*(z*w))*z)*x       => x = x*(x*(y*(y*x)))
hard3_0324: x = ((y*(z*w))*z)*x       => x = x*(((x*y)*x)*x)
hard3_0325: x = ((y*(z*w))*z)*x       => x*y = (y*y)*(y*y)
hard3_0326: x = ((y*(z*w))*w)*x       => x = (((x*y)*x)*x)*x
hard3_0329: x = (((x*y)*x)*z)*w       => x*(x*y) = x*(z*z)
hard3_0365: x*y = x*((z*z)*x)         => x*y = x*(y*y)
hard3_0381: x*y = (x*(z*y))*w         => x*y = (x*(z*x))*z
```

**Pattern:** Many EQ1 forms here have the structure `x = (...)*x` or `x = (...)*(something containing x)` which tends to force strong structural constraints. When EQ2 introduces new variables not in EQ1, models default to FALSE. The correct answer is TRUE because EQ1 is strong enough that any model satisfying it also satisfies the complex EQ2 — but this requires proof by substitution, not counterexample testing.

---

## 3. Haiku FP Analysis: 172 Cases (Defaulting to TRUE)

**Root cause:** Haiku's Step 5 default judgment says TRUE when no counterexample is found. Since the hard3 dataset is specifically designed to resist simple 2-element counterexamples, Haiku rarely finds a counterexample for FALSE cases, and defaults to TRUE.

### 3a. The Default-to-TRUE Pattern

In 152 of the 172 FP cases, the model reasoned: "The only non-singleton magma satisfying EQ1 is Left Projection (or Right Projection), which also satisfies EQ2. No counterexample found. Therefore TRUE."

**Representative example (hard3_0010):**
```
EQ1: x = x*(x*(y*x))
EQ2: x*x = (x*(y*x))*x
Answer: FALSE

Haiku STEP 5 reasoning:
"The only magmas that satisfy EQ1 universally are those that reduce to singletons
(Magmas A, E) or those where the equation is trivially true by structure (Magmas B, C).
In all cases where EQ1 is satisfied, EQ2 is also satisfied. No counterexample found.
VERDICT: TRUE"
```

The actual counterexample (not found by Haiku) is a 3-element magma. This is the fundamental limit of the v5 approach: the hard3 dataset was curated to defeat the 7 standard magma tests.

### 3b. Why the Hard3 FALSE Cases Resist Standard Magmas

Verified computationally: problems like `hard3_0012`, `hard3_0029`, `hard3_0056` have **no 2-element counterexample**. Their first counterexample requires 3 or more elements with carefully constructed operation tables. The v5 cheatsheet only provides 7 specific magmas (all 2-element or linear), which is insufficient for hard3.

**Example:** `hard3_0029` (EQ1: `x = y*((z*y)*x)`, EQ2: `x*y = ((y*z)*z)*y`, answer FALSE):
- No counterexample found among all 16 possible 2-element magmas (verified)
- 3-element counterexample: `op = [[0,1,2],[0,1,2],[1,0,2]]`, fails EQ2 at x=0, y=0, z=2

### 3c. Haiku's FALSE Detection is Nearly Broken

Of 205 FALSE cases, Haiku identified only 33 (16.1%). The v5 cheatsheet's magma battery is insufficient for the hard3 distribution.

---

## 4. Haiku FN Analysis: 43 Cases (Spurious Counterexamples)

Haiku produced FALSE verdicts on TRUE cases by fabricating invalid counterexamples. The 43 FN cases break down by the type of spurious counterexample claimed:

| Claimed counterexample | Count |
|------------------------|-------|
| Left Projection (x*y=x) claimed as CE | 22 |
| XOR (x*y=x+y mod 2) claimed as CE | 6 |
| Linear/mod-3 magma claimed as CE | 4 |
| Right Projection claimed as CE | 3 |
| Other fabricated magmas | 8 |

### 4a. The Dominant Pattern: Left Projection as Spurious Counterexample

In 22 cases, Haiku claimed Left Projection satisfies EQ1 but violates EQ2. **These claims are all false** — either Left Projection fails EQ1 universally (making it irrelevant), or it satisfies both EQ1 and EQ2.

**Example (hard3_0068):**
```
EQ1: x = x*(y*(z*(z*z)))
EQ2: x = x*((y*(y*z))*x)
Answer: TRUE

Haiku's claimed counterexample:
"COUNTEREXAMPLE: Magma C (Left Projection): x*y = x. Assignment x=1, y=2, z=anything.
EQ1 evaluates to 1=1 (true). EQ2 evaluates to 1=2 (false)."

ERROR: In Left Projection, x*y=x always, so EQ2: x = x*((y*(y*z))*x) = x (the left arg).
EQ2: x = x, which is TRUE, not false. The model made an arithmetic error.
```

### 4b. The XOR Parity Check Bug

In 6 cases, Haiku claimed XOR as counterexample through a systematic bug in the XOR parity check. The model was adding up ALL variables in the RHS together and comparing total parity, rather than checking each variable independently.

**Example (hard3_0005):**
```
EQ1: x = (y*z)*x
EQ2: x*y = y*((y*x)*y)
Answer: TRUE

Haiku's XOR check:
"EQ1: x = (y*z)*x. Parity: LHS has x once (odd). RHS has y once, z once, x once (odd total).
Parities match ✓"

THE BUG: The parity check should be per-variable:
  - x: LHS=1, RHS=1 (balanced — OK)
  - y: LHS=0, RHS=1 (UNBALANCED — XOR fails EQ1!)
  - z: LHS=0, RHS=1 (UNBALANCED — XOR fails EQ1!)

Verification: XOR fails EQ1 at x=0, y=0, z=1: LHS=0, RHS=(0 XOR 1) XOR 0 = 1. FAIL.
```

The model incorrectly reported XOR satisfies EQ1 (which it does NOT), then used XOR as a counterexample for EQ2 (which XOR also fails, making it useless even if EQ1 were satisfied).

**Correct XOR rule (from v5 cheatsheet):** "equation holds iff every variable has the same parity of occurrences on both sides." This requires checking each variable's count individually, not the total. The model is not applying this rule correctly.

---

## 5. Gemini FN Analysis: 153 Cases (Defaulting to FALSE with Flawed Heuristics)

**Root cause:** Gemini over-applies the FALSE-leaning heuristics in Step 5, especially (a) the "EQ2 introduces new variables" heuristic and (b) treating a failed proof attempt as evidence of FALSE.

### 5a. The Core Failure Mode: No Counterexample Verification Required

Gemini produces a non-empty COUNTEREXAMPLE field in **all 153 FN cases** — but these are all invalid. The model:
1. Tests standard magmas, finds none satisfying EQ1 (or only trivial ones)
2. Steps through Step 4 proof attempt, fails to construct a proof
3. In Step 5, applies FALSE-leaning heuristics (new variables, complexity)
4. **Invents a plausible-sounding but unverified counterexample**

This is a hallucination pattern: the model knows it "should" provide a counterexample if saying FALSE, so it constructs one that sounds convincing but is not actually valid.

### 5b. The "New Variables in EQ2" Heuristic Misapplied

In 21 of the 153 FN cases, Gemini explicitly cites the Step 5 heuristic "EQ2 introduces new variables not in EQ1 → lean FALSE."

**Example (hard3_0003):**
```
EQ1: x = y*(x*x)
EQ2: x = y*(z*(z*(w*x)))
Answer: TRUE

Gemini STEP 5:
"EQ2 introduces new variables (z, w) not present in EQ1. In equational logic, an implication
that introduces new variables is generally not valid unless the antecedent forces the
variables to be irrelevant... VERDICT: FALSE"

WHY THIS IS WRONG: EQ1 is x = y*(x*x). In Right Projection (x*y=y):
  - EQ1: x = y*(x*x) = x (rightmost of whole expression) ✓
  - EQ2: x = y*(z*(z*(w*x))) = x (rightmost variable) ✓
So EQ1 implies EQ2 because EQ1 is strong enough to force the structure where EQ2 holds.
The "new variable" heuristic is unreliable for strong EQ1 laws.
```

### 5c. The Dominant Failure Pattern: XOR Fails EQ1 → Default FALSE

In 135 of 153 FN cases, Gemini correctly notes that XOR fails EQ1 (meaning XOR can't be a counterexample), then incorrectly concludes FALSE anyway by applying other Step 5 heuristics. The pattern is:

1. XOR fails EQ1 → no counterexample from XOR
2. Other standard magmas fail EQ1 too, or satisfy both EQ1 and EQ2
3. Step 4 proof attempt fails (or has errors)
4. Step 5: "EQ1 is very restrictive, only admits trivial models" → lean FALSE due to complexity/new-vars heuristic

**The correct interpretation of "EQ1 only admits trivial models"** is that the implication is **likely TRUE** (the only models satisfying EQ1 are trivial ones like singletons or projections, which satisfy everything). But Gemini systematically interprets this as evidence for FALSE.

### 5d. Representative Bad Reasoning in Step 4

Gemini frequently makes algebraic errors in Step 4 that then lead to wrong defaults.

**Example (hard3_0001):**
```
EQ1: x = y*x (means: for all x,y, the second operand equals the result)
EQ2: x = x*(x*((y*z)*x))
Answer: TRUE

Gemini Step 4:
"In EQ2: x = x*(x*((y*z)*x)). Let A = (y*z)*x.
By EQ1, x*A = x (since x is the right operand)."

THE ERROR: EQ1 says y*x = x — the SECOND argument x gives result x.
x*A has A as the SECOND argument, so x*A = A by EQ1, NOT x.
The model swapped first and second argument positions.

CORRECT derivation:
  (y*z)*x = x  [by EQ1: any_thing * x = x]
  x*x = x      [by EQ1 with y=x: x*x = x]
  x*(x*((y*z)*x)) = x*(x*x) = x*x = x   ✓
```

---

## 6. Gemini FP Analysis: 35 Cases (Incorrect TRUE)

Gemini said TRUE for 35 problems where the answer is FALSE. These are cases where standard magmas either satisfy EQ1 vacuously (all fail EQ1, so no real test) or where Gemini incorrectly inferred that a specific structure (typically the constant magma or singleton) is the ONLY model of EQ1.

### 6a. The "EQ1 Forces Constant Magma" Over-Generalization

In about 20 of 35 Gemini FP cases, Gemini concludes that EQ1 forces the magma to be a constant (x*y = c for all x,y), and since constant magmas satisfy EQ2, concludes TRUE.

**Example (hard3_0056):**
```
EQ1: x*x = (y*x)*z
EQ2: x*(x*y) = x*(z*z)
Answer: FALSE

Gemini:
"Equation 1 forces the magma to be a constant magma (x*y = c)... In a constant magma,
EQ2 becomes c = c, which is always true. VERDICT: TRUE"

WHY WRONG: EQ1 does NOT force constant magma. 3-element counterexample exists:
op=[[0,0,0],[0,0,0],[0,1,0]]
  EQ1 holds (x*x = (y*x)*z always gives 0=0 for most elements)
  EQ2 fails at x=2, y=1, z=0: LHS=op(2,op(2,1))=op(2,1)=1, RHS=op(2,op(0,0))=op(2,0)=0
```

### 6b. Both Models Over-Lean on "Only Trivial Models Satisfy EQ1 → TRUE"

This is the shared failure in the 32 "both TRUE/answer FALSE" cases: when the 7 standard magmas all fail EQ1 (or only constant/singleton ones satisfy it), both models conclude the implication must be TRUE. But the actual counterexample requires a non-trivial 3+ element magma.

---

## 7. Specific Response Examples Showing Key Reasoning Failures

### Failure Type A: Left Projection arithmetic error (Haiku FN)

From `hard3_0068` (EQ1: `x=x*(y*(z*(z*z)))`, EQ2: `x=x*((y*(y*z))*x)`, answer TRUE):
```
COUNTEREXAMPLE: Magma C (Left Projection, x*y=x). Assignment x=1, y=2.
EQ2 evaluates to 1=2 (false).
```
**Error:** In Left Projection, x*y=x, so EQ2 LHS = x*(...) = x. EQ2 is `x=x`, which is trivially true. The model computed the nested expression incorrectly.

### Failure Type B: XOR parity summed instead of per-variable (Haiku FN)

From `hard3_0005` (EQ1: `x=(y*z)*x`, EQ2: `x*y=y*((y*x)*y)`, answer TRUE):
```
EQ1 parity check: "LHS has x once (odd). RHS has y once, z once, x once (odd total). Parities match ✓"
COUNTEREXAMPLE FOUND: XOR satisfies EQ1 but violates EQ2.
```
**Error:** The check should be per-variable: y has 0 on LHS and 1 on RHS (parity mismatch → XOR fails EQ1). Verified: XOR fails EQ1 at x=0, y=0, z=1.

### Failure Type C: Argument position confusion in substitution proof (Gemini FN)

From `hard3_0001` (EQ1: `x=y*x`, EQ2: `x=x*(x*((y*z)*x))`, answer TRUE):
```
"By EQ1, x*A = x (since x is the right operand)."
```
**Error:** EQ1 says `y*x = x` — the right operand (second argument) equals the result. But `x*A` has A as the right operand, so `x*A = A` by EQ1, not x. The correct chain: `(y*z)*x = x` (by EQ1), then `x*x = x` (by EQ1), then `x*(x*((y*z)*x)) = x*(x*x) = x*x = x`.

### Failure Type D: "New variables → FALSE" heuristic applied to strong EQ1 (Gemini FN)

From `hard3_0003` (EQ1: `x=y*(x*x)`, EQ2: `x=y*(z*(z*(w*x)))`, answer TRUE):
```
"EQ2 introduces new variables (z, w) not present in EQ1... the introduction of z and w
allows for counterexamples where the values of z and w change the result. VERDICT: FALSE"
```
**Error:** When EQ1 forces Right Projection-like behavior (as here), new variables in EQ2 are irrelevant because they reduce to x regardless. The "new variables → FALSE" heuristic is only valid when EQ1 is weak.

### Failure Type E: "All standard magmas fail EQ1 → EQ1 forces trivial model → TRUE" default (Haiku FP)

From `hard3_0010` (EQ1: `x=x*(x*(y*x))`, EQ2: `x*x=(x*(y*x))*x`, answer FALSE):
```
"The only magmas that satisfy EQ1 universally are those that reduce to singletons or
those where the equation is trivially true by structure. In all cases where EQ1 is satisfied,
EQ2 is also satisfied. No counterexample found. VERDICT: TRUE"
```
**Error:** EQ1 restricts the magma but does not collapse it to only trivial models. A 3-element non-trivial magma satisfies EQ1 but violates EQ2, but this was not found by the 7-magma test.

### Failure Type F: Constant magma over-generalization (Gemini FP)

From `hard3_0056` (EQ1: `x*x=(y*x)*z`, EQ2: `x*(x*y)=x*(z*z)`, answer FALSE):
```
"Equation 1 forces the magma to be a constant magma because for any x,y,z,
x*x=(y*x)*z implies that the value of the product is independent of the inputs."
```
**Error:** This conclusion is wrong. Verified: 3-element magma `op=[[0,0,0],[0,0,0],[0,1,0]]` satisfies EQ1 (non-constant) but violates EQ2. EQ1 constrains the magma but not to constant.

---

## 8. Root Cause Analysis

### Why Haiku Fails on FALSE (172 FP)

1. **The 7 standard magmas are insufficient for hard3.** The hard3 dataset was curated to resist exactly the strategy v5 teaches. Most hard3 FALSE cases require 3+ element magmas as counterexamples.

2. **Step 5 default is biased toward TRUE.** When all magmas fail EQ1, the correct heuristic is uncertain (or even slightly TRUE-biased), but the v5 cheatsheet does not give adequate weight to "lean FALSE."

3. **Arithmetic errors in magma evaluation.** Especially with Magma F (negate-right) and Left Projection, models make computational mistakes when expressions are deeply nested.

### Why Gemini Fails on TRUE (153 FN)

1. **Step 5 heuristics are over-applied.** Gemini treats the "new variables → lean FALSE" and "more complex → lean FALSE" signals as near-decisive rather than as weak signals. These heuristics are unreliable for strong EQ1 laws.

2. **Step 4 proof attempts fail or have errors.** When the proof fails, Gemini defaults to FALSE rather than maintaining uncertainty.

3. **Algebraic substitution errors.** Models confuse argument positions, especially with non-commutative operations. The instruction to "use EQ1 as a rewrite rule" is insufficiently specific.

4. **"Trivial model = TRUE" vs "trivial model = ???" confusion.** When EQ1 only admits trivial models (singletons, projections), the correct answer is TRUE. But Gemini interprets this as "EQ1 is strange, probably not a real implication, default FALSE." This is backwards.

---

## 9. v6 Recommendations

### Fix 1: Correct the XOR parity rule (critical)

The v5 description is: "equation holds iff every variable has the same parity of occurrences on both sides." This is correct but models misapply it. Add an explicit worked example showing per-variable checking:

```
XOR PARITY CHECK (must verify each variable independently):
  x = (y*z)*x
  x: LHS=1, RHS=1 — same parity ✓
  y: LHS=0, RHS=1 — DIFFERENT parity → XOR fails this equation
  z: LHS=0, RHS=1 — DIFFERENT parity → XOR fails this equation
  RESULT: XOR does NOT satisfy EQ1 as a universal law
```

### Fix 2: Flip the "trivial models" signal

Replace the current Step 5 heuristic text. Currently: "All standard magmas (A-G) fail to satisfy EQ1 → EQ1 may only admit trivial models → lean TRUE"

This logic is wrong for Gemini: when only trivial models satisfy EQ1, it should clearly lean TRUE. The heuristic needs to be explicit:

**CRITICAL SIGNAL: If EQ1 is satisfied ONLY by singletons/constant magmas/left-projection, and EQ2 is also satisfied by all those same models → this is strong evidence for TRUE. Do not default FALSE.**

### Fix 3: Clarify what "new variables in EQ2" means

Add warning: "The 'new variables in EQ2 → lean FALSE' heuristic applies ONLY when EQ1 is a weak constraint (many magmas satisfy it). When EQ1 is highly restrictive (only trivial models satisfy it), new variables in EQ2 are meaningless because the model space is already collapsed. In that case, lean TRUE."

### Fix 4: Add worked example of substitution proof

The models fail to correctly apply EQ1 as a rewrite rule. Add a worked example:

```
SUBSTITUTION EXAMPLE:
EQ1: x = y*x  (means: the second operand always equals the result)
To prove EQ2: x = x*(x*((y*z)*x))

Step-by-step: EQ1 says [anything]*x = x for all x.
  (y*z)*x = x          [apply EQ1: second arg is x → result is x]
  x*x = x              [apply EQ1 with first-arg=x, second-arg=x → result is x]
  x*(x*((y*z)*x))
   = x*(x*x)           [by step 1: (y*z)*x = x]
   = x*x               [by step 2: x*x = x]
   = x                 [by step 2]
  ✓ EQ2 proved.

KEY: Write out which slot in EQ1 you're filling with which term. Don't skip steps.
```

### Fix 5: Add 3-element magma guidance

Since hard3 requires 3+ element counterexamples, add at least one explicit 3-element magma to test:

```
Magma H - "Partial zero": On {0,1,2}, define x*y = 0 if x=0, else y.
  (Or equivalently: check x*y = floor(x/max)*y)
  Tests cases where EQ1 is satisfied by a non-projection, non-constant magma.
```

Alternatively, instruct the model to try constructing a 3-element table when standard magmas fail and the problem seems like it should be FALSE.

### Fix 6: Add explicit FALSE signal for hard structural patterns

The 32 "both wrong TRUE" cases share patterns in EQ1. Common EQ1 structures that have FALSE implications even when standard magmas can't show it:

- `x = EXP * x` where EXP involves x (often has 3-element CE)
- `x*x = EXP` where EXP varies with variables not on LHS (often has 3-element CE)
- `x = EXP1 * EXP2` where both expressions involve x (often needs larger CE)

Add a heuristic: "If EQ1 has the form `x*x = f(y,z,...)` or `x = f(y,z,...)*x` where the free variables appear only on one side and EQ2 changes the relationship — lean FALSE even if no standard counterexample found."

### Fix 7: Strengthen the default judgment balance

The asymmetry between Haiku (defaults TRUE) and Gemini (defaults FALSE) suggests the Step 5 defaults are too aggressive in both models. Consider:

- Replace the current heuristic list with: "If proof found → TRUE. If valid counterexample found → FALSE. Otherwise: if EQ1 only admits trivial models and all those models also satisfy EQ2 → TRUE. Otherwise → uncertain (consider FALSE if EQ2 adds new variables or complexity that EQ1 doesn't constrain)."
- Explicitly warn: "Do NOT say TRUE just because no counterexample was found. Do NOT say FALSE just because no proof was found."

### Fix 8: Address the hard3 fundamental challenge

The hard3 dataset was designed to defeat simple structural heuristics and 2-element counterexample strategies. For v6 to improve on both models, the cheatsheet needs either:

(a) More sophisticated counterexample magmas (3+ element) with shortcuts for evaluation, OR
(b) Better proof-by-substitution guidance for the TRUE cases, OR
(c) Pattern recognition for specific EQ1 forms that have known TRUE/FALSE outcomes

Option (c) is most tractable: the 36 "both wrong FALSE/answer TRUE" cases show recurring EQ1 patterns like `x = ((y*(...)*z)*w)*x` (ends in `)*x`) which tend to be TRUE because appending `*x` to the product chain repeatedly reduces back to x.

---

## 10. Key Takeaways for v6 Development

1. **v5 is not working for hard3.** Haiku F1=0.586 and Gemini F1=0.309 are both below a reasonable threshold. The dataset is genuinely harder than what v5 was designed for.

2. **The two models fail in opposite directions.** A combined ensemble (majority vote) of Haiku and Gemini would likely outperform either alone, but since only one model is used per submission, we need a cheatsheet that balances both failure modes.

3. **The XOR parity check is broken in practice.** Despite being correctly described in v5, models systematically misapply it. A worked example with explicit per-variable counting is essential.

4. **Step 5 defaults are the biggest single problem.** Both models over-rely on Step 5 heuristics and reach wrong conclusions by defaulting too aggressively. The heuristics in v5 need to be rebalanced and their limitations explicitly stated.

5. **The hard3 FALSE cases need a counterexample strategy beyond the current 7 magmas.** This is the fundamental gap. Either add 3-element magma tests or accept that ~50% of hard3 FALSE cases will be missed.
