#!/usr/bin/env python3 -u
"""
Test Haiku's magma arithmetic in isolation — no cheatsheet, just one magma at a time.
For each problem, ask: "Does EQ1 hold universally in this magma? If yes, does EQ2 fail?"

Usage:
  export ANTHROPIC_API_KEY=...
  python tests/10_magma_arithmetic_isolation/run_test.py
"""

import json, os, re, time
import anthropic

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

MAGMA_DESCRIPTIONS = {
    'H': {
        'name': 'Right-shift',
        'elements': '{0, 1, 2}',
        'rule': 'x*y = (y+1) mod 3',
        'table': '0*0=1, 0*1=2, 0*2=0, 1*0=1, 1*1=2, 1*2=0, 2*0=1, 2*1=2, 2*2=0',
    },
    'I': {
        'name': 'Left-shift',
        'elements': '{0, 1, 2}',
        'rule': 'x*y = (x+1) mod 3',
        'table': '0*0=1, 0*1=1, 0*2=1, 1*0=2, 1*1=2, 1*2=2, 2*0=0, 2*1=0, 2*2=0',
    },
    'J': {
        'name': 'Null-left',
        'elements': '{0, 1, 2}',
        'rule': '0*y=0 for all y; for x!=0: x*y=x if y!=0, x*y=(3-x) if y=0',
        'table': '0*0=0, 0*1=0, 0*2=0, 1*0=2, 1*1=1, 1*2=1, 2*0=1, 2*1=2, 2*2=2',
    },
    'K': {
        'name': 'Swap-row2',
        'elements': '{0, 1, 2}',
        'rule': 'x*y=y if x is 0 or 1; 2*0=1, 2*1=0, 2*2=2',
        'table': '0*0=0, 0*1=1, 0*2=2, 1*0=0, 1*1=1, 1*2=2, 2*0=1, 2*1=0, 2*2=2',
    },
}

PROMPT_TEMPLATE = """Consider the magma on {elements} where {rule}.

Full operation table: {table}

Equation 1: {eq1}
Equation 2: {eq2}

Question 1: Does Equation 1 hold for ALL possible assignments of variables to elements? Test systematically.
Question 2: If Equation 1 holds universally, does Equation 2 FAIL for some specific assignment?

Answer each question with YES or NO and show your work."""


def run_test(api_key):
    client = anthropic.Anthropic(api_key=api_key)

    results = {}
    for mag_name in ['H', 'I', 'J', 'K']:
        mag = MAGMA_DESCRIPTIONS[mag_name]
        problems = json.load(open(os.path.join(TEST_DIR, f'magma_{mag_name}_problems.json')))

        mag_results = []
        correct = 0
        total = 0

        for idx, p in enumerate(problems):
            prompt = PROMPT_TEMPLATE.format(
                elements=mag['elements'], rule=mag['rule'], table=mag['table'],
                eq1=p['equation1'], eq2=p['equation2']
            )

            try:
                resp = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=2000,
                    temperature=0,
                    messages=[{"role": "user", "content": prompt}]
                )
                text = resp.content[0].text
            except Exception as e:
                text = f"ERROR: {e}"
                time.sleep(5)

            # Parse: did it say EQ1 holds? Did it say EQ2 fails?
            text_upper = text.upper()

            # Look for EQ1 verdict
            eq1_holds = None
            if re.search(r'EQUATION 1 HOLDS (UNIVERSALLY|FOR ALL)', text_upper):
                eq1_holds = True
            elif re.search(r'EQUATION 1 DOES NOT HOLD|EQUATION 1 FAILS|EQ1.*DOES NOT HOLD|EQ1.*FAILS', text_upper):
                eq1_holds = False
            elif re.search(r'QUESTION 1.*YES', text_upper):
                eq1_holds = True
            elif re.search(r'QUESTION 1.*NO', text_upper):
                eq1_holds = False

            # Look for EQ2 verdict
            eq2_fails = None
            if eq1_holds:
                if re.search(r'EQUATION 2 FAILS|EQ2.*FAILS|QUESTION 2.*YES', text_upper):
                    eq2_fails = True
                elif re.search(r'EQUATION 2 HOLDS|EQ2.*HOLDS|QUESTION 2.*NO', text_upper):
                    eq2_fails = False

            # Determine if model thinks this is a CE
            model_says_ce = eq1_holds and eq2_fails
            actual_ce = p['is_ce']

            is_correct = (model_says_ce == actual_ce) if model_says_ce is not None else False
            if eq1_holds == False and actual_ce == False:
                is_correct = True  # correctly identified EQ1 doesn't hold

            if is_correct:
                correct += 1
            total += 1

            tag = '✓' if is_correct else '✗'
            ce_str = "IS_CE" if actual_ce else "NOT_CE"
            model_str = f"eq1={'holds' if eq1_holds else 'fails' if eq1_holds==False else '?'}"
            if eq1_holds:
                model_str += f",eq2={'fails' if eq2_fails else 'holds' if eq2_fails==False else '?'}"

            print(f"  {tag} Magma {mag_name} [{idx+1}/{len(problems)}] {p['id']}: {ce_str} → {model_str}")

            mag_results.append({
                'id': p['id'], 'is_ce': actual_ce,
                'eq1_holds': eq1_holds, 'eq2_fails': eq2_fails,
                'model_says_ce': model_says_ce, 'correct': is_correct,
                'response': text,
            })

            time.sleep(0.5)

        print(f"\n  Magma {mag_name}: {correct}/{total} correct ({correct/total*100:.0f}%)\n")
        results[mag_name] = {
            'correct': correct, 'total': total,
            'accuracy': correct/total if total else 0,
            'results': mag_results,
        }

        # Save incrementally
        with open(os.path.join(TEST_DIR, 'results.json'), 'w') as f:
            json.dump(results, f, indent=2)

    # Final summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for mag_name, r in results.items():
        is_ce_correct = sum(1 for x in r['results'] if x['is_ce'] and x['correct'])
        is_ce_total = sum(1 for x in r['results'] if x['is_ce'])
        not_ce_correct = sum(1 for x in r['results'] if not x['is_ce'] and x['correct'])
        not_ce_total = sum(1 for x in r['results'] if not x['is_ce'])
        print(f"  Magma {mag_name}: {r['correct']}/{r['total']} ({r['accuracy']*100:.0f}%)"
              f"  [IS_CE: {is_ce_correct}/{is_ce_total}, NOT_CE: {not_ce_correct}/{not_ce_total}]")


if __name__ == '__main__':
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ERROR: Set ANTHROPIC_API_KEY")
        exit(1)
    run_test(api_key)
