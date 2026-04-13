#!/usr/bin/env python3
"""
Watch active test runs and notify when each one completes.
Usage: python3 watch_runs.py [pid1 pid2 ...]
       python3 watch_runs.py  # auto-detects run_test / run_consistency processes
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


def notify(title, message):
    """Send a desktop/terminal notification."""
    # Bell + prominent print (always works)
    print(f"\a\n{'='*60}")
    print(f"  DONE: {title}")
    print(f"  {message}")
    print(f"{'='*60}\n", flush=True)

    # Try WSL2 Windows notification via PowerShell (silent fail)
    try:
        ps_cmd = (
            f"[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, "
            f"ContentType=WindowsRuntime] | Out-Null; "
            f"$xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent("
            f"[Windows.UI.Notifications.ToastTemplateType]::ToastText02); "
            f"$xml.GetElementsByTagName('text')[0].InnerText = '{title}'; "
            f"$xml.GetElementsByTagName('text')[1].InnerText = '{message}'; "
            f"$toast = [Windows.UI.Notifications.ToastNotification]::new($xml); "
            f"[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Claude Code').Show($toast)"
        )
        subprocess.run(
            ["powershell.exe", "-Command", ps_cmd],
            capture_output=True, timeout=5
        )
    except Exception:
        pass

    # Try notify-send (native Linux desktop)
    try:
        subprocess.run(
            ["notify-send", title, message, "--urgency=normal"],
            capture_output=True, timeout=5
        )
    except Exception:
        pass


def pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists but no permission


def find_log_for_pid(pid):
    """Try to find the log file from /proc/pid/fd (stdout redirect)."""
    try:
        fd_dir = Path(f"/proc/{pid}/fd")
        for fd in fd_dir.iterdir():
            target = os.readlink(str(fd))
            if target.endswith(".log") and "distillation" in target:
                return target
    except Exception:
        pass
    return None


def find_output_for_pid(pid):
    """Extract --output arg from process cmdline."""
    try:
        cmdline = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\x00")
        args = [a.decode() for a in cmdline]
        for i, a in enumerate(args):
            if a == "--output" and i + 1 < len(args):
                return args[i + 1]
    except Exception:
        pass
    return None


def find_test_processes():
    """Find all running run_test / run_consistency processes."""
    result = subprocess.run(
        ["ps", "aux"], capture_output=True, text=True
    )
    procs = []
    for line in result.stdout.splitlines():
        if re.search(r"python.*run_(test|consistency|test_repeat)", line) and "grep" not in line:
            parts = line.split()
            try:
                pid = int(parts[1])
                procs.append(pid)
            except (IndexError, ValueError):
                pass
    return procs


def extract_summary(json_path):
    """Read final summary from a results JSON file."""
    try:
        data = json.loads(Path(json_path).read_text())
        s = data.get("summary", {})
        f1 = s.get("f1", 0)
        acc = s.get("accuracy", 0)
        total = s.get("total", 0)
        correct = s.get("correct", 0)
        tp, fp, fn, tn = s.get("tp",0), s.get("fp",0), s.get("fn",0), s.get("tn",0)
        return (f"F1={f1:.3f} Acc={acc:.1%} ({correct}/{total}) "
                f"TP={tp} FP={fp} FN={fn} TN={tn}")
    except Exception:
        return "(could not read results)"


def extract_log_summary(log_path):
    """Extract RESULTS block from log."""
    try:
        text = Path(log_path).read_text()
        # Find the last RESULTS block
        m = re.findall(
            r"={10,}\nRESULTS.*?\n={10,}\n(.*?)\n\n",
            text, re.DOTALL
        )
        if m:
            return m[-1].strip()
    except Exception:
        pass
    return None


def watch(pids):
    watched = {}
    for pid in pids:
        log = find_log_for_pid(pid)
        out = find_output_for_pid(pid)
        label = Path(out).stem if out else f"pid-{pid}"
        watched[pid] = {"label": label, "log": log, "output": out, "done": False}
        print(f"  Watching PID {pid}: {label}", flush=True)

    print(f"\nMonitoring {len(watched)} run(s). Press Ctrl+C to stop.\n", flush=True)

    while True:
        all_done = True
        for pid, info in watched.items():
            if info["done"]:
                continue
            if not pid_alive(pid):
                info["done"] = True
                label = info["label"]
                summary = ""
                if info["output"]:
                    summary = extract_summary(info["output"])
                if not summary and info["log"]:
                    summary = extract_log_summary(info["log"]) or "(no summary found)"
                notify(f"Run complete: {label}", summary)
            else:
                all_done = False

        if all_done:
            print("All watched runs have completed.", flush=True)
            break

        time.sleep(15)


def main():
    if len(sys.argv) > 1:
        pids = [int(a) for a in sys.argv[1:]]
    else:
        pids = find_test_processes()

    if not pids:
        print("No running test processes found.")
        return

    watch(pids)


if __name__ == "__main__":
    main()
