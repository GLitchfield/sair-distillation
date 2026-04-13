#!/usr/bin/env python3
"""
Direct provider test runner — bypasses OpenRouter for speed.
Supports DeepInfra and Novita with OpenAI-compatible APIs.
"""

import argparse
import json
import os
import sys
import time
import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from openai import OpenAI
import httpx

JUDGE_ROOT = Path(__file__).parent / "equational-theories-stage1-judge"
sys.path.insert(0, str(JUDGE_ROOT))

from judge import judge_response
from prompt import render_prompt

PROVIDERS = {
    "deepinfra": {
        "base_url": "https://api.deepinfra.com/v1/openai",
        "env_key": "DEEPINFRA_API_KEY",
        "models": {
            "gpt-oss-120b": "openai/gpt-oss-120b",
            "llama-3.3-70b": "meta-llama/Llama-3.3-70B-Instruct",
        },
    },
    "novita": {
        "base_url": "https://api.novita.ai/v3/openai",
        "env_key": "NOVITA_API_KEY",
        "models": {
            "gemma-4-31b": "google/gemma-4-31b-it",
        },
    },
    "cerebras": {
        "base_url": "https://api.cerebras.ai/v1",
        "env_key": "CEREBRAS_API_KEY",
        "models": {
            "gpt-oss-120b": "gpt-oss-120b",
        },
    },
    "google": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "env_key": "GOOGLE_API_KEY",
        "supports_seed": False,
        "models": {
            "gemma-4-31b": "models/gemma-4-31b-it",
        },
    },
    "gemini_native": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/models",
        "env_key": "GOOGLE_API_KEY",
        "native": True,
        "thinking_budget": None,
        "models": {
            "gemma-4-31b": "gemma-4-31b-it",
        },
    },
}


def call_gemini_native(base_url, model_id, prompt, api_key, max_tokens=8192, temperature=0.0,
                        thinking_budget=None, max_retries=5):
    """Call Google's native Gemini API with optional thinking budget control."""
    url = f"{base_url}/{model_id}:generateContent?key={api_key}"
    gen_config = {
        "temperature": temperature,
        "maxOutputTokens": max_tokens,
    }
    if thinking_budget is not None:
        gen_config["thinkingConfig"] = {"thinkingBudget": thinking_budget}
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": gen_config,
    }
    delay = 2
    for attempt in range(max_retries + 1):
        try:
            resp = httpx.post(url, json=body, timeout=1200.0)
            if resp.status_code == 429 and attempt < max_retries:
                ts = datetime.datetime.now().strftime("%H:%M:%S")
                print(f"    {ts} [retry {attempt+1}/{max_retries} in {delay}s]: rate limited")
                time.sleep(delay)
                delay = min(delay * 2, 60)
                continue
            if resp.status_code != 200:
                raise Exception(f"HTTP {resp.status_code}: {resp.text[:300]}")
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise Exception(f"No candidates in response: {data}")
            cand = candidates[0]
            finish = cand.get("finishReason", "").lower()
            # Normalize finish reason to match OpenAI style
            if finish == "stop":
                finish = "stop"
            elif finish == "max_tokens":
                finish = "length"
            parts = cand.get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts if "text" in p)
            usage = data.get("usageMetadata", {})
            tokens_in = usage.get("promptTokenCount")
            tokens_out = usage.get("candidatesTokenCount")
            reasoning_tokens = usage.get("thoughtsTokenCount")
            return text, finish, tokens_in, tokens_out, reasoning_tokens
        except httpx.RequestError as e:
            if attempt < max_retries:
                ts = datetime.datetime.now().strftime("%H:%M:%S")
                print(f"    {ts} [retry {attempt+1}/{max_retries} in {delay}s]: {e}")
                time.sleep(delay)
                delay = min(delay * 2, 60)
                continue
            raise
    raise Exception("All retries exhausted")


def call_model(client, model_id, prompt, max_tokens=8192, temperature=0.0, max_retries=5, use_seed=True):
    """Call model with retry on rate limits."""
    delay = 2
    for attempt in range(max_retries + 1):
        try:
            kwargs = {
                "model": model_id,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            if use_seed:
                kwargs["seed"] = 0
            resp = client.chat.completions.create(**kwargs)
            text = resp.choices[0].message.content or ""
            finish = resp.choices[0].finish_reason
            tokens_in = resp.usage.prompt_tokens if resp.usage else None
            tokens_out = resp.usage.completion_tokens if resp.usage else None
            # Try to extract reasoning tokens if available
            reasoning_tokens = None
            try:
                details = getattr(resp.usage, 'completion_tokens_details', None)
                if details:
                    reasoning_tokens = getattr(details, 'reasoning_tokens', None)
            except Exception:
                pass
            return text, finish, tokens_in, tokens_out, reasoning_tokens
        except Exception as e:
            err = str(e)
            if "429" in err or "rate" in err.lower() or "limit" in err.lower():
                if attempt < max_retries:
                    ts = datetime.datetime.now().strftime("%H:%M:%S")
                    print(f"    {ts} [retry {attempt+1}/{max_retries} in {delay}s]: rate limited")
                    time.sleep(delay)
                    delay = min(delay * 2, 60)
                    continue
            raise
    raise Exception("All retries exhausted")


def run_test(provider_name, model_alias, api_key, cheatsheet_path, problems_path, output_path,
             limit=None, delay=1.0, max_tokens=8192, parallel=1, temperature=0.0):
    provider = PROVIDERS[provider_name]
    model_id = provider["models"][model_alias]
    use_seed = provider.get("supports_seed", True)
    is_native = provider.get("native", False)
    thinking_budget = provider.get("thinking_budget", 0)
    client = None if is_native else OpenAI(api_key=api_key, base_url=provider["base_url"], timeout=1200.0)

    template = Path(cheatsheet_path).read_text(encoding="utf-8")
    with open(problems_path) as f:
        problems = [json.loads(line) for line in f if line.strip()]
    if limit:
        problems = problems[:limit]

    # Resume support
    results = []
    completed_ids = set()
    if output_path and Path(output_path).exists():
        with open(output_path) as f:
            for line in f:
                r = json.loads(line)
                if r.get("problem_id") and "correct" in r:
                    completed_ids.add(r["problem_id"])
                    results.append(r)
        if completed_ids:
            print(f"  Resuming: {len(completed_ids)} already done")

    tp = fp = fn = tn = unparsed = errors = 0
    for r in results:
        if r.get("correct") is True:
            tp += 1 if r["expected_answer"] else 0
            tn += 0 if r["expected_answer"] else 1
        elif r.get("correct") is False:
            fn += 1 if r["expected_answer"] else 0
            fp += 0 if r["expected_answer"] else 1
        elif r.get("correct") is None:
            unparsed += 1

    print(f"Model: {model_alias} ({model_id}) on {provider_name}")
    print(f"Cheatsheet: {cheatsheet_path} ({Path(cheatsheet_path).stat().st_size} bytes)")
    print(f"Problems: {len(problems)}, delay: {delay}s, parallel: {parallel}")
    print()

    # Thread-safe lock for results list and counters
    lock = threading.Lock()

    def process_problem(prob):
        nonlocal tp, fp, fn, tn, unparsed, errors
        pid = prob["id"]
        prompt_text = render_prompt(template, prob["equation1"], prob["equation2"])
        ts = datetime.datetime.now().strftime("%H:%M:%S")

        try:
            if is_native:
                text, finish, tok_in, tok_out, reasoning_tok = call_gemini_native(
                    provider["base_url"], model_id, prompt_text, api_key,
                    max_tokens=max_tokens, temperature=temperature, thinking_budget=thinking_budget
                )
            else:
                text, finish, tok_in, tok_out, reasoning_tok = call_model(
                    client, model_id, prompt_text, max_tokens=max_tokens, temperature=temperature, use_seed=use_seed
                )
            correct, reason = judge_response(text, expected_answer=prob["answer"])

            result = {
                "model": model_alias,
                "problem_id": pid,
                "expected_answer": prob["answer"],
                "correct": correct,
                "reason": reason,
                "finish_reason": finish,
                "tokens_in": tok_in,
                "tokens_out": tok_out,
                "reasoning_tokens": reasoning_tok,
                "response": text,
            }

            with lock:
                if correct is True:
                    if prob["answer"]:
                        tp += 1
                    else:
                        tn += 1
                    tag = "✓"
                elif correct is False:
                    if prob["answer"]:
                        fn += 1
                    else:
                        fp += 1
                    tag = "✗"
                else:
                    unparsed += 1
                    tag = "?"

                results.append(result)
                total_done = tp + fp + fn + tn + unparsed
                if output_path:
                    with open(output_path, "w") as f:
                        for r in results:
                            f.write(json.dumps(r) + "\n")

            exp = "TRUE" if prob["answer"] else "FALSE"
            answered = reason.split()[1] if len(reason.split()) > 1 else "?"
            rt_str = f" rtok={reasoning_tok}" if reasoning_tok is not None else ""
            print(f"  {ts} {tag} [{pid}] got={answered} exp={exp} ({total_done}/{len(problems)}) tok={tok_out}{rt_str}")

        except Exception as e:
            result = {
                "model": model_alias,
                "problem_id": pid,
                "error": type(e).__name__,
                "message": str(e)[:200],
            }
            with lock:
                errors += 1
                results.append(result)
                if output_path:
                    with open(output_path, "w") as f:
                        for r in results:
                            f.write(json.dumps(r) + "\n")
            print(f"  {ts} ERROR [{pid}]: {str(e)[:100]}")

    # Filter out already-completed problems
    pending = [prob for prob in problems if prob["id"] not in completed_ids]

    if parallel <= 1:
        for prob in pending:
            process_problem(prob)
            time.sleep(delay)
    else:
        with ThreadPoolExecutor(max_workers=parallel) as pool:
            futures = [pool.submit(process_problem, prob) for prob in pending]
            for future in as_completed(futures):
                future.result()  # raise any exceptions

    total = tp + fp + fn + tn + unparsed
    acc = (tp + tn) / total if total else 0
    prec = tp / (tp + fp) if tp + fp else 0
    rec = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0
    print(f"\n{'='*60}")
    print(f"  {model_alias}: {tp+tn}/{total} ({acc:.1%})")
    print(f"  TP={tp} FP={fp} FN={fn} TN={tn} unparsed={unparsed} errors={errors}")
    print(f"  Precision={prec:.1%} Recall={rec:.1%} F1={f1:.3f}")
    print(f"{'='*60}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--provider", choices=list(PROVIDERS.keys()), required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--api-key", default=None)
    p.add_argument("--cheatsheet", required=True)
    p.add_argument("--problems", default="datasets/hard3_100.jsonl")
    p.add_argument("--output", default=None)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--delay", type=float, default=1.0)
    p.add_argument("--max-tokens", type=int, default=8192)
    p.add_argument("--parallel", type=int, default=1)
    p.add_argument("--temperature", type=float, default=0.0)
    args = p.parse_args()

    api_key = args.api_key or os.environ.get(PROVIDERS[args.provider]["env_key"])
    if not api_key:
        print(f"Set {PROVIDERS[args.provider]['env_key']} or use --api-key")
        sys.exit(1)

    run_test(args.provider, args.model, api_key, args.cheatsheet, args.problems,
             args.output, args.limit, args.delay, args.max_tokens, args.parallel, args.temperature)


if __name__ == "__main__":
    main()
