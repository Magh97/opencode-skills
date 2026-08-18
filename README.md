# opencode-skills

Conjunto de **154 skills** y **22 agentes** para [opencode](https://opencode.ai), agrupados por kits: .NET, ASP.NET Core, SQL Server, PostgreSQL, Python, Node.js, React, Flutter, JavaScript, seguridad, DevOps, Git, planeación, diseño y más.

## Instalación

### 1. Vía recomendada: script del repo (skills + agentes)

**Windows (PowerShell):**
```powershell
# Instalar agentes (21) en ~/.config/opencode/agent/
./install.ps1 -Yes

# Instalar agentes + skills (154) en ~/.config/opencode/
./install.ps1 -Yes -Global
```

**macOS / Linux:**
```bash
# Instalar agentes (21)
./install.sh -y

# Instalar agentes + skills (154) con -Global
./install.sh -y --global
```

Esta vía es la **verificada**: copia exactamente lo que hay en el repo y garantiza sincronía entre repo y config. Puedes comprobar la instalación con el script del repo:

```bash
node .opencode/verify-install.js                 # verifica ~/.config/opencode
node .opencode/verify-install.js --config <dir>  # verifica una instalación en otra ruta (sistema limpio)
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

## Agentes incluidos

| Modo | Agentes |
|------|---------|
| **primary** | `sputnik`, `security`, `devops`, `git`, `code-review`, `qna` |
| **all** | `docs`, `planning`, `design`, `ui`, `business-planning` |
| **subagent** | `dotnet`, `aspnet`, `sqlserver`, `postgres`, `js`, `react`, `node`, `python`, `python-ai-intel`, `flutter` |

## Orquestación

`build` (agente por defecto) delega automáticamente en subagentes según su `description` cuando la tarea coincide con sus keywords. El repo incluye `.opencode/agent/build.md`, un override de `build` con reglas explícitas de orquestación: qué subagente lanzar ante qué keywords y qué no delegar.

Los agentes `primary` (`sputnik`, `security`, `devops`, `git`, `code-review`, `qna`) NO se delegan vía task — se activan con **Tab** o **@-mención**. Los agentes `all` (`docs`, `planning`, `design`, `ui`, `business-planning`) se pueden abrir directo y a la vez son delegables por otros agentes vía task. `business-planning` es un orquestador: genera el plan de negocio (12 secciones) y delega a `planning`, `design` y `docs` para producir la estructura teórica completa del proyecto. `qna` es el agente de Q&A: responde dudas de desarrollo en cualquier stack (usando las skills del dominio), preguntas sobre el proyecto/código actual y preguntas sobre las propias skills y agentes del kit, sin modificar nada (read-only).

Para afinar permisos de delegación a nivel global, copia el patrón de `opencode.example.json` a tu `opencode.json` (p.ej. pedir confirmación antes de lanzar `sputnik`).

## Estructura

```
skills/               # 154 skills (<nombre>/SKILL.md)
.opencode/agent/      # 21 agentes opencode (<nombre>.md)
install.ps1           # Instalador de agentes (Windows)
install.sh            # Instalador de agentes (macOS/Linux)
opencode.example.json # Ejemplo de config global (permisos de delegación)
```

## Desarrollo

- Las skills se definen en `skills/<nombre>/SKILL.md` con frontmatter YAML (`name` + `description`).
- Los agentes se definen en `.opencode/agent/<nombre>.md` con frontmatter (`description`, `mode`).
- Para validar el frontmatter de todas las skills, cualquier SKILL.md que no empiece con `---` ni tenga `name`/`description` no será descubrible.
