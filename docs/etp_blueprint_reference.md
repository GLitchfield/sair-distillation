# ETP Blueprint Reference — Equational Theories of Magmas
## For the SAIR Mathematics Distillation Challenge

This document distills the key mathematical content from the Equational Theories Project (ETP) blueprint at https://teorth.github.io/equational_theories/blueprint/ into a reference useful for building cheat sheets that help LLMs classify whether one equational law implies another over magmas.

---

## 1. Core Definitions

### Magma
A set G equipped with a binary operation ◇ : G × G → G. No other axioms (no associativity, commutativity, identity, or inverses). Groups, semigroups, monoids are all special cases.

### Free Magma
The set M_X of all finite formal expressions built from variables in alphabet X and the operation ◇. These are binary trees. The number of words of order n (using n ◇ symbols) is C_n × |X|^(n+1), where C_n is the nth Catalan number.

Example with X = {0, 1}: Order 0: 0, 1. Order 1: 0◇0, 0◇1, 1◇0, 1◇1. Order 2: 0◇(0◇0), 0◇(0◇1), ..., (1◇1)◇1 (16 words).

### Induced Homomorphism
Given f: X → G mapping variables to magma elements, φ_f: M_X → G is the unique extension evaluating formal expressions in G. It satisfies φ_f(w₁ ◇ w₂) = φ_f(w₁) ◇ φ_f(w₂). This is just "plug in values and evaluate."

### Law
A pair of words (w, w') written w ≃ w'. A magma G **satisfies** w ≃ w' if φ_f(w) = φ_f(w') for ALL functions f: X → G. A magma **violates** the law if ANY single assignment makes the sides unequal.

### Implication
Law E implies E' (written E ⊨ E') if every magma satisfying E also satisfies E'. Two laws are equivalent if they imply each other.

### The 4694 Laws
Up to relabeling, symmetry, and removing trivial identities, there are exactly 4694 laws of total order ≤ 4 (total order = sum of ◇ counts on both sides). These are numbered E1 through E4694. List: https://github.com/teorth/equational_theories/blob/main/data/equations.txt

---

## 2. Key Structural Results

### Birkhoff's Completeness Theorem (Theorem 1.8)
Γ ⊢ w ≃ w' (derivable by rewrite rules) if and only if Γ ⊨ w ≃ w' (semantically true in all models).

**Consequence**: If E1 implies E2, there exists a finite chain of substitution and rewriting steps that derives E2 from E1. This is what automated theorem provers exploit.

### Derivation Rules (Definition 1.7)
From a theory Γ, you can derive new laws by:
1. Using axioms from Γ directly
2. Reflexivity: w ≃ w
3. Symmetry: if w ≃ w', then w' ≃ w
4. Transitivity: if w ≃ w' and w' ≃ w'', then w ≃ w''
5. Substitution: if w ≃ w', then φ_f(w) ≃ φ_f(w') for any f (replace variables with expressions)
6. Congruence: if w₁ ≃ w₂ and w₃ ≃ w₄, then w₁◇w₃ ≃ w₂◇w₄

### Pre-order (Lemma 3.2)
Implication defines a pre-order on laws. Convention: stronger law ≤ weaker law (the class of models of the stronger law is a subset).
- **Maximal (weakest)**: E1, the law 0 ≃ 0 (x = x), satisfied by every magma
- **Minimal (strongest)**: E2, the law 0 ≃ 1 (x = y), forces singleton

### Duality (Lemma 3.5)
Every magma G has a reversal G^op where x ◇^op y := y ◇ x. Every law has a dual obtained by reversing all operations. E1 implies E2 if and only if dual(E1) implies dual(E2). Of 4694 laws, 84 are self-dual, leaving 2305 dual pairs.

### Diagonalization (Theorem 3.6)
If a law has the form F(x₁,...,xₙ) = G(y₁,...,yₘ) where the variable sets are disjoint, it implies F(x₁,...,xₙ) = F(x'₁,...,x'ₙ). For example, E7 (x = y ◇ z) is equivalent to E2 (x = y) because you can apply it twice with different variable choices.

### Constant Law (Theorem 3.7)
E46 (x ◇ y = z ◇ w) implies any law w ≃ w' where both sides have order ≥ 1. If exactly one side has order 0 (is a bare variable), the constant law does NOT imply it.

---

## 3. Necessary Conditions for Implication (Metatheorems)

### Variable Count Criterion (Theorem 3.8)
**CRITICAL FOR COMPETITION**: If E1 has every variable appearing the same number of times on both sides, and E1 implies E2, then E2 must also have every variable appearing the same number of times on both sides.

**Proof**: The magma of multisets with multiset addition satisfies any law where variable counts match. If E1 implies E2, this magma satisfies E2, so E2's counts must match too.

**Contrapositive**: If E1 has balanced variable counts but E2 doesn't, then E1 CANNOT imply E2.

### Invariants — The General Framework (Chapter 9)

An **invariant** for equation E is a function I on expressions such that E implies (w = w') if and only if I(w) = I(w'). The **fundamental property of invariants**: if I(w) = I(w') and I(w'') ≠ I(w'''), then w = w' cannot imply w'' = w'''.

Key invariant examples:

| Equation | Invariant I(w) | What it captures |
|----------|---------------|------------------|
| x ◇ y = x (left absorption) | Leftmost variable of w | Only the leftmost leaf matters |
| x ◇ y = y (right absorption) | Rightmost variable of w | Only the rightmost leaf matters |
| Associativity x◇(y◇z) = (x◇y)◇z | Ordered list of variables in w | Parenthesization doesn't matter |
| Assoc + Commutativity | Multiset of variables in w | Order doesn't matter either |
| Assoc + Idempotency | Set of variables in w | Repetition doesn't matter either |
| Assoc + Comm + x^m = 1 | Multiset of variables mod m | Counts only matter mod m |

### Lifting Magma Families (Definition 9.7)
A family of magmas {G_α} (one per type α) with an embedding ι_α: α → G_α and a lifting property: any f: α → G_α extends to a homomorphism. These formalize invariants semantically.

**Evaluation Theorem (9.8)**: To check if a lifting magma family satisfies a law, it suffices to check with the specific substitution ι (plugging in the "generic" elements). This is computationally much cheaper than checking all substitutions.

Examples: Free abelian groups (gives multiset invariant), Lists (gives ordered-list invariant).

---

## 4. Finite vs. Infinite Magmas (Chapter 5)

### The Key Principle
On a finite set, if f: X → X is injective then it's surjective, and vice versa (pigeonhole principle). This FAILS for infinite sets. Many implications hold for finite magmas but fail for infinite ones.

### Austin Laws
An **Austin law** is one that admits infinite models but NO nontrivial finite models (equivalent to E2 for finite magmas). No law of order ≤ 4 is Austin, but they exist at order 5+.

### The 820 Finite-Only Implications
There are exactly 820 implications between order-≤4 laws that hold for finite magmas but not infinite ones. Listed at: https://github.com/teorth/equational_theories/blob/main/data/Austin_implications.txt

**These are all FALSE for the competition** (which asks about ALL magmas including infinite).

### How Finite-Only Implications Work
The typical pattern: E1 forces some function (like left-multiplication L_y) to be surjective. On finite sets, surjective → injective → cancellation → can derive E2. On infinite sets, surjective ≠ injective, so the derivation breaks.

**Example (Asterix E65 vs Obelix E1491)**: Asterix forces L_y surjective. Finite → injective → cancellative → can derive Obelix. Infinite → constructed counterexample on integers where L_y is surjective but not injective.

### Useful Finite-Model Lemmas
- **f ∘ g = I on finite set → g ∘ f = I** (inverse is two-sided)
- **f = f ∘ f ∘ g on finite set → f = f ∘ g ∘ f** (Lemma 5.5)
- **f = g ∘ f ∘ f on finite set → f = f ∘ g ∘ f** (Lemma 5.6)
- **Eventual period**: for f: X → X with X finite, ∃ n ≥ 1 with f^(2n) = f^n (Lemma 5.7)

---

## 5. Counterexample Magma Constructions

### Small Finite Magmas
Most FALSE implications (for unrestricted magmas) can be refuted by magmas on 2-4 elements. From our data analysis:
- ~90% of FALSE cases on the normal problem set are refuted by a 2-element magma
- 4 specific magmas cover 85% of FALSE cases:

| Magma | Operation | Mental evaluation |
|-------|-----------|-------------------|
| Constant-zero | x◇y = 0 | All compound expressions → 0. Equation holds iff both sides are compound, or both are the same bare variable. |
| Right projection | x◇y = y | Expression → rightmost leaf variable |
| Left projection | x◇y = x | Expression → leftmost leaf variable |
| XOR (on {0,1}) | x◇y = x+y mod 2 | Count variable occurrences; equation holds iff every variable has same parity on both sides |

### Linear Magmas
Define x ◇ y = ax + by in a ring. Every expression becomes a linear combination Σ Pᵢ(a,b)·xᵢ where Pᵢ are polynomials in a,b. Checking if an equation holds reduces to checking polynomial identities.

Over Z/nZ for small n, this gives many counterexamples that small finite magmas miss.

### Free Magma Constructions
For laws with confluent rewriting systems, the free magma quotient provides canonical counterexamples.

### Greedy/Ad-Hoc Infinite Constructions
For the hardest cases (Asterix/Obelix type), infinite magmas are constructed by:
1. Starting with an operation on natural numbers
2. Defining it to satisfy E1 in specific cases
3. Using greedy algorithms to fill in remaining values while avoiding E2

---

## 6. Magma Cohomology (Chapter 11)

### The Construction
Given magma G satisfying E, and abelian group M with linear operation s◇t = as + bt also satisfying E:

1. **Extension**: Build magma on G × M via (x,s)◇(y,t) = (x◇y, as + bt + f(x,y))
2. **E-cocycle**: f: G×G → M such that the extension satisfies E. Space: Z²_E(G,M)
3. **Coboundary**: f(x,y) = g(x◇y) - ag(x) - bg(y) for some g: G → M. Space: B²(G,M)
4. **Cohomology**: H²_E(G,M) = Z²_E(G,M) / B²(G,M)

### The Punchline
If E implies E', then H²_E(G,M) ⊆ H²_E'(G,M). To refute E → E', find G, M where this containment fails. Computing these groups is **pure linear algebra** (Gaussian elimination over finite fields).

### Worked Example
E1110 (x = y ◇ ((y ◇ (x ◇ x)) ◇ y)) vs E1629 (x = (x◇x) ◇ ((x◇x) ◇ x)):
- G = M = F₅, operation x◇y = 3x - y (a=3, b=-1 mod 5; satisfies golden ratio equation)
- B² is 4-dimensional, Z²_E1110 is 6-dimensional → H²_E1110 is 2-dimensional
- Find element of H²_E1110 not in H²_E1629 → counterexample on G×M (25-element magma)

### Connection to Standard Theory
When E is associativity and a=b=1, the cocycle condition becomes f(x,y) + f(x◇y,z) = f(x,y◇z) + f(y,z) — standard group cohomology.

---

## 7. Notation Conventions Used in ETP

| Notation | Meaning |
|----------|---------|
| L_y or L_y(x) | Left multiplication: y ◇ x |
| R_y or R_y(x) | Right multiplication: x ◇ y |
| Sx or S(x) | Squaring: x ◇ x |
| Cx | x ◇ (x ◇ x) or (x ◇ x) ◇ x (context-dependent) |
| G^op | Reversal magma: x ◇^op y := y ◇ x |
| E* | Dual law of E (reverse all operations) |
| ⊨ or |= | Semantic implication (true in all models) |
| ⊢ | Syntactic derivation (provable by rewrite rules) |
| ⊨_fin | Implication restricted to finite magmas |

---

## 8. Decision Procedures and Tools Used by ETP

| Tool | What it does | Typical use |
|------|-------------|-------------|
| Vampire/Prover9 | Automated theorem provers | Proving TRUE implications via rewrite chains |
| Mace4 | Finite model finder | Finding small counterexample magmas for FALSE |
| Z3 | SMT solver | Encoding finite magma search as constraint satisfaction |
| E-graphs (egg/egglog) | Equality saturation | Efficient rewrite exploration |
| Lean 4 | Proof assistant | Formal verification of all results |

### Key Fact
Every TRUE implication between order-≤4 laws was within reach of automated theorem provers. All the hard work was on the FALSE side — constructing counterexamples.

---

## 9. Quick Reference: Equation Classes

### Singleton-Forcing Laws
If a law has a bare variable on one side that doesn't appear on the other side (e.g., x = y ◇ z where x is not in y◇z), it forces the magma to be a singleton. Such laws are equivalent to E2 and imply everything.

### The Constant Law E46 (x ◇ y = z ◇ w)
Forces all products to be equal (x◇y is constant). Implies any law where both sides have order ≥ 1.

### Idempotent Laws
Laws implying x ◇ x = x (or more generally, some form of x = f(x)).

### Commutative Laws
Laws implying or related to x ◇ y = y ◇ x.

### Associative Law E4512 (x ◇ (y ◇ z) = (x ◇ y) ◇ z)
Combined with other properties, gives rich structure theory. The invariant is the ordered variable list.

---

## 10. Practical Strategy for the Competition

### For FALSE (finding counterexamples):
1. Check singleton-forcing conditions on E2 (bare variable not on other side → E1 trivially implies everything, so if E2 is not implied, E1 is not singleton-forcing... but check E2's structure)
2. Test specific small magmas: constant-zero, left-proj, right-proj, XOR, and linear magmas over Z/2Z and Z/3Z
3. Check invariant mismatches: leftmost variable, rightmost variable, variable multiset, variable parity
4. For hard cases: consider whether the implication might be finite-only (Austin type)

### For TRUE (proving implications):
1. Check if E2 is a direct substitution instance of E1
2. Attempt short rewrite chains (1-4 steps of substitution + simplification)
3. Check if E1 is equivalent to a well-known strong law (singleton, constant, etc.)
4. Use the invariant framework: if E1's invariant is finer than E2's invariant, implication may hold

### Key Heuristic Signals:
- E2 has simpler LHS than E1 → lean FALSE
- E2 introduces new variables not in E1 → lean FALSE
- E1 forces operations to be constant/trivial → lean TRUE
- Both equations have similar structure with minor rearrangement → lean TRUE

---

## Sources
- ETP Blueprint: https://teorth.github.io/equational_theories/blueprint/
- ETP Paper: https://teorth.github.io/equational_theories/paper.pdf
- ETP GitHub: https://github.com/teorth/equational_theories
- Tao's Blog Posts: https://terrytao.wordpress.com/tag/equational-theory-project/
- Competition: https://competition.sair.foundation/competitions/mathematics-distillation-challenge-equational-theories-stage1/overview
