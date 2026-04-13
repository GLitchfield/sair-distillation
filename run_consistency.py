#!/usr/bin/env python3 -u
"""
SAIR Math Distillation Challenge - Test Harness
================================================
Tests a cheat sheet against the equational theories dataset.
Supports Anthropic (Claude) and Google (Gemini) APIs.

Setup:
  pip install anthropic

Usage:
  export ANTHROPIC_API_KEY=your_key
  python run_test.py --limit 20                          # quick test with cheatsheet
  python run_test.py --limit 20 --no-cheatsheet          # baseline
  python run_test.py --subset normal                     # full normal set
  python run_test.py --subset hard --output hard_v1.json # hard set with saved results
  python run_test.py --provider gemini --model gemini-2.0-flash-lite  # use gemini instead
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

PROMPT_TEMPLATE_LEGACY = """You are a mathematician specializing in equational theories of magmas.
Your task is to determine whether Equation 1 ({equation1}) implies Equation 2 ({equation2}) over all magmas.
{cheatsheet}
Output format (use exact headers without any additional text or formatting):
VERDICT: must be exactly TRUE or FALSE (in the same line).
REASONING: must be non-empty.
PROOF: required if VERDICT is TRUE, empty otherwise.
COUNTEREXAMPLE: required if VERDICT is FALSE, empty otherwise."""


def build_prompt(equation1, equation2, cheatsheet):
    if '{{ equation1 }}' in cheatsheet or '{{equation1}}' in cheatsheet:
        from jinja2 import Template
        tpl = Template(cheatsheet)
        return tpl.render(equation1=equation1, equation2=equation2)
    cs_block = cheatsheet.strip() + "\n" if cheatsheet.strip() else ""
    return PROMPT_TEMPLATE_LEGACY.format(equation1=equation1, equation2=equation2, cheatsheet=cs_block)


def parse_verdict(response_text):
    cleaned = re.sub(r'\*+', '', response_text)
    m = re.search(r"VERDICT:\s*(TRUE|FALSE)", cleaned, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    for line in response_text.strip().split("\n")[:5]:
        u = line.strip().upper()
        if u in ("TRUE", "FALSE"):
            return u
        if u.startswith("VERDICT"):
            if "TRUE" in u: return "TRUE"
            if "FALSE" in u: return "FALSE"
    return None


def call_anthropic(prompt, model_name, api_key):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key, timeout=120.0)
    message = client.messages.create(
        model=model_name, max_tokens=4096, temperature=0.0,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def call_gemini(prompt, model_name, api_key):
    from google import genai
    from google.genai import types
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=120_000),  # milliseconds
    )
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,
            max_output_tokens=4096,
        ),
    )
    # Safety filter check: .text raises if content was blocked
    if not response.candidates:
        raise ValueError("Gemini returned no candidates (likely safety filter)")
    return response.text


def call_openai_compat(prompt, model_name, api_key, base_url):
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=120.0)
    resp = client.chat.completions.create(
        model=model_name, max_tokens=4096, temperature=0.0,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


def call_model(prompt, model_name, api_key, provider):
    if provider == "anthropic":
        return call_anthropic(prompt, model_name, api_key)
    elif provider == "gemini":
        return call_gemini(prompt, model_name, api_key)
    elif provider == "fireworks":
        return call_openai_compat(prompt, model_name, api_key, "https://api.fireworks.ai/inference/v1")
    raise ValueError(f"Unknown provider: {provider}")


def call_model_with_retry(prompt, model_name, api_key, provider, max_retries=3):
    """Call model with exponential backoff on transient errors.
    Uses longer initial delay for server-overload errors (5xx, 503, 504)."""
    delay = 2
    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            return call_model(prompt, model_name, api_key, provider)
        except Exception as e:
            last_exc = e
            if attempt < max_retries:
                ts = datetime.datetime.now().strftime("%H:%M:%S")
                # Server overload errors get a much longer initial backoff
                err_str = str(e)
                if any(code in err_str for code in ("503", "504", "429", "overload", "Deadline", "high demand")):
                    delay = max(delay, 30)
                print(f"    {ts} [retry {attempt+1}/{max_retries} in {delay}s]: {e}")
                time.sleep(delay)
                delay *= 2
    raise last_exc


def load_problems(data_path, subset):
    for p in [Path(data_path) / f"{subset}.jsonl", Path(f"{subset}.jsonl")]:
        if p.exists():
            return [json.loads(line) for line in open(p)]
    print(f"ERROR: {subset}.jsonl not found. Download from:")
    print(f"  https://huggingface.co/datasets/SAIRfoundation/equational-theories-selected-problems/resolve/main/data/{subset}.jsonl")
    sys.exit(1)


def compute_summary(results):
    correct = total = tp = fp = fn = tn = unparsed = 0
    for r in results:
        if r.get("error"):
            continue
        answer = r["answer"]
        verdict = r["verdict"]
        total += 1
        if verdict is None:
            unparsed += 1
        else:
            predicted = verdict == "TRUE"
            is_correct = predicted == answer
            if is_correct: correct += 1
            if predicted and answer:       tp += 1
            elif predicted and not answer: fp += 1
            elif not predicted and answer: fn += 1
            else:                          tn += 1
    s = {
        "total": total, "correct": correct,
        "accuracy": correct / total if total else 0,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn, "unparsed": unparsed,
        "precision": tp / (tp + fp) if tp + fp else 0,
        "recall": tp / (tp + fn) if tp + fn else 0,
    }
    if tp + fp + fn: s["f1"] = 2 * tp / (2 * tp + fp + fn)
    return s


def make_metadata(model_name, provider, cheatsheet):
    return {
        "model": model_name,
        "provider": provider,
        "cheatsheet_hash": hashlib.md5(cheatsheet.encode()).hexdigest()[:12],
        "timestamp": datetime.datetime.now().isoformat(),
    }


def save_progress(results, save_path, metadata=None):
    """Atomic save: write to .tmp then rename so a crash never corrupts the output file."""
    summary = compute_summary(results)
    payload = {"summary": summary, "results": results}
    if metadata:
        payload["metadata"] = metadata
    tmp = save_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp, save_path)  # atomic on Linux/Mac


N_VOTES = 5  # number of samples for self-consistency majority vote


def run_evaluation(problems, cheatsheet, model_name, api_key, provider, delay=0.5, save_path=None):
    metadata = make_metadata(model_name, provider, cheatsheet)
    metadata["n_votes"] = N_VOTES

    # Warn if no output file and run is large
    if not save_path and len(problems) > 50:
        print(f"WARNING: No --output file specified. Results for {len(problems)} problems will not be saved.")

    # Resume: load any already-completed results
    completed_ids = set()
    results = []
    if save_path and Path(save_path).exists():
        try:
            existing = json.load(open(save_path))
            prior_results = existing.get("results", [])

            # Check for cheatsheet/model mismatch
            prior_meta = existing.get("metadata", {})
            if prior_meta:
                mismatches = []
                if prior_meta.get("model") != model_name:
                    mismatches.append(f"model: {prior_meta['model']} → {model_name}")
                if prior_meta.get("cheatsheet_hash") != metadata["cheatsheet_hash"]:
                    mismatches.append(f"cheatsheet hash: {prior_meta['cheatsheet_hash']} → {metadata['cheatsheet_hash']}")
                if mismatches:
                    print(f"WARNING: Resuming file has different settings: {', '.join(mismatches)}")
                    print(f"  Results will be mixed. Use a different --output file for a clean run.")

            # Only skip successful completions; retry errors
            completed_ids = {r["id"] for r in prior_results if not r.get("error")}
            results = [r for r in prior_results if not r.get("error")]
            n_errors = len(prior_results) - len(results)
            if completed_ids:
                print(f"Resuming: {len(completed_ids)} completed, skipping. {n_errors} errored problems will be retried.")
        except json.JSONDecodeError as e:
            print(f"WARNING: Output file is corrupt ({e}). Starting fresh (old file backed up to {save_path}.bak).")
            os.rename(save_path, save_path + ".bak")
        except Exception as e:
            print(f"WARNING: Could not load existing results ({e}). Starting fresh.")

    start_time = time.time()
    n_done_at_start = len(completed_ids)

    for i, prob in enumerate(problems):
        eq1, eq2, answer = prob["equation1"], prob["equation2"], prob["answer"]
        pid = prob.get("id", f"p{i}")

        if pid in completed_ids:
            continue

        prompt = build_prompt(eq1, eq2, cheatsheet)
        ts = datetime.datetime.now().strftime("%H:%M:%S")

        # Collect N_VOTES independent samples
        votes = []
        responses = []
        for v in range(N_VOTES):
            try:
                resp = call_model_with_retry(prompt, model_name, api_key, provider)
                verd = parse_verdict(resp)
                votes.append(verd)
                responses.append(resp)
            except Exception as e:
                votes.append(None)
                responses.append(str(e))
            time.sleep(delay)

        # Majority vote: TRUE wins if >=ceil(N/2) votes are TRUE
        true_count = votes.count("TRUE")
        false_count = votes.count("FALSE")
        if true_count > false_count:
            verdict = "TRUE"
        elif false_count > true_count:
            verdict = "FALSE"
        else:
            verdict = "FALSE"  # tie-break to FALSE per cheatsheet guidance

        predicted = verdict == "TRUE"
        is_correct = predicted == answer
        exp = "TRUE" if answer else "FALSE"

        done = len([r for r in results if not r.get("error")]) + 1
        elapsed = time.time() - start_time
        n_this_run = done - n_done_at_start
        if n_this_run > 1:
            rate = elapsed / n_this_run
            remaining = (len(problems) - done) * rate
            eta = f" ETA={remaining/60:.0f}m"
        else:
            eta = ""

        tag = "✓" if is_correct else "✗"
        print(f"  {ts} [{pid}] {tag} got={verdict} ({true_count}T/{false_count}F) exp={exp}  ({done}/{len(problems)}){eta}")

        results.append({
            "id": pid, "equation1": eq1, "equation2": eq2,
            "answer": answer, "verdict": verdict, "correct": is_correct,
            "votes": votes, "true_count": true_count, "false_count": false_count,
        })

        if save_path:
            save_progress(results, save_path, metadata)

    summary = compute_summary(results)
    if save_path:
        save_progress(results, save_path, metadata)
        print(f"\nSaved to {save_path}")
    return summary


def print_summary(s, label=""):
    print(f"\n{'='*60}")
    print(f"RESULTS {label}")
    print(f"{'='*60}")
    print(f"  Accuracy: {s['correct']}/{s['total']} = {s['accuracy']:.1%}")
    print(f"  TP={s['tp']} FP={s['fp']} FN={s['fn']} TN={s['tn']}  Unparsed={s['unparsed']}")
    if s.get('precision'): print(f"  Precision: {s['precision']:.1%}  Recall: {s['recall']:.1%}")
    if s.get('f1'): print(f"  F1: {s['f1']:.3f}")
    print()


def latest_cheatsheet():
    cs_dir = Path("cheatsheets")
    files = list(cs_dir.glob("cheatsheet_v*.txt"))
    if not files:
        return None
    # Natural sort by version number so v10 > v9
    def version_num(p):
        m = re.search(r'v(\d+)', p.stem)
        return int(m.group(1)) if m else 0
    return str(sorted(files, key=version_num)[-1])


def main():
    p = argparse.ArgumentParser(description="Test cheat sheet on equational theories problems")
    p.add_argument("--api-key", default=None)
    p.add_argument("--provider", choices=["anthropic", "gemini", "fireworks"], default="anthropic")
    p.add_argument("--model", default=None)
    p.add_argument("--cheatsheet", default=None)
    p.add_argument("--subset", default="normal")
    p.add_argument("--data-dir", default="datasets")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--delay", type=float, default=0.5)
    p.add_argument("--output", default=None)
    p.add_argument("--no-cheatsheet", action="store_true")
    args = p.parse_args()

    defaults = {"anthropic": ("claude-haiku-4-5-20251001", "ANTHROPIC_API_KEY"),
                "gemini": ("gemini-3.1-flash-lite-preview", "GEMINI_API_KEY"),
                "fireworks": ("accounts/fireworks/models/llama-v3p3-70b-instruct", "FIREWORKS_API_KEY")}
    default_model, env_key = defaults[args.provider]
    if not args.model: args.model = default_model
    if not args.api_key: args.api_key = os.environ.get(env_key)
    if not args.api_key:
        print(f"ERROR: No API key. Use --api-key or set {env_key}"); sys.exit(1)

    if args.no_cheatsheet:
        cheatsheet = ""
        print("Mode: BASELINE (no cheat sheet)")
    else:
        cs_path = args.cheatsheet or latest_cheatsheet()
        if not cs_path:
            print("ERROR: No cheatsheet found in cheatsheets/ and --cheatsheet not specified"); sys.exit(1)
        cs = Path(cs_path)
        if not cs.exists(): print(f"ERROR: {cs} not found"); sys.exit(1)
        cheatsheet = cs.read_text()
        print(f"Cheat sheet: {cs} ({len(cheatsheet)} bytes)")

    print(f"Provider: {args.provider}  Model: {args.model}  Subset: {args.subset}")
    if args.limit: print(f"Limit: {args.limit}")

    for subset in (["normal", "hard"] if args.subset == "both" else [args.subset]):
        problems = load_problems(args.data_dir, subset)
        if args.limit: problems = problems[:args.limit]
        print(f"\n--- {len(problems)} {subset} problems ---")
        sp = args.output
        if sp and args.subset == "both":
            b, e = os.path.splitext(sp); sp = f"{b}_{subset}{e}"
        summary = run_evaluation(problems, cheatsheet, args.model, args.api_key,
                                 args.provider, args.delay, sp)
        print_summary(summary, f"({subset})")


if __name__ == "__main__":
    main()
