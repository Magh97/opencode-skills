---
name: compliance-governance
description: "Cumplimiento normativo y gobernanza de seguridad. Cubre GDPR, SOC 2, ISO 27001, NIST CSF, PCI-DSS, políticas de seguridad, risk management, y auditorías. Actívala al preparar certificaciones, definir políticas o gestionar riesgos organizacionales."
disable-model-invocation: true
---

# Cumplimiento y Gobernanza

Guía de frameworks normativos, gestión de riesgos y gobernanza de ciberseguridad.

---

## Frameworks principales

### NIST Cybersecurity Framework (CSF) 2.0

| Función | Descripción | Ejemplos |
|---------|-------------|----------|
| **GOVERN** | Gobernanza, estrategia, políticas | Risk appetite, roles, oversight |
| **IDENTIFY** | Inventario, clasificación, assessment | Asset management, data classification |
| **PROTECT** | Controles preventivos | Access control, training, encryption |
| **DETECT** | Capacidades de detección | Monitoring, anomalies, SIEM |
| **RESPOND** | Respuesta a incidentes | IR plan, communications, mitigation |
| **RECOVER** | Recuperación y resiliencia | Backups, BCP, lessons learned |

### ISO/IEC 27001:2022
- **ISMS** (Information Security Management System)
- 93 controles en 4 categorías: Organizational, People, Physical, Technological
- Requiere: scope, risk assessment, statement of applicability, auditoría externa
- Certificación válida por 3 años con auditorías de seguimiento anuales

### SOC 2 (Service Organization Control)
- **Trust Services Criteria**: Security (obligatorio), Availability, Confidentiality, Processing Integrity, Privacy
- **Type I**: Diseño de controles en un punto de tiempo
- **Type II**: Operación efectiva de controles durante un período (6-12 meses)
- Requiere: políticas, procedimientos, evidencia, auditor externo (CPA)

### GDPR (General Data Protection Regulation)
- Aplicable si procesas datos de residentes EU
- **Principios**: Lawfulness, purpose limitation, data minimization, accuracy, storage limitation, integrity/confidentiality, accountability
- **Derechos del titular**: Acceso, rectificación, supresión (right to be forgotten), portabilidad, oposición
- **Bases legales**: Consentimiento, contrato, obligación legal, interés vital, interés público, interés legítimo
- **Breach notification**: 72h a autoridad, sin demora innecesaria al titular
- **DPO**: Obligatorio para autoridad pública, monitoreo sistemático a gran escala, datos sensibles a gran escala
- **Sanciones**: Hasta €20M o 4% del turnover global

### PCI-DSS (Payment Card Industry)
- Aplicable si almacenas, procesas o transmites datos de tarjetas
- 12 requisitos, 6 objetivos
- Niveles 1-4 según volumen de transacciones
- **SAQ** (Self-Assessment Questionnaire) o **ROC** (Report on Compliance) para Level 1
- Tokenización preferida sobre almacenamiento de PAN

### Otros frameworks
- **HIPAA**: Salud en USA (PHI protection)
- **CCPA/CPRA**: Privacidad en California
- **LGPD**: Brasil (similar a GDPR)
- **NIS2**: Directiva EU de ciberseguridad (2024)
- **CIS Controls**: 18 controles prioritarios, práctico y accionable

---

## Gestión de Riesgos

### Proceso ISO 27005 / NIST RMF

```
1. Context establishment    → Alcance, criterios, asset inventory
2. Risk assessment          → Identificación, análisis, evaluación
3. Risk treatment           → Mitigar, transferir, evitar, aceptar
4. Risk acceptance          → Residual risk aprobado por liderazgo
5. Risk communication       → Reportes, dashboards
6. Risk monitoring          → Continuo, triggers, revisiones
```

### Risk Register

| ID | Asset | Threat | Vulnerability | Likelihood | Impact | Risk | Treatment | Owner |
|----|-------|--------|---------------|------------|--------|------|-----------|-------|
| R01 | Customer DB | Data breach | SQLi | Medium | Critical | High | Mitigate: WAF + input validation | CISO |
| R02 | AWS Account | Account takeover | Weak IAM | Low | Critical | Medium | Mitigate: MFA + PAM | Cloud Lead |

### Risk Appetite
- **Averse**: Evitar casi todo riesgo (finanzas, salud)
- **Minimal**: Solo riesgos esenciales para el negocio
- **Cautious**: Aceptar con controles compensatorios
- **Open**: Aceptar riesgos para innovación (startups)

---

## Políticas de Seguridad

### Jerarquía

```
1. Security Policy (Board/CISO)
   └── 2. Standards (técnicos, obligatorios)
        └── 3. Procedures (paso a paso)
             └── 4. Guidelines (recomendaciones)
                  └── 5. Baselines (configuración mínima)
```

### Políticas esenciales

| Política | Contenido clave |
|----------|-----------------|
| **Information Security** | Alcance, roles, clasificación, incidentes |
| **Acceptable Use** | Uso de assets, internet, email, dispositivos personales |
| **Access Control** | RBAC, provisioning, review, termination |
| **Password / Authentication** | Complejidad, MFA, gestión |
| **Data Protection** | Clasificación, handling, retention, disposal |
| **Incident Response** | Roles, fases, comunicación, legal |
| **Business Continuity** | RTO, RPO, planes, testing |
| **Vendor Management** | Due diligence, contract clauses, audit rights |
| **Remote Work** | VPN, device security, clean desk |

### Documentación efectiva
- Escrita en lenguaje claro, no legal-ese excesivo
- Aprobada por liderazgo (CISO, CEO, Board)
- Comunicada a todo el personal (training, acknowledgment)
- Revisada anualmente o ante cambios significativos
- Enforcement definido (consecuencias claras)

---

## Auditorías

### Tipos

| Tipo | Quién | Enfoque |
|------|-------|---------|
| **Internal audit** | Equipo interno (independiente) | Cumplimiento de políticas, gap analysis |
| **External audit** | Tercero (certificación) | ISO 27001, SOC 2, PCI-DSS |
| **Regulatory audit** | Autoridad | GDPR, HIPAA, banking regulators |
| **Technical audit** | Pentesters / consultants | Vulnerabilidades, config review |
| **Vendor audit** | Cliente o tercero | Due diligence de proveedores |

### Preparación
```
1. Scope claro: qué sistemas, procesos, equipos
2. Evidence collection: políticas, logs, configs, training records
3. Gap analysis previo (self-assessment)
4. Remediación de findings críticos antes de la auditoría
5. Designar liaison (punto de contacto único)
6. NDA y reglas de compromiso
```

### Findings y remediation
- **Critical**: Riesgo inmediato, fix en 24-72h
- **High**: Riesgo significativo, fix en 1-2 semanas
- **Medium**: Mejora necesaria, fix en 1-3 meses
- **Low**: Observación, fix en próximo ciclo
- **Informational**: Buena práctica, no obligatorio

---

## Tercerización y Vendor Risk

### Due diligence
- Questionnaire de seguridad (SIG, VSAQ, custom)
- Certificaciones vigentes (SOC 2 Type II, ISO 27001)
- Pentest reports recientes (12 meses)
- Data processing agreements (DPA) para GDPR
- SLA de seguridad, breach notification, derecho a auditoría

### Contract clauses
- Seguridad mínima requerida (encripción, MFA, patching)
- Notificación de breach en 24-48h
- Derecho a auditoría anual
- Seguro cibernético del vendor
- Cláusula de terminación por incumplimiento de seguridad
- Data deletion post-terminación

---

## Checklist de compliance

- [ ] Framework seleccionado y mapeado (NIST CSF, ISO 27001, SOC 2)
- [ ] Risk register actualizado y revisado trimestralmente
- [ ] Risk appetite definido y aprobado por el Board
- [ ] Políticas de seguridad documentadas, aprobadas y comunicadas
- [ ] Training de seguridad anual para todo el personal
- [ ] Inventario de assets completo (hardware, software, data)
- [ ] Data classification implementada y etiquetada
- [ ] DPA firmado con todos los procesadores de datos
- [ ] DPO designado (si aplica GDPR)
- [ ] Proceso de breach notification documentado (72h GDPR)
- [ ] Auditorías internas trimestrales
- [ ] Auditoría externa anual (si certificación)
- [ ] Vendor risk assessments para proveedores críticos
- [ ] Business continuity plan testeado anualmente
- [ ] Métricas de seguridad reportadas al Board trimestralmente
