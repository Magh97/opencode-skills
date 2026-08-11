---
name: design-review
description: "Revisión estructurada de diseño técnico. Checklist de evaluación: acoplamiento, escalabilidad, seguridad, costos, operabilidad. Formato de sesión de design review. Actívala al evaluar un diseño propuesto, antes de empezar a implementar, o cuando el usuario diga 'revisar diseño', 'design review', 'validar arquitectura', 'revisar el diseño de X'."
---

# Design Review — Validación de Diseño

Antes de escribir código, valida que el diseño no explote en producción.

---

## Checklist de design review

### 1. Acoplamiento y cohesión

- [ ] **Cada módulo tiene una razón para cambiar.** Si un cambio de negocio toca 4 módulos, hay acoplamiento.
- [ ] **Las dependencias van en una dirección.** Sin ciclos (A → B → A).
- [ ] **Los contratos entre módulos son explícitos.** (interfaces, eventos, API contracts). Nada de "importar la clase concreta del otro módulo".
- [ ] **No hay lógica de negocio duplicada.** Misma regla en dos módulos = bug futuro cuando cambie.

### 2. Escalabilidad

- [ ] **Los endpoints GET de listas tienen paginación.** Todos, sin excepción.
- [ ] **Las queries tienen índices que las soportan.** N+1 detectado y resuelto.
- [ ] **Los cálculos pesados son asíncronos** (background job, cola) si toman >2 segundos.
- [ ] **El diseño soporta 10x la carga esperada** sin cambios arquitectónicos. Si 10x rompe la BD, el diseño es frágil.
- [ ] **No hay `SELECT *` en queries core.** Solo columnas necesarias.

### 3. Seguridad

- [ ] **Autenticación en todos los endpoints que mutan datos o exponen datos privados.**
- [ ] **Autorización por rol/recurso.** No alcanza con "estar logueado".
- [ ] **Input validation en toda entrada externa** (body, query params, headers, path params).
- [ ] **Secrets fuera del código** (variables de entorno, vault, no strings hardcodeados).
- [ ] **CORS restringido a orígenes conocidos.** No `AllowAnyOrigin` en producción.
- [ ] **Rate limiting en endpoints públicos** (login, registro, endpoints sin auth).
- [ ] **Datos sensibles no se loguean** (passwords, tokens, PII).

### 4. Costos

- [ ] **El diseño usa servicios managed vs self-hosted con consciencia de costo.** (RDS vs EC2+PostgreSQL, SQS vs RabbitMQ en EC2).
- [ ] **No hay polling innecesario.** Si el frontend hace `setInterval(fetch, 3000)`, hay un problema de diseño.
- [ ] **Las consultas no traen datos que no se usan.** Over-fetching = costo de BD + bandwidth.
- [ ] **El cold start de serverless no degrada UX.** Si usas Lambda/Function, mide el arranque.

### 5. Operabilidad

- [ ] **Health check implementable.** ¿Cómo sabe el load balancer que el servicio está vivo?
- [ ] **Logging estructurado.** Con correlation ID, nivel adecuado (no todo es `Info`).
- [ ] **Métricas expuestas** (al menos: latencia p50/p99, error rate, throughput).
- [ ] **Errores dan contexto.** El mensaje de error le dice al dev y al usuario qué pasó (dos mensajes distintos: uno técnico en log, uno humano en respuesta).
- [ ] **Plan de deploy y rollback.** Si el release sale mal, ¿cómo se vuelve atrás?

### 6. Simplicidad (ponytail check)

- [ ] **¿Hay algo que se pueda eliminar?** Feature, abstracción, dependencia.
- [ ] **¿Hay un interface con una sola implementación?** No lo necesitas hoy.
- [ ] **¿Hay un factory para un solo producto?** `new` es suficiente.
- [ ] **¿El diseño asume escala que no llegará en 12 meses?** Postergar.

---

## Formato de sesión de design review

### Duración: 30-45 minutos

```
Min 0-5:   Autor presenta el diseño (solo el diagrama + 3 decisiones clave)
Min 5-10:  Preguntas de clarificación (no críticas aún)
Min 10-30: Revisión por checklist (todos los participantes)
Min 30-40: Identificar action items
Min 40-45: Decisión: ¿Aprobado / Aprobado con cambios / Re-diseñar?
```

### Participantes mínimos

- **Autor del diseño** (presenta)
- **1 dev senior que no participó en el diseño** (perspectiva fresca)
- **Tech Lead** (decide)

### Anti-patrones en design review

- ❌ El autor defiende el diseño en vez de escuchar.
- ❌ Revisores proponen alternativas sin decir qué problema resuelven.
- ❌ La review se convierte en debate de sintaxis (tabs vs spaces).
- ❌ Aprobar sin leer el diseño ("confío en vos").
- ❌ Bloquear por cosas que se pueden ajustar en implementación.

---

## Reporte de design review

Al finalizar, genera un reporte:

```markdown
# Design Review: [Feature/Sistema]

**Fecha:** [YYYY-MM-DD]
**Autor:** [nombre]
**Revisores:** [nombres]
**Resultado:** ✅ Aprobado / ⚠️ Aprobado con cambios / ❌ Re-diseñar

---

## Hallazgos

| # | Categoría | Severidad | Hallazgo | Recomendación |
|---|-----------|-----------|----------|---------------|
| 1 | Escalabilidad | 🔴 Crítico | Listado de órdenes sin paginación | Agregar page/pageSize con LIMIT/OFFSET |
| 2 | Seguridad | 🟡 Alto | Endpoint de cancelación sin verificar ownership | Validar que el usuario es dueño de la orden |
| 3 | Simplicidad | 🟢 Medio | Capa de repositorio con 1 método | Eliminar, usar DbContext directo |

---

## Action Items

- [ ] Agregar paginación a GET /api/orders — dueño: [nombre], ETA: [fecha]
- [ ] Agregar verificación de ownership en DELETE /api/orders/{id} — dueño: [nombre], ETA: [fecha]

---

## Decisiones tomadas

- Se aprueba el diseño con los 2 cambios requeridos.
- No se requiere segunda revisión. Los cambios se validan en PR.
```

---

## Workflow

1. **Recibe el diseño a revisar** (diagrama C4, design doc, spec, o descripción del usuario).
2. **Evalúa contra la checklist** de 6 categorías.
3. **Genera reporte** con hallazgos, severidad, y action items.
4. **Emite veredicto:** ✅ Aprobado / ⚠️ Cambios requeridos / ❌ Re-diseñar.

---

## Lo que NO debe hacer

- No hacer review de código. Esto es diseño. El código se revisa con `productivity-code-review`.
- No forzar la checklist completa para features pequeñas. Usar juicio: un endpoint GET simple no necesita las 24 preguntas.
- No reemplazar el criterio del equipo. La checklist es guía, no ley.
