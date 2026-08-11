---
name: infrastructure-security
description: "Seguridad de infraestructura generalista. Cubre cloud security (AWS/Azure/GCP), container y Kubernetes security, network security, IaC security, y hardening de servidores. Actívala al desplegar infraestructura, configurar cloud o auditar entornos."
disable-model-invocation: true
---

# Seguridad de Infraestructura

Guía de hardening y configuración segura para cloud, containers, redes y servidores.

---

## Cloud Security

### Modelo de responsabilidad compartida

```
On-Premise:    [You: Todo]
IaaS:          [Provider: Facilities, Networking, Virtualization]
               [You: OS, Apps, Data, IAM, Network config]
PaaS:          [Provider: OS, Middleware, Runtime]
               [You: Apps, Data, IAM, App config]
SaaS:          [Provider: Casi todo]
               [You: Data, IAM, Config]
```

### Principios multi-cloud

1. **Identity is the perimeter**: IAM como firewall principal
2. **Encrypt everything**: At rest y in transit por defecto
3. **Audit everything**: CloudTrail, Activity Logs, Audit Logs
4. **Automate compliance**: Policy as Code, auto-remediation
5. **Least privilege**: Roles granulares, no admin/root por defecto

### Controles comunes (AWS/Azure/GCP)

| Control | AWS | Azure | GCP |
|---------|-----|-------|-----|
| Audit logs | CloudTrail | Activity Log | Cloud Audit Logs |
| Config scanning | Config / Security Hub | Azure Policy / Defender | Security Command Center |
| Encryption KMS | KMS | Key Vault | Cloud KMS |
| Network firewall | Security Groups / NACLs | NSGs | Firewall Rules |
| WAF | AWS WAF | Azure WAF | Cloud Armor |
| Secrets | Secrets Manager | Key Vault | Secret Manager |
| IAM | IAM / IAM Identity Center | Azure AD / RBAC | Cloud IAM |

### Cloud misconfigurations comunes
- Buckets/S3 containers públicos
- Security groups con 0.0.0.0/0
- IAM roles overprivileged
- Unencrypted volumes/databases
- Default passwords en managed services
- Logging desactivado
- Snapshots públicos

---

## Container Security

### Image security
```
1. Base image mínima (distroless, Alpine, scratch)
2. No root user (USER 1000)
3. Read-only root filesystem (readOnlyRootFilesystem)
4. No capabilities innecesarias (drop ALL, add solo las necesarias)
5. Scan de vulnerabilidades en CI (Trivy, Snyk, Clair)
6. Firmar imágenes (cosign, Notary)
7. No secrets en layers (usar BuildKit secrets)
8. Multi-stage build para reducir superficie
```

### Dockerfile hardening
```dockerfile
# ✅ Multi-stage, no root, minimal
FROM golang:1.23-alpine AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 go build -o main

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /app/main /main
USER nonroot:nonroot
EXPOSE 8080
ENTRYPOINT ["/main"]
```

### Runtime security
- Runtime protection (Falco, Sysdig, Aqua)
- No privileged containers
- Resource limits (CPU/memory) para prevenir DoS
- Network policies: default deny, whitelist
- PodSecurityAdmission / OPA Gatekeeper
- Seccomp profiles
- AppArmor/SELinux

---

## Kubernetes Security

### Cluster hardening
```
1. API Server:
   - AuthN: OIDC, webhook, certificados clientes
   - AuthZ: RBAC obligatorio, no anonymous auth
   - Admission controllers: PodSecurity, ResourceQuota, LimitRange

2. etcd:
   - Cifrado at rest (encryption provider)
   - Solo acceso desde API server (firewall)
   - Backups cifrados

3. Kubelet:
   - Autenticación y autorización habilitadas
   - Solo HTTPS
   - No read-only port

4. Network:
   - CNI con network policies (Calico, Cilium)
   - Service mesh con mTLS (Istio, Linkerd)
   - Ingress con TLS termination + WAF
```

### RBAC en K8s
```yaml
# ✅ Role mínimo
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: app-reader
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list"]
  resourceNames: ["app-config"]  # Scopeado
```

### Secrets en K8s
- **No usar** Secretes nativos sin cifrado etcd (base64 != encryption)
- Usar: External Secrets Operator, Vault CSI, Sealed Secrets
- Rotación automática
- No en env vars (preferir mounted files)

---

## Network Security

### Segmentación
- VLANs por función (DMZ, App, DB, Management)
- Zero Trust: no confiar en la red interna
- East-west traffic inspection (service mesh, IDS)

### Firewalls
- Default deny inbound y outbound
- Stateful inspection
- Application-layer filtering donde sea posible
- Regular rule review y cleanup

### DNS Security
- DNSSEC para integridad
- DNS filtering (bloqueo de dominios maliciosos)
- DoH/DoT para privacidad
- Monitorización de DNS tunneling

### VPN / Remote Access
- Preferir Zero Trust Network Access (ZTNA) sobre VPN tradicional
- Si VPN: MFA obligatoria, split tunneling cuidadoso, posture check
- No "full tunnel" para todo el tráfico salvo necesidad

---

## Infrastructure as Code (IaC) Security

### Principios
- **Policy as Code**: OPA, Sentinel, Checkov, tfsec
- **No secrets en IaC**: Usar variables de entorno, vault, remote state encryption
- **State file protection**: Terraform state cifrado, locking, acceso restringido
- **Version control**: Todo en Git, PR reviews obligatorios
- **Immutable infrastructure**: No modificar manualmente; re-deploy

### Scanning de IaC
```
Checkov:    Multi-cloud (Terraform, CloudFormation, ARM, K8s)
tfsec:      Terraform específico, rápido
Terrascan:  OPA-based, extensible
Snyk IaC:   Integrado con Snyk platform
```

### Ejemplos de políticas
```
1. Todo bucket S3 debe tener encryption
2. Todo security group debe denegar 0.0.0.0/0 en puertos sensibles
3. Todo recurso debe tener tagging obligatorio
4. Ningún container debe correr como root
5. Todo secret debe provenir de vault, no hardcodeado
```

---

## Server Hardening

### Linux
```bash
# 1. Updates automáticos (solo security)
unattended-upgrades

# 2. Firewall (nftables/iptables/ufw)
ufw default deny incoming
ufw allow from 10.0.0.0/8 to any port 22

# 3. SSH hardening
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
AllowUsers deploy@10.0.0.*

# 4. Fail2ban / CrowdSec
# 5. AIDE / Tripwire para integrity checking
# 6. Auditd para syscall auditing
# 7. AppArmor / SELinux enforcing
```

### Windows
- Windows Defender / ATP
- Credential Guard / Device Guard
- LAPS (Local Admin Password Solution)
- SMB signing obligatorio
- PowerShell Constrained Language Mode
- EMET / Exploit Guard

---

## Checklist de infraestructura

- [ ] Cloud: Responsabilidad compartida clara y documentada
- [ ] IAM cloud con least privilege, no root keys compartidas
- [ ] Audit logs habilitados y centralizados
- [ ] Containers: non-root, read-only fs, minimal image, scanned
- [ ] K8s: RBAC, network policies, admission controllers, etcd encrypted
- [ ] Network: default deny, segmentation, DNSSEC, east-west inspection
- [ ] IaC: Policy as Code, no secrets en repos, state cifrado
- [ ] Servers: auto-patching, firewall, SSH hardening, integrity monitoring
- [ ] Backup cifrado y testeado
- [ ] Disaster recovery documentado y simulado anualmente
