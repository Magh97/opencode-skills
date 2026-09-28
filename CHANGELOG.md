# Changelog

Todos los cambios notables de este proyecto se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.1.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

### Added
- Agregado archivo `LICENSE` (MIT).
- Agregado `.gitignore` con exclusiones para OS, editores, installs locales y caches.
- Agregado `.editorconfig` para consistencia de formato (UTF-8, LF, 2-space indent).
- Agregado `CONTRIBUTING.md` con convenciones de skills, agentes y verificación local.
- Agregado workflow de GitHub Actions `.github/workflows/verify.yml` para ejecutar `verify-install.js` en cada push/PR.
- Agregado `test-install.sh` para validar el instalador bash en CI.
- Scripts de `docs-pipeline` ahora tienen permisos ejecutables (`+x`).

### Changed
- **install.sh**: `--kits` ahora implica `--global` automáticamente.
- **install.ps1**: `-Kits` ahora implica `-Global` automáticamente.
- Recortadas 18 descripciones de skills que excedían 500 caracteres para mejor compatibilidad con clientes de agentes:
  `sputnik-core`, `ponytail`, `agent-business-planning`, `sputnik-jira`, `docs-pipeline`, `productivity-code-review`, `agent-anti-slop-designer-experimental`, `sql-server-integration`, `nodejs-prisma`, `productivity-spec`, `productivity-deps`, `productivity-onboard`, `nodejs-drizzle`, `sputnik-retro`, `sputnik-excel`, `productivity-refactor`, `productivity-scaffold`, `design-core`.

### Fixed
- Normalización de permisos en scripts de `docs-pipeline`.

## [1.0.0] - 2025-09-26

### Added
- Release inicial con **155 skills** y **22 agentes**.
- Kits: .NET, ASP.NET Core, SQL Server, PostgreSQL, Python, Node.js, React, Flutter, JavaScript, seguridad, DevOps, Git, planeación, diseño, documentación, productividad, Sputnik, Ponytail.
- Instaladores: `install.sh` (bash) y `install.ps1` (PowerShell) con soporte de `--kits` y `--target`.
- Script de verificación: `verify-install.js` con validación de frontmatter, referencias cruzadas y hashing de sincronía.
