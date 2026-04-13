#!/usr/bin/env python3 -u
"""
Micro-benchmark: test different instruction strategies for magma expression evaluation.
Isolates the evaluation sub-skill from the full CE-finding pipeline.

Tests: can Haiku correctly evaluate an expression in Magma H/I/J given different instructions?
"""
import json, random, itertools, os, time, argparse
from pathlib import Path
import anthropic

# ── expression generation ──────────────────────────────────────────────────────

def random_expr(variables, depth, rng):
    """Generate a random expression tree of given max depth."""
    if depth == 0 or (depth == 1 and rng.random() < 0.5):
        return rng.choice(variables)
    left = random_expr(variables, depth - 1, rng)
    right = random_expr(variables, depth - 1, rng)
    return ('*', left, right)

def expr_to_str(expr):
    if isinstance(expr, str): return expr
    _, l, r = expr
    ls = expr_to_str(l)
    rs = expr_to_str(r)
    ls = f"({ls})" if isinstance(l, tuple) else ls
    rs = f"({rs})" if isinstance(r, tuple) else rs
    return f"{ls} * {rs}"

def get_vars(expr):
    if isinstance(expr, str): return {expr}
    return get_vars(expr[1]) | get_vars(expr[2])

def eval_expr(expr, env, table, n):
    if isinstance(expr, str): return env[expr]
    _, l, r = expr
    return table[eval_expr(l,env,table,n)*n + eval_expr(r,env,table,n)]

# ── magma definitions ──────────────────────────────────────────────────────────

MAGMAS = {
    'H': (3, [1,2,0, 1,2,0, 1,2,0], "Right-shift: x*y = (y+1) mod 3"),
    'I': (3, [1,1,1, 2,2,2, 0,0,0], "Left-shift: x*y = (x+1) mod 3"),
    'J': (3, [0,0,0, 2,1,1, 1,2,2], "Null-left: 0*y=0; x*y=x if x≠0,y≠0; x*y=(3-x) if x≠0,y=0"),
}

# ── instruction strategies ─────────────────────────────────────────────────────

STRATEGIES = {}

STRATEGIES['H_bottomup'] = """Magma H — Right-shift: x*y = (y+1) mod 3, values in {0,1,2}.

Evaluation rule (bottom-up, innermost first):
  - Bare variable: evaluates to itself.
  - Any node (A * B): result = (eval(B) + 1) mod 3. Left child A is ignored entirely.

Quick reference:
  x*y → (y+1)%3
  (x*y)*z → (z+1)%3
  x*(y*z) → (z+2)%3
  (x*y)*(z*w) → (w+2)%3

Evaluate the expression and write only the final integer answer (0, 1, or 2)."""

STRATEGIES['H_spine'] = """Magma H — Right-shift: x*y = (y+1) mod 3, values in {0,1,2}.

SIMPLE RULE — two steps only:
  Step 1: Find the RIGHTMOST LEAF by always following the RIGHT child at each * node.
  Step 2: Count how many * nodes you passed following right children (call it D).
  Answer: (rightmost_leaf_value + D) mod 3.

Example: x * (y * z)
  Step 1: from root, go right → (y*z), go right → z. Rightmost leaf = z.
  Step 2: passed 2 * nodes. D=2.
  Answer: (z + 2) mod 3.

Example: (x*y) * z
  Step 1: from root, go right → z (leaf). Rightmost = z.
  Step 2: passed 1 * node. D=1.
  Answer: (z + 1) mod 3.

Evaluate the expression and write only the final integer answer (0, 1, or 2)."""

STRATEGIES['H_table'] = """Magma H — Right-shift on {0,1,2}. Full multiplication table:

  *  | 0  1  2
  ---|--------
  0  | 1  2  0
  1  | 1  2  0
  2  | 1  2  0

(Rows = left operand, Columns = right operand)

To evaluate a compound expression: substitute variable values, then look up each * operation
in the table from innermost parentheses outward.

Evaluate the expression and write only the final integer answer (0, 1, or 2)."""

STRATEGIES['H_trace'] = """Magma H — Right-shift: x*y = (y+1) mod 3, values in {0,1,2}.

Rule: for any (A * B), result = (value_of_B + 1) mod 3. Left side is irrelevant.

REQUIRED FORMAT: evaluate bottom-up, writing one line per operation:
  "[subexpr] = [result]"
Then state the final answer.

Example for x*(y*z) with x=0,y=1,z=2:
  (y*z) = (2+1)%3 = 0
  x*(y*z) = (0+1)%3 = 1
  ANSWER: 1

Evaluate the expression using this format, then write the final integer answer."""

STRATEGIES['I_bottomup'] = """Magma I — Left-shift: x*y = (x+1) mod 3, values in {0,1,2}.

Evaluation rule (bottom-up, innermost first):
  - Bare variable: evaluates to itself.
  - Any node (A * B): result = (eval(A) + 1) mod 3. Right child B is ignored entirely.

Quick reference:
  x*y → (x+1)%3
  (x*y)*z → (x+2)%3
  x*(y*z) → (x+1)%3
  (x*y)*(z*w) → (x+2)%3

CRITICAL: x*(ANYTHING) — outer left is bare x, so result=(x+1)%3, NOT (x+2)%3.
          (x*y)*z — outer left is (x*y)=(x+1)%3, so result=(x+2)%3.

Evaluate the expression and write only the final integer answer (0, 1, or 2)."""

STRATEGIES['I_spine'] = """Magma I — Left-shift: x*y = (x+1) mod 3, values in {0,1,2}.

SIMPLE RULE — two steps only:
  Step 1: Find the LEFTMOST LEAF by always following the LEFT child at each * node.
  Step 2: Count how many * nodes you passed following left children (call it D).
  Answer: (leftmost_leaf_value + D) mod 3.

Example: x * (y * z)
  Step 1: from root, go left → x (leaf). Leftmost = x.
  Step 2: passed 1 * node. D=1.
  Answer: (x + 1) mod 3.

Example: (x*y) * z
  Step 1: from root, go left → (x*y), go left → x (leaf). Leftmost = x.
  Step 2: passed 2 * nodes. D=2.
  Answer: (x + 2) mod 3.

Evaluate the expression and write only the final integer answer (0, 1, or 2)."""

STRATEGIES['I_table'] = """Magma I — Left-shift on {0,1,2}. Full multiplication table:

  *  | 0  1  2
  ---|--------
  0  | 1  1  1
  1  | 2  2  2
  2  | 0  0  0

(Rows = left operand, Columns = right operand)

To evaluate: substitute values, look up each * from innermost outward.

Evaluate the expression and write only the final integer answer (0, 1, or 2)."""

STRATEGIES['I_trace'] = """Magma I — Left-shift: x*y = (x+1) mod 3, values in {0,1,2}.

Rule: for any (A * B), result = (value_of_A + 1) mod 3. Right side is irrelevant.

REQUIRED FORMAT: evaluate bottom-up, one line per operation:
  "[subexpr] = [result]"

Example for (x*y)*z with x=0,y=1,z=2:
  (x*y) = (0+1)%3 = 1
  (x*y)*z = (1+1)%3 = 2
  ANSWER: 2

Evaluate using this format, then write the final integer answer."""

STRATEGIES['J_shortcut'] = """Magma J — "Null-left" on {0,1,2}.
Table: 0*y=0 always; 1*0=2, 1*1=1, 1*2=1; 2*0=1, 2*1=2, 2*2=2.
Shortcut: result=0 if x=0; result=x if x≠0 and y≠0; result=(3-x) if x≠0 and y=0.

Evaluate bottom-up (innermost first). Write only the final integer answer (0, 1, or 2)."""

STRATEGIES['J_table'] = """Magma J — "Null-left" on {0,1,2}. Full multiplication table:

  *  | 0  1  2
  ---|--------
  0  | 0  0  0
  1  | 2  1  1
  2  | 1  2  2

(Rows = left operand, Columns = right operand)

Evaluate by looking up each * from innermost outward. Write only the final integer answer."""

STRATEGIES['J_trace'] = """Magma J — "Null-left" on {0,1,2}.
Table: 0*y=0; 1*0=2,1*1=1,1*2=1; 2*0=1,2*1=2,2*2=2.

REQUIRED FORMAT: one line per operation showing lookup:
  "[subexpr]: [left_val]*[right_val]=[result]"

Example for x*(y*z) with x=1,y=2,z=0:
  (y*z): 2*0=1
  x*(y*z): 1*1=1
  ANSWER: 1

Evaluate using this format, then write the final integer answer."""

# ── benchmark generation ───────────────────────────────────────────────────────

def generate_problems(magma_name, n=40, seed=42):
    rng = random.Random(seed)
    n_elem, table, _ = MAGMAS[magma_name]
    variables = ['x', 'y', 'z']
    problems = []
    seen = set()
    attempts = 0
    while len(problems) < n and attempts < n * 20:
        attempts += 1
        depth = rng.randint(1, 3)
        expr = random_expr(variables, depth, rng)
        expr_str = expr_to_str(expr)
        used_vars = sorted(get_vars(expr))
        env = {v: rng.randint(0, n_elem-1) for v in used_vars}
        answer = eval_expr(expr, env, table, n_elem)
        key = (expr_str, tuple(sorted(env.items())))
        if key in seen: continue
        seen.add(key)
        # Filter trivial (single variable)
        if isinstance(expr, str): continue
        problems.append({
            'expr': expr_str,
            'env': env,
            'answer': answer,
            'magma': magma_name,
        })
    return problems

# ── test runner ────────────────────────────────────────────────────────────────

def build_eval_prompt(strategy_text, expr, env):
    var_str = ', '.join(f"{k}={v}" for k,v in sorted(env.items()))
    return f"{strategy_text}\n\nExpression: {expr}\nGiven: {var_str}\n\nAnswer:"

def extract_answer(text):
    import re
    # Look for final integer 0,1,2
    matches = re.findall(r'\bANSWER:\s*([0-2])\b|\b([0-2])\s*$', text.strip(), re.MULTILINE)
    if matches:
        for m in reversed(matches):
            val = m[0] or m[1]
            if val: return int(val)
    # Last number in response
    nums = re.findall(r'\b[0-2]\b', text)
    if nums: return int(nums[-1])
    return None

def run_strategy(strategy_name, strategy_text, problems, client, delay=0.3):
    results = []
    for i, p in enumerate(problems):
        prompt = build_eval_prompt(strategy_text, p['expr'], p['env'])
        try:
            msg = client.messages.create(
                model='claude-haiku-4-5-20251001',
                max_tokens=512,
                temperature=0.0,
                messages=[{'role':'user','content':prompt}]
            )
            response = msg.content[0].text
            predicted = extract_answer(response)
            correct = (predicted == p['answer'])
            results.append({**p, 'predicted': predicted, 'correct': correct, 'response': response})
        except Exception as e:
            results.append({**p, 'predicted': None, 'correct': False, 'error': str(e)})
        if i % 10 == 9:
            acc = sum(r['correct'] for r in results) / len(results)
            print(f"  [{strategy_name}] {i+1}/{len(problems)}  acc so far: {acc:.0%}")
        time.sleep(delay)
    return results

def score(results):
    n = len(results)
    correct = sum(r['correct'] for r in results)
    unparsed = sum(1 for r in results if r['predicted'] is None)
    return correct, n, unparsed

# ── main ───────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--magmas', default='H,I,J', help='Comma-separated magmas to test')
    p.add_argument('--n', type=int, default=40, help='Problems per strategy')
    p.add_argument('--output', default='results/magma_eval_bench.json')
    p.add_argument('--delay', type=float, default=0.3)
    args = p.parse_args()

    client = anthropic.Anthropic()
    magmas_to_test = args.magmas.split(',')

    # Strategy groups per magma
    strategy_map = {
        'H': ['H_bottomup', 'H_spine', 'H_table', 'H_trace'],
        'I': ['I_bottomup', 'I_spine', 'I_table', 'I_trace'],
        'J': ['J_shortcut', 'J_table', 'J_trace'],
    }

    all_results = {}
    summary = {}

    for magma in magmas_to_test:
        print(f"\n{'='*50}")
        print(f"Magma {magma} — generating {args.n} problems...")
        problems = generate_problems(magma, args.n)
        print(f"Generated {len(problems)} problems")

        for strat_name in strategy_map.get(magma, []):
            print(f"\n  Strategy: {strat_name}")
            results = run_strategy(strat_name, STRATEGIES[strat_name], problems, client, args.delay)
            correct, n, unparsed = score(results)
            acc = correct/n
            print(f"  RESULT: {correct}/{n} = {acc:.1%}  (unparsed: {unparsed})")
            all_results[strat_name] = results
            summary[strat_name] = {'correct': correct, 'n': n, 'accuracy': acc, 'unparsed': unparsed}

    # Save
    json.dump({'summary': summary, 'results': {k: v for k,v in all_results.items()}},
              open(args.output, 'w'), indent=2)

    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    for magma in magmas_to_test:
        print(f"\nMagma {magma}:")
        for s in strategy_map.get(magma, []):
            if s in summary:
                r = summary[s]
                print(f"  {s:<20} {r['correct']:>3}/{r['n']}  {r['accuracy']:>6.1%}")

if __name__ == '__main__':
    main()
