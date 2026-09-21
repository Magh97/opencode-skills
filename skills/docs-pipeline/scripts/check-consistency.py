#!/usr/bin/env python3
"""
check-consistency.py -- cross-document integrity for a documentation set.

Checks:
  1. Every ADR-NNNN referenced anywhere exists as a file
  2. Every requirement ID referenced outside REQUIREMENTS.md is defined there
  3. Every NFR ID referenced outside NFR.md is defined there
  4. Every relative path written in backticks in prose resolves
  5. Tables that appear in more than one document (redundancy signal)

A document set can be complete and still contradict itself. This is the check
that catches it.

Usage:
    python check-consistency.py <project-dir> [--json]

Exit code 0 when every check passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from urllib.parse import unquote

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REQ_ID = re.compile(r"\b([A-Z][A-Z0-9]{1,7}-\d{1,3})\b(?!\.\d)")
NFR_ID = re.compile(r"\b(NFR-\d+\.\d+)\b")
ADR_REF = re.compile(r"\bADR-(\d{3,4})\b")

# ID namespaces that are not functional requirements.
NOT_REQUIREMENTS = {"NFR", "RN", "ADR", "T", "G", "S", "P"}

# Backticked relative paths that look like documents.
PATH_IN_BACKTICKS = re.compile(r"`([A-Za-z0-9_./-]+\.(?:md|yaml|yml|json))`")

# Input and narrative documents. They are not part of the live set:
#   index.md        the raw idea document the project was generated from
#   ACLARACIONES.md the decision log, which narrates past states on purpose
#   CHANGELOG.md    the release history
#   STATUS.md       the status report
# Referencing an ADR or an ID that no longer exists is correct behaviour in these.
SOURCE_DOCS = {"index.md", "ACLARACIONES.md", "CHANGELOG.md", "STATUS.md"}


def read(path: str) -> str:
    return open(path, encoding="utf-8", errors="replace").read()


def find_markdown(root: str) -> list[str]:
    out = []
    for dp, dn, fn in os.walk(root):
        if ".git" in dp.split(os.sep):
            continue
        for f in fn:
            if f.endswith(".md"):
                out.append(os.path.join(dp, f))
    return sorted(out)


def resolve(raw: str, base: str, root: str, docs: str, by_basename: dict[str, str]) -> str | None:
    """Documentation writes paths three ways: relative to the file, relative to
    the project root, and relative to docs/. It also writes bare filenames.
    All four are legitimate."""
    for candidate in (
        os.path.normpath(os.path.join(base, raw)),
        os.path.normpath(os.path.join(root, raw)),
        os.path.normpath(os.path.join(docs, raw)),
    ):
        if os.path.exists(candidate):
            return candidate
    return by_basename.get(os.path.basename(raw))


def live_files(root: str, files: list[str]) -> list[str]:
    """Archive is a record, not a live document. Exclude it from every check."""
    return [f for f in files
            if "archive" not in os.path.relpath(f, root).split(os.sep)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", help="project directory")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = os.path.abspath(args.project)
    if not os.path.isdir(root):
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    files = live_files(root, find_markdown(root))
    docs = os.path.join(root, "docs")

    # --- What exists ---------------------------------------------------------
    # ADRs are searched in the live folder and in the archive. An archived ADR
    # still exists; it was superseded, not deleted.
    adr_files: dict[str, str] = {}
    for sub, prefix in (("adr", "docs/adr"), (os.path.join("archive", "adr"), "docs/archive/adr")):
        d = os.path.join(docs, sub)
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            m = re.match(r"^(\d{3,4})-", f)
            if m and f.endswith(".md") and m.group(1) not in adr_files:
                adr_files[m.group(1)] = f"{prefix}/{f}"

    req_file = os.path.join(docs, "REQUIREMENTS.md")
    nfr_file = os.path.join(docs, "NFR.md")
    defined_reqs = set(re.findall(REQ_ID, read(req_file))) if os.path.exists(req_file) else set()
    defined_reqs = {r for r in defined_reqs if r.rsplit("-", 1)[0] not in NOT_REQUIREMENTS}
    defined_nfrs = set(NFR_ID.findall(read(nfr_file))) if os.path.exists(nfr_file) else set()

    # --- 1. ADR references ---------------------------------------------------
    adr_missing: list[dict] = []
    adr_seen: dict[str, set[str]] = defaultdict(set)
    for f in files:
        rel = os.path.relpath(f, root)
        if os.path.basename(f) in SOURCE_DOCS:
            continue
        for m in ADR_REF.finditer(read(f)):
            num = m.group(1)
            adr_seen[num].add(rel)
            if num not in adr_files:
                adr_missing.append({"adr": f"ADR-{num}", "referenced_in": rel})

    adr_live = {n for n, p in adr_files.items() if "archive" not in p}
    adr_orphans = sorted(adr_live - set(adr_seen))

    # --- 2 and 3. ID references ---------------------------------------------
    req_undefined: list[dict] = []
    nfr_undefined: list[dict] = []
    for f in files:
        rel = os.path.relpath(f, root)
        if os.path.basename(f) in SOURCE_DOCS:
            continue
        if os.path.basename(f) == "REQUIREMENTS.md":
            continue
        text = read(f)
        for m in REQ_ID.finditer(text):
            rid = m.group(1)
            if rid.rsplit("-", 1)[0] in NOT_REQUIREMENTS:
                continue
            if rid not in defined_reqs:
                req_undefined.append({"id": rid, "referenced_in": rel})
        if os.path.basename(f) != "NFR.md":
            for m in NFR_ID.finditer(text):
                if m.group(1) not in defined_nfrs:
                    nfr_undefined.append({"id": m.group(1), "referenced_in": rel})

    # --- 4. Backticked paths in prose ---------------------------------------
    # ADVISORY, not a gate. The documents legitimately reference artifacts that
    # do not exist yet (docker-compose.yml in v0.0) and conventions that are not
    # files (IDEAS.md). Only markdown links are a hard failure, and those are
    # checked by check-docs.py.
    by_basename: dict[str, str] = {}
    for dp, dn, fn in os.walk(root):
        if ".git" in dp.split(os.sep):
            continue
        for f in fn:
            by_basename.setdefault(f, os.path.join(dp, f))

    path_missing: list[dict] = []
    for f in files:
        if os.path.basename(f) in SOURCE_DOCS:
            continue
        base = os.path.dirname(f)
        rel = os.path.relpath(f, root)
        for m in PATH_IN_BACKTICKS.finditer(read(f)):
            raw = m.group(1)
            if raw.startswith(("http", "node_modules")):
                continue
            if resolve(raw, base, root, docs, by_basename) is None:
                path_missing.append({"file": rel, "path": raw,
                                     "kind": "doc" if raw.endswith(".md") else "artifact"})

    # --- 5. Duplicated tables ------------------------------------------------
    # agent-docs/ is a deliberate compact restatement of the main documents, so
    # duplication there is by design and is excluded.
    header_owner: dict[str, set[str]] = defaultdict(set)
    for f in files:
        rel = os.path.relpath(f, root)
        if "agent-docs" in rel.split(os.sep):
            continue
        for line in read(f).splitlines():
            if not line.startswith("|") or line.count("|") < 4:
                continue
            cells = [c.strip() for c in line.strip("|").split("|")[:3]]
            # Skip markdown separator rows: every cell is only dashes and colons.
            if all(c and set(c) <= set("-: ") for c in cells):
                continue
            key = "|".join(cells)
            if key.strip("| ") == "":
                continue
            header_owner[key].add(rel)
    duplicated = {k: sorted(v) for k, v in header_owner.items() if len(v) > 1}

    failures = (len(adr_missing) + len(req_undefined) + len(nfr_undefined))

    if args.json:
        print(json.dumps({
            "adr_files": len(adr_files),
            "adr_missing": adr_missing,
            "adr_orphans": [f"ADR-{a}" for a in adr_orphans],
            "requirements_defined": len(defined_reqs),
            "requirement_refs_undefined": req_undefined,
            "nfr_defined": len(defined_nfrs),
            "nfr_refs_undefined": nfr_undefined,
            "paths_missing": path_missing,
            "duplicated_table_headers": len(duplicated),
            "failures": failures,
        }, indent=2, ensure_ascii=False))
        return 1 if failures else 0

    def head(t: str) -> None:
        print(f"\n{t}")
        print("-" * max(20, len(t)))

    print(f"project  {root}")

    head("ADR references")
    print(f"  files present      {len(adr_files)}")
    if adr_missing:
        for a in adr_missing:
            print(f"  MISSING  {a['adr']} referenced in {a['referenced_in']}")
    else:
        print("  ok  every referenced ADR exists")
    if adr_orphans:
        print(f"  note  present but never referenced: "
              f"{', '.join('ADR-' + a for a in adr_orphans)}")

    head("Requirement ID references")
    print(f"  defined in REQUIREMENTS.md   {len(defined_reqs)}")
    if req_undefined:
        for r in req_undefined:
            print(f"  UNDEFINED  {r['id']} referenced in {r['referenced_in']}")
    else:
        print("  ok  every referenced requirement ID is defined")

    head("NFR ID references")
    print(f"  defined in NFR.md   {len(defined_nfrs)}")
    if nfr_undefined:
        for r in nfr_undefined:
            print(f"  UNDEFINED  {r['id']} referenced in {r['referenced_in']}")
    else:
        print("  ok  every referenced NFR ID is defined")

    head("Paths in prose")
    if path_missing:
        docs_missing = [p for p in path_missing if p["kind"] == "doc"]
        artifacts = [p for p in path_missing if p["kind"] == "artifact"]
        for p in docs_missing:
            print(f"  CHECK  {p['path']}  (in {p['file']})")
        for p in artifacts[:8]:
            print(f"  note   {p['path']}  (in {p['file']}) -- planned artifact?")
        if len(artifacts) > 8:
            print(f"  note   ... and {len(artifacts) - 8} more artifact references")
        print("  note: documents that do not exist yet are expected before implementation")
    else:
        print("  ok  every backticked path resolves")

    head("Duplicated tables")
    if duplicated:
        print(f"  {len(duplicated)} table header(s) appear in more than one document")
        for k, v in list(duplicated.items())[:8]:
            print(f"      {k[:56]:56} {', '.join(v)}")
        if len(duplicated) > 8:
            print(f"      ... and {len(duplicated) - 8} more")
        print("  note: a summary table in two documents is fine. It drifts when the values change.")
    else:
        print("  ok  no table appears in two documents")

    print()
    print(f"{'FAIL' if failures else 'PASS'}  {failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
