#!/usr/bin/env bash
set -euo pipefail

# Instala los agentes y skills de opencode-skills en la config global de opencode.
#
# Uso:
#   ./install.sh            # solo agentes (skills via npx skills add)
#   ./install.sh --global   # agentes + skills copiadas a ~/.config/opencode/skills
#   ./install.sh -y         # no preguntar

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
AGENT_DIR="$CONFIG_DIR/agent"
SKILL_DIR="$CONFIG_DIR/skills"

GLOBAL=0
YES=0
DO_AGENTS=0
DO_SKILLS=0

for arg in "$@"; do
    case "$arg" in
        --global|-g) GLOBAL=1 ;;
        --yes|-y|-Y) YES=1 ;;
        --agents|-a) DO_AGENTS=1 ;;
        --skills|-s) DO_SKILLS=1 ;;
        *) echo "Argumento desconocido: $arg" >&2; exit 1 ;;
    esac
done

if [[ $DO_AGENTS -eq 0 && $DO_SKILLS -eq 0 ]]; then
    DO_AGENTS=1
    if [[ $GLOBAL -eq 1 ]]; then DO_SKILLS=1; fi
fi

confirm() {
    if [[ $YES -eq 1 ]]; then return 0; fi
    read -r -p "$1 (s/N) " resp
    [[ "$resp" =~ ^(s|y|si|yes)$ ]]
}

if [[ $DO_AGENTS -eq 1 ]]; then
    SRC_AGENTS="$SCRIPT_DIR/.opencode/agent"
    if [[ ! -d "$SRC_AGENTS" ]]; then
        echo "Error: no existe $SRC_AGENTS" >&2
        exit 1
    fi
    COUNT=$(find "$SRC_AGENTS" -name '*.md' -type f | wc -l | tr -d ' ')
    if confirm "Instalar $COUNT agentes en $AGENT_DIR?"; then
        mkdir -p "$AGENT_DIR"
        cp -f "$SRC_AGENTS"/*.md "$AGENT_DIR/"
        echo "Agentes instalados en $AGENT_DIR"
        echo "Agentes: $(ls "$AGENT_DIR"/*.md | xargs -n1 basename | sed 's/\.md$//' | tr '\n' ', ')"
    else
        echo "Instalacion de agentes cancelada."
        DO_AGENTS=0
    fi
fi

if [[ $DO_SKILLS -eq 1 && $GLOBAL -eq 1 ]]; then
    SRC_SKILLS="$SCRIPT_DIR/skills"
    if [[ ! -d "$SRC_SKILLS" ]]; then
        echo "Error: no existe $SRC_SKILLS" >&2
        exit 1
    fi
    if confirm "Copiar skills a $SKILL_DIR?"; then
        mkdir -p "$SKILL_DIR"
        cp -r "$SRC_SKILLS"/* "$SKILL_DIR/"
        echo "Skills instaladas en $SKILL_DIR"
    else
        echo "Instalacion de skills cancelada."
        DO_SKILLS=0
    fi
elif [[ $DO_SKILLS -eq 1 ]]; then
    echo "Para instalar skills use: npx skills add Magh97/opencode-skills --all"
    echo "(o pase --global para copiarlas manualmente a la carpeta global de opencode)"
fi

echo ""
echo "Reinicia opencode para que los cambios tomen efecto."
