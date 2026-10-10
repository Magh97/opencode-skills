# Changelog

Todos los cambios notables de este proyecto se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.1.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

### Added
- Agregado archivo `LICENSE` (MIT).
- Agregado `.gitignore` con exclusiones para OS, editores, installs locales y caches.
- Agregado `.editorconfig` para consistencia de formato (UTF-8, LF, 2-space indent).
- Agregado `.gitattributes` (`* text=auto eol=lf`) para evitar churn de CRLF entre plataformas.
- Agregado `CONTRIBUTING.md` con convenciones de skills, agentes y verificación local.
- Agregado workflow de GitHub Actions `.github/workflows/verify.yml` para ejecutar `verify-install.js` en cada push/PR.
- Agregado `test-install.sh` para validar el instalador bash en CI.
- Scripts de `docs-pipeline` ahora tienen permisos ejecutables (`+x`); `agent-anti-slop-designer/scripts/check-slop.py` también.
- Agregado `.opencode/kits.tsv` como **fuente única de kits** para `install.sh`, `install.ps1` y `verify-install.js`.
- Nuevos flags de instalador: `--dry-run`/`-DryRun`, `--prune`/`-Prune` y `--uninstall`/`-Uninstall`.
- `verify-install.js`: modo `--repo-only` para CI, lint de descripciones, campos de frontmatter, nombres duplicados, cobertura de kits, consistencia del README y presupuesto de auto-invocables.
- `test-install.sh`: 6 tests nuevos (list-kits, kit desconocido, dry-run, prune, uninstall, target pi).
- Progressive disclosure: referencias largas movidas a `references/` en `dotnet-patterns`, `dotnet-solid`, `dotnet-clean-code`, `dotnet-api`, `dotnet-ef-core`, `react-antdesign`, `nodejs-database`, `devsecops`, `python-ai-intel-core` y `agent-anti-slop-designer`.

### Changed
- **install.sh**: `--kits` ahora implica `--global` automáticamente.
- **install.ps1**: `-Kits` ahora implica `-Global` automáticamente.
- Recortadas 18 descripciones de skills que excedían 500 caracteres para mejor compatibilidad con clientes de agentes:
  `sputnik-core`, `ponytail`, `agent-business-planning`, `sputnik-jira`, `docs-pipeline`, `productivity-code-review`, `agent-anti-slop-designer-experimental`, `sql-server-integration`, `nodejs-prisma`, `productivity-spec`, `productivity-deps`, `productivity-onboard`, `nodejs-drizzle`, `sputnik-retro`, `sputnik-excel`, `productivity-refactor`, `productivity-scaffold`, `design-core`.
- **Reducción de 155 a 133 skills** fusionando duplicados y moviendo contenido a `references/`:
  - `agent-*` (8) → modos compactos dentro de `productivity-onboard`, `productivity-spec`, `planning-core`, `design-core`, `productivity-docs` + `agent-business-planning` y `agent-anti-slop-designer`.
  - `agent-anti-slop-designer-experimental` → `agent-anti-slop-designer/references/experimental.md` (modo experimental).
  - `ponytail-*` (5 modos) → `ponytail/references/{audit,debt,gain,help,review}.md`.
  - `nodejs-prisma` y `nodejs-drizzle` → `nodejs-database/references/`.
  - `devops-security` → `devsecops/references/tooling.md`.
  - `aspnet-ef-core`, `aspnet-testing`, `aspnet-performance`, `aspnet-web-api` → `references/aspnet.md` de sus equivalentes `dotnet-*`; el kit `dotnet` ahora incluye `aspnet-*` (el kit `aspnet` queda como alias).
  - `python-ai-intel-{npu,openvino,pytorch-xpu,profiling}` → `python-ai-intel-core/references/`.
- Campos `requires-devkits` movidos a `metadata.requires-devkits` (opencode ignora los campos de primer nivel desconocidos).
- `argument-hint` eliminado de `ponytail`; sus disparadores ahora son `@ponytail` + nivel/modo.
- Reducidas las skills auto-invocables de 45 a 25 y las descripciones auto-invocables de ~17.4k a ~5.7k chars (~1.4k tokens por request).
- README y CONTRIBUTING actualizados a los conteos, kits y flujos reales.

### Fixed
- Normalización de permisos en scripts de `docs-pipeline`.
- **CI roto**: `verify.yml` ejecutaba `verify-install.js` sin instalación local y fallaba siempre; ahora usa `--repo-only` + instalación en `HOME` limpio + `test-install.sh` + chequeo de bits ejecutables.
- `install.sh` creaba la carpeta destino tarde: la primera skill se copiaba aplanada sobre `skills/` en lugar de dentro.

## [1.0.0] - 2025-09-26

### Added
- Release inicial con **155 skills** y **22 agentes**.
- Kits: .NET, ASP.NET Core, SQL Server, PostgreSQL, Python, Node.js, React, Flutter, JavaScript, seguridad, DevOps, Git, planeación, diseño, documentación, productividad, Sputnik, Ponytail.
- Instaladores: `install.sh` (bash) y `install.ps1` (PowerShell) con soporte de `--kits` y `--target`.
- Script de verificación: `verify-install.js` con validación de frontmatter, referencias cruzadas y hashing de sincronía.
