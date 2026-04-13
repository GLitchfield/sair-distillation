#!/usr/bin/env python3
"""
Test runner using the official judge harness.
Runs models sequentially with configurable delay between calls.
"""

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

import httpx

JUDGE_ROOT = Path(__file__).parent / "equational-theories-stage1-judge"
sys.path.insert(0, str(JUDGE_ROOT))

from judge import judge_response
from llm import call_llm, LlmError
from models import load_models, resolve
from prompt import render_prompt


def load_problems(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


async def run_model(alias, entry, api_key, prompt_template, problems, delay, output_path, max_tokens_override=None):
    """Run one model on all problems, sequentially with delay."""
    provider_name, provider_config, kwargs = resolve(entry, api_keys=[api_key])
    if max_tokens_override:
        kwargs.max_tokens = min(max_tokens_override, kwargs.max_tokens or max_tokens_override)

    results = []
    # Resume support
    completed_ids = set()
    if output_path and Path(output_path).exists():
        try:
            with open(output_path) as f:
                for line in f:
                    r = json.loads(line)
                    if r.get("problem_id") and "correct" in r:
                        completed_ids.add(r["problem_id"])
                        results.append(r)
            if completed_ids:
                print(f"  Resuming: {len(completed_ids)} already done")
        except Exception:
            pass

    tp = fp = fn = tn = unparsed = errors = 0
    # Count existing results
    for r in results:
        if r.get("correct") is True:
            if r["expected_answer"]:
                tp += 1
            else:
                tn += 1
        elif r.get("correct") is False:
            if r["expected_answer"]:
                fn += 1
            else:
                fp += 1
        elif r.get("correct") is None:
            unparsed += 1

    async with httpx.AsyncClient(timeout=300) as client:
        for i, problem in enumerate(problems):
            pid = problem["id"]
            if pid in completed_ids:
                continue

            prompt_text = render_prompt(
                prompt_template, problem["equation1"], problem["equation2"]
            )

            try:
                response = await call_llm(
                    client,
                    provider_name=provider_name,
                    provider_config=provider_config,
                    model_id=entry.model_id,
                    prompt=prompt_text,
                    kwargs=kwargs,
                )
                correct, reason = judge_response(response.text, expected_answer=problem["answer"])

                result = {
                    "model": alias,
                    "problem_id": pid,
                    "expected_answer": problem["answer"],
                    "correct": correct,
                    "reason": reason,
                    "finish_reason": response.finish_reason,
                    "tokens_in": response.tokens_in,
                    "tokens_out": response.tokens_out,
                    "response": response.text,
                }

                if correct is True:
                    if problem["answer"]:
                        tp += 1
                    else:
                        tn += 1
                    tag = "✓"
                elif correct is False:
                    if problem["answer"]:
                        fn += 1
                    else:
                        fp += 1
                    tag = "✗"
                else:
                    unparsed += 1
                    tag = "?"

                done = len(completed_ids) + i + 1 - len(completed_ids)
                total_done = tp + fp + fn + tn + unparsed
                exp = "TRUE" if problem["answer"] else "FALSE"
                verdict = "TRUE" if correct is not None and ((correct and problem["answer"]) or (not correct and not problem["answer"])) else "FALSE" if correct is not None else "NONE"
                # Simpler: extract from reason
                answered = reason.split()[1] if len(reason.split()) > 1 else "?"
                print(f"  {tag} [{pid}] got={answered} exp={exp} ({total_done}/{len(problems)})")

            except LlmError as exc:
                result = {
                    "model": alias,
                    "problem_id": pid,
                    "error": type(exc).__name__,
                    "message": str(exc)[:200],
                }
                errors += 1
                print(f"  ERROR [{pid}]: {str(exc)[:100]}")

            results.append(result)

            # Save incrementally
            if output_path:
                with open(output_path, "w") as f:
                    for r in results:
                        f.write(json.dumps(r) + "\n")

            # Delay between calls
            await asyncio.sleep(delay)

    total = tp + fp + fn + tn + unparsed
    acc = (tp + tn) / total if total else 0
    print(f"\n  {alias}: {tp+tn}/{total} ({acc:.1%}) TP={tp} FP={fp} FN={fn} TN={tn} unparsed={unparsed} errors={errors}")
    return results


async def main_async(args):
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Set OPENROUTER_API_KEY")
        return

    prompt_template = Path(args.cheatsheet).read_text(encoding="utf-8")
    problems = load_problems(args.problems)
    if args.limit:
        problems = problems[:args.limit]

    model_file = JUDGE_ROOT / "evaluation_models.json"
    configs = load_models(model_file)

    models = args.models or list(configs)

    print(f"Cheatsheet: {args.cheatsheet} ({len(prompt_template)} bytes)")
    print(f"Problems: {len(problems)}")
    print(f"Models: {models}")
    print(f"Delay: {args.delay}s between calls")
    print()

    for alias in models:
        if alias not in configs:
            print(f"Unknown model: {alias}")
            continue

        output = f"{args.output_prefix}_{alias}.jsonl" if args.output_prefix else None
        print(f"=== {alias} ===")
        await run_model(alias, configs[alias], api_key, prompt_template, problems, args.delay, output)
        print()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cheatsheet", required=True)
    p.add_argument("--problems", default="datasets/hard3_100.jsonl")
    p.add_argument("--models", nargs="*")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--delay", type=float, default=3.0)
    p.add_argument("--output-prefix", default=None)
    args = p.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
