# opencode-skills

Conjunto de **154 skills** y **21 agentes** para [opencode](https://opencode.ai), agrupados por kits: .NET, ASP.NET Core, SQL Server, PostgreSQL, Python, Node.js, React, Flutter, JavaScript, seguridad, DevOps, Git, planeación, diseño y más.

## Instalación

### 1. Skills (vía npx)

Usa el CLI [skills](https://www.npmjs.com/package/skills):

```bash
# Listar skills disponibles (opcional)
npx skills add Magh97/opencode-skills --list

# Instalar todas las skills en opencode (global)
npx skills add Magh97/opencode-skills --all -g -a opencode -y

# Instalar solo algunas skills
npx skills add Magh97/opencode-skills --skill dotnet-core --skill dotnet-ef-core -g -a opencode -y
```

### 2. Agentes

El CLI `npx skills add` solo instala skills. Usa el script de instalación del repo:

**Windows (PowerShell):**
```powershell
./install.ps1 -Yes
```

**macOS / Linux:**
```bash
./install.sh -y
```

Los scripts copian `.opencode/agent/*.md` a `~/.config/opencode/agent/`. Para copiar también las skills a la carpeta global de opencode usa `-Global` (Windows) o `--global` (macOS/Linux).

### 3. Reiniciar

Reinicia opencode para que cargue las skills y agentes nuevos.

## Agentes incluidos

| Modo | Agentes |
|------|---------|
| **primary** | `sputnik`, `security`, `devops`, `git`, `code-review` |
| **all** | `docs`, `planning`, `design`, `ui`, `business-planning` |
| **subagent** | `dotnet`, `aspnet`, `sqlserver`, `postgres`, `js`, `react`, `node`, `python`, `python-ai-intel`, `flutter` |

## Orquestación

`build` (agente por defecto) delega automáticamente en subagentes según su `description` cuando la tarea coincide con sus keywords. El repo incluye `.opencode/agent/build.md`, un override de `build` con reglas explícitas de orquestación: qué subagente lanzar ante qué keywords y qué no delegar.

Los agentes `primary` (`sputnik`, `security`, `devops`, `git`, `code-review`) NO se delegan vía task — se activan con **Tab** o **@-mención**. Los agentes `all` (`docs`, `planning`, `design`, `ui`, `business-planning`) se pueden abrir directo y a la vez son delegables por otros agentes vía task. `business-planning` es un orquestador: genera el plan de negocio (12 secciones) y delega a `planning`, `design` y `docs` para producir la estructura teórica completa del proyecto.

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
