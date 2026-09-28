# Contributing to opencode-skills

Gracias por considerar contribuir. Este repo contiene **155 skills** y **22 agentes** para opencode; mantener la calidad y consistencia a esta escala requiere seguir unas pocas reglas simples.

## Cómo contribuir

1. **Fork** el repo y crea una rama (`git checkout -b feature/nueva-skill`).
2. **Implementa** tus cambios siguiendo las convenciones de abajo.
3. **Verifica** con `node .opencode/verify-install.js` antes de pushear.
4. **Abre un PR** con una descripción clara del cambio.

## Convenciones de skills

### Estructura

```
skills/<nombre-kebab-case>/
  SKILL.md                    # obligatorio
  references/                 # opcional: docs de apoyo
  scripts/                    # opcional: utilidades ejecutables
```

### Frontmatter obligatorio

Todo `SKILL.md` debe empezar con:

```yaml
---
name: nombre-exacto-de-la-carpeta
description: "Descripción corta (250–350 chars). Qué hace, cuándo activarla, keywords del usuario."
---
```

- `name` debe coincidir **exactamente** con el nombre de la carpeta.
- `description` debe ser concisa. Si supera los 400 chars, recortar y mover detalles al cuerpo.
- No uses emojis en el frontmatter ni en el cuerpo de skills (documentos human-facing).

### Naming

- Usa `kebab-case`: `python-fastapi`, `sql-server-core`.
- Un kit se identifica por prefijo: `dotnet-*`, `react-*`, `python-*`.
- `security` es la excepción: agrupa skills sueltas sin prefijo común (`application-security`, `cryptography-secrets`, etc.).

### Contenido

- **Guía canónica**, no tutorial paso a paso. La skill es una hoja de ruta que el agente sigue, no un script a ejecutar literalmente.
- **Código de ejemplo** debe ser mínimo y enfocado en la decisión, no en el boilerplate.
- **Cross-references**: si mencionas otra skill en backticks (`` `otra-skill` ``), asegúrate de que exista en `skills/`. `verify-install.js` lo valida.

## Convenciones de agentes

```
.opencode/agent/<nombre>.md
```

Frontmatter obligatorio:

```yaml
---
description: "Qué hace el agente, cuándo activarlo, keywords."
mode: primary | all | subagent
---
```

- `primary`: agentes que el usuario activa directamente (`sputnik`, `security`, `devops`, `git`, `code-review`, `qna`).
- `all`: agentes delegables y también abribles directamente (`docs`, `planning`, `design`, `ui`, `business-planning`).
- `subagent`: agentes especializados que solo se delegan (`dotnet`, `aspnet`, `react`, `python`, etc.).

## Verificación local

```bash
# Verifica frontmatter, referencias cruzadas y consistencia repo vs config
node .opencode/verify-install.js

# Verifica contra un directorio limpio (simulación de CI)
node .opencode/verify-install.js --config /tmp/fake-config
```

Si `verify-install.js` reporta hallazgos, el PR no se mergeará.

## Kits y targets

Los installers (`install.sh`, `install.ps1`) soportan filtrado por kits (`--kits dotnet,react`) y multi-target (`--target opencode,agents,pi`). Si agregas una skill nueva:

1. Asegúrate de que el prefijo coincida con un kit existente en `$KitMap` / `ALL_KITS`.
2. Si es una skill suelta de seguridad, agrégala al case `security` en `skill_in_kits()`.

## Tests de instalador (avanzado)

Para validar que los scripts de instalación copian lo correcto:

```bash
# Linux/macOS
bash test-install.sh
```

Este script crea un directorio temporal, corre `install.sh` con varias combinaciones de flags y aserta el resultado.

## Preguntas

Abre un issue o pregunta en el canal de discusión del repo.
