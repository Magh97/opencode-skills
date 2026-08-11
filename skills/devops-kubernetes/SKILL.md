---
name: devops-kubernetes
description: "Kubernetes 1.36 (Haru) para producción. Cubre pods, deployments, services, ingress, Helm v9, ArgoCD v3.4 para GitOps, HPA, resource limits, namespaces, y ConfigMaps/Secrets. Actívala al desplegar aplicaciones en Kubernetes, configurar auto-scaling, o implementar GitOps con ArgoCD."
disable-model-invocation: true
---

# Kubernetes 1.36

Guía de Kubernetes 1.36 (Abr 2026) con Helm y ArgoCD. Enfoque en aplicaciones, no en administración de cluster.

---

## Recursos esenciales

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: miapp-api
  labels:
    app: miapp-api
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: miapp-api
  template:
    metadata:
      labels:
        app: miapp-api
    spec:
      containers:
      - name: api
        image: ghcr.io/mi-org/miapp-api:1.2.3
        ports:
        - containerPort: 3000
        envFrom:
        - configMapRef:
            name: miapp-config
        - secretRef:
            name: miapp-secrets
        resources:
          requests:
            cpu: 250m
            memory: 256Mi
          limits:
            cpu: 1000m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 10
          periodSeconds: 15
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 10
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 5"]  # Drenar conexiones
```

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: miapp-api
spec:
  type: ClusterIP
  selector:
    app: miapp-api
  ports:
  - port: 80
    targetPort: 3000
    protocol: TCP
```

### Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: miapp-api
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.miapp.com
    secretName: miapp-api-tls
  rules:
  - host: api.miapp.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: miapp-api
            port:
              number: 80
```

---

## HPA (Horizontal Pod Autoscaler)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: miapp-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: miapp-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # Esperar 5 min antes de escalar hacia abajo
```

---

## Helm

```yaml
# Chart.yaml
apiVersion: v2
name: miapp-api
version: 1.0.0
appVersion: "1.2.3"

# values.yaml
replicaCount: 3
image:
  repository: ghcr.io/mi-org/miapp-api
  tag: "1.2.3"
  pullPolicy: IfNotPresent

resources:
  requests:
    cpu: 250m
    memory: 256Mi
  limits:
    cpu: 1000m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

environment:
  DATABASE_URL: "postgresql://user:pass@postgres:5432/miapp"
```

```bash
# Instalar
helm upgrade --install miapp-api ./charts/miapp-api \
  --namespace miapp-prod \
  --set image.tag=1.2.4 \
  --values values-prod.yaml

# Rollback
helm rollback miapp-api 2 --namespace miapp-prod

# Historial
helm history miapp-api --namespace miapp-prod
```

---

## ArgoCD (GitOps)

```yaml
# app-of-apps — despliega múltiples aplicaciones desde un solo repo
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: root-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/mi-org/infra
    path: apps/
    targetRevision: main
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

```bash
# CLI
argocd app sync miapp-api
argocd app rollback miapp-api
argocd app history miapp-api
argocd app diff miapp-api  # Ver cambios antes de sync
```

---

## Resource management

```yaml
# ✅ Requests = lo que se reserva. Limits = tope máximo.
# La diferencia entre request y limit es lo que se desperdicia (FinOps).

# Namespace con quotas
apiVersion: v1
kind: ResourceQuota
metadata:
  name: miapp-quota
  namespace: miapp-prod
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    persistentvolumeclaims: "10"

# LimitRange: defaults para pods sin requests/limits
apiVersion: v1
kind: LimitRange
metadata:
  name: miapp-limits
spec:
  limits:
  - default:
      cpu: 500m
      memory: 512Mi
    defaultRequest:
      cpu: 100m
      memory: 128Mi
    type: Container
```

---

## ConfigMaps y Secrets

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: miapp-config
data:
  LOG_LEVEL: "info"
  CORS_ORIGIN: "https://miapp.com"
  API_TIMEOUT: "30"
---
apiVersion: v1
kind: Secret
metadata:
  name: miapp-secrets
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:pass@host/db"
  JWT_SECRET: "super-secret-value-here"
  STRIPE_API_KEY: "sk_live_..."
```

⚠️ Secrets en YAML no están encriptados (solo base64). Para producción: **Sealed Secrets**, **External Secrets Operator** con Vault/AWS Secrets Manager.

---

## K8s 1.36 novedades clave

- **User Namespaces** (stable): mejor aislamiento de contenedores.
- **AI/ML workload maduration**: soporte mejorado para GPUs y trabajos batch.
- **Declarative validation** (GA): APIs más confiables, schemas validados.

---

## Checklist Kubernetes

- [ ] Deployments con strategy RollingUpdate
- [ ] Resources: requests + limits definidos (sin CPU, sin límites)
- [ ] Liveness + readiness probes configuradas
- [ ] HPA para auto-escalado
- [ ] PodDisruptionBudget para drenado seguro de nodos
- [ ] Helm o Kustomize para templating
- [ ] ArgoCD o Flux para GitOps
- [ ] Secrets gestionados con External Secrets Operator (no en YAML plano)
- [ ] QoS mínimo Burstable (requests definidos)
