---
name: identity-access-management
description: "Gestión de identidades y accesos generalista (IAM). Cubre autenticación, autorización, MFA, SSO, RBAC/ABAC/PBAC, Zero Trust Identity, PAM, y lifecycle de identidades. Actívala al diseñar auth, revisar permisos o auditar control de accesos."
disable-model-invocation: true
---

# Identity and Access Management (IAM)

Guía generalista de autenticación, autorización y gestión del ciclo de vida de identidades.

---

## Autenticación (AuthN)

> Probar quién eres.

### Factores
| Factor | Ejemplos | Fortaleza |
|--------|----------|-----------|
| Conocimiento | Password, PIN, pattern | Baja (phishable) |
| Posesión | TOTP, SMS, hardware key, push | Media-Alta |
| Inherencia | Huella, rostro, iris, voz | Alta (pero irrevocable) |
| Ubicación | GPS, corporate network | Contexto |
| Comportamiento | UEBA, typing cadence | Contexto |

### MFA obligatoria
- Todo acceso administrativo/privilegiado: MFA obligatoria
- Todo acceso a datos sensibles: MFA obligatoria
- Preferir: FIDO2/WebAuthn > TOTP app > Push > SMS
- SMS como último recurso (SIM swap attacks)

### Password Policy moderna
```
- Mínimo 12-16 caracteres
- No requerir complejidad arbitraria (NIST SP 800-63B)
- Revisar contra breach databases (Have I Been Pwned API)
- No expiry forzada salvo compromiso sospechado
- Bloqueo progresivo (no hard lockout)
- Salt + Argon2id (o bcrypt/scrypt)
```

### Protocolos

| Protocolo | Uso | Notas |
|-----------|-----|-------|
| OAuth 2.0 | Delegación de acceso | Nunca para autenticación directa |
| OpenID Connect (OIDC) | AuthN sobre OAuth 2.0 | ID Token (JWT) con claims estándar |
| SAML 2.0 | SSO enterprise legacy | XML, más pesado, bien soportado por IdPs |
| LDAP/LDAPS | Directorio, authN legacy | Usar LDAPS (TLS), no LDAP plano |
| Kerberos | Red Windows interna | Tickets, NTLM deprecated |
| FIDO2/WebAuthn | Passwordless / MFA | Phishing-resistant, preferido |

### Tokens
- **Access Token**: Corta duración (5-15 min), contiene scopes/claims
- **Refresh Token**: Larga duración (días/semanas), rotativo, almacenado seguro
- **ID Token (OIDC)**: Información de identidad, no para autorización de recursos

---

## Autorización (AuthZ)

> Qué puedes hacer.

### Modelos

#### RBAC (Role-Based Access Control)
```
User → Role → Permission → Resource
```
- Simple, escalable para organizaciones medianas
- Roles: admin, editor, viewer, auditor
- Desventaja: role explosion en sistemas complejos

#### ABAC (Attribute-Based Access Control)
```
IF user.department == resource.department
   AND user.clearance >= resource.classification
   AND time.hour BETWEEN 9 AND 17
   AND device.compliance == true
THEN allow
```
- Flexible, políticas dinámicas
- Más complejo de auditar y debuggear

#### PBAC / ReBAC (Policy/Relationship-Based)
- Google Zanzibar, Ory Keto, AWS Cedar
- Basado en relaciones: `user:alice owner doc:report1`
- Ideal para sistemas colaborativos (Google Docs, GitHub)

### Decisiones de autorización
- **Enforce at edge**: API Gateway, reverse proxy
- **Enforce at service**: Cada microservicio valida sus propios permisos
- **Centralized PDP (Policy Decision Point)**: OPA, AWS IAM, Azure ABAC
- **Distributed**: Cada servicio tiene política local sincronizada

### Anti-patrones
```
❌ AuthZ solo en frontend
❌ "IsAdmin" booleano como único control
❌ Confundir autenticación con autorización
❌ Hardcodear roles en código
❌ Sin logs de decisiones de autorización
```

---

## Single Sign-On (SSO)

### Arquitectura
```
Aplicación (SP) → Redirect → IdP (Okta/Azure AD) → AuthN → 
→ Token/SAML Assertion → SP valida → Sesión local
```

### Consideraciones de seguridad
- **Logout**: SLO (Single Logout) para invalidar todas las sesiones
- **Session timeout**: Sincronizar con IdP o ser más restrictivo
- **Token binding**: Vincular token a dispositivo/contexto
- **IdP compromise**: Impacto total; proteger IdP con máxima seguridad

### Identity Providers
- Enterprise: Azure AD, Okta, Ping Identity, OneLogin
- Cloud-native: AWS IAM Identity Center, Google Workspace, Auth0
- Open source: Keycloak, Authelia, Dex

---

## Privileged Access Management (PAM)

### Just-in-Time (JIT) Access
```
1. Usuario solicita acceso elevado
2. Workflow de aprobación (manager, SOC, etc.)
3. Acceso otorgado por tiempo limitado (1-4 horas)
4. Acceso revocado automáticamente
5. Sesión grabada y auditada
```

### Break-glass
- Cuentas de emergencia con procedimiento documentado
- Uso alerta inmediata al SOC
- Rotación de credenciales post-uso
- Acceso físico o dual-control para obtener credenciales

### PAM Solutions
- CyberArk, Delinea (Thycotic), BeyondTrust
- Cloud-native: AWS IAM Identity Center PAM, Azure PIM
- Open source: Teleport, Vault

---

## Lifecycle de Identidades

### Joiner-Mover-Leaver (JML)

| Fase | Acciones |
|------|----------|
| **Joiner** | Crear cuenta, asignar roles base, MFA setup, training |
| **Mover** | Revisar permisos, revocar accesos anteriores, asignar nuevos |
| **Leaver** | Desactivar inmediatamente, transferir ownership, retención de datos, revocar tokens |

### Service Accounts
- Crear por servicio, no genéricas (no "app-service-account")
- Managed identities / IAM roles preferidos sobre credenciales
- Rotación automática de credenciales
- No compartir entre equipos

---

## Zero Trust Identity

### Principios
1. Verify identity explicitly (strong AuthN)
2. Validate device health (MDM compliance)
3. Evaluate risk en cada acceso (adaptive AuthN)
4. Least privilege access (JIT, ephemeral)
5. Assume breach (segmentación, monitoring)

### Señales de riesgo
- Login desde ubicación inusual
- Dispositivo no administrado
- Múltiples fallos de MFA
- Velocidad imposible entre logins
- Tor/VPN conocido
- Credential stuffing patterns

### Respuesta adaptativa
- Step-up authentication (pedir MFA adicional)
- Bloqueo temporal
- Reducción de permisos (downgrade session)
- Alerta SOC

---

## Checklist de IAM

- [ ] MFA obligatoria para todo acceso privilegiado y datos sensibles
- [ ] Passwordless/FIDO2 como meta a largo plazo
- [ ] RBAC/ABAC implementado con deny-by-default
- [ ] AuthZ verificada en backend, no solo frontend
- [ ] SSO con SLO configurado
- [ ] JIT/PAM para acceso administrativo
- [ ] Lifecycle JML automatizado (SCIM provisioning)
- [ ] Service accounts con managed identities y rotación
- [ ] Adaptive risk-based authentication
- [ ] Logs de autenticación y autorización centralizados
- [ ] Revisión de accesos trimestral (access certification)
- [ ] Break-glass procedures documentadas y testeadas
