---
name: security-fundamentals
description: "Fundamentos de seguridad informática generalista. Cubre el triángulo CIA, principios de seguridad (least privilege, defense in depth, fail secure), threat modeling (STRIDE, PASTA, LINDDUN), análisis de riesgos (DREAD, CVSS), y taxonomía de amenazas. Actívala al diseñar cualquier sistema, evaluar riesgos o establecer baseline de seguridad."
disable-model-invocation: true
---

# Fundamentos de Seguridad

Guía generalista de conceptos, principios y metodologías de seguridad aplicables a cualquier stack tecnológico.

---

## Triángulo CIA + Extensiones

| Dimensión | Definición | Ejemplo de fallo |
|-----------|-----------|------------------|
| **Confidencialidad** | Acceso solo a autorizados | Data breach, exfiltración |
| **Integridad** | Datos no alterados sin autorización | Tampering, supply chain attack |
| **Disponibilidad** | Sistema accesible cuando se necesita | DDoS, ransomware, outage |
| **Autenticidad** | Origen verificable | Spoofing, phishing |
| **No repudio** | Acciones trazables a un actor | Negación de transacciones |
| **Privacidad** | Control del titular sobre sus datos | Uso secundario no consentido |

---

## Principios de diseño seguro

### 1. Defense in Depth
No confiar en una sola capa. Múltiples controles independientes:
- Firewall → WAF → Input validation → Parametrized queries → Least privilege DB
- Si una capa falla, la siguiente detiene o limita el impacto.

### 2. Least Privilege
Cada componente (usuario, servicio, proceso) tiene el mínimo acceso necesario:
- Cuentas de servicio con permisos granulares (no admin/root)
- RBAC con scopes restringidos
- Network segmentation (microsegmentación)

### 3. Fail Secure (Secure by Default)
Si algo falla, el sistema debe quedar en estado seguro, no abierto:
- Firewall: default-deny
- AuthZ: denegar si el token no se puede validar
- Feature flags: desactivar si el servicio de config no responde

### 4. Separation of Duties (SoD)
Ninguna persona/control único puede completar una acción crítica:
- Deploy requiere 2 approvers
- Separar desarrollo/producción
- Segregación de ambientes (dev/staging/prod)

### 5. Economy of Mechanism
Menos código = menor superficie de ataque. Evitar complejidad innecesaria:
- No habilitar features por defecto
- Desactivar módulos no usados
- Reducir dependencias

### 6. Complete Mediation
Cada acción sensible debe verificar autorización, sin atajos:
- No confiar en que "el frontend ya validó"
- Revalidar permisos en cada request (stateless auth)
- No cachear decisiones de autorización sin TTL corto

### 7. Open Design
La seguridad no debe depender del secreto del diseño:
- Algoritmos criptográficos públicos y auditados
- No "security through obscurity"
- Asumir que el atacante conoce la arquitectura

---

## Threat Modeling

### STRIDE (Microsoft)

| Amenaza | Propiedad violada | Ejemplo |
|---------|-------------------|---------|
| **S**poofing | Autenticidad | Falsificar JWT, suplantar identidad |
| **T**ampering | Integridad | Modificar request en tránsito |
| **R**epudiation | No repudio | Logs insuficientes para auditoría |
| **I**nformation Disclosure | Confidencialidad | Error messages con stack traces |
| **D**enial of Service | Disponibilidad | DDoS, resource exhaustion |
| **E**levation of Privilege | Autorización | Escalar de user a admin |

### Proceso de Threat Modeling

1. **Diagramar** el sistema (Data Flow Diagram nivel 0, 1, 2)
2. **Identificar threats** con STRIDE por cada elemento del DFD
3. **Clasificar** con DREAD o similar
4. **Mitigar** (eliminar, reducir, transferir, aceptar)
5. **Validar** y repetir en cada cambio arquitectónico significativo

### DREAD Scoring (0-10 por categoría)

| Factor | Pregunta | Score alto |
|--------|----------|------------|
| **D**amage | ¿Qué daño causa? | RCE, data breach total |
| **R**eproducibility | ¿Qué tan fácil es reproducir? | Cada vez, sin auth |
| **E**xploitability | ¿Qué tan fácil es explotar? | CURL/POST simple |
| **A**ffected users | ¿Cuántos usuarios afecta? | Todos los clientes |
| **D**iscoverability | ¿Qué tan fácil es encontrar? | Endpoint público, documentado |

**Score total**: (D+R+E+A+D) / 5
- 0-3: Bajo
- 4-6: Medio
- 7-10: Crítico

### PASTA (Process for Attack Simulation and Threat Analysis)
Foco en negocio + técnico. 7 etapas:
1. Definir objetivos de negocio
2. Definir alcance técnico y assets
3. Decompose application (DFD)
4. Analizar threats
5. Vulnerability & weakness analysis
6. Attack modeling & simulation
7. Risk analysis & residual risk

---

## Análisis de Riesgo

### Formula básica
```
Riesgo = Probabilidad × Impacto
```

### Matriz de riesgo (5×5)

| Prob \ Impacto | Negligible | Bajo | Medio | Alto | Crítico |
|-----------------|------------|------|-------|------|---------|
| **Casi seguro** | Medio | Medio | Alto | Crítico | Crítico |
| **Probable** | Bajo | Medio | Alto | Alto | Crítico |
| **Posible** | Bajo | Medio | Medio | Alto | Alto |
| **Improbable** | Bajo | Bajo | Medio | Medio | Alto |
| **Raro** | Bajo | Bajo | Bajo | Medio | Medio |

### Tratamiento del riesgo

| Estrategia | Cuándo usar | Ejemplo |
|------------|-------------|---------|
| **Mitigar** | Reducir probabilidad o impacto | WAF, input validation, patching |
| **Transferir** | Tercerizar el riesgo | Cyber insurance, cloud provider SLA |
| **Aceptar** | Costo de mitigación > impacto | Riesgo residual documentado |
| **Evitar** | Eliminar la causa | No almacenar datos sensibles innecesarios |

---

## Taxonomía de amenazas comunes

### Por origen
- **Externo**: APT, script kiddies, hacktivists, crimen organizado
- **Interno (malicioso)**: Insider threat, data exfiltration, sabotaje
- **Interno (no intencional)**: Error humano, misconfiguration, phishing victim

### Por vector
- Red: MITM, spoofing, DDoS
- Aplicación: Inyección, XSS, IDOR, deserialization
- Humano: Phishing, social engineering, shoulder surfing
- Físico: Robo de dispositivos, tailgating

### Por motivación
- Financiero: Ransomware, fraude, cryptojacking
- Espionaje: IP theft, state-sponsored
- Hacktivismo: Defacement, DDoS político
- Curiosidad / accidente

---

## Checklist de fundamentos

- [ ] Threat model realizado para cada sistema crítico
- [ ] Principio de least privilege aplicado a usuarios y servicios
- [ ] Defense in depth: al menos 3 capas de control por asset crítico
- [ ] Fail secure validado: ¿qué pasa si el servicio X cae?
- [ ] Separation of duties en operaciones críticas (deploy, acceso a prod)
- [ ] Matriz de riesgo actualizada y revisada trimestralmente
- [ ] No se depende de "security through obscurity"
- [ ] Logs de seguridad habilitados y centralizados
- [ ] Data classification definida (pública, interna, confidencial, restringida)
