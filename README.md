# opencode-skills

Conjunto de **153 skills** y **20 agentes** para [opencode](https://opencode.ai), agrupados por kits: .NET, ASP.NET Core, SQL Server, PostgreSQL, Python, Node.js, React, Flutter, JavaScript, seguridad, DevOps, Git, planeación, diseño y más.

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
| **primary** | `docs`, `planning`, `design`, `sputnik`, `security`, `devops`, `git`, `code-review` |
| **all** | `ui` |
| **subagent** | `dotnet`, `aspnet`, `sqlserver`, `postgres`, `js`, `react`, `node`, `python`, `python-ai-intel`, `flutter` |

## Orquestación

`build` (agente por defecto) delega automáticamente en subagentes según su `description` cuando la tarea coincide con sus keywords. El repo incluye `.opencode/agent/build.md`, un override de `build` con reglas explícitas de orquestación: qué subagente lanzar ante qué keywords y qué no delegar.

Los agentes `primary` (`docs`, `planning`, `design`, `sputnik`, `security`, `devops`, `git`, `code-review`) NO se delegan vía task — se activan con **Tab** o **@-mención**. `ui` es `mode: all`: se puede abrir directo (cuestionario de diseño) y a la vez es delegable por otros agentes vía task.

Para afinar permisos de delegación a nivel global, copia el patrón de `opencode.example.json` a tu `opencode.json` (p.ej. pedir confirmación antes de lanzar `sputnik`).

## Estructura

```
skills/               # 153 skills (<nombre>/SKILL.md)
.opencode/agent/      # 20 agentes opencode (<nombre>.md)
install.ps1           # Instalador de agentes (Windows)
install.sh            # Instalador de agentes (macOS/Linux)
opencode.example.json # Ejemplo de config global (permisos de delegación)
```

## Desarrollo

- Las skills se definen en `skills/<nombre>/SKILL.md` con frontmatter YAML (`name` + `description`).
- Los agentes se definen en `.opencode/agent/<nombre>.md` con frontmatter (`description`, `mode`).
- Para validar el frontmatter de todas las skills, cualquier SKILL.md que no empiece con `---` ni tenga `name`/`description` no será descubrible.
