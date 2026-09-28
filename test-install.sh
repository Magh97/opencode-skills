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

echo ""
echo "=== Todos los tests pasaron ==="
