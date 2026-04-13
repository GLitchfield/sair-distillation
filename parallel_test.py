#!/usr/bin/env python3 -u
"""
Parallel test runner — splits dataset across N workers, merges results.
Usage: python3 parallel_test.py --cheatsheet FILE --subset hard3 --output results/out.json --workers 4
"""
import argparse, json, subprocess, sys, time
from pathlib import Path
from collections import defaultdict

def split_jsonl(data_dir, subset, n_workers):
    """Load and split problems into n_workers chunks."""
    for p in [Path(data_dir)/f"{subset}.jsonl", Path(f"{subset}.jsonl")]:
        if p.exists():
            problems = [json.loads(l) for l in open(p)]
            break
    else:
        print(f"ERROR: {subset}.jsonl not found"); sys.exit(1)
    chunk_size = (len(problems) + n_workers - 1) // n_workers
    return [problems[i:i+chunk_size] for i in range(0, len(problems), chunk_size)]

def write_chunk(problems, path):
    with open(path, 'w') as f:
        for p in problems:
            f.write(json.dumps(p) + '\n')

def merge_results(chunk_files, output_path, cheatsheet):
    """Merge chunk result JSONs into one final result file."""
    all_results = []
    for cf in chunk_files:
        if not Path(cf).exists():
            print(f"WARNING: missing chunk {cf}")
            continue
        d = json.load(open(cf))
        items = d.get('results', d)
        if isinstance(items, dict):
            items = list(items.values())
        all_results.extend(items)

    # Sort by id
    all_results.sort(key=lambda r: r.get('id',''))

    # Compute summary
    tp=fp=tn=fn=skip=0
    for r in all_results:
        v = r.get('verdict','')
        a = r.get('answer')
        if v not in ('TRUE','FALSE') or a is None: skip+=1; continue
        a_bool = a if isinstance(a,bool) else a in ('True','TRUE','1',1)
        if v=='TRUE' and a_bool: tp+=1
        elif v=='TRUE' and not a_bool: fp+=1
        elif v=='FALSE' and not a_bool: tn+=1
        elif v=='FALSE' and a_bool: fn+=1

    n = tp+fp+tn+fn
    acc = (tp+tn)/n if n else 0
    prec = tp/(tp+fp) if tp+fp else 0
    rec = tp/(tp+fn) if tp+fn else 0
    f1 = 2*prec*rec/(prec+rec) if prec+rec else 0

    summary = {"total": len(all_results), "correct": tp+tn,
               "accuracy": acc, "precision": prec, "recall": rec, "f1": f1,
               "tp": tp, "fp": fp, "tn": tn, "fn": fn, "unparsed": skip}
    out = {"summary": summary, "results": all_results,
           "metadata": {"cheatsheet": str(cheatsheet)}}
    json.dump(out, open(output_path, 'w'), indent=2)
    return summary

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cheatsheet", required=True)
    p.add_argument("--subset", default="hard3")
    p.add_argument("--output", required=True)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--delay", type=float, default=2.0)
    p.add_argument("--data-dir", default="datasets")
    p.add_argument("--provider", default="anthropic")
    p.add_argument("--model", default=None)
    args = p.parse_args()

    # Rate limit sanity: warn if too aggressive
    est_rpm = args.workers * (60 / args.delay)
    print(f"Workers: {args.workers}  Delay: {args.delay}s  Est. RPM: {est_rpm:.0f}")
    if est_rpm > 400:
        print("WARNING: estimated RPM > 400, may hit rate limits")

    # Split dataset into chunks
    chunks = split_jsonl(args.data_dir, args.subset, args.workers)
    total = sum(len(c) for c in chunks)
    print(f"Dataset: {total} problems split across {len(chunks)} workers")

    # Write chunk files
    chunk_datasets = []
    chunk_outputs = []
    for i, chunk in enumerate(chunks):
        ds_path = f"/tmp/chunk_{i}_{args.subset}.jsonl"
        out_path = str(Path(args.output).with_suffix('')) + f"_chunk{i}.json"
        write_chunk(chunk, ds_path)
        chunk_datasets.append(ds_path)
        chunk_outputs.append(out_path)
        print(f"  Chunk {i}: {len(chunk)} problems → {out_path}")

    print()
    # Launch all workers
    procs = []
    for i, (ds, out) in enumerate(zip(chunk_datasets, chunk_outputs)):
        cmd = [
            sys.executable, "-u", "run_test.py",
            "--cheatsheet", args.cheatsheet,
            "--subset", Path(ds).stem,
            "--data-dir", "/tmp",
            "--output", out,
            "--delay", str(args.delay),
            "--provider", args.provider,
        ]
        if args.model:
            cmd += ["--model", args.model]
        log_path = str(Path(args.output).with_suffix('')) + f"_chunk{i}.log"
        log_f = open(log_path, 'w')
        proc = subprocess.Popen(cmd, stdout=log_f, stderr=log_f)
        procs.append((i, proc, log_path, out))
        print(f"  Worker {i} started (PID {proc.pid}) → log: {log_path}")

    print(f"\nAll {len(procs)} workers running. Monitoring...")
    print()

    # Monitor until all done
    start = time.time()
    while True:
        time.sleep(15)
        done = [p for _,p,_,_ in procs if p.poll() is not None]
        running = [p for _,p,_,_ in procs if p.poll() is None]
        elapsed = time.time() - start
        # Count total completed problems
        completed = 0
        for i, proc, log_path, out in procs:
            try:
                d = json.load(open(out))
                items = d.get('results', d)
                completed += len(items) if isinstance(items, list) else len(items.values())
            except: pass
        pct = completed/total*100 if total else 0
        eta = (elapsed/completed*(total-completed))/60 if completed > 0 else 0
        print(f"  [{int(elapsed)}s] {completed}/{total} ({pct:.0f}%) done  "
              f"Workers: {len(running)} running, {len(done)} finished  ETA: {eta:.0f}m")
        if not running:
            break

    # Check for failures
    failed = [(i,p) for i,p,_,_ in procs if p.returncode != 0]
    if failed:
        print(f"\nWARNING: {len(failed)} worker(s) failed: {[i for i,_ in failed]}")

    # Merge
    print(f"\nMerging {len(chunk_outputs)} chunk files → {args.output}")
    summary = merge_results(chunk_outputs, args.output, args.cheatsheet)
    elapsed = time.time() - start

    print(f"\n{'='*60}")
    print(f"RESULTS ({args.subset})")
    print(f"{'='*60}")
    print(f"  Accuracy: {summary['correct']}/{summary['total']} = {summary['accuracy']*100:.1f}%")
    print(f"  TP={summary['tp']} FP={summary['fp']} FN={summary['fn']} TN={summary['tn']}"
          f"  Unparsed={summary['unparsed']}")
    print(f"  Precision: {summary['precision']*100:.1f}%  Recall: {summary['recall']*100:.1f}%")
    print(f"  F1: {summary['f1']:.3f}")
    print(f"  Total time: {elapsed/60:.1f} min")

if __name__ == '__main__':
    main()
