---
name: secure-architecture
description: "Arquitectura segura generalista. Cubre Zero Trust, microsegmentación, secure design patterns, hardening de infraestructura, security boundaries, y decisiones arquitectónicas de seguridad. Actívala al diseñar sistemas, revisar arquitecturas o definir perimetros de seguridad."
disable-model-invocation: true
---

# Arquitectura Segura

Guía de decisiones arquitectónicas de seguridad aplicables a cloud, on-premise e híbrido.

---

## Zero Trust Architecture (ZTA)

> "Never trust, always verify."

### Pilares

1. **Verify explicitly**: Autenticar y autorizar cada acceso basado en múltiples señales (identidad, dispositivo, ubicación, comportamiento)
2. **Use least privilege**: Acceso just-in-time (JIT) y just-enough-access (JEA)
3. **Assume breach**: Microsegmentación, cifrado end-to-end, monitorización continua

### Implementación práctica

```
Usuario → Identity Provider (IdP) → MFA → Device Trust → 
→ Microsegmentación de red → Service Mesh mTLS → 
→ RBAC/ABAC por recurso → Audit logging
```

### Señales de contexto
- Identidad: User/Service Principal
- Dispositivo: Compliance state, patch level, encryption
- Ubicación: IP geolocation, corporate network vs público
- Behavorial: UEBA (anomalías de uso)
- Threat intel: IPs maliciosas conocidas

---

## Security Boundaries

### Tipos de fronteras

| Frontera | Control | Ejemplo |
|----------|---------|---------|
| **Perimeter** | Firewall, WAF, DDoS protection | CloudFlare, AWS Shield |
| **Network** | VLANs, subnets, NSGs | Microsegmentación VPC |
| **Application** | AuthZ, input validation, rate limiting | OAuth2 scopes, API gateway |
| **Data** | Encryption at rest/transit, classification | AES-256-GCM, TLS 1.3 |
| **Identity** | IAM, RBAC, PIM | Azure AD, Okta |

### Microsegmentación
Dividir la red en zonas pequeñas con políticas estrictas:
- **DMZ**: Público, WAF, reverse proxy
- **App tier**: Solo acceso desde DMZ, no salida directa a internet
- **Data tier**: Solo acceso desde App tier, puertos mínimos
- **Management**: Bastion hosts, jump boxes, acceso PAM

```
Internet
   │
   ▼
[ WAF / CDN ] ←── Perimeter
   │
   ▼
[ API Gateway ] ←── Application boundary
   │
   ▼
[ App Services ] ←── Internal network segment
   │
   ▼
[ Database ] ←── Data boundary (encrypted)
```

---

## Secure Design Patterns

### 1. Gatekeeper / Policy Enforcement Point (PEP)
Un punto único que aplica políticas antes de permitir acceso:
- API Gateway con authN/authZ
- Service mesh sidecar (Envoy/Istio)
- Reverse proxy con mTLS

### 2. Secure Pipe
Cifrado en tránsito obligatorio:
- TLS 1.3 para todo tráfico externo
- mTLS para servicio-a-servicio
- VPN/Private Link para cloud híbrido

### 3. Sandbox / Isolation
Ejecutar código no confiable en ambientes restringidos:
- Containers sin privilegios, read-only rootfs
- gVisor, Firecracker para sandboxing
- Browser: CSP, iframe sandbox, COOP/COEP

### 4. Secure Factory
Centralizar la creación de objetos sensibles:
- Secret managers (HashiCorp Vault, AWS Secrets Manager)
- Certificate authorities internas
- Token issuance services

### 5. Compartmentalization
Dividir datos y funciones para limitar blast radius:
- Multi-tenant isolation (row-level, schema-level, database-level)
- Feature flags con kill switches
- Circuit breakers para contener fallos

---

## Hardening de infraestructura

### Checklist de hardening

- [ ] **OS/Container**: Minimal base image (distroless, Alpine), no root, read-only filesystem
- [ ] **Network**: Default deny, solo puertos necesarios, no exposición pública de management
- [ ] **Servicios**: Desactivar features no usadas, headers de seguridad, rate limiting
- [ ] **Data**: Cifrado at rest (AES-256), cifrado in transit (TLS 1.3), key rotation
- [ ] **Identidad**: No credenciales hardcodeadas, uso de managed identities, rotación automática
- [ ] **Logging**: Centralizado, inmutable, con integridad (WORM storage)
- [ ] **Backup**: 3-2-1 rule, encrypted, tested restore procedures

### CIS Benchmarks
Aplicar benchmarks del Center for Internet Security:
- CIS Docker Benchmark
- CIS Kubernetes Benchmark
- CIS AWS Foundations
- CIS Azure Foundations
- CIS Windows/Linux Server Benchmarks

---

## Decisiones arquitectónicas de seguridad

| Decisión | Opción A | Opción B | Cuándo elegir A vs B |
|----------|----------|----------|----------------------|
| AuthN | OAuth2/OIDC | SAML | OIDC para APIs/moderno; SAML para enterprise legacy |
| AuthZ | RBAC | ABAC | RBAC para estructura simple; ABAC para políticas dinámicas |
| Segregación | Logical (namespace) | Physical (cluster/VM) | Logical para eficiencia; Physical para compliance estricto |
| Secrets | External vault | Env vars + encryption | Vault para escala/rotación; Env vars para simple con encryption |
| Network | Flat VPC | Microsegmented | Flat solo para dev/test; prod siempre segmentado |
| API exposure | API Gateway | Direct | Gateway para rate limiting, WAF, analytics |
| DB access | Direct connection | Connection pooler + vault | Pooler + vault para least privilege y audit |

---

## Supply Chain Security

### SBOM (Software Bill of Materials)
- Generar SBOM en cada build (SPDX, CycloneDX)
- Almacenar con el artefacto
- Escaneo continuo de vulnerabilidades en dependencias

### SLSA Framework (Supply-chain Levels for Software Artifacts)

| Nivel | Descripción |
|-------|-------------|
| 1 | Provenance: saber de dónde viene el software |
| 2 | Signed provenance + hosted build service |
| 3 | Hardened builds: hermético, reproducible, auditable |
| 4 | Two-party review + hermetic build |

### Controles
- Firmar commits (GPG, Sigstore/cosign)
- Firmar imágenes de container
- Reproducible builds
- Dependency pinning + hash verification
- Private artifact repositories con scanning

---

## Checklist de arquitectura segura

- [ ] Zero Trust: cada acceso verificada, sin confiar en la red
- [ ] Microsegmentación: al menos 3 zonas de red (DMZ/App/Data)
- [ ] mTLS entre servicios internos
- [ ] No secrets en código; uso de vault/secret manager
- [ ] API Gateway como PEP para todo tráfico externo
- [ ] Hardening CIS aplicado a OS, containers, cloud
- [ ] SBOM generado y escaneado en cada release
- [ ] Backup cifrado con restore testeado
- [ ] Logging centralizado e inmutable
- [ ] Kill switches / circuit breakers para contener incidentes
- [ ] Disaster Recovery plan documentado y testeado
