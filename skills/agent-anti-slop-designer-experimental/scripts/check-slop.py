#!/usr/bin/env python3
"""
check-slop.py -- mechanical anti-slop audit for a generated product.

Because prohibitions written as a checklist are advisory. Exit codes are not.

Checks, for one project directory:
  1. The design system document exists and declares every required section.
  2. The generated source carries none of the known slop signatures.
  3. Aggregations that reveal the absence of a decision: one radius for the
     whole app, one duration for every animation, cursors left at the default.

Severity model:
  gate      fails the run (exit 1)
  advisory  reported, fails only with --strict

Nothing here is final judgement. A finding is a prompt to look, and every
rule documents why it exists so a real finding is not "fixed" by weakening
the check.

Usage:
    python check-slop.py <project-dir> [--json] [--quiet] [--strict]
    python check-slop.py <project-dir> --design-system path/to/design-system.md
    python check-slop.py <project-dir> --no-design-system
    python check-slop.py --list-rules

Exit code 0 when no gate fails, 1 otherwise, 2 on a bad invocation.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# --- Output budget -----------------------------------------------------------
# A generated app can carry thousands of hits. Never flood the session.
MAX_LIST = 200
MAX_HUMAN = 40

IGNORED_DIRS = {
    "node_modules", ".git", ".venv", "venv", "build", "dist", ".next", ".nuxt",
    ".svelte-kit", "coverage", "out", ".output", "__pycache__", "vendor",
    "public", "static",  # built output, not source
}

SOURCE_EXT = {
    ".css", ".scss", ".sass", ".less", ".styl",
    ".js", ".mjs", ".cjs", ".jsx",
    ".ts", ".tsx", ".vue", ".svelte", ".astro", ".html", ".htm",
}

MAX_FILE_BYTES = 2_000_000  # skip generated/minified monsters

# --- Design system document --------------------------------------------------
DS_CANDIDATES = [
    "design-system.md", "DESIGN-SYSTEM.md", "DESIGN_SYSTEM.md",
    "docs/design-system.md", "docs/DESIGN-SYSTEM.md", "docs/DESIGN.md",
]

# Stems, accent-free, matched case-insensitively against the document text.
# A section is "declared" when its stem appears anywhere in the title or body.
REQUIRED_SECTIONS = [
    ("arqueolog", "Arqueología y materiales del dominio (0)"),
    ("manifiesto", "Manifiesto de diseño (1)"),
    ("paleta", "Paleta de color (2)"),
    ("tipograf", "Tipografía como arquitectura (3)"),
    ("spacing", "Sistema de spacing (4)"),
    ("borde", "Bordes, radios y texturas (5)"),
    ("sombra", "Sombras, glows y profundidad (6)"),
    ("motion", "Motion, animation & physics (7)"),
    ("navegaci", "Navegación y layout (8)"),
    ("componente", "Componentes base (9)"),
    ("prohibicion", "Prohibiciones explícitas (11)"),
    ("referencia", "Referencias y moodboard (12)"),
    ("notas t", "Notas técnicas para implementación (13)"),
    ("sonido", "Sonido y audio (14)"),
    ("iluminaci", "Iluminación (15)"),
    ("tempo", "Tempo system (16)"),
    ("cursor", "Cursor (17)"),
    ("accesibilidad", "Accesibilidad — piso no negociable (18)"),
    ("degradaci", "Modos de degradación (19)"),
    ("performance", "Presupuesto de performance (20)"),
    ("voz", "Voz y microcopy (21)"),
    ("entrega", "Entrega y artefactos (22)"),
]

# Project-level rules live in this file (see SKILL.md 4.5.2). It lets the
# design system govern its own audit instead of only inheriting the factory set.
PROJECT_RULE_FILES = [
    "prohibitions.lint.json",
    "docs/prohibitions.lint.json",
    ".anti-slop.json",
]

# --- Slop signatures ---------------------------------------------------------
EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u26FF\u2700-\u27BF\u2B00-\u2BFF]")
TYPOGRAPHIC_ALLOWED = set("→←↑↓✓✗×·—–…°±≥≤≈≠∞§¶†‡•∙■□●○◆◇")

RULES = [
    {
        "id": "SLOP-TRANSITION-ALL",
        "severity": "gate",
        "pattern": re.compile(r"transition\s*:\s*all\b|\btransition-all\b|transitionProperty\s*:\s*['\"]all['\"]"),
        "message": "transition: all animates every property",
        "why": "Motion must be specified (type, duration, easing, purpose), not indiscriminate.",
    },
    {
        "id": "SLOP-SPINNER",
        "severity": "gate",
        "pattern": re.compile(r"animate-spin\b|\bspinner\b|react-loader-spinner|\bLoader2\b|\blds-(?:ring|roller|ellipsis|default|spinner)\b", re.IGNORECASE),
        "message": "generic spinner",
        "why": "Loading is a narrative beat (rule 9), not a circle that turns.",
    },
    {
        "id": "SLOP-EMPTY-COPY",
        "severity": "gate",
        "pattern": re.compile(r"(?i)no data found|no results found|nothing (?:here|to show)|no records(?: found)?|sin datos|sin resultados|no hay datos|no se encontraron resultados"),
        "message": "generic empty-state copy",
        "why": "Special states are the zone of maximum personality; this copy is filler.",
    },
    {
        "id": "SLOP-ERROR-COPY",
        "severity": "gate",
        "pattern": re.compile(r"(?i)something went wrong|an error occurred|error occurred|oops!?\b|algo salió mal|ha ocurrido un error|error inesperado"),
        "message": "generic error copy",
        "why": "An error is a designed moment with its own voice.",
    },
    {
        "id": "SLOP-AI-GRADIENT",
        "severity": "gate",
        "pattern": re.compile(
            r"(?i)linear-gradient\([^)]*#(?:8b5cf6|a855f7|7c3aed|6366f1)[^)]*#(?:3b82f6|60a5fa|6366f1|8b5cf6)"
            r"|from-(?:purple|violet|indigo)-\d+[^\n]{0,120}to-(?:blue|indigo|purple|pink)-\d+"
        ),
        "message": "the generic purple-to-blue AI gradient",
        "why": "The single most recognisable generative signature. If it is here by accident, it is slop.",
    },
    {
        "id": "SLOP-INTER-ROBOTO",
        "severity": "advisory",
        "pattern": re.compile(r"font-family\s*:\s*[^;\n]*(?:Inter|Roboto)|['\"]Inter['\"]|['\"]Roboto['\"]|fontFamily[^\n]*(?:Inter|Roboto)"),
        "message": "Inter/Roboto as a primary face",
        "why": "Allowed only with extreme modification (variable axis, distortion). Advisory: heuristic.",
    },
    {
        "id": "SLOP-GRID12",
        "severity": "advisory",
        "pattern": re.compile(r"grid-cols-12\b|col-span-\d+\b|grid-template-columns\s*:\s*repeat\(\s*12\b"),
        "message": "12-column grid by default",
        "why": "The default grid is a template, not a layout decision. Advisory.",
    },
    {
        "id": "SLOP-MATERIAL-ICONS",
        "severity": "advisory",
        "pattern": re.compile(r"@mui/icons-material|@material-ui/icons|material-icons|Material Icons"),
        "message": "Material Design icons uncustomised",
        "why": "A borrowed icon language reads as a library default. Advisory.",
    },
    {
        "id": "SLOP-GRAY-PALETTE",
        "severity": "advisory",
        "pattern": re.compile(r"\b(?:bg|text|border|from|to)-(?:slate|zinc|neutral|stone|gray)-\d{2,3}\b"),
        "message": "framework default gray scale",
        "why": "A grey scale with no emotional point of view. Advisory.",
    },
    {
        "id": "SLOP-EMOJI-ICON",
        "severity": "advisory",
        "pattern": EMOJI,
        "message": "emoji used as an icon",
        "why": "Emoji are a system font, not a custom icon language. Advisory (intent is possible).",
        "ignore_chars": TYPOGRAPHIC_ALLOWED,
    },
    {
        "id": "SLOP-CURSOR-DEFAULT",
        "severity": "advisory",
        "pattern": re.compile(r"cursor\s*:\s*(?:default|auto)\b"),
        "message": "cursor left at the system default",
        "why": "The cursor is part of the scene. Advisory.",
    },
]

# Aggregations ---------------------------------------------------------------
RADIUS_DECL = re.compile(r"border-radius\s*:\s*([0-9.]+(?:px|rem|em)|0)")
RADIUS_TW = re.compile(r"\brounded-(none|sm|md|lg|xl|2xl|3xl|full)\b")
DURATION_DECL = re.compile(r"(?:transition-duration|animation-duration)\s*:\s*([0-9.]+m?s)")
DURATION_SHORTHAND = re.compile(r"transition\s*:[^;]*?([0-9.]+m?s)")
DURATION_TW = re.compile(r"\bduration-(\d+)\b")

GENERIC_RADII = {"4px", "6px", "8px", "12px", "16px"}


def to_px(value: str) -> float | None:
    """Normalise a CSS length to px so 0.5rem and 8px are the same decision."""
    value = value.strip()
    if value == "0":
        return 0.0
    m = re.match(r"([0-9.]+)(px|rem|em)", value)
    if not m:
        return None
    n = float(m.group(1))
    if m.group(2) in ("rem", "em"):
        n *= 16
    return n


def to_ms(value: str) -> float | None:
    """Normalise a CSS duration to ms so 0.3s and 300ms are the same decision."""
    m = re.match(r"([0-9.]+)(ms|s)", value.strip())
    if not m:
        return None
    n = float(m.group(1))
    return n * 1000 if m.group(2) == "s" else n


def read(path: str) -> str:
    return open(path, encoding="utf-8", errors="replace").read()


def find_source_files(root: str) -> list[str]:
    out = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in IGNORED_DIRS]
        for f in fn:
            if os.path.splitext(f)[1].lower() not in SOURCE_EXT:
                continue
            p = os.path.join(dp, f)
            try:
                if os.path.getsize(p) > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            out.append(p)
    return sorted(out)


def find_design_system(root: str, explicit: str | None) -> str | None:
    if explicit:
        p = explicit if os.path.isabs(explicit) else os.path.join(root, explicit)
        return p if os.path.exists(p) else None
    for rel in DS_CANDIDATES:
        p = os.path.join(root, rel)
        if os.path.exists(p):
            return p
    # Any *design-system*.md under the root (one level deep is enough).
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in IGNORED_DIRS]
        for f in fn:
            if f.lower() in ("design-system.md", "design_system.md", "design.md"):
                return os.path.join(dp, f)
    return None


def check_design_system(path: str) -> list[str]:
    """Return the labels of the sections the document does not declare."""
    text = read(path).lower()
    missing = []
    for stem, label in REQUIRED_SECTIONS:
        if stem not in text:
            missing.append(label)
    return missing


def load_project_rules(root: str) -> tuple[list[dict], list[dict]]:
    """Merge the project's own prohibitions.lint.json into the factory rules.

    Returns (rules, errors). A malformed rule file is reported as a gate: a
    silently ignored prohibition is worse than no prohibition.
    """
    for rel in PROJECT_RULE_FILES:
        path = os.path.join(root, rel)
        if not os.path.exists(path):
            continue
        try:
            data = json.loads(read(path))
        except (json.JSONDecodeError, OSError) as e:
            return [], [{"file": rel, "error": f"unreadable: {e}"}]
        rules, errors = [], []
        for i, r in enumerate(data.get("rules", [])):
            rid = r.get("id") or f"PROJECT-{i + 1}"
            severity = r.get("severity", "gate")
            if severity not in ("gate", "advisory"):
                errors.append({"file": rel,
                               "error": f"{rid}: severity must be gate|advisory"})
                continue
            try:
                pattern = re.compile(r["pattern"])
            except (KeyError, TypeError, re.error) as e:
                errors.append({"file": rel, "error": f"{rid}: {e}"})
                continue
            rules.append({
                "id": rid, "severity": severity, "pattern": pattern,
                "message": r.get("message", "project rule"),
                "why": r.get("why", "declared in prohibitions.lint.json"),
            })
        return rules, errors
    return [], []


def scan_rules(root: str, files: list[str], rules: list[dict]) -> list[dict]:
    findings: list[dict] = []
    for f in files:
        rel = os.path.relpath(f, root)
        try:
            lines = read(f).splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, 1):
            if len(line) > 5000:  # minified: skip, it produces noise
                continue
            for rule in rules:
                # One finding per rule per line: a line with two emoji is one
                # problem, not two, and two matches on a line are one location.
                if "ignore_chars" in rule:
                    if not any(c not in rule["ignore_chars"]
                               for c in rule["pattern"].findall(line)):
                        continue
                elif not rule["pattern"].search(line):
                    continue
                findings.append({
                    "rule": rule["id"],
                    "severity": rule["severity"],
                    "file": rel,
                    "line": lineno,
                    "text": line.strip()[:160],
                })
    return findings


def check_aggregations(root: str, files: list[str]) -> list[dict]:
    """The absence of a decision is invisible line by line and obvious in aggregate."""
    findings: list[dict] = []
    radii: dict[str, int] = {}
    durations: dict[str, int] = {}

    for f in files:
        try:
            text = read(f)
        except OSError:
            continue
        for m in RADIUS_DECL.finditer(text):
            px = to_px(m.group(1))
            if px is not None:
                key = f"{px:g}px"
                radii[key] = radii.get(key, 0) + 1
        for m in RADIUS_TW.finditer(text):
            key = "tw-" + m.group(1)
            radii[key] = radii.get(key, 0) + 1
        for pat in (DURATION_DECL, DURATION_SHORTHAND):
            for m in pat.finditer(text):
                ms = to_ms(m.group(1))
                if ms is not None:
                    key = f"{ms:g}ms"
                    durations[key] = durations.get(key, 0) + 1
        for m in DURATION_TW.finditer(text):
            key = f"{float(m.group(1)):g}ms"
            durations[key] = durations.get(key, 0) + 1

    total_radius = sum(radii.values())
    if total_radius >= 5 and len(radii) == 1:
        value = next(iter(radii))
        pretty = value[3:] if value.startswith("tw-") else value
        if value.startswith("tw-") or pretty in GENERIC_RADII:
            findings.append({
                "rule": "SLOP-UNIFORM-RADIUS",
                "severity": "advisory",
                "file": "(project)",
                "line": 0,
                "text": f"{total_radius} declarations, one single radius: {pretty}",
            })

    total_duration = sum(durations.values())
    if total_duration >= 5 and len(durations) == 1:
        value = next(iter(durations))
        findings.append({
            "rule": "SLOP-UNIFORM-DURATION",
            "severity": "advisory",
            "file": "(project)",
            "line": 0,
            "text": f"{total_duration} declarations, one single duration: {value}",
        })

    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", nargs="?", help="project directory")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--quiet", action="store_true", help="only findings")
    ap.add_argument("--strict", action="store_true", help="advisories become failures")
    ap.add_argument("--design-system", help="path to the design system document")
    ap.add_argument("--no-design-system", action="store_true",
                    help="audit the source only (skips section completeness)")
    ap.add_argument("--list-rules", action="store_true", help="print the rules and exit")
    args = ap.parse_args()

    if args.list_rules:
        for rule in RULES:
            print(f"{rule['severity']:9} {rule['id']:24} {rule['message']}")
        return 0

    if not args.project:
        ap.print_usage(sys.stderr)
        print("a project directory is required", file=sys.stderr)
        return 2

    root = os.path.abspath(args.project)
    if not os.path.isdir(root):
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    # --- 1. Design system ------------------------------------------------
    ds_path = None if args.no_design_system else find_design_system(root, args.design_system)
    ds_missing_sections: list[str] = []
    ds_ok = None
    if not args.no_design_system:
        if ds_path:
            ds_missing_sections = check_design_system(ds_path)
            ds_ok = not ds_missing_sections
        else:
            ds_ok = False

    # --- 2. Source signatures -------------------------------------------
    files = find_source_files(root)
    project_rules, rule_errors = load_project_rules(root)
    all_rules = RULES + project_rules
    findings = scan_rules(root, files, all_rules)
    findings.extend(check_aggregations(root, files))
    for e in rule_errors:
        findings.append({"rule": "LINT-CONFIG", "severity": "gate",
                         "file": e["file"], "line": 0, "text": e["error"]})

    gates = [f for f in findings if f["severity"] == "gate"]
    advisories = [f for f in findings if f["severity"] == "advisory"]
    ds_gate = 1 if (not args.no_design_system and not ds_ok) else 0

    failures = len(gates) + ds_gate + (len(advisories) if args.strict else 0)

    by_rule: dict[str, list[dict]] = {}
    for f in findings:
        by_rule.setdefault(f["rule"], []).append(f)

    if args.json:
        print(json.dumps({
            "project": root,
            "source_files": len(files),
            "design_system": None if args.no_design_system else ds_path,
            "design_system_missing_sections": ds_missing_sections[:MAX_LIST],
            "design_system_missing_sections_total": len(ds_missing_sections),
            "gate_findings": gates[:MAX_LIST],
            "gate_findings_total": len(gates),
            "advisory_findings": advisories[:MAX_LIST],
            "advisory_findings_total": len(advisories),
            "by_rule": {k: len(v) for k, v in sorted(by_rule.items())},
            "project_rules": len(project_rules),
            "failures": failures,
        }, indent=2, ensure_ascii=False))
        return 1 if failures else 0

    def head(t: str) -> None:
        print(f"\n{t}")
        print("-" * max(20, len(t)))

    print(f"project       {root}")
    print(f"source files  {len(files)}")
    if not args.no_design_system:
        if ds_path:
            print(f"design system {os.path.relpath(ds_path, root)}"
                  f"  ({len(REQUIRED_SECTIONS) - len(ds_missing_sections)}/{len(REQUIRED_SECTIONS)} sections)")
        else:
            print("design system NOT FOUND")

    head("Design system")
    if args.no_design_system:
        print("  skipped (--no-design-system)")
    elif not ds_path:
        print("  GATE  no design system document found")
        print("        looked for: " + ", ".join(DS_CANDIDATES))
        print("        rule 6: no system means no audit; write it before the first screen")
    elif ds_missing_sections:
        for s in ds_missing_sections[:MAX_HUMAN]:
            print(f"  GATE  missing section: {s}")
        if len(ds_missing_sections) > MAX_HUMAN:
            print(f"  ... and {len(ds_missing_sections) - MAX_HUMAN} more")
    else:
        print("  ok  every required section is declared")

    head("Source findings")
    if not findings:
        print("  ok  no known slop signature")
    else:
        for rule_id, hits in sorted(by_rule.items()):
            sev = hits[0]["severity"].upper()
            print(f"  [{sev:8}] {rule_id}  {len(hits)} finding(s)")
            for h in hits[:6]:
                loc = f"{h['file']}:{h['line']}" if h["line"] else h["file"]
                print(f"             {loc}  {h['text']}")
            if len(hits) > 6:
                print(f"             ... and {len(hits) - 6} more")
            why = next((r["why"] for r in all_rules if r["id"] == rule_id), "")
            if why:
                print(f"             why: {why}")

    print()
    if failures:
        parts = []
        if gates:
            parts.append(f"{len(gates)} source gate(s)")
        if ds_gate:
            parts.append("design system incomplete")
        if args.strict and advisories:
            parts.append(f"{len(advisories)} advisory")
        print("FAIL  " + " + ".join(parts) if parts else f"FAIL  {failures} failure(s)")
    else:
        print("PASS  0 gate(s)")
        if advisories:
            print(f"      {len(advisories)} advisory finding(s) to review (use --strict to gate)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
