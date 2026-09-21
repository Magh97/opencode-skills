#!/usr/bin/env bash
set -euo pipefail

# Instala los agentes y skills de opencode-skills en la config global de opencode.
#
# Uso:
#   ./install.sh            # solo agentes (skills via npx skills add)
#   ./install.sh --global   # agentes + skills copiadas a ~/.config/opencode/skills
#   ./install.sh -y         # no preguntar
#   ./install.sh -y --global --kits dotnet,aspnet,sql-server,react,js,postgresql,flutter,git,planning,design,devops,agent,sputnik
#   ./install.sh --list-kits   # ver los kits disponibles
#   ./install.sh -y --global --target opencode,agents,pi   # instalar skills en varios destinos
#   ./install.sh --list-targets   # ver los destinos disponibles

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
AGENT_DIR="$CONFIG_DIR/agent"

GLOBAL=0
YES=0
DO_AGENTS=0
DO_SKILLS=0
KITS=""
TARGETS="opencode"

ALL_KITS="agent aspnet design devops docs dotnet flutter git js nodejs planning ponytail postgresql productivity python-ai-intel python react security sputnik sql-server"

# Devuelve la carpeta de skills para un destino ("opencode", "agents" o "pi").
# "opencode" es el destino de siempre; "agents" y "pi" son directorios
# universales que otros clientes (npx skills / Eve / PromptScript, y el
# cliente "pi") tambien leen.
target_path() {
    case "$1" in
        opencode) echo "$CONFIG_DIR/skills" ;;
        agents)   echo "$HOME/.agents/skills" ;;
        pi)       echo "$HOME/.pi/agent/skills" ;;
        *) echo "Destino desconocido: '$1'. Usa --list-targets para ver los destinos disponibles." >&2; exit 1 ;;
    esac
}

while [[ $# -gt 0 ]]; do
    arg="$1"
    case "$arg" in
        --global|-g) GLOBAL=1 ;;
        --yes|-y|-Y) YES=1 ;;
        --agents|-a) DO_AGENTS=1 ;;
        --skills|-s) DO_SKILLS=1 ;;
        --kits=*) KITS="${arg#--kits=}" ;;
        --kits|-k) shift; KITS="${1:-}" ;;
        --list-kits) tr ' ' '\n' <<< "$ALL_KITS" | sort; exit 0 ;;
        --target=*) TARGETS="${arg#--target=}" ;;
        --target|-t) shift; TARGETS="${1:-}" ;;
        --list-targets) for t in opencode agents pi; do echo "$t -> $(target_path "$t")"; done; exit 0 ;;
        *) echo "Argumento desconocido: $arg" >&2; exit 1 ;;
    esac
    shift
done

# Devuelve 0 (exito) si $1 (nombre de carpeta de skill) pertenece a alguno de los
# kits en $KITS (lista separada por comas). "python" excluye "python-ai-intel-*"
# (que es su propio kit); "security" agrupa skills sueltas sin prefijo comun.
skill_in_kits() {
    local name="$1"
    local kit
    IFS=',' read -ra kit_list <<< "$KITS"
    for kit in "${kit_list[@]}"; do
        if ! grep -qw "$kit" <<< "$ALL_KITS"; then
            echo "Kit desconocido: '$kit'. Usa --list-kits para ver los kits disponibles." >&2
            exit 1
        fi
        case "$kit" in
            security)
                case "$name" in
                    application-security|compliance-governance|cryptography-secrets|detection-response|devsecops|identity-access-management|infrastructure-security|secure-architecture|security-fundamentals|vulnerability-management)
                        return 0 ;;
                esac
                ;;
            python)
                [[ "$name" == python-* && "$name" != python-ai-intel-* ]] && return 0
                ;;
            ponytail)
                [[ "$name" == "ponytail" || "$name" == ponytail-* ]] && return 0
                ;;
            *)
                [[ "$name" == "$kit" || "$name" == "$kit"-* ]] && return 0
                ;;
        esac
    done
    return 1
}

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
        if [[ -f "$AGENT_DIR/build.md" ]]; then
            echo "Incluye build.md: override del agente build con reglas de orquestacion de subagentes."
        fi
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
    IFS=',' read -ra target_list <<< "$TARGETS"
    TARGET_DIRS=()
    for t in "${target_list[@]}"; do
        TARGET_DIRS+=("$(target_path "$t")")
    done
    if confirm "Copiar skills a ${TARGET_DIRS[*]}?"; then
        for SKILL_DIR in "${TARGET_DIRS[@]}"; do
            mkdir -p "$SKILL_DIR"
            TOTAL=0
            COPIED=0
            for dir in "$SRC_SKILLS"/*/; do
                name="$(basename "$dir")"
                TOTAL=$((TOTAL + 1))
                if [[ -z "$KITS" ]] || skill_in_kits "$name"; then
                    cp -r "$dir" "$SKILL_DIR/"
                    COPIED=$((COPIED + 1))
                fi
            done
            echo "Skills instaladas en $SKILL_DIR ($COPIED de $TOTAL)"
        done
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
