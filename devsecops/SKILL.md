---
name: devsecops
description: "DevSecOps y seguridad del pipeline generalista. Cubre shift-left, seguridad en CI/CD, supply chain security, Infrastructure as Code security, secret scanning, y cultura de seguridad. Actívala al integrar seguridad en el SDLC, configurar pipelines o transformar cultura de equipo."
disable-model-invocation: true
---

# DevSecOps

Guía de integración de seguridad en el ciclo de vida del desarrollo y operaciones.

---

## Shift-Left Security

> "Es 100x más barato fixear un bug en diseño que en producción."

### Fases de seguridad en SDLC

```
Plan          → Threat modeling, requisitos de seguridad
  ↓
Design        → Secure architecture review, privacy by design
  ↓
Develop       → SAST, secret scanning, peer review con checklist de seguridad
  ↓
Build         → SCA, dependency check, image scanning, signing
  ↓
Test          → DAST, fuzzing, pentest automatizado
  ↓
Deploy        → IaC scanning, config validation, approval gates
  ↓
Operate       → Runtime protection, RASP, CSPM
  ↓
Monitor       → SIEM, threat intel, incident response
```

### Responsabilidades compartidas

| Rol | Responsabilidad de seguridad |
|-----|------------------------------|
| **Developers** | Código seguro, input validation, no secrets en código, tests de seguridad |
| **DevOps/SRE** | Pipeline seguro, hardening de infra, secret management, monitoring |
| **Security** | Threat modeling, políticas, tooling, coaching, incident response |
| **Product** | Security requirements, risk acceptance, privacy features |
| **Management** | Budget, risk appetite, compliance, culture |

---

## Seguridad en CI/CD

### Pipeline segura

```
Source Code
   │
   ├── Secret Scanning (GitLeaks, TruffleHog, GitGuardian)
   ├── SAST (Semgrep, SonarQube, Checkmarx)
   └── Lint + Unit Tests
   │
Build
   ├── SCA (Snyk, OWASP Dependency-Check)
   ├── Container Scan (Trivy, Clair)
   └── Image Signing (cosign, Notary)
   │
Test
   ├── DAST (OWASP ZAP, Burp Suite CI)
   ├── Integration Tests
   └── IaC Scan (Checkov, tfsec)
   │
Deploy
   ├── Policy Gate (OPA, Sentinel)
   ├── Approval para prod
   └── Automated Rollback
   │
Runtime
   ├── CSPM (Prowler, ScoutSuite)
   ├── RASP / Runtime Protection
   └── Compliance Drift Detection
```

### Gates de seguridad
```
1. FAIL en secret detection → Block build
2. FAIL en SAST (Critical/High) → Block merge
3. FAIL en SCA (CVE Critical with exploit) → Block build
4. FAIL en container scan (Critical OS vuln) → Block deploy
5. FAIL en DAST (SQLi, RCE confirmed) → Block release
6. FAIL en IaC scan (public S3, open security group) → Block deploy
```

### Seguridad del pipeline mismo
- Runner isolation: no compartir runners entre equipos no confiables
- Secrets en CI: usar native secret management (GitHub Secrets, GitLab CI/CD Variables, Vault)
- No imprimir secrets en logs
- Branch protection: require PR, require reviews, require status checks
- Signed commits (GPG, SSH signing)
- Immutable builds: mismo input = mismo output (reproducible)

---

## Supply Chain Security

### SBOM en cada build
```
Generar: CycloneDX o SPDX
Almacenar: Adjunto al artefacto, en registry
Escaneo: Comparar contra NVD, advisory databases
Alertar: Notificar si nueva CVE afecta artefacto desplegado
```

### Firmas y provenance
```
1. Firmar commits: git commit -S (GPG) o git commit --gpg-sign
2. Firmar imágenes: cosign sign --key cosign.key image:tag
3. Verificar en deploy: cosign verify --key cosign.pub image:tag
4. SLSA provenance: generar attestation de build
5. Binary authorization: solo imágenes firmadas por CI trusted
```

### Dependencias
- Pin versions: `package==1.2.3` no `package>=1.2.3`
- Hash verification: `requirements.txt` con hashes, `package-lock.json`
- Private registry: Nexus, Artifactory, GitHub Packages (no descargar directo de internet en build)
- Vendor dependencies: commitear en repo o private registry

---

## Secret Management en CI/CD

### Anti-patrones
```
❌ Secrets en código fuente
❌ Secrets en variables de entorno del runner (compartidas)
❌ Secrets en logs de build
❌ Hardcodear API keys en Dockerfiles
❌ .env files en repos
```

### Patrones correctos
```
✅ GitHub/GitLab native secrets (encrypted, auditado)
✅ Vault integration: vault kv get -field=api_key secret/ci
✅ Dynamic credentials: Vault AWS STS, database dynamic roles
✅ Short-lived tokens: OIDC federation (no long-lived secrets)
✅ Secret scanning en pre-commit hooks
```

### OIDC / Workload Identity
```
GitHub Actions → OIDC token → Cloud provider (AWS/Azure/GCP)
→ Cloud provider emite token temporal con rol específico
→ No secrets almacenados en CI
→ Rotación automática implícita
```

---

## Cultura de Seguridad

### Security Champions
- Un developer por equipo con interés en seguridad
- 10-20% de su tiempo en seguridad
- Puente entre Security y Development
- Training avanzado, acceso a threat intel

### Training
- **Onboarding**: Seguridad básica, políticas, reporting
- **Anual**: Phishing simulation, awareness general
- **Rol específico**: Secure coding para devs, cloud security para SREs
- **Just-in-time**: Training antes de usar tecnología nueva

### Gamificación
- CTFs internos
- Bug bounty interno
- Leaderboard de vulnerabilidades encontradas y remediated
- Reconocimiento público

### Métricas de cultura
- % de devs con training de secure coding
- Tiempo medio de fix de vulnerabilidades (MTTR)
- Vulnerabilidades por release (tendencia decreciente)
- % de PRs con security review
- Adopción de secret scanning (commits bloqueados)

---

## Tooling por fase

| Fase | Herramientas | Integración |
|------|--------------|-------------|
| Pre-commit | git-secrets, talisman, pre-commit hooks | Local dev |
| CI Secret Scan | GitLeaks, TruffleHog, GitGuardian | Pipeline |
| SAST | Semgrep, SonarQube, Checkmarx, CodeQL | Pipeline |
| SCA | Snyk, Dependabot, OWASP DC, Mend | Pipeline + IDE |
| DAST | OWASP ZAP, Burp Suite, Acunetix | Staging pipeline |
| Container | Trivy, Clair, Snyk Container, Anchore | Build + Registry |
| IaC | Checkov, tfsec, Terrascan, cfn-nag | Pipeline |
| Runtime | Falco, Sysdig, Aqua, Prisma Cloud | K8s / Cloud |
| CSPM | Prowler, ScoutSuite, Prisma, Wiz | Cloud continuo |
| SIEM | Splunk, Sentinel, Elastic, Wazuh | Operaciones |

---

## Checklist DevSecOps

- [ ] Threat modeling en fase de diseño de features críticas
- [ ] SAST en CI con fail en findings críticos
- [ ] Secret scanning en pre-commit + CI
- [ ] SCA con SBOM generado en cada build
- [ ] Container scanning antes de push a registry
- [ ] Image signing con verificación en deploy
- [ ] DAST en staging antes de producción
- [ ] IaC scanning con policy as code
- [ ] Approval gate manual para deploy a prod
- [ ] Automated rollback en caso de anomaly
- [ ] OIDC/workload identity para CI/cloud (no long-lived secrets)
- [ ] Security champions en cada equipo de desarrollo
- [ ] Secure coding training anual
- [ ] Métricas de seguridad visibles para equipos
- [ ] Blameless post-mortems para incidentes de seguridad
