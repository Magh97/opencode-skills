# opencode-skills

Conjunto de **133 skills** y **22 agentes** para [opencode](https://opencode.ai), agrupados por kits: .NET/ASP.NET Core, SQL Server, PostgreSQL, Python, Node.js, React, Flutter, JavaScript, seguridad, DevOps, Git, planeación, diseño, documentación y más.

## Instalación

### 1. Vía recomendada: script del repo (skills + agentes)

**Windows (PowerShell):**
```powershell
# Instalar agentes (22) en ~/.config/opencode/agent/
./install.ps1 -Yes

# Instalar agentes + skills en ~/.config/opencode/
./install.ps1 -Yes -Global

# Instalar solo los kits que te interesan (ej. stack .NET + React + SQL Server)
./install.ps1 -Yes -Global -Kits dotnet,react,sql-server,js,postgresql

# Ver los kits disponibles
./install.ps1 -ListKits

# Instalar las skills tambien en directorios universales de otros clientes de agentes
./install.ps1 -Yes -Global -Target opencode,agents,pi

# Simular la instalacion sin escribir nada / limpiar skills viejas / desinstalar
./install.ps1 -Yes -Global -DryRun
./install.ps1 -Yes -Global -Prune
./install.ps1 -Yes -Uninstall
```

**macOS / Linux:**
```bash
# Instalar agentes (22)
./install.sh -y

# Instalar agentes + skills con --global
./install.sh -y --global

# Instalar solo los kits que te interesan
./install.sh -y --global --kits dotnet,react,sql-server,js,postgresql

# Ver los kits disponibles
./install.sh --list-kits

# Instalar las skills tambien en directorios universales de otros clientes de agentes
./install.sh -y --global --target opencode,agents,pi

# Simular / limpiar / desinstalar
./install.sh -y --global --dry-run
./install.sh -y --global --prune
./install.sh -y --uninstall
```

Kits disponibles (fuente única: `.opencode/kits.tsv`): `agent`, `aspnet`, `design`, `devops`, `docs`, `dotnet`, `flutter`, `git`, `js`, `nodejs`, `planning`, `ponytail`, `postgresql`, `productivity`, `python`, `python-ai-intel`, `react`, `security`, `sputnik`, `sql-server`.

- `dotnet` incluye las skills `dotnet-*` **y** `aspnet-*` (un solo kit para todo el stack .NET).
- `aspnet` se mantiene como alias por compatibilidad: con él instalas solo las `aspnet-*`.
- `--kits`/`-Kits` solo filtra skills; los agentes siempre se instalan completos.

Destinos disponibles para `-Target`/`--target` (solo afecta a dónde van las **skills**; los agentes siempre van a `~/.config/opencode/agent`, específico de opencode):

| Destino | Ruta | Uso |
|---|---|---|
| `opencode` (default) | `~/.config/opencode/skills` | opencode |
| `agents` | `~/.agents/skills` | Directorio universal usado por otros clientes (Eve, PromptScript, etc.) |
| `pi` | `~/.pi/agent/skills` | Cliente pi |

Puedes pasar varios a la vez separados por coma. Nota: `agents`/`pi` son directorios *globales* del usuario (`~/.agents/`, `~/.pi/`) — no tienen relación con el bug del CLI `npx skills` descrito abajo, que crea una carpeta `.agents/` *dentro del repo* por error.

Esta vía es la **verificada**: copia exactamente lo que hay en el repo y garantiza sincronía entre repo y config. Puedes comprobar la instalación con el script del repo:

```bash
node .opencode/verify-install.js                 # verifica ~/.config/opencode
node .opencode/verify-install.js --repo-only     # solo lint del repo (sin instalación)
node .opencode/verify-install.js --config <dir>  # verifica una instalación en otra ruta
```

### 2. Vía alternativa: CLI `npx skills` (⚠️ solo skills, con bug conocido)

El CLI [skills](https://www.npmjs.com/package/skills) instala solo skills (no agentes):

```bash
# Listar skills disponibles (opcional)
npx skills add Magh97/opencode-skills --list

# Instalar todas las skills en opencode (global)
npx skills add Magh97/opencode-skills --all -g -a opencode -y

# Instalar solo algunas skills
npx skills add Magh97/opencode-skills --skill dotnet-core --skill dotnet-ef-core -g -a opencode -y
```

> **BUG CONOCIDO:** El CLI `npx skills` **no funciona de forma confiable para opencode**:
> - Sin `OPENCODE_CLIENT` (cuando se ejecuta desde una shell normal) no detecta opencode como agente: instala para otros agentes (Eve, PromptScript, etc.) y **no** escribe en `~/.config/opencode/skills/`.
> - Con `OPENCODE_CLIENT` (cuando corre dentro de opencode) **ignora `$USERPROFILE`**: instala en el directorio de trabajo (crea `.agents/`, `skills-lock.json`) y, si se ejecuta desde el repo, puede **sobrescribir el config real de opencode con line endings LF** y reemplazar los directorios de `skills/` por **junctions** (rompiendo el working tree de git).
> - **Solución:** usa `install.ps1 -Global` / `install.sh -y --global` (vía 1). Si detectas archivos movidos a `.agents/`, `.claude/`, `agent/` o junctions en `skills/`, restaura con `git checkout HEAD -- skills/` y vuelve a correr `install.ps1 -Global`.

### 3. Reiniciar

Reinicia opencode para que cargue las skills y agentes nuevos.

## Cómo se cargan las skills

- opencode inyecta en el prompt **solo el nombre y la descripción** de las skills auto-invocables (las que no tienen `disable-model-invocation: true`). Este repo mantiene ese conjunto en **25 skills y ~5.7k chars (~1.4k tokens)**, para que el coste por request sea bajo.
- Las skills con `disable-model-invocation: true` (sub-skills de dominio) no se anuncian al modelo pero siguen siendo invocables: los agentes las cargan por instrucción, y tú puedes forzarlas con **@-mención** (`@dotnet-ef-core`) o desde el selector `/skills`.
- El detalle largo de una skill vive en `references/`, que opencode no carga hasta que la skill lo pide (progressive disclosure). Así una skill de 100 líneas puede arrastrar 900 líneas de referencia sin inflar el contexto.

## Agentes incluidos

| Modo | Agentes |
|------|---------|
| **primary** | `sputnik`, `security`, `devops`, `git`, `code-review`, `qna` |
| **all** | `docs`, `planning`, `design`, `ui`, `business-planning` |
| **subagent** | `dotnet`, `aspnet`, `sqlserver`, `postgres`, `js`, `react`, `node`, `python`, `python-ai-intel`, `flutter` |

Además, `.opencode/agent/build.md` es un override del agente `build` con reglas de orquestación (22 archivos de agente en total).

## Orquestación

`build` (agente por defecto) delega automáticamente en subagentes según su `description` cuando la tarea coincide con sus keywords. El repo incluye `.opencode/agent/build.md`, un override de `build` con reglas explícitas de orquestación: qué subagente lanzar ante qué keywords y qué no delegar.

Los agentes `primary` (`sputnik`, `security`, `devops`, `git`, `code-review`, `qna`) NO se delegan vía task — se activan con **Tab** o **@-mención**. Los agentes `all` (`docs`, `planning`, `design`, `ui`, `business-planning`) se pueden abrir directo y a la vez son delegables por otros agentes vía task. `business-planning` es un orquestador: genera el plan de negocio (12 secciones) y delega a `planning`, `design` y `docs` para producir la estructura teórica completa del proyecto. `qna` es el agente de Q&A: responde dudas de desarrollo en cualquier stack (usando las skills del dominio), preguntas sobre el proyecto/código actual y preguntas sobre las propias skills y agentes del kit, sin modificar nada (read-only).

Para afinar permisos de delegación a nivel global, copia el patrón de `opencode.example.json` a tu `opencode.json` (p.ej. pedir confirmación antes de lanzar `sputnik`).

## Estructura

```
skills/               # 133 skills (<nombre>/SKILL.md + references/ y scripts/ opcionales)
.opencode/agent/      # 22 agentes opencode (<nombre>.md)
.opencode/kits.tsv    # fuente única de kits (la leen ambos instaladores y el verificador)
.opencode/verify-install.js # lint del repo + verificación de sincronía repo <-> config
install.ps1           # Instalador (Windows): -Global, -Kits, -Target, -DryRun, -Prune, -Uninstall
install.sh            # Instalador (macOS/Linux): --global, --kits, --target, --dry-run, --prune, --uninstall
test-install.sh       # Test suite del instalador bash
opencode.example.json # Ejemplo de config global (permisos de delegación)
```

## Desarrollo

- Las skills se definen en `skills/<nombre>/SKILL.md` con frontmatter YAML (`name` + `description`, y `disable-model-invocation: true` para sub-skills).
- Los campos extra de opencode (`requires-devkits`, etc.) van dentro de `metadata:`; opencode ignora los campos desconocidos de primer nivel.
- Una skill puede incluir subdirectorios opcionales: `references/` para documentación de apoyo y `scripts/` para utilidades ejecutables. El instalador copia la carpeta completa (`Copy-Item -Recurse` / `cp -R`), y `verify-install.js` hashea **todos** los archivos del skill, no solo `SKILL.md`, para que la deriva en un `references/` o un `scripts/` no pase desapercibida.
- Los agentes se definen en `.opencode/agent/<nombre>.md` con frontmatter (`description`, `mode`).
- Antes de commitear: `node .opencode/verify-install.js --repo-only` (lint del repo) y `bash test-install.sh` (instalador). El lint comprueba frontmatter, referencias cruzadas, cobertura de kits, presupuesto de descripciones auto-invocables y consistencia del README. Ver [CONTRIBUTING.md](CONTRIBUTING.md).
