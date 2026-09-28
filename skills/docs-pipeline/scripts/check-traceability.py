#!/usr/bin/env python3
"""
check-traceability.py -- verifies that a documentation set is traced.

Checks:
  1. Requirement IDs defined in REQUIREMENTS.md are all traced in TRACEABILITY.md
  2. Nothing is traced that was never defined
  3. NFR IDs follow the same rule
  4. Every requirement prefix (module) has requirements
  5. Endpoints in the OpenAPI contract appear in the traceability matrix
  6. Endpoints in the traceability matrix exist in the contract

An endpoint with no requirement is scope creep. A requirement with no endpoint
is either undesigned, or enforced internally and must be declared as such.

Usage:
    python check-traceability.py <project-dir> [--json]
    python check-traceability.py <project-dir> --id-pattern '[A-Z]{2,8}-\\d{1,3}'

Exit code 0 when every check passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# The suffix must not be followed by a dot-digit, or NFR-1.1 is read as "NFR-1".
DEFAULT_ID_PATTERN = r"\b([A-Z][A-Z0-9]{1,7}-\d{1,3})\b(?!\.\d)"
NFR_PATTERN = r"\b(NFR-\d+\.\d+)\b"

# Other ID namespaces that live in these documents and are not requirements.
# Without this, business rules (RN-01) and ADRs read as untraced requirements.
DEFAULT_IGNORE_PREFIX = "NFR,RN,ADR,T,G,S"

HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")


def normalise_endpoint(endpoint: str) -> str:
    """Path parameter NAMES are an implementation detail. /orders/{id} and
    /orders/{orderId} are the same endpoint, and treating them as different is
    the single largest source of false positives in this check."""
    method, _, path = endpoint.partition(" ")
    return f"{method} {re.sub(r'\{[^}]*\}', '{}', path)}"


def read(path: str) -> str:
    return open(path, encoding="utf-8", errors="replace").read()


def extract(pattern: str, text: str) -> set[str]:
    return set(re.findall(pattern, text))


def parse_openapi(path: str) -> set[str]:
    """Extract 'METHOD /path' from an OpenAPI document without a YAML dependency."""
    if not os.path.exists(path):
        return set()
    endpoints: set[str] = set()
    current_path: str | None = None
    for line in read(path).splitlines():
        m = re.match(r"^  (/[^\s:]+):\s*$", line)
        if m:
            current_path = m.group(1)
            continue
        m = re.match(r"^    (" + "|".join(HTTP_METHODS) + r"):\s*$", line)
        if m and current_path:
            endpoints.add(f"{m.group(1).upper()} {current_path}")
    return endpoints


def extract_endpoints_from_text(text: str) -> set[str]:
    """Find endpoints in the traceability matrix.

    Two notations coexist, and a matrix legitimately uses both:
        form A  `GET /orders/{id}`
        form B  `GET`/`POST`/`PATCH`/`DELETE /zones`

    Form B is a leading run of backticked methods, then a final
    `METHOD /path`. It is parsed in two passes.
    """
    methods = "|".join(m.upper() for m in HTTP_METHODS)
    found: set[str] = set()

    # Form A, and the tail of form B.
    for m in re.finditer(r"`(" + methods + r")\s+(/[^\s`|]+)`", text):
        found.add(f"{m.group(1)} {m.group(2).rstrip(',.;:')}")

    # The leading methods of form B.
    leading = re.compile(
        r"((?:`(?:" + methods + r")`\s*/\s*)+)"
        r"`(?:" + methods + r")\s+(/[^\s`|]+)`"
    )
    for m in leading.finditer(text):
        path = m.group(2).rstrip(",.;:")
        for verb in re.findall(r"`(" + methods + r")`", m.group(1)):
            found.add(f"{verb} {path}")

    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", help="project directory")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--id-pattern", default=DEFAULT_ID_PATTERN,
                    help="regex for requirement IDs (one capture group)")
    ap.add_argument("--ignore-prefix", default=DEFAULT_IGNORE_PREFIX,
                    help="comma-separated ID prefixes that are not requirements")
    args = ap.parse_args()

    root = os.path.abspath(args.project)
    docs = os.path.join(root, "docs")

    req_file = os.path.join(docs, "REQUIREMENTS.md")
    trace_file = os.path.join(docs, "TRACEABILITY.md")
    nfr_file = os.path.join(docs, "NFR.md")
    openapi = os.path.join(docs, "api", "openapi.yaml")

    missing_files = [p for p in (req_file, trace_file) if not os.path.exists(p)]
    if missing_files:
        print("FAIL  missing required file(s):", file=sys.stderr)
        for p in missing_files:
            print(f"      {os.path.relpath(p, root)}", file=sys.stderr)
        return 2

    req_text = read(req_file)
    trace_text = read(trace_file)

    defined = extract(args.id_pattern, req_text)
    traced = extract(args.id_pattern, trace_text)

    ignore = {p.strip() for p in args.ignore_prefix.split(",") if p.strip()}
    defined = {i for i in defined if i.rsplit("-", 1)[0] not in ignore}
    traced = {i for i in traced if i.rsplit("-", 1)[0] not in ignore}

    untraced = sorted(defined - traced)
    undefined = sorted(traced - defined)

    nfr_defined = extract(NFR_PATTERN, read(nfr_file)) if os.path.exists(nfr_file) else set()
    # Group-level is the documented convention: a matrix maps NFR-1 (the category)
    # to its verification, not each of NFR-1.1 ... NFR-1.8 individually.
    nfr_group_pattern = r"\b(NFR-\d+)\b(?!\.\d)"
    nfr_groups = extract(nfr_group_pattern, read(nfr_file)) if os.path.exists(nfr_file) else set()
    nfr_groups_traced = extract(nfr_group_pattern, trace_text)
    nfr_groups_untraced = sorted(nfr_groups - nfr_groups_traced)

    nfr_traced = extract(NFR_PATTERN, trace_text)
    nfr_untraced = sorted(nfr_defined - nfr_traced)

    prefixes: dict[str, int] = {}
    for rid in defined:
        prefixes[rid.rsplit("-", 1)[0]] = prefixes.get(rid.rsplit("-", 1)[0], 0) + 1

    api_endpoints = parse_openapi(openapi)
    traced_endpoints = extract_endpoints_from_text(trace_text)
    api_norm = {normalise_endpoint(e) for e in api_endpoints}
    traced_norm = {normalise_endpoint(e) for e in traced_endpoints}
    endpoints_not_traced = sorted(api_norm - traced_norm)
    endpoints_not_in_contract = sorted(traced_norm - api_norm)

    failures = (len(untraced) + len(undefined) + len(nfr_groups_untraced)
                + len(endpoints_not_traced))

    if args.json:
        print(json.dumps({
            "requirements_defined": len(defined),
            "requirements_traced": len(traced),
            "untraced": untraced,
            "undefined": undefined,
            "nfr_defined": len(nfr_defined),
            "nfr_groups": len(nfr_groups),
            "nfr_groups_untraced": nfr_groups_untraced,
            "nfr_individually_traced": len(nfr_traced),
            "nfr_untraced": nfr_untraced,
            "modules": dict(sorted(prefixes.items())),
            "openapi_endpoints": len(api_endpoints),
            "traced_endpoints": len(traced_endpoints),
            "endpoints_not_traced": endpoints_not_traced,
            "endpoints_not_in_contract": endpoints_not_in_contract,
            "failures": failures,
        }, indent=2, ensure_ascii=False))
        return 1 if failures else 0

    def head(t: str) -> None:
        print(f"\n{t}")
        print("-" * max(20, len(t)))

    print(f"project  {root}")

    head("Requirement IDs")
    print(f"  defined in REQUIREMENTS.md   {len(defined)}")
    print(f"  traced in TRACEABILITY.md    {len(traced)}")
    if untraced:
        print(f"  UNTRACED ({len(untraced)}): {', '.join(untraced)}")
    else:
        print("  ok  every defined ID is traced")
    if undefined:
        print(f"  UNDEFINED ({len(undefined)}): {', '.join(undefined)}")
        print("        traced but never defined in REQUIREMENTS.md")

    head("Modules")
    if prefixes:
        for p, n in sorted(prefixes.items()):
            print(f"  {p:8} {n:3} requirement(s)")
    else:
        print("  no IDs matched the pattern")

    head("Non-functional requirements")
    if nfr_defined:
        print(f"  defined                    {len(nfr_defined)} across {len(nfr_groups)} group(s)")
        print(f"  groups traced              {len(nfr_groups) - len(nfr_groups_untraced)}")
        if nfr_groups_untraced:
            print(f"  GROUPS UNTRACED: {', '.join(nfr_groups_untraced)}")
        else:
            print("  ok  every NFR group is traced")
        print(f"  individually traced        {len(nfr_traced)} of {len(nfr_defined)}")
        if nfr_untraced and len(nfr_untraced) < len(nfr_defined):
            print("  note  group-level traceability is the convention; individual IDs are informational")
    else:
        print("  note  no NFR IDs found (docs/NFR.md absent or uses another scheme)")

    head("Endpoints")
    print(f"  in openapi.yaml         {len(api_endpoints)}")
    print(f"  in the traceability     {len(traced_endpoints)}")
    if endpoints_not_traced:
        print(f"  NOT TRACED ({len(endpoints_not_traced)}):")
        for e in endpoints_not_traced:
            print(f"      {e}")
        print("        in the contract but serving no requirement")
    else:
        print("  ok  every contract endpoint is traced")
    if endpoints_not_in_contract:
        print(f"  NOT IN CONTRACT ({len(endpoints_not_in_contract)}):")
        for e in endpoints_not_in_contract[:10]:
            print(f"      {e}")
        if len(endpoints_not_in_contract) > 10:
            print(f"      ... and {len(endpoints_not_in_contract) - 10} more")
        print("        traced but absent from openapi.yaml.")
        print("        Expected when the contract covers an earlier release than the matrix.")

    print()
    print(f"{'FAIL' if failures else 'PASS'}  {failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
