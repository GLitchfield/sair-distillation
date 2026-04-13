#!/usr/bin/env python3 -u
"""
Run decompose prompt × 30 iterations for Magma K and Magma L.
K correct answer: EQ1 YES, EQ2 YES (CE at x=2,y=0,z=0)
L correct answer: EQ1 YES, EQ2 YES (CE at x=0,y=2,z=0)
"""

import anthropic, json, os, time

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(TEST_DIR, 'prompt_KL_results.json')

PROMPTS = {
    'K_decompose': 'prompt_K_decompose.txt',
    'L_decompose': 'prompt_L_decompose.txt',
}

N_RUNS = 30


def parse_response(text):
    text_upper = text.upper()
    eq1 = None
    eq2 = None
    if 'EQ1 HOLDS UNIVERSALLY: YES' in text_upper:
        eq1 = True
    elif 'EQ1 HOLDS UNIVERSALLY: NO' in text_upper:
        eq1 = False
    if 'EQ2 FAILS FOR SOME ASSIGNMENT: YES' in text_upper:
        eq2 = True
    elif 'EQ2 FAILS FOR SOME ASSIGNMENT: NO' in text_upper:
        eq2 = False
    elif 'EQ2 FAILS FOR SOME ASSIGNMENT: N/A' in text_upper:
        eq2 = None
    return eq1, eq2


def main():
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ERROR: Set ANTHROPIC_API_KEY")
        exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    if os.path.exists(OUTPUT_PATH):
        all_results = json.load(open(OUTPUT_PATH))
    else:
        all_results = {}

    for prompt_name, prompt_file in PROMPTS.items():
        prompt_text = open(os.path.join(TEST_DIR, prompt_file)).read()

        if prompt_name in all_results and len(all_results[prompt_name]['runs']) >= N_RUNS:
            print(f"Skipping {prompt_name} — already done")
            continue

        if prompt_name not in all_results:
            all_results[prompt_name] = {'runs': []}

        start_from = len(all_results[prompt_name]['runs'])
        print(f"\n{'='*60}")
        print(f"  Prompt {prompt_name} — runs {start_from+1} to {N_RUNS}")
        print(f"{'='*60}")

        for i in range(start_from, N_RUNS):
            try:
                resp = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=4096,
                    temperature=0,
                    messages=[{"role": "user", "content": prompt_text}]
                )
                text = resp.content[0].text
            except Exception as e:
                text = f"ERROR: {e}"
                time.sleep(5)

            eq1, eq2 = parse_response(text)
            correct = (eq1 == True and eq2 == True)

            tag = '✓' if correct else '✗'
            eq1_str = 'YES' if eq1 else 'NO' if eq1 == False else '?'
            eq2_str = 'YES' if eq2 else 'NO' if eq2 == False else 'N/A' if eq2 is None else '?'
            print(f"  {tag} Run {i+1}/{N_RUNS}: EQ1={eq1_str} EQ2={eq2_str}")

            all_results[prompt_name]['runs'].append({
                'eq1_holds': eq1, 'eq2_fails': eq2, 'correct': correct,
                'response': text,
            })

            with open(OUTPUT_PATH, 'w') as f:
                json.dump(all_results, f, indent=2)

            time.sleep(0.5)

        runs = all_results[prompt_name]['runs']
        n_correct = sum(1 for r in runs if r['correct'])
        n_eq1 = sum(1 for r in runs if r['eq1_holds'] == True)
        n_eq2 = sum(1 for r in runs if r['eq2_fails'] == True)
        print(f"\n  {prompt_name}: {n_correct}/{len(runs)} fully correct, "
              f"EQ1=YES: {n_eq1}/{len(runs)}, EQ2=YES: {n_eq2}/{len(runs)}")

    print(f"\n{'='*60}")
    print(f"  FINAL SUMMARY")
    print(f"{'='*60}")
    for prompt_name in PROMPTS:
        if prompt_name not in all_results:
            continue
        runs = all_results[prompt_name]['runs']
        n_correct = sum(1 for r in runs if r['correct'])
        n_eq1 = sum(1 for r in runs if r['eq1_holds'] == True)
        n_eq2 = sum(1 for r in runs if r['eq2_fails'] == True)
        print(f"  {prompt_name:15s}: {n_correct:2d}/{len(runs)} correct  "
              f"(EQ1 YES: {n_eq1:2d}/{len(runs)}, EQ2 YES: {n_eq2:2d}/{len(runs)})")


if __name__ == '__main__':
    main()
