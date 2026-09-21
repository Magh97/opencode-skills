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
    args = ap.parse_args()

    results = []
    for name in CHECKS:
        cmd = [sys.executable, os.path.join(HERE, name), args.project]
        if args.strict and name == "check-docs.py":
            cmd.append("--strict")
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        tail = [l for l in (proc.stdout or "").splitlines() if l.strip()]
        results.append({
            "script": name,
            "exit": proc.returncode,
            "summary": tail[-1] if tail else "(no output)",
            "output": proc.stdout or "",
            "stderr": proc.stderr or "",
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
            print(r["output"].rstrip())
            if r["stderr"].strip():
                print("--- stderr ---")
                print(r["stderr"].rstrip())

    print("-" * 62)
    print(f"{'FAIL' if failed else 'PASS'}  {len(failed)} of {len(results)} script(s) failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
