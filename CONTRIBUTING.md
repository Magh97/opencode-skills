# Contributing to opencode-skills

Gracias por considerar contribuir. Este repo contiene **133 skills** y **22 agentes** para opencode; mantener la calidad y consistencia a esta escala requiere seguir unas pocas reglas simples.

## Cómo contribuir

1. **Fork** el repo y crea una rama (`git checkout -b feature/nueva-skill`).
2. **Implementa** tus cambios siguiendo las convenciones de abajo.
3. **Verifica** con `node .opencode/verify-install.js --repo-only` y `bash test-install.sh` antes de pushear.
4. **Abre un PR** con una descripción clara del cambio.

## Convenciones de skills

### Estructura

```
skills/<nombre-kebab-case>/
  SKILL.md                    # obligatorio
  references/                 # opcional: documentación de apoyo (progressive disclosure)
  scripts/                    # opcional: utilidades ejecutables (+x en git)
```

- `SKILL.md` es la guía de decisión (idealmente <= 250 líneas). Todo catálogo/cheat-sheet largo va a `references/` y se cita con ruta relativa (ej. `references/patrones.md`).
- Los scripts de `scripts/` deben tener bit ejecutable (`git update-index --chmod=+x <archivo>`); la CI lo comprueba.

### Frontmatter obligatorio

Todo `SKILL.md` debe empezar con:

```yaml
---
name: nombre-exacto-de-la-carpeta
description: "Qué hace + cuándo usarla + keywords del usuario (<= 300 chars si es auto-invocable)."
---
```

- `name` debe coincidir **exactamente** con el nombre de la carpeta.
- **Presupuesto de descripción**: <= 300 chars para skills auto-invocables y <= 400 para las que llevan `disable-model-invocation: true`. El verificador falla por encima del máximo del spec (1024) y avisa por encima de estos límites.
- **Sé conservador con la auto-invocación**: cada skill sin `disable-model-invocation` suma su descripción al prompt de todos los requests. El repo mantiene un presupuesto de <= 30 skills auto-invocables y <= 8000 chars totales; por defecto, solo las `*-core` y los orquestadores deben ser auto-invocables.
- **Campos extra van en `metadata:`**. opencode solo lee `name`, `description`, `metadata`, `license`, `compatibility`, `allowed-tools` y `disable-model-invocation`; cualquier otro campo de primer nivel se ignora (y el verificador avisa).
- No uses emojis en el frontmatter. En el cuerpo, solo en plantillas de salida dirigidas a humanos.

### Naming

- Usa `kebab-case`: `python-fastapi`, `sql-server-core`.
- Un kit se identifica por prefijo: `dotnet-*`, `react-*`, `python-*`.
- `security` es la excepción: agrupa skills sueltas sin prefijo común (`application-security`, `cryptography-secrets`, etc.) mediante lista explícita de nombres.

### Contenido

- **Guía canónica**, no tutorial paso a paso. La skill es una hoja de ruta que el agente sigue, no un script a ejecutar literalmente.
- **Código de ejemplo** debe ser mínimo y enfocado en la decisión, no en el boilerplate.
- **Progressive disclosure**: si una sección supera ~150 líneas o es un catálogo de referencia, muévela a `references/` y deja un puntero. Así la skill no infla el contexto al cargarse.
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
# Lint del repo: frontmatter, refs cruzadas, cobertura de kits, presupuesto de descripciones, README
node .opencode/verify-install.js --repo-only

# Verifica además que la instalación en ~/.config/opencode esté sincronizada (hash MD5)
node .opencode/verify-install.js

# Test suite del instalador bash (11 tests: kits, dry-run, prune, uninstall, multi-target)
bash test-install.sh
```

Si `verify-install.js` reporta hallazgos, el PR no se mergeará. La CI ejecuta el lint, instala en un `HOME` limpio, verifica sincronía, corre `test-install.sh` y comprueba bits ejecutables.

## Kits y targets

La fuente única de kits es **`.opencode/kits.tsv`** (columnas: `kit<TAB>prefijos<TAB>prefijos-excluidos<TAB>nombres-exactos`). La leen `install.sh`, `install.ps1` y `verify-install.js`; no dupliques la lista en otro sitio.

Si agregas una skill nueva:

1. Asegúrate de que su nombre caiga en el prefijo de un kit existente o agrégala a la lista de nombres del kit `security`.
2. Corre `node .opencode/verify-install.js --repo-only`: fallará si la skill no pertenece a ningún kit o si el README no la cuenta.

Los instaladores soportan `--kits`/`-Kits`, `--target`/`-Target`, `--dry-run`/`-DryRun`, `--prune`/`-Prune` y `--uninstall`/`-Uninstall`.

## Tests de instalador

```bash
bash test-install.sh
```

Crea un `HOME` temporal, corre `install.sh` con varias combinaciones de flags y aserta el resultado (incluye `--dry-run`, `--prune`, `--uninstall` y `--target pi`).

## Preguntas

Abre un issue o pregunta en el canal de discusión del repo.
