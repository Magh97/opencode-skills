#!/usr/bin/env python3
"""
run-all.py -- run the three documentation checks and summarise.

Usage:
    python run-all.py <project-dir> [--strict] [--json]

Exit code 0 only when every gating check passes across all three scripts.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKS = ("check-docs.py", "check-traceability.py", "check-consistency.py")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", help="project directory")
    ap.add_argument("--strict", action="store_true",
                    help="pass --strict to check-docs (count conflicts become failures)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--verbose", action="store_true", help="show each script's full output")
    ap.add_argument("--timeout", type=int, default=600,
                    help="kill a script after N seconds (default 600)")
    args = ap.parse_args()

    results = []
    for name in CHECKS:
        cmd = [sys.executable, os.path.join(HERE, name), args.project]
        if args.strict and name == "check-docs.py":
            cmd.append("--strict")
        timed_out = False
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace",
                                  timeout=args.timeout)
            exit_code = proc.returncode
            out = proc.stdout or ""
            err = proc.stderr or ""
        except subprocess.TimeoutExpired as e:
            # A script that walks a huge tree can hang long enough to stall the
            # whole session. Kill it, report the partial output, keep going.
            exit_code = -1
            out = e.stdout or ""
            err = (e.stderr or "") + "\n[TIMED OUT after {}s]".format(args.timeout)
            timed_out = True
        tail = [l for l in out.splitlines() if l.strip()]
        if len(out) > 8000:
            out = out[:8000] + "\n... (output truncated)"
        if timed_out:
            summary = "TIMEOUT"
        elif tail:
            summary = tail[-1]
        else:
            # exit != 0 with no stdout: the failure message went to stderr
            # (e.g. "missing required file(s)"). Surface it in the summary.
            err_tail = [l for l in err.splitlines() if l.strip()]
            summary = " ".join(err_tail[-1].split()) if err_tail else "(no output)"
        results.append({
            "script": name,
            "exit": exit_code,
            "summary": summary,
            "output": out,
            "stderr": err,
        })

    failed = [r for r in results if r["exit"] != 0]

    if args.json:
        print(json.dumps({"project": os.path.abspath(args.project),
                          "results": results,
                          "failed": len(failed)}, indent=2, ensure_ascii=False))
        return 1 if failed else 0

    print(f"documentation checks  {os.path.abspath(args.project)}")
    print("-" * 62)
    for r in results:
        mark = "PASS" if r["exit"] == 0 else "FAIL"
        print(f"  [{mark}] {r['script']:26} {r['summary']}")

    if args.verbose:
        for r in results:
            print()
            print(f"===== {r['script']} =====")
            lines = r["output"].rstrip().splitlines()
            if len(lines) > 200:
                print("\n".join(lines[:200]))
                print(f"... ({len(lines) - 200} more lines)")
            else:
                print(r["output"].rstrip())
            if r["stderr"].strip():
                print("--- stderr ---")
                print(r["stderr"].rstrip())

    print("-" * 62)
    print(f"{'FAIL' if failed else 'PASS'}  {len(failed)} of {len(results)} script(s) failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
