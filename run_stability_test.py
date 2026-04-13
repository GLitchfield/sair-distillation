#!/usr/bin/env python3 -u
"""
Run the same test N times on a subset and report per-problem consistency.
Usage: python run_stability_test.py --cheatsheet FILE --subset SUBSET --runs 10 --output results/stability.json
"""
import argparse, json, subprocess, sys, time
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed

def run_single(i, args_dict):
    """Run a single iteration of the test. Designed for parallel execution."""
    run_output = f"{args_dict['output']}.run{i}.json"
    cmd = [
        sys.executable, "run_test.py",
        "--cheatsheet", args_dict['cheatsheet'],
        "--subset", args_dict['subset'],
        "--data-dir", args_dict['data_dir'],
        "--output", run_output,
        "--provider", args_dict['provider'],
        "--delay", str(args_dict['delay']),
    ]
    if args_dict.get('model'):
        cmd += ["--model", args_dict['model']]

    Path(run_output).unlink(missing_ok=True)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"WARNING: Run {i+1} exited with code {result.returncode}")

    try:
        with open(run_output) as f:
            return json.load(f)
    except Exception as e:
        print(f"WARNING: Could not load {run_output}: {e}")
        return None

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cheatsheet", required=True)
    p.add_argument("--subset", default="stability_subset")
    p.add_argument("--data-dir", default="datasets")
    p.add_argument("--runs", type=int, default=10)
    p.add_argument("--output", required=True)
    p.add_argument("--provider", default="anthropic")
    p.add_argument("--model", default=None)
    p.add_argument("--delay", type=float, default=0.5)
    p.add_argument("--workers", type=int, default=6, help="Parallel workers")
    args = p.parse_args()

    args_dict = {
        'cheatsheet': args.cheatsheet, 'subset': args.subset,
        'data_dir': args.data_dir, 'output': args.output,
        'provider': args.provider, 'model': args.model, 'delay': args.delay,
    }

    print(f"Running {args.runs} iterations with {args.workers} parallel workers...")

    all_runs = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_single, i, args_dict): i for i in range(args.runs)}
        for future in as_completed(futures):
            i = futures[future]
            data = future.result()
            if data:
                all_runs.append(data)
                correct = sum(1 for r in data.get('results', []) if r.get('correct'))
                total = len(data.get('results', []))
                print(f"  Run {i+1}/{args.runs} done: {correct}/{total} correct  ({len(all_runs)}/{args.runs} completed)")

    # Analyze consistency
    problem_verdicts = defaultdict(list)
    problem_correct = defaultdict(list)
    for run_data in all_runs:
        for r in run_data.get("results", []):
            problem_verdicts[r["id"]].append(r.get("verdict"))
            problem_correct[r["id"]].append(r.get("correct", False))

    consistency_report = []
    for pid in sorted(problem_verdicts.keys()):
        verdicts = problem_verdicts[pid]
        corrects = problem_correct[pid]
        true_count = verdicts.count("TRUE")
        false_count = verdicts.count("FALSE")
        none_count = verdicts.count(None)
        accuracy = sum(corrects) / len(corrects) if corrects else 0
        majority = "TRUE" if true_count > false_count else "FALSE"
        consistency = max(true_count, false_count) / len(verdicts)
        consistency_report.append({
            "id": pid,
            "true_count": true_count,
            "false_count": false_count,
            "none_count": none_count,
            "accuracy": accuracy,
            "majority": majority,
            "consistency": consistency,
        })

    # Summary stats
    avg_consistency = sum(r["consistency"] for r in consistency_report) / len(consistency_report) if consistency_report else 0
    avg_accuracy = sum(r["accuracy"] for r in consistency_report) / len(consistency_report) if consistency_report else 0
    perfect = sum(1 for r in consistency_report if r["consistency"] == 1.0)

    summary = {
        "n_runs": len(all_runs),
        "n_problems": len(consistency_report),
        "avg_consistency": round(avg_consistency, 3),
        "avg_accuracy": round(avg_accuracy, 3),
        "perfect_consistency": perfect,
        "perfect_pct": round(perfect / len(consistency_report) * 100, 1) if consistency_report else 0,
    }

    output = {
        "summary": summary,
        "per_problem": consistency_report,
    }

    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  STABILITY SUMMARY")
    print(f"{'='*60}")
    print(f"  Runs: {summary['n_runs']}")
    print(f"  Problems: {summary['n_problems']}")
    print(f"  Avg consistency: {summary['avg_consistency']:.1%}")
    print(f"  Avg accuracy: {summary['avg_accuracy']:.1%}")
    print(f"  Perfect consistency: {summary['perfect_consistency']}/{summary['n_problems']} ({summary['perfect_pct']}%)")
    print(f"  Output: {args.output}")

    # Show inconsistent problems
    inconsistent = [r for r in consistency_report if r["consistency"] < 1.0]
    if inconsistent:
        print(f"\n  Inconsistent problems ({len(inconsistent)}):")
        for r in sorted(inconsistent, key=lambda x: x["consistency"]):
            print(f"    {r['id']}: {r['true_count']}T/{r['false_count']}F acc={r['accuracy']:.0%} consistency={r['consistency']:.0%}")

if __name__ == "__main__":
    main()
