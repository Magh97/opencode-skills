---
name: agent-anti-slop-designer-experimental
description: "Diseño de productos digitales vanguardistas que NO parecen hechos por IA. Arqueología del dominio, cuestionario de estilo arriesgado, exploración con mockups, design-system.md experimental con prohibiciones anti-slop, voz y microcopy, matriz de estados, accesibilidad/degradación/performance, artefactos machine-readable y auditoría con check-slop.py. Úsala cuando el usuario diga 'no quiero que parezca hecho por AI', 'diseño experimental', 'design system vanguardista', 'rompe convenciones', 'auditar anti-slop', o quiera un producto visualmente distintivo."
---

# Skill: Anti-Slop Design Architect — Edición Experimental
## Versión: 2.3 | 2026-09-25
### Propósito
Transformar ideas de aplicaciones en productos digitales que **no parezcan hechos por IA**. Esta skill prioriza el riesgo visual, la experimentación y la vanguardia sobre la seguridad. No busca "usable"; busca **memorable**. Si el resultado no hace que alguien diga "¿cómo hicieron esto?", no hemos terminado.

---

## Anatomía del Slop

El slop no es "feo": es **la mediana**. Un modelo generativo colapsa hacia lo más probable de su corpus de entrenamiento, y el resultado son las mismas decisiones: Inter, un gradiente púrpura, un hero centrado con tres tarjetas, un spinner, un empty state que dice "No data found". No es un error de un diseñador: es un sesgo estadístico.

De ahí salen las tres formas de slop que esta skill intenta evitar:

| Slop | Por qué ocurre | Antídoto |
|---|---|---|
| **De plantilla** | El corpus converge a los mismos componentes | Derivar del dominio (Fase 0.5) y prohibir explícitamente (§11) |
| **De vanguardia** | Los tokens experimentales se usan como checklist: "puse glitch, cumplí" | Derivar, no elegir; la vanguardia es consecuencia, no receta |
| **De ejecución** | El sistema se aprueba y la primera pantalla lo ignora | `check-slop.py` (Fase 6) y matriz de estados (§9.5) |

> La lista de prohibiciones no está para decorar: cada entrada existe porque es la salida por defecto de un modelo. **Lo que no se prohíbe, se genera.**

---

## Fase 0: Diagnóstico Rápido (30 segundos)

- **Si el usuario trae una idea clara** → Fase 0.5 (Arqueología del Dominio) → Fase 2 (Refinamiento de Supuestos Experimentales).
- **Si el usuario trae una idea vaga** → Fase 0.5 → Fase 1 (Cuestionario de Descubrimiento Vanguardista).
- **Si el usuario solo dice "hazme algo que no parezca AI"** → Fase 0.5 → Fase 1 completa + Fase 1.5 (Exploración Visual con Imágenes).

> La Fase 0.5 es **BLOQUEANTE y no se salta**. Un movimiento elegido de una tabla es tan de catálogo como el gradiente púrpura; la diferencia está en si se **deriva** del producto o se **elige** de una lista.

---

## Fase 0.5: Arqueología del Dominio · BLOQUEANTE

Sin código y sin cuestionario todavía. El menú de la Fase 1 es un **vocabulario**, no una solución. Antes de elegir un estilo, inventariar el material real del oficio.

Responder por escrito:

1. **¿Qué artefactos produce este dominio?** No las pantallas: los objetos reales del oficio.
   Tickets térmicos, manifiestos de carga, códigos de barras, recetas, waveforms, logs de servidor, sellos, mapas de ruta, formularios oficiales, hojas de cálculo, radiografías, partituras, planos, tickets de bolsa, actas.
2. **¿Cuáles de esos artefactos tienen una estética propia y reconocible?** Tipografía, retícula, color, tinta, textura, ancho de banda, ruido.
3. **¿Qué material o señal domina la experiencia real del usuario?** Calor, luz, sonido, peso, presión, humedad, vibración, velocidad.
4. **¿Qué se puede extraer como token?** De cada artefacto: un color, una textura, una regla tipográfica, un comportamiento, un sonido.
5. **¿Qué es decorativo y debe descartarse?** El dominio también trae ruido sin significado.

**Salida — `domain-artifacts`:**

| Artefacto real | Rasgo extraíble | Token / regla propuesta | Verdadero o decorativo |
|---|---|---|---|
| [artefacto] | [tipografía / retícula / color / textura / sonido / ritmo] | [`--token` o regla] | verdadero / decorativo |

**Regla de derivación (aplica a cada eje de la Fase 1):**
> Todo eje elegido debe poder trazarse a una fila de `domain-artifacts`. Si no puede, se marca como **importado** y se justifica explícitamente. La app tiene permiso de importar un máximo de **dos** ejes ajenos al dominio: son la firma de autoría, no la base.

**Gate:** presentar `domain-artifacts` y las derivaciones propuestas. No iniciar la Fase 1 sin confirmación del usuario.

---

## Fase 1: Cuestionario de Descubrimiento Vanguardista
> Regla de oro: Una pregunta a la vez. Barra de progreso. 4 alternativas + "Otra". Las alternativas deben ser visualmente **arriesgadas**, no seguras.
> **Filtro de derivación:** cada opción que el usuario elija debe trazarse a `domain-artifacts` (Fase 0.5). Cuando la respuesta natural no se derive de nada, ofrecer la alternativa derivada y registrar el eje como importado.

### Modos de entrada (elegir uno antes de empezar)
> El cuestionario completo son 12 preguntas. No todos los usuarios quieren responderlas.

| Modo | Cuándo | Cómo funciona |
|---|---|---|
| **Cuestionario completo** | El usuario quiere decidir cada eje | Pasos 1.1–1.12, una pregunta a la vez |
| **Fast track** | Hay prisa o no hay criterio visual | 3 preguntas (1.1 movimiento, 1.12 voz, 1.5 paleta). El agente **deriva** el resto del dominio y lo propone en Fase 2 |
| **Sorpréndeme** | "Hazme algo memorable, tú decides" | El agente propone un concepto completo desde `domain-artifacts` (0.5) y el usuario reacciona en Fase 2/3 |
| **Siembra por referencias** | El usuario trae 3 URLs o imágenes | Derivar los 12 ejes de las referencias, marcar los importados y presentarlos en Fase 2 |

**Normalizar "Otra":** cuando el usuario elige "Otra", traducir su respuesta a un eje con **3 keywords + 1 técnica dominante + su artefacto de origen**. Una respuesta libre sin normalizar no entra al design system.

### Paso 1.1: Movimiento Artístico (1/12)
**Pregunta:** Si tu app fuera un movimiento artístico, ¿cuál sería?

| # | Opción | Descripción | Keywords de diseño |
|---|--------|-------------|-------------------|
| 1 | **Deconstructivismo Digital** | Fragmentos, superposición caótica, tipografía rota como escultura. Elementos que parecen colapsar y reconstruirse. | Layouts rotos, z-index extremo, tipografía como imagen, glitch effects |
| 2 | **Biológico-Digital** | Organismos que crecen en la interfaz. Raíces que conectan datos, células que pulsan. | Generative SVG, L-systems, morphing orgánico, colores bioluminiscentes |
| 3 | **Brutalismo Web 3.0** | Raw, sin adornos, tipografía a 200px, bordes de 4px negros, scroll horizontal forzado, sin grid. | System fonts, borders brutales, overflow visible, scroll-snap horizontal |
| 4 | **Maximalismo Controlado** | Todo al mismo tiempo. 5 tipografías, 3 paletas, animaciones superpuestas. Pero con un hilo conductor invisible. | Layering extremo, blend modes múltiples, parallax en 3 ejes, collage digital |
| O | **Otra** | El usuario describe su propio movimiento | Anotar palabras clave exactas |

> Guardar como `personality_axis`.

### Paso 1.2: Espacio y Navegación (2/12)
**Pregunta:** ¿Cómo se MUEVE el usuario por tu app?

| # | Opción | Descripción | Técnica |
|---|--------|-------------|---------|
| 1 | **Scroll como viaje** | No hay "páginas", hay un mundo continuo. Scroll vertical infinito que revela capas de contenido como estratos geológicos. | GSAP ScrollTrigger, pinned sections, morphing entre secciones |
| 2 | **Navegación orbital** | Todo gira alrededor de un centro. El usuario orbita entre nodos de información en 3D. | Three.js, CSS 3D transforms, radial layouts |
| 3 | **Mapa de constelaciones** | Cada elemento es una estrella. Conectar puntos revela relaciones. Zoom infinito hacia dentro y fuera. | D3.js force simulation, zoomable UI, canvas rendering |
| 4 | **Carrusel imposible** | Scroll horizontal que se convierte en vertical, que se convierte en diagonal. La dirección es el contenido. | Scroll hijacking controlado, path-based scrolling, locomotive scroll |
| O | **Otra** | El usuario describe su navegación ideal | |

> Guardar como `navigation_pattern`.

### Paso 1.3: Tipografía como Arquitectura (3/12)
**Pregunta:** La letra en tu app no es solo texto. Es...

| # | Opción | Descripción | Fuentes / Técnicas |
|---|--------|-------------|-------------------|
| 1 | **Un edificio** | Letras de 30vw de alto que ocupan toda la pantalla, con contenido que fluye DENTRO de los contornos tipográficos. | Variable fonts con animación de peso, CSS shapes, clip-path con texto |
| 2 | **Un organismo vivo** | Cada carácter respira, se estira, se contrae. La tipografía tiene latido. | GSAP SplitText, per-character animation, variable font axis animation |
| 3 | **Una máquina de escribir rota** | Texto que se tipea con errores, borra, reescribe. Imperfección como estética. | TypeIt.js, custom typewriter con glitch, caret personalizado |
| 4 | **Un collage tipográfico** | 5 fuentes diferentes en un solo párrafo. Serif junto a mono junto a script. Caos con intención. | Font pairing extremo, inline styles por palabra, rotación de spans |
| O | **Otra** | El usuario describe su tipografía ideal | |

> Guardar como `typography_architecture`.

### Paso 1.4: Materialidad Digital Extrema (4/12)
**Pregunta:** ¿De qué material imposible está hecha tu app?

| # | Opción | Descripción | Técnica |
|---|--------|-------------|---------|
| 1 | **Líquido mercurial** | Superficies que fluyen, gotas que se forman, interfaces que se derriten. Todo tiene tensión superficial. | WebGL shaders (liquid simulation), SVG filters (displacement), CSS backdrop-filter |
| 2 | **Holograma roto** | Interfaz que parpadea, se desdobla en RGB, tiene scanlines, parece proyectada desde el futuro. | CSS chromatic aberration, scanline overlays, glitch keyframes, CRT effects |
| 3 | **Papel vívido** | Texturas de papel arrugado, rasgado, quemado. Capas de papel superpuestas con sombras reales. | Multi-layer box-shadows, paper texture overlays, clip-path irregular borders |
| 4 | **Cristal fracturado** | Glassmorphism pero roto. Grietas que atraviesan la interfaz. Reflejos distorsionados. | CSS glass effects + crack SVG overlays, refraction simulation, shattered grid layouts |
| O | **Otra** | El usuario describe su materialidad | |

> Guardar como `materiality`.

### Paso 1.5: Color como Emoción (5/12)
**Pregunta:** Elige una escena cinematográfica que represente la paleta de tu app:

| # | Opción | Paleta base | Mood |
|---|--------|-------------|------|
| 1 | **Blade Runner 2049 — Las Vegas** | Naranja ácido, ámbar enfermizo, negro profundo. Calor tóxico. | #FF6B35, #1A0F00, #FFB627, #000000 |
| 2 | **Her — Los Ángeles pastel** | Rosa melocotón, azul cielo suave, crema. Melancolía cálida. | #FF9F9F, #A8D8EA, #FFF5E1, #4A4A4A |
| 3 | **Suspiria — Baile rojo** | Rojo sangre, verde enfermo, magenta. Terror elegante. | #8B0000, #2D5016, #FF00FF, #1A1A1A |
| 4 | **2001: Odisea — El monolito** | Negro absoluto, blanco puro, un solo acento de rojo. Minimalismo existencial. | #000000, #FFFFFF, #FF0000, #333333 |
| O | **Otra** | El usuario describe su escena/paleta | |

> Guardar como `palette_mood`.

### Paso 1.6: Interacción como Performance (6/12)
**Pregunta:** ¿Qué pasa cuando el usuario TOCA algo?

| # | Opción | Descripción | Técnica |
|---|--------|-------------|---------|
| 1 | **Ecosistema reactivo** | Cada clic envía ondas que afectan todo lo demás. Nada es independiente. | Canvas particle systems, ripple effects, physics-based UI |
| 2 | **Transformación morphing** | Los elementos no desaparecen; se convierten en otros elementos. Un botón se vuelve un modal. | GSAP Flip, layout animations, shape morphing SVG |
| 3 | **Realidad aumentada digital** | El cursor deja rastros. El hover genera distorsión. La interfaz "recuerda" dónde has estado. | Trail effects, cursor distortion, persistent interaction history |
| 4 | **Ritual de carga** | Los estados de carga son ceremonias. No spinners; son transformaciones visuales con propósito narrativo. | Custom loading sequences, staged reveals, narrative progress indicators |
| O | **Otra** | El usuario describe su interacción ideal | |

> Guardar como `interaction_pattern`.

### Paso 1.7: Estructura de Información (7/12)
**Pregunta:** ¿Cómo se organiza el contenido?

| # | Opción | Descripción | Layout |
|---|--------|-------------|--------|
| 1 | **Pila caótica** | Todo superpuesto como papeles sobre un escritorio. El usuario "excava" para encontrar cosas. | z-index layering, drag-to-reorder, scattered positioning |
| 2 | **Línea de tiempo viviente** | El contenido fluye como un río. Pasado a la izquierda, futuro a la derecha, presente en el centro. | Horizontal scroll timeline, event branching, temporal visualization |
| 3 | **Galaxia de nodos** | Cada pieza de contenido es un planeta. El zoom revela detalles. Las conexiones son constelaciones. | Force-directed graph, zoomable canvas, node-link diagrams |
| 4 | **Caja de sorpresas** | No hay estructura visible. El contenido aparece de formas inesperadas. Descubrimiento como gameplay. | Randomized layouts, easter eggs, progressive disclosure |
| O | **Otra** | El usuario describe su estructura ideal | |

> Guardar como `information_structure`.

### Paso 1.8: Sonido como Atmósfera (8/12)
**Pregunta:** Si tu app sonara, ¿qué escucharías al usarla?

| # | Opción | Descripción | Técnica |
|---|--------|-------------|---------|
| 1 | **Silencio curado** | Cero audio. El silencio es la estética: toda la retroalimentación es visual y háptica. El sonido se reserva SOLO para momentos críticos. | Sin WebAudio, `navigator.vibrate` para háptica, sonido único y memorable para errores |
| 2 | **Paisaje sonoro generativo** | Un ambiente sonoro que evoluciona con scroll, hover y contexto. Nunca se repite, nunca es predecible. | Tone.js / WebAudio, generative sequencers, osciladores por sección |
| 3 | **Interfaz percusiva** | Cada toque, click y transición dispara un micro-hit sonoro. La app suena como un instrumento que el usuario toca. | Sound sprites (Howler.js), síntesis FM corta, hits sincronizados con motion |
| 4 | **Sinestesia audio-visual** | Sonido, color y movimiento son la MISMA señal. Cambian juntos como un organismo único. | Audio-reactive visuals, `AnalyserNode` alimentando color y motion |

> Guardar como `sound_identity`.

### Paso 1.9: Luz y Atmósfera (9/12)
**Pregunta:** ¿Cómo ilumina tu app?

| # | Opción | Descripción | Técnica |
|---|--------|-------------|---------|
| 1 | **Fotograma de cine** | Una sola fuente de luz dramática. Todo lo demás en penumbra. El foco señala lo importante. | Radial-gradients direccionales, vignettes, box-shadow de foco |
| 2 | **Neón perpetuo** | Glows por todas partes. La app brilla en la oscuridad, el color ES luz. | text-shadow/box-shadow glow, blur layers, dark-mode como default |
| 3 | **Luz de día plano** | Sin sombras, sin profundidad. Iluminación frontal uniforme, colores honestos y planos. | Zero box-shadow, surfaces flat, bordes definidos |
| 4 | **Elementos que emiten luz** | Cada componente es una lámpara. Hover = encender. El fondo es oscuridad que respira. | `filter: brightness`, backdrop glow, transiciones de iluminación por estado |

> Guardar como `lighting_profile`.

### Paso 1.10: Ritmo y Tempo (10/12)
**Pregunta:** ¿Cuál es el pulso de tu app?

| # | Opción | Descripción | Técnica |
|---|--------|-------------|---------|
| 1 | **Cine lento** | Todo se toma su tiempo. Transiciones largas, pausas deliberadas que crean suspense y peso. | Durations 600–1200ms, easings suaves, timelines secuenciales |
| 2 | **Pulso cardíaco** | Un ritmo constante late bajo toda la interfaz. Los elementos respiran con él. | Duration tokens con base 500ms, keyframes de "latido", sincronía rítmica |
| 3 | **Edición frenética** | Cortes rápidos, todo reacciona al instante. Energía de montaje de trailer. | Durations 80–200ms, anticipación, easings exagerados |
| 4 | **Tempo por fases** | El ritmo cambia por contexto: lento en lectura, rápido en acción, climax en momentos clave. | Context-based duration maps, transition tokens por zona |

> Guardar como `tempo_rhythm`.

### Paso 1.11: Cursor como Personaje (11/12)
**Pregunta:** ¿Qué hace el puntero cuando el usuario toca tu mundo?

| # | Opción | Descripción | Técnica |
|---|--------|-------------|---------|
| 1 | **Pluma que deja tinta** | El cursor deja rastros y mancha el contenido al pasar. Cada movimiento es una marca. | Pointer trails, `mix-blend-mode`, canvas para el rastro |
| 2 | **Láser quirúrgico** | Preciso, con anillo de foco. El cursor se convierte en una herramienta quirúrgica. | Custom cursor crosshair/anillo, snap en targets interactivos |
| 3 | **Ser vivo** | El cursor respira, se inclina, reacciona al contenido y a la velocidad del movimiento. | Custom cursor animado (keyframes), transform según velocidad/hover |
| 4 | **Mano invisible** | Sin cursor visible. El sistema muestra contexto según dónde estás. | `cursor: none`, tooltips contextuales, highlight de zona activa |

> Guardar como `cursor_identity`.

---

### Paso 1.12: Voz y Copy (12/12)
**Pregunta:** Cuando algo pasa (un error, una espera, un logro), ¿cómo habla tu app?

| # | Opción | Descripción | Regla de copy |
|---|--------|-------------|---------------|
| 1 | **Oráculo seco** | Frases cortas, sentenciosas, sin cortesía. La app no pide permiso. | ≤4 palabras, sin "por favor", sin exclamaciones |
| 2 | **Narrador de campo** | Técnico y preciso, habla la jerga del dominio como un operador. | Vocabulario del oficio, datos antes que adjetivos |
| 3 | **Personaje con carácter** | Primera persona, opinión, humor seco. La app tiene punto de vista. | "Yo", juicios, nada de neutralidad corporativa |
| 4 | **Documento oficial** | Protocolo, formulario, sin emoción. El sistema habla en tercera persona. | Pasiva, folio/fecha/estado, cero calidez |
| O | **Otra** | El usuario describe su voz | Anotar palabras clave exactas |

> Guardar como `voice_profile`.
> **Ficha de voz (obligatoria; alimenta los estados especiales de 9.4 y el copy de todo el producto):**

| Campo | Decisión |
|---|---|
| Persona gramatical | [1ª / 2ª / 3ª / impersonal] |
| Longitud máxima | [n palabras por mensaje] |
| Humor | [sí seco / no] |
| Vocabulario prohibido | ["por favor", "lo sentimos", "exitosamente", "Oops"...] |
| Error | [ejemplo exacto] |
| Empty | [ejemplo exacto] |
| Espera / loading | [ejemplo exacto] |
| Éxito | [ejemplo exacto] |

### Paso 1.13: Preguntas Avanzadas Opcionales (Bonus)
> Después del paso 1.12, ofrecer: *"Ya tienes las bases. ¿Quieres refinar 2 dimensiones más? (Opcional)"*.
> Si el usuario acepta, hacer estas DOS preguntas una a la vez con barra de progreso. Si no, saltar directo a Fase 1.5.
> Si el usuario responde las opcionales, sus keys (`friction_profile`, `temporal_anchor`) se integran a la Fase 2.

#### Pregunta Opcional A: Fricción Deliberada → `friction_profile`
**Pregunta:** ¿Cuánto esfuerzo debe poner el usuario para lograr las cosas?

| # | Opción | Descripción | Técnica |
|---|--------|-------------|---------|
| 1 | **Cero fricción** | Todo es instantáneo. Cero pasos de más; la eficiencia ES la estética. | Optimistic UI, autosave, atajos de teclado |
| 2 | **Ritual ceremonioso** | Cada acción importante es un acto con pasos, pausas y anticipación. | Multi-step reveals, confirmaciones narrativas, transiciones rituales |
| 3 | **Recompensa escalonada** | La app dosifica la información; el usuario "gana" capas al interactuar. | Progressive disclosure, unlocks visuales, meta-progreso |
| 4 | **Obstáculo deliberado** | Pequeños retos para llegar a la funcionalidad. El descubrimiento es parte del juego. | Micro-puzzles, gestos a descubrir, easter eggs como recompensa |

#### Pregunta Opcional B: Ancla Temporal → `temporal_anchor`
**Pregunta:** ¿De qué época parece venir tu app?

| # | Opción | Descripción | Técnica |
|---|--------|-------------|---------|
| 1 | **Retro-futurismo 80s** | El futuro que imaginaba 1984: terminales, scanlines, pronóstico optimista. | Neon, CRT effects, tipografía chunky, paleta sintética |
| 2 | **Y2K Chrome** | 2000s: metal cepillado, brillos, optimismo tecnológico de burbuja. | Gradientes metálicos, highlights blancos, orb shapes |
| 3 | **Presente radical** | 2026 y más allá: limpio pero con decisiones que aún no se ven en las masas. | Colores inusuales, tipografías nuevas, micro-interacciones avanzadas |
| 4 | **Atemporal alienígena** | Sin referencia a ninguna época conocida. Podría venir de otro planeta. | Geometría imposible, sin tropes reconocibles, color no-humano |

---

## Fase 1.5: Exploración Visual con Imágenes (OPCIONAL pero RECOMENDADO)
> Si el usuario no tiene referencias visuales claras, generar 3-4 mockups conceptuales usando un modelo de imagen antes de escribir código.

### Prompt para generación de mockups:
```
Genera 4 mockups de interfaz de app para [tipo de app] con estilo [personality_axis].
- Materialidad: [materiality]
- Paleta: [palette_mood]
- Tipografía: [typography_architecture]
- Navegación: [navigation_pattern]
- Interacción: [interaction_pattern]
- Luz: [lighting_profile]
- Tempo: [tempo_rhythm] (representar en la elección de captura de momento)
- Cursor: [cursor_identity] (mostrar el cursor dentro del mockup)
- Sonido: [sound_identity] (traducir a pistas visuales: ondas, micrófonos, o silencio visual limpio)

Cada mockup debe ser visualmente DISTINTO de los otros. Experimenta con:
- Layouts asimétricos extremos
- Tipografía como elemento dominante
- Superposición de capas con blend modes
- Elementos que rompen el viewport
- Texturas y materialidades visibles
- Iluminación dramática según [lighting_profile]
- Cursor visible y con personalidad

Estilo: UI/UX design mockup, high fidelity, experimental, avant-garde.
```

> Mostrar los 4 mockups al usuario. Pedir que elija uno o que combine elementos de varios.
> Extraer del mockup elegido: paleta exacta, tipografía dominante, layout pattern, texturas visibles, tratamiento de luz y comportamiento de cursor si son visibles.

---

## Fase 1.6: Coherencia de Ejes · BLOQUEANTE

Los ejes se eligieron como si fueran independientes. Algunos se contradicen, y la contradicción no se resuelve en código: se resuelve aquí.

Revisar los pares conocidos y **declarar la resolución**:

| Combinación | Conflicto | Resolución posible |
|---|---|---|
| Caja de sorpresas + Cero fricción | Descubrir requiere esfuerzo; cero fricción lo elimina | La sorpresa vive en la forma, no en el acceso |
| Mano invisible + Realidad aumentada digital | El rastro necesita un puntero visible | El rastro ocurre sin cursor (ondas, calor) |
| Silencio curado + Interfaz percusiva | Silencio total vs. sonido en cada toque | Solo los eventos críticos suenan; el resto es visual |
| Silencio curado + Sinestesia audio-visual | El color/motion no puede seguir a un audio mudo | La sinestesia se invierte: manda el color y el audio sigue |
| Maximalismo controlado + Luz de día plano | La densidad necesita profundidad | Jerarquía por escala y color, no por luz |
| Cine lento + Edición frenética | Un solo tempo base | Tempo por fases (§1.10 opción 4) |
| Scroll como viaje + Mano invisible | El viaje necesita orientación | Indicadores persistentes que no dependen del cursor |
| Brutalismo + Materialidad líquida | Rigidez estructural vs. superficie fluida | "Aceite sobre hormigón": fluido contenido por bordes duros |

> Los pares no listados también cuentan: cualquier cruce que exija una decisión se declara aquí. **Un conflicto no resuelto reaparece como inconsistencia en la tercera pantalla.**

**Gate:** presentar el mapa de coherencia con las resoluciones antes de la Fase 2.

---

## Fase 2: Refinamiento de Supuestos Experimentales
Mostrar al usuario los supuestos derivados del cuestionario. Estos supuestos deben sonar **arriesgados**, no seguros.

### Plantilla de Supuestos Experimentales:
```
Basado en tu selección, propongo lo siguiente para tu app:

1. PERSONALIDAD: [personality_axis] → La app NO será amigable. Será [descripción provocativa].
   El copy será [directo/abstracto/poético/técnico], nunca genérico.

2. NAVEGACIÓN: [navigation_pattern] → Rompemos las convenciones de scroll.
   [Descripción técnica del patrón de navegación].

3. TIPOGRAFÍA: [typography_architecture] → La letra es el héroe.
   [Fuente principal] a [tamaño extremo]px. [Descripción del tratamiento].

4. MATERIALIDAD: [materiality] → La superficie tiene vida propia.
   [Descripción de efectos visuales y técnicas].

5. COLOR: [palette_mood] → Paleta de [n] colores con [descripción del contraste].
   Primario: [hex]. Secundario: [hex]. Fondo: [hex]. Acento: [hex].
   Uso de blend modes: [sí/no, cuáles].

6. INTERACCIÓN: [interaction_pattern] → Cada toque es un evento.
   [Descripción de la respuesta a interacciones].

7. ESTRUCTURA: [information_structure] → El contenido NO está en una grid de 12 columnas.
   [Descripción del layout experimental].

8. MOTION: Las animaciones NO serán fade-in genéricos.
   - Transiciones: [descripción específica]
   - Micro-interacciones: [descripción específica]
   - Loading: [descripción específica, NUNCA spinner]
   - Librería principal: [GSAP / Three.js / Framer Motion / Custom]

9. BORDES: [Mixto extremo / 0px en todo / Irregulares / Variables]
   [Justificación del tratamiento de bordes].

10. RESPONSIVE: En móvil, la app [se adapta fielmente / se transforma en otra cosa / prioriza una versión].
    [Descripción del comportamiento responsive].

11. SONIDO: [sound_identity] → El audio es [silencio curado / generativo / percusivo / sinestésico].
    [Descripción del tratamiento sonoro. Si es silencio: qué fallbacks hápticos y cuándo se rompe el silencio].

12. LUZ: [lighting_profile] → La iluminación es [cine / neón / plano / emisiva].
    [Descripción de tokens de luz, glows y profundidad].

13. TEMPO: [tempo_rhythm] → La app respira con [cine lento / pulso cardíaco / frenético / por fases].
    Duración base: [valor]. Easing principal: [valor]. [Patrón rítmico].

14. CURSOR: [cursor_identity] → El puntero es [tinta / láser / ser vivo / invisible].
    [Descripción del comportamiento del cursor por estado].

15. FRICCIÓN: [friction_profile o "estándar"] → La experiencia exige [cero esfuerzo / ritual / recompensa / reto].
    [Descripción de cómo se dosifica la interacción].

16. ANCLA TEMPORAL: [temporal_anchor o "no definida"] → La estética referencia [época].
    [Referencias concretas de la época si aplica].

17. VOZ: [voice_profile] → La app habla como [oráculo / operador / personaje / documento].
    Persona [1ª/2ª/3ª], máximo [n] palabras, humor [sí/no]. Vocabulario prohibido: [lista].
    Error: "[copy]". Empty: "[copy]". Espera: "[copy]". Éxito: "[copy]".
```

> Pedir al usuario: "¿Hay algún supuesto que NO te guste? Responde con los números (ej: 2, 5, 9) o di 'todo bien' para continuar."

---

## Fase 3: Preguntas de Clarificación (One-by-One)
Por cada supuesto marcado como incorrecto, hacer UNA pregunta a la vez.

### Formato:
```
[Barra de progreso: Pregunta X de Y]

El supuesto #[número] dice: [texto del supuesto].
¿Qué prefieres en su lugar?

1. [Alternativa A - igual de arriesgada]
2. [Alternativa B - igual de arriesgada]
3. [Alternativa C - igual de arriesgada]
4. [Alternativa D - igual de arriesgada]
O. Otra: [espacio para que el usuario escriba]
```

> Regla: Las alternativas nunca deben ser "la versión segura". Siempre ofrecer 4 direcciones distintas, todas experimentales.

---

## Fase 4: Generación del Design System Document Experimental
Generar `design-system.md` con estructura expandida para diseño vanguardista.

### Estructura:

```markdown
# Design System Experimental: [Nombre del Proyecto]
## Última actualización: [fecha]
## Versión: Experimental v1

---

## 0. Arqueología y Materiales del Dominio
| Artefacto real | Rasgo extraíble | Token / regla | Origen |
|---|---|---|---|
| [artefacto] | [tipografía / retícula / color / textura / sonido / ritmo] | [`--token`] | dominio / importado |

> Los ejes marcados "importado" no pueden ser más de dos. Si lo son, el sistema es un collage, no una identidad.

---

## 1. Manifiesto de Diseño
> Esta app existe para [propósito]. No es genérica porque [razón única].
> Si alguien puede decir "esto parece hecho por AI", hemos fallado.

- **Movimiento artístico:** [personality_axis]
- **Navegación:** [navigation_pattern]
- **Tipografía como:** [typography_architecture]
- **Materialidad:** [materiality]
- **Interacción como:** [interaction_pattern]
- **Estructura:** [information_structure]
- **Sonido:** [sound_identity]
- **Luz:** [lighting_profile]
- **Tempo:** [tempo_rhythm]
- **Cursor:** [cursor_identity]
- **Fricción:** [friction_profile — si respondió la opcional]
- **Ancla temporal:** [temporal_anchor — si respondió la opcional]

## 2. Paleta de Color
| Token | Hex | Uso | Blend Mode | Notas |
|-------|-----|-----|------------|-------|
| --color-primary | #XXXXXX | [uso] | [none/overlay/multiply/screen] | |
| --color-secondary | #XXXXXX | [uso] | [blend] | |
| --color-background | #XXXXXX | Fondo general | [blend] | |
| --color-surface | #XXXXXX | Superficies elevadas | [blend] | |
| --color-text-primary | #XXXXXX | Texto principal | [blend] | |
| --color-text-secondary | #XXXXXX | Texto secundario | [blend] | |
| --color-accent | #XXXXXX | Acentos dramáticos | [blend] | |
| --color-glitch-1 | #XXXXXX | Efectos de distorsión | screen | Solo para efectos |
| --color-glitch-2 | #XXXXXX | Efectos de distorsión | multiply | Solo para efectos |

> NOTA: Especificar cuándo usar blend modes. Especificar texturas de fondo.

## 3. Tipografía como Arquitectura
| Rol | Fuente | Peso | Tamaño | Line-height | Letter-spacing | Transform | Uso |
|-----|--------|------|--------|-------------|----------------|-----------|-----|
| Display Hero | [Fuente] | [Peso] | [Size]vw | [LH] | [LS] | [uppercase/none] | H1, títulos de sección |
| Display Secondary | [Fuente] | [Peso] | [Size]px | [LH] | [LS] | [transform] | Subtítulos grandes |
| Body | [Fuente] | [Peso] | [Size]px | [LH] | [LS] | [transform] | Párrafos |
| Mono | [Fuente] | [Peso] | [Size]px | [LH] | [LS] | [transform] | Datos, código, labels técnicos |
| Accent | [Fuente] | [Peso] | [Size]px | [LH] | [LS] | [transform] | Énfasis, citas |
| Micro | [Fuente] | [Peso] | [Size]px | [LH] | [LS] | [uppercase] | Labels, metadata |

> NOTA: Especificar animaciones tipográficas (weight morphing, character reveal, etc.)
> Especificar fallback fonts que mantengan la personalidad.

## 4. Sistema de Spacing
- **Base unit:** [4px / 8px / etc.]
- **Scale:** [Escala experimental: Fibonacci, golden ratio, musical, o caos intencional]
- **Section padding:** [valor] — ¿por qué este valor?
- **Container:** [max-width / fluid / bleeding edges]
- **Grid:** [NO grid / 12-col / asymmetrical / broken / custom]
- **Overlap permitido:** [sí/no, hasta qué punto]

## 5. Bordes, Radios y Texturas
| Elemento | Border-radius | Border | Textura | Notas |
|----------|---------------|--------|---------|-------|
| Botones primarios | [valor] | [valor] | [sí/no, cuál] | |
| Tarjetas | [valor] | [valor] | [sí/no, cuál] | |
| Inputs | [valor] | [valor] | [sí/no, cuál] | |
| Modales | [valor] | [valor] | [sí/no, cuál] | |
| Imágenes | [valor] | [valor] | [sí/no, cuál] | |
| Tags/Chips | [valor] | [valor] | [sí/no, cuál] | |

> NOTA: Si la materialidad es "líquido" o "holograma", considerar bordes animados o sin bordes.
> Especificar SVG filters o CSS filters para texturas.

## 6. Sombras, Glows y Efectos de Profundidad
| Nivel | Shadow / Glow | Uso | Técnica |
|-------|---------------|-----|---------|
| Flat | none | Base | |
| Elevated 1 | [valor] | Hover sutil | CSS box-shadow |
| Elevated 2 | [valor] | Tarjetas activas | CSS + filter |
| Glow | [valor] | Estados activos, acentos | text-shadow / box-shadow glow |
| Distortion | [descripción] | Efectos especiales | SVG filters / WebGL |

## 7. Motion, Animation & Physics
| Tipo | Especificación | Duración | Easing | Librería |
|------|----------------|----------|--------|----------|
| Page transitions | [descripción] | [ms] | [easing] | [GSAP / etc.] |
| Scroll animations | [descripción] | [ms] | [easing] | [ScrollTrigger / etc.] |
| Micro-interactions | [descripción] | [ms] | [easing] | [Framer Motion / etc.] |
| Loading states | [descripción NARRATIVA] | [ms] | [easing] | [Custom / etc.] |
| Hover states | [descripción] | [ms] | [easing] | [CSS / etc.] |
| Typographic motion | [descripción] | [ms] | [easing] | [GSAP SplitText / etc.] |
| Cursor effects | [descripción] | [ms] | [easing] | [Custom / etc.] |

> Especificar: ¿Las animaciones respetan prefers-reduced-motion?

## 8. Navegación y Layout
### 8.1 Patrón de Navegación Principal
- **Tipo:** [navigation_pattern]
- **Comportamiento:** [descripción detallada]
- **Indicadores de estado:** [cómo se muestra dónde está el usuario]
- **Transiciones entre secciones:** [descripción]

### 8.2 Layout por Viewport
- **Mobile:** [descripción experimental del layout móvil]
- **Tablet:** [descripción]
- **Desktop:** [descripción]
- **Breakpoints:** [valores, con justificación]
- **Z-index strategy:** [plan de capas, especialmente si hay overlap]

## 9. Componentes Base (Anti-Genéricos)
### 9.1 Botones
- **Primary:** [estados: default, hover (¿qué pasa?), active, disabled, loading]
- **Secondary:** [estados]
- **Ghost:** [estados]
- **Icon Button:** [estados]
- **Text-as-Button:** [cuando el texto mismo es clickeable]

> Cada estado debe tener una animación específica, no solo un cambio de color.

### 9.2 Inputs
- **Text:** [estados, con descripción de focus effects]
- **Textarea:** [estados]
- **Select:** [estados]
- **Checkbox/Radio:** [estados, con animación de check]

### 9.3 Cards / Contenedores
- **Standard:** [estructura]
- **Feature:** [estructura]
- **Media:** [estructura]
- **Floating:** [estructura]

### 9.4 Estados Especiales (Zona de Personalidad Máxima)
> Todo copy de esta sección sale de la ficha de voz (§21). Prohibido inventarlo aquí.

- **Empty State:** [Copy exacto (voz aplicada) + descripción visual + animación]
- **Error State:** [Copy exacto + descripción visual + animación]
- **Loading State:** [Copy exacto + secuencia narrativa de carga + animación]
- **Success State:** [Copy exacto + celebración visual + animación]
- **Onboarding:** [Copy paso a paso + flujo de introducción]
- **404 / Not Found:** [Copy + experiencia visual memorable]

### 9.5 Matriz de Estados (obligatoria)
> Ningún componente está listo sin la matriz completa. El patrón típico es sobre-indexar en hover y olvidar `focus-visible`, `disabled` y `error`.

| Componente | default | hover | focus-visible | active | disabled | loading | error |
|---|---|---|---|---|---|---|---|
| Botón primario | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Botón ghost | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Input de texto | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Select | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Checkbox / radio | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Card | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Tag / chip | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |
| Nav item | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] |

> Cada estado declara, además: cambio visual, duración (token §16), sonido (§14) y comportamiento con `prefers-reduced-motion` (§19).

## 10. Assets Visuales y Texturas
- **Icon set:** [estilo: hand-drawn / geometric brutal / organic / glitch / custom]
- **Illustration style:** [descripción]
- **Photography treatment:** [filtros, crops, tratamiento]
- **Texture overlays:** [lista de texturas con URLs o descripciones para generar]
- **SVG filters:** [lista de filtros custom necesarios]
- **Shader requirements:** [si aplica, descripción de shaders WebGL]

## 11. Prohibiciones Explícitas (Anti-Slop Manifesto)
Esta app NUNCA usará:

> Auditado por `scripts/check-slop.py` (Fase 6). Un hallazgo es una señal para mirar, no un veredicto final.

- [ ] Gradiente púrpura/azul genérico de AI
- [ ] Inter o Roboto como fuente principal sin modificación extrema
- [ ] Hero centrado con un solo CTA y tres tarjetas debajo
- [ ] Esquinas redondeadas de 8px en TODOS los elementos
- [ ] Sombras al 0.1 de opacidad en todo
- [ ] Spinner de carga genérico (circular girando)
- [ ] "No data found" como empty state
- [ ] "Something went wrong" como error state
- [ ] Paleta de grises sin punto de vista emocional
- [ ] Layout simétrico cuando la personalidad pide asimetría
- [ ] Animaciones fade-in genéricas sin dirección ni propósito
- [ ] Iconos de Material Design sin personalización
- [ ] Grid de 12 columnas por defecto
- [ ] Scroll suave genérico sin propósito narrativo
- [ ] Botones con solo cambio de color en hover
- [ ] Tipografía que no sea un elemento de diseño activo
- [ ] Espaciado predecible (8px, 16px, 24px, 32px...) sin variación
- [ ] "Diseño responsive" que solo significa "más pequeño en móvil"
- [ ] Sonido de notificación del sistema genérico (pop/ding por defecto del OS)
- [ ] Cursor arrow del sistema sin personalidad ni comportamiento
- [ ] Todas las transiciones con la misma duración (tempo uniforme = cadáver rítmico)
- [ ] Iluminación plana sin dirección ni drama cuando la personalidad pide profundidad
- [ ] Silencio total cuando el sonido es parte de la identidad (y viceversa: sonido genérico cuando el silencio es la estética)
- [ ] Bento grid como layout por defecto (cliché 2023–2026)
- [ ] "Liquid glass" / glassmorphism copiado sin derivación
- [ ] Blobs de gradiente como decoración de fondo
- [ ] Emoji como sustituto de un sistema de iconos
- [ ] Cliché brutalista-portfolio (Helvetica gigante + grain + mono labels) por defecto
- [ ] Usar los tokens experimentales como checklist en vez de derivarlos del dominio
- [ ] Copy genérico de sistema operativo ("OK", "Cancelar", "Aceptar", "Error") sin voz propia
- [ ] Inventar el copy de un estado sin pasar por la ficha de voz

## 12. Referencias y Moodboard
[Sugerir 3-5 referencias reales que capturen la esencia]
[Incluir descripción de POR QUÉ cada referencia es relevante]

## 13. Notas Técnicas para Implementación
- **Librerías recomendadas:** [lista con justificación]
- **Performance considerations:** [qué cuidar]
- **Accessibility:** [cómo mantener accesibilidad SIN sacrificar personalidad]
- **Browser support:** [qué features modernos usar con confianza]

## 14. Sonido y Audio
| Acción | Sonido / Silencio | Técnica | Volumen |
|--------|-------------------|---------|---------|
| Click / tap | [descripción o NADA] | [Tone.js / Howler / WebAudio / háptica] | [dB] |
| Transición de sección | [descripción o NADA] | [técnica] | [dB] |
| Error | [descripción] | [técnica] | [dB] |
| Success | [descripción] | [técnica] | [dB] |
| Ambiente | [generativo / silencio / loop] | [técnica] | [dB] |

> Especificar: ¿Respetar prefers-reduced-motion afecta también al audio? ¿Hay mute visible siempre?
> Si `sound_identity` es "silencio curado": documentar exactamente qué ÚNICO sonido existe (el error) y por qué.

## 15. Iluminación
| Token | Valor | Uso | Técnica |
|-------|-------|-----|---------|
| Light source | [dirección/tipo de luz] | Foco principal | [radial-gradient / spotlight / none] |
| --glow-primary | [valor] | [dónde brilla] | [box-shadow / text-shadow / blur] |
| --glow-secondary | [valor] | [dónde brilla] | [técnica] |
| Background darkness | [valor] | Fondo base | [color + depth] |
| Hover illumination | [descripción] | Qué pasa al encender un elemento | [filter brightness / glow] |

> Especificar: ¿El modo oscuro es el default o una elección? ¿La luz cambia con interacción?

## 16. Tempo System
| Token | Valor | Uso |
|-------|-------|-----|
| Duration base | [ms] | Ritmo general |
| Duration fast | [ms] | Micro-interacciones |
| Duration slow | [ms] | Transiciones de sección |
| Easing principal | [cubic-bezier/ease] | Todo el motion |
| Easing de climax | [cubic-bezier/ease] | Momentos importantes |
| Patrón rítmico | [descripción] | Cómo "late" la interfaz |

> Especificar: ¿El tempo es uniforme o por fases? ¿Qué secciones son lentas y cuáles rápidas?

## 17. Cursor
| Estado | Comportamiento | Técnica |
|--------|----------------|---------|
| Default | [descripción] | [custom cursor / none / system] |
| Hover en interactivo | [descripción] | [transform / snap / trail] |
| En texto | [descripción] | [descripción] |
| Drag / activo | [descripción] | [descripción] |
| Loading | [descripción] | [descripción] |

> Especificar: ¿El cursor respeta touch devices (desaparece en móvil)? ¿Deja rastros persistentes?
> Si es "mano invisible": documentar los tooltips contextuales que lo reemplazan.

## 18. Accesibilidad — Piso No Negociable
> La personalidad se diseña POR ENCIMA de este piso, nunca en lugar de él.

| Dimensión arriesgada | Piso obligatorio | Cómo se preserva la personalidad |
|---|---|---|
| Cursor custom (tinta, láser, ser vivo, invisible) | `:focus-visible` siempre visible y con contraste; el cursor nunca es la única señal de foco | El foco también puede ser un efecto propio (glow, expansión), no el outline por defecto |
| Scroll como viaje / scroll hijacking | Paginación por teclado (`PageUp/PageDown`, `Home/End`), escape de la sección pinned, desactivado con `prefers-reduced-motion` | El viaje se conserva como composición estática por secciones |
| Tipografía a 30vw / texto en contornos | Zoom 200% sin pérdida de contenido; cuerpo ≥16px | Escalas fluidas `clamp()` en vez de `vw` puro |
| Color glitch / blend modes | Contraste texto-fondo ≥ 4.5:1 (3:1 en ≥24px o 18.66px bold); el color nunca es el único portador de significado | El glitch se aplica a decoración, no al texto funcional |
| Fricción deliberada / obstáculo | Nunca en el único camino; siempre un bypass accesible y documentado | El ritual queda como opción por defecto; el bypass es discreto |
| Animación / tempo | `prefers-reduced-motion` documentado por eje (ver 19) | La composición estática mantiene el gesto |
| Audio generativo / percusivo | Mute visible siempre; opt-in; `AudioContext.resume()` tras gesto; alternativa visual | El ritmo visual puede sustituir al sonido |
| Mano invisible / `cursor: none` | Todos los targets alcanzables con teclado; foco visible | Los tooltips contextuales se vuelven el "cursor" narrativo |

## 19. Modos de Degradación
> Diseñar la degradación ES diseñar. No se "apagan animaciones": se define qué se convierte la app.

| Condición | Qué se convierte | Qué NUNCA se pierde |
|---|---|---|
| `prefers-reduced-motion: reduce` | [composición estática por sección, corte en vez de transición, sin scroll hijacking] | Jerarquía, contraste, identidad tipográfica y color |
| `prefers-contrast: more` | [paleta de alto contraste, sin blend modes sobre texto] | La personalidad cromática en superficies decorativas |
| `forced-colors: active` (Windows HCM) | [tokens del sistema, bordes visibles, sin gradients] | Todas las funciones y estados |
| `prefers-reduced-transparency` | [superficies opacas equivalentes] | Jerarquía de capas |
| `prefers-reduced-data` | [sin video/audio ambiente, fuentes ya cargadas, imágenes comprimidas] | El layout y la lectura |
| Sin WebGL / GPU débil | [escalera de fallback de la sección 20] | El mensaje visual, aunque simplificado |
| Tier bajo (móvil económico) | [menos capas, blend modes off, DPR limitado] | Interacción y contenido |

> Documentar también: qué se degrada primero cuando no hay presupuesto y qué es intocable.

## 20. Presupuesto de Performance y Escalera de Fallback
| Métrica | Objetivo | Límite duro | Cómo se mide |
|---|---|---|---|
| JS inicial | [KB gzip] | [KB gzip] | [bundle analyzer] |
| LCP | [ms] | [ms] | [Lighthouse / RUM] |
| CLS | < 0.1 | 0.25 | [Lighthouse] |
| Frame budget en scroll | [ms/frame] | 16.6 ms | [DevTools performance] |
| DPR máximo para shaders | [1.5 / 2] | 2 | [device tier] |

| Efecto | 1ª opción | 2ª opción (sin WebGL) | 3ª opción (tier bajo) |
|---|---|---|---|
| [materialidad / shader] | [WebGL] | [CSS filter / SVG] | [textura estática] |
| [blend modes] | [CSS mix-blend-mode] | [imagen precompuesta] | [color plano] |
| [partículas / cursor] | [canvas] | [CSS] | [estático] |
| [tipografía animada] | [variable font axis] | [transform] | [sin animación] |

> Cada efecto experimental declara su escalera. Un efecto sin fallback es una bomba de performance, no una decisión de diseño.

## 21. Voz y Microcopy
| Campo | Decisión |
|---|---|
| Persona gramatical | [1ª / 2ª / 3ª / impersonal] |
| Longitud máxima | [n palabras] |
| Humor | [sí seco / no] |
| Vocabulario prohibido | [lista] |
| Error | [copy exacto] |
| Empty | [copy exacto] |
| Loading | [copy exacto] |
| Success | [copy exacto] |
| Onboarding | [copy exacto] |

> El copy es un token: se define una vez y se reutiliza. Si un estado necesita copy nuevo, se agrega aquí primero.

## 22. Entrega y Artefactos
| Artefacto | Formato | Consumidor |
|---|---|---|
| `design-tokens.json` | DTCG | build, agentes de código |
| `motion.tokens.json` | duración / easing | implementación de motion |
| `prohibitions.lint.json` | reglas para `check-slop.py` | auditoría |
| `DESIGN.agent.md` | token sheet compacto | `agent-docs` / docs-pipeline Fase 6 |
| `design-decisions.md` | ADR con alternativas rechazadas | equipo, `design-adr` |

> La entrega no es el `.md`: es el sistema en formato consumible. Un design system que solo existe en prosa se reescribe mal en la primera pantalla.
```

---

## Fase 4.5: Artefactos Machine-Readable, Decisiones y Entrega

El `design-system.md` es la fuente de verdad narrativa; estos archivos son la fuente de verdad **ejecutable**. Se generan en el mismo paso, no después.

### 4.5.1 `design-tokens.json` (DTCG)
```json
{
  "color": {
    "primary":  { "$value": "#XXXXXX", "$type": "color" },
    "glitch-1": { "$value": "#XXXXXX", "$type": "color" }
  },
  "motion": {
    "duration-base":   { "$value": "640ms", "$type": "duration" },
    "easing-climax":   { "$value": "cubic-bezier(.2,.8,.2,1)", "$type": "cubicBezier" }
  },
  "radius": { "card": { "$value": "14px", "$type": "dimension" } },
  "type": {
    "display-hero": {
      "$type": "typography",
      "$value": { "fontFamily": "...", "fontSize": "18vw", "fontWeight": 800 }
    }
  }
}
```

### 4.5.2 `prohibitions.lint.json`
Reglas extra que `check-slop.py` carga del proyecto, además de las de fábrica. Es la forma de que el design system gobierne la auditoría:
```json
{
  "rules": [
    {
      "id": "NO-BRAND-GLOW",
      "severity": "gate",
      "pattern": "box-shadow:\\s*0 0 40px",
      "message": "glow genérico fuera de la paleta",
      "why": "la luz tiene dirección (regla 17)"
    }
  ]
}
```
> `severity` es `gate` o `advisory`. Una regla malformada es un gate, no un aviso.

### 4.5.3 `DESIGN.agent.md`
Token sheet compacto para agentes de código: paleta, tipografía, spacing, motion, matriz de estados, prohibiciones y la ficha de voz. Sin mermaid, sin prosa. Es el archivo que `docs-pipeline` (Fase 6) espera en `agent-docs/DESIGN.md`.

### 4.5.4 `design-decisions.md`
Un ADR por decisión, con **alternativas rechazadas**. Una decisión sin alternativas rechazadas es una nota, no un decision record.

| # | Decisión | Alternativas rechazadas | Por qué | Fecha |
|---|---|---|---|---|
| 1 | [eje = valor] | [A, B] | [razón] | [fecha] |

### 4.5.5 Handoff
| Cuando | Skill | Qué le pasas |
|---|---|---|
| El sistema es estable | `agent-docs` / `docs-pipeline` Fase 6 | `DESIGN.agent.md` → `agent-docs/DESIGN.md` |
| Hay que registrar una decisión | `design-adr` | las filas de `design-decisions.md` |
| Se necesita arquitectura de front | `design-core` / `react-architecture` | tokens + matriz de estados |

---

## Fase 5: Confirmación de Readiness Experimental

```
✅ DESIGN SYSTEM EXPERIMENTAL COMPLETO

Tu app tiene ahora una identidad visual ÚNICA basada en:
- Movimiento: [personality_axis]
- Navegación: [navigation_pattern]
- Tipografía: [typography_architecture]
- Materialidad: [materiality]
- Paleta: [primario, secundario, fondo, acento]
- Interacción: [interaction_pattern]
- Estructura: [information_structure]
- Sonido: [sound_identity]
- Luz: [lighting_profile]
- Tempo: [tempo_rhythm]
- Cursor: [cursor_identity]
- [Fricción: friction_profile — si respondió la opcional]
- [Ancla temporal: temporal_anchor — si respondió la opcional]
- Arqueología: [n] artefactos, [n] ejes importados (máximo 2)
- Accesibilidad: piso documentado por cada dimensión arriesgada
- Degradación: [n] condiciones cubiertas
- Performance: presupuesto definido y escalera de fallback por efecto
- Voz: [voice_profile] con ficha de voz completa (§21)
- Matriz de estados: [n] componentes × 7 estados (§9.5)
- Artefactos: `design-tokens.json`, `prohibitions.lint.json`, `DESIGN.agent.md`, `design-decisions.md`
- Auditoría: `python scripts/check-slop.py <project-dir>` → 0 gates

El documento `design-system.md` está listo y servirá como fuente de verdad
para TODA la generación de código posterior.

⚠️ ADVERTENCIA: Este design system es experimental. Algunas decisiones
pueden requerir técnicas avanzadas (WebGL, shaders, animaciones complejas).
¿Estás listo para que genere la primera pantalla?

[Si, genera con todo el riesgo] → Proceder a generación experimental.
[Si, pero simplifica lo técnico] → Adaptar a técnicas CSS/JS estándar manteniendo la visión.
[No, quiero ajustar algo] → Volver a Fase 3.
[Muéstrame el design system completo] → Mostrar markdown completo.
```

---

## Fase 6: Auditoría Anti-Slop · BLOQUEANTE

Las prohibiciones no son una lista de intenciones: se ejecutan.

```bash
python scripts/check-slop.py <project-dir>            # gates
python scripts/check-slop.py <project-dir> --strict   # gates + advisories
python scripts/check-slop.py <project-dir> --json     # salida machine-readable
python scripts/check-slop.py --list-rules
```

El script revisa dos cosas:
1. **El documento** `design-system.md`: que declare las 20 secciones requeridas (0–20). Un sistema incompleto no se audita.
2. **El código generado**: firmas de slop en el source (CSS/SCSS/JS/TS/JSX/TSX/Vue/Svelte/Astro/HTML).

**Modelo de severidad** — no todo gatea; un check con falsos positivos se ignora, que es peor que no tener check:

| Familia | Severidad | Regla |
|---|---|---|
| `transition: all` / `transition-all` | GATE | `SLOP-TRANSITION-ALL` |
| Spinner genérico (`animate-spin`, `.spinner`, `Loader2`) | GATE | `SLOP-SPINNER` |
| Copy genérico de empty ("No data found") | GATE | `SLOP-EMPTY-COPY` |
| Copy genérico de error ("Something went wrong") | GATE | `SLOP-ERROR-COPY` |
| Gradiente púrpura→azul de AI | GATE | `SLOP-AI-GRADIENT` |
| Secciones faltantes del design system | GATE | (documento) |
| Inter/Roboto sin modificar | Advisory | `SLOP-INTER-ROBOTO` |
| Radio único / duración única / cursor por defecto | Advisory | `SLOP-UNIFORM-RADIUS`, `SLOP-UNIFORM-DURATION`, `SLOP-CURSOR-DEFAULT` |
| Grid 12-col por defecto, Material Icons, gris Tailwind | Advisory | `SLOP-GRID12`, `SLOP-MATERIAL-ICONS`, `SLOP-GRAY-PALETTE` |
| Emoji como icono | Advisory | `SLOP-EMOJI-ICON` |

**Regla:** si un check falla, o el diseño está mal o existe una clase de falso positivo documentada. **Nunca se debilita el check para que pase.**

> Salida esperada antes de generar la primera pantalla: `PASS 0 gate(s)`.

---

## Reglas de Oro de la Edición Experimental

1. **Nunca generar código antes del design system.** El código sigue al diseño.
2. **Una pregunta a la vez.** No overwhelm.
3. **Siempre mostrar progreso.** El usuario debe saber dónde está.
4. **Las alternativas deben ser visualmente DISTINTAS y ARRIESGADAS.** No 4 versiones de lo mismo.
5. **"Otra" siempre disponible.** El usuario debe poder romper el marco.
6. **Documentar prohibiciones explícitas.** Lo que NO se debe hacer es tan importante.
7. **El design system es ley.** Una vez aprobado, todo el código se justifica contra él.
8. **Microcopy es diseño.** Los estados especiales son oportunidades de personalidad máxima.
9. **Motion requiere especificación.** Tipo, duración, easing, propósito, librería.
10. **La imperfección intencional es un feature.** 1deg de rotación, textura al 5%, leading de 0.85.
11. **Explorar con imágenes ANTES de código.** Los modelos de imagen proponen layouts que los agentes de código nunca se atreverían.
12. **El riesgo visual es el objetivo.** Si no da miedo implementarlo, no es lo suficientemente experimental.
13. **La tipografía NO es decorativa.** Es arquitectura, es narrativa, es la voz de la app.
14. **Cada interacción debe ser memorable.** Un hover que solo cambia de color es un hover fallido.
15. **El responsive no es "más pequeño".** Es una reimaginación del layout para el viewport.
16. **El sonido es diseño.** Un "ding" genérico del sistema es tan slop como un gradiente púrpura. Silencio, ritmo y audio deben ser decisiones tan conscientes como el color.
17. **La luz tiene dirección.** Iluminar no es "agregar sombras"; es decidir de dónde viene la luz y qué resalta.
18. **El tempo define la emoción.** Una misma animación con otra duración cambia el significado. La duración es un token, no un capricho.
19. **El cursor es parte de la escena.** No un puntero que flota sobre tu mundo: un personaje dentro de él.
20. **Las opcionales son palanca, no relleno.** Fricción y ancla temporal son preguntas que solo valen si el usuario quiere más profundidad; nunca forzarlas.
21. **Deriva, no elijas.** Un estilo elegido de una tabla es slop con otro vocabulario. Cada eje se traza a un artefacto del dominio; importar es una excepción declarada, nunca la base.
22. **La accesibilidad es piso, no tope.** La personalidad se diseña por encima del piso: foco visible, zoom, contraste, teclado y bypass de la fricción.
23. **La degradación es diseño.** `prefers-reduced-motion`, `forced-colors`, sin WebGL y tier bajo tienen una composición definida, no un "apagado".
24. **Un efecto sin fallback es una deuda.** Cada shader, blend mode y partícula declara su escalera y su costo.
25. **Lo verifica un script.** El design system se audita con `check-slop.py` antes de la primera pantalla.
26. **La voz es un token.** El copy no se inventa por pantalla: sale de la ficha de voz, con persona, longitud y vocabulario prohibido.
27. **Sin matriz de estados, no hay componente.** `focus-visible`, `disabled`, `loading` y `error` no son opcionales.
28. **El sistema se entrega en formato consumible.** `design-tokens.json`, `DESIGN.agent.md` y `design-decisions.md` son parte del diseño, no un extra.

---

## Mapa de Auditoría

| Sección | Verificación automática | Verificación manual |
|---|---|---|
| 0 Arqueología | — | ¿Cada eje se traza a un artefacto? ¿≤2 importados? |
| 1 Manifiesto | — | ¿Describe una identidad o una categoría? |
| 2 Paleta | `SLOP-AI-GRADIENT`, `SLOP-GRAY-PALETTE` | Contraste mínimo |
| 3 Tipografía | `SLOP-INTER-ROBOTO` | ¿Es activa o decorativa? |
| 4 Spacing | — | ¿Escala intencional o 8/16/24/32? |
| 5 Bordes | `SLOP-UNIFORM-RADIUS` | ¿Un solo radio? |
| 6 Sombras | — | ¿Dirección de luz? |
| 7 Motion | `SLOP-TRANSITION-ALL`, `SLOP-UNIFORM-DURATION` | ¿Cada animación tiene propósito? |
| 8 Navegación / layout | `SLOP-GRID12` | ¿Reimaginación o "más pequeño"? |
| 9 Componentes | `SLOP-SPINNER`, `SLOP-EMPTY-COPY`, `SLOP-ERROR-COPY` | Matriz de estados completa |
| 10 Assets | `SLOP-EMOJI-ICON`, `SLOP-MATERIAL-ICONS` | Licencias |
| 11 Prohibiciones | (todas) | — |
| 12 Referencias | — | ¿Por qué cada una? |
| 13 Notas técnicas | — | ¿Fallback por efecto? |
| 14 Sonido | — | Mute, opt-in, lifecycle |
| 15 Iluminación | — | Dirección de luz |
| 16 Tempo | `SLOP-UNIFORM-DURATION` | ¿Fases o uniforme? |
| 17 Cursor | `SLOP-CURSOR-DEFAULT` | ¿Touch y focus? |
| 18 Accesibilidad | — | Piso por dimensión |
| 19 Degradación | — | Condiciones cubiertas |
| 20 Performance | — | Presupuesto y escaleras |
| 21 Voz y microcopy | `SLOP-EMPTY-COPY`, `SLOP-ERROR-COPY` | Vocabulario prohibido; copy de estados |
| 22 Entrega y artefactos | — | ¿Existen los 4 artefactos? |

---

## Prompt de Activación Rápida

```
Activa la skill Anti-Slop Design Architect — Edición Experimental.
Quiero diseñar [tipo de app] que se sienta [adjetivo arriesgado].
[Opcional: No tengo claro el estilo, guíame con el cuestionario].
[Opcional: Quiero que primero explores visualmente con imágenes].
```
