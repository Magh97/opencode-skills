---
name: application-security
description: "Seguridad de aplicaciones generalista. Cubre OWASP Top 10, secure coding, validación de entrada, gestión de sesiones, seguridad de APIs, y protección contra inyecciones, XSS, CSRF, IDOR, deserialización insegura. Actívala al desarrollar, revisar código o auditar aplicaciones."
disable-model-invocation: true
---

# Seguridad de Aplicaciones

Guía de secure coding y protección de aplicaciones web, móviles y APIs. Stack-agnostic.

---

## OWASP Top 10 (2021 → 2025)

| Rank | Riesgo | Descripción | Mitigación clave |
|------|--------|-------------|------------------|
| A01 | Broken Access Control | Escalada de privilegios, IDOR, path traversal | Deny by default, RBAC, indirect object references |
| A02 | Cryptographic Failures | Datos sensibles expuestos, cifrado débil | TLS 1.3, AES-256-GCM, no algoritmos legacy |
| A03 | Injection | SQLi, NoSQLi, LDAPi, Command injection | Parametrización, ORM, input validation |
| A04 | Insecure Design | Flujos sin controles de seguridad | Threat modeling, secure by design |
| A05 | Security Misconfiguration | Defaults inseguros, stack traces, features activas | Hardening, minimal surface, automated scanning |
| A06 | Vulnerable Components | Dependencias con CVEs | SCA, SBOM, patching automatizado |
| A07 | Auth Failures | Credenciales débiles, session hijacking | MFA, secure session management, password policy |
| A08 | Data Integrity Failures | Deserialización insegura, dependencias sin firmar | Firmas, safe deserialization, integrity checks |
| A09 | Logging Failures | Falta de logging, logs con datos sensibles | Centralized logging, redaction, tamper-proof |
| A10 | SSRF | Server-Side Request Forgery | URL validation, deny lists, network segmentation |

---

## Input Validation

### Regla de oro
> **All input is evil until proven otherwise.**

### Estrategia de defensa

1. **Whitelist > Blacklist**
   - Definir qué está permitido (regex positivo, enum, schema)
   - Nunca intentar filtrar "lo malo" (blacklist incompleta)

2. **Validación en capas**
   - Cliente: UX, no seguridad
   - API Gateway: schema validation (JSON Schema, OpenAPI)
   - Aplicación: business rules, type safety
   - Base de datos: constraints, foreign keys

3. **Sanitización contextual**
   - HTML: encode entities (`<` → `&lt;`)
   - SQL: parametrización (nunca concatenación)
   - OS commands: avoid shell; use exec with array
   - URLs: parse and whitelist schemes/hosts

### Ejemplos de validación

```
Email:    RFC 5322 subset + length limit + domain validation
Phone:    E.164 format only
File:     Extension whitelist + MIME type + magic bytes + size limit
URL:      Scheme whitelist (https only) + deny private IPs
ID:       UUID format or indirect reference map
Date:     ISO 8601 strict parsing (no strings libres)
```

---

## Inyecciones

### SQL Injection
```
❌ "SELECT * FROM users WHERE id = '" + userId + "'"
✅ Prepared statement: "SELECT * FROM users WHERE id = ?"
✅ ORM con parametrización automática
```

### Command Injection
```
❌ Runtime.exec("ping " + userInput)
✅ ProcessBuilder con lista de argumentos (no shell)
✅ Avoid OS commands; use libraries nativas
```

### LDAP Injection
```
❌ Filtro construido con concatenación
✅ LDAP encoder/escaper para caracteres especiales
```

### NoSQL Injection
```
❌ query: { $where: "this.user == '" + input + "'" }
✅ Driver con query builders tipados
✅ Input validation estricta antes de query
```

---

## XSS (Cross-Site Scripting)

### Tipos
- **Reflejado**: Payload en URL/params, respuesta inmediata
- **Almacenado**: Persiste en BD, afecta a múltiples usuarios
- **DOM-based**: Manipulación del DOM sin roundtrip al servidor

### Mitigación
```
1. Output encoding según contexto:
   - HTML body: HTML entity encoding
   - HTML attribute: Attribute encoding
   - JavaScript: JS encoding
   - URL: URL encoding
   - CSS: CSS encoding (evitar user input en CSS)

2. Content Security Policy (CSP)
   default-src 'self'; script-src 'self' https://cdn.example.com;
   object-src 'none'; base-uri 'self'; frame-ancestors 'none';

3. HttpOnly + Secure + SameSite=Strict cookies

4. X-XSS-Protection: 0 (legacy, desactivar para evitar bypasses)
```

---

## CSRF / Cross-Site Request Forgery

### Mitigación
```
1. Synchronizer Token Pattern (STP)
   - Token CSRF en formulario + cookie/headers
   - Validar que coinciden

2. Double Submit Cookie
   - Token en cookie + mismo token en header
   - SameSite=Strict cookies (mitigación moderna)

3. Custom Request Headers
   - X-Requested-With: XMLHttpRequest (no cross-origin sin CORS preflight)

4. Re-authentication para acciones críticas
   - Cambio de password, transferencias, eliminación de cuenta
```

---

## IDOR / Insecure Direct Object Reference

### Problema
Usuario accede a recursos manipulando IDs predecibles:
```
GET /api/orders/12345 → orden de otro usuario
GET /api/invoices/67890 → factura ajena
```

### Mitigación
```
1. Autorización en cada endpoint: ¿el usuario puede ver este recurso?
2. Indirect Object References: mapear IDs internos a tokens aleatorios
   - /api/orders/a1b2c3d4 (UUID) en vez de /api/orders/12345 (secuencial)
3. Query con filtro de ownership:
   SELECT * FROM orders WHERE id = ? AND user_id = ?
4. No exponer IDs de BD; usar UUIDs o hashes
```

---

## Deserialización Insegura

### Riesgo
Datos manipulados ejecutan código durante deserialización.

### Mitigación
```
1. Evitar deserialización de datos no confiables
2. Usar formatos seguros: JSON (no pickle, no Java serialization)
3. Type whitelisting: solo clases permitidas
4. Firmar datos serializados (HMAC) y validar antes de deserializar
5. Deserializar en sandbox con permisos mínimos
```

---

## Seguridad de APIs

### Autenticación
- OAuth 2.0 + PKCE para SPAs/mobile
- Client Credentials para M2M
- JWT con expiración corta (5-15 min) + refresh tokens rotativos
- API Keys solo para servicios internos o partners, nunca para usuarios finales

### Autorización
- Scope validation: token con `orders:read` no puede escribir
- Resource-based: verificar ownership del recurso
- Rate limiting por usuario + por IP

### Headers de seguridad
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Content-Security-Policy: default-src 'self'
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
Cache-Control: no-store (para respuestas sensibles)
```

### Versioning y deprecación
- Versionar APIs para permitir breaking changes seguros
- Deprecar versiones viejas con timeline público
- Forzar migración antes de EOL

---

## Gestión de Sesiones

### Mejores prácticas
- ID de sesión aleatorio, largo (128+ bits), generado CSPRNG
- Expiración: idle timeout (15-30 min) + absolute timeout (8-12 horas)
- Invalidación server-side en logout
- Regenerar ID de sesión después de login (prevenir fixation)
- No almacenar datos sensibles en sesión client-side (cookies JWT son stateless, no session storage)
- Secure, HttpOnly, SameSite=Strict para cookies de sesión

---

## File Upload Security

### Controles
```
1. Validar MIME type (Content-Type header)
2. Validar magic bytes (file signature)
3. Whitelist de extensiones
4. Size limit estricto
5. Rename file (UUID, no conservar nombre original)
6. Store outside webroot (no acceso directo por URL)
7. Scan con AV antes de procesar
8. No ejecutar archivos subidos (no interpretar PHP/JS en uploads)
```

---

## Checklist de AppSec

- [ ] Input validation con whitelist en todas las entradas
- [ ] Parametrización de queries (nunca concatenación)
- [ ] Output encoding contextual
- [ ] CSP configurado y estricto
- [ ] Cookies: Secure + HttpOnly + SameSite=Strict
- [ ] CSRF tokens o SameSite mitigación
- [ ] IDOR mitigado: autorización por recurso + IDs no predecibles
- [ ] Rate limiting en endpoints sensibles
- [ ] Deserialización segura: formatos simples, type whitelisting
- [ ] File upload: magic bytes + size + rename + scan
- [ ] Error handling: sin stack traces ni info sensible al cliente
- [ ] Dependency scanning (SCA) en CI/CD
- [ ] Security headers obligatorios en todas las respuestas
- [ ] Session management: timeout, regeneration, server-side invalidation
