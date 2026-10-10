#!/usr/bin/env bash
set -euo pipefail

# Instala los agentes y skills de opencode-skills en la config global de opencode.
#
# Uso:
#   ./install.sh                  # solo agentes
#   ./install.sh --global         # agentes + skills en ~/.config/opencode/skills
#   ./install.sh -y --global --kits dotnet,react,sql-server
#   ./install.sh -y --global --target opencode,agents,pi
#   ./install.sh --list-kits      # kits disponibles (fuente: .opencode/kits.tsv)
#   ./install.sh --list-targets   # destinos disponibles
#   ./install.sh -y --global --dry-run    # muestra que se copiaria, sin tocar nada
#   ./install.sh -y --global --prune      # ademas borra skills instaladas que ya no existen en el repo
#   ./install.sh -y --uninstall           # borra solo lo instalado desde este repo (agentes + skills)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
AGENT_DIR="$CONFIG_DIR/agent"
KITS_FILE="$SCRIPT_DIR/.opencode/kits.tsv"

GLOBAL=0
YES=0
DO_AGENTS=0
DO_SKILLS=0
KITS=""
TARGETS="opencode"
DRY_RUN=0
PRUNE=0
UNINSTALL=0

# Destino -> carpeta de skills. "opencode" es el destino de siempre; "agents" y
# "pi" son directorios universales que otros clientes tambien leen.
target_path() {
    case "$1" in
        opencode) echo "$CONFIG_DIR/skills" ;;
        agents)   echo "$HOME/.agents/skills" ;;
        pi)       echo "$HOME/.pi/agent/skills" ;;
        *) echo "Destino desconocido: '$1'. Usa --list-targets para ver los destinos disponibles." >&2; exit 1 ;;
    esac
}

list_kits() {
    awk -F'\t' '!/^#/ && $1 != "" { print $1 }' "$KITS_FILE" | sort
}

kit_exists() {
    awk -F'\t' -v k="$1" '$1 == k { found = 1 } END { exit(found ? 0 : 1) }' "$KITS_FILE"
}

# Devuelve 0 si $1 (nombre de carpeta) pertenece al kit $2, segun .opencode/kits.tsv.
kit_matches() {
    local kit="$1" name="$2"
    awk -F'\t' -v kit="$kit" -v name="$name" '
        $1 != kit { next }
        {
            matched = 0
            if ($4 != "") { n = split($4, a, ","); for (i = 1; i <= n; i++) if (a[i] == name) matched = 1 }
            if ($2 != "") {
                n = split($2, p, ",")
                for (i = 1; i <= n; i++) {
                    if (name != p[i] && index(name, p[i]) != 1) continue
                    skip = 0
                    if ($3 != "") { m = split($3, e, ","); for (j = 1; j <= m; j++) if (index(name, e[j]) == 1) skip = 1 }
                    if (!skip) matched = 1
                }
            }
            exit
        }
        END { exit(matched ? 0 : 1) }
    ' "$KITS_FILE"
}

skill_in_kits() {
    local name="$1" kit
    IFS=',' read -ra kit_list <<< "$KITS"
    for kit in "${kit_list[@]}"; do
        if ! kit_exists "$kit"; then
            echo "Kit desconocido: '$kit'. Usa --list-kits para ver los kits disponibles." >&2
            exit 1
        fi
        kit_matches "$kit" "$name" && return 0
    done
    return 1
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
        --list-kits) list_kits; exit 0 ;;
        --target=*) TARGETS="${arg#--target=}" ;;
        --target|-t) shift; TARGETS="${1:-}" ;;
        --list-targets) for t in opencode agents pi; do echo "$t -> $(target_path "$t")"; done; exit 0 ;;
        --dry-run) DRY_RUN=1 ;;
        --prune) PRUNE=1 ;;
        --uninstall) UNINSTALL=1 ;;
        *) echo "Argumento desconocido: $arg" >&2; exit 1 ;;
    esac
    shift
done

if [[ ! -f "$KITS_FILE" ]]; then
    echo "Error: no existe $KITS_FILE (fuente de kits)." >&2
    exit 1
fi

# --kits implica --global: el filtro solo aplica a skills copiadas localmente
if [[ -n "$KITS" && $GLOBAL -eq 0 ]]; then
    GLOBAL=1
fi

if [[ $DO_AGENTS -eq 0 && $DO_SKILLS -eq 0 ]]; then
    DO_AGENTS=1
    if [[ $GLOBAL -eq 1 ]]; then DO_SKILLS=1; fi
fi

# --uninstall implica agentes + skills en modo global
if [[ $UNINSTALL -eq 1 ]]; then
    DO_AGENTS=1
    DO_SKILLS=1
    GLOBAL=1
fi

confirm() {
    if [[ $YES -eq 1 || $DRY_RUN -eq 1 ]]; then return 0; fi
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
    if [[ $UNINSTALL -eq 1 ]]; then
        if confirm "Borrar $COUNT agentes instalados desde este repo en $AGENT_DIR?"; then
            for f in "$SRC_AGENTS"/*.md; do
                name="$(basename "$f")"
                if [[ $DRY_RUN -eq 1 ]]; then echo "[dry-run] rm -f $AGENT_DIR/$name"; else rm -f "$AGENT_DIR/$name"; fi
            done
            echo "Agentes desinstalados de $AGENT_DIR"
        fi
    elif confirm "Instalar $COUNT agentes en $AGENT_DIR?"; then
        if [[ $DRY_RUN -eq 1 ]]; then
            echo "[dry-run] crearia $AGENT_DIR y copiaria $COUNT agentes"
        else
            mkdir -p "$AGENT_DIR"
            cp -f "$SRC_AGENTS"/*.md "$AGENT_DIR/"
            echo "Agentes instalados en $AGENT_DIR"
            echo "Agentes: $(ls "$AGENT_DIR"/*.md | xargs -n1 basename | sed 's/\.md$//' | tr '\n' ', ')"
            if [[ -f "$AGENT_DIR/build.md" ]]; then
                echo "Incluye build.md: override del agente build con reglas de orquestacion de subagentes."
            fi
        fi
    else
        echo "Instalacion de agentes cancelada."
        DO_AGENTS=0
    fi
fi

if [[ $DO_SKILLS -eq 1 && ($GLOBAL -eq 1 || $UNINSTALL -eq 1) ]]; then
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
    ACTION="Copiar skills a"
    [[ $UNINSTALL -eq 1 ]] && ACTION="Borrar skills instaladas desde este repo de"
    if confirm "$ACTION ${TARGET_DIRS[*]}?"; then
        for SKILL_DIR in "${TARGET_DIRS[@]}"; do
            TOTAL=0
            COPIED=0
            if [[ $UNINSTALL -eq 0 && $DRY_RUN -eq 0 ]]; then mkdir -p "$SKILL_DIR"; fi
            for dir in "$SRC_SKILLS"/*/; do
                name="$(basename "$dir")"
                TOTAL=$((TOTAL + 1))
                if [[ -z "$KITS" ]] || skill_in_kits "$name"; then
                    if [[ $UNINSTALL -eq 1 ]]; then
                        if [[ $DRY_RUN -eq 1 ]]; then echo "[dry-run] rm -rf $SKILL_DIR/$name"; else rm -rf "${SKILL_DIR:?}/$name"; fi
                    else
                        if [[ $DRY_RUN -eq 1 ]]; then echo "[dry-run] cp -r skills/$name -> $SKILL_DIR/"; else cp -r "$dir" "$SKILL_DIR/"; fi
                    fi
                    COPIED=$((COPIED + 1))
                fi
            done
            if [[ $UNINSTALL -eq 1 ]]; then
                echo "Skills desinstaladas de $SKILL_DIR ($COPIED de $TOTAL)"
            else
                echo "Skills instaladas en $SKILL_DIR ($COPIED de $TOTAL)"
            fi
            if [[ $PRUNE -eq 1 && $UNINSTALL -eq 0 && -d "$SKILL_DIR" ]]; then
                for installed in "$SKILL_DIR"/*/; do
                    [[ -d "$installed" ]] || continue
                    iname="$(basename "$installed")"
                    if [[ ! -d "$SRC_SKILLS/$iname" ]]; then
                        if [[ $DRY_RUN -eq 1 ]]; then echo "[dry-run] prune $installed"; else rm -rf "$installed"; echo "prune: $iname"; fi
                    fi
                done
            fi
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
