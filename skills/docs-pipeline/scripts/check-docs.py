#!/usr/bin/env python3
"""
check-docs.py -- structural checks for a documentation set.

Verifies, for one project directory:
  1. Completeness: are the required document classes present?
  2. Internal links: do they resolve? (URL-decoded, so %20 works)
  3. Emoji: forbidden on the English surface, allowed in working docs
  4. Mermaid: forbidden in agent-docs/ (they are machine-consumed)
  5. Inventory: file count, line count, extension mix

Usage:
    python check-docs.py <project-dir> [--json] [--quiet]

Exit code 0 when every check passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from urllib.parse import unquote

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# --- The document classes that define "complete" -----------------------------
# key -> (label, [acceptable paths relative to the project root], required)
CLASSES: list[tuple[str, str, list[str], bool]] = [
    ("requirements", "Functional requirements", ["docs/REQUIREMENTS.md"], True),
    ("nfr", "Non-functional requirements", ["docs/NFR.md"], True),
    ("architecture", "Architecture", ["docs/ARCHITECTURE.md", "docs/ARQUITECTURA.md"], True),
    ("schema", "Data model", ["docs/SCHEMA.md"], True),
    ("api", "API inventory", ["docs/API.md"], True),
    ("api_contract", "Executable contract", ["docs/api/openapi.yaml"], True),
    ("ui", "UI specification", ["docs/UI.md"], True),
    ("design_system", "Design system", ["docs/DESIGN-SYSTEM.md"], True),
    ("security", "Security design", ["docs/SECURITY.md"], True),
    ("flows", "Critical flows", ["docs/FLOWS.md"], True),
    ("spec", "Technical specification", ["docs/SPEC.md"], True),
    ("traceability", "Traceability", ["docs/TRACEABILITY.md"], True),
    ("operations", "Operations runbook", ["docs/OPERATIONS.md"], True),
    ("glossary", "Glossary", ["docs/GLOSSARY.md"], True),
    ("roadmap", "Roadmap", ["docs/ROADMAP.md"], True),
    ("adr", "Decision records", ["docs/adr/README.md"], True),
    ("readme", "Project front page", ["README.md"], True),
    ("onboarding", "Onboarding", ["ONBOARDING.md"], False),
    ("changelog", "Changelog", ["CHANGELOG.md"], False),
    ("agent_docs", "Agent docs", ["docs/agent-docs/CONTEXT.md"], False),
]

# --- Concepts whose counts must not contradict each other --------------------
# Matched as "<number> <word>". Keep the words in both languages used.
#
# WARNING: a conflict is a PROMPT TO LOOK, not proof of a bug. Ambiguous nouns
# produce false positives. "33 tables" (schema) and "24 tables" (seed data) are
# not a contradiction; "133 requirements" and "83 requirements" are not either
# when one is functional and the other non-functional. Conflicts are reported as
# advisory unless --strict is passed.
CONCEPTS: dict[str, list[str]] = {
    "tables": ["tables", "tablas"],
    "operations": ["operations", "operaciones"],
    "requirements": ["requirements", "requisitos"],
    "documents": ["documents", "documentos", "files", "archivos"],
    "adrs": ["ADRs", "ADR"],
    "paths": ["paths", "rutas"],
    "schemas": ["schemas"],
    "indexes": ["indexes", "índices", "indices"],
    "modules": ["modules", "módulos", "modulos"],
    "endpoints": ["endpoints"],
}

# Documents that narrate history by definition. They legitimately mention counts
# that no longer hold ("38 documents were generated before the reframe").
# Checking them produces pure noise.
NARRATIVE_DOCS = {"ACLARACIONES.md", "CHANGELOG.md", "STATUS.md"}

# Emoji and pictographs. NOT arrows, math or punctuation: a design system legitimately
# uses → in a state machine and ✓ in a table, and flagging those is noise.
EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\u2600-\u26FF\u2700-\u27BF\u2B00-\u2BFF]"
)
TYPOGRAPHIC_ALLOWED = set("→←↑↓✓✗×·—–…°±≥≤≈≠∞§¶†‡•∙■□●○◆◇")


def emoji_in(text: str) -> list[str]:
    return [c for c in EMOJI.findall(text) if c not in TYPOGRAPHIC_ALLOWED]

# Spanish function words, for the language heuristic.
ES_MARKERS = {
    "de", "la", "el", "los", "las", "que", "en", "un", "una", "para", "con",
    "por", "no", "se", "su", "del", "como", "pero", "más", "mas", "este",
    "esta", "sin", "sobre", "entre", "cada", "todo", "toda", "son", "es",
}
EN_MARKERS = {
    "the", "of", "and", "to", "in", "is", "are", "for", "with", "that",
    "this", "not", "but", "from", "which", "each", "every", "must", "when",
}


def language_of(text: str) -> str:
    """Crude but reliable for long technical docs: count function words."""
    words = re.findall(r"[a-záéíóúñü]+", text.lower())
    if len(words) < 200:
        return "unknown"
    es = sum(1 for w in words if w in ES_MARKERS)
    en = sum(1 for w in words if w in EN_MARKERS)
    if es > en * 1.3:
        return "es"
    if en > es * 1.3:
        return "en"
    return "unknown"


def find_markdown(root: str) -> list[str]:
    out = []
    for dp, dn, fn in os.walk(root):
        if ".git" in dp.split(os.sep):
            continue
        for f in fn:
            if f.endswith(".md"):
                out.append(os.path.join(dp, f))
    return sorted(out)


def check_classes(root: str) -> list[dict]:
    rows = []
    for key, label, paths, required in CLASSES:
        found = next((p for p in paths if os.path.exists(os.path.join(root, p))), None)
        rows.append({
            "key": key, "label": label, "required": required,
            "found": found, "ok": bool(found) or not required,
        })
    return rows


def check_links(root: str, files: list[str]) -> list[dict]:
    """Archive is excluded: it is a historical record, not a live document.
    An archived file pointing at something that moved is expected."""
    broken = []
    for f in files:
        if "archive" in os.path.relpath(f, root).split(os.sep):
            continue
        base = os.path.dirname(f)
        text = open(f, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"\]\(([^)#\s]+?)(?:#[^)]*)?\)", text):
            raw = m.group(1)
            if raw.startswith(("http", "mailto:", "#", "tel:")):
                continue
            target = os.path.normpath(os.path.join(base, unquote(raw)))
            if not os.path.exists(target):
                broken.append({
                    "file": os.path.relpath(f, root),
                    "target": raw,
                })
    return broken


def check_emoji(root: str, files: list[str]) -> tuple[list[dict], list[dict]]:
    violations, allowed = [], []
    for f in files:
        rel = os.path.relpath(f, root)
        if "archive" in rel.split(os.sep):
            continue
        text = open(f, encoding="utf-8", errors="replace").read()
        hits = emoji_in(text)
        if not hits:
            continue
        lang = language_of(text)
        entry = {"file": rel, "count": len(hits), "language": lang,
                 "samples": sorted({hex(ord(c)) for c in hits})[:6]}
        if lang == "en":
            violations.append(entry)
        else:
            allowed.append(entry)
    return violations, allowed


def check_mermaid(root: str) -> list[dict]:
    agent_dir = os.path.join(root, "docs", "agent-docs")
    if not os.path.isdir(agent_dir):
        return []
    bad = []
    for f in sorted(os.listdir(agent_dir)):
        if not f.endswith(".md"):
            continue
        text = open(os.path.join(agent_dir, f), encoding="utf-8", errors="replace").read()
        if "mermaid" in text.lower():
            bad.append({"file": f"docs/agent-docs/{f}"})
    return bad


def check_counts(root: str, files: list[str]) -> list[dict]:
    """Find concepts whose declared count differs between documents.

    Skips narrative documents and archive: they describe past states on purpose.
    """
    pattern = re.compile(r"\b(\d{1,4})\s+([A-Za-zÀ-ÿ]+)\b")
    by_concept: dict[str, list[tuple[int, str]]] = {}
    for f in files:
        rel = os.path.relpath(f, root)
        parts = rel.split(os.sep)
        if "archive" in parts or os.path.basename(f) in NARRATIVE_DOCS:
            continue
        text = open(f, encoding="utf-8", errors="replace").read()
        for m in pattern.finditer(text):
            n, word = int(m.group(1)), m.group(2)
            for concept, words in CONCEPTS.items():
                if word in words:
                    by_concept.setdefault(concept, []).append((n, rel))
    conflicts = []
    for concept, hits in sorted(by_concept.items()):
        values = sorted({n for n, _ in hits})
        if len(values) > 1:
            detail = {}
            for n, rel in hits:
                detail.setdefault(n, set()).add(rel)
            conflicts.append({
                "concept": concept,
                "values": values,
                "where": {n: sorted(v) for n, v in detail.items()},
            })
    return conflicts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", help="project directory")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--quiet", action="store_true", help="only failures")
    ap.add_argument("--strict", action="store_true",
                    help="treat count conflicts as failures (they are advisory by default)")
    args = ap.parse_args()

    root = os.path.abspath(args.project)
    if not os.path.isdir(root):
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    files = find_markdown(root)
    classes = check_classes(root)
    broken = check_links(root, files)
    emoji_bad, emoji_ok = check_emoji(root, files)
    mermaid_bad = check_mermaid(root)
    conflicts = check_counts(root, files)

    missing_required = [c for c in classes if not c["ok"]]
    missing_optional = [c for c in classes if not c["found"] and not c["required"]]

    failures = (len(missing_required) + len(broken) + len(emoji_bad)
                + len(mermaid_bad) + (len(conflicts) if args.strict else 0))

    if args.json:
        print(json.dumps({
            "project": root,
            "files": len(files),
            "classes": classes,
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "broken_links": broken,
            "emoji_violations": emoji_bad,
            "emoji_allowed": emoji_ok,
            "mermaid_in_agent_docs": mermaid_bad,
            "count_conflicts": conflicts,
            "failures": failures,
        }, indent=2, ensure_ascii=False))
        return 1 if failures else 0

    def head(title: str) -> None:
        print(f"\n{title}")
        print("-" * max(20, len(title)))

    if not args.quiet:
        print(f"project  {root}")
        print(f"markdown {len(files)} files")

    head("Completeness")
    for c in classes:
        mark = "ok  " if c["found"] else ("MISS" if c["required"] else "opt ")
        if args.quiet and c["found"]:
            continue
        print(f"  [{mark}] {c['label']:32} {c['found'] or '--'}")
    if missing_optional:
        print(f"  note: {len(missing_optional)} optional class(es) absent: "
              f"{', '.join(c['label'] for c in missing_optional)}")

    head("Internal links")
    if broken:
        for b in broken:
            print(f"  BROKEN  {b['file']} -> {b['target']}")
    else:
        print("  ok  all resolve")

    head("Emoji")
    if emoji_bad:
        for e in emoji_bad:
            print(f"  FAIL  {e['file']}  {e['count']} in an English document  {e['samples']}")
    else:
        print("  ok  none in English documents")
    if emoji_ok and not args.quiet:
        for e in emoji_ok:
            print(f"  note  {e['file']}  {e['count']} in a working document ({e['language']})")

    head("Mermaid in agent-docs")
    if mermaid_bad:
        for b in mermaid_bad:
            print(f"  FAIL  {b['file']}  agent docs use text graphs, not diagrams")
    else:
        print("  ok  none")

    head("Count consistency")
    if conflicts:
        for c in conflicts:
            print(f"  CHECK  {c['concept']}: {c['values']}")
            for n, where in c["where"].items():
                print(f"              {n} declared in {', '.join(where)}")
        print("  note: ambiguous nouns cause false positives here. Verify by hand.")
    else:
        print("  ok  no contradicting counts")

    print()
    if conflicts and not args.strict:
        print(f"{len(conflicts)} count conflict(s) to review (advisory; use --strict to gate)")
    print(f"{'FAIL' if failures else 'PASS'}  {failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
