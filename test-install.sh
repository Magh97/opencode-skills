#!/usr/bin/env bash
set -euo pipefail

# Test suite para install.sh
# Crea un directorio temporal como HOME, ejecuta el instalador con varias
# combinaciones de flags y aserta los resultados.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP_HOME=$(mktemp -d)
CONFIG_DIR="$TMP_HOME/.config/opencode"
AGENTS_DIR="$CONFIG_DIR/agent"
SKILLS_DIR="$CONFIG_DIR/skills"

trap 'rm -rf "$TMP_HOME"' EXIT

count_skills() {
    local dir="$1"
    if [[ ! -d "$dir" ]]; then
        echo 0
        return
    fi
    find "$dir" -maxdepth 1 -mindepth 1 -type d | wc -l | tr -d ' '
}

count_agents() {
    local dir="$1"
    if [[ ! -d "$dir" ]]; then
        echo 0
        return
    fi
    find "$dir" -maxdepth 1 -name '*.md' -type f | wc -l | tr -d ' '
}

run_install() {
    HOME="$TMP_HOME" "$SCRIPT_DIR/install.sh" -y "$@"
}

echo "=== Test 1: solo agentes (default) ==="
rm -rf "$CONFIG_DIR"
run_install
agents=$(count_agents "$AGENTS_DIR")
skills=$(count_skills "$SKILLS_DIR")
if [[ "$agents" -gt 0 && "$skills" -eq 0 ]]; then
    echo "PASS: $agents agentes, $skills skills"
else
    echo "FAIL: esperaba >0 agentes y 0 skills, obtuve $agents agentes y $skills skills"
    exit 1
fi

echo "=== Test 2: agentes + skills (global) ==="
rm -rf "$CONFIG_DIR"
run_install --global
agents=$(count_agents "$AGENTS_DIR")
skills=$(count_skills "$SKILLS_DIR")
if [[ "$agents" -gt 0 && "$skills" -gt 0 ]]; then
    echo "PASS: $agents agentes, $skills skills"
else
    echo "FAIL: esperaba >0 agentes y >0 skills, obtuve $agents agentes y $skills skills"
    exit 1
fi

echo "=== Test 3: filtrado por kits (--kits dotnet) ==="
rm -rf "$CONFIG_DIR"
run_install --global --kits dotnet
skills=$(count_skills "$SKILLS_DIR")
# El kit dotnet tiene varias skills, pero no todas las 155
if [[ "$skills" -gt 0 && "$skills" -lt 155 ]]; then
    echo "PASS: $skills skills (filtrado aplicado)"
else
    echo "FAIL: esperaba skills filtrados, obtuve $skills"
    exit 1
fi

echo "=== Test 4: kits implica global automáticamente ==="
rm -rf "$CONFIG_DIR"
run_install --kits python
skills=$(count_skills "$SKILLS_DIR")
if [[ "$skills" -gt 0 && "$skills" -lt 155 ]]; then
    echo "PASS: --kits sin --global también instaló skills ($skills)"
else
    echo "FAIL: --kits debería implicar --global, obtuve $skills skills"
    exit 1
fi

echo "=== Test 5: multi-target ==="
rm -rf "$CONFIG_DIR" "$TMP_HOME/.agents"
run_install --global --target opencode,agents
agents_skills=$(count_skills "$SKILLS_DIR")
universal_skills=$(count_skills "$TMP_HOME/.agents/skills")
if [[ "$agents_skills" -gt 0 && "$universal_skills" -eq "$agents_skills" ]]; then
    echo "PASS: $agents_skills skills en ambos destinos"
else
    echo "FAIL: esperaba misma cantidad en ambos destinos, obtuve $agents_skills y $universal_skills"
    exit 1
fi

echo "=== Test 6: --list-kits coincide con kits.tsv ==="
expected_kits=$(awk -F'\t' '!/^#/ && $1 != "" { n++ } END { print n }' "$SCRIPT_DIR/.opencode/kits.tsv")
listed_kits=$(HOME="$TMP_HOME" "$SCRIPT_DIR/install.sh" --list-kits | wc -l | tr -d ' ')
if [[ "$listed_kits" -eq "$expected_kits" ]]; then
    echo "PASS: $listed_kits kits listados"
else
    echo "FAIL: esperaba $expected_kits kits, obtuve $listed_kits"
    exit 1
fi

echo "=== Test 7: kit desconocido falla ==="
if HOME="$TMP_HOME" "$SCRIPT_DIR/install.sh" -y --global --kits no-existe >/dev/null 2>&1; then
    echo "FAIL: un kit desconocido deberia fallar"
    exit 1
else
    echo "PASS: kit desconocido rechazado"
fi

echo "=== Test 8: --dry-run no escribe nada ==="
rm -rf "$CONFIG_DIR"
run_install --global --dry-run >/dev/null
if [[ ! -d "$SKILLS_DIR" && ! -d "$AGENTS_DIR" ]]; then
    echo "PASS: dry-run no creo directorios"
else
    echo "FAIL: dry-run escribio en disco"
    exit 1
fi

echo "=== Test 9: --prune elimina skills huerfanas ==="
rm -rf "$CONFIG_DIR"
run_install --global >/dev/null
mkdir -p "$SKILLS_DIR/skill-huerfana"
echo "---" > "$SKILLS_DIR/skill-huerfana/SKILL.md"
run_install --global --prune >/dev/null
if [[ ! -d "$SKILLS_DIR/skill-huerfana" ]]; then
    echo "PASS: skill huerfana eliminada"
else
    echo "FAIL: --prune no elimino la skill huerfana"
    exit 1
fi

echo "=== Test 10: --uninstall borra solo lo instalado ==="
rm -rf "$CONFIG_DIR"
run_install --global >/dev/null
run_install --uninstall >/dev/null
agents_left=$(count_agents "$AGENTS_DIR")
skills_left=$(count_skills "$SKILLS_DIR")
if [[ "$agents_left" -eq 0 && "$skills_left" -eq 0 ]]; then
    echo "PASS: agentes y skills desinstalados"
else
    echo "FAIL: quedaron $agents_left agentes y $skills_left skills"
    exit 1
fi

echo "=== Test 11: --target pi ==="
rm -rf "$CONFIG_DIR" "$TMP_HOME/.pi"
run_install --global --target pi >/dev/null
pi_skills=$(count_skills "$TMP_HOME/.pi/agent/skills")
if [[ "$pi_skills" -eq 133 ]]; then
    echo "PASS: 133 skills instaladas en ~/.pi/agent/skills"
else
    echo "FAIL: esperaba 133 skills en pi, obtuve $pi_skills"
    exit 1
fi

echo ""
echo "=== Todos los tests pasaron ==="
